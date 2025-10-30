"""Utilities for generating and serving project preview assets."""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Any, Final
from uuid import UUID

from app.core.config import settings
from app.services.storage.base import StorageError, StorageService

logger = logging.getLogger(__name__)

_PREVIEW_DIR_NAME: Final = "previews"
_SCHEMATIC_DIR: Final = "schematics"
_LAYOUT_DIR: Final = "layouts"
_MODEL_DIR: Final = "models"
_INDEX_FILENAME: Final = "index.json"
_SAFE_ASSET_SUFFIXES: Final = {".svg", ".glb"}
_SAFE_SOURCE_SUFFIXES: Final = {".kicad_sch", ".kicad_pcb", ".kicad_pro", ".kicad_prl"}
_PLACEHOLDER_SVG_TEMPLATE: Final = (
    """<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"640\" height=\"480\" viewBox=\"0 0 640 480\">\n  <defs>\n    <style>\n      .bg {{ fill: #101828; }}\n      .frame {{ fill: none; stroke: #2563eb; stroke-width: 4; stroke-dasharray: 16 12; }}\n      .label {{ fill: #f8fafc; font: 24px/1.4 \"SFMono-Regular\", Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace; }}\n      .subtitle {{ fill: #cbd5f5; font: 16px/1.4 system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; }}\n    </style>\n  </defs>\n  <rect class=\"bg\" x=\"0\" y=\"0\" width=\"640\" height=\"480\" rx=\"18\"/>\n  <rect class=\"frame\" x=\"36\" y=\"48\" width=\"568\" height=\"384\" rx=\"12\"/>\n  <text class=\"label\" x=\"50\" y=\"120\">{title}</text>\n  <text class=\"subtitle\" x=\"50\" y=\"160\">Preview generation queued. Replace this asset with KiCad output.</text>\n</svg>\n"""
)


def process_project_archive(
    storage: StorageService, project_id: UUID, archive_storage_path: str
) -> None:
    """Extract the uploaded KiCad archive and render preview assets with KiCad CLI.

    Generates multi-page schematic SVGs, front/back PCB renders, and a GLB preview. A
    metadata index describing generated assets is written to disk to support the API.
    """

    try:
        archive_path = storage.filesystem_path(archive_storage_path)
    except StorageError:
        logger.exception(
            "Unable to resolve storage path '%s' for project %s",
            archive_storage_path,
            project_id,
        )
        return

    project_root = archive_path.parent
    extraction_root = project_root / "extracted"
    previews_root = project_root / _PREVIEW_DIR_NAME
    schematics_root = previews_root / _SCHEMATIC_DIR
    layouts_root = previews_root / _LAYOUT_DIR
    models_root = previews_root / _MODEL_DIR

    try:
        if extraction_root.exists():
            shutil.rmtree(extraction_root)
        extraction_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as zip_file:
            _safe_extract(zip_file, extraction_root)
    except (zipfile.BadZipFile, OSError):
        logger.exception("Failed to extract KiCad archive for project %s", project_id)
        return

    for directory in (previews_root, schematics_root, layouts_root, models_root):
        try:
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.exception(
                "Unable to prepare previews directory '%s' for project %s",
                directory,
                project_id,
            )
            return

    index: dict[str, Any] = {
        "project": _read_project_metadata(extraction_root),
        "schematics": [],
        "layouts": [],
        "models": [],
    }

    schematic_file = _find_first(extraction_root, "*.kicad_sch")
    board_file = _find_first(extraction_root, "*.kicad_pcb")

    if schematic_file is None:
        logger.warning("No schematic file found for project %s", project_id)
    else:
        try:
            index["schematics"] = _render_all_schematics(
                schematic_file, schematics_root
            )
        except Exception:  # noqa: BLE001
            logger.exception("Schematic rendering failed for project %s", project_id)

    if board_file is None:
        logger.warning("No PCB file found for project %s", project_id)
    else:
        try:
            layout_entries = _render_board_svgs(board_file, layouts_root)
            if layout_entries:
                index["layouts"].extend(layout_entries)
        except Exception:  # noqa: BLE001
            logger.exception("Board SVG rendering failed for project %s", project_id)

        try:
            model_entry = _render_board_glb(board_file, models_root)
            if model_entry:
                index["models"].append(model_entry)
        except Exception:  # noqa: BLE001
            logger.exception("Board GLB rendering failed for project %s", project_id)

    _ensure_placeholders(index, schematics_root, layouts_root)
    _write_index(previews_root, index)


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


def _render_all_schematics(source: Path, output_dir: Path) -> list[dict[str, Any]]:
    """Render every sheet in the schematic to individual SVG files."""

    entries: list[dict[str, Any]] = []
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
                str(source),
            ]
        )

        exported = sorted(tmp_path.glob("*.svg"))
        if not exported:
            raise RuntimeError("No schematic SVG generated")

        used_filenames: set[str] = set()
        for idx, svg_file in enumerate(exported, start=1):
            title = _derive_sheet_title(svg_file)
            slug = _slugify(f"{idx:02d}-{title}")
            filename = _unique_filename(slug, ".svg", used_filenames)
            used_filenames.add(filename)

            destination = output_dir / filename
            shutil.copyfile(svg_file, destination)

            entries.append(
                {
                    "id": slug,
                    "filename": filename,
                    "title": title,
                    "page": idx,
                    "placeholder": False,
                    "path": f"{_SCHEMATIC_DIR}/{filename}",
                }
            )

    return entries


def _render_board_svgs(source: Path, output_dir: Path) -> list[dict[str, Any]]:
    """Render front and back PCB layout SVGs using KiCad CLI."""

    output_dir.mkdir(parents=True, exist_ok=True)

    layer_specs: list[tuple[str, str, list[str], list[str]]] = [
        (
            "front",
            "Front copper",
            ["F.Cu", "F.Mask", "F.SilkS", "Edge.Cuts", "User.Drawings"],
            [],
        ),
        (
            "back",
            "Back copper",
            ["B.Cu", "B.Mask", "B.SilkS", "Edge.Cuts", "User.Drawings"],
            ["--mirror"],
        ),
    ]

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
            logger.exception("Failed to render %s PCB preview", key)
            continue

        if destination.exists():
            entries.append(
                {
                    "id": key,
                    "filename": filename,
                    "title": title,
                    "layers": layers,
                    "placeholder": False,
                    "path": f"{_LAYOUT_DIR}/{filename}",
                }
            )

    return entries


def _render_board_glb(source: Path, output_dir: Path) -> dict[str, Any] | None:
    """Render a GLB preview if KiCad CLI succeeds."""

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "board.glb"

    _run_cli(
        [
            settings.kicad_cli_path,
            "pcb",
            "export",
            "glb",
            "--output",
            str(destination),
            "--board-only",
            str(source),
        ]
    )

    if destination.exists():
        return {
            "id": "board-3d",
            "filename": destination.name,
            "title": "3D model",
            "placeholder": False,
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


def _write_placeholder(target: Path, title: str) -> None:
    """Write a placeholder SVG asset with the provided title."""

    try:
        target.write_text(
            _PLACEHOLDER_SVG_TEMPLATE.format(title=title), encoding="utf-8"
        )
    except OSError:
        logger.exception("Failed to write placeholder preview asset: %s", target)


def _ensure_placeholders(
    index: dict[str, Any], schematics_root: Path, layouts_root: Path
) -> None:
    """Ensure at least one schematic and layout asset exists."""

    if not index["schematics"]:
        placeholder = schematics_root / "placeholder.svg"
        _write_placeholder(placeholder, "Schematic preview")
        index["schematics"].append(
            {
                "id": "schematic-placeholder",
                "filename": placeholder.name,
                "title": "No schematic provided",
                "page": 1,
                "placeholder": True,
                "path": f"{_SCHEMATIC_DIR}/{placeholder.name}",
            }
        )

    if not index["layouts"]:
        placeholder = layouts_root / "placeholder.svg"
        _write_placeholder(placeholder, "PCB layout preview")
        index["layouts"].append(
            {
                "id": "layout-placeholder",
                "filename": placeholder.name,
                "title": "No layout provided",
                "layers": [],
                "placeholder": True,
                "path": f"{_LAYOUT_DIR}/{placeholder.name}",
            }
        )


def _write_index(previews_root: Path, index: dict[str, Any]) -> None:
    """Persist the preview index JSON file."""

    try:
        (previews_root / _INDEX_FILENAME).write_text(
            json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        logger.exception("Failed to write preview index for %s", previews_root)


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
        "title": title_block.get("title") if isinstance(title_block, dict) else metadata.get("title"),
        "company": title_block.get("company") if isinstance(title_block, dict) else metadata.get("company"),
        "revision": title_block.get("revision") if isinstance(title_block, dict) else metadata.get("revision"),
        "date": title_block.get("date") if isinstance(title_block, dict) else metadata.get("date"),
    }


def load_preview_index(storage: StorageService, project_id: UUID) -> dict[str, Any]:
    """Load the stored preview index for a project."""

    index_path = storage.filesystem_path(_preview_index_storage_path(project_id))
    try:
        content = index_path.read_text(encoding="utf-8")
        return json.loads(content)
    except FileNotFoundError as exc:
        raise FileNotFoundError("Preview index not found") from exc
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to read preview index for project %s", project_id)
        return {"project": {}, "schematics": [], "layouts": [], "models": []}


def list_previews_summary(storage: StorageService, project_id: UUID) -> dict[str, Any]:
    """Return a condensed view of available previews for listings."""

    index = load_preview_index(storage, project_id)
    return {
        "schematics": [entry["path"] for entry in index.get("schematics", [])],
        "layouts": [entry["path"] for entry in index.get("layouts", [])],
        "models": [entry["path"] for entry in index.get("models", [])],
        "project": index.get("project", {}),
    }


def preview_asset_filesystem_path(
    storage: StorageService, project_id: UUID, asset_path: str
) -> Path:
    """Resolve the filesystem path for a preview asset, validating traversal attempts."""

    clean_path = _sanitize_asset_path(asset_path)
    storage_path = _project_preview_base(project_id) / clean_path
    fs_path = storage.filesystem_path(str(storage_path))
    if not fs_path.exists():
        raise FileNotFoundError(clean_path)
    if fs_path.suffix.lower() not in _SAFE_ASSET_SUFFIXES:
        raise FileNotFoundError("Unsupported asset type")
    return fs_path


def _sanitize_asset_path(asset_path: str) -> Path:
    path = Path(asset_path)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise FileNotFoundError("Invalid asset path")
    return path


def _project_preview_base(project_id: UUID) -> Path:
    return Path("projects") / str(project_id) / _PREVIEW_DIR_NAME


def _preview_index_storage_path(project_id: UUID) -> str:
    return str(_project_preview_base(project_id) / _INDEX_FILENAME)


def _derive_sheet_title(svg_file: Path) -> str:
    try:
        content = svg_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return svg_file.stem

    match = re.search(r"<title>(.*?)</title>", content, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_file.stem


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "sheet"


def _unique_filename(base: str, extension: str, used: set[str]) -> str:
    candidate = f"{base}{extension}"
    counter = 1
    while candidate in used:
        candidate = f"{base}-{counter}{extension}"
        counter += 1
    return candidate


__all__ = [
    "process_project_archive",
    "load_preview_index",
    "list_previews_summary",
    "preview_asset_filesystem_path",
]
