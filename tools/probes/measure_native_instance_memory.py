#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Sample the owned native allocation probe at its synchronous phase barriers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
binary = args.binary.resolve()
process = subprocess.Popen(['stdbuf', '-oL', str(binary)], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, text=True)
rows = []
try:
    for line in process.stdout:
        status = dict(item.split(':', 1) for item in Path(f'/proc/{process.pid}/status').read_text().splitlines() if ':' in item)
        row = {'phase': line.strip(), 'rss_kib': int(status['VmRSS'].split()[0]),
               'peak_kib': int(status['VmHWM'].split()[0])}
        rows.append(row)
        print(json.dumps(row), flush=True)
        process.stdin.write('\n')
        process.stdin.flush()
    if process.wait() or len(rows) != 6:
        raise RuntimeError('allocation probe failed or missed its phase barriers')
    result = {'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'scope': '100000 retained four-vertex component meshes; five grouping passes; not renderer FPS',
              'samples': rows}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait(10)
