# ADR-0012 — Product code uses only `kernel/api`

**Status:** accepted
**Date:** 2026-10-31 (decided in #13, recorded here)
**Deciders:** the maintainer

## Context

[ADR-0008](0008-compile-units-with-c-abi-seams.md) compiles the kernel as its own unit behind a
C-ABI seam; `build.sh kernel` builds `kernel/api/exposed.dl` into `libobskernel.a` (#13, seam steps
1 and 2). A seam only holds if the code above it does not reach past it.

## Decision

Product code outside `kernel/` calls the kernel only through `kernel/api`. Tests may import
`kernel/brep` and the other kernel internals directly. `scripts/check-layers.sh` is the place to
enforce this.

## Options considered

### Only `kernel/api` for product code, internals for tests (chosen)
Keeps the seam real while letting tests probe the kernel.

### No rule
Every direct import of a kernel internal would have to be undone before the kernel can be built
and versioned on its own.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| The seam builds and round-trips a mesh on Linux | #13, seam step 2: `mesh_round_trip` PASS | measured |
| The rule was decided in the issue | #13 | claimed (issue comment) |

## Consequences

**What this makes easier:** the kernel can be compiled, timed and versioned as a separate unit.

**What this makes harder:** every new kernel capability product code needs must be exposed in
`kernel/api` first.

**What this commits us to:** a check in `scripts/check-layers.sh` for imports of kernel internals
from product code.

**What we would have to change to reverse it:** a new ADR; ADR-0008's seam would no longer be a
boundary.
