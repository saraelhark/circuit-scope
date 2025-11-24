"""Utilities for generating and serving project preview assets."""

from __future__ import annotations

import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Final
from uuid import UUID

from app.core.config import settings
from app.services.storage.base import StorageError, StorageService
from app.services.svg_utils import compose_svg_grid, derive_sheet_title
from app.services.utils import slugify, unique_filename

logger = logging.getLogger(__name__)

_PREVIEW_DIR_NAME: Final = "previews"
_SCHEMATIC_DIR: Final = "schematics"
_LAYOUT_DIR: Final = "layouts"
_MODEL_DIR: Final = "models"
_INDEX_FILENAME: Final = "index.json"
_SAFE_ASSET_SUFFIXES: Final = {".svg", ".glb"}
_SAFE_SOURCE_SUFFIXES: Final = {".kicad_sch", ".kicad_pcb", ".kicad_pro", ".kicad_prl"}
MAX_KICAD_ARCHIVE_SIZE_MB: Final = 30
MAX_KICAD_ARCHIVE_SIZE_BYTES: Final = MAX_KICAD_ARCHIVE_SIZE_MB * 1024 * 1024


async def process_project_archive(
    storage: StorageService, project_id: UUID, archive_path: Path
) -> None:
    """Extract the uploaded KiCad archive and render preview assets with KiCad CLI.

    Generates multi-page schematic SVGs, front/back/inner PCB renders, and a GLB preview. A
    metadata index describing generated assets is written to disk to support the API.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)
        extraction_root = work_dir / "extracted"
        previews_root = work_dir / _PREVIEW_DIR_NAME
        schematics_root = previews_root / _SCHEMATIC_DIR
        layouts_root = previews_root / _LAYOUT_DIR
        models_root = previews_root / _MODEL_DIR

        try:
            extraction_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive_path) as zip_file:
                _safe_extract(zip_file, extraction_root)
        except (zipfile.BadZipFile, OSError):
            logger.exception(
                "Failed to extract KiCad archive for project %s", project_id
            )
            return

        for directory in (previews_root, schematics_root, layouts_root, models_root):
            directory.mkdir(parents=True, exist_ok=True)

        index: dict[str, Any] = {
            "project": _read_project_metadata(extraction_root),
            "schematics": [],
            "layouts": [],
            "models": [],
        }

        schematic_sources = _find_all_schematics(extraction_root)
        board_file = _find_first(extraction_root, "*.kicad_pcb")

        if not schematic_sources:
            logger.warning("No schematic file found for project %s", project_id)
        else:
            try:
                index["schematics"] = _render_schematic_bundle(
                    schematic_sources[0],
                    schematics_root,
                    schematic_sources,
                    extraction_root,
                )
            except Exception:
                logger.exception(
                    "Schematic rendering failed for project %s", project_id
                )

        if board_file is None:
            logger.warning("No PCB file found for project %s", project_id)
        else:
            try:
                layout_entries = _render_board_svgs(board_file, layouts_root)
                if layout_entries:
                    index["layouts"].extend(layout_entries)
            except Exception:
                logger.exception(
                    "Board SVG rendering failed for project %s", project_id
                )

            try:
                model_entry = _render_board_glb(board_file, models_root)
                if model_entry:
                    index["models"].append(model_entry)
            except Exception:
                logger.exception(
                    "Board GLB rendering failed for project %s", project_id
                )

        base_storage_path = _project_preview_base(project_id)

        for root, _, files in os.walk(previews_root):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(previews_root)
                target_path = str(base_storage_path / relative_path)
                try:
                    await storage.upload(target_path, file_path)
                except StorageError:
                    logger.exception("Failed to upload preview asset: %s", target_path)

        await _write_index(storage, project_id, index)


def _safe_extract(zip_file: zipfile.ZipFile, destination: Path) -> None:
    """Extract zip contents ensuring paths stay within destination."""

    dest_root = destination.resolve()

    safe_suffixes = _SAFE_SOURCE_SUFFIXES

    for member in zip_file.infolist():
        filename = member.filename
        if filename.startswith("__MACOSX/") or filename.endswith("/.DS_Store"):
            continue

        target_path = (dest_root / filename).resolve()
        try:
            target_path.relative_to(dest_root)
            within_destination = True
        except ValueError:
            within_destination = False

        if not within_destination:
            if Path(filename).suffix in safe_suffixes:
                logger.info("Allowing nested KiCad asset outside root: %s", filename)
            else:
                logger.warning("Skipping unsafe archive member: %s", filename)
                continue

        zip_file.extract(member, dest_root)


def _find_first(root: Path, pattern: str) -> Path | None:
    """Return the first path matching the glob pattern under root."""

    return next(root.rglob(pattern), None)


def _find_all_schematics(root: Path) -> list[Path]:
    """Return all schematic sources inside the extracted archive."""

    return sorted(root.rglob("*.kicad_sch"))


def _render_schematic_bundle(
    primary_source: Path,
    output_dir: Path,
    all_sources: list[Path],
    project_root: Path,
) -> list[dict[str, Any]]:
    """Render schematic sheets and return a single preview entry with page metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        _run_cli(
            [
                settings.kicad_cli_path,
                "sch",
                "export",
                "svg",
                "--output",
                str(tmp_path),
                "--exclude-drawing-sheet",
                "--no-background-color",
                str(primary_source),
            ]
        )

        exported = sorted(tmp_path.glob("*.svg"))
        if not exported:
            raise RuntimeError("No schematic SVG generated")

        used_filenames: set[str] = set()
        pages: list[dict[str, Any]] = []
        copied_svg_paths: list[Path] = []
        for idx, svg_file in enumerate(exported, start=1):
            title = derive_sheet_title(svg_file)
            slug = slugify(f"{idx:02d}-{title}")
            filename = unique_filename(slug, ".svg", used_filenames)
            used_filenames.add(filename)

            destination = output_dir / filename
            shutil.copyfile(svg_file, destination)
            copied_svg_paths.append(destination)

            pages.append(
                {
                    "id": slug,
                    "filename": filename,
                    "title": title,
                    "page": idx,
                    "path": f"{_SCHEMATIC_DIR}/{filename}",
                }
            )

    composed_entry: dict[str, Any] | None = None
    if len(copied_svg_paths) > 1:
        composed_filename = unique_filename("schematic-grid", ".svg", used_filenames)
        composed_path = output_dir / composed_filename
        try:
            compose_svg_grid(copied_svg_paths, composed_path)
        except Exception:
            logger.exception(
                "Failed to compose schematic grid; falling back to first sheet"
            )
        else:
            composed_entry = {
                "id": f"{slugify(primary_source.stem) or 'schematics'}-grid",
                "filename": composed_filename,
                "title": "All sheets",
                "path": f"{_SCHEMATIC_DIR}/{composed_filename}",
            }

    sources: list[str] = []
    for source in all_sources:
        try:
            sources.append(str(source.relative_to(project_root)))
        except ValueError:
            sources.append(str(source))

    bundle_id = slugify(primary_source.stem) or "schematics"
    first_entry = composed_entry or pages[0]

    bundle: dict[str, Any] = {
        "id": bundle_id,
        "filename": first_entry["filename"],
        "title": first_entry.get("title", first_entry["filename"]),
        "path": first_entry["path"],
        "page_count": len(pages),
        "pages": pages,
        "sources": sources,
        "multi_page": len(pages) > 1,
    }

    return [bundle]


def _render_board_svgs(source: Path, output_dir: Path) -> list[dict[str, Any]]:
    """Render front and back PCB layout SVGs using KiCad CLI."""

    output_dir.mkdir(parents=True, exist_ok=True)

    layer_specs: list[tuple[str, str, list[str], list[str]]] = [
        (
            "front",
            "Front",
            ["F.Cu", "F.Mask", "F.SilkS", "Edge.Cuts", "User.Drawings"],
            [],
        ),
        (
            "back",
            "Bottom",
            ["B.Cu", "B.Mask", "B.SilkS", "Edge.Cuts", "User.Drawings"],
            [],
        ),
    ]

    # Add specs for inner layers (In1.Cu ... In6.Cu)
    # We try to render them; if the output is empty/invalid, we skip adding them to the index.
    for i in range(1, 7):
        layer_name = f"In{i}.Cu"
        layer_specs.append(
            (
                f"inner-{i}",
                f"Inner Layer {i}",
                [layer_name, "Edge.Cuts", "User.Drawings"],
                [],
            )
        )

    entries: list[dict[str, Any]] = []

    for key, title, layers, extra_flags in layer_specs:
        filename = f"{key}.svg"
        destination = output_dir / filename

        command = [
            settings.kicad_cli_path,
            "pcb",
            "export",
            "svg",
            "--output",
            str(destination),
            "--layers",
            ",".join(layers),
            "--exclude-drawing-sheet",
            "--page-size-mode",
            "2",
        ]
        command.extend(extra_flags)
        command.append(str(source))

        try:
            _run_cli(command)
        except RuntimeError:
            # Expected for missing inner layers
            logger.debug("Failed to render or layer not present: %s", key)
            continue

        if destination.exists():
            # Skip empty or invalid SVGs (approximate check by size)
            if destination.stat().st_size < 500:
                continue

            entries.append(
                {
                    "id": key,
                    "filename": filename,
                    "title": title,
                    "layers": layers,
                    "path": f"{_LAYOUT_DIR}/{filename}",
                }
            )

    return entries


def _render_board_glb(source: Path, output_dir: Path) -> dict[str, Any] | None:
    """Render a GLB preview if KiCad CLI succeeds."""

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "board.glb"

    command = [
        settings.kicad_cli_path,
        "pcb",
        "export",
        "glb",
        "--output",
        str(destination),
        "--include-tracks",
        "--include-pads",
        "--include-zones",
        "--include-silkscreen",
        "--include-soldermask",
        "--subst-models",
        str(source),
    ]

    _run_cli(command)

    if destination.exists():
        return {
            "id": "board-3d",
            "filename": destination.name,
            "title": "3D model",
            "path": f"{_MODEL_DIR}/{destination.name}",
        }
    return None


def _run_cli(command: list[str]) -> None:
    """Execute KiCad CLI command with configured timeout."""

    logger.debug("Running KiCad CLI command: %s", " ".join(command))
    try:
        subprocess.run(  # noqa: PL subprocess security: controlled values
            command,
            check=True,
            timeout=settings.kicad_cli_timeout_seconds,
        )
    except FileNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("kicad-cli executable not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("kicad-cli command timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"kicad-cli exited with code {exc.returncode}") from exc


async def _write_index(
    storage: StorageService, project_id: UUID, index: dict[str, Any]
) -> None:
    """Persist the preview index JSON file."""

    try:
        content = json.dumps(index, indent=2, ensure_ascii=False).encode("utf-8")
        file_obj = io.BytesIO(content)
        await storage.save(_preview_index_storage_path(project_id), file_obj)
    except StorageError:
        logger.exception("Failed to write preview index for project %s", project_id)


def _read_project_metadata(extraction_root: Path) -> dict[str, Any]:
    """Extract basic project metadata from the KiCad project file if present."""

    project_file = _find_first(extraction_root, "*.kicad_pro")
    if not project_file:
        return {}

    try:
        content = project_file.read_text(encoding="utf-8")
        data = json.loads(content)
    except (OSError, json.JSONDecodeError):
        logger.debug("Unable to parse project metadata from %s", project_file)
        return {}

    metadata = data.get("metadata") or data.get("meta") or {}
    title_block = metadata.get("title_block") if isinstance(metadata, dict) else {}

    return {
        "source": str(project_file.relative_to(extraction_root)),
        "title": (
            title_block.get("title")
            if isinstance(title_block, dict)
            else metadata.get("title")
        ),
        "company": (
            title_block.get("company")
            if isinstance(title_block, dict)
            else metadata.get("company")
        ),
        "revision": (
            title_block.get("revision")
            if isinstance(title_block, dict)
            else metadata.get("revision")
        ),
        "date": (
            title_block.get("date")
            if isinstance(title_block, dict)
            else metadata.get("date")
        ),
    }


async def load_preview_index(
    storage: StorageService, project_id: UUID
) -> dict[str, Any]:
    """Load the stored preview index for a project."""

    index_storage_path = _preview_index_storage_path(project_id)
    try:
        content_bytes = await storage.read(index_storage_path)
        content = content_bytes.decode("utf-8")
        return json.loads(content)
    except (StorageError, json.JSONDecodeError):
        logger.exception("Failed to read preview index for project %s", project_id)
        return {"project": {}, "schematics": [], "layouts": [], "models": []}


async def list_previews_summary(
    storage: StorageService, project_id: UUID
) -> dict[str, Any]:
    """Return a condensed view of available previews for listings."""

    index = await load_preview_index(storage, project_id)
    return {
        "schematics": [entry["path"] for entry in index.get("schematics", [])],
        "layouts": [entry["path"] for entry in index.get("layouts", [])],
        "models": [entry["path"] for entry in index.get("models", [])],
        "project": index.get("project", {}),
    }


async def validate_preview_asset_path(project_id: UUID, asset_path: str) -> str:
    """Resolve the storage path for a preview asset, validating traversal attempts."""

    clean_path = _sanitize_asset_path(asset_path)
    storage_path = _project_preview_base(project_id) / clean_path

    if clean_path.suffix.lower() not in _SAFE_ASSET_SUFFIXES:
        raise FileNotFoundError("Unsupported asset type")

    return str(storage_path)


def _sanitize_asset_path(asset_path: str) -> Path:
    path = Path(asset_path)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise FileNotFoundError("Invalid asset path")
    return path


def _project_preview_base(project_id: UUID) -> Path:
    return Path("projects") / str(project_id) / _PREVIEW_DIR_NAME


def _preview_index_storage_path(project_id: UUID) -> str:
    return str(_project_preview_base(project_id) / _INDEX_FILENAME)


__all__ = [
    "process_project_archive",
    "load_preview_index",
    "list_previews_summary",
]
