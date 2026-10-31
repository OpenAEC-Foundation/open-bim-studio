#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""The Dutch type catalogue from the INB template of OpenAEC.

  inb_type_catalogue.py extract TEMPLATE.ifc --commit SHA [--out JSON]
      reads the wall, slab, column and beam types of the template (an IFC
      STEP file) and writes localisation/nl/types/catalogue.json: every wall
      and slab type with its material layers, and the column and beam types
      of a solid rectangular or round profile that is not steel (the steel
      series are listed as excluded; they follow the profile catalogue).
  inb_type_catalogue.py generate [--catalogue JSON] [--out DL]
      writes ui/editor/bim_inb_types.dl, the catalogue as DynLex, which the
      editor's type library loads (the application reads no data files at
      run time, so the catalogue is compiled in).

Thicknesses and profile sizes are metres, rounded to a tenth of a millimetre
(the template holds single-precision noise such as 220.000015258789 mm). The
template's material names map to the application's through MATERIALS; a
material missing there stops the extraction. Treat the template as untrusted
input: run this with `python3 -I`.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "localisation/nl/types/catalogue.json"
GENERATED = ROOT / "ui/editor/bim_inb_types.dl"
REPOSITORY = "https://github.com/OpenAEC-Foundation/inb-template"
TEMPLATE_FILE = "INB-Template 0.6.ifc"

# The template's material names and the application's materials they become
# (the application names materials in English; `the bim dutch name of
# material` in bim/bim_model.dl and the hatches recognise these words).
MATERIALS = {
    "bekledingsplaatmultiplex": "timber plywood",
    "generiek": "generic",
    "gewapendbetonprefab": "precast concrete",
    "gewapendbetontpg": "concrete",
    "gips": "gypsum board",
    "isolatie": "insulation",
    "isolatieEPS": "insulation EPS",
    "isolatiePIR": "insulation PIR",
    "isolatiePUR": "insulation PUR",
    "isolatieglaswol": "insulation glass wool",
    "kalkzandsteen": "sand-lime",
    "metselwerkbaksteenporiso": "brick porous",
    "metselwerkbaksteenrood": "brick",
    "naaldhoutvuren": "timber",
    "naaldhoutvurenCLT": "timber CLT",
    "ongewapendbeton": "unreinforced concrete",
}
STEEL = {"staal"}

# The application's role of each IFC class and predefined type: a slab is a
# floor unless the template calls it a roof (IFC writes both as IfcSlab).
PLANAR_CLASSES = {"IFCWALLTYPE": "IfcWallType", "IFCSLABTYPE": "IfcSlabType"}
LINEAR_CLASSES = {"IFCCOLUMNTYPE": "IfcColumnType", "IFCBEAMTYPE": "IfcBeamType"}
ROLE_ORDER = ["wall", "floor", "roof", "column", "beam"]


def role_of(ifc_class, predefined):
    if ifc_class == "IfcWallType":
        return "wall"
    if ifc_class == "IfcSlabType":
        return "roof" if predefined == "ROOF" else "floor"
    return "column" if ifc_class == "IfcColumnType" else "beam"


# ---------------------------------------------------------------- STEP reading

def decode(text):
    """A STEP string's text: '' is a quote, \\X2\\hhhh\\X0\\ UTF-16 code units."""
    def unicode(match):
        hexes = match.group(1)
        units = [int(hexes[i:i + 4], 16) for i in range(0, len(hexes), 4)]
        return b"".join(u.to_bytes(2, "big") for u in units).decode("utf-16-be")
    text = text.replace("''", "'")
    text = re.sub(r"\\X2\\([0-9A-F]+)\\X0\\", unicode, text)
    return re.sub(r"\\X\\([0-9A-F]{2})", lambda m: bytes([int(m.group(1), 16)]).decode("latin-1"), text)


def entities(path):
    """Every instance of the DATA section: number -> (TYPE, argument text)."""
    found = {}
    buffer = ""
    quoted = False
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            for character in line.rstrip("\r\n"):
                if character == "'":
                    quoted = not quoted
                buffer += character
                if character == ";" and not quoted:
                    match = re.fullmatch(r"\s*#(\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*)\)\s*;\s*", buffer, re.S)
                    if match:
                        found[int(match.group(1))] = (match.group(2), match.group(3))
                    buffer = ""
            if quoted:
                buffer += "\n"
    return found


def split(arguments):
    """The top-level arguments of an argument text."""
    parts, depth, current, quoted = [], 0, "", False
    for character in arguments:
        if character == "'":
            quoted = not quoted
        if not quoted and character == "(":
            depth += 1
        if not quoted and character == ")":
            depth -= 1
        if not quoted and depth == 0 and character == ",":
            parts.append(current.strip())
            current = ""
            continue
        current += character
    parts.append(current.strip())
    return parts


def string(argument):
    return decode(argument[1:-1]) if argument.startswith("'") else ""


def references(argument):
    return [int(number) for number in re.findall(r"#(\d+)", argument)]


def millimetres_to_metres(value):
    """A length in millimetres as metres, rounded to a tenth of a millimetre."""
    return round(float(value) * 10.0) / 10000.0


# ---------------------------------------------------------------- extraction

def natural(name):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+(?:\.\d+)?)", name) if part]


def length_unit(found):
    for kind, arguments in found.values():
        if kind == "IFCSIUNIT":
            parts = split(arguments)
            if parts[1] == ".LENGTHUNIT.":
                return 0.001 if parts[2] == ".MILLI." else 1.0
    raise ValueError("the template names no length unit")


def material_name(found, number):
    kind, arguments = found[number]
    if kind != "IFCMATERIAL":
        raise ValueError(f"#{number} is {kind}, not IFCMATERIAL")
    return string(split(arguments)[0])


def mapped(template_material):
    if template_material not in MATERIALS:
        raise ValueError(f"template material '{template_material}' has no application material in MATERIALS")
    return MATERIALS[template_material]


def layers_of(found, number, scale):
    kind, arguments = found[number]
    if kind == "IFCMATERIALLAYERSETUSAGE":
        return layers_of(found, references(split(arguments)[0])[0], scale)
    if kind != "IFCMATERIALLAYERSET":
        raise ValueError(f"#{number} is {kind}, not a material layer set")
    result = []
    for layer in references(split(arguments)[0]):
        parts = split(found[layer][1])
        template_material = material_name(found, references(parts[0])[0])
        result.append({
            "template_material": template_material,
            "material": mapped(template_material),
            "thickness_m": millimetres_to_metres(float(parts[1]) * scale * 1000.0),
        })
    return result


def profile_of(found, number, scale):
    """The member's profile, or (None, reason) when it is not imported here."""
    kind, arguments = found[number]
    if kind != "IFCMATERIALPROFILESET":
        return None, f"material is {kind}, not a profile set"
    profiles = references(split(arguments)[2])
    if len(profiles) != 1:
        return None, "profile set of more than one profile"
    parts = split(found[profiles[0]][1])
    template_material = material_name(found, references(parts[2])[0])
    if template_material in STEEL:
        return None, "steel profile series; follows the profile catalogue (#95)"
    shape_kind, shape_arguments = found[references(parts[3])[0]]
    shape = split(shape_arguments)
    if shape_kind == "IFCRECTANGLEPROFILEDEF":
        width = millimetres_to_metres(float(shape[3]) * scale * 1000.0)
        depth = millimetres_to_metres(float(shape[4]) * scale * 1000.0)
        round_profile = False
    elif shape_kind == "IFCCIRCLEPROFILEDEF":
        width = depth = millimetres_to_metres(2.0 * float(shape[3]) * scale * 1000.0)
        round_profile = True
    else:
        return None, f"profile {shape_kind} is not a solid rectangle or circle"
    return {"round": round_profile, "width_m": width, "depth_m": depth,
            "template_material": template_material, "material": mapped(template_material)}, None


def extract(template, commit):
    found = entities(template)
    scale = length_unit(found)
    associations = {}
    for kind, arguments in found.values():
        if kind == "IFCRELASSOCIATESMATERIAL":
            parts = split(arguments)
            material = references(parts[5])[0]
            for owner in references(parts[4]):
                associations[owner] = material
    types, excluded = [], []
    for number, (kind, arguments) in found.items():
        if kind not in PLANAR_CLASSES and kind not in LINEAR_CLASSES:
            continue
        parts = split(arguments)
        ifc_class = PLANAR_CLASSES.get(kind) or LINEAR_CLASSES[kind]
        predefined = parts[-1].strip(".")
        record = {"name": string(parts[2]), "ifc_class": ifc_class,
                  "predefined_type": "NOTDEFINED" if predefined == "$" else predefined,
                  "role": role_of(ifc_class, predefined)}
        if kind in PLANAR_CLASSES:
            record["layers"] = layers_of(found, associations[number], scale) if number in associations else []
            if not record["layers"]:
                record["not_imported"] = "the template gives this type no material layer set"
            types.append(record)
        else:
            if number not in associations:
                excluded.append({**record, "reason": "no material profile set"})
                continue
            profile, reason = profile_of(found, associations[number], scale)
            if profile is None:
                excluded.append({"name": record["name"], "ifc_class": ifc_class, "reason": reason})
                continue
            record["profile"] = profile
            types.append(record)
    order = lambda r: (ROLE_ORDER.index(r["role"]) if "role" in r else 0, r["ifc_class"], natural(r["name"]))
    types.sort(key=order)
    excluded.sort(key=lambda r: (r["ifc_class"], natural(r["name"])))
    for record in types:
        name = record["name"]
        numbers = re.findall(r"(\d+(?:\.\d+)?)$", name)
        if record.get("layers") and numbers:
            total = sum(layer["thickness_m"] for layer in record["layers"]) * 1000.0
            if abs(total - float(numbers[0])) > 0.6:
                record["note"] = f"the name says {numbers[0]} mm, the template's layers are {total:g} mm; kept as the template has it"
    return {
        "schema_version": 1,
        "catalogue_id": "org.openaec.nl.types.inb-template",
        "units": "m",
        "language": "nl-NL",
        "status": "runtime-imported",
        "source": {"repository": REPOSITORY, "commit": commit, "file": template.name,
                   "length_unit_m": scale},
        "materials": dict(sorted(MATERIALS.items(), key=lambda item: item[0].lower())),
        "types": types,
        "excluded": excluded,
    }


# ---------------------------------------------------------------- DynLex

ROLE_CODES = {"wall": "bim wall planar role", "floor": "bim floor planar role",
              "roof": "bim roof planar role", "column": "bim column role", "beam": "bim beam role"}

HEADER = """# SPDX-License-Identifier: MPL-2.0
# Written by tools/inb_type_catalogue.py from localisation/nl/types/catalogue.json
# (the INB template of OpenAEC, {repository} at commit {commit}); do not
# edit: change the catalogue and run `python3 -I tools/inb_type_catalogue.py
# generate`. {imported} types: {counts}.
#
# Each type keeps its template name ("Name" of set "Type identity", which the
# naming rules take over the rule name) and its IFC predefined type
# ("PredefinedType" of set "IFC attributes", which the IFC writer uses).
import bim/bim_model.dl

local function keep bim inb name {{a string:typeName}} and predefined type {{a string:predefinedType}} of {{a 64 bit integer:typeId}} in {{a pointer to a bim model record:target}}:
    execute:
        set bim property (the string form of "Name") of set (the string form of "Type identity") of typeId to typeName typed (the string form of "IFCLABEL") in target
        set bim property (the string form of "PredefinedType") of set (the string form of "IFC attributes") of typeId to predefinedType typed (the string form of "IFCLABEL") in target

# A planar type of the template: 1 when added, 0 when the model has a type of
# that role and name already (or the layers are refused).
local function add bim inb planar type {{a string:typeName}} as role {{integer:roleCode}} predefined {{a string:predefinedType}} with {{a pointer to a list:layerValues}} to {{a pointer to a bim model record:target}}:
    execute:
        loop cursor from 0 to the length of (target's wallTypes's values):
            set existing to the item at cursor in (target's wallTypes's values)
            if (existing's role = roleCode) and (existing's name = typeName):
                return 0
        set fresh to add bim planar type named typeName as role roleCode with layerValues to target
        if fresh = the bim refused id:
            return 0
        keep bim inb name typeName and predefined type predefinedType of fresh in target
        return 1

# A linear type of the template, the same way.
local function add bim inb linear type {{a string:typeName}} as role {{integer:roleCode}} predefined {{a string:predefinedType}} sized {{a 64 bit floating-point number:widthValue}} by {{a 64 bit floating-point number:depthValue}} round {{boolean:isRound}} of {{a string:materialName}} to {{a pointer to a bim model record:target}}:
    execute:
        loop cursor from 0 to the length of (target's linearTypes's values):
            set existing to the item at cursor in (target's linearTypes's values)
            if (existing's role = roleCode) and (existing's name = typeName):
                return 0
        set fresh to add bim linear type named typeName as role roleCode sized widthValue by depthValue round isRound of materialName to target
        if fresh = the bim refused id:
            return 0
        keep bim inb name typeName and predefined type predefinedType of fresh in target
        return 1

# The types of the INB template added to `target`, each when the model lacks
# a type of its role and name, named by the rules once at the end. The number
# added.
function add bim inb template types to {{a pointer to a bim model record:target}}:
    execute:
        set added to 0
        set layerValues to an empty list of a bim layer record
"""


def dynlex_string(text):
    if '"' in text or "\\" in text:
        raise ValueError(f"unsupported character in '{text}'")
    return f'(the string form of "{text}")'


def dynlex_real(value):
    text = f"{value:.6f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def generate(catalogue):
    imported = [t for t in catalogue["types"] if "not_imported" not in t]
    counts = ", ".join(f"{sum(1 for t in imported if t['role'] == role)} {role}"
                       for role in ROLE_ORDER)
    lines = [HEADER.format(repository=catalogue["source"]["repository"],
                           commit=catalogue["source"]["commit"],
                           imported=len(imported), counts=counts).rstrip("\n")]
    for record in imported:
        role = ROLE_CODES[record["role"]]
        name = dynlex_string(record["name"])
        predefined = dynlex_string(record["predefined_type"])
        if "layers" in record:
            lines.append("        clear layerValues")
            for layer in record["layers"]:
                lines.append(f"        append (@intrinsic(\"construct\", a bim layer record, {dynlex_string(layer['material'])}, {dynlex_real(layer['thickness_m'])})) to layerValues")
            lines.append(f"        set added to added + (add bim inb planar type {name} as role ({role}) predefined {predefined} with layerValues to target)")
        else:
            profile = record["profile"]
            lines.append(f"        set added to added + (add bim inb linear type {name} as role ({role}) predefined {predefined} sized {dynlex_real(profile['width_m'])} by {dynlex_real(profile['depth_m'])} round {'true' if profile['round'] else 'false'} of {dynlex_string(profile['material'])} to target)")
    lines += ["        free layerValues",
              "        if added > 0:",
              "            name bim types by the rules in target",
              "        return added"]
    return "\n".join(lines) + "\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    extracting = commands.add_parser("extract", help="the catalogue from the template")
    extracting.add_argument("template", type=pathlib.Path)
    extracting.add_argument("--commit", required=True, help="the template repository's commit")
    extracting.add_argument("--out", type=pathlib.Path, default=CATALOGUE)
    generating = commands.add_parser("generate", help="the DynLex of the catalogue")
    generating.add_argument("--catalogue", type=pathlib.Path, default=CATALOGUE)
    generating.add_argument("--out", type=pathlib.Path, default=GENERATED)
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
                raise ValueError("--commit takes the full 40-digit commit")
            catalogue = extract(args.template, args.commit)
            write(args.out, json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n")
            print(f"wrote {args.out}: {len(catalogue['types'])} types, {len(catalogue['excluded'])} excluded")
        else:
            catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
            write(args.out, generate(catalogue))
            print(f"wrote {args.out}")
    except (OSError, ValueError, KeyError, IndexError) as error:
        print(f"inb_type_catalogue: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
