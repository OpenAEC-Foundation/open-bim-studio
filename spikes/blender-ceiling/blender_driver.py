"""Object-count ceiling driver: what does one Blender object cost?

Run headless from the repository root:

    "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
        --factory-startup --python spikes/blender-ceiling/blender_driver.py -- --counts 1000,10000,100000

Writes `results/blender.md`. Standard library plus `bpy` only.

The question (R-03) is whether Blender's ceiling at BIM element counts is Blender's
or the add-on's. This driver measures the part that is unambiguously Blender's: the
cost of *having* N objects, with no add-on, no interface and no drawing. Each count is
built two ways with the same triangles in both:

* **N objects** — one mesh datablock and one object per box, which is how an IFC
  importer maps elements to Blender.
* **1 object, N shells** — the same boxes as disconnected shells inside a single mesh.

The difference between the two is per-object overhead, isolated from geometry volume.

Four numbers per variant: scene construction, the first full depsgraph evaluation,
one incremental update after moving a single object, and the process's resident memory.
The incremental number is the one that decides whether an editor stays interactive —
it is what a user pays for every drag.

This is a spike: throwaway code, no design proposal.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime
import gc
import os
import platform
import statistics
import sys
import time

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))

# Unit cube, indexed the same way as reference/boolean_torture_set.py's `_box`.
_QUADS = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(x: float, y: float, z: float, size: float = 0.8):
    verts = [
        (x, y, z), (x + size, y, z), (x + size, y + size, z), (x, y + size, z),
        (x, y, z + size), (x + size, y, z + size),
        (x + size, y + size, z + size), (x, y + size, z + size),
    ]
    faces = []
    for a, b, c, d in _QUADS:
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


def grid_positions(count: int):
    side = int(count ** (1.0 / 3.0)) + 1
    made = 0
    for i in range(side):
        for j in range(side):
            for k in range(side):
                if made == count:
                    return
                yield (i * 1.0, j * 1.0, k * 1.0)
                made += 1


def resident_bytes() -> int | None:
    """Process working set, via the Win32 API; None where it is unavailable."""
    try:
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_uint32),
                        ("PageFaultCount", ctypes.c_uint32),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        # The pseudo-handle must be passed as a pointer-width value: without the
        # c_void_p wrapper ctypes marshals the Python int as 32 bits and the call
        # fails silently on x64.
        handle = ctypes.c_void_p(ctypes.windll.kernel32.GetCurrentProcess())
        if not ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb):
            return None
        return int(counters.WorkingSetSize)
    except Exception:
        return None


def wipe_scene() -> None:
    """Remove every object and mesh datablock.

    `bpy.data.batch_remove` rather than a loop over `objects.remove`: the loop is
    quadratic in the object count and does not finish in reasonable time at 1e5
    objects — which is itself a datapoint about per-object cost, but not the one
    this driver is trying to measure.
    """
    ids = list(bpy.data.objects) + list(bpy.data.meshes)
    if ids:
        bpy.data.batch_remove(ids)
    gc.collect()


def build_separate(count: int):
    collection = bpy.context.collection
    objects = []
    for index, (x, y, z) in enumerate(grid_positions(count)):
        verts, faces = box(0.0, 0.0, 0.0)
        me = bpy.data.meshes.new("box%d" % index)
        me.from_pydata(verts, [], [list(f) for f in faces])
        me.update()
        ob = bpy.data.objects.new("box%d" % index, me)
        ob.location = (x, y, z)
        collection.objects.link(ob)
        objects.append(ob)
    return objects


def build_single(count: int):
    verts = []
    faces = []
    for (x, y, z) in grid_positions(count):
        bverts, bfaces = box(x, y, z)
        offset = len(verts)
        verts.extend(bverts)
        faces.extend([i0 + offset, i1 + offset, i2 + offset] for i0, i1, i2 in bfaces)
    me = bpy.data.meshes.new("all")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("all", me)
    bpy.context.collection.objects.link(ob)
    return [ob]


def measure(count: int, variant: str, repeats: int) -> dict:
    def log(message: str) -> None:
        print("    [%6d %-8s] %s" % (count, variant, message), flush=True)

    wipe_scene()
    baseline = resident_bytes()

    log("building...")
    start = time.perf_counter()
    objects = build_separate(count) if variant == "separate" else build_single(count)
    build_ms = (time.perf_counter() - start) * 1000.0
    log("built in %.0f ms; first full evaluation..." % build_ms)

    start = time.perf_counter()
    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get()
    full_ms = (time.perf_counter() - start) * 1000.0
    log("full evaluation %.0f ms; incremental updates..." % full_ms)

    # One object moves; everything else is untouched. This is the cost of a drag.
    incremental = []
    for i in range(repeats):
        objects[0].location = (float(i) * 0.01, 0.0, 0.0)
        start = time.perf_counter()
        bpy.context.view_layer.update()
        incremental.append((time.perf_counter() - start) * 1000.0)
        log("  incremental %d: %.3f ms" % (i, incremental[-1]))

    peak = resident_bytes()
    log("tearing down...")
    objects_count = len(bpy.data.objects)
    mesh_count = len(bpy.data.meshes)
    # 12 triangles per box, counted rather than tessellated: calling
    # `calc_loop_triangles()` on 1e5 datablocks would dominate the measurement.
    triangles = 12 * count
    wipe_scene()
    return {
        "count": count,
        "variant": variant,
        "build_ms": build_ms,
        "full_ms": full_ms,
        "incremental_ms": statistics.median(incremental),
        "incremental_min": min(incremental),
        "incremental_max": max(incremental),
        "objects": objects_count,
        "meshes": mesh_count,
        "triangles": triangles,
        "memory_bytes": (peak - baseline) if (peak and baseline) else None,
    }


def g(value, digits: int = 6) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", default="1000,10000,100000")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default=os.path.join(_HERE, "results", "blender.md"))
    args = parser.parse_args(argv)
    counts = [int(c) for c in args.counts.split(",") if c.strip()]

    lines = []
    out = lines.append
    out("# Object-count ceiling — Blender raw results")
    out("")
    out("Produced by [`../blender_driver.py`](../blender_driver.py). Raw data for")
    out("[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)")
    out("§Measurements and for `problems.md` P-07. Do not edit by hand — re-run the driver.")
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
    out(f"| platform | `{platform.system()} {platform.version()} ({platform.machine()})` |")
    out(f"| processor | `{platform.processor()}` |")
    out(f"| repeats per incremental timing | {args.repeats} (median reported) |")
    out("| startup | `--factory-startup`, `--background` (no interface, no drawing) |")
    out("")
    out("**Background mode draws nothing.** Every number below is therefore a *lower bound* on")
    out("what an interactive session costs: it excludes the viewport, the outliner and the draw")
    out("manager entirely. A ceiling measured here is a ceiling the interface has not yet been")
    out("added to.")
    out("")
    out("## Results")
    out("")
    out("Each box is 12 triangles. *Separate* is one mesh datablock and one object per box —")
    out("how an IFC importer maps elements. *Single* is the same boxes as disconnected shells")
    out("in one mesh, one object. *Incremental* is one `view_layer.update()` after moving a")
    out("single object, with everything else untouched: the cost of one drag.")
    out("")
    out("| Objects | Variant | Datablocks (obj / mesh) | Triangles | Build ms | First full eval ms | Incremental ms | Memory |")
    out("|---|---|---|---|---|---|---|---|")
    results = []
    for count in counts:
        for variant in ("separate", "single"):
            row = measure(count, variant, args.repeats)
            results.append(row)
            out("| %d | %s | %d / %d | %s | %s | %s | **%s** | %s |" % (
                row["count"], row["variant"], row["objects"], row["meshes"],
                g(row["triangles"]), g(row["build_ms"], 4), g(row["full_ms"], 4),
                g(row["incremental_ms"], 4),
                ("%.0f MB" % (row["memory_bytes"] / 1e6))
                if row["memory_bytes"] is not None else "unavailable"))
            print("%6d %-9s build %8.1f ms  full %8.1f ms  incr %8.3f ms" % (
                row["count"], row["variant"], row["build_ms"], row["full_ms"],
                row["incremental_ms"]), flush=True)
    out("")

    out("## Per-object overhead")
    out("")
    out("The difference between the two variants at the same triangle count, divided by the")
    out("object count. Memory per object includes the object, its mesh datablock and the")
    out("depsgraph's evaluated copy.")
    out("")
    out("| Objects | Δ build ms | Δ full eval ms | Δ incremental ms | Δ memory / object |")
    out("|---|---|---|---|---|")
    by_count = {}
    for row in results:
        by_count.setdefault(row["count"], {})[row["variant"]] = row
    for count in counts:
        pair = by_count.get(count, {})
        if "separate" not in pair or "single" not in pair:
            continue
        sep, one = pair["separate"], pair["single"]
        memory = None
        if sep["memory_bytes"] is not None and one["memory_bytes"] is not None:
            memory = (sep["memory_bytes"] - one["memory_bytes"]) / count
        out("| %d | %s | %s | %s | %s |" % (
            count,
            g(sep["build_ms"] - one["build_ms"], 4),
            g(sep["full_ms"] - one["full_ms"], 4),
            g(sep["incremental_ms"] - one["incremental_ms"], 4),
            ("%.0f B" % memory) if memory is not None else "unavailable"))
    out("")
    out("An interactive editor has roughly 16 ms per frame. Which rows above fit inside that,")
    out("and which do not, is the whole of R-03's question for the part that is Blender's.")
    out("")

    path = args.out
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
