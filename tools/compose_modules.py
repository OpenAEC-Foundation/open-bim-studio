"""Composes the modules: reads every MODULE manifest under the root and writes
generated/model.dl (the bim model record with one member per declared store,
plus its empty constructor and its snapshot) and generated/compose.dl (one
dispatcher per extension point, calling each implementing module in layer
order). Programs import the generated files; nobody edits them.

Manifest lines (plain text, `#` comments):
  name: planar
  layer: 3
  depends: bim
  records: elements/planar/records.dl
  value: nextId as a 64 bit integer = 1 as a 64 bit integer
  store: walls as a cad topology list of a bim wall record
  shared: journal as a cad topology list of a 64 bit integer
  point: candidates elements/planar/evaluation.dl

A `store` is cloned by the snapshot, a `shared` list is shared by it and a
`value` is copied. Usage: compose_modules.py [--root DIR] [--out DIR].
"""
import argparse
import os
import pathlib
import sys

HEADER = "# Written by tools/compose_modules.py from the MODULE manifests; do not edit.\n"
SKIPPED_DIRS = {".git", "build", "generated", "tests", "node_modules", "__pycache__"}

# Each point: the dispatcher's header line and how one module's call reads.
POINTS = {
    "scene": {
        "header": "function append bim module scene meshes of {bim model record:modelValue} within {a 64 bit floating-point number:tolerance} reusing {a pointer to a list:previous} keyed {a pointer to a list:keys} refreshing {a pointer to a list:remadeIds} with reinforcement detail {boolean:rebarDetail} into {a pointer to a list:result}:",
        "call": "append bim scene meshes of modelValue within tolerance reusing previous keyed keys refreshing remadeIds with reinforcement detail rebarDetail into result with {module} elements",
        "style": "each",
    },
    "candidates": {
        "header": "function collect bim module candidates of {bim model record:modelValue} into {a pointer to a list:candidates}:",
        "call": "collect bim candidates of modelValue with {module} elements into candidates",
        "style": "each",
    },
    "build": {
        "header": "function build bim module element {a 64 bit integer:elementId} of {bim model record:modelValue} into {a pointer to a bim evaluation record:target} through {bim hosted index record:hostedIndex}:",
        "call": "build bim element elementId of modelValue into target through hostedIndex with {module} elements",
        "style": "first-true",
    },
}


class ManifestError(Exception):
    pass


def parse_manifest(path, root):
    module = {"name": None, "layer": None, "depends": [], "records": None,
              "members": [], "points": []}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ManifestError(f"{path}:{number}: expected 'key: value'")
        key, value = (part.strip() for part in line.split(":", 1))
        if key == "name":
            module["name"] = value
        elif key == "layer":
            module["layer"] = int(value)
        elif key == "depends":
            module["depends"] = [d for d in value.replace(",", " ").split() if d]
        elif key == "records":
            module["records"] = value
        elif key in ("value", "store", "shared"):
            if " as " not in value:
                raise ManifestError(f"{path}:{number}: expected '<name> as <type>'")
            name, rest = (part.strip() for part in value.split(" as ", 1))
            initial = None
            if key == "value":
                if " = " not in rest:
                    raise ManifestError(f"{path}:{number}: a value needs '= <initial>'")
                rest, initial = (part.strip() for part in rest.split(" = ", 1))
            module["members"].append({"kind": key, "name": name, "type": rest, "initial": initial})
        elif key == "point":
            parts = value.split()
            if len(parts) != 2:
                raise ManifestError(f"{path}:{number}: expected 'point: <name> <file>'")
            if parts[0] not in POINTS:
                raise ManifestError(f"{path}:{number}: unknown point '{parts[0]}'")
            module["points"].append({"point": parts[0], "file": parts[1]})
        else:
            raise ManifestError(f"{path}:{number}: unknown key '{key}'")
    for required in ("name", "layer"):
        if module[required] is None:
            raise ManifestError(f"{path}: missing '{required}'")
    module["path"] = path.relative_to(root).as_posix()
    return module


def find_modules(root):
    modules = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
        if "MODULE" in files:
            modules.append(parse_manifest(pathlib.Path(directory) / "MODULE", root))
    modules.sort(key=lambda m: (m["layer"], m["name"]))
    names = [m["name"] for m in modules]
    if len(set(names)) != len(names):
        raise ManifestError("two manifests share a module name")
    seen = set()
    for module in modules:
        for dependency in module["depends"]:
            if dependency not in names:
                raise ManifestError(f"{module['path']}: depends on unknown module '{dependency}'")
        for member in module["members"]:
            if member["name"] in seen:
                raise ManifestError(f"{module['path']}: member '{member['name']}' is declared twice")
            seen.add(member["name"])
    return modules


def member_line(member):
    if member["kind"] == "value":
        return f"{member['name']} as {member['type']}"
    return f"{member['name']} as the type of ({member['type']})"


def empty_expression(member):
    return member["initial"] if member["kind"] == "value" else member["type"]


def snapshot_expression(member):
    if member["kind"] == "store":
        return f"the cad clone of modelValue's {member['name']}"
    return f"modelValue's {member['name']}"


def model_text(modules):
    members = [m for module in modules for m in module["members"]]
    lines = [HEADER.rstrip("\n")]
    lines += [f"import {module['records']}" for module in modules if module["records"]]
    lines += ["", "class:", "    patterns:", "        [a|] bim model record", "    members:"]
    lines += [f"        {member_line(m)}" for m in members]
    lines += ["", "function an empty bim model:", "    execute:",
              "        return @intrinsic(\"construct\", a bim model record, "
              + ", ".join(empty_expression(m) for m in members) + ")"]
    lines += ["", "# A snapshot shares no store with the original: stores are cloned, values",
              "# copied and shared members shared.",
              "function the bim snapshot of {bim model record:modelValue}:", "    execute:",
              "        return @intrinsic(\"construct\", a bim model record, "
              + ", ".join(snapshot_expression(m) for m in members) + ")"]
    return "\n".join(lines) + "\n"


def compose_text(modules):
    files = []
    for module in modules:
        for point in module["points"]:
            if point["file"] not in files:
                files.append(point["file"])
    lines = [HEADER.rstrip("\n")] + [f"import {file}" for file in files]
    for name, spec in POINTS.items():
        implementers = [m["name"] for m in modules if any(p["point"] == name for p in m["points"])]
        lines += ["", spec["header"], "    execute:"]
        if spec["style"] == "each":
            lines += [f"        {spec['call'].format(module=m)}" for m in implementers] or ["        ignore 0"]
        else:
            for m in implementers:
                lines += [f"        if {spec['call'].format(module=m)}:", "            return true"]
            lines += ["        return false"]
    return "\n".join(lines) + "\n"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="where the MODULE manifests are searched")
    parser.add_argument("--out", default="generated", help="where model.dl and compose.dl are written")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    try:
        modules = find_modules(root)
    except ManifestError as error:
        print(f"compose_modules: {error}", file=sys.stderr)
        return 1
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("model.dl", model_text(modules)), ("compose.dl", compose_text(modules))):
        with open(out / name, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    print(f"wrote {out / 'model.dl'} and {out / 'compose.dl'} from {len(modules)} modules")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
