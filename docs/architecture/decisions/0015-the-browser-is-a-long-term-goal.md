# ADR-0015 — The full application in the browser is a long-term goal

**Status:** accepted
**Date:** 2026-11-05
**Deciders:** the maintainer

## Context

[R-08](../../risks.md) asks for an explicit decision on browser support, recorded as an ADR,
because it constrains the whole stack. The application is native: Vulkan for rendering, GLFW for
windows and input, the C shim in `platform/`. On 31 October the maintainer set the full application
in the browser (WASM/WebGPU) as a goal; on 5 November they set how hard that goal is
([`open-questions.md`](../../open-questions.md), round 2, question 3).

The DynLex compiler can already emit WebAssembly (`--emit-wasm`), and `platform/web/run.mjs` runs
such a program under Node on the host of the DynLex web IDE.

## Decision

The full application in the browser is a **long-term goal, not a requirement for any release**.
Until it is planned, the code keeps the door open:

- Rendering stays behind the application's own layer, so a WebGPU backend can sit next to Vulkan.
- No operating-system code outside `platform/`.
- Nothing may assume a GPU is present for computation ([ADR-0014](0014-choose-cpu-or-gpu-per-call-by-problem-size.md)).
- What the browser needs from DynLex beyond `--emit-wasm` (threads, file access, a WebGPU binding)
  is tracked on the DynLex tracker when the goal is planned.

## Options considered

### Long-term goal, door kept open (chosen)
Costs little now and stops the native stack from closing the route.

### A requirement for version 1.0
Would put a WebGPU renderer and a full WASM host next to the MVP.

### A read-only IfcX viewer in the browser first
A smaller first step; not chosen, because the goal is the application, not a viewer.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| DynLex emits WebAssembly, and a compiled program runs under Node | `platform/web/run.mjs` | claimed (the repository; not run for this ADR) |
| The application is native (Vulkan, GLFW, C shim) | `viewer/vulkan/`, `platform/` | measured (the repository) |

## Consequences

**What this makes easier:** a later browser build does not require untangling OS calls from
product code.

**What this makes harder:** the render layer has to stay an abstraction even while it has one
backend.

**What this commits us to:** review of OS-specific code and direct Vulkan calls outside their layers.

**What we would have to change to reverse it:** nothing structural; dropping the goal only removes
the constraints above.
