"""Dumps the two reference case sets to `cases.json` for the Rust driver.

The Rust driver in this directory cannot import `reference/boolean_torture_set.py`
or `reference/precision_set.py`, and re-typing ten vertex lists into Rust would
make the spike measure a transcription rather than a kernel. So this script is the
single bridge: it imports both reference modules verbatim and writes their cases
out as JSON, with the analytic expectations and the operand volumes computed by
`reference.signed_volume` so the Rust side never re-derives them either.

Run from the repository root:

    python spikes/boolean-torture/ocs_driver/dump_cases.py

Writes `spikes/boolean-torture/ocs_driver/cases.json`. Dependency-free.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / "reference"))

import boolean_torture_set as torture  # noqa: E402
import precision_set as precision  # noqa: E402
from boolean_torture_set import signed_volume  # noqa: E402


def mesh(m) -> dict:
    return {
        "vertices": [list(v) for v in m.vertices],
        "faces": [list(f) for f in m.faces],
        "volume": signed_volume(m.vertices, m.faces),
    }


def main() -> None:
    payload = {
        "source": {
            "torture": "reference/boolean_torture_set.py",
            "precision": "reference/precision_set.py",
        },
        "offset": list(precision.OFFSET),
        "torture": [
            {
                "name": c.name,
                "a": mesh(c.a),
                "b": mesh(c.b),
                "expected_union": c.expected_volume_union,
                "expected_intersection": c.expected_volume_intersection,
            }
            for c in torture.cases()
        ],
        "precision": [
            {
                "name": c.name,
                "a": mesh(c.a),
                "b": mesh(c.b),
                "expected_union": c.expected_volume_union,
                "expected_intersection": c.expected_volume_intersection,
                "offset": list(c.offset),
            }
            for c in precision.cases()
        ],
    }
    out = HERE / "cases.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(
        f"wrote {out} — {len(payload['torture'])} torture cases, "
        f"{len(payload['precision'])} precision cases, {out.stat().st_size} bytes"
    )


if __name__ == "__main__":
    main()
