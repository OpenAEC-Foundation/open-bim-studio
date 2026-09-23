"""Build the pinned DWG reader and exercise the DynLex viewer with a real DWG."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cadkernel"))
from verify import run_process  # noqa: E402


def check(command: list[str], phase: str, timeout: float = 120) -> str:
    status, output, _ = run_process(command, timeout=timeout, cwd=ROOT, phase=phase)
    if status != 0:
        raise RuntimeError(f"{phase} failed ({status}):\n{output[-4000:]}")
    return output


def main() -> int:
    bridge = ROOT / "examples" / "dynedra-dwg" / "bridge" / "Cargo.toml"
    target = ROOT / "build" / "dynedra-dwg-cargo"
    cargo = os.environ.get("CARGO", "cargo")
    compiler = ROOT / "build" / ("dynlex.exe" if os.name == "nt" else "dynlex")
    reader = target / "debug" / ("dynedra-dwg-reader.exe" if os.name == "nt" else "dynedra-dwg-reader")
    fixture = ROOT / "build" / "dynedra-dwg-sample.dwg"
    check([cargo, "test", "--offline", "--manifest-path", str(bridge), "--target-dir", str(target)], "reader tests", 300)
    check([cargo, "build", "--offline", "--manifest-path", str(bridge), "--target-dir", str(target)], "reader build", 300)
    check([str(reader), "fixture", str(fixture)], "sample DWG generation", 90)
    stream = check([str(reader), "export", str(fixture)], "DWG decoding", 90)
    if not stream.startswith("DYNEDRA-DWG-1 6 115 0\n"):
        raise RuntimeError(f"unexpected DWG wireframe: {stream[:100]!r}")
    for optimization in ("0", "2"):
        suffix = ".exe" if os.name == "nt" else ""
        probe = ROOT / "build" / f"dynedra-dwg-check-O{optimization}{suffix}"
        viewer = ROOT / "build" / f"dynedra-dwg-viewer-O{optimization}{suffix}"
        check([str(compiler), "tests/cadkernel/dwg_viewer/main.dl", f"-O{optimization}", "-o", str(probe)], f"DynLex test compile O{optimization}", 180)
        check([str(compiler), "examples/dynedra-dwg/main.dl", f"-O{optimization}", "-o", str(viewer)], f"DynLex viewer compile O{optimization}", 180)
        output = check([str(probe), str(fixture), str(reader)], f"DynLex hidden graphics O{optimization}", 90)
        if "decoded, parsed and drew 115 segments" not in output:
            raise RuntimeError(f"missing viewer success marker: {output!r}")
        print(f"O{optimization}: DWG reader, DynLex parser and drawable frame passed")
    print(f"Sample drawing: {fixture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
