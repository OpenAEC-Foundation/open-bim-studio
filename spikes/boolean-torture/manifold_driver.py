"""Manifold driver for the boolean torture set.

THROWAWAY SPIKE CODE. Run:

    pip install manifold3d==3.5.3
    python spikes/boolean-torture/manifold_driver.py --out spikes/boolean-torture/results/manifold.md

from the repository root.

`numpy` is imported here only because `manifold3d` requires it: the `Mesh` /
`Mesh64` constructors take typed numpy arrays and nothing else, and numpy is a
hard dependency of the `manifold3d` wheel (`pyproject.toml`). Everything else is
standard library.

For every case in `reference/boolean_torture_set.py` the driver builds both
operands as `manifold3d.Manifold` objects under each setting, checks
`Manifold.status()` before the boolean, runs union (`+`) and intersection
(`^`), and then measures the result on the *exported* triangles rather than
trusting the library's own accessors:

  * validity is this driver's own check on the exported mesh - closed, every
    edge shared by exactly two triangles, consistent winding, no loose
    vertices, no triangle below 1e-14 m^2 - plus `status()` and `is_empty()`;
  * volumes are `reference.signed_volume` over the exported triangles, with
    Manifold's own `volume()` recorded beside them so a disagreement between
    the two would be visible;
  * the identity residual |V(A) + V(B) - (V(union) + V(intersection))| is
    computed from the *measured* operand volumes, so it isolates the boolean
    from any error already present in the operands.

Operands are rebuilt from the reference set for every setting and every repeat.
Manifold does not mutate its inputs (its operators are functional), but the
rebuild also re-runs the `Mesh -> Manifold` constructor, which is where the
epsilon, the tolerance and the float32 rounding are decided, and that is part
of what is being measured.
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

import boolean_torture_set as torture  # noqa: E402
from boolean_torture_set import signed_volume  # noqa: E402

# (label, precision, explicit tolerance or None for "leave the default").
# "f64" builds the operands through `manifold3d.Mesh64` (float64 positions,
# uint64 indices); "f32" builds them through `manifold3d.Mesh` (float32
# positions, uint32 indices), which is the only mesh type the C++ `MeshGL`
# alias and most bindings expose by default.
SETTINGS = [
    ("f64, default tolerance", "f64", None),
    ("f64, tolerance=1e-9", "f64", 1e-9),
    ("f64, tolerance=1e-6", "f64", 1e-6),
    ("f32, default tolerance", "f32", None),
]

# Thresholds, identical in shape to the ones `results/blender.md` uses so the two
# candidates are judged the same way: relative for expectations above 1 m^3, with
# an absolute floor below it. DELTA_FLOOR drives the Δ notes in the table,
# CORRECT_TOL drives the "numerically correct" count in the summary.
DELTA_FLOOR = 1e-9
CORRECT_TOL = 1e-6


def build(mesh, precision):
    """Reference `Mesh` -> `manifold3d.Manifold`, at the requested precision."""
    if precision == "f64":
        gl = m3.Mesh64(
            np.asarray(mesh.vertices, dtype=np.float64),
            np.asarray(mesh.faces, dtype=np.uint64),
        )
    else:
        gl = m3.Mesh(
            np.asarray(mesh.vertices, dtype=np.float32),
            np.asarray(mesh.faces, dtype=np.uint32),
        )
    return m3.Manifold(gl)


def operands(case, precision, tolerance):
    a = build(case.a, precision)
    b = build(case.b, precision)
    if tolerance is not None:
        a = a.set_tolerance(tolerance)
        b = b.set_tolerance(tolerance)
    return a, b


def export(man):
    """Exported triangles as (vertices, faces) in the shape `reference` uses.

    Always exported through `to_mesh64()` so the measurement itself never
    rounds: what a float32 setting cost is then a property of the input path,
    not of the readback.
    """
    mesh = man.to_mesh64()
    verts = [tuple(float(c) for c in v[:3]) for v in mesh.vert_properties]
    faces = [tuple(int(i) for i in t) for t in mesh.tri_verts]
    return verts, faces


def check_mesh(verts, faces):
    """This driver's own validity check. Returns a list of complaints."""
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


def measure(case, precision, tolerance, repeats):
    """One case under one setting: both operations, timed and checked."""
    a, b = operands(case, precision, tolerance)
    out = {
        "status_a": str(a.status()).replace("Error.", ""),
        "status_b": str(b.status()).replace("Error.", ""),
        "vol_a": 0.0,
        "vol_b": 0.0,
        "tol_a": a.get_tolerance(),
        "tol_b": b.get_tolerance(),
    }
    if not a.is_empty():
        va, fa = export(a)
        out["vol_a"] = signed_volume(va, fa)
    if not b.is_empty():
        vb, fb = export(b)
        out["vol_b"] = signed_volume(vb, fb)

    for op_name, op in (("union", lambda x, y: x + y), ("intersection", lambda x, y: x ^ y)):
        times = []
        result = None
        for _ in range(repeats):
            fa, fb = operands(case, precision, tolerance)
            t0 = time.perf_counter()
            result = op(fa, fb)
            # `+` and `^` build a deferred CSG node; `status()` forces
            # evaluation, so the timing has to include it or it times nothing.
            status = result.status()
            empty = result.is_empty()
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)
        verts, faces = ([], []) if empty else export(result)
        out[op_name] = {
            "ms": statistics.median(times),
            "status": str(status).replace("Error.", ""),
            "empty": empty,
            "verts": len(verts),
            "tris": len(faces),
            "volume": signed_volume(verts, faces) if faces else 0.0,
            "own_volume": result.volume(),
            "problems": check_mesh(verts, faces) if faces else [],
        }
    return out


def fmt(x, digits=12):
    if x == 0:
        return "0"
    return f"{x:.{digits}g}"


def delta_note(measured, expected):
    d = measured - expected
    if abs(d) > max(DELTA_FLOOR, DELTA_FLOOR * abs(expected)):
        return f"{d:.3g}"
    return None


def valid_cell(entry, expected_volume):
    """The Valid? cell, in the same shape `results/blender.md` uses."""
    if entry["status"] != "NoError":
        return f"**no** — status `{entry['status']}`"
    if entry["empty"]:
        if abs(expected_volume) <= DELTA_FLOOR:
            return "yes (empty, as expected)"
        return "**no** — empty result"
    if entry["problems"]:
        return "**no** — " + ", ".join(entry["problems"])
    return "yes"


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


def construction_table():
    rows = []
    for case in torture.cases():
        for name, mesh in (("A", case.a), ("B", case.b)):
            for precision in ("f64", "f32"):
                man = build(mesh, precision)
                status = str(man.status()).replace("Error.", "")
                if man.is_empty():
                    rows.append(
                        f"| `{case.name}` | {name} | {precision} | **{status}** | - | - | - | - | - |"
                    )
                    continue
                verts, faces = export(man)
                rows.append(
                    "| `{c}` | {n} | {p} | {s} | {nv} | {nt} | {comp} | {vol} | {tol} |".format(
                        c=case.name, n=name, p=precision, s=status,
                        nv=len(verts), nt=len(faces),
                        comp=len(man.decompose()),
                        vol=fmt(signed_volume(verts, faces)),
                        tol=fmt(man.get_tolerance(), 4),
                    )
                )
    return rows


def probe_multi_shell():
    """Does Manifold take one mesh of twelve disconnected shells as one Manifold?"""
    case = {c.name: c for c in torture.cases()}["wall_with_openings"]
    rows = []
    for precision in ("f64", "f32"):
        a = build(case.a, precision)
        b = build(case.b, precision)
        for op_name, op in (
            ("union", lambda x, y: x + y),
            ("intersection", lambda x, y: x ^ y),
            ("difference", lambda x, y: x - y),
        ):
            r = op(a, b)
            verts, faces = ([], []) if r.is_empty() else export(r)
            problems = check_mesh(verts, faces) if faces else []
            rows.append(
                "| {p} | {o} | {comp_b} | {vol} | {nv} | {nt} | {comp} | {ok} |".format(
                    p=precision, o=op_name, comp_b=len(b.decompose()),
                    vol=fmt(signed_volume(verts, faces) if faces else 0.0),
                    nv=len(verts), nt=len(faces),
                    comp=len(r.decompose()) if faces else 0,
                    ok="yes" if not problems else "**no** — " + ", ".join(problems),
                )
            )
    return rows


def probe_sliver_tolerance():
    """What tolerance makes the 1e-7 m slab stop being a solid?"""
    case = {c.name: c for c in torture.cases()}["sliver"]
    rows = []
    for precision in ("f64", "f32"):
        for tol in (None, 1e-9, 1e-8, 1e-7, 1e-6, 1e-4):
            a, b = operands(case, precision, tol)
            if b.is_empty():
                rows.append(
                    "| {p} | {t} | - | **empty**, status `{s}` | - | - |".format(
                        p=precision, t="default" if tol is None else f"{tol:g}",
                        s=str(b.status()).replace("Error.", ""),
                    )
                )
                continue
            vb, fb = export(b)
            r = a ^ b
            verts, faces = ([], []) if r.is_empty() else export(r)
            rows.append(
                "| {p} | {t} | {tb} | {vb} | {vi} | {nt} |".format(
                    p=precision, t="default" if tol is None else f"{tol:g}",
                    tb=fmt(b.get_tolerance(), 4),
                    vb=fmt(signed_volume(vb, fb)),
                    vi=fmt(signed_volume(verts, faces)) if faces else "**empty**",
                    nt=len(faces),
                )
            )
    return rows


def probe_t_junction():
    """The T-junction operand: what the standalone library does with it."""
    case = {c.name: c for c in torture.cases()}["near_degenerate_triangle"]
    rows = []
    for precision in ("f64", "f32"):
        b = build(case.b, precision)
        rows.append(
            "| {p} | operand B alone | `{s}` | {e} | {nt} |".format(
                p=precision, s=str(b.status()).replace("Error.", ""),
                e=b.is_empty(), nt=b.num_tri(),
            )
        )
        a = build(case.a, precision)
        for op_name, op in (("A + B", lambda x, y: x + y), ("A ^ B", lambda x, y: x ^ y)):
            r = op(a, b)
            rows.append(
                "| {p} | {o} | `{s}` | {e} | {nt} |".format(
                    p=precision, o=op_name,
                    s=str(r.status()).replace("Error.", ""),
                    e=r.is_empty(), nt=r.num_tri(),
                )
            )
    # Does the merge helper the README points at repair it?
    gl = m3.Mesh64(
        np.asarray(case.b.vertices, dtype=np.float64),
        np.asarray(case.b.faces, dtype=np.uint64),
    )
    changed = gl.merge()
    merged = m3.Manifold(gl)
    rows.append(
        "| f64 | operand B after `Mesh64.merge()` | `{s}` | {e} | {nt} |".format(
            s=str(merged.status()).replace("Error.", ""),
            e=merged.is_empty(), nt=merged.num_tri(),
        )
    )
    return rows, changed


def probe_determinism(runs):
    """Same input, N runs, how many distinct results?"""
    by_name = {c.name: c for c in torture.cases()}
    rows = []
    for case_name, op_name, op in (
        ("overlap_half", "union", lambda x, y: x + y),
        ("wall_with_openings", "union", lambda x, y: x + y),
        ("wall_with_openings", "difference", lambda x, y: x - y),
        ("sliver", "intersection", lambda x, y: x ^ y),
    ):
        case = by_name[case_name]
        signatures = {}
        for _ in range(runs):
            a, b = operands(case, "f64", None)
            r = op(a, b)
            verts, faces = export(r)
            key = (len(verts), len(faces), repr(signed_volume(verts, faces)))
            signatures[key] = signatures.get(key, 0) + 1
        detail = "; ".join(
            f"{k[0]}v/{k[1]}f/V={float(k[2]):.12g} x{n}" for k, n in signatures.items()
        )
        rows.append(
            f"| `{case_name}` | {op_name} | {runs} | {len(signatures)} | {detail} |"
        )
    return rows


def probe_cancellation():
    """Is a long operation cancellable, and is the cancellation distinguishable?"""
    case = {c.name: c for c in torture.cases()}["wall_with_openings"]
    a, b = operands(case, "f64", None)
    rows = []

    ctx = m3.ExecutionContext()
    before = ctx.progress()
    result = (a + b).with_context(ctx)
    rows.append(
        "| union, context attached, not cancelled | `{s}` | {e} | {nt} | {p0} → {p1} |".format(
            s=str(result.status()).replace("Error.", ""), e=result.is_empty(),
            nt=result.num_tri(), p0=fmt(before, 3), p1=fmt(ctx.progress(), 3),
        )
    )

    ctx2 = m3.ExecutionContext()
    ctx2.cancel()
    before2 = ctx2.progress()
    result2 = (a + b).with_context(ctx2)
    rows.append(
        "| union, context cancelled before evaluation | `{s}` | {e} | {nt} | {p0} → {p1} |".format(
            s=str(result2.status()).replace("Error.", ""), e=result2.is_empty(),
            nt=result2.num_tri(), p0=fmt(before2, 3), p1=fmt(ctx2.progress(), 3),
        )
    )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--determinism-runs", type=int, default=10)
    ap.add_argument(
        "--out",
        default=os.path.join(_HERE, "results", "manifold.md"),
    )
    args = ap.parse_args()

    rows = []
    n_valid = 0
    n_total = 0
    per_setting = {label: {"valid": 0, "correct": 0, "worst": 0.0} for label, _, _ in SETTINGS}
    for case in torture.cases():
        for label, precision, tolerance in SETTINGS:
            r = measure(case, precision, tolerance, args.repeats)
            u, i = r["union"], r["intersection"]
            identity = abs((r["vol_a"] + r["vol_b"]) - (u["volume"] + i["volume"]))
            # The identity is only a statement about a boolean that ran. A refused
            # operand makes it |V(A)| by construction, which says nothing about the
            # algorithm, so those rows are excluded from the worst-residual column.
            if u["status"] == "NoError" and i["status"] == "NoError":
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
            du = delta_note(u["volume"], case.expected_volume_union)
            di = delta_note(i["volume"], case.expected_volume_intersection)
            if du:
                notes.append(f"Δ∪={du}")
            if di:
                notes.append(f"Δ∩={di}")
            if r["status_a"] != "NoError":
                notes.append(f"operand A rejected: `{r['status_a']}`")
            if r["status_b"] != "NoError":
                notes.append(f"operand B rejected: `{r['status_b']}`")
            notes.append(f"tol(A)={fmt(r['tol_a'], 4)}, tol(B)={fmt(r['tol_b'], 4)}")
            if abs(u["own_volume"] - u["volume"]) > 1e-12 * max(1.0, abs(u["volume"])):
                notes.append(f"Manifold.volume()∪={fmt(u['own_volume'])}")
            if abs(i["own_volume"] - i["volume"]) > 1e-12 * max(1.0, abs(i["volume"])):
                notes.append(f"Manifold.volume()∩={fmt(i['own_volume'])}")

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

    t_rows, merge_changed = probe_t_junction()

    text = [
        "# Boolean torture set — Manifold raw results",
        "",
        "Produced by [`../manifold_driver.py`](../manifold_driver.py). This file is raw data for",
        "`../FINDINGS.md` (assembled once every candidate has run) and for",
        "[`../../../docs/research/kernels/manifold.md`](../../../docs/research/kernels/manifold.md)",
        "§Measurements. Do not edit by hand — re-run the driver.",
        "",
        f"**Run date:** {date.today().isoformat()}",
        "",
        "## Environment",
        "",
    ] + environment(args.repeats) + [
        "",
        "The standalone library measured here is **v3.5.3**. Blender 5.0, whose Manifold",
        "solver rows are in [`results/blender.md`](blender.md), bundles **v3.2.1**",
        "(`MANIFOLD_VERSION v3.2.1` in Blender's `build_files/build_environment/cmake/versions.cmake`",
        "at the build's own commit), and feeds it float32 vertex positions. Both differences are",
        "held constant here by measuring the f32 and the f64 input path separately.",
        "",
        "## Construction of the operands",
        "",
        "`manifold3d.Mesh` (float32 positions, uint32 indices) and `manifold3d.Mesh64`",
        "(float64, uint64) into `Manifold(...)`, from `reference/boolean_torture_set.py`",
        "verbatim: no welding, no merge vectors, no repair. *Components* is",
        "`Manifold.decompose()`, i.e. how many disconnected solids the one input mesh",
        "became. *Volume* is `reference.signed_volume` over the triangles exported by",
        "`to_mesh64()`. *Tolerance* is `Manifold.get_tolerance()` after construction.",
        "",
        "| Case | Operand | Precision | Status | Verts | Tris | Components | Volume | Tolerance |",
        "|---|---|---|---|---|---|---|---|---|",
    ] + construction_table() + [
        "",
        "## Boolean results",
        "",
        "One row per case × setting. *Valid?* is this driver's own check on the exported",
        "result mesh — every directed edge used once with a matching opposite halfedge",
        "(closed, manifold and consistently wound), no loose vertices, no triangle below",
        "1e-14 m² — plus `Manifold.status()` and `is_empty()`. *Identity* is",
        "`|V(A) + V(B) − (V(∪) + V(∩))|` computed from the **measured** operand volumes.",
        "Times are milliseconds, median of the repeats, union / intersection; each repeat",
        "rebuilds both operands and the timing includes the `status()` call that forces",
        "the deferred CSG node to evaluate.",
        "",
        "| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |",
        "|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        f"**Summary:** {n_valid} of {n_total} case×setting combinations produced a result this",
        "driver's check accepts for both the union and the intersection.",
        "",
        "*Valid* and *correct* are different questions and are counted separately, on the",
        "same definitions [`results/blender.md`](blender.md) uses. *Correct* is both volumes",
        f"within `{CORRECT_TOL:g} * max(1.0, abs(expected))` of the analytic expectation — relative above",
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
        for label, _, _ in SETTINGS
    ] + [
        "",
        "The `tol(B)` values on the refused rows are not driver artefacts. `0` is the",
        "`tolerance` field of the input `Mesh` (the binding's default), kept by the",
        "`Mesh -> Impl` constructor before it reaches `MakeEmpty(NotManifold)`; `-1` is the",
        "uninitialised `Impl::tolerance_`, which is what `SetTolerance` on an already-errored",
        "Manifold returns via `PropagateStatus`",
        "([`manifold.cpp#L367-L383`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/manifold.cpp#L367-L383),",
        "[`impl.h#L57-L58`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/impl.h#L57-L58)).",
        "",
        "## Probe A — the twelve-shell operand",
        "",
        "`wall_with_openings` B is **one mesh with twelve disconnected closed shells**, the",
        "same construction `results/blender.md` used. This probe records whether Manifold",
        "accepts it as a single `Manifold` and what `decompose()` then reports, including",
        "the `DIFFERENCE` operation the case actually models. The analytic expectation for",
        "the difference is V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.",
        "",
        "| Precision | Operation | Components in B | V(result) | Verts | Tris | Components in result | Valid? |",
        "|---|---|---|---|---|---|---|---|",
    ] + probe_multi_shell() + [
        "",
        "## Probe B — the 1e-7 m slab against the tolerance",
        "",
        "`sliver` B is a 1 m × 1 m × 1e-7 m slab. Manifold's default epsilon is",
        "`kPrecision * bBox.Scale()` with `kPrecision = 1e-12`, and `Box::Scale()` is the",
        "largest absolute coordinate, not the diagonal. `set_tolerance` above that value",
        "runs simplification. This probe raises the tolerance past the slab's thickness on",
        "both input paths and reports what survives.",
        "",
        "| Precision | Requested tolerance | tol(B) after | V(B) | V(A∩B) | Tris in A∩B |",
        "|---|---|---|---|---|---|",
    ] + probe_sliver_tolerance() + [
        "",
        "## Probe C — the T-junction operand",
        "",
        "`near_degenerate_triangle` B has a vertex lying *on* an edge (the reference set",
        "splits the cube's top face by inserting a vertex on the edge v5→v6), so one",
        "halfedge has no twin: a T-junction, and not a manifold mesh. Blender's Manifold",
        "solver refuses it and returns the unmodified first operand",
        "([`results/blender.md`](blender.md)). This probe records what the standalone",
        "library does, and whether the `Merge` helper the README offers for \"slightly",
        "non-manifold meshes\" repairs it.",
        "",
        "| Precision | Input | `status()` | `is_empty()` | Tris |",
        "|---|---|---|---|---|",
    ] + t_rows + [
        "",
        f"`Mesh64.merge()` reported that it changed the mesh: **{merge_changed}**.",
        "",
        "## Probe D — run-to-run determinism",
        "",
        "The same operands, rebuilt from the reference set and run N times in one process,",
        "on the f64 path at default tolerance. *Signatures* is the number of distinct",
        "`(verts, tris, volume)` triples observed; a deterministic library produces exactly",
        "one. This is asked because Blender's tracker carries a non-determinism that was",
        "reproduced in this library and fixed upstream",
        "([#143644](https://projects.blender.org/blender/blender/issues/143644)), and",
        "because a kernel whose output depends on thread scheduling cannot be diffed,",
        "cached or regression-tested. The wheel is built with `MANIFOLD_PAR=ON`, so TBB is",
        "in the process.",
        "",
        "| Case | Op | Runs | Signatures | Distinct results |",
        "|---|---|---|---|---|",
    ] + probe_determinism(args.determinism_runs) + [
        "",
        "## Probe E — cancellation and progress",
        "",
        "`ExecutionContext` (`Cancel`, `Cancelled`, `Progress`,",
        "[`common.h#L250-L299`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/common.h#L250-L299))",
        "is the API `problems.md` P-15 asks every candidate for: a way to bound a runaway",
        "operation from outside it. Booleans are deferred, so the context is attached to the",
        "tree and consumed by `Status()`. This probe runs the twelve-opening wall's union with",
        "a context attached, and again with the context cancelled beforehand. `Progress()`",
        "returns 1.0 when no work has been scheduled, which is why the uncancelled row starts",
        "at 1.0 — that is documented behaviour, not a reading error.",
        "",
        "| Run | `status()` | `is_empty()` | Tris | `progress()` before → after |",
        "|---|---|---|---|---|",
    ] + probe_cancellation() + [
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
