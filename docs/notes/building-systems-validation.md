# Building Systems validation on the Nino Linux machine

## Source and toolchain

- Application baseline: `main` `c5fdfc8` (2026-10-28).
- Task branch: `mod/pattern/system-editing-test`; coordination: [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22).
- Machine: Linux x86-64, AMD Ryzen 7 3700U, approximately 13 GiB RAM.
- Compiler: DynLex `0.0.3`, pinned `c2d32bea` plus the six application compiler patches. The isolated build branch contains those patches and a Linux bootstrap workflow; no additional compiler behaviour is introduced.
- Compiler source: `ff5c334e528b428abe4090a3c935539808a0307b` in `OpenAEC-Foundation/dynlex`.
- Compiler binary SHA-256: `a5e0723adb8d4171312f6d68118bfe305e8ec1fecb0d116f54666ac9aeb5348d`.
- Successful compiler build: [Actions run 40773371392](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40773371392), artifact `obs-linux-toolchain-c2d32bea`.

The host has no passwordless administrator access. GLFW and development-library
packages are extracted under the user's local data directory. The native DynLex
runtime archives are built locally from the same compiler source with the system
C compiler, and placed in the compiler's installed-library layout. The compiler
checkout is selected by the ignored `.dynlex-root.local`; its bootstrap library
path supplies linking and runtime lookup. Ignored local links under `lib/` expose
the pinned standard library while retaining all tracked application overrides;
the CI compiler's original build path does not exist on this machine. None of
these host paths or library links is part of the product change.

## Restored editing regression

`pattern/common/tests/system_editing.dl` used two calls shaped as
`a cad vector2 with x ..., y ...` when creating the system for the part-context
checks. The constructor in `kernel/core/core.dl` requires `with x ... and y ...`.
A two-vector reproduction importing only the core reports two unresolved
patterns with the original spelling; after using the declared constructor both
calls compile without diagnostics and print the expected coordinates `0` and `6`.
The full uncorrected editing test was stopped before it returned diagnostics;
that partial run is not counted as a baseline result.

Only the two test calls are corrected. Existing expected output is retained,
including part suppression, undo, frame replacement and panel unpinning checks.

## Checks

- Python module-composition/preflight tests: 10 passed.
- `scripts/check-layers.sh`: passed; no new dependency edges.
- Minimal vector reproduction: original calls DIAG, corrected calls compile and run.
- `BIM_DEBUG=0 bash build.sh dev-test system_editing building_system system_types`: in progress.
- Interactive application inspection: pending the build.

Elize's independent Linux baseline in #22 reports every pattern check passing
except `system_editing` (the diagnostic above) and `grid_sheet` (runtime assertion
`reference sheet records paper and artwork once`). The latter is not fixed or
claimed as passing by this change. A full test suite and installer validation
are outside this bounded regression repair.
