# ADR-0004 — Build our own geometry kernel in DynLex

**Status:** proposed
**Date:** 2026-09-09
**Reviewed:** 2026-09-12 — amended on the evidence and **kept `proposed`**. The three conditions
that would accept it are named in §Consequences, "What must be true before this ADR is accepted".
The reasoning is in [`docs/research/kernels/synthesis.md`](../../research/kernels/synthesis.md) §6.3.

## Context

ADR-0003 committed to building on an existing geometry kernel, on the premise that a kernel is
not a differentiator and that writing one is a multi-year project that consumes the whole
effort. That premise held while candidates remained unevaluated.

Two things changed. First, DynLex — the maintainer's own language — now exists as a target
capable, in principle, of compiling and running kernel-shaped code, which was not true when
ADR-0003 was written. Second, the research phase against the candidates in
`docs/research/kernels/` produced an early finding, not a final one: every candidate evaluated so
far imposes an assumption the product cannot accept without dropping a requirement — batch-only
conversion with no cheap re-evaluation of a single changed element, float32-only paths, a single
global coordinate origin, or a licence that blocks embedding or later open-sourcing (see
`docs/research/kernels/problems.md` P-05 batch re-evaluation, and P-06 origin and licence
constraints, as the recurring shapes of the disqualifying assumption).

`docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` records the resulting hypothesis in
full: a multi-representation kernel written in DynLex. This ADR proposes the first and largest
part of that hypothesis — building our own kernel at all, in DynLex specifically — as the
decision ADR-0003 already named as the reconsideration trigger: "writing our own is reconsidered
only if the research shows that no candidate can meet a requirement we are unwilling to drop."

This ADR stays `proposed` until the evidence table below is filled. Until then ADR-0003 remains
in force and no kernel code is written (spec §0, header).

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §6.3 — the evidence
table below is now filled, and it does not accept this ADR.** Two things changed against the
paragraph above.

**First, the "early finding" hardened into twenty-one evaluated candidates, and the claim it
supported is too strong.** Of the twenty-one, four carry no kernel-role verdict at all — FreeCAD (an
application, not scored), Parasolid / ACIS (a documentation-only reference), Potree (a converter and
a viewer) and the DynLex graphics runtime (the given). **Of the seventeen that remain, sixteen cannot
supply the kernel**: eleven are an unqualified *no* on the *build on* axis, three are a *no* for the
kernel with a *yes* for a role that is not the kernel, and two carry a build-on question their own
note leaves open and narrower than the kernel. The enumeration, with each verdict as its note words
it, is the first row of the evidence table below. **The seventeenth is not a no.** `cadkernel`, the MPL-2.0 B-rep
crate under Open CAD Studio, is a *conditional shortlist* for the B-rep arm
([`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Verdict (a)): f64
throughout, generational typed handles, a typed refusal, and an identity residual of exactly 0 on
every torture case that ran. What holds it back is cost and maturity — three of ten benchmark cases
produce nothing, it is 5–110× slower than the other candidates, single-threaded, one
representation, no exact predicates, 34 days old with no release, and its C ABI does not exist and
would be ours to write — not an assumption the product cannot accept. The claim is therefore
narrowed: *no candidate can supply the kernel; one candidate is a live, priced option for one of
its four arms.*

**Second, the DynLex half is contradicted by its own spike.** R-18 **failed**: 20k lines compile in
72.19 s against a 30 s pass line and 50k in 1146.72 s, with the implied exponent worsening from 1.89
to 3.03. R-19 passes at 1.12× / 1.23× / 1.01× **only with an explicit `-O` flag** — unflagged the
same workloads are 9.09× / 6.78× / 21.14×. And the compiler cannot emit a compute entry point at
all (`problems.md` P-28), which spec §6 item 4, §7 `gpu/` and §9 M7 assume it can.

That is why this ADR is amended rather than accepted, and why the fallback ADR-0003 names is still
the decision in force.

## Decision

We build our own geometry kernel, written in DynLex.

The kernel is a pure DynLex library (`kernel/`) with no dependency on an existing geometry
kernel. It is developed as its own sub-project with milestones M0–M8, ahead of the UI and IFC
libraries that depend on it, because it carries the largest unknowns: boolean robustness,
precision, and performance (spec §2).

## Options considered

### Option A — build on an existing kernel (ADR-0003)
The status quo. Concentrates effort on the areas that differentiate the product — interaction
model, evaluation, drawing pipeline — and avoids the multi-year risk of a from-scratch kernel.
Rejected as the sole path because every candidate evaluated so far forces a choice between the
product's requirements and the kernel's assumptions: a kernel that cannot cheaply re-evaluate one
changed element undermines the interaction thesis (R-01) at the root, not at the edges, and no
candidate offers f64-precision paths, multi-representation breadth and a compatible licence
together. Remains available as a fallback if the DynLex evidence in this ADR fails — that
fallback is the reason the research programme keeps evaluating candidates in parallel with the
spikes below, rather than stopping once this ADR is proposed.

**Amended 2026-09-12.** "No candidate offers f64-precision paths, multi-representation breadth and a
compatible licence together" survives; "every candidate forces a choice between the product's
requirements and the kernel's assumptions" does not, for one candidate. `cadkernel` is MPL-2.0
(links from a differently licensed product), f64 with zero f32 in the modelling path, and refuses
rather than answers wrongly. It is single-representation, which is why it could only ever fill one
of ADR-0005's four arms — and that possibility is now split out as Options D and E below, because a
rejected option has to be recorded as the specific thing it is, not folded into "the status quo".
This option, as written, remains the fallback in force while this ADR is `proposed`.

### Option B — write our own kernel in an established systems language
Rust, C++ or similar. Removes the language-maturity risk entirely: SIMD codegen, threading, and
memory-mapped I/O are solved problems in these ecosystems, and the kernel would not be blocked on
extending a compiler that has never carried a program this large. Rejected because it does not
serve the project's actual differentiator, which is that the whole stack — kernel, UI, IFC — is
written in one language the maintainer controls end to end, and because a systems-language kernel
still has to be bound into DynLex for the UI and app layers, reintroducing an FFI seam of exactly
the kind ADR-0003 already accepted as a cost of building on someone else's kernel. If the DynLex
evidence in this ADR fails outright — not merely falls short on one workload — this option is the
next one to evaluate, ahead of returning to Option A.

### Option C — write our own kernel in DynLex — chosen
Full control, one language across the stack, and a kernel design that can be shaped exactly to
the interaction model instead of adapted to one. Costs: DynLex has never compiled or run a
program at this scale, and the extensions in spec §8 (threading, memory-mapped allocation,
verified SIMD codegen) do not exist yet and must be built as part of the kernel effort. This is
the paper-thin line between "differentiator" and "the classic way ambitious modelling projects
fail" that ADR-0003 warned about — the evidence table below exists to keep that line honest rather
than assumed.

**Amended 2026-09-12.** The costs this option names are no longer estimates. "DynLex has never
compiled or run a program at this scale" is now measured in both directions: it **runs** kernel-shaped
code at 1.12× / 1.23× / 1.01× of C++ `-O2` with bit-identical output, and it **compiles** 20k lines in
72.19 s against a 30 s budget, with the cost scaling superlinearly and worsening. And the extension
list in spec §8 was incomplete: a SPIR-V compute entry point is missing from it and is assumed by
three other sections.

### Option D — port `cadkernel` from Rust to DynLex as the content of the first kernel milestones

**The maintainer's proposal, 2026-09-11.** Rather than writing the B-rep arm from a blank file, port
the MPL-2.0 Rust crate `cadkernel` into DynLex module by module, extending DynLex where the port
needs facilities the language lacks — so M1–M5 produce both a working B-rep arm and the compiler
work the kernel needs anyway.

**For.** The design is already close to the spec's, independently arrived at: generational typed
handles in an arena (spec §6's mechanism), f64 throughout with zero f32 in the modelling path
(ADR-0006), a translation-only local frame stated as a contract (spec §5), a scale-derived operation
tolerance, a typed refusal that names the class of input that defeated the operation (spec §12), and
provenance on every node that our spec does not have. It is small enough to read end to end — 336
commits, two contributors — and its API is `Result`-shaped throughout. Porting is also the cheapest
honest way to find DynLex's real gaps: a port has a reference implementation to diff against, so a
codegen or type-inference defect shows up as a wrong number rather than as a design argument. And
unlike Option E it leaves no FFI seam and no second toolchain.

**Against, and these are the reasons it is not adopted here:**

1. **Licence.** MPL-2.0 is *file-level* copyleft (`problems.md` **P-14**). A port is a derivative of
   the ported files, so those files stay MPL-2.0 and every modification to them must be published —
   in a kernel where those files are the B-rep arm, not a leaf. That is a real constraint on any
   later licence choice for the whole, and it must be decided deliberately rather than discovered.
2. **R-18 lands squarely on it.** A B-rep arm of this size is exactly the program R-18 measured:
   20k lines compile in **72.19 s** today and the exponent worsens above it. The port *is* the
   program the compile-scale result says cannot yet be built at an acceptable cost.
3. **It inherits the two designs ADR-0006 decides against.** cadkernel classifies by tolerance
   comparison and has **no exact predicates** (`robust` is listed as planned, not present), and it
   has no per-entity tolerance. A line-by-line port would import exactly the mechanism ADR-0006
   exists to replace, and then have to unpick it.
4. **It is one representation.** ADR-0005 needs four; the port supplies one arm and none of the
   mesh, point-cloud or implicit work.
5. **The measured profile is the slowest in the torture file** — `overlap_half` ∪ at 32.256 ms
   against 4.62 (OCCT), 3.21 (Blender Exact), 0.380 (CGAL) and 0.293 (Manifold) — and the note traces
   it to source: the imprint's face pairing is O(n·m) with an AABB reject and **no spatial index**.
   A port carries that scaling property across with the code.
6. **It is 34 days old at the pinned commit, with no tags and no crates.io release**, so what would
   be ported is a moving target with no stability contract.

**What would change the answer.** If R-18 is fixed and cadkernel gains lump/shell containment and
exact predicates upstream, a *selective* port — the topology arena, the provenance model, the typed
refusal, the tolerance formula, read as a reference rather than transliterated — becomes the
cheapest way to build the B-rep arm, and the licence question then applies only to the files actually
derived. That is a different proposal from a wholesale port and should be written as one.

### Option E — build on `cadkernel` behind a C-ABI shim

Keep the Rust crate as a linked dependency and reach it from DynLex through a C ABI we write.

**For.** MPL-2.0 permits linking from a differently licensed product with no obligation beyond the
MPL files themselves. It is the only *build on* candidate this research produced for the B-rep arm;
it is f64 throughout; its identity residual is exactly 0 on every case that ran; it kept the 1e-7 m
slab at its specified volume where OCCT degraded it at construction and Manifold deleted it
silently; and it is deterministic across ten runs where two other candidates are not. The API is
small enough to wrap: `combine`, `imprint`, the `make` constructors, `tessellate`, `validate`,
`lift`/`append`.

**Against.** There is **no** C-callable surface to build on — zero `extern "C"`, zero `#[no_mangle]`,
zero `#[repr(C)]`, no `cdylib` — so the shim and its maintenance are entirely ours, over an API five
weeks old. It refuses three of ten benchmark cases, and two of those refusals are in the constructor
rather than the boolean, so whether `combine` can cut a wall with twelve openings is
**unmeasurable** until lumps carry containment. It is single-threaded by design, has no spatial
index, no exact predicates and no per-entity tolerance. And it reintroduces precisely the FFI seam
Option C exists to remove, plus a second toolchain in the build.

**Both D and E are recorded as rejected-for-now rather than dismissed.** If the acceptance conditions
below are not met — in particular if R-18 cannot be fixed — Option E is the cheapest path to a
working B-rep arm and should be re-evaluated before Option B, because it is the only one whose
licence, precision model and refusal discipline this research has already checked.

## Evidence

> Every claim the decision rests on, with where it is shown. An ADR with an empty cell in this
> table stays `proposed`. Evidence type is **measured** (a `spikes/*/FINDINGS.md`), **claimed**
> (documentation or a third party, with URL) or **inferred** (reasoning shown in the note).

**Amended 2026-09-12.** Every row is now filled, three rows are added, and two rows carry **negative**
evidence. The first row's claim is narrowed to what the research supports; the rows marked ✗ are the
reason this ADR stays `proposed`.

| Claim | Where shown | Evidence type |
|---|---|---|
| **Sixteen of the seventeen candidates evaluated for the kernel role cannot supply the kernel**, enumerated rather than counted loosely. [`synthesis.md`](../../research/kernels/synthesis.md) §2 scores **twenty-one** candidates; four of those carry no kernel-role verdict — **FreeCAD** ("not scored — an application, never a candidate"), **Parasolid / ACIS** ("documentation-only reference, not a candidate"), **Potree** ("**Not applicable** — a converter and a viewer") and the **DynLex graphics runtime** ("**It is the given**"). The remaining seventeen: **eleven unqualified *no*** — **OCCT**, **Truck**, **Fornjot**, **Blender**, **libigl**, **OpenMesh**, **PCL**, **Open3D**, **libfive**, **web-ifc**, **xBIM** — for a GPL licence or a GPL boolean, float32 storage or float32 at the API boundary, no invalidation mechanism, no embeddable surface, an archived project, or library rather than kernel scope; **three *no* for the kernel with a *yes* for another role** — **Manifold** ("**No as a kernel; yes as a candidate boolean component**", and the note records it as **not taken**), **PDAL** ("**No as the module; genuinely yes as an ingest dependency**"), **IfcOpenShell** ("**Yes for parsing and representation mapping; qualified yes for geometry, and no as the evaluation layer**"); and **two whose build-on question the note leaves open rather than closed** — **CGAL**, no as the kernel and no as the boolean but "linking Epick as an LGPL library for its predicates … is a live option" against writing Shewchuk's predicates ourselves, and **OpenVDB**, no as a kernel but "could plausibly sit behind the kernel's `implicit` module … **Not answered here**". Neither open question is a candidate to supply the kernel; both are recorded so the count is not read as closing them | [`kernels/synthesis.md`](../../research/kernels/synthesis.md) §2, the *Build on* column, which links each note's own §Verdict; [`cgal.md`](../../research/kernels/cgal.md) §Build on and [`implicit.md`](../../research/kernels/implicit.md) §Build on for the two open questions: [`occt.md`](../../research/kernels/occt.md), [`blender.md`](../../research/kernels/blender.md), [`manifold.md`](../../research/kernels/manifold.md), [`cgal.md`](../../research/kernels/cgal.md), [`libigl-openmesh.md`](../../research/kernels/libigl-openmesh.md), [`implicit.md`](../../research/kernels/implicit.md), [`pointclouds.md`](../../research/kernels/pointclouds.md), [`truck-fornjot.md`](../../research/kernels/truck-fornjot.md), [`ifcopenshell.md`](../../research/kernels/ifcopenshell.md), [`web-ifc.md`](../../research/kernels/web-ifc.md), [`xbim.md`](../../research/kernels/xbim.md) | **measured** where a spike decided it (Blender's float32, web-ifc's float32 and broken invalidation, IfcOpenShell's missing dependency tracking), **source** for the absences (no `extern "C"`, no C ABI) and for PCL's float32 xyz — **PCL itself was never run**, and the 500 km f32 cost was measured on Open3D's f32 tensor, not on PCL ([`pointclouds.md`](../../research/kernels/pointclouds.md) §Measurements) — **claimed** for the licences |
| ✗ **The seventeenth candidate is not disqualified.** `cadkernel` is a *conditional shortlist* for the B-rep arm: MPL-2.0, f64 throughout, an identity residual of exactly 0 on every case that ran — held back by cost and maturity (3 of 10 cases produce nothing, 5–110× slower, single-threaded, one representation, no exact predicates, 34 days old, no C ABI), not by an assumption the product cannot accept | [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Verdict (a); [`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) §Added after assembly — cadkernel | **measured** — and it is why the row above says *sixteen of seventeen*, not *every*. Options D and E exist for it |
| ✗ **DynLex does not compile kernel-shaped code within the compile-time budget.** 20k lines take **72.19 s** against a 30 s pass line; 50k lines take **1146.72 s**; the implied exponent worsens from 1.89 (5k→20k) to **3.03** (20k→50k). Memory is not the problem (2.8 GB at 50k) and neither is correctness (zero diagnostics, every binary matched an independent computation) | [`spikes/dynlex-scale/FINDINGS.md`](../../../spikes/dynlex-scale/FINDINGS.md) (R-18) §Results, §Verdict, §What this means for ADR-0004 | **measured**, and **negative**. The findings' own words: "the ADR should not move to `Accepted` on this row until it is fixed and remeasured" |
| DynLex runs kernel-shaped code within 1.5× of C++ `-O2` — 1.12× (triangle/triangle), 1.23× (BVH build), 1.01× (orient3d), with **bit-identical output** in both languages at both optimisation levels | [`spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md) (R-19) §Results, §Verdict | **measured** |
| …**conditional on an explicit `-O` flag.** The compiler's default emitted-code level is `-O0`, verified in-repo by comparing a no-flag build against an explicit `-O0` build after neutralising the linker's embedded timestamp; unflagged the same workloads are 9.09× / 6.78× / 21.14× and would fail the criterion | [`spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md) §Method (Flags), §Verdict | **measured** |
| ✗ **DynLex cannot compile a GPU compute kernel at all**, which spec §6 item 4, §7 `gpu/` and §9 M7 assume it can: the shader stage is a two-member enum, the CLI accepts only `vertex` or `fragment`, and the runtime has zero `vkCmdDispatch`, zero compute pipelines and zero storage buffers | [`kernels/problems.md`](../../research/kernels/problems.md) **P-28**; [`research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The gap list, §Risks | **source** (an absence, established by a stated grep rule over a pinned commit) |
| The DynLex graphics runtime cannot draw the target scene either: a 32 MiB per-frame transient arena is the only path to the GPU, holding **25 890 twelve-triangle boxes**, so 10⁵ boxes fail rather than slow down | [`kernels/problems.md`](../../research/kernels/problems.md) **P-27**; [`research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The DynLex graphics runtime in detail | **source** + **inferred** (the arithmetic is shown; the failure was not observed) |
| Two language facilities the kernel will need are missing — no unsigned integers or logical right shift (`shift right` lowers to `ashr`), and scientific-notation float literals are rejected. Neither blocked a workload; both were worked around identically in both languages | [`spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md) §Language facilities that were missing | **measured** (runtime behaviour) + **source** (the lowering) |
| DynLex can be extended for threading and memory mapping — asserted, and **not** established by any spike. R-18 measured compile time and R-19 measured runtime; neither measured threading, SIMD or mapped allocation, and neither exists in the runtime today | [`spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md) §What this does not settle ("Nothing here is parallel or SIMD"); spec §8 | **unknown** — the original row pointed at a "`kernels/dynlex-readiness`" section that does not exist. Recorded as an open item rather than a filled cell |
| Per-object overhead is the cause of scale ceilings we must avoid: one moved object costs **16.3 ms at 10k objects and 332.1 ms at 100k** in Blender, at ≈63–65 kB per object, while the same 1.2 M triangles as one object cost 0.018 ms — so the quantity being counted is datablocks, not geometry | [`kernels/problems.md`](../../research/kernels/problems.md) **P-07**; [`kernels/blender.md`](../../research/kernels/blender.md) §Object-count ceiling (R-03, partial); [`spikes/blender-ceiling/results/blender.md`](../../../spikes/blender-ceiling/results/blender.md) | **measured** (headless; the viewport half of R-03 is unmeasured and a headless driver cannot measure it) |
| Generational handles in an arena are not a novel bet: a shipping B-rep kernel arrived at the same mechanism independently | [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §1, Topology | **source** |

## Consequences

**What this makes easier:** the kernel's data model can be built around handle-addressed,
per-object operations from the start, which is what R-01 (incremental evaluation) needs and no
evaluated candidate offers natively. The whole stack shares one language, one build, one test
convention, and one set of debugging tools.

**What this makes harder:** every capability an existing kernel gives for free — boolean
robustness accumulated over decades, a validated tessellation pipeline, a tolerance model that
has survived production use — has to be built and proven from nothing, on a compiler that itself
is unproven at this scale.

**What this commits us to:** a milestone sequence (spec §9) where later milestones cannot start
before earlier ones pass their exit criteria, DynLex compiler defects fixed in dynlex rather than
worked around in the kernel (spec §8, §12), and the performance targets of spec §10 measured and
recorded rather than assumed.

**What we would have to change to reverse it:** fall back to Option A, B, D or E above. Reversal
after M0 discards the kernel skeleton but not the research — `docs/research/kernels/` and
`problems.md` remain valid evidence for evaluating any replacement candidate.

## What must be true before this ADR is accepted

Added 2026-09-12. These are conditions, not aspirations: each names the measurement or the change
that closes it, and the ADR stays `proposed` until all three are met. Until then **ADR-0003 remains
in force**, the kernel spec stays a working hypothesis, and the M0 repository restart (spec §9, §13)
does not start.

1. **R-18 passes, on a clean compiler pin.** The compile-scale defect is root-caused and fixed in
   dynlex per its own procedure — a minimal reproducer first, not a workaround in the kernel — and
   the spike is re-run against the commit `metadata/DYNLEX_COMMIT` will pin, because the measured
   binary was built from a **dirty** tree whose six modified files are all in type inference, the
   phase this spike loads hardest. The cheap and most useful next step the findings name: separate
   whether the cost scales with pattern count, call-site count or lines, and whether it is per-file
   or whole-program — the second question decides whether separate compilation rescues the developer
   loop even if whole-program compilation stays slow. Tracked here as
   [R-18](../../risks.md); the fix itself belongs on the dynlex tracker, where
   [issue #7](https://github.com/OpenAEC-Foundation/dynlex/issues/7) is the place these findings are
   to be carried — its contents were not read into this repository and are not evidence here.
2. **The GPU compute gap is decided one way or the other, outside this repository's own tables.**
   Spec §8 already carries a `GLCompute` row against M7 and §6 item 4 already names the CPU-thread
   fallback — both added in the same commit as this amendment — so *writing the row down* cannot be
   the condition; it is already true, and a condition a document satisfies by describing itself is
   not a condition. What is testable is a commitment on one side or the other: **either** a dynlex
   change scoping the `GLCompute` entry point, workgroup builtins, storage buffers, barriers and a
   memory model exists on the dynlex tracker with an accepted scope and a target, **or** spec §6
   item 4 and §9 M7 are rewritten to run that work on CPU threads for good — not as a fallback —
   with §10's targets rechecked against CPU figures and the revised numbers written into §10's
   measured-reference column. Until one of those is done, the gap is recorded and undecided.
   **P-28**.
   *Direction of 31 October 2026:* the maintainer chose neither side alone but the best combination
   of CPU and GPU per operation ([`open-questions.md`](../../open-questions.md), round 1, A3). That
   keeps both sides of this condition live — a GPU path that must exist and a CPU path that must
   meet §10 on its own — and does not by itself meet the condition; how the choice per operation
   is made is round 2, question 2.
3. **The `-O` flag is demonstrated in a build that exists before M0, not asserted about a script M0
   creates.** The original wording made this circular: it required `scripts/build.sh` to pass the
   flag "at M0", while M0 itself does not start until this ADR is accepted. The testable form: R-19's
   three workloads are re-run through the exact build command the kernel will use, and the measured
   ratios land on the `-O2` figures (1.12× / 1.23× / 1.01×) rather than the unflagged ones
   (9.09× / 6.78× / 21.14×) — which demonstrates the flag is reaching the compiler. Spec §8 records
   the requirement; this condition is the check that it works. Any future performance measurement
   that omits the flag is treated as a false failure.

**A fourth thing that is not a condition but must be decided before M1:** whether the B-rep arm is
written, ported (Option D) or linked (Option E). The research priced all three and the decision is
not forced by this ADR — but taking Option D or E changes the licence position (MPL-2.0 file-level
copyleft, **P-14**) and must be recorded as its own ADR rather than absorbed here. *Recorded
31 October 2026:* Option D, in [ADR-0009](0009-port-cadkernel-as-the-b-rep-arm.md).

## Sources

- [DynLex design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Kernel research method](../../research/kernels/README.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
- [Kernel research synthesis](../../research/kernels/synthesis.md) — the assembled evidence, the
  three-axis verdict per candidate, and the reasoning behind keeping this ADR `proposed`
- [R-18 findings, DynLex compile scale](../../../spikes/dynlex-scale/FINDINGS.md)
- [R-19 findings, DynLex runtime performance](../../../spikes/dynlex-performance/FINDINGS.md)
- [R-01 findings, incremental evaluation](../../../spikes/incremental-evaluation/FINDINGS.md)
- [GPU paths across six engines, and the DynLex runtime's gap list](../../research/renderers/gpu-paths.md)
