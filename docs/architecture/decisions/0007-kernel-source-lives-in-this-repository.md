# ADR-0007 — Keep the kernel source in this repository

**Status:** accepted
**Date:** 2026-10-27
**Deciders:** the maintainer

## Context

By October 2026 the CAD kernel written in DynLex existed in four places: the
DynLex fork's `codex/cadkernel-port` branch (`lib/cadkernel`, 124 files, last
kernel commit 2026-09-24), the fork's `master` (`lib/bim`, a 63-file subset
extracted from PR 8 with small integration fixes, merged 2026-10-23 as PR 12),
this repository's overlay (`spikes/dynlex-bim-slice/overlay/lib/cadkernel`: 21
files overriding the port's with 42,870 differing lines and 6 files that exist
only here, plus the fast kernel and the Vulkan layer which exist only here),
and local checkouts. The application compiled the overlay over the port's tree,
assembled at build time by `build.sh`. Nobody could say which copy was the
kernel, and a change to it had to be made in one place and carried to another.
The restructuring design
(`docs/superpowers/specs/2026-10-27-restructuring-design.md`, §2 and §3)
records the measurements.

## Decision

The kernel source lives in this repository under `kernel/`, with its fixtures
(`kernel/tests/`), its reference material (`kernel/reference/`) and its notes
(`kernel/docs/`). The DynLex fork carries the compiler and the generic standard
library only. `kernel/` was seeded on 2026-10-27 from the port at `c2d32bea`
with this repository's overlay files replacing 21 of them and adding 6; the
fast kernel and the Vulkan layer were already this repository's. The kernel's
licence (MPL-2.0, file-level copyleft) travels with it as `kernel/LICENSE`.

## Options considered

### Option A — the kernel stays in the fork's `lib/`
One line to keep in sync with upstream DynLex, and the fork's test harness
runs it. Rejected: the application overrides a quarter of the files, so the
fork's copy was never what the application compiled; the fork's two lines
(`master` with `lib/bim`, the port with `lib/cadkernel`) had already diverged
from each other and from the overlay; and the overlay mechanism assembled a
tree at every build.

### Option B — the kernel lives here, the fork is the compiler — chosen
One authoritative tree beside the model that uses it, moved with `git mv` so
the overlay's history follows the files; the compiler is pinned by commit
(`.dynlex-root.local` or `DYNLEX_ROOT`) and finds its own `lib/` without any
staging. The cost: the fork's copies must be retired by agreement with its
other contributors, and kernel fixes are no longer shared with other DynLex
programs through the fork.

## Evidence

- Copies and their differences: design §3 (the copy table; `comm` and `diff`
  counts of 2026-10-27).
- Import resolution that makes staging unnecessary: the fork's
  `src/cpp/compiler/compiler.cpp`, `resolveImportPath` (importing file's
  directory, its root, the working directory, the compiler's source tree).
- The seed: this repository's commit "Move the application and kernel into
  unit directories" names the port commit and the overlay counts.

## Consequences

**What this makes easier:** one kernel tree to read, change and test; the
kernel seam of ADR-0008 can be cut inside this repository; no overlay, no
`rsync`, no patching of library files at build time.

**What this makes harder:** sharing kernel improvements with other DynLex
programs; the fork's `lib/cadkernel` and `lib/bim` become stale until retired.

**What this commits us to:** retiring the fork's copies (design §9), keeping
`lib/` here empty except for overrides tied to upstream pull requests, and
pinning the compiler by commit.

**What we would have to change to reverse it:** move `kernel/` back into the
fork's `lib/` and reinstate the overlay assembly in `build.sh`.

## Sources

- `docs/superpowers/specs/2026-10-27-restructuring-design.md`
- DynLex fork pull requests 8 (`codex/cadkernel-port` → `master`, open) and 12
  (`merge-pr8-pr11` → `master`, merged 2026-10-23)
- ADR-0004 (own kernel in DynLex, proposed), which already names `kernel/`
