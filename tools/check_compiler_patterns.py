#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check pattern tracking, precedence components and bounded resolution time."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


FIXTURES = (
    "pattern_reference_tracking",
    "precedence_accessor_component",
    "precedence_component_self_cycle",
)
BENCH_PRELUDE = '''function set variable to value:
    replacement:
        @intrinsic("store", variable, value)

function an integer:
    replacement:
        @intrinsic("type", "int")

function emit value:
    replacement:
        @intrinsic("discard", @intrinsic("variadic call", "libc", "printf", an integer, 1, "%d\\n", value))

function left + right:
    before: default
    replacement:
        @intrinsic("add", left, right)

'''


def benchmark_source():
    classes = "".join(
        f"class:\n    patterns:\n        storage{index}\n"
        "    members:\n        x as an integer\n\n"
        for index in range(600)
    )
    return BENCH_PRELUDE + classes + '''set first to @intrinsic("construct", storage0, 10)
set second to @intrinsic("construct", storage1, 20)
emit first's x + second's x
'''


def normalized(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text).replace("\r\n", "\n").strip()


def run(command, tree, environment, timeout):
    result = subprocess.run(
        [str(part) for part in command], cwd=tree, env=environment,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout,
    )
    return result


def check(args):
    compiler = args.compiler.resolve()
    if not compiler.is_file():
        raise ValueError(f"Compiler does not exist: {compiler}")
    tree = args.compiler_tree.resolve() if args.compiler_tree else next(
        (parent for parent in compiler.parents if (parent / "tests/required").is_dir()), None
    )
    if tree is None:
        raise ValueError("Cannot locate tests/required; supply --compiler-tree")
    fixtures = tree / "tests/required"
    for name in FIXTURES:
        expected = "expected_diagnostics.txt" if name.endswith("self_cycle") else "expected.txt"
        for filename in ("main.dl", expected):
            if not (fixtures / name / filename).is_file():
                raise ValueError(f"Missing fixture file: {fixtures / name / filename}")
    environment = os.environ.copy()
    for name in ("DYNLEX_PROFILE_STAGES", "DYNLEX_TRACE_RESOLUTION"):
        environment.pop(name, None)
    with tempfile.TemporaryDirectory(prefix="bim-compiler-patterns-") as temporary:
        work = Path(temporary)
        for name in FIXTURES:
            fixture = fixtures / name
            executable = work / (name + (".exe" if os.name == "nt" else ".out"))
            result = run([compiler, fixture / "main.dl", "-o", executable],
                         tree, environment, args.timeout_seconds)
            diagnostics = normalized(result.stdout + result.stderr)
            if name.endswith("self_cycle"):
                expected = normalized((fixture / "expected_diagnostics.txt").read_text(encoding="utf-8"))
                if result.returncode != 1 or diagnostics != expected or executable.exists():
                    raise ValueError(f"{name}: expected cycle rejection, exit {result.returncode}\n{diagnostics}")
            else:
                if result.returncode != 0 or diagnostics or not executable.is_file():
                    raise ValueError(f"{name}: compilation failed, exit {result.returncode}\n{diagnostics}")
                result = run([executable], tree, environment, args.timeout_seconds)
                expected = normalized((fixture / "expected.txt").read_text(encoding="utf-8"))
                if result.returncode != 0 or result.stderr or normalized(result.stdout) != expected:
                    raise ValueError(f"{name}: output mismatch, exit {result.returncode}\n"
                                     f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}")
            print(f"{name}: PASS", flush=True)
        source = work / "precedence-bench-600.dl"
        source.write_text(benchmark_source(), encoding="utf-8")
        started = time.perf_counter()
        result = run([compiler, source, "--emit-completions", "1:1"],
                     tree, environment, args.timeout_seconds)
        elapsed = time.perf_counter() - started
        if result.returncode != 0 or normalized(result.stderr):
            raise ValueError(f"precedence-bench-600: failed, exit {result.returncode}\n{result.stderr}")
        if elapsed > args.budget_seconds:
            raise ValueError(f"precedence-bench-600: {elapsed:.3f}s exceeds {args.budget_seconds:g}s budget")
        print(f"precedence-bench-600: PASS ({elapsed:.3f}s, budget {args.budget_seconds:g}s)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True, help="Compiler executable to check")
    parser.add_argument("--compiler-tree", type=Path, help="Source tree containing tests/required (default: compiler ancestor)")
    parser.add_argument("--budget-seconds", type=float, default=30, help="600-class resolution budget (default: 30)")
    parser.add_argument("--timeout-seconds", type=float, default=120, help="Timeout for each subprocess (default: 120)")
    args = parser.parse_args()
    if not (0 < args.budget_seconds <= args.timeout_seconds < float("inf")):
        parser.error("require 0 < budget-seconds <= timeout-seconds < infinity")
    try:
        check(args)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
