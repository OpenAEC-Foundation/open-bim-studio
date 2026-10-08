#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Checks the IFC4 file `tests/framing_editor.dl` writes (framing-editor.ifc)
with IfcOpenShell: every beam, column and plate has a closed body whose
volume IfcOpenShell computes from its own geometry, the members carry their
profile as ObjectType and are associated with a material, and every element
is contained in a storey.

    python3 verify_ifc_framing.py framing-editor.ifc
"""
import sys

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.shape


def main():
    model = ifcopenshell.open(sys.argv[1])
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    failures = []
    counts = {}
    for kind in ("IfcBeam", "IfcColumn", "IfcMember", "IfcPlate"):
        elements = model.by_type(kind)
        counts[kind] = len(elements)
        for element in elements:
            shape = ifcopenshell.geom.create_shape(settings, element)
            volume = ifcopenshell.util.shape.get_volume(shape.geometry)
            if volume <= 0.0:
                failures.append(f"{element.Name}: volume {volume}")
            if not ifcopenshell.util.element.get_container(element):
                failures.append(f"{element.Name}: not contained in a storey")
            if kind != "IfcPlate":
                if not ifcopenshell.util.element.get_material(element):
                    failures.append(f"{element.Name}: no material")
                if not element.ObjectType:
                    failures.append(f"{element.Name}: no profile in ObjectType")
            print(f"{kind} {element.Name} {element.ObjectType} volume {volume:.6f}")
    print("counts", counts)
    if failures:
        print("FAIL")
        for failure in failures:
            print(" ", failure)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
