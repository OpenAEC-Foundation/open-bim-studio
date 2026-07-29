# Roadmap

Every phase ends in a concrete artefact. "We thought about it" is not an artefact.

Phases 2 and 3 overlap and are the natural point to divide work between contributors.

| Phase | Content | Artefact | Status |
|---|---|---|---|
| **0** | Skeleton, repository rules, vision, non-goals, glossary | A repository others can work in | **done** |
| **1** | Domain knowledge and prior art: what must this do, what do existing tools get right | `domain/capability-inventory.md` | next |
| **2** | Kernel research against the weighting matrix (layers 1, 2, 3) | Completed matrix, shortlist of two | |
| **3** | Spikes: measure the shortlist on the benchmark set | `FINDINGS.md` per spike | |
| **4** | Freeze architecture, accept ADRs, specify the MVP slice | ADR set + MVP specification | |
| **5** | Consolidate into the handover document | `BUILD-BRIEF.md` | |

## Phase 1 — domain and prior art

Turn "does what a professional BIM tool does" into something countable. Without this the scope
stays infinite and phase 4 cannot happen.

- Capability inventory, prioritised
- Prior-art notes, focused on *why* tools succeed or fail rather than what features they list
- IFC data model written down at the depth we actually need
- Honest scoping of the 2D drawing subsystem (see R-05)

## Phase 2 — kernel research

The decisive phase. Method and criteria are fixed in
[`research/kernels/README.md`](research/kernels/README.md) **before** candidates are evaluated,
so this stays an evaluation rather than an exchange of preferences.

Note that layer 3 (host vs. standalone) can proceed in parallel with layers 1 and 2 — they are
independent decisions.

## Phase 3 — spikes

Documentation claims do not survive contact with measurement often enough to be trusted. Every
critical risk in [`risks.md`](risks.md) has a spike with a pass/fail criterion written in
advance.

No conclusions without measurements.

## Phase 4 — freeze

Architecture recorded, decisions accepted as ADRs, MVP slice specified.

**MVP scope direction** (to be confirmed, not assumed): a **thin vertical slice through the
entire chain** — one wall type, one opening, one storey, one plan, one section, one parametric
component, one IFC export.

The architectural risk lives in the *chain* — parametric → geometry → 2D → IFC, with changes
propagating — not in breadth. Once that chain holds, broaden into architectural elements (walls,
floors, roofs, doors, windows, spaces), where IFC support is most mature and the visible result
is most convincing.

## Phase 5 — the build brief

Consolidate everything into [`BUILD-BRIEF.md`](BUILD-BRIEF.md).

**Acceptance test:** hand it to a fresh AI session with no other context. If it cannot produce a
coherent implementation plan, the brief is not finished.

## After phase 5

The build itself, which is out of scope for this repository as currently constituted. If it
happens here, phase 5 is where the repository changes character and this document gets rewritten.
