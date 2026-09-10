"""CGAL driver for the boolean torture set.

THROWAWAY SPIKE CODE. Run:

    pip install cgal==6.0.1.post202410241521
    python spikes/boolean-torture/cgal_driver.py --out spikes/boolean-torture/results/cgal.md

from the repository root. Standard library plus the `cgal` wheel (the official
CGAL SWIG bindings); nothing else is imported.

What is measured, and what is not
--------------------------------
The `cgal` wheel exposes `CGAL_Polygon_mesh_processing` on `CGAL_Polyhedron_3`.
Its `Point_3::x()` returns a Python `float`, i.e. the bound kernel's number type
is `double`: this is `Exact_predicates_inexact_constructions_kernel` (Epick) —
**exact predicates, inexact constructions**. The wheel exposes no
`Nef_polyhedron_3` module and no Epeck-based mesh type, so the exact-construction
path is *not* measured here. Every claim about it in the note is labelled
*claimed* with a URL.

The boolean measured is PMP corefinement: `corefine_and_compute_union` /
`_intersection` / `_difference`. These functions **modify their operands in
place** (they corefine A and B against each other before extracting the result),
which this driver measures in Probe F and works around everywhere else by
rebuilding both operands for every repeat, every setting and every probe.

Settings
--------
CGAL has no tolerance parameter to sweep — there is nothing corresponding to
Manifold's `set_tolerance` — and the binding offers one kernel. The axis that is
available and that ADR-0006 actually asks about is the *ingest* precision:

  * `f64 input` — the reference set's coordinates verbatim;
  * `f32-rounded input` — every coordinate passed through the nearest float32
    and back before the `Point_3` is built, then stored as a double.

The second setting asks whether exact predicates rescue coordinates that were
rounded to float32 on the way in. It changes no case: the same ten pairs, the
same expected volumes.

Measurement conventions, kept identical to the sibling drivers
--------------------------------------------------------------
  * validity is this driver's own check on the **exported** triangles — closed,
    every directed edge used once with a matching opposite halfedge, no loose
    vertices, no triangle below 1e-14 m^2 — plus the boolean's own bool return;
  * volumes are `reference.signed_volume` over those exported triangles, with
    `PMP::volume()` recorded beside them and reported in the row when the two
    disagree by more than 1e-12 relative;
  * the identity residual |V(A) + V(B) - (V(union) + V(intersection))| is
    computed from the *measured* operand volumes;
  * timing is `time.perf_counter`, five repeats, median, with both operands
    rebuilt inside every repeat but outside the timed region — the boolean call
    itself is what is timed.
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
from fractions import Fraction

from CGAL.CGAL_Kernel import Point_2, Point_3
from CGAL.CGAL_Kernel import orientation as cgal_orientation
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL import CGAL_Polygon_mesh_processing as PMP

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "reference"))

import boolean_torture_set as torture  # noqa: E402
from boolean_torture_set import signed_volume  # noqa: E402

# (label, whether to round every input coordinate through float32 first)
SETTINGS = [
    ("Epick, f64 input", False),
    ("Epick, f32-rounded input", True),
]

# Same thresholds and the same meaning as in `manifold_driver.py` /
# `results/blender.md`, so the candidates are judged the same way.
DELTA_FLOOR = 1e-9
CORRECT_TOL = 1e-6


def f32(x: float) -> float:
    """The nearest float32 to `x`, returned as a Python float (a double)."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def build(mesh, round_f32: bool) -> Polyhedron_3:
    """Reference `Mesh` -> `Polyhedron_3`, via PMP's polygon-soup converter.

    No welding, no repair, no orientation fixing: `orient_polygon_soup` is
    deliberately *not* called, because whether the reference set's operands are
    already consistently oriented is part of what is being measured.
    """
    points = PMP.Point_3_Vector()
    points.reserve(len(mesh.vertices))
    for (x, y, z) in mesh.vertices:
        if round_f32:
            x, y, z = f32(x), f32(y), f32(z)
        points.append(Point_3(x, y, z))
    polygons = PMP.Polygon_Vector()
    for face in mesh.faces:
        indices = PMP.Int_Vector()
        indices.reserve(3)
        for i in face:
            indices.append(i)
        polygons.append(indices)
    poly = Polyhedron_3()
    PMP.polygon_soup_to_polygon_mesh(points, polygons, poly)
    return poly


def export(poly: Polyhedron_3):
    """Exported triangles as (vertices, faces) in the shape `reference` uses.

    Facets are walked through their halfedge circulator; `h.vertex()` is the
    halfedge's target, and the cycle runs counter-clockwise around the facet, so
    the triangle comes out with the winding CGAL stores. A facet with more than
    three vertices is fanned from its first vertex and counted, so a non-triangular
    result cannot be silently turned into triangles without being reported.

    The walk is bounded by `facet_degree()` rather than by comparing halfedge
    handles: a SWIG `Halfedge_handle` is a fresh Python object wrapping a *copy*
    of the C++ handle on every call, so `h is start` and `h.this == start.this`
    are both false forever and a "walk until you come back" loop never ends.
    """
    index = {}
    verts = []
    for v in poly.vertices():
        p = v.point()
        index[v.id()] = len(verts)
        verts.append((p.x(), p.y(), p.z()))
    faces = []
    non_triangular = 0
    for facet in poly.facets():
        ring = []
        h = facet.halfedge()
        for _ in range(facet.facet_degree()):
            ring.append(index[h.vertex().id()])
            h = h.next()
        if len(ring) > 3:
            non_triangular += 1
        for k in range(1, len(ring) - 1):
            faces.append((ring[0], ring[k], ring[k + 1]))
    return verts, faces, non_triangular


def renumber(poly: Polyhedron_3) -> None:
    """Give every vertex a distinct id, so `export` can index them.

    `Polyhedron_3` vertex ids are not maintained by the boolean; the halfedge
    data structure identifies a vertex by its handle. This assigns ids once,
    immediately before an export, and is the only mutation this driver performs
    on a result.
    """
    for i, v in enumerate(poly.vertices()):
        v.set_id(i)


def check_mesh(verts, faces):
    """This driver's own validity check, character for character the check the
    Manifold and Blender drivers apply, so "valid" means the same thing in all
    three results files. Returns a list of complaints."""
    problems = []
    directed = {}
    for i0, i1, i2 in faces:
        for e in ((i0, i1), (i1, i2), (i2, i0)):
            directed[e] = directed.get(e, 0) + 1
    repeated = sum(1 for n in directed.values() if n > 1)
    if repeated:
        problems.append(f"{repeated} directed edges used more than once")
    boundary = 0
    for (u, v), n in directed.items():
        if directed.get((v, u), 0) != n:
            boundary += 1
    if boundary:
        problems.append(f"{boundary} edges without a matching opposite halfedge")
    used = set()
    for f in faces:
        used.update(f)
    loose = len(verts) - len(used)
    if loose:
        problems.append(f"{loose} loose verts")
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


def preconditions(poly: Polyhedron_3):
    """The preconditions PMP corefinement documents, as far as the binding
    exposes them. `does_bound_a_volume` is **not** in the binding's surface —
    that absence is recorded rather than worked around."""
    closed = poly.is_closed()
    pure_tri = poly.is_pure_triangle()
    self_int = PMP.does_self_intersect(poly)
    # `is_outward_oriented` has `is_closed` as its own precondition.
    outward = PMP.is_outward_oriented(poly) if closed else None
    return {
        "closed": closed,
        "pure_triangle": pure_tri,
        "self_intersecting": self_int,
        "outward": outward,
        "valid_hds": poly.is_valid(),
    }


OPS = [
    ("union", PMP.corefine_and_compute_union),
    ("intersection", PMP.corefine_and_compute_intersection),
]


def run_boolean(case, round_f32, fn):
    """One boolean on fresh operands. Returns (returned_bool, result_polyhedron)."""
    a = build(case.a, round_f32)
    b = build(case.b, round_f32)
    out = Polyhedron_3()
    returned = fn(a, b, out)
    return returned, out


def measure(case, round_f32, repeats):
    a = build(case.a, round_f32)
    b = build(case.b, round_f32)
    pre_a = preconditions(a)
    pre_b = preconditions(b)
    renumber(a)
    renumber(b)
    va, fa, _ = export(a)
    vb, fb, _ = export(b)
    out = {
        "pre_a": pre_a,
        "pre_b": pre_b,
        "vol_a": signed_volume(va, fa),
        "vol_b": signed_volume(vb, fb),
        "pmp_vol_a": PMP.volume(a) if pre_a["closed"] else None,
        "pmp_vol_b": PMP.volume(b) if pre_b["closed"] else None,
    }

    for op_name, fn in OPS:
        times = []
        returned = None
        result = None
        for _ in range(repeats):
            fresh_a = build(case.a, round_f32)
            fresh_b = build(case.b, round_f32)
            result = Polyhedron_3()
            t0 = time.perf_counter()
            returned = fn(fresh_a, fresh_b, result)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)
        empty = result.size_of_facets() == 0
        if empty:
            verts, faces, non_tri = [], [], 0
        else:
            renumber(result)
            verts, faces, non_tri = export(result)
        out[op_name] = {
            "ms": statistics.median(times),
            "returned": bool(returned),
            "empty": empty,
            "verts": len(verts),
            "tris": len(faces),
            "non_triangular_facets": non_tri,
            "closed": result.is_closed(),
            "volume": signed_volume(verts, faces) if faces else 0.0,
            "own_volume": PMP.volume(result) if (faces and result.is_closed()) else None,
            "problems": check_mesh(verts, faces) if faces else [],
        }
    return out


def fmt(x, digits=12):
    if x is None:
        return "-"
    if x == 0:
        return "0"
    return f"{x:.{digits}g}"


def delta_note(measured, expected):
    d = measured - expected
    if abs(d) > max(DELTA_FLOOR, DELTA_FLOOR * abs(expected)):
        return f"{d:.3g}"
    return None


def valid_cell(entry, expected_volume):
    """The Valid? cell, in the same shape the sibling results files use."""
    if not entry["returned"]:
        return "**no** — the boolean returned `False`"
    if entry["empty"]:
        if abs(expected_volume) <= DELTA_FLOOR:
            return "yes (empty, as expected)"
        return "**no** — empty result"
    if not entry["closed"]:
        return "**no** — result is not closed"
    if entry["problems"]:
        return "**no** — " + ", ".join(entry["problems"])
    return "yes"


# --- probes ---------------------------------------------------------------------


def component_count(poly) -> int:
    """`PMP::connected_components(P)` returns one component id per face; the number
    of components is the number of distinct ids."""
    return len(set(int(x) for x in PMP.connected_components(poly)))


def probe_multi_shell():
    """`wall_with_openings` B is one mesh of twelve disconnected closed shells."""
    case = {c.name: c for c in torture.cases()}["wall_with_openings"]
    rows = []
    ops = [
        ("union", PMP.corefine_and_compute_union),
        ("intersection", PMP.corefine_and_compute_intersection),
        ("difference", PMP.corefine_and_compute_difference),
    ]
    for label, round_f32 in SETTINGS:
        b_probe = build(case.b, round_f32)
        comps_b = component_count(b_probe)
        for op_name, fn in ops:
            a = build(case.a, round_f32)
            b = build(case.b, round_f32)
            result = Polyhedron_3()
            returned = fn(a, b, result)
            if result.size_of_facets() == 0:
                rows.append(
                    f"| {label} | {op_name} | {comps_b} | {returned} | - | 0 | 0 | - | empty |"
                )
                continue
            renumber(result)
            verts, faces, _ = export(result)
            comps = component_count(result)
            problems = check_mesh(verts, faces)
            rows.append(
                "| {l} | {o} | {cb} | {r} | {v} | {nv} | {nt} | {c} | {ok} |".format(
                    l=label, o=op_name, cb=comps_b, r=returned,
                    v=fmt(signed_volume(verts, faces)),
                    nv=len(verts), nt=len(faces), c=comps,
                    ok="yes" if not problems else "**no** — " + ", ".join(problems),
                )
            )
    return rows


def probe_sliver():
    """The 1e-7 m slab. CGAL has no tolerance knob, so the question is not
    "at what tolerance does it vanish" but "does a feature three orders of
    magnitude below the model size survive the boolean at all"."""
    case = {c.name: c for c in torture.cases()}["sliver"]
    rows = []
    for label, round_f32 in SETTINGS:
        b = build(case.b, round_f32)
        renumber(b)
        vb, fb, _ = export(b)
        thickness = max(p[2] for p in vb) - min(p[2] for p in vb)
        for op_name, fn in OPS:
            returned, result = run_boolean(case, round_f32, fn)
            if result.size_of_facets() == 0:
                rows.append(
                    f"| {label} | {op_name} | {fmt(thickness)} | {fmt(signed_volume(vb, fb))} | "
                    f"{returned} | **empty** | 0 |"
                )
                continue
            renumber(result)
            verts, faces, _ = export(result)
            rows.append(
                "| {l} | {o} | {t} | {vb} | {r} | {v} | {nt} |".format(
                    l=label, o=op_name, t=fmt(thickness), vb=fmt(signed_volume(vb, fb)),
                    r=returned, v=fmt(signed_volume(verts, faces)), nt=len(faces),
                )
            )
    return rows


def probe_t_junction():
    """The T-junction operand: what the corefinement path does with input that
    violates its preconditions, and whether `stitch_borders` repairs it."""
    case = {c.name: c for c in torture.cases()}["near_degenerate_triangle"]
    rows = []
    for label, round_f32 in SETTINGS:
        b = build(case.b, round_f32)
        b.normalize_border()
        pre = preconditions(b)
        rows.append(
            "| {l} | operand B as built | {c} | {s} | {o} | {bh} | - |".format(
                l=label, c=pre["closed"], s=pre["self_intersecting"],
                o="n/a (not closed)" if pre["outward"] is None else pre["outward"],
                bh=b.size_of_border_halfedges(),
            )
        )
        for op_name, fn in OPS:
            returned, result = run_boolean(case, round_f32, fn)
            rows.append(
                "| {l} | A {o} B | - | - | - | - | returned `{r}`, {nf} facets |".format(
                    l=label, o="∪" if op_name == "union" else "∩",
                    r=returned, nf=result.size_of_facets(),
                )
            )
    # Does the repair helper the manual points at fix it?
    b = build(case.b, False)
    before = (b.size_of_vertices(), b.size_of_facets())
    PMP.stitch_borders(b)
    b.normalize_border()
    after_pre = preconditions(b)
    rows.append(
        "| Epick, f64 input | operand B after `stitch_borders` | {c} | {s} | {o} | {bh} | "
        "{v0}v/{f0}f → {v1}v/{f1}f |".format(
            c=after_pre["closed"], s=after_pre["self_intersecting"],
            o="n/a (not closed)" if after_pre["outward"] is None else after_pre["outward"],
            bh=b.size_of_border_halfedges(),
            v0=before[0], f0=before[1],
            v1=b.size_of_vertices(), f1=b.size_of_facets(),
        )
    )
    return rows


def probe_determinism(runs):
    """Same input, N runs, how many distinct results?"""
    by_name = {c.name: c for c in torture.cases()}
    rows = []
    for case_name, op_name, fn in (
        ("overlap_half", "union", PMP.corefine_and_compute_union),
        ("wall_with_openings", "union", PMP.corefine_and_compute_union),
        ("wall_with_openings", "difference", PMP.corefine_and_compute_difference),
        ("sliver", "intersection", PMP.corefine_and_compute_intersection),
    ):
        case = by_name[case_name]
        signatures = {}
        geometries = set()
        orders = set()
        for _ in range(runs):
            _, result = run_boolean(case, False, fn)
            renumber(result)
            verts, faces, _ = export(result)
            key = (len(verts), len(faces), repr(signed_volume(verts, faces)))
            signatures[key] = signatures.get(key, 0) + 1
            # The *geometry* signature is order-independent: the sorted multiset
            # of vertex coordinates. If this is constant while the volume sum is
            # not, the solid is the same and only the order it is emitted in
            # varies — and `signed_volume` sums in emission order, so an ordering
            # change alone moves the last bits of the sum.
            geometries.add(tuple(sorted(verts)))
            # The *order* signature is the emitted vertex list itself.
            orders.add(tuple(verts))
        detail = "; ".join(
            f"{k[0]}v/{k[1]}f/V={k[2]} x{n}" for k, n in signatures.items()
        )
        rows.append(
            f"| `{case_name}` | {op_name} | {runs} | {len(signatures)} | "
            f"{len(geometries)} | {len(orders)} | {detail} |"
        )
    return rows


def probe_operand_mutation():
    """Corefinement modifies its operands. Measured, not assumed."""
    rows = []
    for case in torture.cases():
        a = build(case.a, False)
        b = build(case.b, False)
        before = (a.size_of_vertices(), a.size_of_facets(),
                  b.size_of_vertices(), b.size_of_facets())
        out = Polyhedron_3()
        returned = PMP.corefine_and_compute_union(a, b, out)
        after = (a.size_of_vertices(), a.size_of_facets(),
                 b.size_of_vertices(), b.size_of_facets())
        rows.append(
            "| `{c}` | {r} | {a0}v/{f0}f | {a1}v/{f1}f | {b0}v/{g0}f | {b1}v/{g1}f | {ch} |".format(
                c=case.name, r=returned,
                a0=before[0], f0=before[1], a1=after[0], f1=after[1],
                b0=before[2], g0=before[3], b1=after[2], g1=after[3],
                ch="**yes**" if before != after else "no",
            )
        )
    return rows


def probe_contacts():
    """The three cases whose operands touch without overlapping.

    `shared_edge` is the one case in the set where the union CGAL is asked for
    would have a non-manifold edge — four facets meeting along the line
    x=1, y=1 — and `Polyhedron_3` cannot hold that. `touching_vertex` and
    `coplanar_faces` touch too, but in ways a 2-manifold surface *can* represent.
    This probe records what comes out of each, so the refusal in the main table
    is read against the two contacts that succeeded rather than on its own.
    """
    by_name = {c.name: c for c in torture.cases()}
    rows = []
    for case_name in ("coplanar_faces", "shared_edge", "touching_vertex"):
        case = by_name[case_name]
        for op_name, fn in OPS:
            returned, result = run_boolean(case, False, fn)
            if result.size_of_facets() == 0:
                rows.append(
                    f"| `{case_name}` | {op_name} | {returned} | 0 | 0 | - | - | empty result |"
                )
                continue
            renumber(result)
            verts, faces, _ = export(result)
            problems = check_mesh(verts, faces)
            rows.append(
                "| `{c}` | {o} | {r} | {nv} | {nt} | {cc} | {v} | {ok} |".format(
                    c=case_name, o=op_name, r=returned,
                    nv=len(verts), nt=len(faces), cc=component_count(result),
                    v=fmt(signed_volume(verts, faces)),
                    ok="valid" if not problems else "**" + ", ".join(problems) + "**",
                )
            )
    return rows


def _naive_orient2d(p, q, r):
    """The determinant a boolean would compute without an exact predicate."""
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _exact_orient2d(p, q, r):
    """The same determinant over exact rationals: the oracle."""
    fp = [Fraction(c) for c in p]
    fq = [Fraction(c) for c in q]
    fr = [Fraction(c) for c in r]
    return (fq[0] - fp[0]) * (fr[1] - fp[1]) - (fq[1] - fp[1]) * (fr[0] - fp[0])


def _sign(x):
    return (x > 0) - (x < 0)


def probe_exact_predicates(grid=64):
    """Do CGAL's predicates decide `orientation` correctly where plain double
    arithmetic does not?

    The construction is the standard one from the robustness literature: the
    *first* argument sweeps a lattice whose spacing is one ULP of 0.5, and the
    other two points are fixed and exactly representable.

        p_ij = (0.5 + i·u, 0.5 + j·u)    u = 2⁻⁵³
        q    = (12, 12)
        r    = (24, 24)

    Over the rationals the determinant is exactly `12·u·(j − i)`, so the correct
    answer is `sign(j − i)` — known in closed form, and reproduced independently
    by the `Fraction` oracle. It is the *subtractions* that break the plain
    double evaluation: `12 − (0.5 + i·u)` has to be rounded, because 11.5 lies in
    a binade whose ULP is 2⁻⁴⁹, sixteen times the lattice spacing. The rounding
    error is therefore the same size as the determinant itself.

    Three answers per lattice point: the naive double determinant's sign, CGAL's
    `orientation(Point_2, Point_2, Point_2)`, and the same determinant over
    `fractions.Fraction`, which is exact and is the oracle. Every coordinate is a
    dyadic rational, so `Fraction(float)` is lossless. The counts are
    disagreements with the oracle.
    """
    ulp = 2.0 ** -53  # one ULP of 0.5
    q = (12.0, 12.0)
    r = (24.0, 24.0)
    naive_wrong = 0
    cgal_wrong = 0
    closed_form_disagreements = 0
    total = 0
    naive_examples = []
    for i in range(grid):
        for j in range(grid):
            p = (0.5 + i * ulp, 0.5 + j * ulp)
            truth = _sign(_exact_orient2d(p, q, r))
            if truth != _sign(j - i):
                closed_form_disagreements += 1
            naive = _sign(_naive_orient2d(p, q, r))
            # `CGAL_Kernel.orientation` returns the CGAL `Orientation` enum,
            # whose values are literally -1 / 0 / +1 (RIGHT_TURN / COLLINEAR /
            # LEFT_TURN) — checked in `probe_orientation_mapping`, not assumed.
            cgal_sign = int(cgal_orientation(Point_2(*p), Point_2(*q), Point_2(*r)))
            total += 1
            if naive != truth:
                naive_wrong += 1
                if len(naive_examples) < 3:
                    naive_examples.append((p, truth, naive))
            if cgal_sign != truth:
                cgal_wrong += 1
    return {
        "total": total,
        "naive_wrong": naive_wrong,
        "cgal_wrong": cgal_wrong,
        "closed_form_disagreements": closed_form_disagreements,
        "examples": naive_examples,
        "ulp": ulp,
        "grid": grid,
        "q": q,
        "r": r,
    }


def probe_orientation_mapping():
    """Record what `CGAL_Kernel.orientation` returns for three known configurations,
    so the sign mapping used in the previous probe is shown rather than assumed."""
    rows = []
    for label, (p, q, r) in (
        ("left turn", ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))),
        ("right turn", ((0.0, 0.0), (1.0, 0.0), (0.0, -1.0))),
        ("collinear", ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0))),
    ):
        got = cgal_orientation(Point_2(*p), Point_2(*q), Point_2(*r))
        rows.append(f"| {label} | `{int(got)}` | {_sign(_naive_orient2d(p, q, r))} |")
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
        "| kernel bound | `Exact_predicates_inexact_constructions_kernel` (Epick) — see Probe G |",
        f"| repeats per timing | {repeats} (median reported) |",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--determinism-runs", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "cgal.md"))
    args = ap.parse_args()

    rows = []
    construction = []
    n_valid = 0
    n_total = 0
    per_setting = {label: {"valid": 0, "correct": 0, "worst": 0.0} for label, _ in SETTINGS}

    for case in torture.cases():
        for label, round_f32 in SETTINGS:
            r = measure(case, round_f32, args.repeats)
            for operand, pre, vol, pmp_vol in (
                ("A", r["pre_a"], r["vol_a"], r["pmp_vol_a"]),
                ("B", r["pre_b"], r["vol_b"], r["pmp_vol_b"]),
            ):
                construction.append(
                    "| `{c}` | {n} | {s} | {cl} | {tri} | {si} | {ow} | {v} | {pv} |".format(
                        c=case.name, n=operand, s=label,
                        cl=pre["closed"], tri=pre["pure_triangle"],
                        si=pre["self_intersecting"],
                        ow="n/a" if pre["outward"] is None else pre["outward"],
                        v=fmt(vol), pv=fmt(pmp_vol),
                    )
                )
            u, i = r["union"], r["intersection"]
            identity = abs((r["vol_a"] + r["vol_b"]) - (u["volume"] + i["volume"]))
            if u["returned"] and i["returned"]:
                per_setting[label]["worst"] = max(per_setting[label]["worst"], identity)
            correct = (
                abs(u["volume"] - case.expected_volume_union)
                <= CORRECT_TOL * max(1.0, abs(case.expected_volume_union))
                and abs(i["volume"] - case.expected_volume_intersection)
                <= CORRECT_TOL * max(1.0, abs(case.expected_volume_intersection))
            )
            if correct:
                per_setting[label]["correct"] += 1

            notes = []
            for op_label, entry in (("∪", u), ("∩", i)):
                if entry["tris"] and abs(entry["volume"]) < 1e-12:
                    notes.append(
                        f"{op_label} is a non-empty zero-volume shell ({entry['tris']} tris)"
                    )
                if entry["non_triangular_facets"]:
                    notes.append(
                        f"{op_label} has {entry['non_triangular_facets']} non-triangular facets"
                    )
            du = delta_note(u["volume"], case.expected_volume_union)
            di = delta_note(i["volume"], case.expected_volume_intersection)
            if du:
                notes.append(f"Δ∪={du}")
            if di:
                notes.append(f"Δ∩={di}")
            if not r["pre_a"]["closed"]:
                notes.append("operand A is **not closed**")
            if not r["pre_b"]["closed"]:
                notes.append("operand B is **not closed**")
            if r["pre_a"]["self_intersecting"]:
                notes.append("operand A **self-intersects**")
            if r["pre_b"]["self_intersecting"]:
                notes.append("operand B **self-intersects**")
            for op_label, entry in (("∪", u), ("∩", i)):
                if entry["own_volume"] is not None and abs(
                    entry["own_volume"] - entry["volume"]
                ) > 1e-12 * max(1.0, abs(entry["volume"])):
                    notes.append(f"PMP::volume(){op_label}={fmt(entry['own_volume'])}")

            vu = valid_cell(u, case.expected_volume_union)
            vi = valid_cell(i, case.expected_volume_intersection)
            if vu.startswith("yes") and vi.startswith("yes"):
                valid = "yes"
                n_valid += 1
                per_setting[label]["valid"] += 1
            elif vu.startswith("yes"):
                valid = f"∪ ok; ∩: {vi}"
            elif vi.startswith("yes"):
                valid = f"∪: {vu}; ∩ ok"
            else:
                valid = f"∪: {vu}; ∩: {vi}"
            n_total += 1

            rows.append(
                "| `{c}` | {s} | {v} | {vu} | {vi} | {id} | {mu:.3f} / {mi:.3f} | {n} |".format(
                    c=case.name, s=label, v=valid,
                    vu=fmt(u["volume"]), vi=fmt(i["volume"]),
                    id=fmt(identity, 3), mu=u["ms"], mi=i["ms"],
                    n="; ".join(notes) if notes else "-",
                )
            )

    pred = probe_exact_predicates()

    text = [
        "# Boolean torture set — CGAL raw results",
        "",
        "Produced by [`../cgal_driver.py`](../cgal_driver.py). This file is raw data for",
        "`../FINDINGS.md` (assembled once every candidate has run) and for",
        "[`../../../docs/research/kernels/cgal.md`](../../../docs/research/kernels/cgal.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        "",
        "## Environment",
        "",
    ] + environment(args.repeats) + [
        "",
        "**What is measured here is the Epick corefinement path and nothing else.** The",
        "`cgal` wheel exposes no `Nef_polyhedron_3` module and no",
        "`Exact_predicates_exact_constructions_kernel` mesh type, so CGAL's",
        "exact-*construction* path — the one `problems.md` P-03 is about — is **not**",
        "measured in this file. Every claim about it in the note is labelled *claimed*.",
        "",
        "## Settings",
        "",
        "CGAL exposes no tolerance parameter, so there is nothing here corresponding to",
        "the tolerance sweep in [`results/manifold.md`](manifold.md). The axis that is",
        "available, and the one ADR-0006 asks about, is the precision of the coordinates",
        "handed in:",
        "",
        "| Setting | What it does |",
        "|---|---|",
        "| `Epick, f64 input` | the reference set's coordinates verbatim into `Point_3` |",
        "| `Epick, f32-rounded input` | every coordinate rounded to the nearest float32 (`struct.pack('<f', …)`) and back before the `Point_3` is built; storage is still `double` |",
        "",
        "The second setting asks a question no other candidate can answer as cleanly: do",
        "exact predicates rescue coordinates that were rounded to float32 on the way in?",
        "It changes no case — the same ten pairs, the same analytic expectations.",
        "",
        "## Construction of the operands",
        "",
        "`reference/boolean_torture_set.py` verbatim into a `PMP::Point_3_Vector` /",
        "`PMP::Polygon_Vector` soup, then `polygon_soup_to_polygon_mesh` into a",
        "`Polyhedron_3`. `orient_polygon_soup` is deliberately **not** called: whether the",
        "reference set's operands are already consistently oriented is part of what is",
        "being measured. *Volume* is `reference.signed_volume` over the exported",
        "triangles; *PMP::volume* is CGAL's own integrator, `PMP::volume()`, which has",
        "`is_closed` as a precondition and is therefore blank for an open surface.",
        "",
        "The corefinement functions document four preconditions on each operand: it is a",
        "triangulated surface mesh, it does not self-intersect, and it bounds a volume",
        "(which implies closed and outward-oriented). The binding exposes",
        "`is_closed`, `is_pure_triangle`, `does_self_intersect` and `is_outward_oriented`",
        "— but **not** `does_bound_a_volume`, so the last precondition cannot be checked",
        "through this binding at all. That absence is recorded, not worked around.",
        "",
        "| Case | Operand | Setting | Closed | Pure triangle | Self-intersects | Outward | Volume | PMP::volume |",
        "|---|---|---|---|---|---|---|---|---|",
    ] + construction + [
        "",
        "## Boolean results",
        "",
        "One row per case × setting. *Valid?* is this driver's own check on the exported",
        "result mesh — every directed edge used once with a matching opposite halfedge",
        "(closed, manifold and consistently wound), no loose vertices, no triangle below",
        "1e-14 m² — plus `Polyhedron_3::is_closed()` and the boolean's own `bool` return",
        "value. *Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` computed from the",
        "**measured** operand volumes. Times are milliseconds, median of the repeats,",
        "union / intersection; both operands are rebuilt inside every repeat (PMP",
        "corefinement modifies its operands in place — Probe F) but outside the timed",
        "region, so what is timed is the boolean call.",
        "",
        "| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |",
        "|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        f"**Summary:** {n_valid} of {n_total} case×setting combinations produced a result this",
        "driver's check accepts for both the union and the intersection.",
        "",
        "*Valid* and *correct* are different questions and are counted separately, on the",
        "same definitions [`results/blender.md`](blender.md) and",
        "[`results/manifold.md`](manifold.md) use. *Correct* is both volumes within",
        f"`{CORRECT_TOL:g} * max(1.0, abs(expected))` of the analytic expectation — relative above",
        "1 m³, an absolute floor below it, so a case whose expected volume is 0 or 1e-07 m³",
        f"is not judged on a relative error it cannot meet. The Δ notes above use {DELTA_FLOOR:g} instead.",
        "",
        "| Setting | Valid (closed manifold) | Numerically correct | Worst identity residual (refusals excluded) |",
        "|---|---|---|---|",
    ] + [
        "| {s} | {v} / {n} | {c} / {n} | {w} |".format(
            s=label, v=per_setting[label]["valid"], c=per_setting[label]["correct"],
            n=len(torture.cases()), w=fmt(per_setting[label]["worst"], 3),
        )
        for label, _ in SETTINGS
    ] + [
        "",
        "## Probe A — the twelve-shell operand",
        "",
        "`wall_with_openings` B is **one mesh with twelve disconnected closed shells**, the",
        "same construction [`results/blender.md`](blender.md) and",
        "[`results/manifold.md`](manifold.md) used. *Components* is",
        "`PMP::connected_components`. The analytic expectation for the difference is",
        "V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.",
        "",
        "| Setting | Operation | Components in B | Returned | V(result) | Verts | Tris | Components in result | Valid? |",
        "|---|---|---|---|---|---|---|---|---|",
    ] + probe_multi_shell() + [
        "",
        "## Probe B — the 1e-7 m slab",
        "",
        "`sliver` B is a 1 m × 1 m × 1e-7 m slab. CGAL has no tolerance to raise, so the",
        "question [`results/manifold.md`](manifold.md) Probe B asks (at what tolerance does",
        "the slab vanish?) has no CGAL form. What can be asked instead is whether a feature",
        "seven orders of magnitude below the operand's size survives ingest and the boolean",
        "at all. *Thickness as stored* is read back from the constructed `Polyhedron_3`.",
        "",
        "| Setting | Operation | Thickness as stored | V(B) as stored | Returned | V(result) | Tris |",
        "|---|---|---|---|---|---|---|",
    ] + probe_sliver() + [
        "",
        "## Probe C — the T-junction operand",
        "",
        "`near_degenerate_triangle` B has a vertex lying *on* an edge (the reference set",
        "splits the cube's top face by inserting a vertex on the edge v5→v6), so three",
        "halfedges have no twin. Manifold refuses it outright with `Error::NotManifold`",
        "and an empty result; Blender's Manifold solver returns the unmodified first",
        "operand. This probe records what the CGAL corefinement path does — whether the",
        "operand is even *built*, which precondition it violates, what the boolean returns,",
        "and whether `PMP::stitch_borders` (the repair the manual points at for meshes",
        "whose borders should be joined) repairs it.",
        "",
        "*Border halfedges* is `size_of_border_halfedges()` after `normalize_border()`;",
        "without that call `Polyhedron_3` does not maintain the count.",
        "",
        "| Setting | Input | Closed | Self-intersects | Outward | Border halfedges | Boolean |",
        "|---|---|---|---|---|---|---|",
    ] + probe_t_junction() + [
        "",
        "## Probe D — the three contact cases",
        "",
        "Three cases in the set have operands that touch without overlapping, and the",
        "main table shows CGAL refusing exactly one of them. This probe puts the three",
        "side by side so the refusal is read in context. `shared_edge` is the case whose",
        "union would have a **non-manifold edge** — four facets meeting along the line",
        "x=1, y=1 — which a `Polyhedron_3`, a halfedge data structure, cannot hold;",
        "`touching_vertex` and `coplanar_faces` touch in ways a 2-manifold surface can",
        "represent. *Components* is the distinct-id count from `PMP::connected_components`.",
        "",
        "| Case | Op | Returned | Verts | Tris | Components | V(result) | This driver's check |",
        "|---|---|---|---|---|---|---|---|",
    ] + probe_contacts() + [
        "",
        "## Probe E — run-to-run determinism",
        "",
        "The same operands, rebuilt from the reference set and run N times in one process.",
        "*Signatures* is the number of distinct `(verts, tris, volume)` triples observed; a",
        "deterministic library produces exactly one. Asked of every candidate because a",
        "kernel whose output depends on scheduling cannot be diffed, cached or",
        "regression-tested.",
        "",
        "Two further columns separate two different things a varying signature could mean.",
        "*Distinct geometries* counts distinct **sorted** multisets of vertex coordinates —",
        "order-independent, so it changes only if the solid itself changed. *Distinct",
        "emission orders* counts distinct vertex lists in the order CGAL emitted them.",
        "`reference.signed_volume` sums in emission order, so a pure reordering moves the",
        "last bits of the sum without moving a single vertex; the two columns say which of",
        "the two happened.",
        "",
        "| Case | Op | Runs | Signatures | Distinct geometries | Distinct emission orders | Distinct results |",
        "|---|---|---|---|---|---|---|",
    ] + probe_determinism(args.determinism_runs) + [
        "",
        "## Probe F — corefinement modifies its operands",
        "",
        "`corefine_and_compute_union(A, B, out)` corefines A and B against each other",
        "*in place* before extracting the result: after the call, A and B carry the",
        "intersection polylines as new vertices and facets. Every driver loop in this file",
        "rebuilds both operands per repeat because of it. This probe measures the effect",
        "once per case, on the f64 setting, with the union.",
        "",
        "| Case | Returned | A before | A after | B before | B after | Operands changed |",
        "|---|---|---|---|---|---|---|",
    ] + probe_operand_mutation() + [
        "",
        "## Probe G — the bound kernel is Epick",
        "",
        "`Point_3::x()` returns a Python `float`, so the bound kernel's number type is",
        "`double`: `Exact_predicates_inexact_constructions_kernel`. If the binding were",
        "built on `Exact_predicates_exact_constructions_kernel` the coordinate would be a",
        "lazy exact number, and a construction such as the boolean's intersection points",
        "would be exact rather than rounded. The volume column of the construction table",
        "shows the consequence directly: `PMP::volume()` of the reference set's **unit",
        "cube** is not 1.",
        "",
        f"- `Point_3(1/3, 0, 0).x()` returns `{repr(Point_3(1.0 / 3.0, 0.0, 0.0).x())}`, a Python `float`.",
        f"- `PMP::volume()` of the reference set's unit cube A (`disjoint` A): "
        f"`{repr(PMP.volume(build({c.name: c for c in torture.cases()}['disjoint'].a, False)))}`.",
        "",
        "## Probe H — do the exact predicates actually decide what plain doubles cannot?",
        "",
        "This is the probe [`../../../docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md`](../../../docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md)",
        "needs, and the one thing in this file that measures the *predicate* rather than",
        "the boolean. A lattice of query points `p_ij = (0.5 + i·u, 0.5 + j·u)` with",
        f"`u = 2⁻⁵³` (one ULP of 0.5), `i, j ∈ [0, {pred['grid']})`, is tested for orientation",
        f"against the fixed, exactly representable pair `q = {pred['q']}`, `r = {pred['r']}`.",
        "",
        "Over the rationals the determinant is exactly `12·u·(j − i)`, so the correct",
        "answer is `sign(j − i)`. What breaks the plain double evaluation is the",
        "*subtraction*: `12 − (0.5 + i·u)` must be rounded, because 11.5 sits in a binade",
        "whose ULP is 2⁻⁴⁹ — sixteen times the lattice spacing — so the rounding error is",
        "the same size as the determinant being computed. Three answers per point:",
        "",
        "1. the sign of the determinant `(qx−px)(ry−py) − (qy−py)(rx−px)` in plain",
        "   `double` — what a boolean without an exact predicate computes;",
        "2. `CGAL_Kernel.orientation(Point_2, Point_2, Point_2)` — Epick's filtered",
        "   predicate;",
        "3. the same determinant over `fractions.Fraction` — exact, and therefore the",
        "   **oracle**. Every input coordinate is a dyadic rational, so `Fraction(float)` is",
        "   lossless and the oracle is not itself an approximation. The oracle was also",
        f"   checked against the closed form `sign(j − i)`: **{pred['closed_form_disagreements']}** disagreements out of",
        f"   {pred['total']}.",
        "",
        f"| Answer | Disagreements with the exact oracle, out of {pred['total']} |",
        "|---|---|",
        f"| plain `double` determinant | **{pred['naive_wrong']}** |",
        f"| `CGAL_Kernel.orientation` (Epick) | **{pred['cgal_wrong']}** |",
        "",
        "Three of the points where the plain determinant disagrees with the oracle:",
        "",
        "| Query point `p` | Exact sign | Plain `double` sign |",
        "|---|---|---|",
    ] + ([
        f"| `({repr(pt[0])}, {repr(pt[1])})` | {t} | {n} |" for (pt, t, n) in pred["examples"]
    ] or ["| — | — | — |"]) + [
        "",
        "The sign mapping used above is not assumed; `CGAL_Kernel.orientation` was called",
        "on three known configurations and its return value recorded:",
        "",
        "| Configuration | `orientation()` returns | Sign of the plain determinant |",
        "|---|---|---|",
    ] + probe_orientation_mapping() + [
        "",
        "**No timing is reported for this probe.** Each `orientation` call crosses the SWIG",
        "boundary and constructs two Python objects, which costs far more than the predicate",
        "does; a ratio measured here would describe the binding, not the filter. The cost of",
        "the filtered predicate itself is a *claimed* number in the note, with a citation.",
        "",
    ]

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(text))
    print(f"wrote {out}")
    print(f"{n_valid}/{n_total} case x setting combinations valid")
    print(f"predicates: naive wrong {pred['naive_wrong']}/{pred['total']}, "
          f"CGAL wrong {pred['cgal_wrong']}/{pred['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
