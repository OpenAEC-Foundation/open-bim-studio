# SPDX-License-Identifier: MPL-2.0
"""Check role/type bindings in the generated exchange fixture, without extra packages."""
import re
import sys
from pathlib import Path


def verify(text):
    entities = {int(number): (kind, body) for number, kind, body in
                re.findall(r"#(\d+)=([A-Z0-9_]+)\((.*)\);", text)}
    expected = {"IFCWALL": "IFCWALLTYPE", "IFCSLAB": "IFCSLABTYPE", "IFCCOVERING": "IFCCOVERINGTYPE",
                "IFCCOLUMN": "IFCCOLUMNTYPE", "IFCBEAM": "IFCBEAMTYPE", "IFCPILE": "IFCPILETYPE",
                "IFCDOOR": "IFCDOORTYPE", "IFCWINDOW": "IFCWINDOWTYPE"}
    assigned, relationships = {}, {}
    for number, (kind, body) in entities.items():
        if kind != "IFCRELDEFINESBYTYPE":
            continue
        match = re.search(r",\((#[\d,#]+)\),#(\d+)$", body)
        assert match, f"malformed relationship #{number}"
        type_number = int(match[2])
        assert type_number not in relationships, f"multiple Types inverses for #{type_number}"
        relationships[type_number] = number
        for owner in map(int, re.findall(r"#(\d+)", match[1])):
            assert owner not in assigned, f"multiple type assignments for #{owner}"
            assert entities[owner][0] in expected, f"unexpected typed occurrence #{owner}"
            assert entities[type_number][0] == expected[entities[owner][0]], f"wrong type for #{owner}"
            assigned[owner] = type_number
    occurrences = {number for number, (kind, _) in entities.items() if kind in expected}
    assert occurrences == set(assigned), f"untyped occurrences: {occurrences - set(assigned)}"
    assert len(relationships) == 10 and len(assigned) == 11, (len(relationships), len(assigned))
    for kind in ("IFCDOORTYPE", "IFCWINDOWTYPE"):
        body = next(body for entity_kind, body in entities.values() if entity_kind == kind)
        # Names in this fixture contain no commas, so the 13 IFC4 subtype attributes are unambiguous.
        assert len(body.split(",")) == 13, f"wrong subtype attribute count: {kind}"
    print(f"PASS: {len(assigned)} native occurrences bound to {len(relationships)} correct IFC type objects")


if __name__ == "__main__":
    verify(Path(sys.argv[1] if len(sys.argv) > 1 else "ifc-types-test.ifc").read_text(encoding="utf-8"))
