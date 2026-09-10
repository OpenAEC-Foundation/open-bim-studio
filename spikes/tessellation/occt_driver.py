"""OCCT tessellation timing on the 10k synthetic scale model.

THROWAWAY SPIKE CODE. Run:

    python reference/generate_scale_models.py --count 10000 --out build/scale_10k.obj
    python spikes/tessellation/occt_driver.py --obj build/scale_10k.obj \
        --out spikes/tessellation/results/occt.md

from the repository root. Requires `cadquery-ocp` (see `../boolean-torture/README.md`).

The question: how long does `BRepMesh_IncrementalMesh` take on 10k elements, and how
much does the linear deflection parameter change both the time and the triangle count?
This is the number behind `problems.md` P-11 ("tessellation quality vs. speed"): if one
deflection is right for the viewport and another for a drawing, the cost of holding both
is the difference between these rows.

Construction method (part of the measurement): `reference/generate_scale_models.py`
emits axis-aligned unit boxes, so each box is rebuilt as a native
`BRepPrimAPI_MakeBox` from its parsed min corner rather than sewn from its twelve
triangles. That is deliberate — sewing 10k boxes would make construction, not
tessellation, dominate the wall clock, and the question here is about
`BRepMesh_IncrementalMesh`. The parse asserts each box is axis-aligned and unit-sized,
so nothing is assumed about the file that is not checked.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "spikes", "boolean-torture"))

from OCP.BRep import BRep_Builder, BRep_Tool  # noqa: E402
from OCP.BRepMesh import BRepMesh_IncrementalMesh  # noqa: E402
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox  # noqa: E402
from OCP.TopAbs import TopAbs_ShapeEnum  # noqa: E402
from OCP.TopExp import TopExp_Explorer  # noqa: E402
from OCP.TopLoc import TopLoc_Location  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Compound  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from occt_common import environment  # noqa: E402

DEFLECTIONS = [1.0, 0.1, 0.01, 0.001]


def read_boxes(path: str) -> list[tuple[float, float, float, float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("v "):
                _, x, y, z = line.split()
                verts.append((float(x), float(y), float(z)))
    assert len(verts) % 8 == 0, f"{len(verts)} vertices is not a whole number of boxes"
    boxes = []
    for i in range(0, len(verts), 8):
        chunk = verts[i : i + 8]
        xs = sorted({v[0] for v in chunk})
        ys = sorted({v[1] for v in chunk})
        zs = sorted({v[2] for v in chunk})
        assert len(xs) == len(ys) == len(zs) == 2, "box is not axis-aligned"
        boxes.append((xs[0], ys[0], zs[0], xs[1], ys[1], zs[1]))
    return boxes


def triangle_count(shape) -> int:
    total = 0
    exp = TopExp_Explorer(shape, TopAbs_ShapeEnum.TopAbs_FACE)
    loc = TopLoc_Location()
    while exp.More():
        tri = BRep_Tool.Triangulation_s(TopoDS.Face(exp.Current()), loc)
        if tri is not None:
            total += tri.NbTriangles()
        exp.Next()
    return total


def build_compound(boxes):
    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    for x0, y0, z0, x1, y1, z1 in boxes:
        solid = BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), x1 - x0, y1 - y0, z1 - z0).Shape()
        builder.Add(comp, solid)
    return comp


def sphere_control(count: int, deflection: float) -> list[str]:
    """Control for the parallel-flag result on the box model.

    If `isInParallel` shows no speed-up on 10k planar boxes, that could mean either
    "this OCCT build has no working threading" or "the per-face work is too small to
    pay for the parallel path". Spheres settle it: one sphere face at a fine deflection
    is thousands of triangles, so if threading works at all it must show here.
    """
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere

    rows = []
    for label, parallel in (("single", False), ("parallel", True)):
        builder = BRep_Builder()
        comp = TopoDS_Compound()
        builder.MakeCompound(comp)
        for i in range(count):
            builder.Add(comp, BRepPrimAPI_MakeSphere(gp_Pnt(i * 3.0, 0.0, 0.0), 1.0).Shape())
        t0 = time.perf_counter()
        mesher = BRepMesh_IncrementalMesh(comp, deflection, False, 0.05, parallel)
        ms = (time.perf_counter() - t0) * 1000.0
        tris = triangle_count(comp)
        rows.append(
            "| {} spheres, deflection {:g} | {} | {} | {:.0f} | {} |".format(
                count, deflection, label, "yes" if mesher.IsDone() else "**no**",
                ms, f"{tris:,}",
            )
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj", default=os.path.join(_ROOT, "build", "scale_10k.obj"))
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "occt.md"))
    ap.add_argument("--spheres", type=int, default=400,
                    help="how many spheres in the parallel-flag control")
    ap.add_argument("--sphere-deflection", type=float, default=5e-4)
    ap.add_argument("--parallel", action="store_true",
                    help="also time each deflection with BRepMesh_IncrementalMesh's parallel flag")
    args = ap.parse_args()

    t0 = time.perf_counter()
    boxes = read_boxes(args.obj)
    parse_ms = (time.perf_counter() - t0) * 1000.0

    rows = []
    for deflection in DEFLECTIONS:
        modes = [("single", False)] + ([("parallel", True)] if args.parallel else [])
        for label, parallel in modes:
            # A fresh compound per run: BRepMesh caches its triangulation on the faces,
            # so re-meshing the same shape would time a no-op.
            t0 = time.perf_counter()
            comp = build_compound(boxes)
            build_ms = (time.perf_counter() - t0) * 1000.0
            t0 = time.perf_counter()
            mesher = BRepMesh_IncrementalMesh(comp, deflection, False, 0.5, parallel)
            mesh_ms = (time.perf_counter() - t0) * 1000.0
            tris = triangle_count(comp)
            rows.append(
                "| {} | {} | {} | {:.0f} | {:.0f} | {} | {:.1f} |".format(
                    f"{deflection:g}",
                    label,
                    "yes" if mesher.IsDone() else "**no**",
                    build_ms,
                    mesh_ms,
                    f"{tris:,}",
                    mesh_ms * 1000.0 / max(tris, 1),
                )
            )

    from OCP.OSD import OSD_ThreadPool

    threads = OSD_ThreadPool.DefaultPool_s().NbThreads()
    control = sphere_control(args.spheres, args.sphere_deflection)

    env = environment()
    text = [
        "# Tessellation on the 10k scale model — OCCT raw results",
        "",
        "Produced by [`../occt_driver.py`](../occt_driver.py). Raw data for",
        "[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        f"**Model:** `{os.path.relpath(args.obj, _ROOT).replace(os.sep, '/')}` — "
        f"{len(boxes):,} unit boxes from `reference/generate_scale_models.py --count 10000`, "
        f"parsed in {parse_ms:.0f} ms.",
        "",
        "## Environment",
        "",
        "| Item | Value |",
        "|---|---|",
    ]
    for k, v in env.items():
        if k.startswith("Precision") or k == "sewing tolerance":
            continue
        text.append(f"| {k} | `{v}` |")
    text += [
        "",
        "## Results",
        "",
        "*Linear deflection* is `BRepMesh_IncrementalMesh`'s `theLinDeflection`, in model units",
        "(the boxes are 1 unit on a side). Angular deflection is 0.5 rad throughout and is",
        "irrelevant here — the model is entirely planar, which is why the triangle count is",
        "constant and the deflection changes only the time.",
        "",
        "| Linear deflection | Mode | Done? | Build ms | Mesh ms | Triangles | µs / triangle |",
        "|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        "## Control — does the parallel flag work at all?",
        "",
        f"`OSD_ThreadPool::DefaultPool()->NbThreads()` reports **{threads}** on this machine. The rows",
        "above show the parallel flag costing time rather than saving it on the box model; the rows",
        "below use spheres, where one face is thousands of triangles, to separate \"threading does not",
        "work in this build\" from \"the per-face work is too small to pay for the parallel path\".",
        "",
        "| Model | Mode | Done? | Mesh ms | Triangles |",
        "|---|---|---|---|---|",
    ] + control + [
        "",
    ]
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(text))
    print(f"wrote {out}")
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
