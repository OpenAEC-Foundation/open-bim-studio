#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Rasterizes the slice's interface icons from the OpenAEC Style Repo.

The editor draws its icons from `icons/ui-icons.txt`: per icon, size and part
one line of coverage bytes (00 to ff, row by row), which the editor colours
by its theme. General commands come from the B2 icon set (filled outlines,
a primary part and an accent part, 16 and 24 pixel masters); building
elements, for which B2 has no icons yet, from the BIM drafts (1.75 pixel
strokes on a 24 grid). Both are CC BY-SA 4.0, see `icons/README.md`.

    make_ui_icons.py STYLE_REPO OUT.txt

Pure Python, no imaging library: fills are sampled 8 x 8 per pixel with the
even-odd rule, strokes as round-capped lines at the same sampling.
"""
import math
import re
import sys
from pathlib import Path

SAMPLES = 8
SIZES = (16, 22)

# Glyph number (as `bim icon ...` in bim_ui.dl), name, source: "b2:<id>" or
# "bim:<draft>".
ICONS = [
    (0, "select", "b2:edit.select"),
    (1, "wall", "bim:wall"),
    (2, "floor", "bim:slab"),
    (3, "roof", "bim:roof"),
    (4, "window", "bim:window"),
    (5, "door", "bim:door"),
    (6, "opening", "bim:opening"),
    (7, "grid", "bim:grid"),
    (8, "column", "bim:column"),
    (9, "beam", "bim:beam"),
    (10, "section", "bim:section"),
    (11, "cube", "b2:view.orbit"),
    (12, "eye", "b2:object.show"),
    (13, "table", "b2:data.table"),
    (14, "layers", "b2:object.layers"),
    (15, "fit", "b2:view.fit"),
    (16, "undo", "b2:edit.undo"),
    (17, "redo", "b2:edit.redo"),
    (18, "delete", "b2:edit.delete"),
    (19, "save", "b2:file.save"),
    (20, "open", "b2:file.open"),
    (21, "export", "b2:file.export"),
    (22, "up", "b2:layer.raise"),
    (23, "down", "b2:layer.lower"),
    (24, "move", "b2:transform.move"),
    (25, "text", "b2:draw.text"),
    (26, "dimension", "b2:draw.dimension"),
    (27, "facade", "bim:curtain-wall"),
    (28, "line", "b2:draw.line"),
    (29, "rectangle", "b2:draw.rectangle"),
    (30, "push", "b2:transform.stretch"),
    (31, "component", "bim:instance"),
    (32, "place", "bim:viewport"),
    (33, "explode", "b2:transform.explode"),
    (34, "copy", "b2:edit.copy"),
    (35, "rotate", "b2:transform.rotate"),
    (36, "mirror", "b2:transform.mirror"),
    (37, "trim", "b2:transform.trim"),
    (38, "extend", "b2:transform.extend"),
    (39, "offset", "b2:transform.offset"),
    (40, "align", "bim:align"),
    (41, "zoom", "b2:view.zoom-in"),
    (42, "back", "b2:nav.back"),
    (43, "stair", "bim:stair"),
    (44, "railing", "bim:railing"),
    (45, "schedule", "bim:schedule"),
    (46, "sheet", "bim:sheet"),
    (47, "tag", "bim:tag"),
    (48, "level", "bim:level"),
    (49, "storey", "bim:storey"),
    (50, "clip box", "bim:section-box"),
    (51, "plan", "bim:plan"),
    (52, "elevation", "bim:elevation"),
    (53, "type", "bim:type"),
    (54, "property set", "bim:property-set"),
    (55, "ifc import", "b2:ifc.import"),
    (56, "ifc export", "b2:ifc.export"),
    (57, "cut", "b2:edit.cut"),
    (58, "import", "b2:file.import"),
    (59, "settings", "b2:ui.settings"),
    (60, "hide", "b2:object.hide"),
    (61, "detail", "bim:detail"),
    (62, "space", "bim:space"),
    (63, "array", "b2:transform.array"),
    (64, "phasing", "bim:phasing"),
    (65, "clash", "bim:clash"),
    (66, "scale", "b2:transform.scale"),
    (67, "pile", "bim:pile"),
    (68, "zone", "bim:zone"),
    (69, "new", "b2:file.new"),
    (70, "properties", "b2:object.properties"),
    (71, "measure", "b2:measure.distance"),
    (72, "polyline", "b2:draw.polyline"),
    (73, "circle", "b2:draw.circle"),
    (74, "arc", "b2:draw.arc"),
    (75, "search", "b2:view.search"),
    (76, "help", "b2:ui.help"),
    (77, "panel left", "b2:panel.left"),
    (78, "panel right", "b2:panel.right"),
    (79, "join", "bim:join"),
    (80, "link", "bim:link-model"),
    (81, "ids", "bim:ids-check"),
    (82, "classification", "bim:classification"),
    (83, "project origin", "bim:project-origin"),
    (84, "site", "bim:site"),
    (85, "footing", "bim:footing"),
    (86, "material", "bim:material-layers"),
    (87, "quantity", "bim:quantity"),
    (88, "revision", "bim:revision"),
    (89, "ramp", "bim:ramp"),
]

NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOKEN = re.compile(r"[MmLlHhVvZzCcSsQqAa]|" + NUMBER.pattern)


def flatten_path(d):
    """The subpaths of SVG path data `d` as (points, closed) lists."""
    tokens = TOKEN.findall(d)
    subpaths, points = [], []
    x = y = startx = starty = 0.0
    lastc = None
    i, command = 0, None

    def take(n):
        nonlocal i
        values = [float(t) for t in tokens[i:i + n]]
        i += n
        return values

    def close_current(closed):
        nonlocal points
        if len(points) > 1:
            subpaths.append((points, closed))
        points = []

    while i < len(tokens):
        if re.fullmatch(r"[A-Za-z]", tokens[i]):
            command = tokens[i]
            i += 1
            if command in "Zz":
                close_current(True)
                x, y = startx, starty
                lastc = None
                continue
        relative = command.islower()
        c = command.upper()
        if c == "M":
            dx, dy = take(2)
            close_current(False)
            x, y = (x + dx, y + dy) if relative else (dx, dy)
            startx, starty = x, y
            points = [(x, y)]
            command = "l" if relative else "L"
            lastc = None
        elif c == "L":
            dx, dy = take(2)
            x, y = (x + dx, y + dy) if relative else (dx, dy)
            points.append((x, y))
            lastc = None
        elif c == "H":
            (dx,) = take(1)
            x = x + dx if relative else dx
            points.append((x, y))
            lastc = None
        elif c == "V":
            (dy,) = take(1)
            y = y + dy if relative else dy
            points.append((x, y))
            lastc = None
        elif c in "CS":
            if c == "C":
                x1, y1, x2, y2, ex, ey = take(6)
                if relative:
                    x1, y1, x2, y2 = x1 + x, y1 + y, x2 + x, y2 + y
            else:
                x2, y2, ex, ey = take(4)
                if relative:
                    x2, y2 = x2 + x, y2 + y
                x1, y1 = (2 * x - lastc[0], 2 * y - lastc[1]) if lastc else (x, y)
            if relative:
                ex, ey = ex + x, ey + y
            for step in range(1, 17):
                t = step / 16
                u = 1 - t
                points.append((u**3 * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * ex,
                               u**3 * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * ey))
            lastc = (x2, y2)
            x, y = ex, ey
        elif c == "A":
            rx, ry, rotation, large, sweep, ex, ey = take(7)
            if relative:
                ex, ey = ex + x, ey + y
            points.extend(arc_points(x, y, rx, ry, rotation, large, sweep, ex, ey))
            x, y = ex, ey
            lastc = None
        else:
            raise ValueError(f"path command {command} not supported")
    close_current(False)
    return subpaths


def arc_points(x1, y1, rx, ry, rotation, large, sweep, x2, y2):
    """An SVG elliptical arc as points (endpoint parameterization)."""
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(rotation)
    cos, sin = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    xp, yp = cos * dx + sin * dy, -sin * dx + cos * dy
    rx, ry = abs(rx), abs(ry)
    scale = xp * xp / (rx * rx) + yp * yp / (ry * ry)
    if scale > 1:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    numerator = rx * rx * ry * ry - rx * rx * yp * yp - ry * ry * xp * xp
    factor = math.sqrt(max(0.0, numerator / (rx * rx * yp * yp + ry * ry * xp * xp)))
    if large == sweep:
        factor = -factor
    cxp, cyp = factor * rx * yp / ry, -factor * ry * xp / rx
    cx = cos * cxp - sin * cyp + (x1 + x2) / 2
    cy = sin * cxp + cos * cyp + (y1 + y2) / 2

    def angle(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    start = angle(1, 0, (xp - cxp) / rx, (yp - cyp) / ry)
    delta = angle((xp - cxp) / rx, (yp - cyp) / ry, (-xp - cxp) / rx, (-yp - cyp) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi
    steps = max(4, int(abs(delta) / (math.pi / 16)))
    result = []
    for step in range(1, steps + 1):
        a = start + delta * step / steps
        px, py = rx * math.cos(a), ry * math.sin(a)
        result.append((cos * px - sin * py + cx, sin * px + cos * py + cy))
    return result


def circle_points(cx, cy, r):
    return [(cx + r * math.cos(2 * math.pi * k / 64), cy + r * math.sin(2 * math.pi * k / 64)) for k in range(64)]


def attribute(tag, name, default=None):
    found = re.search(r'\s' + re.escape(name) + r'="([^"]*)"', tag)
    return found.group(1) if found else default


def fill_coverage(polygons, size, scale):
    """Per pixel the share of samples inside `polygons` (even-odd)."""
    edges = []
    for points in polygons:
        for k in range(len(points)):
            (ax, ay), (bx, by) = points[k], points[(k + 1) % len(points)]
            if ay != by:
                edges.append((ax * scale, ay * scale, bx * scale, by * scale))
    counts = [0] * (size * size)
    for row in range(size * SAMPLES):
        sy = (row + 0.5) / SAMPLES
        crossings = []
        for ax, ay, bx, by in edges:
            if (ay <= sy) != (by <= sy):
                crossings.append(ax + (sy - ay) * (bx - ax) / (by - ay))
        crossings.sort()
        pixel_row = (row // SAMPLES) * size
        for k in range(0, len(crossings) - 1, 2):
            first = max(0, math.ceil(crossings[k] * SAMPLES - 0.5))
            last = min(size * SAMPLES - 1, math.ceil(crossings[k + 1] * SAMPLES - 0.5) - 1)
            for sample in range(first, last + 1):
                counts[pixel_row + sample // SAMPLES] += 1
    return counts


def stroke_coverage(lines, width, size, scale):
    """Per pixel the share of samples within `width` / 2 of `lines`."""
    half = width * scale / 2
    segments = []
    for points, closed in lines:
        pts = [(x * scale, y * scale) for x, y in points]
        if closed:
            pts.append(pts[0])
        segments.extend(zip(pts, pts[1:]))
    counts = [0] * (size * size)
    for py in range(size):
        for px in range(size):
            near = [s for s in segments
                    if min(s[0][0], s[1][0]) - half <= px + 1 and max(s[0][0], s[1][0]) + half >= px
                    and min(s[0][1], s[1][1]) - half <= py + 1 and max(s[0][1], s[1][1]) + half >= py]
            if not near:
                continue
            count = 0
            for sy in range(SAMPLES):
                for sx in range(SAMPLES):
                    x, y = px + (sx + 0.5) / SAMPLES, py + (sy + 0.5) / SAMPLES
                    for (ax, ay), (bx, by) in near:
                        vx, vy = bx - ax, by - ay
                        length = vx * vx + vy * vy
                        t = 0.0 if length == 0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / length))
                        if (x - ax - t * vx) ** 2 + (y - ay - t * vy) ** 2 <= half * half:
                            count += 1
                            break
            counts[py * size + px] = count
    return counts


def merge(a, b):
    return [max(x, y) for x, y in zip(a, b)]


def b2_parts(repo, name, size):
    master = 16 if size <= 16 else 24
    text = (repo / "design/icon-set-b2/svg" / str(master) / f"{name}.svg").read_text()
    parts = {}
    for tag in re.findall(r"<path\b[^>]*>", text):
        polygons = [points for points, _ in flatten_path(attribute(tag, "d", ""))]
        part = attribute(tag, "data-part", "primary")
        coverage = fill_coverage(polygons, size, size / master)
        parts[part] = merge(parts[part], coverage) if part in parts else coverage
    return parts


def draft_parts(repo, name, size):
    text = (repo / "design/icon-drafts/bim" / f"{name}.svg").read_text()
    root = re.search(r"<svg\b[^>]*>", text).group(0)
    width = float(attribute(root, "stroke-width", "1.75"))
    scale = size / 24
    # A 16 pixel icon keeps a stroke of at least 1.25 pixels.
    width = max(width, 1.25 / scale)
    total = [0] * (size * size)
    for tag in re.findall(r"<(?:path|circle)\b[^>]*>", text):
        if tag.startswith("<circle"):
            shapes = [(circle_points(float(attribute(tag, "cx")), float(attribute(tag, "cy")), float(attribute(tag, "r"))), True)]
        else:
            shapes = flatten_path(attribute(tag, "d", ""))
        fill = attribute(tag, "fill", attribute(root, "fill", "none"))
        stroke = attribute(tag, "stroke", attribute(root, "stroke", "none"))
        if fill != "none":
            total = merge(total, fill_coverage([points for points, _ in shapes], size, scale))
        if stroke != "none":
            total = merge(total, stroke_coverage(shapes, width, size, scale))
    return {"primary": total}


def main():
    repo, out = Path(sys.argv[1]), Path(sys.argv[2])
    full = SAMPLES * SAMPLES
    lines = [
        "# Interface icons of the BIM slice, made by tools/make_ui_icons.py from the",
        "# OpenAEC Style Repo (CC BY-SA 4.0, see README.md here). One line per icon,",
        "# size and part: glyph size part coverage, the coverage one hex byte per",
        "# pixel, row by row; part 0 is the primary colour, 1 the accent.",
    ]
    for glyph, name, source in ICONS:
        kind, source_name = source.split(":")
        for size in SIZES:
            parts = b2_parts(repo, source_name, size) if kind == "b2" else draft_parts(repo, source_name, size)
            for part_name, part in (("primary", 0), ("accent", 1)):
                counts = parts.get(part_name)
                if counts is None or not any(counts):
                    continue
                coverage = "".join(f"{min(255, round(255 * c / full)):02x}" for c in counts)
                lines.append(f"{glyph} {size} {part} {coverage}")
        print(f"{glyph:3} {name:15} {source}", file=sys.stderr)
    out.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
