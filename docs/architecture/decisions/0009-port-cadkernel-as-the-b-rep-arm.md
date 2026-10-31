# ADR-0009 — Use the DynLex port of `cadkernel` as the B-rep arm

**Status:** accepted
**Date:** 2026-10-31
**Deciders:** the maintainer

## Context

[ADR-0004](0004-build-our-own-kernel-in-dynlex.md) leaves the B-rep arm of the kernel open between
three routes: written ourselves, ported from `cadkernel` (Option D) or linked to `cadkernel` behind a
C-ABI shim (Option E). It requires Options D and E to be recorded in their own ADR before M1,
because both change the licence position: MPL-2.0 is file-level copyleft (`problems.md` P-14).

In practice the choice was already made. [ADR-0007](0007-kernel-source-lives-in-this-repository.md)
seeded `kernel/` on 2026-10-27 from the DynLex port of `cadkernel` at `c2d32bea` plus this
repository's overlay, and `kernel/LICENSE` is MPL-2.0. This ADR records that choice; it does not
make a new one.

## Decision

The B-rep arm is the DynLex port of `cadkernel` (Option D), maintained in `kernel/`.

- Every file derived from `cadkernel` stays under MPL-2.0, file by file, with its SPDX header.
- Files written new in this repository that are not derived from `cadkernel` may carry another
  licence. The repository has no root `LICENSE` file yet and most source files carry an MPL-2.0
  SPDX header; which licence new, non-derived files carry is an open question in
  [`open-questions.md`](../../open-questions.md), and until it is answered they keep MPL-2.0.
- Rewriting parts of the port (for exact predicates or speed) is ordinary maintenance under this
  ADR. A rewritten file that still derives from a `cadkernel` file stays MPL-2.0.

This ADR does not accept [ADR-0004](0004-build-our-own-kernel-in-dynlex.md); its three conditions
remain as written.

## Options considered

### Option D — port `cadkernel` to DynLex (chosen)
Already done: the port exists, the application builds on it, and it leaves no foreign-function
seam and no second toolchain. The licence cost is file-level copyleft on the derived files, which
is compatible with an open-source product.

### Option E — link `cadkernel` in Rust behind a C-ABI shim
Keeps the kernel's upstream maintenance, but adds a Rust toolchain to the build and a seam on the
hottest path. ADR-0004 keeps it as the fallback if R-18 cannot be fixed; this ADR does not remove
that fallback.

### Writing the B-rep arm ourselves
The cleanest licence position, but it discards a working kernel for years of work the research
priced in [`research/kernels/synthesis.md`](../../research/kernels/synthesis.md).

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| `kernel/` is seeded from the port at `c2d32bea` | [ADR-0007](0007-kernel-source-lives-in-this-repository.md) § Decision | measured (the repository) |
| `kernel/` is MPL-2.0 | `kernel/LICENSE` | measured (the repository) |
| MPL-2.0 is file-level copyleft | `problems.md` P-14; [MPL-2.0 FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) | claimed |

## Consequences

**What this makes easier:** M1 is no longer blocked on the B-rep route; licence headers have one
rule.

**What this makes harder:** every file must say whether it derives from `cadkernel`; a new file
copied from a derived one inherits MPL-2.0.

**What this commits us to:** keeping SPDX headers accurate, and the licence check that
accompanies every PR adding a dependency (R-11, decision of 31 October 2026).

**What we would have to change to reverse it:** a new ADR choosing Option E or a rewrite, and
replacing every derived file.
