# M0 — Repository Restart and Kernel Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Blocked until** ADR-0004, 0005 and 0006 are `accepted` by Task 16 of `2026-09-09-kernel-research-programme.md`. If ADR-0004 is withdrawn there, this plan is retired. Revised 2026-09-09: research documents are no longer archived (the research phase continues); the ADRs are written as `proposed` by the research programme and only *accepted* here.

**Goal:** Turn this research repository into a build repository whose `scripts/test.sh` compiles and runs a first DynLex kernel test against a pinned DynLex compiler, with the accepted kernel decisions in force.

**Architecture:** Milestone 0 of `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`. Research, vision, domain and UX documents stay where they are; the superseded layered hypothesis is marked as such. The accepted ADRs are verified; `kernel/` gets its first module and test; `scripts/` locates the DynLex compiler from a sibling checkout pinned by commit hash.

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
docs/architecture/layers.md            status line: superseded hypothesis, points at the kernel spec
docs/roadmap.md                        phase 4 done, phase 6 (kernel milestones) in progress
docs/architecture/decisions/0003-build-on-an-existing-kernel.md   already superseded by Task 16 of the research programme — verified only
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

### Task 3: Mark the superseded hypothesis and advance the roadmap

**Files:**
- Modify: `docs/architecture/layers.md` (status line)
- Modify: `docs/roadmap.md` (phase table)

- [ ] **Step 1: Mark layers.md**

Directly under the title of `docs/architecture/layers.md` insert:

```markdown
**Status (2026-09-09):** superseded hypothesis. This document described building on existing
kernels under ADR-0003. The research programme (`../research/kernels/synthesis.md`) led to
ADR-0004; the current architecture is `../superpowers/specs/2026-09-09-geometry-kernel-design.md`.
Kept for the reasoning; do not update.
```

- [ ] **Step 2: Advance the roadmap**

In `docs/roadmap.md` set phase 4 to `**done**` (ADRs accepted in the research programme's Task 16) and the phase 6 row (kernel milestones) to `**in progress — M0**`.

- [ ] **Step 3: Verify and commit**

Run: `head -5 docs/architecture/layers.md && grep -n "in progress — M0" docs/roadmap.md`
Expected: the status paragraph, and one matching roadmap line.

```bash
git add docs/architecture/layers.md docs/roadmap.md
git commit -m "Mark the layered hypothesis superseded and advance the roadmap to M0

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Verify the accepted decision records

The ADRs were written as `proposed` and accepted by Task 16 of the research programme. This task only verifies the state M0 depends on.

**Files:**
- Read: `docs/architecture/decisions/0003-build-on-an-existing-kernel.md`, `0004-build-our-own-kernel-in-dynlex.md`, `0005-multi-representation-kernel.md`, `0006-f64-local-coordinates-in-tile-frames.md`

- [ ] **Step 1: Verify statuses**

Run: `grep -n '^\*\*Status:\*\*' docs/architecture/decisions/000*.md`
Expected: 0001 and 0002 `accepted`; 0003 `superseded by [ADR-0004](0004-build-our-own-kernel-in-dynlex.md)`; 0004, 0005, 0006 `accepted`. If any differs, stop: M0 is not unblocked.

- [ ] **Step 2: Verify the evidence tables are complete**

Run: `grep -n '^| .* | .* | *|$' docs/architecture/decisions/000[456]*.md; echo "exit=$?"`
Expected: no output, `exit=1` (no empty evidence-type cell). No commit — nothing changes in this task.

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
docs/     vision, domain knowledge, research notes and spikes findings, decisions, specs
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
| Read the research behind the decisions | [`docs/research/`](docs/research/) — start with `kernels/synthesis.md` and `kernels/problems.md` |

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
- Do not change a research note's verdict or an ADR's evidence table without a new measurement or source; decisions stay traceable to what was actually shown.
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

- [ ] **Step 5: Mark the kernel spec as in implementation**

The research programme's Task 16 already set the spec's status paragraph to `accepted <date>` (or amended it). Append to that status paragraph:

```
M0 implemented by `../plans/2026-09-09-m0-repository-restart.md`.
```

Do not touch the rest of the paragraph; it records what the acceptance rested on.

- [ ] **Step 6: Verify no entry document still describes this as a research-only repository**

Run: `grep -n "research repository\|no product code\|Preparation repository" README.md CLAUDE.md CONTRIBUTING.md; echo "exit=$?"`
Expected: no output, `exit=1`. (Research notes, the spec, the plans and the ADRs legitimately describe the former state.)

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

Expected: `docs` lists `architecture domain kernel-design.html research superpowers ux vision` plus `roadmap.md`, `risks.md`, `BUILD-BRIEF.md`; ADR statuses as in Task 4 Step 1; five commits from Tasks 1, 2, 3, 5 and 6 on top of the research programme's final commit.
