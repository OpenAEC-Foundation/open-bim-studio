"""OCCT driver for the boolean torture set.

THROWAWAY SPIKE CODE. Run:

    python spikes/boolean-torture/occt_driver.py --out spikes/boolean-torture/results/occt.md

from the repository root. Requires `cadquery-ocp` (see `../README.md`).

For every case in `reference/boolean_torture_set.py` it constructs both operands as
OCCT solids (method in `occt_common.py`), then runs `BRepAlgoAPI_Fuse` and
`BRepAlgoAPI_Common` under each setting, checks the result with
`BRepCheck_Analyzer`, measures volumes with `BRepGProp`, and reports the
volume-identity residual

    |V(A) + V(B) - (V(A union B) + V(A intersect B))|

which is zero for an exact boolean regardless of what the analytic volumes are.
It also reports the deviation from the analytic expectations in `reference/`.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "reference"))
sys.path.insert(0, _HERE)

import boolean_torture_set as torture  # noqa: E402
from occt_common import (  # noqa: E402
    SEW_TOLERANCE,
    boolean,
    build_solid,
    environment,
)

# (label, fuzzy value passed to SetFuzzyValue). `None` means "leave the default",
# which BOPAlgo_Options sets to Precision::Confusion() = 1e-7.
SETTINGS: list[tuple[str, float | None]] = [
    ("default", None),
    ("fuzzy=1e-5", 1e-5),
    ("fuzzy=1e-3", 1e-3),
]


def fmt(x: float, digits: int = 9) -> str:
    if x != x:
        return "nan"
    return f"{x:.{digits}g}"


def tolerance_probe(steps: int = 8, gap: float = 5e-6, fuzz: float = 1e-5) -> list[str]:
    """Does a fuzzy boolean's tolerance growth compound over a chain of operations?

    Chains `steps` unit boxes, each separated from the previous one by `gap` — a gap
    too wide for Precision::Confusion() (1e-7) but inside the fuzzy value, so every
    step needs the fuzzy value to glue. After each step we report the largest entity
    tolerance in the result and the result's volume. The nominal volume of N glued
    boxes is N; anything above that is gap that the tolerance bridged and the volume
    integral counted.
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCP.TopAbs import TopAbs_ShapeEnum
    from OCP.collections import List_TopoDS_Shape

    from occt_common import count, max_tolerance, volume

    def box(x0, y0, z0, x1, y1, z1):
        mesh = torture._box(x0, y0, z0, x1, y1, z1)
        return build_solid(mesh.vertices, mesh.faces).shape

    out = [
        f"| 0 (input) | 1 | {fmt(1.0)} | {fmt(1e-7, 4)} | - |",
    ]
    cur = box(0, 0, 0, 1, 1, 1)
    x = 1.0
    for i in range(1, steps + 1):
        nxt = box(x + gap, 0, 0, x + gap + 1.0, 1, 1)
        op = BRepAlgoAPI_Fuse()
        la, lb = List_TopoDS_Shape(), List_TopoDS_Shape()
        la.Append(cur)
        lb.Append(nxt)
        op.SetArguments(la)
        op.SetTools(lb)
        op.SetFuzzyValue(fuzz)
        op.Build()
        if not op.IsDone():
            out.append(f"| {i} | - | - | - | **not done** |")
            break
        cur = op.Shape()
        x = x + gap + 1.0
        v = volume(cur)
        out.append(
            "| {} | {} | {} | {} | {} |".format(
                i,
                count(cur, TopAbs_ShapeEnum.TopAbs_SOLID),
                fmt(v, 10),
                fmt(max_tolerance(cur), 4),
                fmt(v - (i + 1), 3),
            )
        )
    return out


def input_mutation_probe() -> list[str]:
    """Does a boolean raise the tolerance of its *input* shapes?

    `BOPAlgo` runs in destructive mode by default (`SetNonDestructive(false)`), and
    the user guide states that safe mode "prevents the input arguments from any
    modification such as tolerance increase". This measures whether that happens on
    the benchmark operands.
    """
    from occt_common import max_tolerance

    rows = []
    case = [c for c in torture.cases() if c.name in ("overlap_half", "sliver")]
    for c in case:
        for label, fuzz in (("default", None), ("fuzzy=1e-3", 1e-3)):
            a = build_solid(c.a.vertices, c.a.faces)
            b = build_solid(c.b.vertices, c.b.faces)
            before = max(max_tolerance(a.shape), max_tolerance(b.shape))
            r = boolean("fuse", a.shape, b.shape, fuzz, repeats=1)
            after = max(max_tolerance(a.shape), max_tolerance(b.shape))
            rows.append(
                "| `{}` | {} | {} | {} | {} |".format(
                    c.name, label, fmt(before, 4), fmt(after, 4), fmt(r.max_tolerance, 4)
                )
            )
    return rows


def sewing_floor_probe() -> list[str]:
    """Does asking for a sewing tolerance below `Precision::Confusion()` change anything?

    `BRepBuilderAPI_Sewing::Init` clamps with `std::max(tolerance, Confusion())`, so the
    prediction from the source is that 1e-8, 1e-9 and 1e-12 all behave as 1e-7. This
    checks it on the result rather than on the source: the same operand is sewn at each
    tolerance and the resulting shape is serialised with `BRepTools::Write` (ASCII BREP,
    with triangulation) and hashed, so "identical" means byte-identical output, not
    merely equal volume.
    """
    import hashlib
    import io

    from OCP.BRepTools import BRepTools

    def digest(shape) -> str:
        buf = io.BytesIO()
        BRepTools.Write_s(shape, buf)
        return hashlib.sha256(buf.getvalue()).hexdigest()

    # `sliver` B is the operand whose own thickness (1e-7) sits at the clamp, so if any
    # case can show a difference below Confusion() it is this one; `overlap_half` A is
    # the ordinary control.
    cases = {c.name: c for c in torture.cases()}
    rows = []
    for label, mesh in (
        ("`overlap_half` A (unit cube)", cases["overlap_half"].a),
        ("`sliver` B (1e-7 m slab)", cases["sliver"].b),
    ):
        base = None
        for tol in (1e-7, 1e-8, 1e-9, 1e-12):
            built = build_solid(mesh.vertices, mesh.faces, sew_tolerance=tol)
            if built.shape is None:
                rows.append(f"| {label} | {fmt(tol, 3)} | construction failed | - | - |")
                continue
            d = digest(built.shape)
            if base is None:
                base = d
            rows.append(
                "| {} | {} | `{}` | {} | {} |".format(
                    label, fmt(tol, 3), d[:16],
                    fmt(built.volume, 12),
                    "same as 1e-7" if d == base else "**differs from 1e-7**",
                )
            )
    return rows


def box_floor_probe() -> list[str]:
    """How thin a solid will `BRepPrimAPI_MakeBox` build?

    `BRepPrim_GWedge::IsDegeneratedShape()` rejects any extent `<= Precision::Confusion()`,
    so the prediction is a hard floor at 1e-7 exclusive. Measured by construction, and the
    exception type is reported rather than summarised, because "it throws" and "it returns
    an invalid shape" are different failure modes for a caller.
    """
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.gp import gp_Pnt

    rows = []
    for thickness in (1e-6, 1.0001e-7, 1e-7, 9.9999e-8, 1e-9):
        try:
            shape = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 1.0, 1.0, thickness).Shape()
        except Exception as exc:  # noqa: BLE001 - the exception *is* the measurement
            rows.append(
                f"| {fmt(thickness, 6)} | **no** | `{type(exc).__name__}` | - |"
            )
            continue
        from occt_common import volume as _volume

        rows.append(
            "| {} | yes | - | {} |".format(fmt(thickness, 6), fmt(_volume(shape), 12))
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "occt.md"))
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()

    env = environment()
    rows: list[str] = []
    construction: list[str] = []
    n_valid = 0
    n_total = 0

    for case in torture.cases():
        a = build_solid(case.a.vertices, case.a.faces)
        b = build_solid(case.b.vertices, case.b.faces)
        construction.append(
            "| `{}` | {} | {} | {} | {} | {} | {} |".format(
                case.name,
                "yes" if a.valid else "**no**",
                fmt(a.volume),
                fmt(a.max_tolerance, 4),
                "yes" if b.valid else "**no**",
                fmt(b.volume),
                (b.note or a.note or "-"),
            )
        )
        if a.shape is None or b.shape is None:
            for label, _ in SETTINGS:
                rows.append(
                    f"| `{case.name}` | {label} | construction failed | - | - | - | - | - |"
                )
                n_total += 1
            continue

        # Fresh operands for every setting *and* every repeat. BOPAlgo is destructive
        # by default (Probe B), so reusing one pair across three settings x N repeats
        # would run each later boolean on operands already degraded by ~20 earlier
        # ones, and the fuzzy rows would then measure the history rather than the
        # setting. `build_solid` is deterministic, so every rebuild is the same shape.
        def fresh(c=case):
            return (
                build_solid(c.a.vertices, c.a.faces).shape,
                build_solid(c.b.vertices, c.b.faces).shape,
            )

        for label, fuzz in SETTINGS:
            n_total += 1
            u = boolean("fuse", None, None, fuzz, repeats=args.repeats, rebuild=fresh)
            i = boolean("common", None, None, fuzz, repeats=args.repeats, rebuild=fresh)
            both_ok = u.ok and i.ok
            both_valid = both_ok and u.valid and i.valid
            if both_valid:
                n_valid += 1
            identity = abs((a.volume + b.volume) - (u.volume + i.volume)) if both_ok else float("nan")
            dev_u = abs(u.volume - case.expected_volume_union) if u.ok else float("nan")
            dev_i = abs(i.volume - case.expected_volume_intersection) if i.ok else float("nan")
            valid_cell = "yes" if both_valid else ("**no**" if both_ok else "**not done**")
            note = "; ".join(x for x in (u.note, i.note) if x)
            rows.append(
                "| `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
                    case.name,
                    label,
                    valid_cell,
                    fmt(u.volume) + (f" (Δ{fmt(dev_u, 3)})" if dev_u > 1e-12 else ""),
                    fmt(i.volume) + (f" (Δ{fmt(dev_i, 3)})" if dev_i > 1e-12 else ""),
                    fmt(identity, 3),
                    f"{u.ms:.2f} / {i.ms:.2f}",
                    (note or f"tol≤{fmt(max(u.max_tolerance, i.max_tolerance), 3)}"),
                )
            )

    text = [
        "# Boolean torture set — OCCT raw results",
        "",
        "Produced by [`../occt_driver.py`](../occt_driver.py). This file is raw data for",
        "`../FINDINGS.md` (assembled once every candidate has run) and for",
        "[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        "",
        "## Environment",
        "",
        "| Item | Value |",
        "|---|---|",
    ]
    for k, v in env.items():
        text.append(f"| {k} | `{v}` |")
    text += [
        f"| repeats per timing | {args.repeats} (fastest reported) |",
        "| threading | `SetRunParallel(false)` — single-threaded, so the timings compare algorithms not core counts |",
        "",
        "## Construction of the operands",
        "",
        "Triangle soup → planar faces → `BRepBuilderAPI_Sewing` → solid(s), at sewing",
        f"tolerance `{fmt(SEW_TOLERANCE)}`. Construction is part of the measurement: a case whose",
        "operands cannot be built is a finding about OCCT, not a driver error.",
        "",
        "| Case | A valid? | V(A) | max tol(A) | B valid? | V(B) | Note |",
        "|---|---|---|---|---|---|---|",
    ] + construction + [
        "",
        "## Boolean results",
        "",
        "`Δ` is the deviation from the analytic expectation in `reference/boolean_torture_set.py`;",
        "it is shown only where it exceeds 1e-12. *Identity* is",
        "`|V(A) + V(B) − (V(A∪B) + V(A∩B))|` computed from the **measured** operand volumes, so it",
        "isolates the boolean from any error already present in the operands. Times are milliseconds,",
        "union / intersection.",
        "",
        "| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |",
        "|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        f"**Summary:** {n_valid} of {n_total} case×setting combinations produced results that",
        "`BRepCheck_Analyzer` reports valid for both the union and the intersection.",
        "",
        "## Probe A — does tolerance growth compound over chained booleans?",
        "",
        "Eight unit boxes fused one at a time, each separated from the previous by a 5e-6 gap",
        "(wider than `Precision::Confusion()`, inside `SetFuzzyValue(1e-5)`), so every step needs",
        "the fuzzy value to glue. *Excess volume* is the measured volume minus the nominal N+1;",
        "it is the gap the tolerance bridged and the volume integral then counted as solid.",
        "",
        "| Step | Solids | V | max entity tolerance | Excess volume |",
        "|---|---|---|---|---|",
    ] + tolerance_probe() + [
        "",
        "## Probe B — does a boolean raise the tolerance of its input shapes?",
        "",
        "`BOPAlgo` is destructive by default (`SetNonDestructive(false)`). Measured on the operands",
        "before and after one `BRepAlgoAPI_Fuse`.",
        "",
        "| Case | Setting | max tol(inputs) before | after | max tol(result) |",
        "|---|---|---|---|---|",
    ] + input_mutation_probe() + [
        "",
        "## Probe C — is a sewing tolerance below `Precision::Confusion()` honoured?",
        "",
        "`BRepBuilderAPI_Sewing::Init` clamps with `std::max(tolerance, Confusion())`. This probe",
        "sews the same operand at 1e-7, 1e-8, 1e-9 and 1e-12 and hashes the ASCII BREP written by",
        "`BRepTools::Write` (triangulation included), so *identical* here means byte-identical",
        "serialised output and not merely equal volume.",
        "",
        "| Operand | Requested sewing tolerance | SHA-256 of the BREP (first 16 hex) | Volume | vs. 1e-7 |",
        "|---|---|---|---|---|",
    ] + sewing_floor_probe() + [
        "",
        "## Probe D — how thin a solid will `BRepPrimAPI_MakeBox` build?",
        "",
        "`BRepPrim_GWedge::IsDegeneratedShape()` rejects any extent `<= Precision::Confusion()`.",
        "Measured by construction; the *exception type* is reported because \"throws\" and \"returns",
        "an invalid shape\" are different things for a caller to handle.",
        "",
        "| Requested thickness (m) | Built? | Exception | Volume |",
        "|---|---|---|---|",
    ] + box_floor_probe() + [
        "",
    ]
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(text))
    print(f"wrote {out}")
    print(f"{n_valid}/{n_total} case x setting combinations valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
