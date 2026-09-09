# M0 — Repository Restart and Kernel Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this research repository into a build repository whose `scripts/test.sh` compiles and runs a first DynLex kernel test against a pinned DynLex compiler, with the reversed kernel decision recorded in ADRs.

**Architecture:** Milestone 0 of `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`. Research documents move unmodified to `docs/archive/`; vision, domain and UX documents stay. Three new ADRs record the decisions; `kernel/` gets its first module and test; `scripts/` locates the DynLex compiler from a sibling checkout pinned by commit hash.

**Tech Stack:** DynLex (pinned commit `7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd` of `https://github.com/OpenAEC-Foundation/dynlex`, checked out at `../dynlex`), Git Bash on Windows for scripts, Markdown for documents.

## Global Constraints

- Everything written to disk is English (ADR-0002): documents, file names, commit messages, code, comments.
- Never name competing geotechnical or structural calculation software anywhere. BIM and 3D software (OpenCascade, Blender, AutoCAD, Revit, …) may be named.
- No conversation transcripts, assistant responses or "in this session we…" text anywhere, including commit messages. `PROMPTS.md` is not modified by this plan.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Archived documents are moved, never edited. Kept documents receive only the link fixes and the f64 amendment named in this plan.
- DynLex source files use 4-space indentation and the `.dl` extension. Scripts are Bash (`#!/bin/bash`, `set -euo pipefail`) and run from Git Bash on Windows as well as Linux/macOS.
- All scripts run from the repository root; import paths in kernel `.dl` files are written relative to the repository root (`import kernel/core/core.dl`), which the DynLex compiler resolves through the working directory. Standard-library imports are written `import lib/std.dl` and resolve through the compiler's own source tree.
- Run every DynLex-related shell command from Git Bash (the Bash tool), not PowerShell — the dynlex scripts are Bash scripts.

---

## File structure after M0

```
metadata/DYNLEX_COMMIT                 the pinned dynlex commit hash, one line
scripts/dynlex_toolchain.sh            sourced by build.sh and test.sh; exports DYNLEX_COMPILER or fails with instructions
scripts/build.sh                       compile-checks every kernel library file
scripts/test.sh                        compiles and runs every kernel/**/tests/*/main.dl, compares with expected.txt
kernel/README.md                       what the kernel is, module list, how to run tests
kernel/core/core.dl                    first module file: the kernel version
kernel/tests/smoke/main.dl             first test: prints the kernel version
kernel/tests/smoke/expected.txt
ui/README.md                           brief for the UI library sub-project
ifc/README.md                          brief for the IFC library sub-project
docs/archive/README.md                 why these documents are archived and what superseded them
docs/archive/research/                 moved from docs/research/
docs/archive/architecture/layers.md    moved from docs/architecture/layers.md
docs/archive/architecture/overview.md  moved from docs/architecture/overview.md
docs/archive/roadmap.md, risks.md, BUILD-BRIEF.md   moved from docs/
docs/architecture/decisions/0003-build-on-an-existing-kernel.md   status → superseded
docs/architecture/decisions/0004-build-our-own-kernel-in-dynlex.md
docs/architecture/decisions/0005-multi-representation-kernel.md
docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md
docs/domain/spatial-model.md           amended: f64 local coordinates
docs/domain/capability-inventory.md    amended: one row
README.md, CLAUDE.md, CONTRIBUTING.md  rewritten for a build repository
.gitignore                             build output added
```

---

### Task 0: Build the pinned DynLex compiler (one-time, no commit)

The compiler is not built on this machine: `../dynlex/build/` does not exist and `../dynlex/.cache/llvm-toolchain/` contains only the LLVM source checkout. The bootstrap Clang on PATH is 19.1.1; dynlex requires Clang 20 or newer and installs it through `scripts/install.ps1`. Building the pinned LLVM 23 fork takes hours on first run; every later build reuses the cache.

**Files:** none in this repository.

**Interfaces:**
- Produces: an executable `../dynlex/build/dynlex.exe` at commit `7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd` that compiles `tests/required/simple/main.dl`.

- [ ] **Step 1: Confirm the checkout is at the pinned commit**

Run: `git -C ../dynlex rev-parse HEAD`
Expected: `7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd`

If it differs, stop and report — the pin in Task 1 must match what is built. Do not check out a different commit in `../dynlex`; another agent may be working there (the tree currently has a modified `.gitignore` and an untracked `tests/benchmarks/matrix_solver/`).

- [ ] **Step 2: Install dependencies (PowerShell, once)**

Run in PowerShell from `../dynlex`: `.\scripts\install.ps1`
Expected: ends without a thrown error; installs Clang 20+ bootstrap, CMake, Ninja, vcpkg packages (nlohmann_json, GLFW, FreeType, Vulkan loader).

- [ ] **Step 3: Build the compiler (Git Bash)**

Run from `../dynlex`: `./scripts/build.sh --lint=false`
Expected: first run builds the LLVM toolchain into `.cache/llvm-toolchain` (hours), then the compiler. Run in the background with a 600000 ms timeout and poll; report progress to the maintainer rather than waiting silently.

- [ ] **Step 4: Verify the compiler runs and links**

Run from `../dynlex`: `./build/dynlex.exe --version && ./build/dynlex.exe tests/required/simple/main.dl -o /tmp/simple.out && /tmp/simple.out`
Expected: a version string, then `52`.

If linking fails with "failed to find linker", the dynlex Windows toolchain staging did not complete; rerun `.\scripts\install.ps1` and report the exact error. Do not work around it in this repository.

---

### Task 1: Toolchain pin and locator scripts

**Files:**
- Create: `metadata/DYNLEX_COMMIT`
- Create: `scripts/dynlex_toolchain.sh`
- Create: `scripts/build.sh`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `scripts/dynlex_toolchain.sh`, to be sourced; on success exports `DYNLEX_ROOT` (checkout directory) and `DYNLEX_COMPILER` (absolute path to the executable); on failure prints one `Error: …` line to stderr and exits 1.
- Produces: `scripts/build.sh` — compile-checks `kernel/*/*.dl` into `build/check/`, exit 0 when all compile.

- [ ] **Step 1: Write the pin**

Create `metadata/DYNLEX_COMMIT` containing exactly one line:

```
7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd
```

- [ ] **Step 2: Write the locator**

Create `scripts/dynlex_toolchain.sh`:

```bash
#!/bin/bash
# Locates the pinned DynLex compiler. Source this file; do not execute it.
#
# Exports DYNLEX_ROOT (the dynlex checkout) and DYNLEX_COMPILER (the executable).
# Fails with an instruction when the checkout, the pin or the build is missing.

set -euo pipefail

DYNLEX_TOOLCHAIN_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DYNLEX_TOOLCHAIN_PROJECT_DIR="$(cd "$DYNLEX_TOOLCHAIN_SCRIPT_DIR/.." && pwd)"
DYNLEX_ROOT="${DYNLEX_ROOT:-$DYNLEX_TOOLCHAIN_PROJECT_DIR/../dynlex}"
DYNLEX_PINNED_COMMIT="$(tr -d '[:space:]' < "$DYNLEX_TOOLCHAIN_PROJECT_DIR/metadata/DYNLEX_COMMIT")"

if ! git -C "$DYNLEX_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: no DynLex checkout at $DYNLEX_ROOT. Clone https://github.com/OpenAEC-Foundation/dynlex there or set DYNLEX_ROOT." >&2
    exit 1
fi
DYNLEX_ROOT="$(cd "$DYNLEX_ROOT" && pwd)"

DYNLEX_ACTUAL_COMMIT="$(git -C "$DYNLEX_ROOT" rev-parse HEAD)"
if [[ "$DYNLEX_ACTUAL_COMMIT" != "$DYNLEX_PINNED_COMMIT" ]]; then
    echo "Error: DynLex at $DYNLEX_ROOT is at commit $DYNLEX_ACTUAL_COMMIT but this repository pins $DYNLEX_PINNED_COMMIT (metadata/DYNLEX_COMMIT). Check out the pinned commit, or update the pin deliberately." >&2
    exit 1
fi

DYNLEX_COMPILER="$DYNLEX_ROOT/build/dynlex"
if [[ -x "$DYNLEX_COMPILER.exe" ]]; then
    DYNLEX_COMPILER="$DYNLEX_COMPILER.exe"
fi
if [[ ! -x "$DYNLEX_COMPILER" ]]; then
    echo "Error: DynLex compiler not built at $DYNLEX_COMPILER. Build it with: (cd \"$DYNLEX_ROOT\" && ./scripts/build.sh --lint=false)" >&2
    exit 1
fi

export DYNLEX_ROOT DYNLEX_COMPILER
```

- [ ] **Step 3: Write the build script**

Create `scripts/build.sh`:

```bash
#!/bin/bash
# Compile-checks every kernel library file with the pinned DynLex compiler.
# A library file compiles to a program that defines patterns and does nothing;
# this catches syntax and type errors before the tests run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/dynlex_toolchain.sh"

cd "$PROJECT_DIR"
CHECK_DIR="$PROJECT_DIR/build/check"
mkdir -p "$CHECK_DIR"

echo "DynLex compiler: $DYNLEX_COMPILER ($("$DYNLEX_COMPILER" --version))"

checked=0
while IFS= read -r library_file; do
    relative="${library_file#$PROJECT_DIR/}"
    output="$CHECK_DIR/${relative//\//_}.out"
    echo "check $relative"
    "$DYNLEX_COMPILER" "$library_file" -o "$output"
    checked=$((checked + 1))
done < <(find "$PROJECT_DIR/kernel" -mindepth 2 -maxdepth 2 -name '*.dl' -not -path '*/tests/*' | sort)

echo "$checked library file(s) compile."
```

- [ ] **Step 4: Make the scripts executable and ignore build output**

Run: `chmod +x scripts/build.sh scripts/dynlex_toolchain.sh`

Append to `.gitignore`:

```
# Build output of scripts/build.sh and scripts/test.sh
build/
*.out
```

- [ ] **Step 5: Verify the failure path**

Run: `DYNLEX_ROOT=/nonexistent ./scripts/build.sh; echo "exit=$?"`
Expected: `Error: no DynLex checkout at /nonexistent. …` and `exit=1`.

- [ ] **Step 6: Verify the success path**

Run: `./scripts/build.sh`
Expected: `DynLex compiler: …/dynlex/build/dynlex.exe (<version>)` followed by `0 library file(s) compile.` (the kernel has no files yet).

- [ ] **Step 7: Commit**

```bash
git add metadata/DYNLEX_COMMIT scripts/dynlex_toolchain.sh scripts/build.sh .gitignore
git commit -m "Pin the DynLex compiler and add the build entry point

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Kernel skeleton, test runner and smoke test

**Files:**
- Create: `kernel/README.md`
- Create: `kernel/core/core.dl`
- Create: `kernel/tests/smoke/main.dl`
- Create: `kernel/tests/smoke/expected.txt`
- Create: `scripts/test.sh`

**Interfaces:**
- Consumes: `scripts/dynlex_toolchain.sh` (Task 1), exporting `DYNLEX_COMPILER`.
- Produces: pattern `the kernel version` in `kernel/core/core.dl`, returning the string `0.0.0`.
- Produces: `scripts/test.sh` — discovers every `kernel/**/tests/<name>/main.dl`, compiles it, runs it, compares stdout with `expected.txt` in the same directory (carriage returns and trailing newlines ignored); prints `N passed, M failed`; exit 1 when any fail.

- [ ] **Step 1: Write the failing test**

Create `kernel/tests/smoke/main.dl`:

```
import lib/std.dl
import kernel/core/core.dl

print the kernel version as a line
```

Create `kernel/tests/smoke/expected.txt` containing exactly:

```
0.0.0
```

- [ ] **Step 2: Write the test runner**

Create `scripts/test.sh`:

```bash
#!/bin/bash
# Compiles and runs every kernel test with the pinned DynLex compiler.
#
# A test is a directory containing main.dl and expected.txt. The program's
# standard output must equal expected.txt; carriage returns and trailing
# newlines are ignored so the comparison is the same on every platform.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/dynlex_toolchain.sh"
# The toolchain script enables -e for its own checks; the runner must keep going after a failing test.
set +e

cd "$PROJECT_DIR"
OUTPUT_DIR="$PROJECT_DIR/build/tests"
mkdir -p "$OUTPUT_DIR"

passed=0
failed=0
failures=()

# Command substitution already strips trailing newlines; only carriage returns need removing.
normalize() {
    tr -d '\r'
}

while IFS= read -r main_file; do
    test_dir="$(dirname "$main_file")"
    name="${test_dir#$PROJECT_DIR/}"
    expected_file="$test_dir/expected.txt"
    binary="$OUTPUT_DIR/${name//\//_}.out"

    if [[ ! -f "$expected_file" ]]; then
        failed=$((failed + 1))
        failures+=("$name: missing expected.txt")
        continue
    fi

    if ! compile_output="$("$DYNLEX_COMPILER" "$main_file" -o "$binary" 2>&1)"; then
        failed=$((failed + 1))
        failures+=("$name: compile failed"$'\n'"$compile_output")
        continue
    fi

    actual="$("$binary" 2>&1 | normalize)"
    exit_code=$?    # pipefail is inherited by the substitution, so this is the program's exit code
    expected="$(normalize < "$expected_file")"

    if [[ $exit_code -ne 0 ]]; then
        failed=$((failed + 1))
        failures+=("$name: exited with $exit_code"$'\n'"$actual")
    elif [[ "$actual" != "$expected" ]]; then
        failed=$((failed + 1))
        failures+=("$name: output differs"$'\n'"$(diff <(printf '%s\n' "$expected") <(printf '%s\n' "$actual") || true)")
    else
        passed=$((passed + 1))
        echo "pass $name"
    fi
done < <(find "$PROJECT_DIR/kernel" -path '*/tests/*' -name main.dl | sort)

for failure in "${failures[@]+"${failures[@]}"}"; do
    printf '\nFAIL %s\n' "$failure"
done
printf '\n%d passed, %d failed\n' "$passed" "$failed"
[[ $failed -eq 0 ]]
```

Run: `chmod +x scripts/test.sh`

- [ ] **Step 3: Run the test to verify it fails**

Run: `./scripts/test.sh; echo "exit=$?"`
Expected: `FAIL kernel/tests/smoke: compile failed` with a diagnostic that `kernel/core/core.dl` cannot be found, then `0 passed, 1 failed`, `exit=1`.

- [ ] **Step 4: Write the first module**

Create `kernel/core/core.dl`:

```
# Kernel core: the module every other kernel module imports first.
#
# Milestone 0 defines only the version. Milestone 1 adds vectors, matrices,
# transforms, the tolerance model, exact predicates and handles.

import lib/std.dl

function the kernel version:
    replacement:
        "0.0.0"
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `./scripts/test.sh; echo "exit=$?"`
Expected: `pass kernel/tests/smoke`, `1 passed, 0 failed`, `exit=0`.

If the compiler rejects the program, this is either a kernel-side mistake (fix it here) or a DynLex defect: minimise it to a single file without `import lib/std.dl`, root-cause it in `../dynlex` following its `AGENTS.md`, and report before changing anything in the dynlex repository.

- [ ] **Step 6: Verify the runner detects a wrong expectation**

Run: `printf '9.9.9\n' > kernel/tests/smoke/expected.txt && ./scripts/test.sh; echo "exit=$?"; printf '0.0.0\n' > kernel/tests/smoke/expected.txt`
Expected: `FAIL kernel/tests/smoke: output differs` with a diff, `0 passed, 1 failed`, `exit=1`; the last command restores the expectation.

- [ ] **Step 7: Verify build.sh now checks the module**

Run: `./scripts/build.sh`
Expected: `check kernel/core/core.dl` and `1 library file(s) compile.`

- [ ] **Step 8: Write the kernel README**

Create `kernel/README.md`:

```markdown
# Geometry kernel

A geometry kernel written in DynLex. Design: `../docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`.
Decisions: `../docs/architecture/decisions/0004-…`, `0005-…`, `0006-…`.

## Modules

Dependencies point downward only.

| Module | Purpose | Status |
|---|---|---|
| `core/` | f64 vectors, matrices, quaternions, transforms, frames; tolerance model; exact predicates; generational handles; bounding boxes | M0: version only |
| `curves/` | analytic and NURBS curves | not started |
| `surfaces/` | analytic and NURBS surfaces | not started |
| `brep/` | boundary representation topology and geometry attachment | not started |
| `mesh/` | half-edge mesh with attributes | not started |
| `pointcloud/` | chunked point storage with octree | not started |
| `implicit/` | signed-distance trees and dual contouring | not started |
| `csg/` | booleans per representation | not started |
| `convert/` | explicit cross-representation conversions | not started |
| `spatial/` | BVH, octree, tile grid, ray casting, picking | not started |
| `ops/` | extrude, revolve, sweep, loft, offset, fillet, planar section | not started |
| `gpu/` | buffer layouts, camera-relative f32 packing, compute kernels | not started |
| `io/` | kernel binary format, OBJ and PLY | not started |

## Conventions

- One public `.dl` file per module named after the module (`core/core.dl`); private definitions are marked `local`.
- Imports are written from the repository root: `import kernel/core/core.dl`. Standard library: `import lib/std.dl`.
- Every module has a `tests/` directory. A test is a directory with `main.dl` and `expected.txt`.
- Operations return a result value with an error message on failure; there are no exceptions.
- Compiler defects are minimised, root-caused and fixed in the DynLex repository — never worked around here.

## Running

From the repository root, in Bash:

```bash
./scripts/build.sh   # compile-check every module
./scripts/test.sh    # compile and run every test
```

Both locate the DynLex compiler through `scripts/dynlex_toolchain.sh` (checkout at `../dynlex` or `$DYNLEX_ROOT`, commit pinned in `metadata/DYNLEX_COMMIT`).
```

- [ ] **Step 9: Commit**

```bash
git add kernel scripts/test.sh
git commit -m "Add the kernel skeleton, test runner and smoke test

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Archive the research documents

**Files:**
- Move: `docs/research/` → `docs/archive/research/`
- Move: `docs/architecture/layers.md`, `docs/architecture/overview.md` → `docs/archive/architecture/`
- Move: `docs/roadmap.md`, `docs/risks.md`, `docs/BUILD-BRIEF.md` → `docs/archive/`
- Create: `docs/archive/README.md`
- Modify: links in `docs/vision/*.md`, `docs/domain/*.md`, `docs/ux/*.md` that point at moved files

**Interfaces:**
- Produces: `docs/` containing only `archive/`, `architecture/decisions/`, `domain/`, `superpowers/`, `ux/`, `vision/`.

- [ ] **Step 1: Move with git so history follows**

```bash
mkdir -p docs/archive/architecture
git mv docs/research docs/archive/research
git mv docs/architecture/layers.md docs/archive/architecture/layers.md
git mv docs/architecture/overview.md docs/archive/architecture/overview.md
git mv docs/roadmap.md docs/archive/roadmap.md
git mv docs/risks.md docs/archive/risks.md
git mv docs/BUILD-BRIEF.md docs/archive/BUILD-BRIEF.md
```

- [ ] **Step 2: Verify the layout**

Run: `ls docs docs/architecture docs/archive docs/archive/architecture`
Expected: `docs`: `archive architecture domain superpowers ux vision`; `docs/architecture`: `decisions`; `docs/archive`: `BUILD-BRIEF.md README.md architecture research risks.md roadmap.md` (README appears after Step 3); `docs/archive/architecture`: `layers.md overview.md`.

- [ ] **Step 3: Write the archive README**

Create `docs/archive/README.md`:

```markdown
# Archive

Documents from the research phase (July–September 2026), kept unmodified for their reasoning
and their sources. Relative links inside them may be stale.

They were written under [ADR-0003](../architecture/decisions/0003-build-on-an-existing-kernel.md),
which chose to build on existing geometry and IFC kernels. That decision is superseded by
[ADR-0004](../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md): a new kernel is
written in DynLex. The kernel design is in
[`../superpowers/specs/2026-09-09-geometry-kernel-design.md`](../superpowers/specs/2026-09-09-geometry-kernel-design.md).

| Archived | What it was |
|---|---|
| `research/` | Evaluations of kernels, renderers, hosts, and prior-art notes on existing BIM and 3D tools |
| `architecture/layers.md` | The layered hypothesis built on existing kernels — falsified by decision, not by measurement |
| `architecture/overview.md` | System overview for that hypothesis |
| `roadmap.md` | The research-phase plan (phases 0–5) |
| `risks.md` | The research-phase risk register; R-01 (evaluation), R-13 (topological naming) and R-14 (cross-tile evaluation) remain real and are re-addressed in the application design |
| `BUILD-BRIEF.md` | The intended handover document, never completed |

Still current, and therefore not archived: `docs/vision/`, `docs/domain/`, `docs/ux/`.
```

- [ ] **Step 4: Fix links in the kept documents**

Run from the repository root:

```bash
grep -rln '\.\./research/\|\.\./architecture/layers\.md\|\.\./architecture/overview\.md\|\.\./roadmap\.md\|\.\./risks\.md\|\.\./BUILD-BRIEF\.md' docs/vision docs/domain docs/ux
```

For every listed file apply, in Bash:

```bash
sed -i \
  -e 's#\.\./research/#../archive/research/#g' \
  -e 's#\.\./architecture/layers\.md#../archive/architecture/layers.md#g' \
  -e 's#\.\./architecture/overview\.md#../archive/architecture/overview.md#g' \
  -e 's#\.\./roadmap\.md#../archive/roadmap.md#g' \
  -e 's#\.\./risks\.md#../archive/risks.md#g' \
  -e 's#\.\./BUILD-BRIEF\.md#../archive/BUILD-BRIEF.md#g' \
  <file>
```

- [ ] **Step 5: Verify no dangling links remain in kept documents**

Run:

```bash
grep -rn '\.\./research/\|\.\./architecture/layers\.md\|\.\./architecture/overview\.md\|\.\./roadmap\.md\|\.\./risks\.md\|\.\./BUILD-BRIEF\.md' docs/vision docs/domain docs/ux; echo "exit=$?"
```

Expected: no output and `exit=1` (grep found nothing).

- [ ] **Step 6: Commit**

```bash
git add -A docs
git commit -m "Archive the research-phase documents

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Architecture decision records

**Files:**
- Modify: `docs/architecture/decisions/0003-build-on-an-existing-kernel.md:3`
- Create: `docs/architecture/decisions/0004-build-our-own-kernel-in-dynlex.md`
- Create: `docs/architecture/decisions/0005-multi-representation-kernel.md`
- Create: `docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md`

**Interfaces:**
- Consumes: the ADR template at `docs/architecture/decisions/_template.md` (sections: Status/Date, Context, Decision, Options considered, Consequences, Sources).

- [ ] **Step 1: Mark ADR-0003 superseded**

In `docs/architecture/decisions/0003-build-on-an-existing-kernel.md` replace line 3

```
**Status:** accepted
```

with

```
**Status:** superseded by [ADR-0004](0004-build-our-own-kernel-in-dynlex.md)
```

Change nothing else in that file.

- [ ] **Step 2: Write ADR-0004**

Create `docs/architecture/decisions/0004-build-our-own-kernel-in-dynlex.md`:

```markdown
# ADR-0004 — Build our own geometry kernel, in DynLex

**Status:** accepted
**Date:** 2026-09-09

## Context

ADR-0003 chose to build on existing geometry and IFC kernels, on the grounds that a kernel is a
multi-year effort and not a differentiator. Two things changed.

First, the maintainer has DynLex: a natural-language-like language compiling to native code and
SPIR-V through LLVM, with a Vulkan runtime and a standard library written in the language
itself. A kernel in DynLex is the largest program the language will have carried, and building
it is part of the language's purpose.

Second, the research phase found that every candidate kernel imposes architectural assumptions
(single origin, float32 tessellation paths, evaluation models built for batch rather than
interactive use) that conflict with structural requirements in
`docs/domain/spatial-model.md` and `docs/domain/capability-inventory.md`. Working around a
kernel's assumptions is a different kind of multi-year effort.

## Decision

We build our own geometry kernel, in DynLex, as the first of three libraries in this
repository: `kernel/`, `ui/` (Vulkan-based UI and viewport), `ifc/` (IFC/STEP read-write). The
application is built on the three.

Where DynLex lacks a facility the kernel needs (threading, memory-mapped allocation), the
language is extended in its own repository following its own rules, rather than the kernel
working around the gap.

The design is `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`.

## Options considered

### Build on existing kernels (ADR-0003)
Rejected, reversing ADR-0003. Its argument — a kernel consumes the whole effort — assumed a
general-purpose language and a general-purpose kernel. A kernel scoped by the capability
inventory, in a language the maintainer controls, is a different bet: larger than any single
library integration, smaller than the industry kernels it is compared with, and free of their
assumptions.

### Own kernel in an established systems language
Rejected. It forfeits the reason DynLex exists — a language designed for humans and AI agents
to write together — and it would leave DynLex without its defining large program.

### Own kernel in DynLex — chosen
Full control of representation, precision and evaluation model. Costs: the kernel is the
critical path for everything else, and compiler maturity is now on that path too.

## Consequences

**Easier:** the coordinate architecture, the tolerance model and the evaluation model are ours
from the first line. No licence coupling to upstream kernels (retires the licence-compatibility
risk of the research phase).

**Harder:** robustness of booleans and B-rep operations must be earned by us; there is no
upstream to inherit twenty years of fixes from. Compiler defects block kernel work until fixed.

**Commits us to:** the milestone discipline and performance targets in the kernel design;
extending DynLex when needed; never working around the compiler.

**To reverse:** adopt an existing kernel behind the kernel API. The API is designed to make
that possible in principle; the cost would be the representations that kernel lacks.
```

- [ ] **Step 3: Write ADR-0005**

Create `docs/architecture/decisions/0005-multi-representation-kernel.md`:

```markdown
# ADR-0005 — The kernel has four equal representations with explicit conversions

**Status:** accepted
**Date:** 2026-09-09

## Context

BIM geometry is mostly planar solids, but a building model also carries curved façades, terrain
surfaces, scan data, and free-form elements. The capability inventory lists free-form modelling
as an unlocated seam and point cloud import as within reach once tiling exists. A kernel with a
single native representation forces every other kind of geometry through a lossy conversion.

## Decision

The kernel holds four first-class representations: **B-rep** (analytic and NURBS geometry on
explicit topology, with per-entity tolerances), **mesh** (half-edge, f64, attributed),
**point cloud** (chunked structure-of-arrays with an octree) and **implicit** (signed-distance
trees). None is the source of the others.

Conversions between representations are explicit, named operations with their own parameters
and failure modes. The kernel never converts silently; CSG on mixed representations requires the
caller to pass a conversion policy.

CSG dispatches on representation: B-rep booleans on B-rep, exact arrangement-based booleans on
meshes, node composition on implicits.

## Options considered

### B-rep as the single source, mesh derived (the classic CAD kernel)
Rejected. Exact and complete for engineered solids, but every mesh, scan and organic shape must
be lifted into B-rep or held outside the kernel. B-rep booleans are the hardest software in the
field and would gate every other capability.

### Mesh as the single source (the modelling-tool kernel)
Rejected. Fast and free, but no true curved faces, and IFC export of curved geometry would be
approximated. Dimensional accuracy depends on tessellation density.

### Four equal representations — chosen
Most work, most freedom. Each representation is implemented in the form in which it is strong;
the cost is the conversion matrix, which is kept honest by being explicit.

## Consequences

**Easier:** every geometry class the product needs has a native home; the free-form seam moves
from "unlocated" to "a conversion with known loss".

**Harder:** four representations to keep valid, four sets of tests, and a conversion matrix
whose every cell needs a defined behaviour.

**Commits us to:** an API whose operations name their representation, and to never adding an
implicit conversion for convenience.

**To reverse:** drop a representation by deleting its module; the others do not depend on it.
```

- [ ] **Step 4: Write ADR-0006**

Create `docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md`:

```markdown
# ADR-0006 — Coordinates are f64 in tile-local frames; combinatorial decisions are exact

**Status:** accepted
**Date:** 2026-09-09

## Context

`docs/domain/spatial-model.md` established that unbounded geographic extent is achieved by
keeping every coordinate small: many tile origins held in high precision, geometry expressed
relative to its tile. It proposed float32 for local coordinates on the grounds that a tile a
few hundred metres across keeps float32 below a millimetre.

The kernel's accuracy target is dimensional accuracy of the kind engineering CAD users expect,
and its boolean operations must be robust on real input. Both push the choice away from float32
and toward a separation between metric and combinatorial arithmetic.

## Decision

All kernel coordinates are **64-bit floating point in a tile-local frame**. Tile origins are
64-bit values in the project's projected CRS. Geometry never stores world coordinates; the
`spatial` module owns the tile grid. Only the `gpu` module produces 32-bit values, camera-relative,
at upload time.

**Combinatorial decisions** (orientation, intersection existence, in-circle, in-sphere) use
exact adaptive-precision predicates in the style of Shewchuk. **Metric decisions** (coincidence,
planarity) use an explicit tolerance model — linear 1e-6 m and angular 1e-9 rad by default,
overridable per operation, carried per entity in B-rep.

`spatial-model.md` is amended accordingly; its tile architecture is unchanged.

## Options considered

### float32 local coordinates (the research-phase proposal)
Rejected. Adequate for display, not for modelling: repeated operations accumulate error far
faster than a single representation bound suggests, and exact predicates on float32 input would
still not repair a boolean whose constructed points are already coarse.

### f64 everywhere including the GPU
Rejected. GPU double precision is slow or absent; camera-relative f32 is standard practice for
large worlds and loses nothing visible.

### Exact rational arithmetic throughout
Rejected. Orders of magnitude slower and incompatible with the performance targets; exactness
is needed for decisions, not for stored coordinates.

### f64 local, exact predicates, explicit tolerances — chosen

## Consequences

**Easier:** booleans and intersections can be made robust; dimensional accuracy is a property
of the kernel rather than of tessellation density.

**Harder:** memory per vertex doubles relative to float32; the GPU packing step must exist
from the first rendered frame.

**Commits us to:** implementing and fuzz-testing the exact predicates in milestone 1 before any
operation that relies on them.

**To reverse:** every stored coordinate would have to be reinterpreted — this is the decision
`spatial-model.md` warned cannot be retrofitted.

## Sources

- [Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates — Shewchuk](https://people.eecs.berkeley.edu/~jrs/papers/robustr.pdf)
- [Floating origin](https://en.wikipedia.org/wiki/Floating_origin)
- [Emulating double precision on the GPU to render large worlds — Godot](https://godotengine.org/article/emulating-double-precision-gpu-render-large-worlds/)
```

- [ ] **Step 5: Verify numbering and status lines**

Run: `grep -n '^\*\*Status:\*\*' docs/architecture/decisions/000*.md`
Expected: 0001 and 0002 `accepted`; 0003 `superseded by [ADR-0004](0004-build-our-own-kernel-in-dynlex.md)`; 0004, 0005, 0006 `accepted`.

- [ ] **Step 6: Commit**

```bash
git add docs/architecture/decisions
git commit -m "Record the kernel decisions in ADR-0004, 0005 and 0006

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Amend the spatial model for f64 local coordinates

**Files:**
- Modify: `docs/domain/spatial-model.md` (status line, the "Three coordinate frames" table, the rendering paragraph)
- Modify: `docs/domain/capability-inventory.md` (the "Tiled coordinate architecture" row)

- [ ] **Step 1: Amend the status line**

In `docs/domain/spatial-model.md` replace

```
**Status:** first pass — phase 1. Added after the requirement that the tool also behave as a
tile-based, GIS-like database supporting effectively unbounded coordinates.
```

with

```
**Status:** first pass — phase 1, amended 2026-09-09 by
[ADR-0006](../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md): local
coordinates are 64-bit, not 32-bit. Added after the requirement that the tool also behave as a
tile-based, GIS-like database supporting effectively unbounded coordinates.
```

- [ ] **Step 2: Amend the frames table**

Replace the row

```
| **Local coordinates** | 32-bit, relative to tile origin | Everything geometric |
```

with

```
| **Local coordinates** | 64-bit, relative to tile origin | Everything geometric; 32-bit only at GPU upload, camera-relative |
```

and replace the sentence

```
Geometry is authored, stored and evaluated in **local** coordinates only. A tile a few hundred
metres across keeps float32 precision far below a millimetre. Extent becomes unbounded because
tiles are unbounded in number, not because any single coordinate is large.
```

with

```
Geometry is authored, stored and evaluated in **local** coordinates only, in 64-bit floating
point (ADR-0006). Tiles remain the precision strategy for *rendering* — a tile a few hundred
metres across keeps the camera-relative float32 the GPU receives far below a millimetre — and
the paging strategy for the model. Extent becomes unbounded because tiles are unbounded in
number, not because any single coordinate is large.
```

- [ ] **Step 3: Amend the capability inventory row**

In `docs/domain/capability-inventory.md` replace

```
| **Tiled coordinate architecture** | core | M | 🔴 | 64-bit tile origins, float32 local coordinates. The minimum viable version is one tile and is cheap |
```

with

```
| **Tiled coordinate architecture** | core | M | 🔴 | 64-bit tile origins, 64-bit local coordinates, float32 only at GPU upload (ADR-0006). The minimum viable version is one tile and is cheap |
```

- [ ] **Step 4: Verify no float32-local claims remain**

Run: `grep -n "32-bit, relative\|float32 local" docs/domain/*.md; echo "exit=$?"`
Expected: no output, `exit=1`.

- [ ] **Step 5: Commit**

```bash
git add docs/domain/spatial-model.md docs/domain/capability-inventory.md
git commit -m "Amend the spatial model to 64-bit local coordinates

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Rewrite the repository entry documents and add the sub-project briefs

**Files:**
- Rewrite: `README.md`
- Rewrite: `CLAUDE.md`
- Rewrite: `CONTRIBUTING.md`
- Create: `ui/README.md`
- Create: `ifc/README.md`
- Modify: `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md:4` (status)

- [ ] **Step 1: Rewrite README.md**

Replace the whole file with:

```markdown
# open-bim-studio

A BIM modeller that combines the capabilities of a professional BIM authoring tool (3D
modelling, parametric components, coordinated 2D drawings, IFC exchange) with the immediacy of a
real-time 3D application. Written in [DynLex](https://github.com/OpenAEC-Foundation/dynlex).

## Structure

```
kernel/   geometry kernel — B-rep, mesh, point cloud, implicit; exact predicates; f64   (in progress)
ui/       Vulkan-based UI and viewport library                                          (brief only)
ifc/      IFC/STEP read-write library                                                   (brief only)
docs/     vision, domain knowledge, decisions, specs; research-phase archive
scripts/  build.sh and test.sh, which locate the pinned DynLex compiler
```

## Building and testing

Requires a DynLex checkout at `../dynlex` (or `$DYNLEX_ROOT`) at the commit in
`metadata/DYNLEX_COMMIT`, built with its own `scripts/build.sh`. Then, from this directory in
Bash:

```bash
./scripts/build.sh
./scripts/test.sh
```

## Where to start

| If you want to… | Read |
|---|---|
| Understand the goal | [`docs/vision/vision.md`](docs/vision/vision.md) |
| Understand the boundaries | [`docs/vision/non-goals.md`](docs/vision/non-goals.md) |
| See what the product must do | [`docs/domain/capability-inventory.md`](docs/domain/capability-inventory.md) |
| See the kernel design | [`docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`](docs/superpowers/specs/2026-09-09-geometry-kernel-design.md) |
| See the decisions | [`docs/architecture/decisions/`](docs/architecture/decisions/) |
| Work in the kernel | [`kernel/README.md`](kernel/README.md) |
| Read the research that preceded this | [`docs/archive/`](docs/archive/) |

## Status

Kernel milestone 0 complete: repository restarted, DynLex pinned, first module and test in
place. Milestone 1 (numerics, exact predicates, handles) is next; see §9 of the kernel design.
```

- [ ] **Step 2: Rewrite CLAUDE.md**

Replace the whole file with:

```markdown
# CLAUDE.md — instructions for AI agents working in this repository

## What this repository is

The build repository for a BIM modeller written in DynLex. It holds three libraries — `kernel/`,
`ui/`, `ifc/` — and later the application. Read `README.md`, then the spec for the part you are
working on in `docs/superpowers/specs/`, then the ADRs in `docs/architecture/decisions/`.

## Language

**All repository content is in English** — documents, file names, commit messages, code and
comments (ADR-0002). Conversations with maintainers are typically in Dutch; that does not change
what gets written to disk. Dutch domain terms without an accurate English equivalent are kept in
Dutch and explained in `docs/vision/glossary.md`.

## Naming rules — this repository has an explicit exception

The maintainer's global instructions prohibit naming commercial software in repository content.
**That rule is scoped to competing calculation software** (geotechnical and structural analysis
packages) and remains fully in force here.

**BIM and 3D software may be named explicitly**: OpenCascade, Blender, AutoCAD, Revit, Archicad,
Rhino, FreeCAD, Godot and similar tools are legitimate points of comparison. The exception does
not extend to calculation packages, client names, project names, or customer data.

## Conversation history

`PROMPTS.md` logs originating prompts from maintainers only. Never add assistant responses,
transcripts, paraphrased conversations or session dumps anywhere — not in `PROMPTS.md`, not in
commit messages. Commit messages describe changes, never the conversation that produced them.

## DynLex

The compiler lives in a sibling checkout (`../dynlex` or `$DYNLEX_ROOT`) at the commit pinned in
`metadata/DYNLEX_COMMIT`. `scripts/build.sh` and `scripts/test.sh` locate it; run them from the
repository root in Bash.

- Kernel code follows the DynLex conventions: `.dl` files, 4-space indentation, `local` for
  private definitions, result values with an error message instead of exceptions, tests as a
  directory with `main.dl` and `expected.txt`.
- Imports are written from the repository root (`import kernel/core/core.dl`); the standard
  library is `import lib/std.dl`.
- **Compiler defects are never worked around.** Minimise to a single file without
  `import lib/std.dl`, root-cause in the dynlex repository following its `AGENTS.md`, report,
  and fix there. Updating `metadata/DYNLEX_COMMIT` is a deliberate, separate commit.
- Extending DynLex (threading, allocation, intrinsics) is in scope when a milestone needs it;
  see §8 of the kernel design.

## Decisions

Settled decisions are ADRs in `docs/architecture/decisions/`. Once an ADR is `accepted`, do not
contradict it elsewhere; to change it, write a new ADR that supersedes it. ADR-0003 is
superseded by ADR-0004.

## Milestones

The kernel design (§9) fixes milestones M0–M8 in order. A milestone starts only when the
previous one passes its tests. Performance targets (§10) are measured and recorded, never
adjusted silently.

## What not to do

- Do not commit large binaries. Reference models go in `reference/` with acquisition
  instructions; see `reference/README.md` and `.gitignore`.
- Do not edit anything under `docs/archive/`.
- Do not add a representation, a conversion, or an operation that is not in the kernel design
  without updating the design first.
- Do not fill stubs with plausible prose. An honest "not started" is more useful than filler.
```

- [ ] **Step 3: Rewrite CONTRIBUTING.md**

Replace the whole file with:

```markdown
# Contributing

This is a build repository. Contributions are code with tests, and decisions with reasoning.

## Where things go

| You have… | Put it in |
|---|---|
| Kernel code | `kernel/<module>/` with a test in `kernel/<module>/tests/<name>/` |
| A cross-module kernel test or a reference-model regression | `kernel/tests/<name>/` |
| A benchmark | `kernel/benchmarks/`, results committed as a table |
| A settled decision | `docs/architecture/decisions/` as an ADR, numbered sequentially |
| A design for a new part | `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` |
| A specification, schema or reference model | `reference/` (binaries are gitignored — see its README) |
| Domain knowledge (IFC, drawings, standards) | `docs/domain/` |

## Tests

A test is a directory containing `main.dl` and `expected.txt`. `scripts/test.sh` compiles and
runs every test and compares standard output with `expected.txt`. Write the test before the
implementation; a test that never failed proves nothing.

Numeric tests compare against independently computed values and state the tolerance. Property
tests (volume conservation, Euler characteristic, round-trip identity) are preferred over
example tests for geometric operations.

## Commits

Small, one change each, messages in English describing the change. Never describe the
conversation that produced the change.

## Writing an ADR

Use `docs/architecture/decisions/_template.md`. Record the rejected options properly; they are
what stops a decision being reopened by the next person who has the same idea.
```

- [ ] **Step 4: Write the sub-project briefs**

Create `ui/README.md`:

```markdown
# UI library — brief

Not started. This directory will hold the Vulkan-based UI and viewport library written in
DynLex, built on `kernel/`.

Its brief, from the kernel design (§3): it owns windows, swapchains, input, draw shaders,
materials and widgets. It uploads the buffers the kernel produces and dispatches the compute
kernels the kernel provides. It never reimplements geometry.

Its design spec will live in `docs/superpowers/specs/` and is written after kernel milestone 2,
when there are kernel buffers to display.
```

Create `ifc/README.md`:

```markdown
# IFC library — brief

Not started. This directory will hold the IFC/STEP read-write library written in DynLex, built
on `kernel/`.

Its brief, from the kernel design (§3) and `docs/domain/capability-inventory.md`: read IFC2x3
and IFC4 from day one, export target decided deliberately; map IFC geometry representations to
kernel representations (B-rep for swept solids and boundary representations, mesh for
triangulated face sets); carry georeferencing (`IfcMapConversion`, `IfcProjectedCRS`) to and
from the kernel's tile frames.

Its design spec will live in `docs/superpowers/specs/` and is written after kernel milestone 4,
when there is a B-rep to map to.
```

- [ ] **Step 5: Mark the kernel spec accepted**

In `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` replace line 4

```
**Status:** draft for review
```

with

```
**Status:** accepted 2026-09-09; M0 implemented by `../plans/2026-09-09-m0-repository-restart.md`
```

- [ ] **Step 6: Verify no document outside the archive still describes this as a research repository**

Run: `grep -rn "research repository\|no product code\|Preparation repository" --include=*.md . | grep -v "^./docs/archive/" | grep -v "^./docs/superpowers/" | grep -v "^./docs/architecture/decisions/000[34]"; echo "exit=$?"`
Expected: no output, `exit=1`. (The spec, the plan and ADR-0003/0004 legitimately describe the former state.)

- [ ] **Step 7: Run the full verification**

Run: `./scripts/build.sh && ./scripts/test.sh && git status --short`
Expected: `1 library file(s) compile.`, `1 passed, 0 failed`, and `git status` listing only the files of this task.

- [ ] **Step 8: Commit**

```bash
git add README.md CLAUDE.md CONTRIBUTING.md ui/README.md ifc/README.md docs/superpowers/specs/2026-09-09-geometry-kernel-design.md
git commit -m "Rewrite the entry documents for the build repository and add sub-project briefs

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Verification of the whole milestone

From a clean checkout with `../dynlex` built at the pinned commit:

```bash
./scripts/build.sh && ./scripts/test.sh
```

Expected: `1 library file(s) compile.` and `1 passed, 0 failed`. Then:

```bash
ls docs && grep -n '^\*\*Status:\*\*' docs/architecture/decisions/000*.md && git log --oneline -7
```

Expected: `docs` lists `archive architecture domain superpowers ux vision`; ADR statuses as in Task 4 Step 5; six commits from Tasks 1–6 on top of the spec commit `cdd3745`.
