#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check the slice's IFC5 (IfcX) export independently.

Reads the file `tests/ifcx.dl` writes, checks the header and that every path is
a unique UUID and every child and inheritance reference resolves, composes the
tree as the IFC5 reference implementation does (inherits, then children, then
own attributes), and checks the spatial structure, the classes, the layered
wall bodies reaching their materials, and that both component instances
receive the component's body through inheritance.
"""
import json, re, sys

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

def main(path):
    document = json.load(open(path))
    header = document["header"]
    assert header["ifcxVersion"] == "ifcx_alpha", header
    for key in ("id", "dataVersion", "author", "timestamp"):
        assert isinstance(header[key], str) and header[key], key
    assert set(document) == {"header", "imports", "schemas", "data"}, set(document)
    nodes = {}
    for node in document["data"]:
        assert UUID.match(node["path"]), node["path"]
        assert node["path"] not in nodes, "path written twice: " + node["path"]
        nodes[node["path"]] = node
    for node in nodes.values():
        for group in ("children", "inherits"):
            for name, target in (node.get(group) or {}).items():
                assert target in nodes, f"{node['path']} {group} {name} -> missing {target}"
    def compose(path):
        node = nodes[path]
        result = {"children": {}, "attributes": {}}
        for target in (node.get("inherits") or {}).values():
            inherited = compose(target)
            result["children"].update(inherited["children"])
            result["attributes"].update(inherited["attributes"])
        for name, target in (node.get("children") or {}).items():
            result["children"][name] = compose(target)
        result["attributes"].update(node.get("attributes") or {})
        return result
    referenced = {t for n in nodes.values() for g in ("children", "inherits") for t in (n.get(g) or {}).values()}
    roots = [p for p in nodes if p not in referenced]
    assert len(roots) == 1, roots
    tree = None
    for root in roots:
        composed = compose(root)
        if "Project" in composed["children"]:
            tree = composed
    assert tree is not None, "no root holds the project"
    def cls(node):
        return node["attributes"].get("bsi::ifc::class", {}).get("code")
    project = tree["children"]["Project"]
    assert cls(project) == "IfcProject"
    building = project["children"]["Site"]["children"]["Building"]
    assert cls(building) == "IfcBuilding"
    counts = {}
    def walk(node):
        counts[cls(node)] = counts.get(cls(node), 0) + 1
        for child in node["children"].values():
            walk(child)
    walk(project)
    storeys = [c for c in building["children"].values() if cls(c) == "IfcBuildingStorey"]
    assert storeys, "no storey"
    layered = 0
    for storey in storeys:
        for name, child in storey["children"].items():
            if cls(child) == "IfcWall":
                bodies = [b for b in child["children"].values() if "usd::usdgeom::mesh" in b["attributes"]]
                assert bodies, name + " has no body"
                for body in bodies:
                    mesh = body["attributes"]["usd::usdgeom::mesh"]
                    assert len(mesh["faceVertexIndices"]) % 3 == 0
                    assert max(mesh["faceVertexIndices"]) < len(mesh["points"])
                if len(bodies) > 1:
                    layered += 1
                    for body in bodies:
                        assert "bsi::ifc::material" in body["attributes"], name + " layer without material"
                assert child["attributes"]["bsi::ifc::prop::Volume"] > 0
    instances = [c for s in storeys for c in s["children"].values() if cls(c) == "IfcBuildingElementProxy" and "usd::xformop" in c["attributes"]]
    assert len(instances) == 2, len(instances)
    for instance in instances:
        part = instance["children"]["Part_1"]
        assert "usd::usdgeom::mesh" in part["children"]["Body"]["attributes"], "instance without inherited body"
    windows = counts.get("IfcWindow", 0) + counts.get("IfcDoor", 0)
    print(f"ifcx ok: {len(nodes)} nodes, {len(storeys)} storeys, {counts.get('IfcWall', 0)} walls ({layered} layered), "
          f"{counts.get('IfcSlab', 0)} slabs, {windows} doors and windows, {counts.get('IfcSpace', 0)} spaces, "
          f"{len(instances)} instances, {counts.get('IfcAnnotation', 0)} annotations")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bim-slice-test.ifcx")
