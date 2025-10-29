"""Utilities for generating and serving project preview assets."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Final
from uuid import UUID

from app.core.config import settings
from app.services.storage.base import StorageError, StorageService

logger = logging.getLogger(__name__)

_PREVIEW_DIR_NAME: Final = "previews"
_PREVIEW_FILES: Final[dict[str, str]] = {
    "schematic": "schematic.svg",
    "layout": "board.svg",
    "view3d": "model.glb",
}
_PLACEHOLDER_SVG_TEMPLATE: Final = (
    """<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"640\" height=\"480\" viewBox=\"0 0 640 480\">\n  <defs>\n    <style>\n      .bg {{ fill: #101828; }}\n      .frame {{ fill: none; stroke: #2563eb; stroke-width: 4; stroke-dasharray: 16 12; }}\n      .label {{ fill: #f8fafc; font: 24px/1.4 \"SFMono-Regular\", Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace; }}\n      .subtitle {{ fill: #cbd5f5; font: 16px/1.4 system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; }}\n    </style>\n  </defs>\n  <rect class=\"bg\" x=\"0\" y=\"0\" width=\"640\" height=\"480\" rx=\"18\"/>\n  <rect class=\"frame\" x=\"36\" y=\"48\" width=\"568\" height=\"384\" rx=\"12\"/>\n  <text class=\"label\" x=\"50\" y=\"120\">{title}</text>\n  <text class=\"subtitle\" x=\"50\" y=\"160\">Preview generation queued. Replace this asset with KiCad output.</text>\n</svg>\n"""
)


def process_project_archive(
    storage: StorageService, project_id: UUID, archive_storage_path: str
) -> None:
    """Extract the uploaded KiCad archive and render preview assets with KiCad CLI.

    Falls back to placeholder SVGs when rendering fails or source files are missing.
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

    try:
        if extraction_root.exists():
            shutil.rmtree(extraction_root)
        extraction_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as zip_file:
            _safe_extract(zip_file, extraction_root)
    except (zipfile.BadZipFile, OSError):
        logger.exception("Failed to extract KiCad archive for project %s", project_id)
        return

    try:
        if previews_root.exists():
            shutil.rmtree(previews_root)
        previews_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.exception(
            "Unable to create previews directory for project %s", project_id
        )
        return

    schematic_file = _find_first(extraction_root, "*.kicad_sch")
    board_file = _find_first(extraction_root, "*.kicad_pcb")

    if schematic_file is None:
        logger.warning("No schematic file found for project %s", project_id)
    if board_file is None:
        logger.warning("No PCB file found for project %s", project_id)

    if schematic_file is not None:
        try:
            _render_schematic(
                schematic_file, previews_root / _PREVIEW_FILES["schematic"]
            )
        except Exception:  # noqa: BLE001
            logger.exception("Schematic rendering failed for project %s", project_id)

    if board_file is not None:
        try:
            _render_board_svg(board_file, previews_root / _PREVIEW_FILES["layout"])
        except Exception:  # noqa: BLE001
            logger.exception("Board SVG rendering failed for project %s", project_id)

        try:
            _render_board_glb(board_file, previews_root / _PREVIEW_FILES["view3d"])
        except Exception:  # noqa: BLE001
            logger.exception("Board GLB rendering failed for project %s", project_id)

    # Ensure we leave at least placeholder assets for missing outputs.
    schematic_path = previews_root / _PREVIEW_FILES["schematic"]
    board_path = previews_root / _PREVIEW_FILES["layout"]
    if not schematic_path.exists():
        _write_placeholder(schematic_path, "Schematic preview")
    if not board_path.exists():
        _write_placeholder(board_path, "PCB layout preview")


def _safe_extract(zip_file: zipfile.ZipFile, destination: Path) -> None:
    """Extract zip contents ensuring paths stay within destination."""

    dest_root = destination.resolve()

    safe_suffixes = {".kicad_sch", ".kicad_pcb", ".kicad_pro", ".kicad_prl"}

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


def _render_schematic(source: Path, target: Path) -> None:
    """Render schematic sheets to SVG and copy the first page as target."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        _run_cli(
            [
                settings.kicad_cli_path,
                "sch",
                "export",
                "svg",
                "--output",
                str(output_dir),
                "--exclude-drawing-sheet",
                "--no-background-color",
                str(source),
            ]
        )

        exported = sorted(output_dir.glob("*.svg"))
        if not exported:
            raise RuntimeError("No schematic SVG generated")
        shutil.copyfile(exported[0], target)


def _render_board_svg(source: Path, target: Path) -> None:
    """Render board layout SVG using KiCad CLI."""

    _run_cli(
        [
            settings.kicad_cli_path,
            "pcb",
            "export",
            "svg",
            "--output",
            str(target),
            "--layers",
            "F.Cu,Edge.Cuts,User.Comments",
            "--exclude-drawing-sheet",
            "--page-size-mode",
            "2",
            str(source),
        ]
    )


def _render_board_glb(source: Path, target: Path) -> None:
    """Render a GLB preview if KiCad CLI succeeds."""

    _run_cli(
        [
            settings.kicad_cli_path,
            "pcb",
            "export",
            "glb",
            "--output",
            str(target),
            "--board-only",
            str(source),
        ]
    )


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


def preview_storage_path(project_id: UUID, preview_type: str) -> str:
    """Return the storage-relative path for the requested preview type."""

    filename = _PREVIEW_FILES.get(preview_type)
    if filename is None:
        raise KeyError(preview_type)
    return f"projects/{project_id}/{_PREVIEW_DIR_NAME}/{filename}"


def preview_exists(
    storage: StorageService, project_id: UUID, preview_type: str
) -> bool:
    """Return whether the requested preview asset exists in storage."""

    try:
        fs_path = storage.filesystem_path(
            preview_storage_path(project_id, preview_type)
        )
    except StorageError:
        return False
    return fs_path.exists()


def preview_filesystem_path(
    storage: StorageService, project_id: UUID, preview_type: str
) -> Path:
    """Resolve the filesystem path for a preview asset, raising on failure."""

    relative_path = preview_storage_path(project_id, preview_type)
    fs_path = storage.filesystem_path(relative_path)
    if not fs_path.exists():
        raise FileNotFoundError(relative_path)
    return fs_path


def list_available_previews(
    storage: StorageService, project_id: UUID
) -> dict[str, bool]:
    """Return a mapping of preview type to availability flag."""

    return {key: preview_exists(storage, project_id, key) for key in _PREVIEW_FILES}


__all__ = [
    "process_project_archive",
    "preview_storage_path",
    "preview_exists",
    "preview_filesystem_path",
    "list_available_previews",
]
