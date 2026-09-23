"""Stage the DynLex DWG viewer from this repository and run its integration check."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SPIKE = Path(__file__).resolve().parent
REPOSITORY = SPIKE.parents[1]
OVERLAY = SPIKE / "overlay"
DEFAULT_CHECKOUT = REPOSITORY / "build" / "dynlex-port" / ".worktrees" / "cadkernel-port"


def stage(checkout: Path) -> list[Path]:
    compiler = checkout / "build" / ("dynlex.exe" if os.name == "nt" else "dynlex")
    if not compiler.is_file() or not (checkout / "lib" / "process.dl").is_file():
        raise RuntimeError(f"Geen gebouwde DynLex-checkout gevonden: {checkout}")
    created: list[Path] = []
    for source in sorted(OVERLAY.rglob("*")):
        if not source.is_file():
            continue
        destination = checkout / source.relative_to(OVERLAY)
        if destination.exists():
            if destination.read_bytes() != source.read_bytes():
                raise RuntimeError(f"Bestaand bestand wijkt af; niet overschrijven: {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(destination)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dynlex", type=Path, default=Path(os.environ.get("DYNLEX_CHECKOUT", DEFAULT_CHECKOUT)))
    parser.add_argument("--keep", action="store_true", help="laat de gestagede app in de checkout staan")
    arguments = parser.parse_args()
    checkout = arguments.dynlex.resolve()
    created = stage(checkout)
    try:
        verification = checkout / "tests" / "cadkernel" / "dwg_viewer" / "verify.py"
        subprocess.run([sys.executable, "-B", str(verification)], cwd=checkout, check=True, timeout=900)
    finally:
        if not arguments.keep:
            for path in reversed(created):
                path.unlink()
    if arguments.keep:
        print(f"Viewerbronbestanden staan in: {checkout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
