#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Checks an IFC4 file the framing tests write (framing-editor.ifc,
connections.ifc, rebar.ifc) with IfcOpenShell: every beam, column, plate,
fastener and reinforcing bar has a closed body whose volume IfcOpenShell
computes from its own geometry, the members carry their profile as
ObjectType and are associated with a material, every bar has a diameter, a
section, a length and a type, and every element is contained in a storey.

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
    members = ("IfcBeam", "IfcColumn", "IfcMember")
    for kind in members + ("IfcPlate", "IfcMechanicalFastener", "IfcReinforcingBar"):
        elements = model.by_type(kind)
        counts[kind] = len(elements)
        bars = {}
        for element in elements:
            shape = ifcopenshell.geom.create_shape(settings, element)
            volume = ifcopenshell.util.shape.get_volume(shape.geometry)
            if volume <= 0.0:
                failures.append(f"{element.Name}: volume {volume}")
            if not ifcopenshell.util.element.get_container(element):
                failures.append(f"{element.Name}: not contained in a storey")
            if kind in members:
                if not ifcopenshell.util.element.get_material(element):
                    failures.append(f"{element.Name}: no material")
                if not element.ObjectType:
                    failures.append(f"{element.Name}: no profile in ObjectType")
            if kind == "IfcReinforcingBar":
                if not (element.NominalDiameter and element.CrossSectionArea and element.BarLength):
                    failures.append(f"{element.Name}: bar without diameter, section or length")
                if element.PredefinedType not in ("MAIN", "LIGATURE"):
                    failures.append(f"{element.Name}: bar type {element.PredefinedType}")
                key = (element.Name, element.PredefinedType)
                bars[key] = bars.get(key, 0) + 1
            else:
                print(f"{kind} {element.Name} {element.ObjectType} volume {volume:.6f}")
        for (name, bar_type), count in sorted(bars.items()):
            print(f"{kind} {name} {bar_type} x {count}")
    print("counts", counts)
    if failures:
        print("FAIL")
        for failure in failures:
            print(" ", failure)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
