#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""The profile catalogue: every standard profile the Profiles tab browses.

  profile_catalogue.py generate [--check]
      reads the series files elements/linear/profiles/NN-name.json and writes
      elements/linear/bim_profile_catalogue_data.dl, the catalogue as DynLex
      (the application reads no data files at run time, so the catalogue is
      compiled in). With --check it only reports whether that file is current.

A series file holds one series: its code (the order of the catalogue, and for
the European steel series 1 to 13 the code `bim steel series setting` keeps
on a type), its short name, title, standard, material, IFC profile kind,
whether its profiles are columns too, whether a type made from one keeps
the profile's name ("type_name": "catalogue") or takes the naming rules' name
("rules", the default), and its profiles, one array each in the
order of "fields" (millimetres). See elements/linear/profiles/README.md.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERIES_DIR = ROOT / "elements/linear/profiles"
GENERATED = ROOT / "elements/linear/bim_profile_catalogue_data.dl"

# IFC profile kinds and their codes in elements/linear/bim_profiles.dl; a
# Rectangle and a Circle are a plain type (code 0), a Circle with round set.
KINDS = {
    "Rectangle": 0, "Circle": 0, "IShape": 1, "LShape": 2, "UShape": 3,
    "TShape": 4, "CShape": 5, "ZShape": 6, "RectangleHollow": 7,
    "CircleHollow": 8, "Ellipse": 9, "Trapezium": 10,
}
DIMENSIONS = ("h", "b", "tw", "tf", "r", "fourth")
# Records per string literal in the generated file.
CHUNK = 12


def number_text(value):
    value = float(value)
    if value == int(value):
        return str(int(value))
    return ("%.3f" % value).rstrip("0").rstrip(".")


def field_text(value):
    """A text field of the generated tables: no separator or quote inside."""
    text = str(value)
    for separator in ("|", ";", '"', "\\", "\n"):
        if separator in text:
            raise SystemExit("separator %r in %r" % (separator, text))
    return text


def read_series():
    series = []
    for path in sorted(SERIES_DIR.glob("[0-9][0-9]-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise SystemExit("%s: unknown schema_version" % path.name)
        data["_file"] = path.name
        series.append(data)
    codes = [entry["code"] for entry in series]
    if len(set(codes)) != len(codes):
        raise SystemExit("series codes repeat: %s" % codes)
    return series


def records_of(entry):
    fields = entry["fields"]
    if fields[0] != "name":
        raise SystemExit("%s: the first field is the name" % entry["_file"])
    records = []
    for row in entry["profiles"]:
        if len(row) != len(fields):
            raise SystemExit("%s: %r has %d fields" % (entry["_file"], row, len(fields)))
        values = dict(zip(fields, row))
        name = field_text(values["name"])
        if "," in name:
            raise SystemExit("%s: a comma in %r" % (entry["_file"], name))
        kind_name = values.get("profile", entry["profile"])
        if kind_name not in KINDS:
            raise SystemExit("%s: unknown profile %r" % (entry["_file"], kind_name))
        if "d" in values:
            values["h"] = values["d"]
            values["b"] = values["d"]
        dims = [float(values.get(key, 0)) for key in DIMENSIONS]
        if dims[0] <= 0 or dims[1] <= 0:
            raise SystemExit("%s: %r needs a depth and a width" % (entry["_file"], row))
        nominal = 0
        match = re.fullmatch(re.escape(entry["series"]) + r" (\d+)", name)
        if match:
            nominal = int(match.group(1))
        round_flag = 1 if kind_name == "Circle" else 0
        column_flag = 1 if entry["column"] else 0
        fields_out = [str(entry["code"]), str(nominal), str(KINDS[kind_name])]
        fields_out += [number_text(value) for value in dims]
        fields_out += [str(column_flag), str(round_flag), name]
        records.append(",".join(fields_out))
    return records


def generated_text(series):
    total = sum(len(entry["profiles"]) for entry in series)
    lines = [
        "# SPDX-License-Identifier: MPL-2.0",
        "# Written by tools/profile_catalogue.py from elements/linear/profiles/*.json;",
        "# do not edit: change a series file and run `python3 -I",
        "# tools/profile_catalogue.py generate`. %d series, %d profiles." % (len(series), total),
        "#",
        "# A series line: code|series|title|standard|material|count|named (1:",
        "# a type made from it keeps the profile's name, 0: the naming rules name it). A profile",
        "# record: series,nominal,kind,h,b,tw,tf,r,fourth,column,round,name in",
        "# millimetres, records apart by ';' (`bim_profile_catalogue.dl` reads them).",
        "import bim/bim_model.dl",
        "",
        "function the bim profile catalogue series lines:",
        "    execute:",
        "        set seriesLines to an empty list of a string",
    ]
    for entry in series:
        line = "|".join([
            str(entry["code"]), field_text(entry["series"]), field_text(entry["title"]),
            field_text(entry["standard"]), field_text(entry["material"]), str(len(entry["profiles"])),
            "1" if entry.get("type_name", "rules") == "catalogue" else "0",
        ])
        lines.append('        append (the string form of "%s") to seriesLines' % line)
    lines.append("        return seriesLines")
    lines.append("")
    lines.append("# The profile records of series `seriesCode`, in chunks; none for another code.")
    lines.append("function the bim profile catalogue chunks of series {integer:seriesCode}:")
    lines.append("    execute:")
    lines.append("        set chunkTexts to an empty list of a string")
    for entry in series:
        records = records_of(entry)
        lines.append("        if seriesCode = %d:" % entry["code"])
        for start in range(0, len(records), CHUNK):
            text = ";".join(records[start:start + CHUNK])
            lines.append('            append (the string form of "%s") to chunkTexts' % text)
    lines.append("        return chunkTexts")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    text = generated_text(read_series())
    if arguments.check:
        current = GENERATED.read_text(encoding="utf-8") if GENERATED.exists() else ""
        if current != text:
            print("%s is not current: run tools/profile_catalogue.py generate" % GENERATED.relative_to(ROOT))
            return 1
        print("%s is current" % GENERATED.relative_to(ROOT))
        return 0
    GENERATED.write_text(text, encoding="utf-8")
    print("wrote %s" % GENERATED.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
