#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Validate already-generated DynLex IFC4/IFC4.3 fixtures; never compile."""
import argparse
import math
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.validate
from verify_ifc import mesh_volume

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("ifc43")
parser.add_argument("ifc4")
args = parser.parse_args()
new = ifcopenshell.open(args.ifc43)
old = ifcopenshell.open(args.ifc4)
assert new.schema_identifier == "IFC4X3_ADD2", new.schema_identifier
assert old.schema == "IFC4", old.schema
logger = ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(new, logger, express_rules=True)
if logger.statements:
    for issue in logger.statements:
        print(issue)
    raise SystemExit("FAIL: IFC4.3 schema validation")
classes = ("IfcWall", "IfcSlab", "IfcBeam", "IfcWindow", "IfcOpeningElement", "IfcBuildingStorey",
           "IfcMaterialLayerSet", "IfcRelVoidsElement", "IfcRelFillsElement", "IfcGrid")
for kind in classes:
    assert len(new.by_type(kind)) == len(old.by_type(kind)), kind
old_guids = {entity.GlobalId for entity in old.by_type("IfcRoot")}
new_guids = [entity.GlobalId for entity in new.by_type("IfcRoot")]
assert len(new_guids) == len(set(new_guids))
assert set(new_guids) == old_guids
settings = ifcopenshell.geom.settings()
settings.set("use-world-coords", True)
assert new.by_type("IfcCartesianPointList3D"), "fixture must exercise tessellation"
for element in new.by_type("IfcWall") + new.by_type("IfcSlab") + new.by_type("IfcBeam"):
    reference = old.by_guid(element.GlobalId)
    actual = mesh_volume(ifcopenshell.geom.create_shape(settings, element))
    expected = mesh_volume(ifcopenshell.geom.create_shape(settings, reference))
    assert actual > 0 and abs(actual - expected) <= max(1e-7, expected * 1e-6), (element, actual, expected)
    if element.is_a("IfcSlab"):
        # Independent dimensions of the L-shaped fixture: 20.4768 m2,
        # less its 1 m2 opening, 250 mm thick; top offset 500 mm, pitch .1 rad.
        assert abs(actual - 4.8692) < 1e-6, actual
        shape = ifcopenshell.geom.create_shape(settings, element)
        heights = shape.geometry.verts[2::3]
        assert abs(min(heights) - 0.25) < 1e-6, min(heights)
        assert abs(max(heights) - (0.5 + math.tan(0.1) * 6.32)) < 1e-6, max(heights)
print("PASS: IFC4.3 schema, identifiers, relationships and geometry match the IFC4 reference")
