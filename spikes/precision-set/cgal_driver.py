"""CGAL driver for the precision set.

THROWAWAY SPIKE CODE. Run:

    pip install cgal==6.0.1.post202410241521
    python spikes/precision-set/cgal_driver.py --out spikes/precision-set/results/cgal.md

from the repository root. Standard library plus the `cgal` wheel.

The driver builds each case twice — once at the origin, once with `OFFSET`
applied to the input coordinates, which is what a project does when it models in
a national projection — runs union and intersection on both, translates the far
result back by −offset, and reports the worst nearest-neighbour vertex distance
and the volume difference, absolute and relative. Matching is nearest-neighbour
rather than by index, because a kernel is free to emit vertices in any order —
and this one demonstrably does (see the boolean-torture results, Probe E).

The kernel behind the binding is `Exact_predicates_inexact_constructions_kernel`
(Epick): predicates are exact, **constructions are rounded to `double`**. The
whole question this file answers is what that combination is worth at 500 km. Two
ingest settings are measured, as in the boolean-torture driver:

  * `f64 input` — the reference set's coordinates verbatim;
  * `f32-rounded input` — every coordinate through the nearest float32 and back
    before the `Point_3` is built, then stored as a double.

The second is the ADR-0006 question put directly: exact predicates are in force
on both rows, so anything the f32 row loses is lost to the *storage*, not to the
arithmetic that decides topology.

Operands are rebuilt for every repeat, every setting and both locations. PMP
corefinement modifies its operands in place, so reusing a pair would compare a
near result from pristine operands against a far result from corefined ones.

**Volumes at 500 km are computed on back-translated vertices.**
`reference.signed_volume` sums `x0*(y1*z2 − z1*y2)` over raw coordinates; at
5e5 m each term is ~1e17 against a sum of ~10, so the integrand loses ~1e-4 m³ to
cancellation before any library is involved. `spikes/precision-set/manifold_driver.py`
established this and mitigates it the same way; the last probe in this file
measures the artefact again on CGAL's own output so the choice stays auditable.
"""
from __future__ import annotations

import argparse
import os
import platform
import statistics
import struct
import subprocess
import sys
import time
from datetime import date

from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL import CGAL_Polygon_mesh_processing as PMP

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "reference"))

import precision_set as pset  # noqa: E402
from precision_set import OFFSET, offset, signed_volume  # noqa: E402

SETTINGS = [("f64 input", False), ("f32-rounded input", True)]

OPS = [
    ("union", PMP.corefine_and_compute_union),
    ("intersection", PMP.corefine_and_compute_intersection),
]


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def build(vertices, faces, round_f32: bool) -> Polyhedron_3:
    points = PMP.Point_3_Vector()
    points.reserve(len(vertices))
    for (x, y, z) in vertices:
        if round_f32:
            x, y, z = f32(x), f32(y), f32(z)
        points.append(Point_3(x, y, z))
    polygons = PMP.Polygon_Vector()
    for face in faces:
        indices = PMP.Int_Vector()
        indices.reserve(3)
        for i in face:
            indices.append(i)
        polygons.append(indices)
    poly = Polyhedron_3()
    PMP.polygon_soup_to_polygon_mesh(points, polygons, poly)
    return poly


def renumber(poly: Polyhedron_3) -> None:
    for i, v in enumerate(poly.vertices()):
        v.set_id(i)


def export(poly: Polyhedron_3):
    """See `boolean-torture/cgal_driver.py`'s `export` for why the facet walk is
    bounded by `facet_degree()` rather than by comparing halfedge handles."""
    index = {}
    verts = []
    for v in poly.vertices():
        p = v.point()
        index[v.id()] = len(verts)
        verts.append((p.x(), p.y(), p.z()))
    faces = []
    for facet in poly.facets():
        ring = []
        h = facet.halfedge()
        for _ in range(facet.facet_degree()):
            ring.append(index[h.vertex().id()])
            h = h.next()
        for k in range(1, len(ring) - 1):
            faces.append((ring[0], ring[k], ring[k + 1]))
    return verts, faces


def check_mesh(verts, faces):
    """Validity check, matching the boolean-torture driver's `check_mesh` so a
    mesh is judged "valid" the same way in both results files."""
    problems = []
    directed = {}
    for i0, i1, i2 in faces:
        for e in ((i0, i1), (i1, i2), (i2, i0)):
            directed[e] = directed.get(e, 0) + 1
    if any(n > 1 for n in directed.values()):
        problems.append("directed edge used more than once")
    unmatched = sum(1 for (u, v), n in directed.items() if directed.get((v, u), 0) != n)
    if unmatched:
        problems.append(f"{unmatched} edges without a matching opposite halfedge")
    used = set()
    for f in faces:
        used.update(f)
    if len(verts) - len(used):
        problems.append(f"{len(verts) - len(used)} loose verts")
    tiny = 0
    for i0, i1, i2 in faces:
        p0, p1, p2 = verts[i0], verts[i1], verts[i2]
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        cx = u[1] * v[2] - u[2] * v[1]
        cy = u[2] * v[0] - u[0] * v[2]
        cz = u[0] * v[1] - u[1] * v[0]
        if 0.5 * (cx * cx + cy * cy + cz * cz) ** 0.5 < 1e-14:
            tiny += 1
    if tiny:
        problems.append(f"{tiny} zero-area faces")
    return problems


def worst_nearest(a, b):
    """Worst nearest-neighbour distance, taken as the worse of both directions."""
    if not a or not b:
        return None

    def one_way(src, dst):
        worst = 0.0
        for p in src:
            best = min(
                (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 for q in dst
            )
            worst = max(worst, best ** 0.5)
        return worst

    return max(one_way(a, b), one_way(b, a))


def fmt(x, digits=12):
    if x is None:
        return "-"
    if x == 0:
        return "0"
    return f"{x:.{digits}g}"


def timed(fn, va, fa, vb, fb, round_f32, repeats):
    """Times `repeats` boolean calls on freshly rebuilt operands.

    Operand construction is outside the timed region — as in the boolean-torture
    driver — but inside the loop, because corefinement modifies its operands.
    Preconditions are checked on the operands of the last repeat and returned, so
    an operand that already violates a precondition cannot be absorbed into a
    result that then looks merely "empty".
    """
    times = []
    result = None
    returned = None
    pre_a = pre_b = None
    for _ in range(repeats):
        a = build(va, fa, round_f32)
        b = build(vb, fb, round_f32)
        pre_a = (a.is_closed(), PMP.does_self_intersect(a))
        pre_b = (b.is_closed(), PMP.does_self_intersect(b))
        result = Polyhedron_3()
        t0 = time.perf_counter()
        returned = fn(a, b, result)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    return statistics.median(times), result, bool(returned), pre_a, pre_b


def storage_round_trip():
    """What a coordinate costs to store in a `Point_3`, before any boolean.

    A coordinate is written into a `Point_3` and read back with `x()`. On the
    f64 row this is a pure double round trip and must be exact; the f32 row is
    the cost of arriving through a float32 interchange format. *ULP* is the
    distance to the next representable float32.
    """
    rows = []
    for c in (0.0, 1.0, 0.1, 1e-07, 500000.0, 500000.1, 500000.001, 500001.0):
        # float32 ULP from the IEEE-754 bit pattern, without numpy: the next
        # representable float32 above `c` is the one whose bit pattern is one
        # greater (for a non-negative finite value).
        bits = struct.unpack("<I", struct.pack("<f", f32(c)))[0]
        nxt = struct.unpack("<f", struct.pack("<I", bits + 1))[0]
        ulp = nxt - f32(c)
        r64 = Point_3(c, 0.0, 0.0).x()
        r32 = Point_3(f32(c), 0.0, 0.0).x()
        rows.append(
            "| `{c}` | {u} | {r64} | {e64} | {r32} | {e32} |".format(
                c=repr(c), u=fmt(ulp, 6),
                r64=fmt(r64, 17), e64=fmt(abs(r64 - c), 6),
                r32=fmt(r32, 17), e32=fmt(abs(r32 - c), 6),
            )
        )
    return rows


def operand_round_trip():
    rows = []
    for case in pset.cases():
        for label, round_f32 in SETTINGS:
            worst_near = 0.0
            worst_far = 0.0
            for mesh in (case.a, case.b):
                near = build(mesh.vertices, mesh.faces, round_f32)
                renumber(near)
                nv, _ = export(near)
                far_v = offset(mesh.vertices, case.offset)
                far = build(far_v, mesh.faces, round_f32)
                renumber(far)
                fv, _ = export(far)
                worst_near = max(worst_near, worst_nearest(nv, list(mesh.vertices)) or 0.0)
                worst_far = max(worst_far, worst_nearest(fv, far_v) or 0.0)
            rows.append(
                "| `{c}` | {p} | {n} | {v} | **{f}** |".format(
                    c=case.name, p=label,
                    n=len(case.a.vertices) + len(case.b.vertices),
                    v=fmt(worst_near, 6), f=fmt(worst_far, 6),
                )
            )
    return rows


def op_valid(result, returned, pre_a, pre_b, expected, problems):
    """The Valid? verdict for one boolean result, in the same shape the sibling
    drivers use: an operand that violated a precondition, a boolean that returned
    `False`, and an empty-but-unexpected result are all **not** valid."""
    if pre_a is not None and not pre_a[0]:
        return "**no** — operand A not closed"
    if pre_b is not None and not pre_b[0]:
        return "**no** — operand B not closed"
    if pre_a is not None and pre_a[1]:
        return "**no** — operand A self-intersects"
    if pre_b is not None and pre_b[1]:
        return "**no** — operand B self-intersects"
    if not returned:
        return "**no** — the boolean returned `False`"
    if result.size_of_facets() == 0:
        if abs(expected) < 1e-9:
            return "yes (empty, as expected)"
        return "**no** — empty result"
    if not result.is_closed():
        return "**no** — result is not closed"
    if problems:
        return "**no** — " + ", ".join(problems)
    return "yes"


def near_far_table(repeats):
    rows = []
    worst_overall = 0.0
    for case in pset.cases():
        for label, round_f32 in SETTINGS:
            for op_name, fn in OPS:
                ms_near, near, ret_near, npa, npb = timed(
                    fn, case.a.vertices, case.a.faces, case.b.vertices, case.b.faces,
                    round_f32, repeats,
                )
                fa = offset(case.a.vertices, case.offset)
                fb = offset(case.b.vertices, case.offset)
                ms_far, far, ret_far, fpa, fpb = timed(
                    fn, fa, case.a.faces, fb, case.b.faces, round_f32, repeats
                )

                if near.size_of_facets():
                    renumber(near)
                    nv, nf = export(near)
                else:
                    nv, nf = [], []
                if far.size_of_facets():
                    renumber(far)
                    fv, ff = export(far)
                else:
                    fv, ff = [], []
                dx, dy, dz = case.offset
                fv_back = [(x - dx, y - dy, z - dz) for (x, y, z) in fv]

                v_near = signed_volume(nv, nf) if nf else 0.0
                v_far = signed_volume(fv_back, ff) if ff else 0.0
                dv = v_far - v_near
                rel = dv / v_near if v_near else float("nan")
                dev = worst_nearest(nv, fv_back)
                if dev is not None:
                    worst_overall = max(worst_overall, dev)

                expected = (case.expected_volume_union if op_name == "union"
                            else case.expected_volume_intersection)
                pn = check_mesh(nv, nf) if nf else []
                pf = check_mesh(fv, ff) if ff else []
                near_ok = op_valid(near, ret_near, npa, npb, expected, pn)
                far_ok = op_valid(far, ret_far, fpa, fpb, expected, pf)
                valid = near_ok if near_ok == far_ok else f"near: {near_ok}; far: {far_ok}"

                rows.append(
                    "| `{c}` | {s} | {o} | {v} | {vn} / {vf} | {dv} ({rel} rel) | "
                    "**{dev} m** over {nn}/{nfv} v | {mn:.3f} / {mf:.3f} |".format(
                        c=case.name, s=label, o=op_name, v=valid,
                        vn=fmt(v_near), vf=fmt(v_far),
                        dv=fmt(dv, 6), rel=fmt(rel, 6),
                        dev=fmt(dev, 6), nn=len(nv), nfv=len(fv),
                        mn=ms_near, mf=ms_far,
                    )
                )
    return rows, worst_overall


def volume_formulation_probe():
    """How much of a far-field volume error belongs to the *measurement*.

    All four columns describe the same solid, on the f64 setting. *Near* is
    `reference.signed_volume` at the origin. *Near, coords shifted* adds the
    offset to every vertex of the near result and re-integrates: no boolean, no
    library, so the difference from the first column is pure cancellation in the
    divergence-theorem sum. *Far, raw* is the same function on the far result's
    own coordinates; *Far, back-translated* is the number the main table reports.

    CGAL's own `PMP::volume()` is **not** a fifth column here: it is the same
    divergence sum over raw coordinates with no compensation, so on the far
    result it carries the same artefact rather than avoiding it — which the
    `Far, PMP::volume()` column shows, and is why it is reported as data rather
    than as a reference value.
    """
    rows = []
    dx, dy, dz = OFFSET
    for case in pset.cases():
        for op_name, fn in OPS:
            near = Polyhedron_3()
            fn(build(case.a.vertices, case.a.faces, False),
               build(case.b.vertices, case.b.faces, False), near)
            far = Polyhedron_3()
            fn(build(offset(case.a.vertices, case.offset), case.a.faces, False),
               build(offset(case.b.vertices, case.offset), case.b.faces, False), far)
            if near.size_of_facets() == 0 or far.size_of_facets() == 0:
                continue
            renumber(near)
            renumber(far)
            nv, nf = export(near)
            fv, ff = export(far)
            shifted = [(x + dx, y + dy, z + dz) for (x, y, z) in nv]
            back = [(x - dx, y - dy, z - dz) for (x, y, z) in fv]
            rows.append(
                "| `{c}` | {o} | {v0} | {v1} | {v2} | {v3} | {v4} |".format(
                    c=case.name, o=op_name,
                    v0=fmt(signed_volume(nv, nf)),
                    v1=fmt(signed_volume(shifted, nf)),
                    v2=fmt(signed_volume(fv, ff)),
                    v3=fmt(signed_volume(back, ff)),
                    v4=fmt(PMP.volume(far) if far.is_closed() else None),
                )
            )
    return rows


def frame_probe():
    """The offset carried by a transform applied *after* the boolean, instead of
    by the input coordinates — the local-frame mitigation ADR-0006 proposes.

    The binding exposes no `Aff_transformation_3` on `Polyhedron_3`, so the move
    is applied by this driver, in `double`, to the exported vertices: it is the
    same arithmetic a tile frame would do on the way to a global CRS, and the
    point of the probe is what the *boolean* did, not who added the offset. The
    comparison is therefore between "boolean at the origin, then move" and
    "move, then boolean at 500 km".
    """
    rows = []
    dx, dy, dz = OFFSET
    for case in pset.cases():
        for label, round_f32 in SETTINGS:
            for op_name, fn in OPS:
                near = Polyhedron_3()
                fn(build(case.a.vertices, case.a.faces, round_f32),
                   build(case.b.vertices, case.b.faces, round_f32), near)
                far = Polyhedron_3()
                fn(build(offset(case.a.vertices, case.offset), case.a.faces, round_f32),
                   build(offset(case.b.vertices, case.offset), case.b.faces, round_f32), far)
                if near.size_of_facets() == 0 or far.size_of_facets() == 0:
                    rows.append(f"| `{case.name}` | {label} | {op_name} | - | - | - |")
                    continue
                renumber(near)
                renumber(far)
                nv, nf = export(near)
                fv, ff = export(far)
                moved = [(x + dx, y + dy, z + dz) for (x, y, z) in nv]
                rows.append(
                    "| `{c}` | {s} | {o} | {d} | {dm} | {v} |".format(
                        c=case.name, s=label, o=op_name,
                        d=fmt(worst_nearest(
                            nv, [(x - dx, y - dy, z - dz) for (x, y, z) in fv]), 6),
                        dm=fmt(worst_nearest(moved, fv), 6),
                        v=fmt(signed_volume(nv, nf)),
                    )
                )
    return rows


def environment(repeats):
    try:
        cpu = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=60,
        ).stdout.strip()
    except Exception:
        cpu = "unknown"
    try:
        import importlib.metadata as md
        version = md.version("cgal")
    except Exception:
        version = "unknown"
    return [
        "| Item | Value |",
        "|---|---|",
        f"| python | `{platform.python_version()}` |",
        f"| platform | `{platform.system()} {platform.release()} ({platform.machine()})` |",
        f"| cpu | `{cpu}` |",
        "| installed RAM | `32 GB` |",
        f"| `cgal` wheel | `{version}` |",
        f"| `CGAL_VERSION_NR` reported by the binding | `{PMP.CGAL_VERSION_NR}` (CGAL 6.0.1) |",
        f"| `CGAL_RELEASE_DATE` reported by the binding | `{PMP.CGAL_RELEASE_DATE}` |",
        "| CGAL source tag | `v6.0.1`, commit `50cfbde3b84dbeae8338268db2d78fe4fcb522de` |",
        "| kernel bound | `Exact_predicates_inexact_constructions_kernel` (Epick) |",
        f"| repeats per timing | {repeats} (median reported) |",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "cgal.md"))
    args = ap.parse_args()

    rows, worst = near_far_table(args.repeats)

    text = [
        "# Precision set — CGAL raw results",
        "",
        "Produced by [`../cgal_driver.py`](../cgal_driver.py). Raw data for",
        "`../FINDINGS.md` and for",
        "[`../../../docs/research/kernels/cgal.md`](../../../docs/research/kernels/cgal.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        f"**Offset:** `{OFFSET}` (500 km east, 500 km north — a plausible distance from a national",
        "projection's false origin to a project site).",
        "",
        "## Environment",
        "",
    ] + environment(args.repeats) + [
        "",
        "The kernel behind the binding is `Exact_predicates_inexact_constructions_kernel`",
        "(Epick): **predicates are exact, constructions are rounded to `double`**. Both",
        "settings below run with those exact predicates in force, so whatever the",
        "f32-rounded row loses is lost to the *storage*, not to the arithmetic that",
        "decides topology. That is the ADR-0006 question, asked of CGAL directly.",
        "",
        "| Setting | What it does |",
        "|---|---|",
        "| `f64 input` | the reference set's coordinates verbatim into `Point_3` |",
        "| `f32-rounded input` | every coordinate rounded to the nearest float32 and back before the `Point_3` is built; storage is still `double` |",
        "",
        "## Storage — the coordinate round trip, before any boolean",
        "",
        "A coordinate written into a `Point_3` and read back with `x()`. *ULP* is the",
        "distance to the next representable float32. There is no tolerance column: CGAL",
        "has no per-solid tolerance to report, which is itself the difference from",
        "[`results/manifold.md`](manifold.md), where the same table's tolerance column is",
        "the headline finding.",
        "",
        "| Coordinate | float32 ULP | f64 read back | f64 error | f32 read back | f32 error |",
        "|---|---|---|---|---|---|",
    ] + storage_round_trip() + [
        "",
        "Operand round trip per case, worst over all vertices of A and B, matched",
        "nearest-neighbour against the coordinates the reference set specifies:",
        "",
        "| Case | Setting | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |",
        "|---|---|---|---|---|",
    ] + operand_round_trip() + [
        "",
        "## Boolean results near vs far",
        "",
        "The offset is applied to the **vertex coordinates**. *Vertex deviation* is the",
        "worst nearest-neighbour distance after translating the far result back by",
        "−offset, taken as the worse of both matching directions. *ΔV* is the far volume",
        "minus the near volume, absolute and relative — the same two forms",
        "[`results/occt.md`](occt.md), [`results/blender.md`](blender.md) and",
        "[`results/manifold.md`](manifold.md) report.",
        "",
        "**Comparability caveat**, carried over from",
        "[`results/manifold.md`](manifold.md): the four candidates' *ΔV* columns measure",
        "the same thing (the far solid's volume, near vs. far) but are not computed by one",
        "formula. This driver and the Manifold and Blender drivers use",
        "`reference.signed_volume` over exported triangles; the OCCT driver uses OCCT's own",
        "`BRepGProp` integrator throughout.",
        "",
        "**The far volume is computed on the back-translated vertices**, for the reason",
        "the last probe measures: `reference.signed_volume` sums `x0*(y1*z2 − z1*y2)` over",
        "raw coordinates, and at 5e5 m each term is ~1e17 against a sum of ~10, so the",
        "integrand loses ~1e-4 m³ to cancellation *before any library is involved*.",
        "Reporting the raw-coordinate figure here would have charged that to CGAL.",
        "",
        "| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far |",
        "|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        f"**Worst vertex deviation over the whole set: {fmt(worst, 6)} m.** R-17's pass line is",
        "1e-6 m and its fail line is 1e-4 m.",
        "",
        "## Probe — origin-then-move against move-then-boolean",
        "",
        "The local-frame mitigation ADR-0006 proposes, measured on this candidate. The",
        "binding exposes no `Aff_transformation_3` on `Polyhedron_3`, so the 500 km move",
        "is applied by the driver, in `double`, to the exported vertices — the same",
        "arithmetic a tile frame would perform on the way out to a global CRS. Two",
        "distances per row, both against the same pair of results:",
        "",
        "* *far, back-translated vs. origin* — the main table's number, repeated here so",
        "  the two columns are read together;",
        "* *origin, moved out vs. far* — the mirror comparison, moving the origin result",
        "  into the far frame instead of bringing the far result home. The two must agree",
        "  to within the arithmetic of one f64 addition and subtraction at 5e5 m",
        "  (an ULP of ~5.8e-11 m); a large disagreement would mean the back-translation",
        "  itself is doing the work, which would invalidate the main table.",
        "",
        "| Case | Setting | Op | far → origin | origin → far | V at the origin |",
        "|---|---|---|---|---|---|",
    ] + frame_probe() + [
        "",
        "## Probe — how much of a far-field volume error is the measurement's own",
        "",
        "All five columns describe the **same solid**, on the f64 setting. *Near* is",
        "`reference.signed_volume` at the origin. *Near, coords shifted* adds the offset",
        "to every vertex of the near result and re-integrates: no boolean, no library, so",
        "the difference from the first column is pure floating-point cancellation in the",
        "divergence-theorem sum. *Far, raw* is the same function on the far result's own",
        "coordinates; *Far, back-translated* is the number the main table reports.",
        "",
        "*Far, `PMP::volume()`* is CGAL's own integrator on the far result. It is reported",
        "as data, not as a reference value: unlike Manifold's `Volume()`, which subtracts a",
        "common origin and applies Kahan compensation",
        "([`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294)),",
        "CGAL's is an uncompensated sum of tetrahedron volumes about the origin and",
        "therefore carries the same cancellation rather than avoiding it.",
        "",
        "| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `PMP::volume()` |",
        "|---|---|---|---|---|---|---|",
    ] + volume_formulation_probe() + [
        "",
    ]

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(text))
    print(f"wrote {out}")
    print(f"worst vertex deviation {worst:.6g} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
