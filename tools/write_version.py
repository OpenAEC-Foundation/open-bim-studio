#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Writes generated/version.dl: the version the application shows (issues #3
and #29). BIM_VERSION, which the release workflow sets to YYYY.W.N, or else
the ISO year and week marked "dev"; and the short source commit, so local
builds can be told apart. Called by build.sh generate and the Windows build
scripts."""
import argparse
import datetime
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="generated/version.dl")
parser.add_argument("--root", default=".")
arguments = parser.parse_args()

year, week, _ = datetime.date.today().isocalendar()
version = os.environ.get("BIM_VERSION") or f"{year}.{week} dev"
try:
    commit = subprocess.run(["git", "-C", arguments.root, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip() or "unknown"
except (OSError, subprocess.CalledProcessError):
    commit = "unknown"
for text in (version, commit):
    if '"' in text or "\\" in text:
        raise SystemExit(f"write_version: unusable text {text!r}")

os.makedirs(os.path.dirname(arguments.out) or ".", exist_ok=True)
with open(arguments.out, "w", encoding="utf-8", newline="\n") as written:
    written.write("# Written by tools/write_version.py: the version the application shows.\n"
                  "function the bim app version:\n    execute:\n"
                  f"        return the string form of \"{version}\"\n"
                  "function the bim app commit:\n    execute:\n"
                  f"        return the string form of \"{commit}\"\n")
