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
path supplies linking and runtime lookup.

The downloaded compiler embeds its CI build root. An initial attempt to expose
its library through ignored application-local links was incorrect: canonical
source paths then fell outside the compiler's internal-library prefix.
`isInternalSourcePath` controls standard-library handling in both pattern
expansion and validation. That run was stopped after 53:13 (peak 1,725,824 KiB),
without diagnostics or a test result; it is not a valid performance baseline.
The temporary library links were removed, retaining tracked overrides.

The corrected local launcher uses a user-local PRoot bind of the compiler
checkout at its original `/home/runner/work/dynlex/dynlex` build root. This keeps
canonical standard-library paths under the compiler's expected prefix, without
modifying compiler code, replacing the binary or requiring administrator access.
A core-only vector reproduction compiles and runs through that launcher. Local
builds use `bash build/run-with-toolchain.sh bash build.sh ...`; the launcher
and host configuration remain ignored build artifacts.

An independent app-only Linux build of application source `2b58b0f` passed in
[Actions run 40780935702](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40780935702).
The `BIM_DEBUG=0 build.sh dev` command took 24:03.82, peak RSS 3,511,468 KiB on the
Actions runner, with no compiler diagnostics. This build excludes embedded checks.
Its compiler source `c184581` differs from `ff5c334` only by the build workflow;
the binary SHA-256 is the same. The resulting binary was downloaded and run on
this machine with the user-local shared libraries.

A replacement compiler built at the actual local destination prefix is available
from [run 40782028896](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40782028896),
source `328c27557a69b8b2dca53291fcbec9b6c861d548`, binary SHA-256
`e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.
Only the build workflow changes; its embedded prefix is the local compiler
checkout, so native use avoids PRoot. After the app/check compile finished, the
binary and its matching runtime archives were installed atomically, retaining a
backup of the previous binaries. Every supplied `.dl` library source matched
the existing checkout byte-for-byte. The isolated `system_planning` fixture from
PR #26 then compiled locally without diagnostics and passed all nine assertions,
including exact output comparison. This validates native-prefix operation, not
the full application or the failed editing fixture below.

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
- `BIM_DEBUG=0 bash build.sh dev-test system_editing building_system system_types`:
  compilation completed with an empty diagnostic file, but the self-test returned
  a runtime failure. Total command duration was 1:22:58, peak RSS 3,907,584 KiB.
  The application source built was `2b58b0f`; later branch changes are documentation only.
- Windows app CI for #24: passed in 12m43s.
- Independent app-only Linux build: passed; native application starts locally.
- Native application/API smoke: passed for library enumeration, two curtain-system recipes,
  a fixed timber window, and an HSB wall with its two child layers. Undo/redo restores
  complete HSB creation atomically. The model is the supplied example plus synthetic samples.
- Native 3D view inspected; screenshot and API response reports remain ignored build artifacts.

## Runtime failure exposed after compilation

The wrapper's original self-test output was empty. Running the same binary
outside PRoot with the user-local shared-library path and line-buffered output
reproduces an abort (exit 134) in `system_editing`. The output first diverges at
the contour sketch message: the editor offers point/edge selection instead of
the expected line-start state. After the test's Escape/pick/delete sequence it
prints `picked: -1` and `Tab: select an element to edit its points`.

A native GDB backtrace identifies `stop_because_a_list_index_is_out_of_bounds`,
called by `show_system_test_parts_of...` inside `run_bim_bundled_test_qaa`.
That helper unconditionally reads the first curtain. This establishes where
the run aborts; it does not establish whether the preceding interaction is an
outdated fixture or an editor regression. The editor owner is asked to confirm
the intended Escape/sketch workflow before any behavioural change. Expected
output has not been weakened or replaced to hide the failure.

Consequently `system_editing` is **RUNTIME FAIL**, and the later embedded
`building_system` and `system_types` checks were **not reached**. PR #24 fixes
the two constructor diagnostics but is not a fully passing regression repair.
The successful app-only Linux/Windows builds and interactive smoke checks are
separate evidence; they do not turn this runtime failure into a pass.

Elize's independent Linux baseline in #22 reports every pattern check passing
except `system_editing` (the diagnostic above) and `grid_sheet` (runtime assertion
`reference sheet records paper and artwork once`). The latter is not fixed or
claimed as passing by this change. A full test suite and installer validation
are outside this bounded regression repair.
