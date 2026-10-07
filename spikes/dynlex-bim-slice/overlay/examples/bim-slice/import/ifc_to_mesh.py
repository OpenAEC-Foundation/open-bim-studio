#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Convert an IFC file into a BIM-MESH file the BIM slice can open.

This is the first step of the slice's IFC import: IfcOpenShell triangulates the
model, and the slice reads the triangles. A later step replaces it with a DynLex
IFC library.

The output is little-endian binary:

    magic        8 bytes  b"BIMMESH1"
    count        u32      number of elements
    per element:
      category   u32      the slice's category code (bim_view.dl)
      label      u32 n, then n bytes of UTF-8: "<IFC class> <GlobalId> <Name>"
      vertices   u32 v, then v x 3 f64: world x, y, z in metres
      triangles  u32 t, then t x 3 u32: vertex indices, counter-clockwise
                                         seen from outside

Coordinates stay in binary64, so models far from the origin keep their precision.
"""
from __future__ import annotations

import argparse
import multiprocessing
from pathlib import Path
import struct
import sys
import time

import ifcopenshell
import ifcopenshell.geom

# The slice's categories (bim_view.dl). Classes not listed are "other".
CATEGORIES = {
    "IfcWall": 0, "IfcWallStandardCase": 0, "IfcCurtainWall": 0, "IfcPlate": 0,
    "IfcSlab": 1, "IfcCovering": 1,
    "IfcDoor": 2,
    "IfcWindow": 3,
    "IfcSpace": 4,
    "IfcGrid": 5,
    "IfcColumn": 7,
    "IfcBeam": 8, "IfcMember": 8,
    "IfcRoof": 9,
    "IfcStair": 10, "IfcStairFlight": 10, "IfcRamp": 10, "IfcRampFlight": 10,
    "IfcRailing": 11,
    "IfcFurnishingElement": 12, "IfcFurniture": 12,
}
OTHER = 13

# Not drawn: voids, annotation, and the spatial structure itself.
SKIPPED = ("IfcOpeningElement", "IfcAnnotation", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcVirtualElement")


def category_of(ifc_class: str) -> int:
    return CATEGORIES.get(ifc_class, OTHER)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--threads", type=int, default=multiprocessing.cpu_count())
    args = parser.parse_args()

    started = time.time()
    model = ifcopenshell.open(str(args.source))
    opened = time.time()
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    elements = [product for product in model.by_type("IfcProduct")
                if product.Representation is not None and not product.is_a() in SKIPPED]
    iterator = ifcopenshell.geom.iterator(settings, model, args.threads, include=elements)
    records = []
    vertex_total = 0
    triangle_total = 0
    failures = 0
    if iterator.initialize():
        while True:
            shape = iterator.get()
            element = model.by_id(shape.id)
            vertices = shape.geometry.verts
            faces = shape.geometry.faces
            if len(vertices) >= 9 and len(faces) >= 3:
                label = f"{element.is_a()} {element.GlobalId} {element.Name or ''}".encode("utf-8")
                records.append((category_of(element.is_a()), label, vertices, faces))
                vertex_total += len(vertices) // 3
                triangle_total += len(faces) // 3
            if not iterator.next():
                break
    failures = len(elements) - len(records)
    meshed = time.time()

    with open(args.target, "wb") as stream:
        stream.write(b"BIMMESH1")
        stream.write(struct.pack("<I", len(records)))
        for category, label, vertices, faces in records:
            stream.write(struct.pack("<II", category, len(label)))
            stream.write(label)
            stream.write(struct.pack("<I", len(vertices) // 3))
            stream.write(struct.pack(f"<{len(vertices)}d", *vertices))
            stream.write(struct.pack("<I", len(faces) // 3))
            stream.write(struct.pack(f"<{len(faces)}I", *faces))
    written = time.time()
    print(f"{args.source.name}: {len(records)} elements, {vertex_total} vertices, {triangle_total} triangles; "
          f"{failures} products without a mesh")
    print(f"open {opened - started:.1f} s, triangulate {meshed - opened:.1f} s ({args.threads} threads), "
          f"write {written - meshed:.1f} s; {args.target.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
