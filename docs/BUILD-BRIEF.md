# Build brief

**The endpoint of this repository.** Everything else exists to fill this document in.

## Status: empty — phase 5 artefact

This is a placeholder with a defined shape. Do not fill sections speculatively; each one is
completed from settled research and accepted ADRs, not from expectation.

## What this document is for

A single handover package, complete enough that a developer or AI agent with **no other
context** can produce a coherent implementation plan from it.

That is the literal acceptance test: hand it to a fresh session and see what comes back. If the
result is incoherent or full of questions, the brief is not finished — and the gaps it exposes
are exactly the research that was skipped.

## Required sections

### 1. What we are building
One page. The product, its users, its scope boundary. Sourced from
[`vision/vision.md`](vision/vision.md) and [`vision/non-goals.md`](vision/non-goals.md).

### 2. Technology decisions
Every choice, with its reasoning and the options rejected. Sourced from the ADRs in
[`architecture/decisions/`](architecture/decisions/).

The rejected options matter as much as the chosen ones — without them, an implementer will
rediscover and re-argue decisions we already settled.

### 3. Architecture
Layers, components, data flow, and the boundaries between them. Sourced from
[`architecture/`](architecture/).

### 4. Data model
The semantic model, its relationship to IFC, and how parametric evaluation works. This is where
most implementation questions will originate.

### 5. The MVP slice
Precisely what the first working version does, end to end. Specific enough to build from and to
test against.

### 6. Interaction model
How this is meant to feel and the concrete rules that produce it. Sourced from
[`ux/interaction-model.md`](ux/interaction-model.md).

Without this section the result will be functionally correct and feel like every other BIM tool
— which would defeat the purpose of the project.

### 7. Known risks and open questions
What we could not settle in advance, and what we chose to defer. Honesty here prevents an
implementer from assuming a solved problem.

### 8. Verification
How to know the result is correct: benchmark models, expected behaviours, exchange tests.

## Rules

- **Nothing enters this document that is not settled elsewhere.** This is a consolidation, not a
  place to make decisions.
- **Every decision carries its reasoning.** A brief of bare conclusions gets argued with.
- **Written for a reader with no context.** No references to conversations, no assumed shared
  understanding.
- **Do not assume the reader is an AI.** If the premise about AI capability does not hold
  (see R-10), this must still work for human developers.
