#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Convert a 2D drawing (DXF, DWG or PDF) into line segments the BIM slice reads.

The slice imports a drawing as sketch lines on the active storey. This script
does the reading the slice cannot do yet:

- DXF is read directly: LINE, LWPOLYLINE, POLYLINE/VERTEX, ARC and CIRCLE in the
  model space, in the file's units ($INSUNITS; millimetres when unset).
- DWG goes through LibreDWG's `dwg2dxf` first, when it is installed.
- PDF goes through Poppler's `pdftocairo -svg` (first page); its paths are read
  from the SVG, curves flattened, and paper points scaled by `--scale`
  (1:100 by default) into model metres.

The output is text, one segment a line, in metres:

    bimlines 1
    l x1 y1 x2 y2
    ...

On failure it prints `error <reason>` and exits with 1.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

INSUNITS_METRES = {0: 0.001, 1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 14: 0.1}
ARC_STEPS = 32


def fail(reason: str) -> None:
    print(f"error {reason}")
    sys.exit(1)


def dxf_pairs(text: str):
    lines = text.splitlines()
    for index in range(0, len(lines) - 1, 2):
        yield lines[index].strip(), lines[index + 1].strip()


def arc_points(cx, cy, radius, start_deg, end_deg):
    if end_deg < start_deg:
        end_deg += 360.0
    steps = max(2, int(ARC_STEPS * (end_deg - start_deg) / 360.0) + 1)
    return [
        (cx + radius * math.cos(math.radians(start_deg + (end_deg - start_deg) * i / steps)),
         cy + radius * math.sin(math.radians(start_deg + (end_deg - start_deg) * i / steps)))
        for i in range(steps + 1)
    ]


def read_dxf(path: Path):
    text = path.read_text(errors="replace")
    pairs = list(dxf_pairs(text))
    unit = 0.001
    for index, (code, value) in enumerate(pairs):
        if code == "9" and value == "$INSUNITS" and index + 1 < len(pairs):
            unit = INSUNITS_METRES.get(int(float(pairs[index + 1][1])), 0.001)
            break
    segments = []
    in_entities = False
    entity = None
    fields: dict[str, list[str]] = {}
    polyline_points: list[tuple[float, float]] | None = None
    polyline_closed = False

    def flush():
        nonlocal polyline_points, polyline_closed
        if entity is None:
            return
        get = lambda c, i=0: float(fields[c][i]) if c in fields and len(fields[c]) > i else 0.0
        if entity == "LINE":
            segments.append((get("10"), get("20"), get("11"), get("21")))
        elif entity == "LWPOLYLINE":
            xs, ys = fields.get("10", []), fields.get("20", [])
            points = [(float(x), float(y)) for x, y in zip(xs, ys)]
            if int(get("70")) & 1 and points:
                points.append(points[0])
            segments.extend((a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))
        elif entity == "POLYLINE":
            polyline_points = []
            polyline_closed = bool(int(get("70")) & 1)
        elif entity == "VERTEX" and polyline_points is not None:
            polyline_points.append((get("10"), get("20")))
        elif entity == "SEQEND" and polyline_points is not None:
            points = polyline_points + ([polyline_points[0]] if polyline_closed and polyline_points else [])
            segments.extend((a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))
            polyline_points = None
        elif entity in ("ARC", "CIRCLE"):
            start, end = (get("50"), get("51")) if entity == "ARC" else (0.0, 360.0)
            points = arc_points(get("10"), get("20"), get("40"), start, end)
            segments.extend((a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))

    for code, value in pairs:
        if code == "2" and value == "ENTITIES":
            in_entities = True
            continue
        if not in_entities:
            continue
        if code == "0":
            flush()
            if value == "ENDSEC":
                break
            entity, fields = value, {}
        else:
            fields.setdefault(code, []).append(value)
    return [(x1 * unit, y1 * unit, x2 * unit, y2 * unit) for x1, y1, x2, y2 in segments]


def read_dwg(path: Path):
    converter = shutil.which("dwg2dxf")
    if converter is None:
        fail("DWG needs LibreDWG's dwg2dxf (sudo apt install libredwg-tools); or save the drawing as DXF")
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "drawing.dxf"
        subprocess.run([converter, "-y", "-o", str(target), str(path)], capture_output=True, check=False)
        if not target.exists():
            fail("dwg2dxf could not convert the drawing")
        return read_dxf(target)


NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def svg_transform(text: str):
    """The affine (a, b, c, d, e, f) of an SVG transform attribute."""
    total = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, arguments in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        values = [float(v) for v in NUMBER.findall(arguments)]
        if name == "matrix" and len(values) == 6:
            step = tuple(values)
        elif name == "translate":
            step = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if len(values) > 1 else 0.0)
        elif name == "scale":
            step = (values[0], 0.0, 0.0, values[1] if len(values) > 1 else values[0], 0.0, 0.0)
        else:
            continue
        a, b, c, d, e, f = total
        a2, b2, c2, d2, e2, f2 = step
        total = (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
                 a * e2 + c * f2 + e, b * e2 + d * f2 + f)
    return total


def apply(matrix, x, y):
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def path_segments(data: str):
    """The segments of SVG path data: M, L, H, V, C, Q, Z, absolute or relative."""
    tokens = re.findall(r"[MmLlHhVvCcQqZz]|" + NUMBER.pattern, data)
    segments, index = [], 0
    current = start = (0.0, 0.0)
    command = "M"
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command in "Zz":
                if current != start:
                    segments.append((current, start))
                current = start
                continue
        relative = command.islower()
        kind = command.upper()
        take = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4}.get(kind, 0)
        if take == 0 or index + take > len(tokens):
            break
        values = [float(v) for v in tokens[index:index + take]]
        index += take
        ox, oy = current if relative else (0.0, 0.0)
        if kind == "M":
            current = start = (values[0] + ox, values[1] + oy)
            command = "l" if relative else "L"
        elif kind == "L":
            point = (values[0] + ox, values[1] + oy)
            segments.append((current, point))
            current = point
        elif kind == "H":
            point = (values[0] + ox, current[1])
            segments.append((current, point))
            current = point
        elif kind == "V":
            point = (current[0], values[0] + oy)
            segments.append((current, point))
            current = point
        else:
            controls = [(values[i] + ox, values[i + 1] + oy) for i in range(0, take, 2)]
            points = [current] + controls
            previous = current
            for step in range(1, 9):
                t = step / 8.0
                if kind == "C":
                    p0, p1, p2, p3 = points
                    x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
                    y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
                else:
                    p0, p1, p2 = points
                    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
                    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
                segments.append((previous, (x, y)))
                previous = (x, y)
            current = controls[-1]
    return segments


def read_pdf(path: Path, scale: float):
    converter = shutil.which("pdftocairo")
    if converter is None:
        fail("PDF needs Poppler's pdftocairo (sudo apt install poppler-utils)")
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "page.svg"
        subprocess.run([converter, "-svg", "-f", "1", "-l", "1", str(path), str(target)],
                       capture_output=True, check=False)
        if not target.exists():
            fail("pdftocairo could not read the PDF")
        svg = target.read_text(errors="replace")
    # A point is 1/72 inch on paper; at 1:scale that is scale * 0.0254 / 72 m.
    metres = scale * 0.0254 / 72.0
    # The page's foot is the plan's origin: SVG's y runs down from its top.
    box = re.search(r'viewBox="([^"]*)"', svg)
    page_height = float(NUMBER.findall(box.group(1))[3]) if box else 0.0
    segments = []
    # Groups' transforms apply to what they hold; nesting is followed by a stack.
    stack = [(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)]
    for tag in re.finditer(r"<(/?)(g|path)\b([^>]*?)(/?)>", svg):
        closing, name, attributes, empty = tag.groups()
        if name == "g":
            if closing:
                if len(stack) > 1:
                    stack.pop()
            elif not empty:
                local = svg_transform((re.search(r'transform="([^"]*)"', attributes) or [None, ""])[1])
                a, b, c, d, e, f = stack[-1]
                a2, b2, c2, d2, e2, f2 = local
                stack.append((a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
                              a * e2 + c * f2 + e, b * e2 + d * f2 + f))
            continue
        data = re.search(r'\sd="([^"]*)"', attributes)
        if data is None:
            continue
        local = svg_transform((re.search(r'transform="([^"]*)"', attributes) or [None, ""])[1])
        a, b, c, d, e, f = stack[-1]
        a2, b2, c2, d2, e2, f2 = local
        matrix = (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
                  a * e2 + c * f2 + e, b * e2 + d * f2 + f)
        for first, second in path_segments(data.group(1)):
            x1, y1 = apply(matrix, *first)
            x2, y2 = apply(matrix, *second)
            segments.append((x1 * metres, (page_height - y1) * metres, x2 * metres, (page_height - y2) * metres))
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("drawing", type=Path)
    parser.add_argument("--scale", type=float, default=100.0, help="a PDF's scale, 1:SCALE")
    arguments = parser.parse_args()
    path = arguments.drawing
    if not path.exists():
        fail(f"no file {path}")
    suffix = path.suffix.lower()
    if suffix == ".dxf":
        segments = read_dxf(path)
    elif suffix == ".dwg":
        segments = read_dwg(path)
    elif suffix == ".pdf":
        segments = read_pdf(path, arguments.scale)
    else:
        fail("only DXF, DWG and PDF drawings are read")
    print("bimlines 1")
    for x1, y1, x2, y2 in segments:
        if math.hypot(x2 - x1, y2 - y1) > 1e-6:
            print(f"l {x1:.6f} {y1:.6f} {x2:.6f} {y2:.6f}")


if __name__ == "__main__":
    main()
