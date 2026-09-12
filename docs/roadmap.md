# Roadmap

Every phase ends in a concrete artefact. "We thought about it" is not an artefact.

Phases 2 and 3 overlap and are the natural point to divide work between contributors.

| Phase | Content | Artefact | Status |
|---|---|---|---|
| **0** | Skeleton, repository rules, vision, non-goals, glossary | A repository others can work in | **done** |
| **1** | Domain knowledge and prior art: what must this do, what do existing tools get right | `domain/capability-inventory.md` | **in progress** |
| **2** | Kernel research against the weighting matrix (layers 1, 2, 3) | [`research/kernels/synthesis.md`](research/kernels/synthesis.md) — completed matrix, twenty-one candidates, three-axis verdicts | **done** (2026-09-12) |
| **3** | Spikes: measure the shortlist on the benchmark set | `FINDINGS.md` per spike — R-01, R-16, R-17, R-18, R-19, plus the point-cloud, tessellation, object-count and topological-naming result sets | **done** (2026-09-12) |
| **4** | Freeze architecture, accept ADRs, specify the MVP slice | ADR set + MVP specification | **in progress** — ADR-0005 and ADR-0006 accepted; **ADR-0004 amended and still `proposed`** with three named conditions, so ADR-0003 stays in force and the kernel spec stays a working hypothesis. The MVP slice is not yet specified |
| **5** | Consolidate into the handover document | `BUILD-BRIEF.md` | |
| **6** | Kernel build milestones M0–M8 | working kernel | blocked on phase 4 |

## Phase 1 — domain and prior art

Turn "does what a professional BIM tool does" into something countable. Without this the scope
stays infinite and phase 4 cannot happen.

- [x] Capability inventory, classified and weighted, with the structural-decision list
- [x] Prior-art notes: Revit, SketchUp, Blender, Bonsai, Rhino/Grasshopper, Onshape
- [x] Prior-art synthesis
- [x] Parametric components: reference model and the two-path authoring position
- [x] Spatial model: georeferencing, tiling and precision
- [ ] **Decide: unbounded extent only, or streaming too?** Separable, and the second is an order
      of magnitude more work. Blocks R-14
- [ ] Prior art: Archicad, FreeCAD, Speckle
- [ ] Prior art: geospatial tiling approaches — 3D Tiles and comparable formats
- [ ] IFC data model written down at the depth we actually need
- [ ] Honest scoping of the 2D drawing subsystem (R-05)
- [ ] Dutch standards, starting with what BIM Basis ILS requires of an authoring tool

### What phase 1 has established so far

The premise survives in a **weakened and more useful form**. BIM modelling is slow for three
separable reasons — inherent semantic cost, data-model debt, and interface debt — and only the
last two are addressable. Expect meaningfully faster, not game-engine fast.

The encouraging finding: the mechanisms that make low-friction tools fast (inference-based
snapping, verb-first modal commands, in-gesture numeric input, instant undo) are **orthogonal to
semantics** and can be adopted without giving up the data model. That is the project's
load-bearing claim, and the evidence supports it.

The second round added the finding with the largest architectural consequence, and it came from
mechanical CAD rather than BIM: **the topological naming problem** (R-13). Anything referring to
derived geometry stores a name for the output of a computation, and re-evaluation may destroy it.
Three decades of mechanical CAD have not solved it. The available answer — references point at
*semantic* entities rather than derived topology — is only available to a domain-specific
modeller, and only if the data model is built for it from the start.

It also located the differentiator precisely: **gestural parameterisation as the primary path for
component authoring, with a computational graph as a deliberately-entered escape hatch.** Every
existing tool makes authoring a separate world, including the visual-programming ones — because
visual programming removes syntax, and syntax was never the hard part.

New requirements tracked: R-12 (the model must stay fast without curation), R-13 (topological
naming), and R-01 confirmed as *the* critical risk rather than one of several.

See [`research/prior-art/synthesis.md`](research/prior-art/synthesis.md).

## Phase 2 — kernel research

The decisive phase. Method and criteria are fixed in
[`research/kernels/README.md`](research/kernels/README.md) **before** candidates are evaluated,
so this stays an evaluation rather than an exchange of preferences.

Note that layer 3 (host vs. standalone) can proceed in parallel with layers 1 and 2 — they are
independent decisions.

Revised 2026-09-09: the question now includes what each kernel teaches a kernel of our own.
Method: `research/kernels/README.md`. Order of work:
`superpowers/plans/2026-09-09-kernel-research-programme.md`.

**Closed 2026-09-12 — and the artefact is not the one this table originally named.** "A shortlist of
two" assumed the answer would be a choice between kernels. It was not: **fourteen of the fifteen
kernel-scale candidates are a `no` on the *build on* axis**, and the fifteenth — `cadkernel`, the
MPL-2.0 B-rep crate under Open CAD Studio — is a *conditional shortlist for one arm*, priced rather
than chosen. What the phase produced instead is [`research/kernels/synthesis.md`](research/kernels/synthesis.md):
the completed matrix over twenty-one candidates, a verdict per candidate on all three axes, the
*borrow from* harvest grouped by the kernel spec section each design lands in, and the list of spec
claims the evidence contradicted. That is a more useful artefact than a shortlist, and saying so is
not the same as pretending the original one was delivered.

## Phase 3 — spikes

Documentation claims do not survive contact with measurement often enough to be trusted. Every
critical risk in [`risks.md`](risks.md) has a spike with a pass/fail criterion written in
advance.

No conclusions without measurements.

**Closed 2026-09-12.** Five cross-candidate `FINDINGS.md` files were produced, each applying a
pass/fail criterion quoted verbatim from [`risks.md`](risks.md): R-16 (boolean robustness, five
candidates, fifteen candidate × setting combinations), R-17 (precision at 500 km, five candidates),
R-01 (incremental evaluation, two IFC implementations), R-18 (DynLex compile scale — **failed**) and
R-19 (DynLex runtime performance — passes, conditionally). Result sets without their own FINDINGS
exist for the point-cloud scale, tessellation, object-count and topological-naming spikes. Four
spikes named in `risks.md` were **not** run and stay open: R-02 (the geometry seam), R-04 (renderer
scale), R-14 (cross-tile evaluation) and R-20 (the DynLex GPU path) — four spike directories that do
not exist under [`../spikes/`](../spikes/).

## Phase 4 — freeze

Architecture recorded, decisions accepted as ADRs, MVP slice specified.

**In progress since 2026-09-12.** Two of the three kernel ADRs are accepted — ADR-0005 (four equal
representations) and ADR-0006 (f64 local coordinates, exact predicates, explicit tolerance).
**ADR-0004 (build our own kernel, in DynLex) is amended and still `proposed`**: R-18 failed, R-19
passes only with an explicit `-O` flag, the DynLex compiler cannot emit a GPU compute entry point,
and one candidate turned out to be a live option rather than a disqualified one. Its three
acceptance conditions are written into the ADR. Until they are met **ADR-0003 remains in force**,
the kernel design spec stays a working hypothesis, and phase 6's M0 does not start.

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
