# ADR-0014 — Choose CPU or GPU per call by problem size

**Status:** accepted
**Date:** 2026-11-05
**Deciders:** the maintainer

## Context

[ADR-0004](0004-build-our-own-kernel-in-dynlex.md) condition 2 asked for the GPU compute gap to be
decided one way or the other: a DynLex `GLCompute` path, or CPU threads for good. On 31 October the
maintainer chose neither side alone but the best combination per operation; on 5 November they chose
how ([`open-questions.md`](../../open-questions.md), round 2, question 2).

The work in question is computation, not rendering (rendering is already Vulkan): tessellation,
booleans, point clouds, clash checks and the parametric evaluation of large systems. Compute dispatch
and float64 exist only on this repository's DynLex pin (DynLex PR #8); upstream has the `GLCompute`
entry point only ([`notes/dynlex-upstream.md`](../../notes/dynlex-upstream.md)).

## Decision

- Every operation that has a GPU path also has a CPU path, its **CPU twin**. The CPU twin is the
  reference: it is written first and it is what tests compare against.
- Which path runs is chosen **per call, by problem size**: small inputs run on the CPU, large ones
  on the GPU, above a threshold per operation. Without a usable GPU, everything runs on the CPU.
- Topological decisions (inside/outside, orientation, coincidence) stay on exact predicates
  ([ADR-0006](0006-f64-local-coordinates-in-tile-frames.md)). A GPU path may compute candidates or
  approximate values, but the result it hands back must equal the CPU twin's within the explicit
  tolerance of ADR-0006.

## Options considered

### Per call, by problem size, with a CPU twin (chosen)
Uses each machine fully and degrades to CPU-only machines and the browser
([ADR-0015](0015-the-browser-is-a-long-term-goal.md)) without a separate code path.

### CPU first; a GPU path only after a measured gain
Cheaper, because no operation is written twice until it has to be; rejected by the maintainer in
favour of using the GPU wherever the problem is large enough.

### A fixed table per operation
Clear, but a fixed choice is wrong at one end of the size range for most operations.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| The pin has compute dispatch and float64, upstream has `GLCompute` only | [`notes/dynlex-upstream.md`](../../notes/dynlex-upstream.md) | claimed (source reading) |
| GPU paths for the kernel are argued, not measured | [R-20](../../risks.md) | claimed |

## Consequences

**What this makes easier:** each operation works everywhere; the GPU is an accelerator, never a
requirement.

**What this makes harder:** every GPU operation is written and tested twice, and the two must agree.
The thresholds have to be measured per operation and per class of hardware.

**What this commits us to:** an equality test between the CPU twin and the GPU path for every GPU
operation, and a recorded threshold per operation, measured, not guessed.

**What we would have to change to reverse it:** a new ADR; GPU-only operations would lose their
fallback.
