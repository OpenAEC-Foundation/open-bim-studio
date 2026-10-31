#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Validate the Dutch type catalogue (localisation/nl/types/catalogue.json) and
that ui/editor/bim_inb_types.dl is generated from it. Data checks only: the
catalogue's thicknesses are the template's, not a building design."""
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import inb_type_catalogue  # noqa: E402

# The IFC4 predefined types of the four type classes the catalogue holds.
PREDEFINED = {
    "IfcWallType": set("MOVABLE PARAPET PARTITIONING PLUMBINGWALL SHEAR SOLIDWALL STANDARD POLYGONAL "
                       "ELEMENTEDWALL RETAININGWALL WAVEWALL USERDEFINED NOTDEFINED".split()),
    "IfcSlabType": set("FLOOR ROOF LANDING BASESLAB APPROACH_SLAB PAVING WEARING SIDEWALK USERDEFINED NOTDEFINED".split()),
    "IfcColumnType": set("COLUMN PILASTER PIERSTEM PIERSTEM_SEGMENT STANDCOLUMN USERDEFINED NOTDEFINED".split()),
    "IfcBeamType": set("BEAM JOIST HOLLOWCORE LINTEL SPANDREL T_BEAM GIRDER_SEGMENT DIAPHRAGM PIERCAP "
                       "HATSTONE CORNICE EDGEBEAM USERDEFINED NOTDEFINED".split()),
}


def validate(data):
    errors = []

    def require(condition, location, message):
        if not condition:
            errors.append(f"{location}: {message}")

    def length(value, location):
        require(type(value) in (int, float) and math.isfinite(value) and 0.0 < value <= 2.0, location, "a length in metres above 0 and at most 2")

    required = {"schema_version", "catalogue_id", "units", "language", "status", "source", "materials", "types", "excluded"}
    if not isinstance(data, dict) or not required <= data.keys():
        return [f"catalogue: missing fields {sorted(required - set(data))}" if isinstance(data, dict) else "catalogue: expected object"]
    require(data["schema_version"] == 1 and data["units"] == "m", "catalogue", "unsupported schema or units")
    source = data["source"]
    require(isinstance(source, dict) and str(source.get("repository", "")).startswith("https://"), "source", "repository URL required")
    require(isinstance(source, dict) and bool(re.fullmatch(r"[0-9a-f]{40}", str(source.get("commit", "")))), "source", "the template's full commit required")
    materials = data["materials"]
    require(isinstance(materials, dict) and materials == inb_type_catalogue.MATERIALS, "materials", "differ from the mapping in tools/inb_type_catalogue.py")
    seen = set()
    for index, record in enumerate(data["types"]):
        where = f"types[{index}]"
        if not isinstance(record, dict) or not {"name", "ifc_class", "predefined_type", "role"} <= record.keys():
            errors.append(f"{where}: expected name, ifc_class, predefined_type and role")
            continue
        where = f"{record['ifc_class']} {record['name']}"
        require(isinstance(record["name"], str) and record["name"] and not re.search(r'["\\\n]', record["name"]), where, "name must be plain text")
        require(record["ifc_class"] in PREDEFINED, where, "unknown IFC class")
        require(record["predefined_type"] in PREDEFINED.get(record["ifc_class"], ()), where, "not a predefined type of its class")
        require(record["role"] == inb_type_catalogue.role_of(record["ifc_class"], record["predefined_type"]), where, "role disagrees with class and predefined type")
        imported = "not_imported" not in record
        if record["ifc_class"] in ("IfcWallType", "IfcSlabType"):
            layers = record.get("layers")
            require(isinstance(layers, list) and (bool(layers) or not imported), where, "layers required (or a not_imported reason)")
            for number, layer in enumerate(layers or []):
                require(materials.get(layer.get("template_material")) == layer.get("material"), f"{where} layer {number}", "material not mapped")
                length(layer.get("thickness_m"), f"{where} layer {number}")
        else:
            profile = record.get("profile")
            require(isinstance(profile, dict) and imported, where, "a member needs its profile")
            if isinstance(profile, dict):
                require(materials.get(profile.get("template_material")) == profile.get("material"), where, "material not mapped")
                require(profile.get("template_material") not in inb_type_catalogue.STEEL, where, "steel series belong to the profile catalogue")
                length(profile.get("width_m"), f"{where} width")
                length(profile.get("depth_m"), f"{where} depth")
                require(not profile.get("round") or profile.get("width_m") == profile.get("depth_m"), where, "a round profile has one diameter")
        if imported:
            key = (record["role"], record["name"])
            require(key not in seen, where, "two types of one role share a name")
            seen.add(key)
    for record in data["excluded"]:
        require(isinstance(record, dict) and bool(record.get("reason")), "excluded", "every exclusion needs its reason")
    return errors


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else inb_type_catalogue.CATALOGUE
    try:
        data = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite {value}")))
        errors = validate(data)
        if not errors and len(sys.argv) <= 1:
            generated = inb_type_catalogue.GENERATED
            if generated.read_text(encoding="utf-8") != inb_type_catalogue.generate(data):
                errors.append(f"{generated.relative_to(ROOT)}: out of date; run python3 -I tools/inb_type_catalogue.py generate")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Invalid catalogue: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    imported = [t for t in data["types"] if "not_imported" not in t]
    print(f"PASS: {len(imported)} types imported of {len(data['types'])}, {len(data['excluded'])} excluded; "
          f"template {data['source']['commit'][:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
