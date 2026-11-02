#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Summarise retained native orbit measurements without discarding raw samples."""
import argparse
import json
from pathlib import Path


def milliseconds(result, metric, percentile):
    value = (result.get(metric) or {}).get(percentile)
    return f"{value:.3f}" if value is not None else "unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    lines = [
        "# Native component orbit measurements", "",
        "Times are milliseconds. Prep includes prior GPU/fence/acquire waits; it is not pure CPU work.",
        "Presented time includes the preparation and presentation stages.",
        "FPS counts submitted frames during the measured orbit; it is not monitor refresh rate.", "",
        "| Model | Surface | GPU | Observed FPS | Prep p95 | GPU p95 | Presented p95 | Peak RSS MiB |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    entries = []
    for path in args.results:
        result = json.loads(path.read_text())
        if not result.get("frames"):
            raise ValueError(f"no moving-camera frames: {path}")
        if not result.get("model_unchanged"):
            raise ValueError(f"model preservation not established: {path}")
        peak_kib = max(
            (int(sample["VmHWM"].split()[0]) for sample in result["memory_samples"]),
            default=0,
        )
        fps = result.get("observed_fps")
        fps_text = f"{fps:.1f}" if fps is not None else "not recorded"
        name = Path(result["model"]).name
        renderer = "; ".join(result.get("renderer", []))
        gpu_name = renderer.split("device=", 1)[-1].split(" kind=", 1)[0] if renderer else "not recorded"
        row = [name, result.get("surface", "legacy/unrecorded"), gpu_name, fps_text, milliseconds(result, "cpu", "p95_ms"),
               milliseconds(result, "gpu", "p95_ms"),
               milliseconds(result, "presented", "p95_ms"), f"{peak_kib / 1024:.1f}"]
        lines.append("| " + " | ".join(row) + " |")
        entries.append((path, result, name))
    for path, result, name in entries:
        renderer = "; ".join(result.get("renderer", [])) or "not recorded; legacy run"
        lines.extend([
            "", f"## {name}", "",
            f"- Renderer: {renderer}",
            f"- Viewport: {result['viewport']}",
            f"- Build: {result.get('build_note', 'not recorded')}",
            f"- Motion: {result.get('motion_source', 'legacy/unrecorded')}",
            f"- Host recording/presentation p95: {milliseconds(result, 'host_record', 'p95_ms')} / {milliseconds(result, 'host_present', 'p95_ms')} ms.",
            f"- API ready: {result['startup_seconds']:.3f} s; not a first-presentation measurement.",
            f"- Deferred-fit barrier: {result.get('fit_barrier', False)}; fit ready at {result.get('fit_ready_seconds', 'not recorded')} s.",
            f"- Binary SHA-256: `{result['binary_sha256']}`",
            f"- Source model SHA-256: `{result['sha256']}`",
            f"- Raw evidence: `{path.parent.name}/results.json`, `before.png`, `after.png`.",
            "- Build flags and screenshot review must be supplied with any performance conclusion.",
        ])
    text = "\n".join(lines) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
