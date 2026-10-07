#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check the slice's IFC4 export independently with IfcOpenShell.

Builds and runs `tests/ifc.dl`, which prints the native wall and slab volumes
and writes the IFC file, then re-reads the file and compares structure and the
volume of every wall, with its openings subtracted by IfcOpenShell's own
geometry engine, and of every slab.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.guid

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def run(command, timeout=2400):
    done = subprocess.run([str(item) for item in command], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if done.returncode:
        raise SystemExit(f"exit {done.returncode}: {command}\n{done.stdout}{done.stderr}")
    return done.stdout


def mesh_volume(shape) -> float:
    verts = shape.geometry.verts
    faces = shape.geometry.faces
    total = 0.0
    for index in range(0, len(faces), 3):
        a, b, c = (faces[index + offset] * 3 for offset in range(3))
        ax, ay, az = verts[a:a + 3]
        bx, by, bz = verts[b:b + 3]
        cx, cy, cz = verts[c:c + 3]
        total += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6.0
    return abs(total)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=ROOT / "build/dynlex")
    parser.add_argument("--optimization", default="O0", choices=("O0", "O2"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as scratch:
        binary = Path(scratch) / "ifc-export"
        diagnostics = run([args.compiler.resolve(), HERE / "ifc.dl", f"-{args.optimization}", "-o", binary])
        if diagnostics.strip():
            raise SystemExit(f"native diagnostics:\n{diagnostics}")
        ifc_path = Path(scratch) / "slice.ifc"
        output = run([binary, ifc_path], timeout=300)
        native = {"wall": {}, "slab": {}}
        for line in output.splitlines():
            if line.startswith("native "):
                _, kind, element_id, volume = line.split()
                native[kind][int(element_id)] = float(volume)
        check(output.strip().endswith("written"), "the native export reported success")
        model = ifcopenshell.open(str(ifc_path))
        check(model.schema == "IFC4", f"schema {model.schema}")
        counts = {kind: len(model.by_type(kind)) for kind in (
            "IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcWallType", "IfcWall",
            "IfcOpeningElement", "IfcWindow", "IfcRelVoidsElement", "IfcRelFillsElement", "IfcMaterialLayerSet", "IfcSpace", "IfcSlab", "IfcGrid", "IfcGridAxis")}
        print("counts " + " ".join(f"{kind}={count}" for kind, count in counts.items()))
        check(counts["IfcWall"] == len(native["wall"]) == 6, "six walls")
        check(counts["IfcBuildingStorey"] == 2, "two storeys")
        check(counts["IfcSlab"] == len(native["slab"]) == 1, "one slab")
        check(counts["IfcOpeningElement"] == counts["IfcWindow"] == counts["IfcRelVoidsElement"] == counts["IfcRelFillsElement"] == 3, "three filled openings, one in the curved upper wall")
        guids = [entity.GlobalId for entity in model.by_type("IfcRoot")]
        check(len(guids) == len(set(guids)), "GlobalIds are unique")
        for guid in guids:
            check(len(ifcopenshell.guid.expand(guid)) == 32, f"GlobalId {guid} expands")
        storeys = {entity.Name: entity for entity in model.by_type("IfcBuildingStorey")}
        storey = storeys["Ground floor"]
        upper = storeys["First floor"]
        check(abs(upper.Elevation - 3.0) <= 1e-12, f"first floor elevation {upper.Elevation}")

        def contents(of):
            return {element.id() for rel in of.ContainsElements for element in rel.RelatedElements}

        contained = contents(storey)
        upper_contained = contents(upper)
        check(not contained & upper_contained, "no element is in both storeys")
        for wall in model.by_type("IfcWall"):
            check(wall.id() in contained | upper_contained, f"{wall.Name} is contained in a storey")
            types = [rel.RelatingType for rel in wall.IsTypedBy]
            check(len(types) == 1 and types[0].is_a("IfcWallType"), f"{wall.Name} has one wall type")
            usages = [rel.RelatingMaterial for rel in wall.HasAssociations if rel.is_a("IfcRelAssociatesMaterial")]
            check(len(usages) == 1 and usages[0].is_a("IfcMaterialLayerSetUsage"), f"{wall.Name} has a layer set usage")
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", True)
        compared = 0
        for wall in model.by_type("IfcWall"):
            wall_id = int(wall.Name.split()[-1])
            shape = ifcopenshell.geom.create_shape(settings, wall)
            volume = mesh_volume(shape)
            heights = shape.geometry.verts[2::3]
            # The first-floor wall is the only one on that storey, from 3 m to 6 m.
            expected_floor = 3.0 if wall.id() in upper_contained else 0.0
            check(abs(min(heights) - expected_floor) <= 1e-9 and abs(max(heights) - expected_floor - 3.0) <= 1e-9, f"wall {wall_id} spans {min(heights)} to {max(heights)}")
            difference = abs(volume - native["wall"][wall_id])
            print(f"wall {wall_id} ifc {volume:.6f} native {native['wall'][wall_id]:.6f}")
            check(difference <= 1e-6, f"wall {wall_id} volume differs by {difference}")
            compared += 1
        # The L-shaped slab: 6.32 m x 2.16 m plus 3.16 m x 2.16 m, 0.25 m thick,
        # with its top at the storey's elevation.
        for slab in model.by_type("IfcSlab"):
            slab_id = int(slab.Name.split()[-1])
            check(slab.id() in contained, f"{slab.Name} is contained in the storey")
            check(slab.PredefinedType == "FLOOR", f"{slab.Name} is a floor")
            shape = ifcopenshell.geom.create_shape(settings, slab)
            volume = mesh_volume(shape)
            heights = shape.geometry.verts[2::3]
            print(f"slab {slab_id} ifc {volume:.6f} native {native['slab'][slab_id]:.6f}")
            check(abs(volume - native["slab"][slab_id]) <= 1e-6, f"slab {slab_id} volume differs")
            check(abs(volume - (6.32 * 2.16 + 3.16 * 2.16) * 0.25) <= 1e-6, f"slab {slab_id} volume {volume}")
            check(abs(max(heights)) <= 1e-9 and abs(min(heights) + 0.25) <= 1e-9, f"slab {slab_id} spans {min(heights)} to {max(heights)}")
            compared += 1
        upper_kinds = sorted(model.by_id(number).is_a() for number in upper_contained)
        check(upper_kinds == ["IfcWall", "IfcWindow"], f"the first floor holds its curved wall and its window: {upper_kinds}")
        # One grid: the numbered lines as V axes, the lettered as U axes.
        check(counts["IfcGrid"] == 1 and counts["IfcGridAxis"] == 3, "one grid of three axes")
        grid = model.by_type("IfcGrid")[0]
        check(sorted(axis.AxisTag for axis in grid.VAxes) == ["1", "2"], "numbered V axes")
        check([axis.AxisTag for axis in grid.UAxes] == ["A"], "lettered U axis")
        check(grid.id() in contained, "the grid is contained in the ground floor")
        first_axis = next(axis for axis in grid.VAxes if axis.AxisTag == "2")
        check([tuple(point.Coordinates) for point in first_axis.AxisCurve.Points] == [(6.0, -1.0), (6.0, 5.0)], "axis 2 runs from (6, -1) to (6, 5)")
        # The two rooms either side of the partition: 2.79 m x 3.68 m clear,
        # extruded over the 3 m storey height.
        check(counts["IfcSpace"] == 2, "two spaces")
        for space in model.by_type("IfcSpace"):
            check(any(rel.RelatingObject == storey for rel in space.Decomposes), f"{space.Name} belongs to the storey")
            volume = mesh_volume(ifcopenshell.geom.create_shape(settings, space))
            print(f"space {space.Name} ifc volume {volume:.6f}")
            check(abs(volume - 2.79 * 3.68 * 3.0) <= 1e-6, f"{space.Name} volume {volume}")
        print(f"PASS: IFC4 structure, {compared} wall and slab volumes and {counts['IfcSpace']} space volumes match ({args.optimization})")


if __name__ == "__main__":
    main()
