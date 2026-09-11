"""R-19 harness: build the three workloads in both languages, run them, compare.

Throwaway spike code.

Every workload prints its answer lines first and the elapsed milliseconds of its
own timed region last. The harness compares the answer lines between the two
languages, takes the median of five runs of the internal timing, and also
records whole-process wall time with an empty-program baseline subtracted as a
cross-check on the internal clock.

    python harness.py --dynlex ../../../dynlex/build/dynlex.exe

Writes results/dynlex-performance.md.
"""

import argparse
import os
import pathlib
import statistics
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE / "build"
RESULTS = HERE / "results"

WORKLOADS = ["tritri", "bvh", "orient3d"]

WORKLOAD_TITLES = {
    "tritri": "Triangle/triangle, 1e6 pairs",
    "bvh": "BVH build, 1e6 boxes",
    "orient3d": "orient3d f64, 1e7 quadruples",
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

    rows = []
    for name in WORKLOADS:
        record = {"name": name}
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

    RESULTS.mkdir(exist_ok=True)
    write_results(rows, baseline, buildlog, calibration)
    for row in rows:
        print(
            row["name"],
            "dl-O2", row["dl_O2"]["internal_median"],
            "dl-O0", row["dl_O0"]["internal_median"],
            "cpp", row["cpp"]["internal_median"],
            "equal", row["equal_O2"], row["equal_O0"],
        )


def write_results(rows, baseline, buildlog, calibration):
    out = []
    out.append("# Raw results — R-19, DynLex runtime performance against C++\n")
    out.append("Generated by `harness.py`. Every number in `FINDINGS.md` comes from a row here.\n")
    out.append(f"Runs per binary: {RUNS}; the reported figure is the median.\n")
    out.append("The binaries of one workload are run round-robin, one each per round, so that")
    out.append("background load on the machine falls on both languages equally rather than being")
    out.append("attributed to whichever ran first.\n")

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

    (RESULTS / "dynlex-performance.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
