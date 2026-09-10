"""Precision set driver for Blender's Boolean modifier.

Run headless from the repository root:

    "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
        --factory-startup --python spikes/precision-set/blender_driver.py -- --repeats 5

Writes `results/blender.md`. Standard library plus `bpy`/`bmesh` only.

The question (R-17) is whether the same geometry gives the same answer at the origin
and 500 km from it. For Blender the answer is decided before any boolean runs, by the
mesh format: `Mesh` vertex positions are a **float32** attribute. This driver therefore
reports three things, in increasing order of interest:

1. the float32 round trip of the operand coordinates themselves (storage cost alone);
2. the boolean result near vs. far, matched nearest-neighbour after translating back;
3. the same far case with the 500 km carried by the **object transform** instead of the
   vertex data — the mitigation ADR-0006 proposes (a local frame), measured rather than
   assumed.

Operands are rebuilt for every repeat and for every solver; nothing is reused.
"""
from __future__ import annotations

import argparse
import datetime
import math
import os
import platform
import statistics
import struct
import sys
import time

import bpy
import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(_REPO, "reference"))

import precision_set  # noqa: E402
from precision_set import OFFSET, offset, signed_volume  # noqa: E402

SOLVER_LABELS = {"FLOAT": "Fast (float)", "EXACT": "Exact", "MANIFOLD": "Manifold"}


def wipe_scene() -> None:
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def make_object(name: str, vertices, faces, location=(0.0, 0.0, 0.0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vertices], [], [list(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    bpy.context.collection.objects.link(ob)
    return ob


def drop_object(ob) -> None:
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)


def read_back(vertices):
    """Store a vertex list in a mesh and read it back: the float32 round trip."""
    me = bpy.data.meshes.new("probe")
    me.from_pydata([tuple(v) for v in vertices], [], [])
    me.update()
    out = [(v.co.x, v.co.y, v.co.z) for v in me.vertices]
    bpy.data.meshes.remove(me)
    return out


def result_geometry(me):
    """Triangulated vertices/faces plus topology facts of a result mesh."""
    bm = bmesh.new()
    bm.from_mesh(me)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    n_faces_untri = len(bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    verts = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
    tris = [tuple(v.index for v in f.verts) for f in bm.faces if len(f.verts) == 3]
    bm.free()
    return {
        "verts": verts,
        "tris": tris,
        "volume": signed_volume(verts, tris) if tris else 0.0,
        "boundary_edges": boundary,
        "non_manifold_edges": non_manifold,
        "faces": n_faces_untri,
        "valid": boundary == 0 and non_manifold == 0 and n_faces_untri > 0,
    }


def run_boolean(a_verts, a_faces, b_verts, b_faces, solver, operation,
                location=(0.0, 0.0, 0.0)):
    ob_a = make_object("A", a_verts, a_faces, location)
    ob_b = make_object("B", b_verts, b_faces, location)
    mod = ob_a.modifiers.new("bool", "BOOLEAN")
    mod.object = ob_b
    mod.operation = operation
    mod.solver = solver
    mod.show_viewport = True
    start = time.perf_counter()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob_a.evaluated_get(depsgraph)
    result = bpy.data.meshes.new_from_object(ob_eval, depsgraph=depsgraph)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    geometry = result_geometry(result)
    bpy.data.meshes.remove(result)
    drop_object(ob_a)
    drop_object(ob_b)
    geometry["ms"] = elapsed_ms
    return geometry


def max_nearest_deviation(near_verts, far_verts):
    """Worst nearest-neighbour distance from each far vertex to the near set.

    Nearest-neighbour rather than by index, because a kernel may emit vertices in
    any order. Reported symmetrically (worst of both directions) so a far result
    that dropped a vertex cannot hide behind the matching.
    """
    if not near_verts or not far_verts:
        return None

    def worst(source, target):
        worst_d = 0.0
        for x0, y0, z0 in source:
            best = math.inf
            for x1, y1, z1 in target:
                d = (x0 - x1) ** 2 + (y0 - y1) ** 2 + (z0 - z1) ** 2
                if d < best:
                    best = d
            worst_d = max(worst_d, math.sqrt(best))
        return worst_d

    return max(worst(far_verts, near_verts), worst(near_verts, far_verts))


def valid_word(geometry: dict, expected_volume: float | None) -> str:
    """Validity of one result, with an empty result judged against the expectation.

    An empty intersection is the correct answer for `coplanar_faces` (the operands
    meet in a plane, not in a volume), so it is reported as such rather than as a
    failure — the same rule the torture-set driver uses.
    """
    if geometry["faces"] == 0:
        if expected_volume is not None and expected_volume == 0.0:
            return "yes (empty, as expected)"
        return "**no** (empty)"
    return "yes" if geometry["valid"] else "**no**"


def g(value, digits: int = 12) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return f"{value:.{digits}g}"
    return str(value)


def float32_step(value: float) -> float:
    """Distance to the next representable float32 above `value` (the ULP)."""
    as32 = struct.unpack("<f", struct.pack("<f", value))[0]
    bits = struct.unpack("<I", struct.pack("<f", as32))[0]
    nxt = struct.unpack("<f", struct.pack("<I", bits + 1))[0]
    return nxt - as32


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
    cases = precision_set.cases()

    lines = []
    out = lines.append
    out("# Precision set — Blender raw results")
    out("")
    out("Produced by [`../blender_driver.py`](../blender_driver.py). Raw data for")
    out("`../FINDINGS.md` and for")
    out("[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)")
    out("§Measurements. Do not edit by hand — re-run the driver.")
    out("")
    out(f"**Run date:** {datetime.date.today().isoformat()}")
    out("**Offset:** `%s` (500 km east, 500 km north — a plausible distance from a national"
        % (OFFSET,))
    out("projection's false origin to a project site).")
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
    out(f"| solvers measured | `{', '.join(solvers)}` |")
    out(f"| repeats per timing | {args.repeats} (median reported) |")
    out("| startup | `--factory-startup` (no add-ons) |")
    out("")

    # --- Probe 0: what float32 storage costs before any boolean runs -------------
    out("## Storage — the float32 round trip, before any boolean")
    out("")
    out("A `Mesh` stores vertex positions as float32. This probe writes a coordinate into a")
    out("mesh and reads it back; nothing else happens to it. *ULP* is the distance to the next")
    out("representable float32, computed in Python from the IEEE-754 bit pattern.")
    out("")
    out("| Coordinate | float32 ULP | Written | Read back | Round-trip error |")
    out("|---|---|---|---|---|")
    probes = [0.0, 1.0, 0.1, 1e-7, 500000.0, 500000.1, 500000.0 + 1e-3, 500001.0]
    read = read_back([(p, 0.0, 0.0) for p in probes])
    for p, (x, _, _) in zip(probes, read):
        out("| `%s` | %s | %s | %s | %s |"
            % (g(p), g(float32_step(p), 6), g(p, 17), g(x, 17), g(abs(x - p), 6)))
    out("")
    out("The 500 km rows are the finding: a float32 near 5e5 has an ULP of %s m, so **no**"
        % g(float32_step(500000.0), 6))
    out("coordinate detail below ~3 cm survives being stored at that distance from the origin,")
    out("regardless of what any algorithm does afterwards.")
    out("")
    out("Operand round trip per case, worst over all vertices of A and B:")
    out("")
    out("| Case | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |")
    out("|---|---|---|---|")
    for case in cases:
        near_src = list(case.a.vertices) + list(case.b.vertices)
        far_src = offset(case.a.vertices, case.offset) + offset(case.b.vertices, case.offset)
        near_rt = max(max(abs(a - b) for a, b in zip(s, r))
                      for s, r in zip(near_src, read_back(near_src)))
        far_rt = max(max(abs(a - b) for a, b in zip(s, r))
                     for s, r in zip(far_src, read_back(far_src)))
        out("| `%s` | %d | %s | **%s** |" % (case.name, len(near_src), g(near_rt, 6), g(far_rt, 6)))
    out("")

    # --- The boolean, near vs far -------------------------------------------------
    out("## Boolean results near vs far")
    out("")
    out("The offset is applied to the **vertex coordinates**, which is what a project does when")
    out("it models in a national projection. *Vertex deviation* is the worst nearest-neighbour")
    out("distance after translating the far result back by −offset, taken as the worse of both")
    out("matching directions. Times are the median of %d fresh runs." % args.repeats)
    out("")
    out("| Case | Solver | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far |")
    out("|---|---|---|---|---|---|---|---|")
    worst_overall = 0.0
    rows = []
    for case in cases:
        far_a = offset(case.a.vertices, case.offset)
        far_b = offset(case.b.vertices, case.offset)
        for solver in solvers:
            for operation in ("UNION", "INTERSECT"):
                near_times, far_times = [], []
                near = far = None
                for _ in range(args.repeats):
                    near = run_boolean(case.a.vertices, case.a.faces,
                                       case.b.vertices, case.b.faces, solver, operation)
                    far = run_boolean(far_a, case.a.faces, far_b, case.b.faces,
                                      solver, operation)
                    near_times.append(near["ms"])
                    far_times.append(far["ms"])
                far_back = [(x - OFFSET[0], y - OFFSET[1], z - OFFSET[2])
                            for (x, y, z) in far["verts"]]
                deviation = max_nearest_deviation(near["verts"], far_back)
                far_volume = signed_volume(far_back, far["tris"]) if far["tris"] else 0.0
                delta_v = far_volume - near["volume"]
                if deviation is not None:
                    worst_overall = max(worst_overall, deviation)
                rows.append((case.name, solver, operation, deviation))
                expected = (case.expected_volume_union if operation == "UNION"
                            else case.expected_volume_intersection)
                near_word = valid_word(near, expected)
                far_word = valid_word(far, expected)
                out("| `%s` | %s | %s | %s | %s / %s | %s | **%s m** over %d/%d v | %.2f / %.2f |" % (
                    case.name, SOLVER_LABELS.get(solver, solver),
                    "union" if operation == "UNION" else "common",
                    (near_word if near_word == far_word else
                     "near %s / far %s" % (near_word, far_word)),
                    g(near["volume"]), g(far_volume), g(delta_v, 6),
                    g(deviation, 6), len(near["verts"]), len(far["verts"]),
                    statistics.median(near_times), statistics.median(far_times),
                ))
    out("")
    out("**Worst vertex deviation over the whole set: %s m.** R-17's pass line is 1e-6 m and its"
        % g(worst_overall, 6))
    out("fail line is 1e-4 m.")
    out("")

    # --- Probe: the offset in the object transform instead of the vertices --------
    out("## Probe — the same offset carried by the object transform")
    out("")
    out("Identical geometry, but the 500 km sits in each object's `location` and the vertex data")
    out("stays at the origin: a local frame with the far placement outside it. Both operands")
    out("carry the same location, so the modifier evaluates in A's local space. This is the")
    out("mitigation ADR-0006 proposes, measured on the candidate rather than assumed.")
    out("")
    out("| Case | Solver | Op | Valid? | V | Vertex deviation vs. the origin run |")
    out("|---|---|---|---|---|---|")
    for case in cases:
        for solver in solvers:
            for operation in ("UNION", "INTERSECT"):
                near = run_boolean(case.a.vertices, case.a.faces,
                                   case.b.vertices, case.b.faces, solver, operation)
                placed = run_boolean(case.a.vertices, case.a.faces,
                                     case.b.vertices, case.b.faces, solver, operation,
                                     location=OFFSET)
                deviation = max_nearest_deviation(near["verts"], placed["verts"])
                expected = (case.expected_volume_union if operation == "UNION"
                            else case.expected_volume_intersection)
                out("| `%s` | %s | %s | %s | %s | %s m |" % (
                    case.name, SOLVER_LABELS.get(solver, solver),
                    "union" if operation == "UNION" else "common",
                    valid_word(placed, expected),
                    g(placed["volume"]), g(deviation, 6)))
    out("")
    out("The modifier evaluates in the modified object's local space, so the result mesh is")
    out("expressed in that space too: these deviations are measured against the origin run")
    out("directly, with no translation back.")
    out("")

    path = args.out
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s" % path)
    print("worst vertex deviation %s m" % g(worst_overall, 6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
