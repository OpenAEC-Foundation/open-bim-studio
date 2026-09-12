"""Point cloud scale driver: how much does one point cost, and where does it stop fitting?

Serves docs/research/kernels/pointclouds.md (P-13, P-05).

Each stage runs in its own process so that a stage that dies of MemoryError is
recorded as a result rather than losing the whole run. `orchestrate` spawns the
stages and prints one JSON object per stage to stdout.

Usage:
    python open3d_driver.py orchestrate            # everything, JSON lines on stdout
    python open3d_driver.py <stage> [--n N] ...    # one stage, one JSON object

Stages:
    env         interpreter, library and machine versions
    construct   time and peak RSS of building a cloud from a (N,3) f64 array
    octree      time and peak RSS of o3d.geometry.Octree.convert_from_point_cloud
    nn          index build + 1000 knn queries, 100 of them verified brute force
    precision   f32 vs f64 storage of the same cloud offset 500 km from the origin
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np
import psutil

# --- fixed parameters, identical in every stage ---------------------------------
SEED = 20260910
EXTENT = 100.0          # metres; the cube the points are drawn from
CHUNK = 2_000_000       # points generated per chunk, to avoid a second full copy
N_QUERIES = 1000        # knn queries timed
N_VERIFY = 100          # of those, verified against brute-force numpy
FAR_OFFSET = (500_000.0, 500_000.0, 0.0)   # the precision-set placement


def peak_rss_bytes():
    """Peak resident set of this process.

    On Windows psutil exposes the OS's own peak working set (`peak_wset`), so no
    polling thread is needed and the peak cannot be missed between samples.
    Elsewhere fall back to the current RSS, which is a lower bound; the JSON
    records which one was used.
    """
    mi = psutil.Process().memory_info()
    if hasattr(mi, "peak_wset"):
        return int(mi.peak_wset), "psutil.memory_info().peak_wset"
    return int(mi.rss), "psutil.memory_info().rss (current, not peak)"


def make_points(n, offset=(0.0, 0.0, 0.0)):
    """(n,3) f64 uniform points in an EXTENT cube, generated in chunks.

    One allocation; each chunk is filled in place, so the array is never
    duplicated. The stream is a function of SEED and n only.
    """
    rng = np.random.default_rng(SEED)
    a = np.empty((n, 3), dtype=np.float64)
    ox, oy, oz = offset
    for start in range(0, n, CHUNK):
        stop = min(start + CHUNK, n)
        block = rng.random((stop - start, 3)) * EXTENT
        block[:, 0] += ox
        block[:, 1] += oy
        block[:, 2] += oz
        a[start:stop] = block
    return a


def timed(fn, repeats):
    """Run fn `repeats` times, return (median_s, all_s, last_result)."""
    times, result = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - t0)
    return float(np.median(times)), [float(t) for t in times], result


# --- stages ---------------------------------------------------------------------

def stage_env(_args):
    import open3d as o3d
    return {
        "python": sys.version.split()[0],
        "open3d": o3d.__version__,
        "numpy": np.__version__,
        "psutil": psutil.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "total_ram_bytes": int(psutil.virtual_memory().total),
        "seed": SEED,
        "extent_m": EXTENT,
    }


def stage_construct(args):
    """Build one point cloud representation and report time and peak RSS.

    `rss_after_source_array` is taken once the numpy source array exists, so the
    delta to `rss_after_build` is the cost of Open3D's own copy alone.
    """
    import open3d as o3d
    n, rep, repeats = args.n, args.rep, args.repeats
    proc = psutil.Process()

    pts = make_points(n)

    if rep == "legacy":
        src = pts

        def build():
            return o3d.geometry.PointCloud(o3d.utility.Vector3dVector(src))
    elif rep == "tensor64":
        src = pts

        def build():
            return o3d.t.geometry.PointCloud(o3d.core.Tensor(src, o3d.core.float64))
    elif rep == "tensor32":
        src = pts.astype(np.float32)          # the f32 cast itself is not timed
        del pts

        def build():
            return o3d.t.geometry.PointCloud(o3d.core.Tensor(src, o3d.core.float32))
    else:
        raise SystemExit("unknown representation: " + rep)

    # Taken once the source array for *this* representation exists, so the delta
    # below is Open3D's own copy and nothing else.
    rss_source = proc.memory_info().rss
    median, all_times, cloud = timed(build, repeats)
    rss_built = proc.memory_info().rss
    peak, peak_method = peak_rss_bytes()
    n_points = len(cloud.points) if rep == "legacy" else cloud.point.positions.shape[0]
    del cloud
    return {
        "n": n, "rep": rep, "repeats": repeats,
        "build_s_median": median, "build_s_all": all_times,
        "n_points_in_cloud": int(n_points),
        "rss_after_source_array_bytes": int(rss_source),
        "rss_after_build_bytes": int(rss_built),
        "delta_rss_bytes": int(rss_built - rss_source),
        "delta_bytes_per_point": (rss_built - rss_source) / n,
        "peak_rss_bytes": peak, "peak_method": peak_method,
    }


def stage_octree(args):
    import open3d as o3d
    n, depth = args.n, args.depth
    proc = psutil.Process()
    pts = make_points(n)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
    del pts
    rss_before = proc.memory_info().rss

    def build():
        tree = o3d.geometry.Octree(max_depth=depth)
        tree.convert_from_point_cloud(cloud, size_expand=0.01)
        return tree

    median, all_times, tree = timed(build, args.repeats)
    rss_after = proc.memory_info().rss
    peak, peak_method = peak_rss_bytes()
    return {
        "n": n, "max_depth": depth, "repeats": args.repeats,
        "build_s_median": median, "build_s_all": all_times,
        "root_size_m": float(tree.size),
        "rss_before_bytes": int(rss_before), "rss_after_bytes": int(rss_after),
        "delta_rss_bytes": int(rss_after - rss_before),
        "delta_bytes_per_point": (rss_after - rss_before) / n,
        "peak_rss_bytes": peak, "peak_method": peak_method,
    }


def brute_force_nn(pts, queries):
    """Index of the nearest point to each query, computed in chunks in f64."""
    best_i = np.zeros(len(queries), dtype=np.int64)
    best_d = np.full(len(queries), np.inf)
    step = 100_000
    for start in range(0, len(pts), step):
        block = pts[start:start + step]
        # (len(queries), len(block)) squared distances
        d = ((queries[:, None, :] - block[None, :, :]) ** 2).sum(axis=2)
        j = d.argmin(axis=1)
        dj = d[np.arange(len(queries)), j]
        better = dj < best_d
        best_d[better] = dj[better]
        best_i[better] = (start + j)[better]
    return best_i, best_d


def stage_nn(args):
    """Build a nearest-neighbour index, time queries, verify the answers."""
    import open3d as o3d
    n = args.n
    proc = psutil.Process()
    pts = make_points(n)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
    rss_before = proc.memory_info().rss

    median_build, all_build, tree = timed(
        lambda: o3d.geometry.KDTreeFlann(cloud), args.repeats)
    rss_after = proc.memory_info().rss

    rng = np.random.default_rng(SEED + 1)
    queries = rng.random((N_QUERIES, 3)) * EXTENT

    def run_queries():
        out = np.empty(N_QUERIES, dtype=np.int64)
        for i in range(N_QUERIES):
            _, idx, _ = tree.search_knn_vector_3d(queries[i], 1)
            out[i] = idx[0]
        return out

    median_q, all_q, found = timed(run_queries, args.repeats)

    ref_i, ref_d2 = brute_force_nn(pts, queries[:N_VERIFY])
    same_index = int((found[:N_VERIFY] == ref_i).sum())
    # A different index is only a real mismatch if it is a different point.
    got = pts[found[:N_VERIFY]]
    ref = pts[ref_i]
    same_point = int(np.all(got == ref, axis=1).sum())
    peak, peak_method = peak_rss_bytes()
    return {
        "n": n, "repeats": args.repeats,
        "index_build_s_median": median_build, "index_build_s_all": all_build,
        "queries": N_QUERIES,
        "query_batch_s_median": median_q, "query_batch_s_all": all_q,
        "per_query_us": median_q / N_QUERIES * 1e6,
        "verified": N_VERIFY,
        "verify_same_index": same_index,
        "verify_same_point": same_point,
        "verify_mismatches": N_VERIFY - same_point,
        "max_verified_distance_m": float(np.sqrt(ref_d2.max())),
        "rss_before_index_bytes": int(rss_before),
        "rss_after_index_bytes": int(rss_after),
        "delta_rss_bytes": int(rss_after - rss_before),
        "delta_bytes_per_point": (rss_after - rss_before) / n,
        "peak_rss_bytes": peak, "peak_method": peak_method,
    }


def stage_precision(args):
    """Store the same cloud at 500 km as f32 and as f64; measure what storage costs.

    The reference is the f64 world array translated back to the local frame by
    subtracting the offset, which at these magnitudes is exact in f64.
    """
    import open3d as o3d
    n = args.n
    off = np.array(FAR_OFFSET, dtype=np.float64)
    local = make_points(n)                    # the true local-frame coordinates
    far64 = local + off                       # f64 world coordinates

    pc64 = o3d.t.geometry.PointCloud(o3d.core.Tensor(far64, o3d.core.float64))
    pc32 = o3d.t.geometry.PointCloud(
        o3d.core.Tensor(far64.astype(np.float32), o3d.core.float32))

    back64 = pc64.point.positions.numpy().astype(np.float64) - off
    back32 = pc32.point.positions.numpy().astype(np.float64) - off

    err64 = np.abs(back64 - local)
    err32 = np.abs(back32 - local)

    # The same cloud stored f32 at the origin, for the contrast.
    origin32 = local.astype(np.float32).astype(np.float64)
    err_origin32 = np.abs(origin32 - local)

    return {
        "n": n,
        "offset_m": list(FAR_OFFSET),
        "max_abs_error_f32_at_offset_m": float(err32.max()),
        "rms_abs_error_f32_at_offset_m": float(np.sqrt((err32 ** 2).mean())),
        "max_abs_error_f64_at_offset_m": float(err64.max()),
        "max_abs_error_f32_at_origin_m": float(err_origin32.max()),
        "f32_ulp_at_offset_m": float(np.spacing(np.float32(FAR_OFFSET[0]))),
        "f64_ulp_at_offset_m": float(np.spacing(np.float64(FAR_OFFSET[0]))),
    }


STAGES = {
    "env": stage_env,
    "construct": stage_construct,
    "octree": stage_octree,
    "nn": stage_nn,
    "precision": stage_precision,
}


# --- orchestration --------------------------------------------------------------

# (argv, timeout_s). The 10**8 stages are given a generous but finite ceiling:
# a stage that pages for an hour has answered the question just as well as one
# that raises MemoryError, and the record says which happened.
PLAN = [
    (["env"], 300),
    (["construct", "--n", "10000000", "--rep", "legacy", "--repeats", "5"], 900),
    (["construct", "--n", "10000000", "--rep", "tensor64", "--repeats", "5"], 900),
    (["construct", "--n", "10000000", "--rep", "tensor32", "--repeats", "5"], 900),
    (["construct", "--n", "100000000", "--rep", "legacy", "--repeats", "1"], 1800),
    (["construct", "--n", "100000000", "--rep", "tensor64", "--repeats", "1"], 1800),
    (["construct", "--n", "100000000", "--rep", "tensor32", "--repeats", "1"], 1800),
    (["octree", "--n", "1000000", "--depth", "8", "--repeats", "3"], 900),
    (["octree", "--n", "10000000", "--depth", "6", "--repeats", "3"], 1800),
    (["octree", "--n", "10000000", "--depth", "8", "--repeats", "1"], 1800),
    (["nn", "--n", "1000000", "--repeats", "3"], 900),
    (["nn", "--n", "10000000", "--repeats", "3"], 1800),
    (["nn", "--n", "100000000", "--repeats", "1"], 1800),
    (["precision", "--n", "10000000"], 900),
    # Last, because it is the one expected to exhaust the machine.
    (["octree", "--n", "100000000", "--depth", "8", "--repeats", "1"], 1800),
]


def orchestrate(args):
    for call, timeout in PLAN:
        if args.stage_timeout is not None:
            timeout = args.stage_timeout
        cmd = [sys.executable, os.path.abspath(__file__)] + call
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            rc, out = None, (exc.stdout or b"").decode(errors="replace")
            err = "TIMEOUT after {} s".format(timeout)
        wall = time.perf_counter() - t0
        record = {"stage": call[0], "argv": call[1:], "wall_s": wall,
                  "timeout_s": timeout, "returncode": rc}
        if rc == 0 and out.strip():
            record["result"] = json.loads(out.strip().splitlines()[-1])
        else:
            # A stage that dies is a result, not an accident: record what killed it.
            record["failed"] = True
            record["stderr_tail"] = (err or "").strip().splitlines()[-12:]
        print(json.dumps(record), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=list(STAGES) + ["orchestrate"])
    p.add_argument("--n", type=int, default=10_000_000)
    p.add_argument("--rep", default="legacy")
    p.add_argument("--depth", type=int, default=8)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--stage-timeout", type=float, default=None,
                   help="override the per-stage timeout in PLAN (orchestrate only)")
    args = p.parse_args()
    if args.stage == "orchestrate":
        orchestrate(args)
    else:
        print(json.dumps(STAGES[args.stage](args)), flush=True)


if __name__ == "__main__":
    main()
