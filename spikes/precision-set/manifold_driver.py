"""Manifold driver for the precision set.

THROWAWAY SPIKE CODE. Run:

    pip install manifold3d==3.5.3
    python spikes/precision-set/manifold_driver.py --out spikes/precision-set/results/manifold.md

from the repository root.

`numpy` is imported here only because `manifold3d` requires it (see the
boolean-torture driver's module docstring). Everything else is standard library.

The driver builds each case twice — once at the origin, once with `OFFSET`
applied to the input coordinates, which is what a project does when it models in
a national projection — runs union and intersection on both, translates the far
result back by −offset, and reports the worst nearest-neighbour vertex distance
and the volume difference, absolute and relative. Matching is nearest-neighbour
rather than by index, because a kernel is free to emit vertices in any order.

Because `manifold3d` exposes **two** mesh types — `Mesh` (float32 positions,
uint32 indices, the type the C++ `MeshGL` alias and most bindings default to)
and `Mesh64` (float64, uint64) — every measurement is taken on both input paths.
That is the question ADR-0006 asks, put to the library directly.

Operands are rebuilt for every repeat, every setting and both locations.
"""
from __future__ import annotations

import argparse
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import date

import numpy as np

import manifold3d as m3

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "reference"))

import precision_set as pset  # noqa: E402
from precision_set import OFFSET, offset, signed_volume  # noqa: E402

SETTINGS = [("f64", "f64"), ("f32", "f32")]

OPS = [("union", lambda a, b: a + b), ("intersection", lambda a, b: a ^ b)]


def build(vertices, faces, precision):
    if precision == "f64":
        gl = m3.Mesh64(
            np.asarray(vertices, dtype=np.float64),
            np.asarray(faces, dtype=np.uint64),
        )
    else:
        gl = m3.Mesh(
            np.asarray(vertices, dtype=np.float32),
            np.asarray(faces, dtype=np.uint32),
        )
    return m3.Manifold(gl)


def export(man):
    mesh = man.to_mesh64()
    verts = [tuple(float(c) for c in v[:3]) for v in mesh.vert_properties]
    faces = [tuple(int(i) for i in t) for t in mesh.tri_verts]
    return verts, faces


def check_mesh(verts, faces):
    """Validity check, matching the boolean-torture driver's `check_mesh` so a mesh
    is judged "valid" the same way in both results files.
    """
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


def timed(op, va, fa, vb, fb, precision, repeats):
    """Times `repeats` fresh builds of both operands plus the boolean.

    Also checks `status()` on each operand *before* the boolean runs, the way
    `boolean-torture/manifold_driver.py`'s `measure()` does — an operand that is
    itself rejected (e.g. `NotManifold`) must be visible in the result, not
    silently absorbed into an empty-and-therefore-"valid" boolean result.
    """
    times = []
    result = None
    status_a = status_b = "NoError"
    for _ in range(repeats):
        t0 = time.perf_counter()
        a = build(va, fa, precision)
        b = build(vb, fb, precision)
        status_a = str(a.status()).replace("Error.", "")
        status_b = str(b.status()).replace("Error.", "")
        result = op(a, b)
        result.status()
        result.is_empty()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    return statistics.median(times), result, status_a, status_b


def storage_round_trip():
    """What a coordinate costs to store, before any boolean runs.

    A unit box is placed with its minimum corner at (c, c, 0) and read back
    through `Manifold.bounding_box()`, which reports the library's own stored
    extreme. `ULP` is the distance to the next representable float32, computed
    from the IEEE-754 bit pattern.
    """
    rows = []
    for c in (0.0, 1.0, 0.1, 1e-07, 500000.0, 500000.1, 500000.001, 500001.0):
        ulp = float(np.spacing(np.float32(c))) if c != 0 else float(np.spacing(np.float32(0)))
        cells = []
        for precision in ("f32", "f64"):
            verts = [
                (c, c, 0.0), (c + 1, c, 0.0), (c + 1, c + 1, 0.0), (c, c + 1, 0.0),
                (c, c, 1.0), (c + 1, c, 1.0), (c + 1, c + 1, 1.0), (c, c + 1, 1.0),
            ]
            faces = []
            for a, b, d, e in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                               (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
                faces.append((a, b, d))
                faces.append((a, d, e))
            man = build(verts, faces, precision)
            read_back = man.bounding_box()[0]
            cells.append((read_back, abs(read_back - c), man.get_tolerance()))
        rows.append(
            "| `{c}` | {ulp} | {r32} | {e32} | {t32} | {r64} | {e64} | {t64} |".format(
                c=repr(c), ulp=fmt(ulp, 6),
                r32=fmt(cells[0][0], 17), e32=fmt(cells[0][1], 6), t32=fmt(cells[0][2], 6),
                r64=fmt(cells[1][0], 17), e64=fmt(cells[1][1], 6), t64=fmt(cells[1][2], 6),
            )
        )
    return rows


def operand_round_trip():
    rows = []
    for case in pset.cases():
        for precision in ("f32", "f64"):
            worst_near = 0.0
            worst_far = 0.0
            for mesh in (case.a, case.b):
                near = build(mesh.vertices, mesh.faces, precision)
                far_v = offset(mesh.vertices, case.offset)
                far = build(far_v, mesh.faces, precision)
                nv, _ = export(near)
                fv, _ = export(far)
                worst_near = max(worst_near, worst_nearest(nv, list(mesh.vertices)) or 0.0)
                worst_far = max(worst_far, worst_nearest(fv, far_v) or 0.0)
            rows.append(
                "| `{c}` | {p} | {n} | {v} | **{f}** |".format(
                    c=case.name, p=precision,
                    n=len(case.a.vertices) + len(case.b.vertices),
                    v=fmt(worst_near, 6), f=fmt(worst_far, 6),
                )
            )
    return rows


def op_valid(result, result_status, status_a, status_b, expected, problems):
    """The Valid? verdict for one boolean result, in the same shape
    `boolean-torture/manifold_driver.py`'s `valid_cell()` uses: an operand
    rejected before the boolean, a result whose own `status()` is not
    `NoError`, and an empty-but-unexpected result are all **not** valid — an
    empty or errored result is never silently reported as "yes".
    """
    if status_a != "NoError":
        return f"**no** — operand A `{status_a}`"
    if status_b != "NoError":
        return f"**no** — operand B `{status_b}`"
    if result_status != "NoError":
        return f"**no** — result `{result_status}`"
    if result.is_empty():
        if abs(expected) < 1e-9:
            return "yes (empty, as expected)"
        return "**no** — empty result"
    if problems:
        return "**no** — " + ", ".join(problems)
    return "yes"


def near_far_table(repeats):
    rows = []
    worst_overall = 0.0
    for case in pset.cases():
        for label, precision in SETTINGS:
            for op_name, op in OPS:
                ms_near, near, near_sa, near_sb = timed(
                    op, case.a.vertices, case.a.faces, case.b.vertices, case.b.faces,
                    precision, repeats,
                )
                fa = offset(case.a.vertices, case.offset)
                fb = offset(case.b.vertices, case.offset)
                ms_far, far, far_sa, far_sb = timed(
                    op, fa, case.a.faces, fb, case.b.faces, precision, repeats
                )
                near_status = str(near.status()).replace("Error.", "")
                far_status = str(far.status()).replace("Error.", "")

                nv, nf = ([], []) if near.is_empty() else export(near)
                fv, ff = ([], []) if far.is_empty() else export(far)
                dx, dy, dz = case.offset
                fv_back = [(x - dx, y - dy, z - dz) for (x, y, z) in fv]

                # The far volume is measured on the **back-translated** vertices.
                # `reference.signed_volume` sums x0*(y1*z2 - z1*y2) over raw
                # coordinates; at 5e5 m each term is ~1e17 and the sum is ~10, so
                # the integrand itself loses ~1e-4 m^3 to cancellation before the
                # library is involved at all. The Δ probe below measures exactly
                # that artefact so this choice is auditable rather than silent.
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
                near_ok = op_valid(near, near_status, near_sa, near_sb, expected, pn)
                far_ok = op_valid(far, far_status, far_sa, far_sb, expected, pf)
                valid = near_ok if near_ok == far_ok else f"near: {near_ok}; far: {far_ok}"

                rows.append(
                    "| `{c}` | {s} | {o} | {v} | {vn} / {vf} | {dv} ({rel} rel) | **{dev} m** over {nn}/{nfv} v | {mn:.3f} / {mf:.3f} | {tn} / {tf} |".format(
                        c=case.name, s=label, o=op_name, v=valid,
                        vn=fmt(v_near), vf=fmt(v_far),
                        dv=fmt(dv, 6), rel=fmt(rel, 6),
                        dev=fmt(dev, 6), nn=len(nv), nfv=len(fv),
                        mn=ms_near, mf=ms_far,
                        tn=fmt(near.get_tolerance(), 4), tf=fmt(far.get_tolerance(), 4),
                    )
                )
    return rows, worst_overall


def volume_formulation_probe():
    """How much of a 500 km volume error belongs to the *measurement*, not the library.

    Three numbers for the same mesh: `reference.signed_volume` at the origin, the
    same function on the identical mesh with the offset added to every coordinate
    (no boolean, no library — a pure summation artefact), and `Manifold.volume()`
    on the far result, which sums `dot(cross(v1 - v0, v2 - v0), v0) / 6` with Kahan
    compensation and therefore cancels the common offset before multiplying.
    """
    rows = []
    dx, dy, dz = OFFSET
    for case in pset.cases():
        for op_name, op in OPS:
            a = build(case.a.vertices, case.a.faces, "f64")
            b = build(case.b.vertices, case.b.faces, "f64")
            near = op(a, b)
            far = op(
                build(offset(case.a.vertices, case.offset), case.a.faces, "f64"),
                build(offset(case.b.vertices, case.offset), case.b.faces, "f64"),
            )
            if near.is_empty() or far.is_empty():
                continue
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
                    v4=fmt(far.volume()),
                )
            )
    return rows


def transform_probe():
    """The offset carried by `Manifold.translate()` instead of the vertex data."""
    rows = []
    dx, dy, dz = OFFSET
    for case in pset.cases():
        for label, precision in SETTINGS:
            for op_name, op in OPS:
                a = build(case.a.vertices, case.a.faces, precision)
                b = build(case.b.vertices, case.b.faces, precision)
                origin = op(a, b)
                moved = op(a.translate(list(OFFSET)), b.translate(list(OFFSET)))
                ov, of = ([], []) if origin.is_empty() else export(origin)
                mv, mf = ([], []) if moved.is_empty() else export(moved)
                mv_back = [(x - dx, y - dy, z - dz) for (x, y, z) in mv]
                dev = worst_nearest(ov, mv_back)
                problems = check_mesh(mv, mf) if mf else []
                rows.append(
                    "| `{c}` | {s} | {o} | {ok} | {v} | **{dev} m** | {t0} → {t1} |".format(
                        c=case.name, s=label, o=op_name,
                        ok="yes" if not problems else "**no** — " + ", ".join(problems),
                        # back-translated, for the same cancellation reason as above
                        v=fmt(signed_volume(mv_back, mf) if mf else 0.0),
                        dev=fmt(dev, 6),
                        t0=fmt(origin.get_tolerance(), 4), t1=fmt(moved.get_tolerance(), 4),
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
        version = md.version("manifold3d")
    except Exception:
        version = "unknown"
    return [
        "| Item | Value |",
        "|---|---|",
        f"| python | `{platform.python_version()}` |",
        f"| platform | `{platform.system()} {platform.release()} ({platform.machine()})` |",
        f"| cpu | `{cpu}` |",
        "| installed RAM | `32 GB` |",
        f"| manifold3d | `{version}` |",
        "| manifold source tag | `v3.5.3`, commit `0edd9d54876f3135e431575214dd6d8a72866fee` |",
        "| build flags of the wheel | `MANIFOLD_PAR=ON` (TBB), `MANIFOLD_CROSS_SECTION=ON`, `MANIFOLD_PYBIND=ON` (`pyproject.toml` at the tag) |",
        f"| numpy | `{np.__version__}` (required by manifold3d) |",
        f"| repeats per timing | {repeats} (median reported) |",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(_HERE, "results", "manifold.md"))
    args = ap.parse_args()

    rows, worst = near_far_table(args.repeats)

    text = [
        "# Precision set — Manifold raw results",
        "",
        "Produced by [`../manifold_driver.py`](../manifold_driver.py). Raw data for",
        "`../FINDINGS.md` and for",
        "[`../../../docs/research/kernels/manifold.md`](../../../docs/research/kernels/manifold.md)",
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
        "Two input paths are measured throughout: **f32** is `manifold3d.Mesh` (float32",
        "positions, uint32 indices), the type the C++ `MeshGL` alias resolves to and the one",
        "Blender feeds the library; **f64** is `manifold3d.Mesh64` (float64, uint64).",
        "`Manifold::Impl` stores positions as `vec3`, i.e. double, in both cases — what the",
        "f32 path costs is paid on the way in, not in the algorithm. Every result is exported",
        "through `to_mesh64()` so the readback never rounds.",
        "",
        "## Storage — the coordinate round trip, before any boolean",
        "",
        "A unit box with its minimum corner at `(c, c, 0)`, read back through",
        "`Manifold.bounding_box()`. *ULP* is the distance to the next representable float32.",
        "*Tolerance* is `Manifold.get_tolerance()`: Manifold derives it from the bounding box",
        "as `kPrecision * Box::Scale()` with `kPrecision = 1e-12`, and `Box::Scale()` is the",
        "**largest absolute coordinate**, not the diagonal — so the tolerance is a function of",
        "distance from the origin even on the f64 path.",
        "",
        "| Coordinate | float32 ULP | f32 read back | f32 error | f32 tolerance | f64 read back | f64 error | f64 tolerance |",
        "|---|---|---|---|---|---|---|---|",
    ] + storage_round_trip() + [
        "",
        "Operand round trip per case, worst over all vertices of A and B, matched",
        "nearest-neighbour against the coordinates the reference set specifies:",
        "",
        "| Case | Precision | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |",
        "|---|---|---|---|---|",
    ] + operand_round_trip() + [
        "",
        "## Boolean results near vs far",
        "",
        "The offset is applied to the **vertex coordinates**. *Vertex deviation* is the worst",
        "nearest-neighbour distance after translating the far result back by −offset, taken as",
        "the worse of both matching directions. *ΔV* is the far volume minus the near volume,",
        "absolute and relative — the same two forms [`results/occt.md`](occt.md) and",
        "[`results/blender.md`](blender.md) report, so the candidates compare column for column.",
        "*Tolerance* is `get_tolerance()` on the near and the far result.",
        "",
        "**Comparability caveat.** \"Compare column for column\" is about what each *ΔV* column",
        "measures (the far solid's volume, near vs. far), not about a shared formula. This",
        "driver's *V near / far* is `reference.signed_volume` over exported triangles;",
        "`results/blender.md`'s precision driver back-translates before integrating, with the",
        "same function (`blender_driver.py#L341`, the `far_back = [...]` assignment feeding",
        "`signed_volume`). `results/occt.md`'s driver never calls `reference.signed_volume` at",
        "all — every volume there is OCCT's own `BRepGProp.VolumeProperties_s` integrator",
        "(`spikes/boolean-torture/occt_common.py#L70-L72`). So this driver's and Blender's",
        "columns share a measurement method; OCCT's does not. `docs/research/kernels/manifold.md`",
        "§A warning about measuring volume at 500 km states this explicitly.",
        "",
        "**The far volume is computed on the back-translated vertices**, for the reason the",
        "last probe in this file measures: `reference.signed_volume` sums",
        "`x0*(y1*z2 − z1*y2)` over raw coordinates, and at 5e5 m each term is ~1e17 against a",
        "sum of ~10, so the integrand loses ~1e-4 m³ to cancellation *before any library is",
        "involved*. Reporting the raw-coordinate figure here would have charged that to",
        "Manifold.",
        "",
        "| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far | tol near / far |",
        "|---|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        f"**Worst vertex deviation over the whole set: {fmt(worst, 6)} m.** R-17's pass line is 1e-6 m",
        "and its fail line is 1e-4 m.",
        "",
        "## Probe — the same offset carried by `Manifold.translate()`",
        "",
        "Identical geometry built at the origin, then moved 500 km by",
        "`Manifold.translate()` before the boolean, and the result translated back. This is",
        "the local-frame mitigation ADR-0006 proposes, measured on the candidate rather than",
        "assumed. Manifold's transforms are lazy but not symbolic: `Impl::Transform` writes the",
        "moved coordinates into `vertPos_` and then re-derives epsilon from the **new** bounding",
        "box, so the tolerance column is the part to read.",
        "",
        "| Case | Setting | Op | Valid? | V | Deviation vs. the origin run | tol origin → translated |",
        "|---|---|---|---|---|---|---|",
    ] + transform_probe() + [
        "",
        "## Probe — how much of a far-field volume error is the measurement's own",
        "",
        "All five columns describe the **same solid**, on the f64 path. *Near* is",
        "`reference.signed_volume` at the origin. *Near, coords shifted* adds the offset to",
        "every vertex of the near result and re-integrates: no boolean, no library, so the",
        "difference from the first column is pure floating-point cancellation in the",
        "divergence-theorem sum. *Far, raw* is the same function on the far result's own",
        "coordinates; *Far, back-translated* is the number the table above reports; *Far,",
        "`Manifold.volume()`* is the library's own figure, which sums",
        "`dot(cross(v1 − v0, v2 − v0), v0) / 6` with Kahan compensation",
        "([`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294)),",
        "i.e. it subtracts the common offset before multiplying.",
        "",
        "| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `Manifold.volume()` |",
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
