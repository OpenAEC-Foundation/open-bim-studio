"""Extract a rebuild plan (storeys, walls, slabs, openings) from a simple IFC4 STEP file.

Usage: python3 -I ifc_extract.py MODEL.ifc > plan.json
Reads only placements, extrusions, axis polylines and base quantities; no ifcopenshell.
"""
import json
import re
import sys

ENTITY = re.compile(r"^#(\d+)\s*=\s*([A-Z0-9_]+)\((.*)\);\s*$")


def split_args(text):
    """Splits a STEP argument list into Python values (refs as ('ref', n))."""
    out, i = [], 0

    def parse(i):
        while text[i] == " ":
            i += 1
        c = text[i]
        if c == "(":
            items, i = [], i + 1
            while text[i] != ")":
                value, i = parse(i)
                items.append(value)
                while text[i] in " ,":
                    i += 1
            return items, i + 1
        if c == "'":
            j = i + 1
            while True:
                if text[j] == "'" and (j + 1 >= len(text) or text[j + 1] != "'"):
                    break
                j += 2 if text[j] == "'" else 1
            return text[i + 1:j].replace("''", "'"), j + 1
        if c == "#":
            m = re.match(r"#(\d+)", text[i:])
            return ("ref", int(m.group(1))), i + len(m.group(0))
        if c in "$*":
            return None, i + 1
        if c == ".":
            j = text.index(".", i + 1)
            return text[i:j + 1], j + 1
        m = re.match(r"([A-Z0-9_]+)\(", text[i:])
        if m:  # typed value such as IFCLENGTHMEASURE(2.5)
            inner, k = parse(i + len(m.group(1)))
            return (m.group(1), inner), k
        m = re.match(r"[-+0-9.Ee]+", text[i:])
        token = m.group(0)
        try:
            return (int(token) if re.fullmatch(r"[-+]?\d+", token) else float(token)), i + len(token)
        except ValueError:
            return token, i + len(token)

    while i < len(text):
        value, i = parse(i)
        out.append(value)
        while i < len(text) and text[i] in " ,":
            i += 1
    return out


def load(path):
    data, buffer = {}, ""
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            buffer += line.strip()
            if not buffer.endswith(";"):
                continue
            m = ENTITY.match(buffer)
            buffer = ""
            if m:
                data[int(m.group(1))] = (m.group(2), m.group(3))
    return data


class Model:
    def __init__(self, path):
        self.raw = load(path)
        self.cache = {}

    def get(self, ref):
        n = ref[1] if isinstance(ref, tuple) else ref
        if n not in self.cache:
            kind, text = self.raw[n]
            self.cache[n] = (kind, split_args(text))
        return self.cache[n]

    def of(self, kind):
        return [n for n, (k, _) in self.raw.items() if k == kind]

    # -- geometry -------------------------------------------------------
    def point(self, ref):
        coords = self.get(ref)[1][0]
        return [float(c) for c in coords] + [0.0] * (3 - len(coords))

    def direction(self, ref, default):
        if ref is None:
            return default
        ratios = [float(c) for c in self.get(ref)[1][0]]
        return ratios + [0.0] * (3 - len(ratios))

    def axis_matrix(self, ref):
        kind, args = self.get(ref)
        origin = self.point(args[0])
        if kind == "IFCAXIS2PLACEMENT2D":
            x = self.direction(args[1], [1.0, 0.0, 0.0])
            z = [0.0, 0.0, 1.0]
        else:
            z = self.direction(args[1], [0.0, 0.0, 1.0])
            x = self.direction(args[2], [1.0, 0.0, 0.0])
        z = norm(z)
        x = norm(sub(x, scale(z, dot(x, z))))
        y = cross(z, x)
        return [x, y, z, origin]

    def placement(self, ref):
        if ref is None:
            return identity()
        kind, args = self.get(ref)
        local = self.axis_matrix(args[1])
        parent = self.placement(args[0]) if args[0] is not None else identity()
        return compose(parent, local)


def identity():
    return [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [0, 0, 0.0]]


def dot(a, b):
    return sum(p * q for p, q in zip(a, b))


def sub(a, b):
    return [p - q for p, q in zip(a, b)]


def scale(a, s):
    return [p * s for p in a]


def norm(a):
    length = dot(a, a) ** 0.5 or 1.0
    return scale(a, 1.0 / length)


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def apply(m, p):
    x, y, z, o = m
    return [o[i] + x[i] * p[0] + y[i] * p[1] + z[i] * p[2] for i in range(3)]


def rotate(m, v):
    x, y, z, _ = m
    return [x[i] * v[0] + y[i] * v[1] + z[i] * v[2] for i in range(3)]


def compose(parent, local):
    return [rotate(parent, local[0]), rotate(parent, local[1]), rotate(parent, local[2]), apply(parent, local[3])]


def r(v, n=3):
    return round(v, n)


def main(path):
    model = Model(path)
    quantities, psets = {}, {}
    for rel in model.of("IFCRELDEFINESBYPROPERTIES"):
        args = model.get(rel)[1]
        kind, definition = model.get(args[5])
        if kind != "IFCELEMENTQUANTITY":
            continue
        values = {}
        for q in definition[5]:
            qkind, qargs = model.get(q)
            if qkind in ("IFCQUANTITYLENGTH", "IFCQUANTITYAREA", "IFCQUANTITYVOLUME"):
                values[qargs[0]] = qargs[3]
        for obj in args[4]:
            quantities.setdefault(obj[1], {}).update(values)

    containment = {}
    for rel in model.of("IFCRELCONTAINEDINSPATIALSTRUCTURE"):
        args = model.get(rel)[1]
        storey = model.get(args[5])[1][2]
        for obj in args[4]:
            containment[obj[1]] = storey
    for rel in model.of("IFCRELAGGREGATES"):
        args = model.get(rel)[1]
        parent = args[4][1]
        for obj in args[5]:
            if parent in containment:
                containment.setdefault(obj[1], containment[parent])

    def representations(n):
        args = model.get(n)[1]
        found = {}
        if args[6] is None:
            return found
        for rep in model.get(args[6])[1][2]:
            rargs = model.get(rep)[1]
            found.setdefault(rargs[1], []).extend(model.get(i) for i in rargs[3])
        return found

    plan = {"storeys": [], "walls": [], "slabs": [], "openings": [], "other": {}}
    for n in model.of("IFCBUILDINGSTOREY"):
        args = model.get(n)[1]
        plan["storeys"].append({"name": args[2], "elevation": float(args[9])})
    plan["storeys"].sort(key=lambda s: s["elevation"])

    for kind in ("IFCWALLSTANDARDCASE", "IFCWALL"):
        for n in model.of(kind):
            args = model.get(n)[1]
            matrix = model.placement(args[5])
            reps = representations(n)
            axis = [i for i in reps.get("Axis", []) if i[0] == "IFCPOLYLINE"]
            if not axis:
                continue
            pts = [apply(matrix, model.point(p)) for p in axis[0][1][0]]
            q = quantities.get(n, {})
            height = q.get("Height")
            thickness = q.get("Width")
            for item in reps.get("Body", []):
                if item[0] == "IFCEXTRUDEDAREASOLID" and height is None:
                    height = item[1][3]
            plan["walls"].append({"id": n, "name": args[2], "storey": containment.get(n),
                                  "start": [r(pts[0][0]), r(pts[0][1])], "end": [r(pts[-1][0]), r(pts[-1][1])],
                                  "z": r(pts[0][2]), "height": height, "thickness": thickness})

    for n in model.of("IFCSLAB"):
        args = model.get(n)[1]
        matrix = model.placement(args[5])
        entry = {"id": n, "name": args[2], "storey": containment.get(n), "predefined": args[8]}
        for item in representations(n).get("Body", []):
            if item[0] != "IFCEXTRUDEDAREASOLID":
                continue
            solid = matrix and compose(matrix, model.axis_matrix(item[1][1]))
            profile_kind, profile = model.get(item[1][0])
            depth_dir = rotate(solid, model.direction(item[1][2], [0, 0, 1.0]))
            entry["depth"] = item[1][3]
            entry["extrusion"] = [r(c) for c in depth_dir]
            if profile_kind == "IFCARBITRARYCLOSEDPROFILEDEF":
                curve_kind, curve = model.get(profile[2])
                if curve_kind == "IFCPOLYLINE":
                    entry["outline"] = [[r(c) for c in apply(solid, model.point(p))] for p in curve[0]]
            elif profile_kind == "IFCRECTANGLEPROFILEDEF":
                inner = compose(solid, model.axis_matrix(profile[2]))
                hx, hy = profile[3] / 2, profile[4] / 2
                entry["outline"] = [[r(c) for c in apply(inner, [sx * hx, sy * hy, 0])]
                                    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        plan["slabs"].append(entry)

    hosts = {}
    for rel in model.of("IFCRELVOIDSELEMENT"):
        args = model.get(rel)[1]
        hosts[args[5][1]] = args[4][1]
    fills = {}
    for rel in model.of("IFCRELFILLSELEMENT"):
        args = model.get(rel)[1]
        fills[args[5][1]] = hosts.get(args[4][1])
    for kind in ("IFCWINDOW", "IFCDOOR"):
        for n in model.of(kind):
            args = model.get(n)[1]
            matrix = model.placement(args[5])
            plan["openings"].append({"id": n, "kind": kind[3:].lower(), "name": args[2], "storey": containment.get(n),
                                     "origin": [r(c) for c in matrix[3]], "xdir": [r(c) for c in matrix[0]],
                                     "height": args[8], "width": args[9], "host": fills.get(n)})

    for kind in ("IFCROOF", "IFCSTAIR", "IFCRAILING", "IFCBEAM", "IFCMEMBER", "IFCSPACE", "IFCCOLUMN"):
        plan["other"][kind[3:].lower()] = len(model.of(kind))
    json.dump(plan, sys.stdout, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
