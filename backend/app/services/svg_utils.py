"""SVG manipulation utilities."""

from __future__ import annotations

import math
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NAMESPACE)
_DIMENSION_RE = re.compile(r"([0-9.+-eE]+)")


@dataclass(slots=True)
class SvgDimensions:
    width: float
    height: float


def parse_svg_dimensions(svg: ET.ElementTree) -> SvgDimensions:
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
        return SvgDimensions(width, height)

    viewbox = root.get("viewBox")
    if viewbox:
        parts = [p for p in re.split(r"[\s,]+", viewbox.strip()) if p]
        if len(parts) == 4:
            try:
                _, _, vb_width, vb_height = map(float, parts)
                return SvgDimensions(vb_width, vb_height)
            except ValueError:
                pass

    raise ValueError("Unable to determine SVG dimensions")


def grid_dimensions(count: int) -> tuple[int, int]:
    """Return (rows, columns) providing a balanced grid for the given count."""
    if count <= 0:
        return (1, 1)
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    return rows, columns


def compose_svg_grid(
    svgs: list[Path], destination: Path, *, padding_ratio: float = 0.05
) -> Path:
    """Combine multiple SVG sheets into a single grid-based SVG."""
    trees: list[ET.ElementTree] = []
    dimensions: list[SvgDimensions] = []
    for svg_path in svgs:
        tree = ET.parse(svg_path)
        trees.append(tree)
        try:
            dimensions.append(parse_svg_dimensions(tree))
        except ValueError as exc:
            raise RuntimeError(f"Unable to read dimensions from {svg_path}") from exc

    if not trees:
        raise RuntimeError("No SVGs supplied for composition")

    max_width = max(dim.width for dim in dimensions)
    max_height = max(dim.height for dim in dimensions)
    rows, cols = grid_dimensions(len(trees))

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


def derive_sheet_title(svg_file: Path) -> str:
    """Extract title from SVG metadata or fallback to filename."""
    try:
        content = svg_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return svg_file.stem

    match = re.search(r"<title>(.*?)</title>", content, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_file.stem
