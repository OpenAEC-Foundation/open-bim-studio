# ADR-0008 — Compile the application as units joined by C-ABI seams

**Status:** accepted
**Date:** 2026-10-27
**Deciders:** the maintainer

## Context

The application is one DynLex program of about 102,000 lines compiled as a
single unit (180 files in the import closure of `main.dl`). The compiler's cost
grows superlinearly with unit size: R-18 measured 20k lines in 72 s and 50k in
1,147 s (exponent about 3); the application took 40 to 51 minutes at `-O2`, a
headless test 3 to 18 minutes, and one test peaked at 9.6 GB of compiler memory
(dynlex issue 13, fixed on the fork since 2026-10-16). The compiler is
single-threaded, so a single unit cannot use more than one core. Files are
already small (two above 5,000 lines); splitting files changes nothing while
the import closure is compiled as one unit.

## Decision

The application is compiled as several units joined by C-ABI seams. A unit is
a definition-only DynLex library compiled once with `--emit-object --no-main`
into a static library; its `exposed function` declarations are its C ABI, and
the programs that use it import a generated client of natural-language
wrappers over `@intrinsic("call", …)`, exactly as the platform shim is called
today. Units compile as separate compiler processes, so a build uses several
cores and no process needs the memory of the whole program. The kernel is the
first unit (design §6); formats and model follow in later designs.

The seam carries scalars and pointers only: plain-data records by pointer,
lists as pointer and count, bodies as opaque handles held in a managed wrapper,
result records through caller-provided storage with their class definitions
shared as source. Vector arithmetic and other small, hot code stays
source-shared and is compiled into every unit.

## Options considered

### Option A — wait for a DynLex module system with typed interfaces
The only route to units of a few thousand lines, because it would let the
compiler cache the frontend per module. Not available: the fork's
`--incremental` mode reuses native partitions, not frontend work. Requested
upstream; not waited for.

### Option B — units with C-ABI seams — chosen
Works with the compiler as it is (`--emit-object`, `exposed`, verified by the
fork's `scripts/test_object_output.py`). Costs: no inlining across a seam, a
generated client with the compiler's symbol mangling, and seams that must be
coarse.

### Option C — split files only
Rejected: the compiler compiles the import closure, so file boundaries do not
change the unit.

## Evidence

- R-18 (`docs/risks.md`), dynlex issue 13, `docs/notes/findings.md` for the
  measured compile times.
- `--emit-object --no-main` and `exposed function`: fork commit `f54f8475`,
  test `scripts/test_object_output.py`, documented in the fork's README.
- The measured kernel surface the application uses: design §3 (161 patterns,
  of which about twenty are heavy operations).

## Consequences

**What this makes easier:** a change to application code compiles without the
kernel; tests link a prebuilt kernel; builds run in parallel; the kernel's API
becomes explicit.

**What this makes harder:** cross-seam calls cost a real call; the seam has to
be designed (batched, handle-based); the generated client must track the
compiler's mangling until the fork offers a manifest or a symbol clause.

**What this commits us to:** the layout of design §5 (`kernel/`, `model/`,
`formats/`, `graphics/`, `editor/`, `app/`, `automation/`, `content/`), the
import direction checked by `scripts/check-layers.sh`, and measurements
before and after each unit is cut (design §11).

**What we would have to change to reverse it:** import the kernel sources
again instead of the generated client; the layout stays useful either way.

## Sources

- `docs/superpowers/specs/2026-10-27-restructuring-design.md`
- `docs/superpowers/plans/2026-10-27-restructuring-stage-0-1.md`
- DynLex fork: `README.md` (object output), `docs/stages.md` (callable ABI),
  issue 7 (extensions wish-list), issue 13 (inference memory)
