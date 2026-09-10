"""OCCT driver for the precision set.

THROWAWAY SPIKE CODE. Run:

    python spikes/precision-set/occt_driver.py --out spikes/precision-set/results/occt.md

from the repository root. Requires `cadquery-ocp` (see `../README.md`).

The question: does the same boolean give the same answer 500 km from the origin?
For each case in `reference/precision_set.py` the driver builds both operands twice
— once at the origin, once translated by `precision_set.OFFSET` — runs
`BRepAlgoAPI_Fuse` and `BRepAlgoAPI_Common` on both, translates the far result back
by −OFFSET, and compares. Two comparisons are reported:

* **volume deviation** — |V(far) − V(near)|, absolute and relative;
* **vertex deviation** — every vertex of the translated-back far result matched to
  its nearest vertex in the near result, worst distance reported. This is the
  number that shows precision loss even when the volume happens to agree.

The translation is applied to the *input coordinates*, not with `gp_Trsf`, because
that is what a real project does: the geometry is authored at its map coordinates.
Reusing the shared helpers from the boolean-torture spike keeps the construction
method identical between the two spikes.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "reference"))
sys.path.insert(0, os.path.join(_ROOT, "spikes", "boolean-torture"))

import precision_set  # noqa: E402
from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.TopAbs import TopAbs_ShapeEnum  # noqa: E402
from OCP.TopExp import TopExp_Explorer  # noqa: E402
from OCP.TopoDS import TopoDS  # noqa: E402
from occt_common import SEW_TOLERANCE, boolean, build_solid, environment  # noqa: E402

SETTINGS: list[tuple[str, float | None]] = [("default", None), ("fuzzy=1e-5", 1e-5)]


def vertices_of(shape) -> list[tuple[float, float, float]]:
    out = []
    exp = TopExp_Explorer(shape, TopAbs_ShapeEnum.TopAbs_VERTEX)
    seen = set()
    while exp.More():
        p = BRep_Tool.Pnt_s(TopoDS.Vertex(exp.Current()))
        key = (p.X(), p.Y(), p.Z())
        if key not in seen:
            seen.add(key)
            out.append(key)
        exp.Next()
    return out


def worst_vertex_deviation(near, far, delta) -> tuple[float, int, int]:
    """Translate `far` back by −delta, then match every vertex to its nearest in
    `near`. Returns (worst distance, |near|, |far|). Nearest-neighbour matching is
    the honest comparison here: OCCT is free to emit vertices in any order and to
    merge or split them, so index-wise comparison would measure the wrong thing.
    """
    dx, dy, dz = delta
    back = [(x - dx, y - dy, z - dz) for (x, y, z) in far]
    worst = 0.0
    for bx, by, bz in back:
        best = float("inf")
        for nx, ny, nz in near:
            d = math.dist((bx, by, bz), (nx, ny, nz))
            if d < best:
                best = d
        worst = max(worst, best)
    return worst, len(near), len(back)


def fmt(x: float, digits: int = 6) -> str:
    if x != x:
        return "nan"
    if x == 0.0:
        return "0"
    return f"{x:.{digits}g}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "occt.md"))
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()

    delta = precision_set.OFFSET
    rows: list[str] = []
    construction: list[str] = []

    for case in precision_set.cases():
        near_a = build_solid(case.a.vertices, case.a.faces)
        near_b = build_solid(case.b.vertices, case.b.faces)
        far_a = build_solid(precision_set.offset(case.a.vertices, delta), case.a.faces)
        far_b = build_solid(precision_set.offset(case.b.vertices, delta), case.b.faces)
        construction.append(
            "| `{}` | {} / {} | {} / {} | {} | {} |".format(
                case.name,
                "yes" if near_a.valid else "**no**",
                "yes" if near_b.valid else "**no**",
                "yes" if far_a.valid else "**no**",
                "yes" if far_b.valid else "**no**",
                fmt(abs((far_a.volume + far_b.volume) - (near_a.volume + near_b.volume)), 3),
                fmt(max(far_a.max_tolerance, far_b.max_tolerance), 4),
            )
        )
        if any(s.shape is None for s in (near_a, near_b, far_a, far_b)):
            rows.append(f"| `{case.name}` | - | construction failed | - | - | - | - |")
            continue

        for label, fuzz in SETTINGS:
            for kind, expected in (
                ("fuse", case.expected_volume_union),
                ("common", case.expected_volume_intersection),
            ):
                n = boolean(kind, near_a.shape, near_b.shape, fuzz, repeats=args.repeats)
                f = boolean(kind, far_a.shape, far_b.shape, fuzz, repeats=args.repeats)
                if not (n.ok and f.ok):
                    rows.append(
                        f"| `{case.name}` | {label} | {kind} | **not done** | - | - | - |"
                    )
                    continue
                dv = abs(f.volume - n.volume)
                rel = dv / abs(n.volume) if n.volume else float("nan")
                dev, n_near, n_far = worst_vertex_deviation(
                    vertices_of(n.shape), vertices_of(f.shape), delta
                )
                valid = "yes" if (n.valid and f.valid) else "**no**"
                rows.append(
                    "| `{}` | {} | {} | {} | {} | {} | {} |".format(
                        case.name,
                        label,
                        kind,
                        valid,
                        f"{fmt(n.volume, 12)} / {fmt(f.volume, 12)}",
                        f"{fmt(dv, 3)} ({fmt(rel, 3)} rel)",
                        f"{fmt(dev, 3)} m over {n_near}/{n_far} v",
                    )
                )

    env = environment()
    text = [
        "# Precision set — OCCT raw results",
        "",
        "Produced by [`../occt_driver.py`](../occt_driver.py). Raw data for `../FINDINGS.md` and for",
        "[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        f"**Offset:** `{delta}` (500 km east, 500 km north — a plausible distance from a national",
        "projection's false origin to a project site).",
        "",
        "## Environment",
        "",
        "| Item | Value |",
        "|---|---|",
    ]
    for k, v in env.items():
        text.append(f"| {k} | `{v}` |")
    text += [
        f"| repeats per timing | {args.repeats} |",
        "| threading | `SetRunParallel(false)` |",
        "",
        "## Construction at both locations",
        "",
        "| Case | near A/B valid? | far A/B valid? | ΔV(A)+V(B) far−near | max tol far |",
        "|---|---|---|---|---|",
    ] + construction + [
        "",
        "## Boolean results near vs far",
        "",
        "*Vertex deviation* is the worst nearest-neighbour distance after translating the far result",
        "back by −offset, followed by the vertex counts of the near and far results. A kernel that is",
        "translation-invariant at this distance reports a deviation at the level of f64 rounding of",
        "the coordinate itself (5e5 m × 2⁻⁵² ≈ 1.1e-10 m).",
        "",
        "| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation |",
        "|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
    ]
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(text))
    print(f"wrote {out}")
    return 0


def _vertices(kind, a, b, fuzz, repeats):
    """Re-run one boolean purely to get at its result shape's vertices."""
    r = boolean(kind, a.shape, b.shape, fuzz, repeats=1)
    if not r.ok:
        return []
    # `boolean` returns metrics, not the shape; rebuild the operation here.
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse
    from OCP.collections import List_TopoDS_Shape

    op = {"fuse": BRepAlgoAPI_Fuse, "common": BRepAlgoAPI_Common}[kind]()
    la, lb = List_TopoDS_Shape(), List_TopoDS_Shape()
    la.Append(a.shape)
    lb.Append(b.shape)
    op.SetArguments(la)
    op.SetTools(lb)
    op.SetRunParallel(False)
    if fuzz is not None:
        op.SetFuzzyValue(fuzz)
    op.Build()
    if not op.IsDone() or op.Shape().IsNull():
        return []
    return vertices_of(op.Shape())


if __name__ == "__main__":
    raise SystemExit(main())
