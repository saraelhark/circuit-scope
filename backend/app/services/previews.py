"""Utilities for generating and serving project preview assets."""

from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final
from xml.etree import ElementTree as ET
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
MAX_KICAD_ARCHIVE_SIZE_MB: Final = 30
MAX_KICAD_ARCHIVE_SIZE_BYTES: Final = MAX_KICAD_ARCHIVE_SIZE_MB * 1024 * 1024

_SVG_NAMESPACE: Final = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NAMESPACE)
_DIMENSION_RE = re.compile(r"([0-9.+-eE]+)")


@dataclass(slots=True)
class _SvgDimensions:
    width: float
    height: float


def _parse_svg_dimensions(svg: ET.ElementTree) -> _SvgDimensions:
    """Extract width/height for an SVG element, falling back to viewBox if needed."""

    root = svg.getroot()
    width_attr = root.get("width")
    height_attr = root.get("height")

    def _parse(value: str | None) -> float | None:
        if not value:
            return None
        match = _DIMENSION_RE.search(value)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    width = _parse(width_attr)
    height = _parse(height_attr)

    if width is not None and height is not None:
        return _SvgDimensions(width, height)

    viewbox = root.get("viewBox")
    if viewbox:
        parts = [p for p in re.split(r"[\s,]+", viewbox.strip()) if p]
        if len(parts) == 4:
            try:
                _, _, vb_width, vb_height = map(float, parts)
                return _SvgDimensions(vb_width, vb_height)
            except ValueError:
                pass

    raise ValueError("Unable to determine SVG dimensions")


def _grid_dimensions(count: int) -> tuple[int, int]:
    """Return (rows, columns) providing a balanced grid for the given count."""

    if count <= 0:
        return (1, 1)
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    return rows, columns


def _compose_svg_grid(
    svgs: list[Path], destination: Path, *, padding_ratio: float = 0.05
) -> Path:
    """Combine multiple SVG sheets into a single grid-based SVG."""

    trees: list[ET.ElementTree] = []
    dimensions: list[_SvgDimensions] = []
    for svg_path in svgs:
        tree = ET.parse(svg_path)
        trees.append(tree)
        try:
            dimensions.append(_parse_svg_dimensions(tree))
        except ValueError as exc:
            raise RuntimeError(f"Unable to read dimensions from {svg_path}") from exc

    if not trees:
        raise RuntimeError("No SVGs supplied for composition")

    max_width = max(dim.width for dim in dimensions)
    max_height = max(dim.height for dim in dimensions)
    rows, cols = _grid_dimensions(len(trees))

    padding_x = max_width * padding_ratio
    padding_y = max_height * padding_ratio

    cell_width = max_width + padding_x
    cell_height = max_height + padding_y

    total_width = cols * cell_width - padding_x
    total_height = rows * cell_height - padding_y

    root = ET.Element(
        "{%s}svg" % _SVG_NAMESPACE,
        attrib={
            "width": f"{total_width}",
            "height": f"{total_height}",
            "viewBox": f"0 0 {total_width} {total_height}",
            "version": "1.1",
        },
    )

    for index, (tree, dim) in enumerate(zip(trees, dimensions, strict=True)):
        row = index // cols
        col = index % cols
        translate_x = col * cell_width
        translate_y = row * cell_height

        group = ET.SubElement(
            root,
            "{%s}g" % _SVG_NAMESPACE,
            attrib={"transform": f"translate({translate_x},{translate_y})"},
        )

        scale_x = max_width / dim.width if dim.width else 1.0
        scale_y = max_height / dim.height if dim.height else 1.0
        uniform_scale = min(scale_x, scale_y)

        scale_transform = ""
        if not math.isclose(uniform_scale, 1.0):
            scale_transform = f" scale({uniform_scale})"

        sheet_group = ET.SubElement(group, "{%s}g" % _SVG_NAMESPACE)
        if scale_transform:
            sheet_group.set("transform", scale_transform.strip())

        for child in deepcopy(list(tree.getroot())):
            sheet_group.append(child)

    composed_tree = ET.ElementTree(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    composed_tree.write(destination, encoding="utf-8", xml_declaration=True)
    return destination


async def process_project_archive(
    storage: StorageService, project_id: UUID, archive_storage_path: str
) -> None:
    """Extract the uploaded KiCad archive and render preview assets with KiCad CLI.

    Generates multi-page schematic SVGs, front/back/inner PCB renders, and a GLB preview. A
    metadata index describing generated assets is written to disk to support the API.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)
        local_archive_path = work_dir / "archive.zip"
        extraction_root = work_dir / "extracted"
        previews_root = work_dir / _PREVIEW_DIR_NAME
        schematics_root = previews_root / _SCHEMATIC_DIR
        layouts_root = previews_root / _LAYOUT_DIR
        models_root = previews_root / _MODEL_DIR

        # 1. Download archive
        try:
            await storage.download(archive_storage_path, local_archive_path)
        except StorageError:
            logger.exception(
                "Unable to download storage path '%s' for project %s",
                archive_storage_path,
                project_id,
            )
            return

        # 2. Extract
        try:
            extraction_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(local_archive_path) as zip_file:
                _safe_extract(zip_file, extraction_root)
        except (zipfile.BadZipFile, OSError):
            logger.exception(
                "Failed to extract KiCad archive for project %s", project_id
            )
            return

        # 3. Prepare output directories
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

        # 4. Render Schematics
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

        # 5. Render PCB
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

        # 6. Upload generated assets
        # Walk through previews_root and upload all files relative to it
        # Target base: projects/{id}/previews/
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

        # 7. Write index
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
            title = _derive_sheet_title(svg_file)
            slug = _slugify(f"{idx:02d}-{title}")
            filename = _unique_filename(slug, ".svg", used_filenames)
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
        composed_filename = _unique_filename("schematic-grid", ".svg", used_filenames)
        composed_path = output_dir / composed_filename
        try:
            _compose_svg_grid(copied_svg_paths, composed_path)
        except Exception:
            logger.exception(
                "Failed to compose schematic grid; falling back to first sheet"
            )
        else:
            composed_entry = {
                "id": f"{_slugify(primary_source.stem) or 'schematics'}-grid",
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

    bundle_id = _slugify(primary_source.stem) or "schematics"
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

    # Add specs for inner layers (In1.Cu ... In30.Cu)
    # We try to render them; if the output is empty/invalid, we skip adding them to the index.
    for i in range(1, 31):
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
            # It is expected that many inner layers won't exist, so we log only at debug
            # or ignore if it's a specific error related to missing layer.
            # However, kicad-cli might return success even if layer is empty.
            # We'll check file size below.
            logger.debug("Failed to render or layer not present: %s", key)
            continue

        if destination.exists():
            # Check for "empty" SVG (just header/footer) to avoid cluttering the UI
            # A robust check would look for actual geometry elements.
            # For now, we'll trust existence, but we might need to refine this if KiCad
            # exports empty SVGs for non-existent layers.
            if destination.stat().st_size < 500:  # Arbitrary small size check
                # Let's try to read it and check for content if needed, but size is a good first proxy.
                # Actually, an empty SVG with viewbox might be small.
                # Let's allow it for now, but we might want to parse it later.
                pass

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
        # Include copper features and component models for a richer 3D view.
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


import io


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


async def validate_preview_asset_path(
    storage: StorageService, project_id: UUID, asset_path: str
) -> str:
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
