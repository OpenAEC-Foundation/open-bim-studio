# Kernels — evaluation method, candidates, and what each one teaches

**Decision question: which kernels do we build on, borrow from, or build ourselves — and if we
build, what must our design take from each existing kernel, and what must it avoid?**

**Status:** method revised 2026-09-09. The working hypothesis changed from "build on an existing
kernel" ([ADR-0003](../../architecture/decisions/0003-build-on-an-existing-kernel.md), still in
force) to "build our own multi-representation kernel in DynLex"
([spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md), proposed
[ADR-0004](../../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md)). **Neither is
settled.** This directory produces the evidence that accepts one and supersedes the other.

**Closed 2026-09-12.** The evidence is in, assembled in [`synthesis.md`](synthesis.md), and it
decided two of the three ADRs: **ADR-0005 and ADR-0006 are accepted**; **ADR-0004 is amended and
stays `proposed`**, with three named acceptance conditions; and **ADR-0003 therefore remains in
force and is not superseded.** The method below is unchanged and is what produced that outcome —
including the rule that kept ADR-0004 proposed.

---

## Post-evaluation evidence

- [NVIDIA USD BRep](../brep/usd-brep.md), source review of a fixed October 2026
  commit for #156: schema, included SMLib kernel and CPU tessellation. This
  supplements the exchange prior art and does not revise the closed matrix.

## The rule

No architecture decision is accepted until its evidence table (see the ADR template) points, for
every claim, at a section of a note in this directory or at a `FINDINGS.md` in `spikes/`. A
claim without a pointer is an opinion, and opinions do not accept ADRs.

The reverse also holds: a note that does not feed a decision is not research, it is reading.
Every note names the decision it serves.

## Three verdicts, not one

A candidate note used to end in *recommend / reject / shortlist*. With "build our own" on the
table, each candidate is judged on three separate questions, and the verdict answers all three:

| Verdict axis | Question | Feeds |
|---|---|---|
| **Build on** | Could this be the kernel, or a layer of it, for the product? | ADR-0003 vs ADR-0004 |
| **Borrow from** | Which of its designs, algorithms and data structures should our kernel adopt — with citation? | the kernel spec, per section |
| **Avoid** | Which of its documented problems come from its design, and how does our design not repeat them? | [`problems.md`](problems.md), ADR-0005/0006 |

"Borrow from" and "avoid" are the parts that make this research useful even when "build on" is
answered no. They are also the parts that turn "we build our own" from ambition into a design
with a paper trail.

## Weighting matrix

Every candidate is scored on every axis. Unknowns are recorded as unknown, never skipped.

| Criterion | Why it matters | Weight |
|---|---|---|
| **License** | Determines whether open-sourcing later is possible, and whether *borrowing* code (not just ideas) is possible | High |
| **Representations held natively** | B-rep, mesh, point cloud, implicit, and which conversions exist between them — the kernel spec's central bet | High |
| **Boolean robustness** | Documented failure modes on coplanar, touching and degenerate input; whether the algorithm is exact, tolerant, or heuristic | **Critical** |
| **Tolerance and precision model** | Internal precision; whether tolerances are per-entity, global, or absent; how they accumulate through operations. float32-only is disqualifying for *build on* | **Critical** |
| **Incremental evaluation** | Can one changed element be re-evaluated without reprocessing the model? | **Critical** (build on) |
| **Threading model** | What runs in parallel, what is locked, what is single-threaded by design | High |
| **GPU path** | How geometry reaches the GPU (tessellation, buffer layout, instancing, culling, picking) and how results come back | High |
| **IFC coverage** | Schema versions; round-trip loss; how geometry representations map | High (IFC candidates) |
| **Performance** | Measured on the benchmark set: load, boolean, tessellation, pick at 10k / 100k / 1M | High |
| **Embeddability** | Bindings, WASM, native, in-process use from DynLex | Medium (build on) |
| **2D derivation** | Section, projection, hidden-line | Medium |
| **Maturity** | Community, release cadence, bus factor, issue-tracker health | Medium |
| **AI familiarity** | Public code and documentation volume; one column, never a tiebreaker (R-09) | Medium |

### On boolean robustness and the tolerance model

These are weighted critical because they are where geometry kernels fail in practice and where
the failures are hardest to diagnose afterwards. The research must go past "booleans sometimes
fail" to *why*: exact arithmetic vs. floating filters, tolerant modelling vs. exact topology,
which inputs trigger which failure, and which design choice each failure traces back to. Issue
trackers are primary sources here; so is the source code at a pinned commit.

## Benchmark set

Fixed once in [`../../../reference/`](../../../reference/), used by every candidate. Extended
for the kernel questions:

1. **A realistic IFC model** from an open test set.
2. **Synthetic scale tests** at 10k / 100k / 1M elements.
3. **A parametric change that forces re-evaluation** — move a wall; openings, junctions and 2D
   views must follow.
4. **A boolean torture set** — coplanar faces, shared edges, touching vertices, near-degenerate
   triangles, a wall with many openings; each case with a known correct volume so
   V(A∪B) + V(A∩B) = V(A) + V(B) can be checked.
5. **A precision set** — the same geometry placed at the origin and at 500 km from it; results
   must agree to the stated tolerance.

Cases 4 and 5 are the ones that separate "works on the demo" from "works on a building".

## Candidates

Grouped by the representation they are strongest in. A candidate may appear in two groups.

**Every box below is ticked: each candidate has a note in this directory, and each note carries a
verdict on all three axes.** [`synthesis.md`](synthesis.md) §1 is the completed matrix and §2 the
three-axis verdict table, with each row linking the note's own `§Verdict`. A tick means *evaluated
and decided*, never *recommended* — of the seventeen candidates carrying a kernel-role verdict,
sixteen cannot supply the kernel and the seventeenth is a conditional shortlist for one arm.
[`synthesis.md`](synthesis.md) §6.3 enumerates which candidate falls where and on whose words.

### A — B-rep kernels
- [x] **OCCT** (Open CASCADE Technology) — tolerant B-rep, the kernel under FreeCAD and
      IfcOpenShell; the richest source of documented boolean and tolerance problems
- [x] **FreeCAD** as a case study on OCCT — the topological naming problem in production (R-13)
- [x] **Truck** and **Fornjot** — small B-rep kernels in Rust; useful for design clarity
- [x] **cadkernel**, the geometry under **Open CAD Studio** — a third Rust B-rep kernel, MPL-2.0
      and separable from its GPL application; f64 with a local-frame invariant, a typed boolean
      refusal, and provenance that writes untouched source records back unchanged
      ([`opencadstudio.md`](opencadstudio.md))
- [x] **Parasolid-class commercial kernels** — documentation-only reference for what "engineering
      accuracy" is taken to mean in industry; not a candidate to build on

### B — Mesh and boolean libraries
- [x] **Blender** — BMesh, the exact boolean (and the earlier Carve/BMesh booleans it replaced —
      a root-cause case), geometry-nodes evaluation, the GPU module
- [x] **Manifold** — fast, robust mesh booleans on manifold input; its constraints are the point
- [x] **CGAL** — exact predicates and constructions, Nef polyhedra, polygon mesh processing;
      the reference for what exactness costs
- [x] **libigl** — mesh arrangements and booleans; the research lineage behind Blender's exact
      boolean
- [x] **OpenMesh** — half-edge data structure design reference

### C — Point cloud and implicit
- [x] **PCL**, **Open3D**, **PDAL** — point cloud storage, indexing, filtering, normal estimation
- [x] **Potree** — out-of-core octree LOD for 10⁸–10⁹ points; the paging design reference
- [x] **OpenVDB** — sparse volumes and signed distance fields; the implicit-representation reference
- [x] **libfive** — implicit modelling with dual contouring / manifold contouring

### D — IFC and the GPU path
- [x] **IfcOpenShell** — IFC parsing and geometry through OCCT, and its CGAL-based kernel option
- [x] **web-ifc / That Open Engine** (That Open Company) — IFC parsing and geometry written for
      the browser; a different set of trade-offs from IfcOpenShell
- [x] **xBIM** — a third IFC implementation for disagreement analysis
- [x] **GPU paths**: Blender's GPU module and Vulkan backend, OCCT's visualisation layer, wgpu /
      bevy, Filament, That Open's three.js-based viewer, and the DynLex graphics runtime itself —
      evaluated in [`../renderers/`](../renderers/), summarised here for the kernel's buffer
      layout decisions

## Questions every candidate note must answer

1. Can it re-evaluate a single changed element without reprocessing the model?
2. What exactly happens to geometry on an IFC round trip? (IFC candidates)
3. Can it be driven in-process from DynLex, without a subprocess or a file?
4. What is its threading model, and what is single-threaded by design?
5. What breaks first at scale — memory, load time, or evaluation time?
6. What numeric precision does it use internally, and can it be configured?
7. Can it operate on a subset of the model — one tile, one region? (R-14)
8. Who maintains it, and what happens to us if they stop?
9. **What are its documented failure modes**, with issue links, and **what design choice does
   each trace back to?** This is the section [`problems.md`](problems.md) is built from.
10. **Which representations does it hold natively, and how does it convert between them?**
11. **How does geometry reach the GPU and come back?**
12. **What would we take into our own kernel, and what would we avoid?** With citations.

## Traceability

- Every note records the **version or commit hash** of the source it read, and links to files
  and line ranges at that commit, not at `main`.
- Every claim is labelled **claimed / measured / inferred / source / unknown** and carries a URL,
  an issue number, a paper, or a `spikes/<name>/FINDINGS.md`. **source** means read directly in the
  pinned source at the commit the note records — including an *absence* established by a stated
  grep rule — as distinct from **claimed**, which is what documentation or a third party says.
  **unknown** means the claim is not established by any note or spike and is recorded as an open
  item rather than a filled cell.
- Every note names the **decision it serves** (an ADR number or a spec section) in its header.
- [`problems.md`](problems.md) is the cross-cutting index: problem → root cause → which
  candidates → evidence. It is updated by every note, not written once.
- ADRs cite notes by file and section. An ADR whose evidence table has an empty cell stays
  `proposed`.

## Output of this directory

**[`synthesis.md`](synthesis.md)** — written 2026-09-12, and the single place all four outputs below
now live:

1. The completed matrix, one row per candidate, every cell labelled — [`synthesis.md`](synthesis.md) §1.
2. [`problems.md`](problems.md) complete for every candidate — P-01 … P-31 and N-01 … N-04, with no
   row left a bare `hypothesis`.
3. A verdict per candidate on all three axes — [`synthesis.md`](synthesis.md) §2, each row linking
   the note's own `§Verdict`.
4. Evidence tables filled for ADR-0004, 0005 and 0006 — [`synthesis.md`](synthesis.md) §6.
   **ADR-0005 and ADR-0006 accepted; ADR-0004 amended and kept `proposed`; ADR-0003 reaffirmed, not
   superseded.**

[`synthesis.md`](synthesis.md) §3 additionally carries the *borrow from* harvest grouped by the spec
section each design lands in, §4 the spec sections the evidence contradicted and the amendment made
to each, and §5 what is still unmeasured.

The order of work, the spikes, and their pass/fail criteria are in
[`../../superpowers/plans/2026-09-09-kernel-research-programme.md`](../../superpowers/plans/2026-09-09-kernel-research-programme.md).
