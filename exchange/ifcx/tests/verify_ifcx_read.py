#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Compose IfcX files independently and compare with the slice's import.

Runs the compiled `tests/ifcx_read.dl` on the given IfcX files, composes the
same files here (flatten by path in layer order; inherits, then children,
then own attributes; instance-path overrides), and checks that both find the
same number of meshes and of non-degenerate triangles and the same extent.
"""
import json, subprocess, sys

def flatten(files):
    nodes = {}
    for document in files:
        for node in document["data"]:
            flat = nodes.setdefault(node["path"], {"children": {}, "inherits": {}, "attributes": {}})
            for name, target in (node.get("children") or {}).items():
                flat["children"][name] = target
            for name, target in (node.get("inherits") or {}).items():
                if target is None:
                    flat["inherits"].pop(name, None)
                else:
                    flat["inherits"][name] = target
            for key, value in (node.get("attributes") or {}).items():
                flat["attributes"][key] = value
    return nodes

def compose(nodes, reference, depth=0):
    head, _, tail = reference.partition("/")
    node = compose_path(nodes, head, depth)
    for step in [t for t in tail.split("/") if t]:
        target = node["children"].get(step)
        if not target:
            return {"children": {}, "attributes": {}}
        node = compose(nodes, target, depth + 1)
    return node

def compose_path(nodes, path, depth):
    result = {"children": {}, "attributes": {}}
    flat = nodes.get(path)
    if flat is None or depth > 64:
        return result
    for target in flat["inherits"].values():
        inherited = compose(nodes, target, depth + 1)
        result["children"].update(inherited["children"])
        result["attributes"].update(inherited["attributes"])
    result["children"].update(flat["children"])
    result["attributes"].update(flat["attributes"])
    return result

def multiply(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]

def main(binary, paths):
    files = [json.load(open(p)) for p in paths]
    nodes = flatten(files)
    referenced = set()
    for flat in nodes.values():
        for target in list(flat["children"].values()) + list(flat["inherits"].values()):
            if target:
                referenced.add(target.split("/")[0])
    meshes = 0
    triangles = 0
    segments = 0
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    identity = [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]
    def walk(reference, instance, parent, depth):
        nonlocal meshes, triangles, segments
        node = compose(nodes, reference)
        node = {"children": dict(node["children"]), "attributes": dict(node["attributes"])}
        if instance != reference and instance in nodes:
            node["children"].update(nodes[instance]["children"])
            node["attributes"].update(nodes[instance]["attributes"])
        own = identity
        transform = (node["attributes"].get("usd::xformop") or {}).get("transform")
        if isinstance(transform, list) and len(transform) == 4 and all(isinstance(r, list) and len(r) == 4 for r in transform):
            own = transform
        matrix = multiply(own, parent)
        curve = node["attributes"].get("usd::usdgeom::basiscurves")
        if isinstance(curve, dict) and isinstance(curve.get("points"), list):
            segments += max(0, len(curve["points"]) - 1)
        mesh = node["attributes"].get("usd::usdgeom::mesh")
        if isinstance(mesh, dict) and "points" in mesh and "faceVertexIndices" in mesh:
            meshes += 1
            placed = []
            for x, y, z in ((p + [0, 0, 0])[:3] for p in mesh["points"]):
                placed.append([x * matrix[0][c] + y * matrix[1][c] + z * matrix[2][c] + matrix[3][c] for c in range(3)])
            for point in placed:
                for c in range(3):
                    low[c] = min(low[c], point[c]); high[c] = max(high[c], point[c])
            corners = mesh["faceVertexIndices"]
            for i in range(0, len(corners) - 2, 3):
                a, b, c = corners[i:i + 3]
                if all(0 <= v < len(placed) for v in (a, b, c)):
                    p, q, r = placed[a], placed[b], placed[c]
                    u = [q[k] - p[k] for k in range(3)]; v = [r[k] - p[k] for k in range(3)]
                    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
                    if any(n):
                        triangles += 1
        for name, target in node["children"].items():
            if target:
                walk(target, instance + "/" + name, matrix, depth + 1)
    for path in nodes:
        if path not in referenced:
            walk(path, path, identity, 0)
    output = subprocess.run([binary] + paths, capture_output=True, text=True, check=True).stdout
    print(output, end="")
    lines = output.splitlines()
    found = lines[0].split()
    assert found[0] == "meshes", lines[0]
    assert int(found[1]) == meshes, f"meshes: DynLex {found[1]}, composed here {meshes}"
    assert int(found[3]) == triangles, f"triangles: DynLex {found[3]}, composed here {triangles}"
    found_segments = [l for l in lines if l.startswith("curve segments ")]
    assert found_segments and int(found_segments[0].split()[2]) == segments, f"curve segments: DynLex {found_segments}, composed here {segments}"
    if meshes:
        extent = [l for l in lines if l.startswith("extent ") or l.startswith("    to ")]
        got = [float(v) for v in extent[0].split()[1:]] + [float(v) for v in extent[1].split()[1:]]
        want = low + high
        assert all(abs(g - w) <= 1e-9 * max(1.0, abs(w)) for g, w in zip(got, want)), (got, want)
    print(f"verified: {meshes} meshes, {triangles} triangles, {segments} curve segments, extent matches")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
