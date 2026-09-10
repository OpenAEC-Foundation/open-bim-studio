"""Boolean torture set driver for Blender's Boolean modifier.

Run headless from the repository root:

    "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
        --factory-startup --python spikes/boolean-torture/blender_driver.py -- --repeats 5

`--factory-startup` is not optional: without it any add-on installed in the user's
configuration is loaded into the measured process.

Writes `results/blender.md`. Standard library plus `bpy`/`bmesh` only.

Method notes that are part of the measurement
---------------------------------------------
* Operands are built with `Mesh.from_pydata` from `reference/boolean_torture_set.py`
  verbatim: no welding, no triangulation, no scaling.
* **Fresh operand objects are built for every solver, every operation and every
  repeat.** The modifier itself is non-destructive, but the evaluated result is a
  function of the object's state, and reusing objects across settings would also
  reuse whatever a previous `mesh.validate()` did to them.
* The `wall_with_openings` operand B is a *single mesh object holding twelve
  disconnected shells* — the natural reading of the benchmark for a mesh kernel,
  and deliberately different from the OCCT driver, which had to sew it into a
  compound of twelve solids. Whether the modifier accepts it is a finding.
* Timing covers depsgraph evaluation plus the copy of the evaluated mesh
  (`bpy.data.meshes.new_from_object`). The modifier's own self-reported
  `execution_time` is recorded next to it so the copy overhead is visible.
* Volume is computed by this driver's own triangulation of the result
  (`bmesh.ops.triangulate`) fed to `reference.signed_volume` — the same function
  the reference set and the OCCT driver use. Blender is never asked for a volume.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import os
import platform
import re
import statistics
import sys
import tempfile
import time

import bpy
import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(_REPO, "reference"))

import boolean_torture_set as torture  # noqa: E402
from boolean_torture_set import Mesh, signed_volume  # noqa: E402

# Solver enum values of `BooleanModifier.solver` in Blender 5.0, with the label the
# manual uses. Read from the RNA at runtime as well (see `solver_enum_at_runtime`).
SOLVER_LABELS = {
    "FLOAT": "Fast (float)",
    "EXACT": "Exact",
    "MANIFOLD": "Manifold",
}

ZERO_AREA = 1e-14  # m^2; a face below this is reported as degenerate


@contextlib.contextmanager
def captured_stdout():
    """Capture Blender's own C-level log output around a call.

    The modifier reports its failures through `CLOG` on file descriptor 1, which
    Python's `sys.stdout` redirection does not see. Duplicating the descriptor is
    the only way to attribute a warning to the run that produced it — and which
    run produced it is exactly what we need, because the modifier returns the
    unmodified operand when it refuses to execute.
    """
    handle = tempfile.TemporaryFile(mode="w+b")
    sys.stdout.flush()
    saved = os.dup(1)
    os.dup2(handle.fileno(), 1)
    messages = []
    try:
        yield messages
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(saved)
        handle.seek(0)
        text = handle.read().decode("utf-8", errors="replace")
        handle.close()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip CLOG's leading timestamp so repeated runs compare equal.
            messages.append(re.sub(r"^\d\d:\d\d\.\d+\s+", "", line))


# --- scene helpers ---------------------------------------------------------------


def wipe_scene() -> None:
    """Remove every object and mesh datablock, so no measurement inherits state."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def make_object(name: str, mesh: Mesh):
    """Build a fresh mesh object from a reference-set mesh, verbatim."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in mesh.vertices], [], [list(f) for f in mesh.faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def drop_object(ob) -> None:
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)


def mesh_report(me) -> dict:
    """Validity and volume of a mesh datablock, computed here and not by Blender.

    `closed` and `manifold` come from bmesh edge queries on the mesh as produced.
    The volume is computed on a triangulated *copy*, so the reported topology is
    the untriangulated result's.
    """
    bm = bmesh.new()
    bm.from_mesh(me)
    n_verts = len(bm.verts)
    n_faces = len(bm.faces)
    n_edges = len(bm.edges)
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    boundary_edges = sum(1 for e in bm.edges if e.is_boundary)
    wire_edges = sum(1 for e in bm.edges if e.is_wire)
    loose_verts = sum(1 for v in bm.verts if not v.link_edges)
    degenerate_faces = sum(1 for f in bm.faces if f.calc_area() < ZERO_AREA)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    verts = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
    tris = []
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        if len(idx) == 3:
            tris.append(tuple(idx))
    volume = signed_volume(verts, tris) if tris else 0.0
    n_tris = len(tris)
    bm.free()

    return {
        "verts": n_verts,
        "edges": n_edges,
        "faces": n_faces,
        "tris": n_tris,
        "non_manifold_edges": non_manifold_edges,
        "boundary_edges": boundary_edges,
        "wire_edges": wire_edges,
        "loose_verts": loose_verts,
        "degenerate_faces": degenerate_faces,
        "closed": boundary_edges == 0 and wire_edges == 0 and n_faces > 0,
        "manifold": non_manifold_edges == 0 and n_faces > 0,
        "volume": volume,
    }


def shell_count(me) -> int:
    """Number of connected components of a mesh datablock."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.index_update()  # `.index` is only guaranteed after this call
    seen = set()
    shells = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        shells += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)
    bm.free()
    return shells


def boolean_once(case_a: Mesh, case_b: Mesh, solver: str, operation: str,
                 threshold: float | None, self_intersection: bool,
                 hole_tolerant: bool):
    """Build fresh operands, evaluate one boolean, return (ms, modifier_ms, result mesh).

    The caller owns the returned mesh datablock and must remove it.
    """
    ob_a = make_object("A", case_a)
    ob_b = make_object("B", case_b)
    mod = ob_a.modifiers.new("bool", "BOOLEAN")
    mod.object = ob_b
    mod.operation = operation
    mod.solver = solver
    mod.show_viewport = True
    mod.show_render = True
    mod.use_self = self_intersection
    mod.use_hole_tolerant = hole_tolerant
    if threshold is not None:
        mod.double_threshold = threshold
    applied_threshold = mod.double_threshold

    with captured_stdout() as messages:
        start = time.perf_counter()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        ob_eval = ob_a.evaluated_get(depsgraph)
        result = bpy.data.meshes.new_from_object(ob_eval, depsgraph=depsgraph)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        modifier_ms = None
        if ob_eval.modifiers:
            modifier_ms = ob_eval.modifiers[0].execution_time * 1000.0

    drop_object(ob_a)
    drop_object(ob_b)
    return elapsed_ms, modifier_ms, result, applied_threshold, messages


def run_setting(case, solver: str, operation: str, repeats: int,
                threshold: float | None = None, self_intersection: bool = False,
                hole_tolerant: bool = False) -> dict:
    """Time `repeats` fresh booleans; report the last result's topology and volume."""
    times = []
    modifier_times = []
    report = None
    validate_changed = None
    post_validate = None
    applied_threshold = None
    messages = []
    for i in range(repeats):
        ms, mod_ms, result, applied_threshold, run_messages = boolean_once(
            case.a, case.b, solver, operation, threshold, self_intersection, hole_tolerant
        )
        times.append(ms)
        for message in run_messages:
            if message not in messages:
                messages.append(message)
        if mod_ms is not None:
            modifier_times.append(mod_ms)
        if i == repeats - 1:
            report = mesh_report(result)
            # `validate()` returns True when it *changed* something, and it mutates
            # the mesh, so it runs after the report and its effect is reported apart.
            validate_changed = result.validate(verbose=False)
            post_validate = mesh_report(result)
        bpy.data.meshes.remove(result)
    return {
        "solver": solver,
        "operation": operation,
        "threshold": applied_threshold,
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "modifier_median_ms": statistics.median(modifier_times) if modifier_times else None,
        "report": report,
        "validate_changed": validate_changed,
        "post_validate": post_validate,
        "messages": messages,
    }


def operand_report(case) -> dict:
    """Construction facts about the operands, on throwaway builds.

    `mesh.validate()` mutates, so this runs on objects that are discarded
    afterwards and never feed a boolean.
    """
    out = {}
    for key, mesh in (("a", case.a), ("b", case.b)):
        ob = make_object(key.upper(), mesh)
        me = ob.data
        rep = mesh_report(me)
        rep["shells"] = shell_count(me)
        rep["source_verts"] = len(mesh.vertices)
        rep["source_faces"] = len(mesh.faces)
        rep["expected_volume"] = signed_volume(mesh.vertices, mesh.faces)
        rep["validate_changed"] = me.validate(verbose=False)
        after = mesh_report(me)
        rep["verts_after_validate"] = after["verts"]
        rep["faces_after_validate"] = after["faces"]
        rep["volume_after_validate"] = after["volume"]
        out[key] = rep
        drop_object(ob)
    return out


# --- formatting ------------------------------------------------------------------


def g(value, digits: int = 12) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return f"{value:.{digits}g}"
    return str(value)


def validity_cell(rep: dict, validate_changed, expected_volume: float | None = None) -> str:
    """Validity of one result mesh.

    An **empty** result is judged against the analytic expectation: empty is the
    right answer when the expected volume is zero (`disjoint`, `shared_edge`,
    `touching_vertex`, `coplanar_faces` intersections) and a silent failure when
    it is not. Conflating the two is how a missing opening ships unnoticed.
    """
    if rep is None:
        return "-"
    if rep["faces"] == 0:
        if expected_volume is not None and expected_volume == 0.0:
            return "yes (empty, as expected)"
        return "**no** — empty result"
    flags = []
    if not rep["closed"]:
        flags.append(f"{rep['boundary_edges']} boundary edges")
    if rep["non_manifold_edges"]:
        flags.append(f"{rep['non_manifold_edges']} non-manifold edges")
    if rep["wire_edges"]:
        flags.append(f"{rep['wire_edges']} wire edges")
    if rep["loose_verts"]:
        flags.append(f"{rep['loose_verts']} loose verts")
    if rep["degenerate_faces"]:
        flags.append(f"{rep['degenerate_faces']} zero-area faces")
    if validate_changed:
        flags.append("`validate()` corrected")
    if not flags:
        return "yes"
    return "**no** — " + ", ".join(flags)


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default=os.path.join(_HERE, "results", "blender.md"))
    args = parser.parse_args(argv)

    wipe_scene()

    solver_enum = [
        item.identifier
        for item in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items
    ]
    solvers = [s for s in ("EXACT", "FLOAT", "MANIFOLD") if s in solver_enum]

    cases = torture.cases()
    lines = []
    out = lines.append

    out("# Boolean torture set — Blender raw results")
    out("")
    out("Produced by [`../blender_driver.py`](../blender_driver.py). This file is raw data for")
    out("`../FINDINGS.md` (assembled once every candidate has run) and for")
    out("[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)")
    out("§Measurements. Do not edit by hand — re-run the driver.")
    out("")
    out(f"**Run date:** {datetime.date.today().isoformat()}")
    out("")
    out("## Environment")
    out("")
    out("| Item | Value |")
    out("|---|---|")
    out(f"| blender | `{bpy.app.version_string}` |")
    out(f"| build hash | `{bpy.app.build_hash.decode()}` |")
    out(f"| build date | `{bpy.app.build_date.decode()} {bpy.app.build_time.decode()}` |")
    out(f"| bundled python | `{platform.python_version()}` |")
    out(f"| platform | `{platform.system()} {platform.version()} ({platform.machine()})` |")
    out(f"| processor | `{platform.processor()}` |")
    out(f"| solver enum | `{', '.join(solver_enum)}` |")
    out(f"| solvers measured | `{', '.join(solvers)}` |")
    out("| default solver | `%s` |" % bpy.types.BooleanModifier.bl_rna.properties["solver"].default)
    out("| default `double_threshold` | `%s` |"
        % g(bpy.types.BooleanModifier.bl_rna.properties["double_threshold"].default))
    out(f"| repeats per timing | {args.repeats} (median reported) |")
    out("| startup | `--factory-startup` (no add-ons) |")
    out("")
    out("Vertex positions are **float32** in Blender's mesh storage; this driver reads them")
    out("back into f64 Python floats for the volume computation, so every number below carries")
    out("whatever float32 already cost. At unit scale that is ~6e-8 relative; the precision set")
    out("([`../../precision-set/results/blender.md`](../../precision-set/results/blender.md))")
    out("is where it stops being negligible.")
    out("")

    out("## Construction of the operands")
    out("")
    out("`Mesh.from_pydata` from `reference/boolean_torture_set.py` verbatim, no welding and no")
    out("triangulation. *Shells* is the number of connected components — the `wall_with_openings`")
    out("tool is **one mesh object with twelve disconnected shells**, not a compound of twelve")
    out("objects. `validate()` is Blender's own `Mesh.validate()`; it returns True when it")
    out("*changed* the mesh, and it ran on throwaway copies that never fed a boolean.")
    out("")
    out("| Case | Operand | Verts | Faces | Shells | Closed? | Manifold? | Volume | `validate()` changed? |")
    out("|---|---|---|---|---|---|---|---|---|")

    operands = {}
    for case in cases:
        rep = operand_report(case)
        operands[case.name] = rep
        for key in ("a", "b"):
            r = rep[key]
            out("| `%s` | %s | %d | %d | %d | %s | %s | %s | %s |" % (
                case.name, key.upper(), r["verts"], r["faces"], r["shells"],
                "yes" if r["closed"] else "no",
                "yes" if r["manifold"] else "no",
                g(r["volume"]),
                "**yes**" if r["validate_changed"] else "no",
            ))
    out("")
    out("Two operand rows are findings in themselves and are read, not assumed:")
    out("")
    out("* `near_degenerate_triangle` B is **not manifold as a mesh**. The reference set splits")
    out("  the cube's top face by inserting a vertex *on* the edge v5→v6, which leaves that edge")
    out("  bounded by one face on the side quad and by two shorter edges on the top: a T-junction.")
    out("  A B-rep kernel sews it into a valid solid; a mesh kernel sees non-manifold input. Which")
    out("  solvers refuse it is recorded in the table below.")
    out("* `sliver` B has volume %s, not the 1e-7 the reference set specifies."
        % g(next(o for n, o in operands.items() if n == 'sliver')["b"]["volume"]))
    out("  Nothing has run yet: `0.5 + 1e-7` is not representable in float32, and the slab")
    out("  became 19% thicker on its way into the mesh. This is P-05 at **unit** scale.")
    out("")

    out("## Boolean results")
    out("")
    out("One row per case × solver. *Valid?* is this driver's own check on the result mesh:")
    out("closed (no boundary or wire edges), manifold (every edge shared by exactly two faces),")
    out("no loose vertices, no faces below %g m², and `Mesh.validate()` making no correction."
        % ZERO_AREA)
    out("*Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` computed from the **measured** operand")
    out("volumes, so it isolates the boolean from the operands. Times are milliseconds, median of")
    out("%d fresh runs, union / intersection; the parenthesised value is the modifier's own" % args.repeats)
    out("self-reported `execution_time`, which excludes the evaluated-mesh copy.")
    out("")
    out("| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |")
    out("|---|---|---|---|---|---|---|---|")

    summary_rows = []
    for case in cases:
        v_a = operands[case.name]["a"]["volume"]
        v_b = operands[case.name]["b"]["volume"]
        for solver in solvers:
            union = run_setting(case, solver, "UNION", args.repeats)
            inter = run_setting(case, solver, "INTERSECT", args.repeats)
            u_rep, i_rep = union["report"], inter["report"]
            identity = abs((v_a + v_b) - (u_rep["volume"] + i_rep["volume"]))
            expected_u = case.expected_volume_union
            expected_i = case.expected_volume_intersection
            valid_u = validity_cell(u_rep, union["validate_changed"], expected_u)
            valid_i = validity_cell(i_rep, inter["validate_changed"], expected_i)
            ok_u = valid_u.startswith("yes")
            ok_i = valid_i.startswith("yes")
            valid = "yes" if ok_u and ok_i else (
                ("∪: " + valid_u + "; " if not ok_u else "∪ ok; ")
                + ("∩: " + valid_i if not ok_i else "∩ ok"))
            notes = []
            if abs(u_rep["volume"] - expected_u) > 1e-9 * max(1.0, abs(expected_u)):
                notes.append("Δ∪=%s" % g(u_rep["volume"] - expected_u, 3))
            if abs(i_rep["volume"] - expected_i) > 1e-9 * max(1.0, abs(expected_i)):
                notes.append("Δ∩=%s" % g(i_rep["volume"] - expected_i, 3))
            if u_rep["faces"] == 0:
                notes.append("**empty union**")
            if i_rep["faces"] == 0 and expected_i != 0.0:
                notes.append("**empty intersection**")
            if solver == "FLOAT":
                notes.append("threshold=%s" % g(union["threshold"], 3))
            for message in union["messages"] + inter["messages"]:
                short = message.split("| ", 1)[-1]
                if short not in notes:
                    notes.append("`%s`" % short)
            mods = []
            if union["modifier_median_ms"] is not None:
                mods.append(g(union["modifier_median_ms"], 3))
            if inter["modifier_median_ms"] is not None:
                mods.append(g(inter["modifier_median_ms"], 3))
            timing = "%.2f / %.2f" % (union["median_ms"], inter["median_ms"])
            if len(mods) == 2:
                timing += " (%s / %s)" % (mods[0], mods[1])
            correct = (
                abs(u_rep["volume"] - expected_u) <= 1e-6 * max(1.0, abs(expected_u))
                and abs(i_rep["volume"] - expected_i) <= 1e-6 * max(1.0, abs(expected_i)))
            out("| `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
                case.name, SOLVER_LABELS.get(solver, solver), valid,
                g(u_rep["volume"]), g(i_rep["volume"]), g(identity, 3),
                timing, ", ".join(notes) if notes else "-",
            ))
            summary_rows.append((case.name, solver, valid == "yes", identity, correct))
    out("")

    total = len(summary_rows)
    ok = sum(1 for r in summary_rows if r[2])
    out("**Summary:** %d of %d case×solver combinations produced a closed manifold result for"
        % (ok, total))
    out("both the union and the intersection.")
    out("")
    out("*Valid* and *correct* are different questions and are counted separately. A result can")
    out("be a perfectly valid closed manifold mesh of the wrong volume, and — the `shared_edge`")
    out("and `touching_vertex` cases show it — the mathematically correct union of two solids")
    out("meeting at an edge or a point is **not** manifold, so a solver that returns the right")
    out("volume there is marked invalid by the topological check and is not wrong to be.")
    out("*Correct* is both volumes within 1e-6 relative of the analytic expectation.")
    out("")
    per_solver = {}
    for name, solver, valid, identity, correct in summary_rows:
        per_solver.setdefault(solver, []).append((valid, identity, correct))
    out("| Solver | Valid (closed manifold) | Numerically correct | Worst identity residual |")
    out("|---|---|---|---|")
    for solver in solvers:
        rows = per_solver.get(solver, [])
        out("| %s | %d / %d | %d / %d | %s |" % (
            SOLVER_LABELS.get(solver, solver),
            sum(1 for v, _, _ in rows if v), len(rows),
            sum(1 for _, _, c in rows if c), len(rows),
            g(max((i for _, i, _ in rows), default=0.0), 3)))
    out("")
    out("Cases each solver got numerically wrong:")
    out("")
    for solver in solvers:
        wrong = [n for n, s, _, _, c in summary_rows if s == solver and not c]
        out("* **%s** — %s" % (SOLVER_LABELS.get(solver, solver),
                               ", ".join("`%s`" % w for w in wrong) if wrong else "none"))
    out("")

    # --- Probe A: the sliver against the fast solver's overlap threshold ----------
    out("## Probe A — the `sliver` slab against the overlap threshold")
    out("")
    out("`sliver` B is a 1 m × 1 m × 1e-7 m slab: **thinner than the Fast solver's default")
    out("`double_threshold` of 1e-6 m** (the manual's *Overlap Threshold*). This probe varies the")
    out("threshold on the Fast solver only — the Exact and Manifold solvers ignore it — and")
    out("reports what the intersection returns. Expected intersection volume is 1e-7 m³.")
    out("")
    out("| Solver | `double_threshold` | V(intersection) | Faces | Valid? | ms |")
    out("|---|---|---|---|---|---|")
    sliver = next(c for c in cases if c.name == "sliver")
    for solver, thresholds in (("FLOAT", [1e-6, 1e-7, 1e-8, 0.0]),
                               ("EXACT", [None]),
                               ("MANIFOLD", [None])):
        if solver not in solvers:
            continue
        for th in thresholds:
            res = run_setting(sliver, solver, "INTERSECT", args.repeats, threshold=th)
            rep = res["report"]
            out("| %s | %s | %s | %d | %s | %.2f |" % (
                SOLVER_LABELS.get(solver, solver), g(res["threshold"], 3),
                g(rep["volume"]), rep["faces"],
                validity_cell(rep, res["validate_changed"],
                              sliver.expected_volume_intersection),
                res["median_ms"]))
    out("")

    # --- Probe B: the multi-shell tool -------------------------------------------
    out("## Probe B — the twelve-shell cutting tool")
    out("")
    out("`wall_with_openings` B is one mesh object holding twelve disconnected closed shells.")
    out("This probe records what each solver does with it, including the `DIFFERENCE` operation")
    out("the case actually models (a wall with twelve openings cut out), which the torture set's")
    out("union/intersection identity does not exercise.")
    out("")
    out("| Solver | Operation | V(result) | Verts | Faces | Shells | Valid? | ms | Blender's own message |")
    out("|---|---|---|---|---|---|---|---|---|")
    wall = next(c for c in cases if c.name == "wall_with_openings")
    expected_by_op = {
        "UNION": wall.expected_volume_union,
        "INTERSECT": wall.expected_volume_intersection,
        "DIFFERENCE": 9.0 - wall.expected_volume_intersection,
    }
    for solver in solvers:
        for operation in ("UNION", "INTERSECT", "DIFFERENCE"):
            ms, mod_ms, result, _, messages = boolean_once(
                wall.a, wall.b, solver, operation, None, False, False)
            rep = mesh_report(result)
            shells = shell_count(result)
            changed = result.validate(verbose=False)
            bpy.data.meshes.remove(result)
            out("| %s | %s | %s | %d | %d | %d | %s | %.2f | %s |" % (
                SOLVER_LABELS.get(solver, solver), operation, g(rep["volume"]),
                rep["verts"], rep["faces"], shells,
                validity_cell(rep, changed, expected_by_op[operation]), ms,
                ("`%s`" % messages[0].split("| ", 1)[-1]) if messages else "-"))
    out("")
    out("The analytic expectation for `DIFFERENCE` is V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.")
    out("")

    # --- Probe C: self-intersection and hole-tolerant options ---------------------
    out("## Probe C — the Exact solver's `use_self` and `use_hole_tolerant` options")
    out("")
    out("Both default to off. This probe re-runs two cases with each enabled, to record what")
    out("they cost when the input does not need them — the cost a caller pays for turning on a")
    out("robustness option defensively.")
    out("")
    out("| Case | Options | V(union) | Valid? | ms |")
    out("|---|---|---|---|---|")
    if "EXACT" in solvers:
        for case_name in ("wall_with_openings", "near_degenerate_triangle"):
            case = next(c for c in cases if c.name == case_name)
            for label, use_self, hole in (("none", False, False),
                                          ("`use_self`", True, False),
                                          ("`use_hole_tolerant`", False, True),
                                          ("both", True, True)):
                res = run_setting(case, "EXACT", "UNION", args.repeats,
                                  self_intersection=use_self, hole_tolerant=hole)
                out("| `%s` | %s | %s | %s | %.2f |" % (
                    case_name, label, g(res["report"]["volume"]),
                    validity_cell(res["report"], res["validate_changed"],
                                  case.expected_volume_union),
                    res["median_ms"]))
    out("")

    # --- Probe D: the touching_vertex degeneracy ---------------------------------
    out("## Probe D — `touching_vertex`, where the Exact solver loses an operand")
    out("")
    out("Two unit cubes meeting at exactly one point. The Exact solver's union returns a")
    out("**closed, manifold, single-shell mesh of volume 1**: one of the two cubes, with the")
    out("other silently gone. This probe pins that down — both operand orders, and the same")
    out("pair perturbed by ±1 mm so the contact is no longer exact. The perturbed rows are a")
    out("deliberate modification of the case and are reported apart from the torture set")
    out("proper; the unperturbed rows are the case verbatim.")
    out("")
    out("| Input | Solver | Verts | Faces | Shells | V(union) | Valid? |")
    out("|---|---|---|---|---|---|---|")
    touching = next(c for c in cases if c.name == "touching_vertex")
    shifted = {
        "B moved +1 mm away (no contact)": Mesh(
            vertices=[(x + 1e-3, y + 1e-3, z + 1e-3) for (x, y, z) in touching.b.vertices],
            faces=list(touching.b.faces)),
        "B moved −1 mm in (real overlap)": Mesh(
            vertices=[(x - 1e-3, y - 1e-3, z - 1e-3) for (x, y, z) in touching.b.vertices],
            faces=list(touching.b.faces)),
    }
    shared = next(c for c in cases if c.name == "shared_edge")
    variants = [("A ∪ B (the case)", touching.a, touching.b),
                ("B ∪ A (operands swapped)", touching.b, touching.a)]
    variants += [(label, touching.a, mesh) for label, mesh in shifted.items()]
    variants += [("`shared_edge` A ∪ B (for comparison)", shared.a, shared.b)]
    for label, mesh_a, mesh_b in variants:
        for solver in solvers:
            ms, mod_ms, result, _, messages = boolean_once(
                mesh_a, mesh_b, solver, "UNION", None, False, False)
            rep = mesh_report(result)
            shells = shell_count(result)
            changed = result.validate(verbose=False)
            bpy.data.meshes.remove(result)
            out("| %s | %s | %d | %d | %d | %s | %s |" % (
                label, SOLVER_LABELS.get(solver, solver), rep["verts"], rep["faces"],
                shells, g(rep["volume"]),
                validity_cell(rep, changed, touching.expected_volume_union)))
    out("")
    out("The expected union volume is 2 in the first four rows and 2 in the `shared_edge` row.")
    out("Nothing is reported by the modifier in the rows that return 1: no warning, no error,")
    out("and a result the validity check likes.")
    out("")

    # --- Probe E: run-to-run determinism -----------------------------------------
    out("## Probe E — run-to-run determinism")
    out("")
    out("The same operands, rebuilt from the reference set and run %d times in one process."
        % (args.repeats * 2))
    out("*Signatures* is the number of distinct `(verts, faces, volume)` triples observed. A")
    out("deterministic solver produces exactly one. This is asked because Blender's own tracker")
    out("carries a confirmed threading non-determinism in one of these solvers")
    out("([#143644](https://projects.blender.org/blender/blender/issues/143644)), and because a")
    out("kernel whose output depends on thread scheduling cannot be diffed, cached or")
    out("regression-tested.")
    out("")
    out("| Case | Solver | Op | Runs | Signatures | Distinct results |")
    out("|---|---|---|---|---|---|")
    determinism_cases = [("overlap_half", "UNION"), ("wall_with_openings", "UNION"),
                         ("wall_with_openings", "DIFFERENCE"), ("sliver", "INTERSECT")]
    runs = args.repeats * 2
    for case_name, operation in determinism_cases:
        case = next(c for c in cases if c.name == case_name)
        for solver in solvers:
            seen = {}
            for _ in range(runs):
                ms, mod_ms, result, _, messages = boolean_once(
                    case.a, case.b, solver, operation, None, False, False)
                rep = mesh_report(result)
                bpy.data.meshes.remove(result)
                key = (rep["verts"], rep["faces"], round(rep["volume"], 12))
                seen[key] = seen.get(key, 0) + 1
            detail = "; ".join("%dv/%df/V=%s ×%d" % (k[0], k[1], g(k[2]), n)
                               for k, n in seen.items())
            signatures = ("**%d**" % len(seen)) if len(seen) > 1 else str(len(seen))
            out("| `%s` | %s | %s | %d | %s | %s |" % (
                case_name, SOLVER_LABELS.get(solver, solver), operation, runs,
                signatures, detail if len(seen) > 1 else "identical every run"))
    out("")

    path = args.out
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s" % path)
    print("%d of %d case x solver combinations valid" % (ok, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
