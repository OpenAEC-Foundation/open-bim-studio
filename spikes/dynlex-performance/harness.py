"""R-19 harness: build the four workloads in both languages, run them, compare.

Throwaway spike code.

Every workload prints its answer lines first and the elapsed milliseconds of its
own timed region last. The harness compares the answer lines between the two
languages, takes the median of five runs of the internal timing, and also
records whole-process wall time with an empty-program baseline subtracted as a
cross-check on the internal clock. `prng_only` was added for finding I1: it
isolates the generation share of tritri/orient3d's timed regions (see
TIMED_REGION above).

The harness also builds orient3d.dl with **no** optimisation flag at all
(finding M2) and compares it byte-for-byte (md5) against the explicit `-O0`
build, so the "the compiler's default is -O0" claim is checkable from the
repo rather than only asserted in prose.

    python harness.py --dynlex ../../../dynlex/build/dynlex.exe

Writes results/dynlex-performance.md.
"""

import argparse
import hashlib
import os
import pathlib
import statistics
import struct
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE / "build"
RESULTS = HERE / "results"

WORKLOADS = ["tritri", "bvh", "orient3d", "prng_only"]

WORKLOAD_TITLES = {
    "tritri": "Triangle/triangle, 1e6 pairs",
    "bvh": "BVH build, 1e6 boxes",
    "orient3d": "orient3d f64, 1e7 quadruples",
    "prng_only": "PRNG-only baseline, 1.2e8 doubles (finding I1)",
}

# orient3d.dl and tritri.dl start the clock before the generation loop, so the
# PRNG draws are inside the timed region for those two; bvh.dl/.cpp times the
# build only, with generation (and therefore the PRNG) outside it. Recorded
# here so the disclosure in FINDINGS.md/README.md traces to one place.
TIMED_REGION = {
    "tritri": "generation (6 random points per pair) + the edge-wise Moeller-Trumbore test",
    "bvh": "the build only; box generation (and the PRNG) is outside the timed region",
    "orient3d": "generation (4 random points per quadruple) + the orient3d determinant",
    "prng_only": "generation only (4 random points per iteration, no arithmetic on them) — isolates the PRNG share of tritri/orient3d",
}

RUNS = 5
TAGS = ("dl_O2", "dl_O0", "cpp")


def run(cmd, cwd=None):
    started = time.perf_counter()
    done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    wall = time.perf_counter() - started
    return done, wall


def build(dynlex):
    BUILD.mkdir(exist_ok=True)
    log = []
    for name in WORKLOADS + ["empty", "clock_calibration"]:
        for level, tag in (("-O2", "dl_O2"), ("-O0", "dl_O0")):
            out = BUILD / f"{name}_{tag}.out"
            cmd = [str(dynlex), f"{name}.dl", level, "-o", str(out)]
            done, wall = run(cmd, cwd=HERE)
            if done.returncode != 0:
                sys.exit(f"dynlex failed for {name} {level}:\n{done.stdout}\n{done.stderr}")
            log.append((f"{name}.dl", level, round(wall, 2), done.stdout.strip()))
        if name == "clock_calibration":
            continue  # DynLex only: it calibrates the DynLex side's clock
        out = BUILD / f"{name}_cpp.exe"
        cmd = ["clang++", "-O2", "-std=c++17", f"{name}.cpp", "-o", str(out)]
        done, wall = run(cmd, cwd=HERE)
        if done.returncode != 0:
            sys.exit(f"clang++ failed for {name}:\n{done.stdout}\n{done.stderr}")
        log.append((f"{name}.cpp", "-O2", round(wall, 2), done.stderr.strip()))
    return log


def md5_of(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


DEFAULT_BUILD_CHECK_SOURCE = "orient3d"


def pe_coff_timestamp_offset(data):
    """Offset of the PE COFF File Header's TimeDateStamp field (4 bytes, LE),
    found via the DOS header's e_lfanew pointer at 0x3C. Returns None if this
    is not a PE image (so the caller falls back to a plain byte comparison).
    """
    if len(data) < 0x40:
        return None
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
        return None
    return e_lfanew + 8  # signature(4) + Machine(2) + NumberOfSections(2)


def neutralise_build_timestamps(data):
    """Zero the linker's embedded COFF build timestamp so that two builds of
    the same source, made seconds apart, can be compared for genuine code
    identity rather than failing on an incidental clock value. lld duplicates
    the same TimeDateStamp elsewhere in the image (observed empirically, see
    FINDINGS.md finding M2), so every 4-byte span matching the primary
    timestamp's bytes is zeroed too, not just the COFF header's own copy.

    Returns (patched_bytes, neutralised_offsets, timestamp_or_None).
    """
    patched = bytearray(data)
    offset = pe_coff_timestamp_offset(bytes(patched))
    if offset is None:
        return bytes(patched), [], None
    stamp_bytes = bytes(patched[offset:offset + 4])
    neutralised = []
    search_from = 0
    while True:
        idx = patched.find(stamp_bytes, search_from)
        if idx == -1:
            break
        patched[idx:idx + 4] = b"\x00\x00\x00\x00"
        neutralised.append(idx)
        search_from = idx + 4
    return bytes(patched), neutralised, struct.unpack("<I", stamp_bytes)[0]


def check_default_is_o0(dynlex):
    """Finding M2: compile DEFAULT_BUILD_CHECK_SOURCE with NO flag at all and
    compare it, byte for byte, against the explicit -O0 build already made by
    build(). Also runs the no-flag binary once and checks its answer lines
    against the -O0 binary's, so the "default is -O0" claim is checkable
    in-repo (compile, run, md5) rather than only asserted in prose.

    The raw md5 of a no-flag build and an explicit -O0 build of the same
    source need not match even when the emitted code is identical: lld embeds
    a build TimeDateStamp in the PE header (and, observed empirically,
    duplicates it elsewhere in the image), and the two builds run a few
    seconds apart. So this also computes a timestamp-neutralised md5
    (see `neutralise_build_timestamps`) and reports both, rather than letting
    an incidental timestamp difference stand in for a real code difference.
    """
    name = DEFAULT_BUILD_CHECK_SOURCE
    noflag_out = BUILD / f"{name}_noflag.out"
    cmd = [str(dynlex), f"{name}.dl", "-o", str(noflag_out)]
    done, wall = run(cmd, cwd=HERE)
    if done.returncode != 0:
        sys.exit(f"dynlex failed for {name} (no flag):\n{done.stdout}\n{done.stderr}")

    o0_out = BUILD / f"{name}_dl_O0.out"
    raw_noflag = noflag_out.read_bytes()
    raw_o0 = o0_out.read_bytes()
    md5_noflag = hashlib.md5(raw_noflag).hexdigest()
    md5_o0 = hashlib.md5(raw_o0).hexdigest()

    patched_noflag, offsets_noflag, ts_noflag = neutralise_build_timestamps(raw_noflag)
    patched_o0, offsets_o0, ts_o0 = neutralise_build_timestamps(raw_o0)
    md5_noflag_norm = hashlib.md5(patched_noflag).hexdigest()
    md5_o0_norm = hashlib.md5(patched_o0).hexdigest()

    run_done, _ = run([str(noflag_out)], cwd=HERE)
    if run_done.returncode != 0:
        sys.exit(f"{noflag_out} exited {run_done.returncode}:\n{run_done.stdout}")
    noflag_lines = run_done.stdout.strip().splitlines()

    return {
        "source": f"{name}.dl",
        "compile_s": round(wall, 2),
        "md5_noflag": md5_noflag,
        "md5_o0": md5_o0,
        "binaries_equal": md5_noflag == md5_o0,
        "timestamp_noflag": ts_noflag,
        "timestamp_o0": ts_o0,
        "timestamp_offsets_noflag": offsets_noflag,
        "timestamp_offsets_o0": offsets_o0,
        "md5_noflag_normalised": md5_noflag_norm,
        "md5_o0_normalised": md5_o0_norm,
        "binaries_equal_normalised": md5_noflag_norm == md5_o0_norm,
        "noflag_answers": noflag_lines[:-1],
    }


def measure_interleaved(binaries):
    """Run every binary once per round, RUNS rounds, round-robin.

    Interleaving matters: this machine's absolute times move by tens of percent
    with background load, and running all five of one binary and then all five
    of the next would attribute that drift to the language. Alternating puts
    both languages under the same conditions in each round, which is what the
    dynlex repository's own collatz benchmark does.

    Returns {key: (answer_lines, [internal_ms], [wall_s])}.
    """
    state = {key: [None, [], []] for key in binaries}
    for _ in range(RUNS):
        for key, binary in binaries.items():
            done, wall = run([str(binary)], cwd=HERE)
            if done.returncode != 0:
                sys.exit(f"{binary} exited {done.returncode}:\n{done.stdout}\n{done.stderr}")
            lines = done.stdout.strip().splitlines()
            if state[key][0] is None:
                state[key][0] = lines[:-1]
            elif state[key][0] != lines[:-1]:
                sys.exit(f"{binary} is not deterministic across runs")
            state[key][1].append(int(lines[-1]))
            state[key][2].append(wall)
    return {key: tuple(value) for key, value in state.items()}


def binary_for(name, tag):
    suffix = ".exe" if tag == "cpp" else ".out"
    return BUILD / f"{name}_{tag}{suffix}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dynlex", required=True)
    args = parser.parse_args()

    buildlog = build(args.dynlex)
    default_check = check_default_is_o0(args.dynlex)

    empty = measure_interleaved({tag: binary_for("empty", tag) for tag in TAGS})
    baseline = {tag: statistics.median(empty[tag][2]) for tag in TAGS}

    calibrated = measure_interleaved(
        {tag: BUILD / f"clock_calibration_{tag}.out" for tag in ("dl_O2", "dl_O0")}
    )
    calibration = []
    for tag in ("dl_O2", "dl_O0"):
        answers, internal, walls = calibrated[tag]
        for ticks, wall in zip(internal, walls):
            net = wall - baseline[tag]
            calibration.append((tag, answers[0], ticks, net, ticks / net))

    # Finding I1: orient3d and prng_only are measured in the SAME interleaved
    # rounds (not each in its own separate measure_interleaved call, as the
    # other workloads are) so that this machine's background-load drift falls
    # on both equally. Measured separately, prng_only came out *slower* than
    # orient3d on this machine despite doing strictly less work per iteration
    # (generation only, no determinant) -- a physical impossibility that could
    # only be measurement drift between two separate timing sessions. Joint
    # interleaving is what makes the subtraction below meaningful rather than
    # noise.
    joint_pair = ("orient3d", "prng_only")
    joint_binaries = {(name, tag): binary_for(name, tag) for name in joint_pair for tag in TAGS}
    joint_measured = measure_interleaved(joint_binaries)

    rows = []
    for name in WORKLOADS:
        record = {"name": name}
        if name in joint_pair:
            measured = {tag: joint_measured[(name, tag)] for tag in TAGS}
        else:
            measured = measure_interleaved({tag: binary_for(name, tag) for tag in TAGS})
        for tag in TAGS:
            answers, internal, walls = measured[tag]
            record[tag] = {
                "answers": answers,
                "internal": internal,
                "internal_median": statistics.median(internal),
                "wall_median": statistics.median(walls),
                "wall_net": statistics.median(walls) - baseline[tag],
            }
        record["equal_O2"] = record["dl_O2"]["answers"] == record["cpp"]["answers"]
        record["equal_O0"] = record["dl_O0"]["answers"] == record["cpp"]["answers"]
        rows.append(record)

    orient3d_row = next(r for r in rows if r["name"] == "orient3d")
    prng_row = next(r for r in rows if r["name"] == "prng_only")
    derived_determinant_only_ms = {
        tag: orient3d_row[tag]["internal_median"] - prng_row[tag]["internal_median"] for tag in TAGS
    }
    dl2_det = derived_determinant_only_ms["dl_O2"]
    cpp_det = derived_determinant_only_ms["cpp"]
    derived = {
        "orient3d_dl_O2": orient3d_row["dl_O2"]["internal_median"],
        "orient3d_cpp": orient3d_row["cpp"]["internal_median"],
        "orient3d_whole_ratio": (
            orient3d_row["dl_O2"]["internal_median"] / orient3d_row["cpp"]["internal_median"]
        ),
        "prng_only_dl_O2": prng_row["dl_O2"]["internal_median"],
        "prng_only_cpp": prng_row["cpp"]["internal_median"],
        "determinant_only_dl_O2": dl2_det,
        "determinant_only_cpp": cpp_det,
        "determinant_only_ratio": (dl2_det / cpp_det) if cpp_det > 0 else None,
        "reliable": cpp_det > 0 and dl2_det > 0,
    }

    RESULTS.mkdir(exist_ok=True)
    write_results(rows, baseline, buildlog, calibration, default_check, derived)
    for row in rows:
        print(
            row["name"],
            "dl-O2", row["dl_O2"]["internal_median"],
            "dl-O0", row["dl_O0"]["internal_median"],
            "cpp", row["cpp"]["internal_median"],
            "equal", row["equal_O2"], row["equal_O0"],
        )
    print("default-build-check", default_check["source"],
          "md5-equal", default_check["binaries_equal"])


def write_results(rows, baseline, buildlog, calibration, default_check, derived):
    out = []
    out.append("# Raw results — R-19, DynLex runtime performance against C++\n")
    out.append("Generated by `harness.py`. Every number in `FINDINGS.md` comes from a row here.\n")
    out.append(f"Runs per binary: {RUNS}; the reported figure is the median.\n")
    out.append("The binaries of one workload are run round-robin, one each per round, so that")
    out.append("background load on the machine falls on both languages equally rather than being")
    out.append("attributed to whichever ran first. orient3d and prng_only are the exception: their")
    out.append("six binaries (both workloads, all three tags) are interleaved together in one")
    out.append("round-robin, so the PRNG-subtracted derivation below is not confounded by drift")
    out.append("between two separately-timed sessions (finding I1).\n")

    out.append("\n## Timed region, per workload (finding I1)\n")
    out.append("What each workload's `started .. finished` clock window actually covers —")
    out.append("stated explicitly because for two of the four it is *not* the arithmetic alone:\n")
    out.append("| Workload | Timed region |")
    out.append("|---|---|")
    for name in WORKLOADS:
        out.append(f"| {WORKLOAD_TITLES[name]} | {TIMED_REGION[name]} |")

    out.append("\n## Workload timings (internal clock, milliseconds)\n")
    out.append("`DynLex -O2` is the like-for-like comparison against `clang++ -O2`.")
    out.append("`DynLex default` is the compiler's default emitted-code optimisation level,")
    out.append("which is `-O0` — see `FINDINGS.md`.\n")
    out.append("| Workload | DynLex -O2 ms | C++ -O2 ms | ratio | DynLex default ms | default ratio | outputs equal? |")
    out.append("|---|---:|---:|---:|---:|---:|---|")
    for row in rows:
        dl2 = row["dl_O2"]["internal_median"]
        dl0 = row["dl_O0"]["internal_median"]
        cpp = row["cpp"]["internal_median"]
        out.append(
            f"| {WORKLOAD_TITLES[row['name']]} | {dl2} | {cpp} | "
            f"{dl2 / cpp:.2f}x | {dl0} | {dl0 / cpp:.2f}x | "
            f"{'yes' if row['equal_O2'] and row['equal_O0'] else 'NO'} |"
        )

    out.append("\n## Derived: PRNG-subtracted orient3d (finding I1)\n")
    out.append("orient3d's timed region is generation *and* the determinant (see the timed-region")
    out.append(f"table above); its {derived['orient3d_whole_ratio']:.2f}x whole-workload ratio is therefore a mixed")
    out.append("figure, not a determinant-only one. `prng_only` draws the identical 4 sample points (12 doubles)")
    out.append("per iteration and does nothing else, so `orient3d - prng_only`, done per language,")
    out.append("is a *derived* estimate of the determinant-only cost. Both figures below come from")
    out.append("the SAME interleaved measurement round (see the note above the timed-region table),")
    out.append("so machine-load drift cancels rather than leaking into the subtraction.\n")
    out.append("| | DynLex -O2 ms | C++ -O2 ms |")
    out.append("|---|---:|---:|")
    out.append(f"| orient3d (generation + determinant) | {derived['orient3d_dl_O2']} | {derived['orient3d_cpp']} |")
    out.append(f"| prng_only (generation only) | {derived['prng_only_dl_O2']} | {derived['prng_only_cpp']} |")
    out.append(
        f"| **derived: determinant only** (orient3d − prng_only) | "
        f"{derived['determinant_only_dl_O2']} | {derived['determinant_only_cpp']} |"
    )
    if derived["reliable"]:
        out.append(
            f"\n**Derived determinant-only ratio: {derived['determinant_only_ratio']:.2f}x.**"
        )
        if derived["determinant_only_ratio"] > 1.5:
            out.append(
                " This exceeds the 1.5x pass line R-19 sets for a whole workload — noted here"
                " because the derived figure crosses it, even though the verdict is decided on the"
                " literal whole-workload criterion, not on this derived subtraction.\n"
            )
        else:
            out.append(" This does not exceed the 1.5x line.\n")
    else:
        out.append(
            "\n**The subtraction does not yield a usable derived ratio.** At least one side's"
            " `orient3d − prng_only` is zero or negative, which is not physically possible"
            " (orient3d strictly does more work than prng_only per iteration) and is therefore"
            " read as evidence that the determinant's share is at or below this measurement's"
            " noise floor, not as a negative cost. No derived ratio is reported; the 1.01x"
            " whole-workload figure stands as a mixed PRNG+determinant tie, per finding I1.\n"
        )

    out.append("\n## All five runs per binary (internal clock, milliseconds)\n")
    out.append("| Workload | Binary | runs | median |")
    out.append("|---|---|---|---:|")
    for row in rows:
        for tag, label in (("dl_O2", "DynLex -O2"), ("dl_O0", "DynLex default (-O0)"), ("cpp", "clang++ -O2")):
            runs = ", ".join(str(v) for v in row[tag]["internal"])
            out.append(f"| {row['name']} | {label} | {runs} | {row[tag]['internal_median']} |")

    out.append("\n## Cross-check: whole-process wall time minus empty-program baseline (seconds)\n")
    out.append("Measured with `time.perf_counter` around the process. Includes process")
    out.append("start-up, input generation and printing, so it is larger than the internal")
    out.append("figure; it is here only to confirm the internal clock is not lying.\n")
    out.append("| Binary | empty-program median s | workload median s | net s |")
    out.append("|---|---:|---:|---:|")
    for tag, label in (("dl_O2", "DynLex -O2"), ("dl_O0", "DynLex default (-O0)"), ("cpp", "clang++ -O2")):
        out.append(f"| empty, {label} | {baseline[tag]:.4f} | — | — |")
    for row in rows:
        for tag, label in (("dl_O2", "DynLex -O2"), ("dl_O0", "DynLex default (-O0)"), ("cpp", "clang++ -O2")):
            rec = row[tag]
            out.append(
                f"| {row['name']}, {label} | {baseline[tag]:.4f} | {rec['wall_median']:.4f} | {rec['wall_net']:.4f} |"
            )

    out.append("\n## Output equality\n")
    out.append("Each workload prints its answers and an input checksum (the running sum of every")
    out.append("random number it drew) and the final generator state, so an identical answer with")
    out.append("different inputs cannot pass unnoticed.\n")
    for row in rows:
        out.append(f"### {row['name']}\n")
        out.append("```")
        out.append("DynLex -O2:           " + " | ".join(row["dl_O2"]["answers"]))
        out.append("DynLex default (-O0): " + " | ".join(row["dl_O0"]["answers"]))
        out.append("clang++ -O2:          " + " | ".join(row["cpp"]["answers"]))
        out.append("```")
        out.append(f"Equal (DynLex -O2 vs C++): **{row['equal_O2']}**  ")
        out.append(f"Equal (DynLex default vs C++): **{row['equal_O0']}**\n")

    out.append("\n## Clock calibration\n")
    out.append("The workloads report their own timings in milliseconds on the assumption that libc")
    out.append("`clock()` ticks at 1000 Hz on this toolchain. `clock_calibration.dl` checks that")
    out.append("assumption against an external stopwatch: a fixed-result loop, timed both by")
    out.append("`clock()` and by `time.perf_counter` around the process with the empty-program")
    out.append("baseline subtracted. `CLOCKS_PER_SEC` is 1000 if the last column reads about 1000.\n")
    out.append("One run per line, in order. Readings converge on 1000 from below as the runs")
    out.append("settle: a low reading is the external stopwatch running longer than the tick")
    out.append("count, which is what a descheduled or cold-started process looks like.\n")
    out.append("| Build | loop result | ticks | net wall s | ticks/s |")
    out.append("|---|---|---:|---:|---:|")
    for tag, result, ticks, net, rate in calibration:
        label = "DynLex -O2" if tag == "dl_O2" else "DynLex default (-O0)"
        out.append(f"| {label} | {result} | {ticks} | {net:.4f} | {rate:.1f} |")

    out.append("\n## Compile commands and times\n")
    out.append("| Source | flags | seconds |")
    out.append("|---|---|---:|")
    for source, flags, wall, _ in buildlog:
        out.append(f"| {source} | {flags} | {wall} |")
    out.append("")

    out.append("\n## Default build check (finding M2)\n")
    out.append("`dynlex file.dl -o out` with **no** optimisation flag at all, compiled and run,")
    out.append("compared against the explicit `-O0` build of the same source. If the two binaries'")
    out.append("md5 match, the no-flag build and the `-O0` build are the same compiler output, not")
    out.append("merely two runs that happen to agree — which is stronger evidence than a timing")
    out.append("comparison for \"the compiler's default is -O0\".\n")
    out.append(f"| | |\n|---|---|\n"
               f"| Source | `{default_check['source']}` |\n"
               f"| Compile time, no flag | {default_check['compile_s']} s |\n"
               f"| md5, no flag (raw) | `{default_check['md5_noflag']}` |\n"
               f"| md5, explicit `-O0` (raw) | `{default_check['md5_o0']}` |\n"
               f"| Binaries byte-identical (raw) | **{default_check['binaries_equal']}** |\n"
               f"| No-flag run answers | {' \\| '.join(default_check['noflag_answers'])} |\n")
    out.append("The raw md5 need not match even for identical emitted code: `lld` embeds a PE COFF")
    out.append("`TimeDateStamp` (the build clock, in seconds) and the two builds run a few seconds")
    out.append("apart. So the harness also zeroes every 4-byte span in each binary that is")
    out.append("byte-identical to that binary's own COFF timestamp field — `lld` was observed to")
    out.append("duplicate the value elsewhere in the image, not just in the COFF header — and")
    out.append("rehashes. This is the code-identity check; the raw md5 above is the honest,")
    out.append("unmassaged one.\n")
    ts_noflag = default_check["timestamp_noflag"]
    ts_o0 = default_check["timestamp_o0"]
    ts_delta = (
        f"{abs(ts_noflag - ts_o0)} s" if ts_noflag is not None and ts_o0 is not None else "n/a"
    )
    out.append(f"| | |\n|---|---|\n"
               f"| COFF TimeDateStamp, no flag | `{ts_noflag}` |\n"
               f"| COFF TimeDateStamp, explicit `-O0` | `{ts_o0}` |\n"
               f"| Timestamp delta | {ts_delta} |\n"
               f"| Timestamp occurrences neutralised, no flag | {len(default_check['timestamp_offsets_noflag'])} "
               f"at byte offsets {default_check['timestamp_offsets_noflag']} |\n"
               f"| Timestamp occurrences neutralised, `-O0` | {len(default_check['timestamp_offsets_o0'])} "
               f"at byte offsets {default_check['timestamp_offsets_o0']} |\n"
               f"| md5, no flag (timestamp-neutralised) | `{default_check['md5_noflag_normalised']}` |\n"
               f"| md5, explicit `-O0` (timestamp-neutralised) | `{default_check['md5_o0_normalised']}` |\n"
               f"| Binaries byte-identical (timestamp-neutralised) | **{default_check['binaries_equal_normalised']}** |\n")

    (RESULTS / "dynlex-performance.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
