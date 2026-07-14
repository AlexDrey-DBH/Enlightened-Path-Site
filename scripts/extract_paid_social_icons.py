"""Extract the licensed social marks used by the site from an EPS icon sheet.

The input is the Adobe Stock EPS/AI source supplied by the client. The generated
SVG files preserve the original path geometry and apply the site's plum color.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


COMMANDS = {"moveto", "lineto", "curveto", "closepath", "newpath", "fill", "setrgbcolor"}
BRAND_PLUM = "#6f5665"
WHITE = "#ffffff"
SHEET_HEIGHT = 768.0

ICONS = {
    "instagram": (271.5, 407.9, 200.0, 200.0),
    "tiktok": (904.4, 407.9, 200.0, 200.0),
    "youtube": (1115.4, 407.9, 200.0, 200.0),
}


def parse_eps(source: Path) -> list[dict]:
    tokens = re.findall(r"-?\d+(?:\.\d+)?|[A-Za-z]+", source.read_text(encoding="latin-1"))
    stack: list[float] = []
    paths: list[dict] = []
    current: dict | None = None
    color = (0.0, 0.0, 0.0)

    for token in tokens:
        if token not in COMMANDS:
            try:
                stack.append(float(token))
            except ValueError:
                continue
            continue

        if token == "newpath":
            current = {"subpaths": [], "active": None}
        elif token == "moveto" and current is not None:
            x, y = stack[-2:]
            stack.clear()
            active = {"commands": [("M", x, y)], "points": [(x, y)]}
            current["subpaths"].append(active)
            current["active"] = active
        elif token == "lineto" and current is not None and current["active"] is not None:
            x, y = stack[-2:]
            stack.clear()
            current["active"]["commands"].append(("L", x, y))
            current["active"]["points"].append((x, y))
        elif token == "curveto" and current is not None and current["active"] is not None:
            values = tuple(stack[-6:])
            stack.clear()
            current["active"]["commands"].append(("C", *values))
            current["active"]["points"].extend((values[0:2], values[2:4], values[4:6]))
        elif token == "closepath" and current is not None and current["active"] is not None:
            current["active"]["commands"].append(("Z",))
        elif token == "setrgbcolor":
            color = tuple(stack[-3:])
            stack.clear()
        elif token == "fill" and current is not None:
            for subpath in current["subpaths"]:
                if not subpath["points"]:
                    continue
                xs = [point[0] for point in subpath["points"]]
                ys = [point[1] for point in subpath["points"]]
                subpath["bbox"] = (min(xs), min(ys), max(xs), max(ys))
            current["color"] = color
            paths.append(current)
            current = None

    return paths


def inside_cell(bbox: tuple[float, float, float, float], cell: tuple[float, float, float, float]) -> bool:
    x, y, width, height = cell
    center_x = (bbox[0] + bbox[2]) / 2
    center_y = (bbox[1] + bbox[3]) / 2
    return x <= center_x <= x + width and y <= center_y <= y + height


def svg_path(commands: list[tuple]) -> str:
    parts = []
    for command in commands:
        op = command[0]
        if op == "Z":
            parts.append("Z")
        else:
            values = " ".join(f"{value:.2f}".rstrip("0").rstrip(".") for value in command[1:])
            parts.append(f"{op}{values}")
    return " ".join(parts)


def write_icon(paths: list[dict], destination: Path, cell: tuple[float, float, float, float]) -> None:
    x, y, width, height = cell
    svg_paths = []

    for parsed in paths:
        selected = [subpath for subpath in parsed["subpaths"] if inside_cell(subpath["bbox"], cell)]
        if not selected:
            continue
        is_white = min(parsed["color"]) > 0.95
        fill = WHITE if is_white else BRAND_PLUM
        path_data = " ".join(svg_path(subpath["commands"]) for subpath in selected)
        svg_paths.append(f'    <path d="{path_data}" fill="{fill}" fill-rule="nonzero"/>')

    transform = f"translate({-x:.2f} {y + height:.2f}) scale(1 -1)"
    svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img">',
            "  <!-- Derived from the client-supplied licensed Adobe Stock EPS. -->",
            f'  <g transform="{transform}">',
            *svg_paths,
            "  </g>",
            "</svg>",
            "",
        ]
    )
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to the licensed Adobe Stock EPS/AI source")
    parser.add_argument("destination", type=Path, help="Directory for generated SVG files")
    args = parser.parse_args()

    args.destination.mkdir(parents=True, exist_ok=True)
    paths = parse_eps(args.source)
    for name, cell in ICONS.items():
        write_icon(paths, args.destination / f"{name}.svg", cell)
        print(f"Generated {name}.svg")


if __name__ == "__main__":
    main()
