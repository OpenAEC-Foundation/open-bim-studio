#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Choose the next YYYY.W.N release from local tags; publish nothing.

Fetch tags before calling this in CI. Calendar weeks use UTC. The full
version identifies the app, archives and tag; MSI maps YYYY to YYYY-2000
because its major version must fit in a byte. Explicit legacy versions
remain usable for reproducing old packages.
"""
import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path


def msi_version(version):
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError("version must contain three integers without leading zeros")
    major, minor, patch = map(int, version.split("."))
    if major >= 2000:
        datetime.date.fromisocalendar(major, minor, 1)
        major -= 2000
    if not (0 <= major <= 255 and 0 <= minor <= 255 and 0 <= patch <= 65535):
        raise ValueError("version exceeds MSI's 255.255.65535 limits")
    return f"{major}.{minor}.{patch}"


def next_version(today, tags):
    year, week, _ = today.isocalendar()
    prefix = f"v{year}.{week}."
    sequences = []
    for tag in tags:
        if tag.startswith(prefix):
            sequence = tag[len(prefix):]
            if re.fullmatch(r"0|[1-9][0-9]*", sequence):
                sequences.append(int(sequence))
    version = f"{year}.{week}.{max(sequences, default=-1) + 1}"
    msi_version(version)
    return version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--version", help="explicit package version instead of the next tag")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    try:
        version = args.version
        if version is None:
            result = subprocess.run(["git", "-C", args.root, "tag", "--list"],
                                    capture_output=True, text=True, check=True)
            today = datetime.datetime.now(datetime.timezone.utc).date()
            version = next_version(today, result.stdout.splitlines())
        metadata = {"version": version, "tag": f"v{version}", "msi": msi_version(version)}
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8", newline="\n") as output:
                for key, value in metadata.items():
                    output.write(f"{key}={value}\n")
        print(json.dumps(metadata) if args.json else version)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"release_version: {error}\n")


if __name__ == "__main__":
    main()
