# Roadmap

Every step ends in a concrete artefact. "We thought about it" is not an artefact.

**Rewritten 31 October 2026** on the maintainer's decision ([`open-questions.md`](open-questions.md),
round 1, A4 and A5). The repository began as research that would hand over a build brief; since
October the native application is built here (ADR-0007, ADR-0008, the module split of 28 October).
The research phases 0–3 are kept below as closed history. From here the roadmap continues in
epics, modules and releases, and the build brief is no longer the endpoint.

## Research phases (history)

| Phase | Content | Artefact | Status |
|---|---|---|---|
| **0** | Skeleton, repository rules, vision, non-goals, glossary | A repository others can work in | **done** |
| **1** | Domain knowledge and prior art | `domain/capability-inventory.md` | **closed** 2026-10-31 — two items kept (the IFC data model with #66, BIM Basis ILS), the rest dropped |
| **2** | Kernel research against the weighting matrix | [`research/kernels/synthesis.md`](research/kernels/synthesis.md) | **done** (2026-09-12) |
| **3** | Spikes: measure the shortlist on the benchmark set | `FINDINGS.md` per spike — R-01, R-16, R-17, R-18, R-19 and four result sets | **done** (2026-09-12) |
| 4–6 | Freeze, build brief, kernel milestones M0–M8 | — | **replaced** by the product roadmap below |

## Product roadmap

### The MVP: the structural plan, end to end

The first end-to-end target is the **structural plan**: grid, levels, columns, beams, walls and
floors, tags, a sheet, and IFC export — drawn from the model and IfcX-based throughout. It
replaces the earlier "thin vertical slice" (one wall type, one opening, one storey, …): the
architectural risk still lives in the chain parametric → geometry → 2D → IFC, and the structural
plan exercises that whole chain on the drawing the maintainer needs first.

Its design is [`superpowers/specs/2026-10-30-structural-plan-design.md`](superpowers/specs/2026-10-30-structural-plan-design.md)
(PR #81, step 0 merged in PR #83). Acceptance is the design's §3 plus a comparison with one real
structural drawing that the maintainer supplies and that stays outside this repository.

### Epics

| Epic | Scope | Plan | Status |
|---|---|---|---|
| Views, grids, levels, georeferencing | [#67](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/67) | [plan](superpowers/plans/2026-10-29-views-grids-levels-plan.md) | blocking questions answered except the KW/FB codings (parked); building on computer 2 |
| Module split | [#13](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/13) | `superpowers/plans/2026-10-28-module-split-plan.md` | phase C2 merged; next extension point is `tools` |
| Building systems | [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22), #30 | — | regeneration in place approved; eight handles before vertices |
| Steel connections | [#6](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/6), #77 | — | recipes as schema plus DynLex code; review against Bouwen met Staal and SCI |
| Large models | [#76](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/76) | — | measure first, then the LOD slice |
| Compiler upstream | — | [`notes/dynlex-upstream.md`](notes/dynlex-upstream.md) | stay on the pin until four patches are upstream |

### Modules

Each module has an owner in [`OWNERS.md`](OWNERS.md); claims are made per module in issues, and the
[work board](WERKBORD.md) keeps only code reservations and handovers.

### Releases

From the next release: version numbers `YYYY.W.N` set by the release workflow (development builds
also show the short commit), and signed installers for Linux (`.asc`) and Windows (Authenticode) as
a hard condition (#3, #29, #39).

### Architecture still open

- **ADR-0004** (own kernel in DynLex) is still `proposed`, so ADR-0003 formally stays in force. The
  product track runs ahead of that decision; it is round 2, question 1 in
  [`open-questions.md`](open-questions.md).
- The browser goal (R-08) and designing for streaming (R-14) were decided as directions on
  31 October; their scope is still open (round 2).

## Phase 1 — domain and prior art

Turn "does what a professional BIM tool does" into something countable. Without this the scope
stays infinite and phase 4 cannot happen.

- [x] Capability inventory, classified and weighted, with the structural-decision list
- [x] Prior-art notes: Revit, SketchUp, Blender, Bonsai, Rhino/Grasshopper, Onshape
- [x] Prior-art synthesis
- [x] Parametric components: reference model and the two-path authoring position
- [x] Spatial model: georeferencing, tiling and precision
- [x] **Decided 2026-10-31: design for both** unbounded extent and streaming, so the data model
      does not rule streaming out (R-14)
- ~~Prior art: Archicad, FreeCAD, Speckle~~ — dropped 2026-10-31
- ~~Prior art: geospatial tiling approaches — 3D Tiles and comparable formats~~ — dropped 2026-10-31
- [ ] IFC data model written down at the depth we actually need — kept, with #66
- ~~Honest scoping of the 2D drawing subsystem (R-05)~~ — dropped 2026-10-31; the structural plan
      is now the scoping exercise
- [ ] Dutch standards, starting with what BIM Basis ILS requires of an authoring tool — kept

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
two" assumed the answer would be a choice between kernels. It was not: **of the seventeen candidates
carrying a kernel-role verdict, sixteen cannot supply the kernel**, and the seventeenth — `cadkernel`, the
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

## Phase 4 — freeze (history)

ADR-0005, ADR-0006, ADR-0007 and ADR-0008 were accepted in this phase, and ADR-0009 to ADR-0013 on
31 October 2026. ADR-0004 stays `proposed` with its three conditions. The MVP slice the phase was
to specify is now the structural plan (above).

## Phase 5 — the build brief (dropped)

[`BUILD-BRIEF.md`](BUILD-BRIEF.md) was to hand the research over to a build elsewhere. The build
moved here instead, so the brief is no longer the endpoint; it stays as a record.
