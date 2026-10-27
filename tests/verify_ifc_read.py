#!/usr/bin/env python3
"""Compares the boxes the DynLex IFC reader found per element (build/X.elements.txt:
label|triangles|lowx|lowy|lowz|highx|highy|highz, the label "<Class> <GlobalId> <Name>")
with IfcOpenShell's geometry of the same element (world coordinates, metres).

    verify_ifc_read.py MODEL.ifc MODEL.elements.txt [--openings]

With --openings IfcOpenShell cuts the openings too, as the reader does for
hosts made of extrusions.
"""
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np

model = ifcopenshell.open(sys.argv[1])
ours = {}
for line in open(sys.argv[2]):
    parts = line.rstrip("\n").split("|")
    if len(parts) < 8:
        continue
    label = parts[0].split(" ")
    area = float(parts[8]) if len(parts) > 8 else None
    ours[label[1]] = (label[0], int(parts[1]), np.array([float(v) for v in parts[2:5]]), np.array([float(v) for v in parts[5:8]]), area)
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, "--openings" not in sys.argv)
theirs = {}
iterator = ifcopenshell.geom.iterator(settings, model)
if iterator.initialize():
    while True:
        shape = iterator.get()
        element = model.by_guid(shape.guid)
        verts = np.array(shape.geometry.verts).reshape(-1, 3)
        if len(verts) and not element.is_a("IfcOpeningElement") and not element.is_a("IfcSpace"):
            tris = verts[np.array(shape.geometry.faces).reshape(-1, 3)]
            area = 0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum()
            theirs[shape.guid] = (element.is_a(), len(shape.geometry.faces) // 3, verts.min(0), verts.max(0), area)
        if not iterator.next():
            break
both = set(ours) & set(theirs)
only_theirs = set(theirs) - set(ours)
only_ours = set(ours) - set(theirs)
worst = []
for guid in both:
    a, b = ours[guid], theirs[guid]
    error = max(np.abs(a[2] - b[2]).max(), np.abs(a[3] - b[3]).max())
    worst.append((error, guid, b[0]))
worst.sort(reverse=True)
close = sum(1 for e, _, _ in worst if e < 0.002)
print(f"{len(ours)} elements read, IfcOpenShell {len(theirs)}; {len(both)} in both, {close} boxes within 2 mm")
from collections import Counter
print("only IfcOpenShell:", dict(Counter(theirs[g][0] for g in only_theirs)))
print("only ours:", dict(Counter(ours[g][0] for g in only_ours)))
areas = [(abs(ours[g][4] - theirs[g][4]) / max(theirs[g][4], 1e-9), g) for g in both if ours[g][4] is not None]
areas.sort(reverse=True)
print(f"surface areas within 1%: {sum(1 for e, _ in areas if e < 0.01)} of {len(areas)}")
for error, guid in areas[:8]:
    if error >= 0.01:
        print(f"  area {error * 100:.1f}%  {theirs[guid][0]} {guid}  ours {ours[guid][4]:.3f}  theirs {theirs[guid][4]:.3f} m2")
for error, guid, kind in worst[:12]:
    if error >= 0.002:
        print(f"  {error * 1000:.0f} mm  {kind} {guid}  ours {ours[guid][2].round(3)}..{ours[guid][3].round(3)}  theirs {theirs[guid][2].round(3)}..{theirs[guid][3].round(3)}")
