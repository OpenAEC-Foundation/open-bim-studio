# Blender — BMesh, the exact boolean, and the object model

**Decision question:** Blender ships the most widely used open-source *exact* mesh boolean and the
most widely used open-source 3D application architecture. Can either be built on — and if not,
which of its designs must our kernel take, and which of its failure modes must it not repeat?

**Serves:** ADR-0004, ADR-0005, ADR-0006; kernel spec §4–§6; R-03; Task 11 (GPU paths)

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

> This note is about Blender **as a geometry kernel**. Blender's *interaction model* is a separate
> question with a separate verdict in
> [`../prior-art/blender.md`](../prior-art/blender.md), which recommends adopting its command
> grammar. Nothing below revises that. Keeping the two apart matters: rejecting Blender's object
> model says nothing about its interaction design, and vice versa.

---

## Summary

Blender ships a production implementation of the algorithm our kernel spec proposes — an
arrangement decided by exact rational predicates, from Zhou et al.'s *Mesh Arrangements for Solid
Geometry* — wrapped at both ends in **float32**, which is where its errors come from: at 500 km
from the origin our benchmark wall lost 0.15 m³ of volume and 3.5 cm of vertex position, which is
the float32 ULP at that distance and has nothing to do with the algorithm. It cannot be built on
for three independent reasons — GPL, float32 storage, and a per-object evaluation cost we measured
at 16.8 ms for **one** moved object in a 10k-object scene with no viewport at all — but it is the
richest source of design to borrow after OCCT, and the only candidate so far that shows what an
exact arrangement costs in practice (0.4–15.6 ms per boolean on the torture set). It also supplies
the sharpest single example of what a kernel must never do: its Exact solver returned a valid,
closed, manifold union of **one** cube when handed two cubes touching at a point, and said nothing.

## What it is

Blender is a GPL 3D creation suite, over thirty years old, maintained by the Blender Foundation
with a paid development team and a large contributor base. It is not a geometry kernel and does not
present itself as one; the parts relevant here are libraries inside it that happen to be as good as
anything published.

It holds **two mesh representations** and converts between them constantly. `Mesh` is the storage
form: structure-of-arrays attributes (`position` as `float3`, corner and edge index arrays), cheap
to copy and to upload. `BMesh` is the editing form: a non-manifold-tolerant half-edge structure
with radial loops, per-element allocated from pools, used by edit mode and by tools that need
topological queries. Volumes (OpenVDB), point clouds, curves and Grease Pencil exist as separate
datablock types. *Inferred from the source tree:* there is **no B-rep** and no solid modelling on
parametric surfaces — no package in the tree provides one.

**Three boolean solvers** ship in 5.0, all reachable from the same modifier through one enum:

| RNA value | Manual name | What it is |
|---|---|---|
| `EXACT` (default) | *Exact* | The mesh-arrangement algorithm with GMP rational arithmetic |
| `FLOAT` | *Fast* | The older BMesh intersection, floating-point with a distance threshold |
| `MANIFOLD` | *Manifold* | A binding to the external `manifold` library, added in 4.5 |

That three solvers coexist, each with its own failure envelope, is itself the finding: no single
one of them was good enough to replace the others.

**Maturity and licence.** *Claimed* by the project: "Blender as a whole is licensed under the GNU
General Public License, Version 3. Individual files may have a different but compatible license"
([`README.md`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/README.md#L32-L38));
the boolean and BMesh sources carry `SPDX-License-Identifier: GPL-2.0-or-later`. For this project
that is decisive and is discussed under §Verdict: ideas may be reimplemented, code may not be
copied into a differently-licensed kernel (R-11).

## What was read, and at which commit

Everything below is pinned to **tag `v5.0.0`, commit
[`a37564c4df7a9b604809e5192918400e46a0205f`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f)**.

The installed binary that produced every measurement reports `bpy.app.build_hash == a37564c4df7a`
and `bpy.app.version_string == 5.0.0`, so **the source read and the binary measured are the same
commit** — not merely the same release line. Obtained with
`git clone --depth 1 --branch v5.0.0 https://projects.blender.org/blender/blender.git`, hash
confirmed with `git rev-parse HEAD`.

| What | Path at the pinned commit |
|---|---|
| Exact boolean: patches, cells, winding numbers, PWN test, raycast fallback | [`source/blender/blenlib/intern/mesh_boolean.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc) (3756 lines) |
| The arrangement itself | [`source/blender/blenlib/intern/mesh_intersect.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_intersect.cc) (3145 lines), [`BLI_mesh_intersect.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_intersect.hh) |
| Exact-arithmetic types and predicates | [`BLI_math_mpq.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_math_mpq.hh), [`BLI_math_boolean.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_math_boolean.hh) |
| Boolean API and its stated contract | [`BLI_mesh_boolean.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_boolean.hh), [`GEO_mesh_boolean.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/GEO_mesh_boolean.hh) |
| Solver dispatch, float32→exact→float32 conversion, the Fast path | [`source/blender/geometry/intern/mesh_boolean.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc) |
| The Manifold-library binding and its error mapping | [`source/blender/geometry/intern/mesh_boolean_manifold.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean_manifold.cc) |
| The modifier: options, error reporting, fallback | [`source/blender/modifiers/intern/MOD_boolean.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/modifiers/intern/MOD_boolean.cc) |
| BMesh element structures and allocation | [`source/blender/bmesh/bmesh_class.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/bmesh_class.hh), [`bmesh/tools/bmesh_boolean.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/tools/bmesh_boolean.cc), [`bmesh_intersect.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/tools/bmesh_intersect.hh) |
| Mesh and Object storage precision | [`DNA_mesh_types.h`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_mesh_types.h#L251-L257), [`DNA_object_types.h`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_object_types.h#L396-L398) |
| Depsgraph node model and update flags | [`depsgraph/intern/node/deg_node.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/intern/node/deg_node.hh#L46-L110), [`DNA_ID.h#L1050-L1080`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_ID.h#L1050-L1080) |
| GPU module and its backends | [`source/blender/gpu/`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu) (`opengl/` 38, `vulkan/` 85, `metal/` 45, `intern/` 67 files), [`GPU_vertex_buffer.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_vertex_buffer.hh), [`GPU_select.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_select.hh) |
| Mesh → GPU buffer extraction | [`draw/intern/mesh_extractors/extract_mesh_vbo_pos.cc`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/mesh_extractors/extract_mesh_vbo_pos.cc#L73-L84) |
| Batch evaluation for nodes | [`functions/FN_multi_function.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/functions/FN_multi_function.hh#L9-L17), [`FN_lazy_function.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/functions/FN_lazy_function.hh) |
| Build-time optionality of both exact solvers | [`CMakeLists.txt#L345-L346`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/CMakeLists.txt#L345-L346) |

Documentation, pinned separately because it lives in other repositories:

| What | Where |
|---|---|
| Boolean modifier manual | [`manual/modeling/modifiers/generate/booleans.rst`](https://projects.blender.org/blender/blender-manual/src/commit/ce0478a5b9329738e2cde9b7cbc22dd93500a8b8/manual/modeling/modifiers/generate/booleans.rst) at `blender-manual` commit `ce0478a5b9329738e2cde9b7cbc22dd93500a8b8` (branch `blender-v5.0-release`), file blob `32d690352c65` |
| 2.91 release notes — the exact boolean's announcement | [`docs/release_notes/2.91/modeling.md`](https://projects.blender.org/blender/blender-developer-docs/src/commit/fb9a26df737598c4e538ba8f57daf66ba2151057/docs/release_notes/2.91/modeling.md) at `blender-developer-docs` commit `fb9a26df7375` |

## Evaluation

Scored against every criterion in [`README.md`](README.md).

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | **GPL.** The project as a whole is GPL-3.0; the boolean and BMesh files are `GPL-2.0-or-later`. Linking a GPL library into our kernel would make the kernel GPL. Designs may be reimplemented from the published paper and the documentation; **source may not be copied** (R-11). GMP, which the Exact solver requires, is itself copyleft — *claimed* by its project as dual LGPLv3+/GPLv2+, <https://gmplib.org/> — so the exact path carries a second copyleft dependency even if Blender's own code were avoided. | claimed | [`README.md#L32-L38`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/README.md#L32-L38); SPDX headers on the files listed above |
| **Representations held natively** | **Two mesh forms plus separate datablock types.** `Mesh` (structure-of-arrays attributes) and `BMesh` (radial-loop half-edge) with conversions in both directions, used constantly — the boolean modifier's own comment calls its round trip "utterly non-optimal, we may go from a bmesh to a mesh back to a bmesh" ([`MOD_boolean.cc#L547-L549`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/modifiers/intern/MOD_boolean.cc#L547-L549)). Volumes (OpenVDB), point clouds, curves are separate datablocks, not a common representation layer. **No B-rep, no NURBS solids.** | inferred from the source tree | package structure; [`DNA_mesh_types.h`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_mesh_types.h) |
| **Boolean robustness** | Measured on the torture set, per solver: **Exact 9/10 numerically correct, 8/10 topologically valid; Fast 7/10 and 5/10; Manifold 10/10 and 10/10.** The Exact solver's one wrong answer is `touching_vertex`, where it returned a valid closed manifold union of volume **1** instead of 2 — an operand silently deleted. The Fast solver is wrong on `overlap_half`, `identical` and `near_degenerate_triangle`, and is **non-deterministic** on `overlap_half` (2 distinct results in 10 identical runs). Algorithm class: exact-arrangement (Exact), floating with a distance threshold (Fast), external exact-ish library (Manifold). | measured | [`spikes/boolean-torture/results/blender.md`](../../../spikes/boolean-torture/results/blender.md) |
| **Tolerance and precision model** | **float32 storage, exact arithmetic in the middle, float32 out.** `Mesh` positions are `float3`, `BMesh` vertices are `float co[3]`, object transforms are `float4x4`. The Exact solver converts to `mpq_class` rationals for the arrangement and writes `double`→`float` back. There is no per-entity tolerance and no global epsilon; the Fast solver has one threshold (`double_threshold`, default 1e-6 m) and the Exact solver has none. **float32-only storage is disqualifying for *build on* by the README's own rule.** | measured + source | §Precision below; [`spikes/precision-set/results/blender.md`](../../../spikes/precision-set/results/blender.md) |
| **Incremental evaluation** | **Present — the only candidate read so far that has one** — and still too coarse. The depsgraph tracks relations per *datablock component* (`TRANSFORM`, `GEOMETRY`, `PARAMETERS`, …), tags with `ID_RECALC_*` flags, and re-evaluates only tagged operation nodes. But the granularity is one object = one ID, so cost scales with object count: measured **16.8 ms for one `view_layer.update()` after moving a single object** in a 10k-object scene, against **0.013 ms** for the same triangles in one object. | measured + source | [`deg_node.hh#L46-L110`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/intern/node/deg_node.hh#L46-L110); [`spikes/blender-ceiling/results/blender.md`](../../../spikes/blender-ceiling/results/blender.md) |
| **Threading model** | Parallel by default and pervasive, via TBB behind `threading::parallel_for`: the arrangement, the PWN check ([`mesh_boolean.cc#L1362`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L1362)), the raycast fallback and the float32→rational conversion all run threaded. The price is visible on the tracker and in our own numbers: non-determinism. Blender's own developers confirm a threading non-determinism in the Manifold solver ([#143644](https://projects.blender.org/blender/blender/issues/143644)); we measured one in the Fast solver. | measured + source | §Known problems; Probe E in [`results/blender.md`](../../../spikes/boolean-torture/results/blender.md) |
| **GPU path** | Full backend abstraction (`opengl/`, `vulkan/`, `metal/`, `dummy/`) behind `VertBuf` / `IndexBuf` / `Batch`. Mesh data is turned into buffers by 30 single-purpose extractors; positions upload as `SFLOAT_32_32_32` **per face corner**, not per vertex. Nothing comes back except selection: `GPUSelectResult` is `{id, depth}`. See §GPU. | inferred from source | [`extract_mesh_vbo_pos.cc#L73-L84`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/mesh_extractors/extract_mesh_vbo_pos.cc#L73-L84), [`GPU_select.hh#L29-L42`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_select.hh#L29-L42) |
| **IFC coverage** | None. IFC reaches Blender only through the Bonsai add-on, evaluated in [`../prior-art/bonsai.md`](../prior-art/bonsai.md). | inferred | source tree |
| **Performance** | Torture-set booleans: Exact **0.41–15.6 ms**, Fast **0.21–1.06 ms**, Manifold **0.26–1.43 ms** (median of 5, two-operand cases plus the twelve-opening wall). On the wall the Exact solver is **11× slower than Manifold for an identical result**. `use_self` costs +81% when the input does not need it (15.4 → 27.8 ms). Object-model cost dominates everything: 10k objects = 494 ms to build, 473 ms first evaluation, 16.8 ms per single-object move, 62 kB of memory per object. | measured | [`spikes/boolean-torture/results/blender.md`](../../../spikes/boolean-torture/results/blender.md), [`spikes/blender-ceiling/results/blender.md`](../../../spikes/blender-ceiling/results/blender.md) |
| **Embeddability** | **Effectively none for our purpose.** The libraries are internal: `blenlib` and `geometry` are static libraries inside the Blender binary with no stable ABI, no packaging and no C API. `bpy` as a Python module exists but embeds the whole application. Driving it as a subprocess is what every measurement here did, and that is exactly the seam ADR-0004 Option B exists to avoid. | inferred; the subprocess path is measured (it ran) | this note's drivers |
| **2D derivation** | Line Art (`GREASE_PENCIL_LINEART` modifier) produces stylised outlines for rendering, not dimensioned drawings. No section/hidden-line facility comparable to a CAD kernel's. Not measured. | claimed (feature exists) | modifier type enum |
| **Maturity** | Very high as an application: ~30 years, funded foundation, quarterly releases, an issue tracker with active triage — of the 20 boolean reports surveyed, **12 closed and 8 open**, and the boolean's own author (`howardt`) answers on the tracker by name. That is materially healthier than the comparison in [`occt.md`](occt.md) §Maturity. The countervailing fact: **three solvers coexist because none is sufficient**, and the newest of them was added in 2025. | measured (survey; see §Known problems) | §Known problems |
| **AI familiarity** | Very high — three decades of public C/C++, an enormous body of Python API material, and the boolean algorithm's source paper is public. Recorded as one column and not used as a tiebreaker (R-09). | inferred | — |

## Exact boolean

This is the section [ADR-0005](../../architecture/decisions/0005-multi-representation-kernel.md)
cites, so it states the mechanism rather than summarising it.

### The algorithm and its provenance

The Exact solver is an implementation of **Mesh Arrangements for Solid Geometry** (Zhou, Grinspun,
Zorin and Jacobson, SIGGRAPH 2016) — named as such in the code
([`GEO_mesh_boolean.hh#L16-L27`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/GEO_mesh_boolean.hh#L16-L27),
where the enum value is literally `MeshArr`) and in the release notes. The same paper is the
lineage behind libigl's boolean, which is why [`README.md`](README.md) lists libigl alongside
Blender.

The pipeline, read at the pinned commit:

1. **Triangulate and intersect.** All operands are combined into one `IMesh` and every
   triangle–triangle intersection is computed, producing an arrangement of triangles that meet only
   at shared edges and vertices (`mesh_intersect.cc`).
2. **Test whether the input is PWN** — "Piece-wise constant Winding Number", "roughly means that
   the faces connect so as to form closed volumes"
   ([`mesh_boolean.cc#L1339-L1351`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L1339-L1351)).
   The test is edge-based: every edge's incident face orientations must sum to zero. The comment is
   candid that this is necessary and not sufficient, naming Klein bottles as the counter-example
   and calling the routine "only approximately right".
3. **If PWN**, group triangles into *patches*, build the *cell* graph they bound, propagate
   **winding numbers** from the ambient cell, and select cells by operation: intersection needs all
   winding numbers non-zero, union at least one, difference the first non-zero and at least one of
   the rest zero
   ([L2260-L2266](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L2260-L2266)).
   This branch is exact.
4. **If not PWN**, fall back to **ray casting** — per patch, or per triangle when `hole_tolerant`
   is on
   ([L3590-L3600](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L3590-L3600)).
   The ray-cast branch accumulates `Array<float> in_shape` — **float**, not rational
   ([L2750-L2752](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L2750-L2752)) —
   and its own comment says why it exists: "when the input is not PWN, some patches can be both
   inside and outside some shapes"
   ([L2726-L2733](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L2726-L2733)).

**The exactness is conditional on the input being closed.** That is the single most important
sentence in this section. An "exact boolean" that receives a mesh with a hole quietly becomes a
heuristic, and the API documents this as intended: "If the meshes don't satisfy those conditions,
all solvers will try to use ray-shooting to determine whether particular faces survive or not. This
may or may not work in the way the user hopes"
([`GEO_mesh_boolean.hh#L66-L72`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/GEO_mesh_boolean.hh#L66-L72)).

### How exactness is actually implemented

Two mechanisms, and they are separable — which matters, because our spec proposes taking one and
not the other.

**Exact predicates with a floating filter.** `orient2d`, `orient3d`, `incircle` and `insphere`
"give the exact result, using multi-precision arithmetic when result is close to zero", each paired
with a `_fast` variant that "just uses double arithmetic, so may be wrong if the answer is very
close to zero"
([`BLI_math_boolean.hh#L21-L45`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_math_boolean.hh#L21-L45)).
This is the adaptive-filter design our kernel spec §5 proposes, in production.

**Exact coordinates, carried alongside the approximate ones.** A `Vert` holds *both*:

```cpp
struct Vert {
  mpq3 co_exact;
  double3 co;
  int id = NO_INDEX;
  int orig = NO_INDEX;
};
```

— [`BLI_mesh_intersect.hh#L47-L62`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_intersect.hh#L47-L62),
with equality and hashing defined **on `co_exact`**, and the arena guaranteeing "that only one
instance of a Vert with a given co_exact will exist. I.e., it de-duplicates the vertices"
([L186-L192](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_intersect.hh#L186-L192)).
Vertex *identity* is therefore an exact-arithmetic decision, not a distance-under-tolerance
decision. This is the precise opposite of OCCT's model ([`occt.md`](occt.md) §Tolerance model) and
it is the reason Blender's boolean has no tolerance-growth problem at all: there is no tolerance to
grow.

The rationals are GMP's `mpq_class`, "separate multi-precision integer numerator and denominator,
reduced to lowest terms after each arithmetic operation"
([`BLI_math_mpq.hh#L11-L28`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_math_mpq.hh#L11-L28)),
and the whole file is inside `#ifdef WITH_GMP`: "The boolean functions in Blenlib use exact
arithmetic, so require GMP"
([`BLI_mesh_boolean.hh#L11`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_boolean.hh#L11)).
`WITH_GMP` and `WITH_MANIFOLD` are both build options
([`CMakeLists.txt#L345-L346`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/CMakeLists.txt#L345-L346)),
so a Blender built without them has only the Fast solver — an availability question a downstream
tool cannot control, and one reason `SolverNotAvailable` exists in the error enum.

### The float32 sandwich

The arrangement is exact. What it is given, and what it returns, is not:

| Stage | Type | Where |
|---|---|---|
| Stored mesh positions | **float32** | [`DNA_mesh_types.h#L251-L257`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_mesh_types.h#L251-L257) |
| Operand-to-operand transform | **float32** `float4x4`, snapped | [`mesh_boolean.cc#L325-L326`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L325-L326) |
| Conversion into the arrangement | float32 → `mpq3` → `double3` | [`#L344-L363`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L344-L363) |
| The arrangement and cell selection | exact rational | `blenlib/intern/mesh_boolean.cc` |
| Result written back | double → **float32** | [`#L758`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L758) |

The transform row deserves quoting, because it is the whole thesis of this note in one comment.
Before the exact arithmetic starts, the transform matrix is passed through `clean_transform`, which
snaps any entry within 1e-6 of 0, 1 or −1 to that value, with this reasoning:

> …rotation matrices for multiples of 90 degrees have tiny numbers where there should be zeros…
> so this is a hack to clean up such matrices. Would be better to change the transformation code
> itself.

— [`mesh_boolean.cc#L52-L79`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L52-L79),
elided at the ellipses, otherwise verbatim including its grammar. An exact algorithm is being fed
float32 input that has to be *snapped with a 1e-6 fuzz* to restore the coplanarity the user drew.
**Exactness downstream of an approximate representation buys correctness with respect to the wrong
input** — and the comment's own last sentence says where the fix belongs.

## The other two solvers

### Fast (`FLOAT`)

The pre-2.91 BMesh intersection, kept because it is quicker — *measured* at 1.1× (`disjoint`,
where neither has any work to do) to 15× (the twelve-opening wall) faster than the Exact solver
across the torture set, and 5–10× on the cases in between. It takes an
epsilon — and *which* epsilon depends on which caller you are:

- The **modifier** passes the user-visible `double_threshold`
  ([`MOD_boolean.cc#L364-L368`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/modifiers/intern/MOD_boolean.cc#L364-L368)),
  default 1e-6 m, documented as "Maximum distance between two faces to consider them as
  overlapping."
- The **geometry-node / mesh-level** path hard-codes `1e-6f` at two call sites
  ([`geometry/intern/mesh_boolean.cc#L1091-L1102`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L1091-L1102)
  and [L1115-L1126](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L1115-L1126)),
  ignoring any user setting.

It also **cannot report failure**: the dispatcher sets `*r_error = BooleanError::NoError`
unconditionally on the `Solver::Float` branch
([L1202-L1208](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L1202-L1208)).
Measured, this is not theoretical: on `identical` and `near_degenerate_triangle` it returned an
**empty union** (volume 0 where 1 was expected) and an intersection of volume 2, with 8 boundary
edges, and no error of any kind.

### Manifold (`MANIFOLD`)

A binding to the external `manifold` library, added **2025-04-22** in commit
[`dd559259d84f`](https://projects.blender.org/blender/blender/commit/dd559259d84f) ("Modeling: Add a
new boolean solver based on the Manifold library"), shipped in 4.5. It is the only solver that
**refuses** input it cannot handle: `Manifold::Error::NotManifold` becomes
`BooleanError::NonManifold`
([`mesh_boolean_manifold.cc#L1734-L1745`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean_manifold.cc#L1734-L1745),
[L2019-L2030](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean_manifold.cc#L2019-L2030)),
which the modifier turns into the message "Cannot execute, non-manifold inputs"
([`MOD_boolean.cc#L492-L501`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/modifiers/intern/MOD_boolean.cc#L492-L501)).

**And then returns the unmodified first operand.** We measured this on
`near_degenerate_triangle`, whose operand B is a T-junction mesh: the warning appears in the
console and the modifier's output is operand A. In that particular case A happens to *be* the right
answer, so the numbers look perfect — which is precisely how this class of fallback stays invisible
until it is not. Compare [`occt.md`](occt.md) §Known problems on IfcOpenShell's
"using first operand" path: the same shape of failure, a layer down.

The manual states the trade honestly: *Manifold* "Uses a solver that is usually fastest but only
works on Manifold meshes", and the page's warning is unambiguous — "Only Manifold meshes are
guaranteed to give proper results"
([`booleans.rst#L16-L20`, `#L67-L79`](https://projects.blender.org/blender/blender-manual/src/commit/ce0478a5b9329738e2cde9b7cbc22dd93500a8b8/manual/modeling/modifiers/generate/booleans.rst)).
On our torture set it was the **only solver that got every case right**, and 10× faster than Exact
on the twelve-opening wall. Its constraint is the point, and it is the same constraint
`problems.md` P-09 predicted.

## Carve history

[`README.md`](README.md) describes Blender as "the exact boolean (and the earlier Carve/BMesh
booleans it replaced — a root-cause case)", which is right that both earlier booleans belong to the
case. The sequence is worth stating precisely all the same, because it is easily compressed into
"Carve was removed when the exact boolean landed in 2.91" — and that is **wrong by almost three
years**, in a way that changes what the case teaches.

| When | What | Evidence |
|---|---|---|
| through 2.79b | Carve is the boolean library | `extern/carve` present at tag `v2.79b`, absent at `v2.80` (checked via the repository API at both tags) |
| **2018-02-07** | **Carve removed**, commit [`e0597baed57f`](https://projects.blender.org/blender/blender/commit/e0597baed57fa7a9dfaf6dff6d0fa120784d21ea) by Sergey Sharybin, reviewed by Campbell Barton | commit message, quoted below |
| 2.80 – 2.90 | The BMesh boolean is the *only* boolean | *inferred* from the absence of any other in the tree between those tags |
| **2020-08-28** | Exact solver merged, commit [`9e09b5c418c0`](https://projects.blender.org/blender/blender/commit/9e09b5c418c0a436e3c84ccf38c065527988b0a0) by Howard Trickey, design task T67744 "Boolean Redesign"; the BMesh solver stays as *Fast*; **default set to Exact** | commit message |
| 2020-09-07 | `Self` option added for the Exact solver, commit [`de21ab418d69`](https://projects.blender.org/blender/blender/commit/de21ab418d69ca82a07ec7c836b1deca09bbd57f) | commit message |
| 2020-11 | Shipped in 2.91 | [release notes](https://projects.blender.org/blender/blender-developer-docs/src/commit/fb9a26df737598c4e538ba8f57daf66ba2151057/docs/release_notes/2.91/modeling.md) |
| **2025-04-22** | Manifold solver added, commit [`dd559259d84f`](https://projects.blender.org/blender/blender/commit/dd559259d84f), shipped in 4.5 | commit message |

The Carve removal message is the interesting document, because it is a maintainer explaining that
replacing a boolean library with a different one **did not fix the failure class**. Sergey
Sharybin's message gives two reasons, in this order. The BMesh implementation is "way
easier for maintenance than abandoned Carve library" — and, after all the time, it "was working on
the same level of limitations about manifold meshes and touching edges than Carve" (commit
[`e0597baed57f`](https://projects.blender.org/blender/blender/commit/e0597baed57fa7a9dfaf6dff6d0fa120784d21ea),
2018-02-07, reviewed by Campbell Barton).

**The same limitations, about manifold meshes and touching edges.** Two floating-point boolean
implementations, written independently, failed on the same class of input, and the decision between
them was therefore made on maintenance cost — there was no quality difference left to decide on.

What *did* change the failure class was changing the arithmetic, two years later. The 2.91 release
note says so directly: "The Exact solver uses exact multi-precision arithmetic and a new algorithm
(taken from Mesh Arrangements for Solid Geometry…)… Overlapping geometry — coplanar faces,
overlapping edges — is handled properly", with the qualifier that matters kept in: confusion about
inside and outside "should be eliminated. At least, in the case where the input meshes describe
closed volumes."

**What this case teaches, corrected:** it is not "Blender replaced a bad boolean library with a
good one". It is *swapping implementations of the same numeric approach bought nothing; changing
the arithmetic bought the coplanar cases; and neither step fixed the cases where the input is not
closed.* That is the argument for kernel spec §5's exact predicates, and against expecting a
library swap to solve a boolean problem.

## Precision — the float32 finding

This is the section [ADR-0006](../../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md)
cites. It is the strongest measured result in this note and the least ambiguous.

### Storage, measured before any algorithm runs

Blender stores vertex positions as float32 in both mesh forms. Writing a coordinate into a mesh and
reading it back — nothing else — gives:

| Coordinate | float32 ULP | Round-trip error |
|---|---|---|
| 1 m | 1.19e-07 | 0 |
| 0.1 m | 7.45e-09 | 1.49e-09 |
| **500 000 m** | **0.03125** | — |
| 500 000.1 m | 0.03125 | **0.00625 m** |
| 500 000.001 m | 0.03125 | **0.001 m** |

*Measured*, [`spikes/precision-set/results/blender.md`](../../../spikes/precision-set/results/blender.md).
At 500 km from the origin, one float32 step is **3.125 cm**. No detail finer than that survives
storage, whatever the algorithm downstream does.

This is not only a large-coordinate problem. The torture set's `sliver` operand — a slab specified
as 1 m × 1 m × 1e-7 m at z = 0.5 — comes back out of Blender with volume **1.192e-7 m³**, because
`0.5 + 1e-7` is not representable in float32 and rounds to the next step. The slab is **19%
thicker than specified before any boolean runs**. Every `sliver` row in the results file inherits
that, and the boolean is not responsible for any of it. (It still counts as "correct" in the
summary table only because the correctness tolerance is floored at 1e-6 m³ absolute; in relative
terms it is 19% wrong.)

### The boolean at 500 km

Same geometry, offset by (500 km, 500 km, 0), result translated back, matched nearest-neighbour:

| Case | Solver | ΔV far − near | Worst vertex deviation |
|---|---|---|---|
| `wall_with_openings` union | Exact | **+0.15 m³** (1.2%) | **0.0348 m** |
| `wall_with_openings` intersection | Exact | **+0.225 m³** (4.2%) | **0.0348 m** |
| `wall_with_openings` union | Manifold | +0.15 m³ | 0.0348 m |
| `wall_with_openings` union | Fast | **−2.33 m³** (18%) | **0.1376 m** |
| `overlap_half`, `coplanar_faces` | Exact, Manifold | 0 | 0 m |

R-17's pass line is 1e-6 m and its fail line is 1e-4 m. **Blender fails R-17 by two to three orders
of magnitude**, and 0.0348 m is 1.1 × the float32 ULP at that distance — the deviation *is* the
storage quantisation, not an algorithmic error.

The two cases that came through at **exactly zero** are the proof of that diagnosis, and they are
worth reading carefully rather than as good news. `overlap_half` and `coplanar_faces` use only the
coordinates 0, 0.5, 1, 1.5 and 2; offset by 500 000 those are still exact multiples of the 0.03125
ULP, so **nothing was lost to round the operands to**, and the same driver's operand round-trip
table reports 0 error for both against 0.01375 m for the wall. The wall's coordinates (0.1, 0.3,
1.76, 3.42 …) are not. So the algorithm is translation-invariant and the representation is not —
and whether a given model survives depends on whether its dimensions happen to land on a 3 cm grid,
which is the worst possible property for a failure to have.

For contrast, [`occt.md`](occt.md) §Measurements records OCCT passing the same test at 2.65e-10 m,
which is f64 rounding of the coordinate itself. The gap between the two candidates on this test is
a factor of ~10⁸, and it is entirely explained by one type declaration.

### The local frame rescues it — and Blender cannot hold the frame

The same booleans, with the 500 km moved out of the vertex data and into each object's `location`
so the modifier evaluates in operand A's local space:

| Case | Solver | Deviation vs. the origin run |
|---|---|---|
| all three cases | Exact, Manifold | **0 m** |

*Measured*, same results file, §Probe. A local frame with the far placement outside it restores the
result exactly — which is the mitigation ADR-0006 proposes, measured on a real candidate rather
than argued.

**But Blender cannot be the tool that holds that frame**, and this is where the probe stops being
good news. *Inferred from the source, combined with the measured ULP table above:* `Object` stores
`float loc[3]` and returns a `float4x4 object_to_world`
([`DNA_object_types.h#L396-L398`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_object_types.h#L396-L398)),
so the *frame origin itself* is quantised to 3.125 cm at 500 km. The geometry inside the frame is
clean and the frame is in the wrong place. ADR-0006's requirement is therefore sharper than "use
local frames": **the frame origin must be f64 even when the geometry inside it is f32**, which is
exactly the split ADR-0006 proposes (f64 tile frames, camera-relative f32 at upload) and which
Blender does not implement.

A user-visible instance of the same thing is on the tracker:
[#158822](https://projects.blender.org/blender/blender/issues/158822), where a triager reproduces a
failing sculpt trim and reports it "related to the fact the geomtry is far away from the object
origin" [sic], fixed by *Origin to Geometry* — i.e. by moving the local frame.

## Incremental evaluation — the depsgraph

Question 1 of the twelve, and the design most worth borrowing.

The dependency graph is built from **ID nodes** (one per datablock) holding **component nodes**
(`TRANSFORM`, `GEOMETRY`, `PARAMETERS`, `ANIMATION`, `COPY_ON_EVAL`, `VISIBILITY`, …) holding
**operation nodes**
([`deg_node.hh#L46-L110`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/intern/node/deg_node.hh#L46-L110)).
A change tags an ID with a component-level flag — `ID_RECALC_TRANSFORM`, `ID_RECALC_GEOMETRY`
([`DNA_ID.h#L1054`, `#L1074`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_ID.h#L1050-L1080)) —
and evaluation "takes the operation-nodes the Depsgraph has tagged for updating, and schedules them
up for being evaluated/executed such that the all dependency relationship constraints are
satisfied"
([`DEG_depsgraph.hh#L9-L24`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/DEG_depsgraph.hh#L9-L24)).
Evaluation writes into *copies*, not into the authored datablocks: the graph has a `COPY_ON_EVAL`
component as "entry component of majority of ID nodes", and the query API distinguishes original
from evaluated IDs explicitly — "Original IDs are considered all the IDs which are not covered by
copy-on-evaluation system"
([`DEG_depsgraph_query.hh#L141-L152`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/DEG_depsgraph_query.hh#L141-L152)).
That is the same separation kernel spec §3 wants between authored and derived geometry.

Three properties are worth taking: **tagging is per component, not per datablock**, so moving an
object does not re-run its geometry; **evaluation is a scheduled DAG**, so independent work
parallelises for free; and **the evaluated copy is separate from the source**, so the source is
never in a half-updated state.

The property to *avoid* is the granularity. One IFC element is one object is one ID, and the graph
has a per-ID cost. Measured on a scene of nothing but boxes, headless, with no viewport:

| Objects | One `view_layer.update()` after moving one object |
|---|---|
| 1 000, as 1 000 objects | 1.23 ms |
| 1 000, as one 1 000-shell mesh | 0.005 ms |
| 10 000, as 10 000 objects | **16.8 ms** |
| 10 000, as one 10 000-shell mesh | 0.013 ms |
| 100 000, as 100 000 objects | **295.3 ms** |
| 100 000, as one 100 000-shell mesh | 0.028 ms |

*Measured*, [`spikes/blender-ceiling/results/blender.md`](../../../spikes/blender-ceiling/results/blender.md).
Ten thousand objects is a small building. 16.8 ms is the entire frame budget, spent on the
bookkeeping for one dragged object, before anything is drawn. The same triangles in one object cost
0.013 ms — a factor of ~1300 — so this is per-object overhead and not geometry volume. Memory says
the same thing: the 100k-object scene cost **6 224 MB**, about **62 kB per object**, for 1.2 M
triangles that occupy a few tens of MB when they live in a single mesh.

The tracker carries the user-facing version:
[#156584](https://projects.blender.org/blender/blender/issues/156584), "Mesh with very slow Boolean
modifier slows down the whole scene, even when not interacted", where a Blender developer confirms
"a boolean modifier appears to be needlessly reevaluated" and another commenter replies "though I
believe this is a known limitation".

## The GPU module

Summarised here for the kernel's buffer-layout decisions and for Task 11; the renderer comparison
belongs in [`../renderers/`](../renderers/).

**Backend abstraction.** `source/blender/gpu/` presents `VertBuf`, `IndexBuf`, `Batch`, `Shader`,
`FrameBuffer`, `StorageBuf`, `Texture` over four backends: `opengl/` (38 files), `vulkan/` (85),
`metal/` (45) and `dummy/`. That Vulkan is now the largest backend directory is the clearest
available signal of where the project's GPU work is going. Usage hints are explicit
(`GPU_USAGE_STREAM` / `STATIC` / `DYNAMIC` / `DEVICE_ONLY`,
[`GPU_vertex_buffer.hh#L42-L54`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_vertex_buffer.hh#L42-L54)),
which is the interface a kernel wants: the producer says how the data will be used, the backend
decides where it lives.

**Geometry reaches the GPU through single-purpose extractors.** `draw/intern/mesh_extractors/`
holds 30 files, one per buffer: `extract_mesh_vbo_pos`, `_vnor`, `_lnor`, `_uv`, `_tan`,
`_select_idx`, `ibo_tris`, `ibo_lines`, … Each turns the `Mesh` attribute arrays into one vertex or
index buffer. Positions upload as `SFLOAT_32_32_32` — float32, matching storage exactly, with no
camera-relative rebasing — and are allocated **per face corner**, not per vertex
([`extract_mesh_vbo_pos.cc#L73-L84`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/mesh_extractors/extract_mesh_vbo_pos.cc#L73-L84)).
Per-corner layout trades memory for the ability to give every corner its own normal and UV without
splitting the source mesh — a deliberate choice worth weighing rather than copying.

**What comes back is only identity.** `GPU_select_begin` / `GPU_select_end` fill a buffer of
`GPUSelectResult { unsigned int id; unsigned int depth; }`
([`GPU_select.hh#L29-L42`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_select.hh#L29-L42)) —
an id written by the shader and a depth. No geometry, no positions, nothing the kernel could
consume. The GPU is a display and a picking oracle; it is not part of the modelling path.

**Node evaluation is batch-shaped.** `functions/` provides `MultiFunction`, "optimized for
throughput (instead of latency)… by always processing many elements at once, instead of each
element separately"
([`FN_multi_function.hh#L9-L17`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/functions/FN_multi_function.hh#L9-L17)),
with `LazyFunction` for the node graph. The pairing is instructive: an object-granular scheduler
(depsgraph) on top of an element-batched executor (multi-functions). Our spec's structure-of-arrays
kernel with an evaluation graph in `app/` is the same split, one level down.

## Known problems

This section supplies the evidence for [`problems.md`](problems.md) P-01, P-05, P-07, P-09 and the
new P-16.

### Issue-tracker survey

Twenty reports from Blender's own tracker, every one opened by us against the tracker's public API
(`/api/v1/repos/blender/blender/issues/<n>` plus its `/comments`) and read before being listed —
the HTML pages return 403 to automated fetches, so the API is the only route and titles, dates and
states below are copied from its JSON. **Roles are labelled, not assumed:** `howardt` is Howard
Trickey, the author of the exact solver's merge commit
[`9e09b5c418c0`](https://projects.blender.org/blender/blender/commit/9e09b5c418c0a436e3c84ccf38c065527988b0a0),
so his diagnoses are the implementer's. Where a comment shows implementer-level work (bisecting,
naming a commit, running ASAN) without the tracker labelling the role, it is called *developer*.
Everything else is *reporter* or *triage*.

| # | Solver | Trigger | Traced cause | State | Link |
|---|---|---|---|---|---|
| 143644 | Manifold | coplanar + threading | **Developer-confirmed.** `howardt`: the case "creates quite a number of coplanar faces that have to be handled by Manifold"; a Blender developer adds "this is indeed a threading issue… When running Blender single threaded, this doesn't happen"; reported upstream to the Manifold library | closed 2026-05 | [issue](https://projects.blender.org/blender/blender/issues/143644) |
| 145491 | Fast | large coordinates / object size | Reporter-level but code-level: "Setting epsilon to 1e-7 in `BM_mesh_intersect` makes the flickering disappear… But it can slow down the algorithm". Triage confirms "the issue is gone when using the `Exact` or `Manifold` boolean" | open 2025-09, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/145491) |
| 135135 | (mesh boolean) | precision | Commenter: "I tend to think of this as systematic limitation of the boolean algorithm… It's limited by floating point precision." Triage moved it to the Modeling module and labelled it **Type/Known Issue** | open 2025-02 | [issue](https://projects.blender.org/blender/blender/issues/135135) |
| 108780 | Exact | thin / planar cutter | Not traced. Triage response points at the manual's non-manifold warning and suggests adding a Solidify modifier "(even with a tiny 0.0001 amount)" as the workaround | open 2023-06, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/108780) |
| 161732 | Exact | — (regression) | **Developer-bisected** to a specific commit; `howardt`: "Strange, since I haven't changed anything in that code lately. Though there have been some changes in the delaunay triangulation that maybe caused some issue." The bisecting developer adds "it might be something that is revealed by it, rather than caused" | open 2026-07, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/161732) |
| 153708 | Exact + `use_self` | self-intersection | **Developer diagnosis** with a source link: a failing assert suggests that "the `face_edge_offset` number gets too large" and that a 32-bit integer runs out of bits. Triage had first guessed out-of-memory and was corrected by measurement — "It's not out of memory, Blender only uses around 2GB at the time of the crash" | closed 2026-02, Resolved | [issue](https://projects.blender.org/blender/blender/issues/153708) |
| 149112 | Exact | empty result | Triage confirmed and bisected: "I can confirm the crash in 5.1, but not 5.0", then named the causing commit and referred it to a developer — a crash when a difference produces an empty mesh. Opened and closed the same day | closed 2025-10, Resolved | [issue](https://projects.blender.org/blender/blender/issues/149112) |
| 150360 | Fast | duplicate output geometry | **Developer diagnosis**, and an unusually explicit one: "the BMesh float boolean implementation outputs a mesh with duplicate edges", traced to `BM_face_split_edgenet_connect_islands`, with two attempted fixes that each broke something else | closed 2025-11, Resolved | [issue](https://projects.blender.org/blender/blender/issues/150360) |
| 150728 | Fast | attribute loss | Reported, triage-confirmed, and given a **hedged developer hypothesis**: a Blender developer suggests a specific `CustomData_has_math` check "has to be removed from `BM_face_split_edgenet`" while saying "I don't really know this code though, so not sure". The reporter's own observation — that a degenerate UV map makes the Float solver behave like the others — is the reporter's, not a maintainer's | open 2025-11, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/150728) |
| 139370 | Manifold | flipped normals | **`howardt`**: "I have confirmed that the bad result comes from the manifold library" — a mesh with inverted normals is not "manifold" by the library's definition | closed 2025-05, Archived | [issue](https://projects.blender.org/blender/blender/issues/139370) |
| 140590 | Manifold | coplanar faces | **`howardt`** rejects the input as out of contract: "The objects in the attached files are not really in the form expected for manifold boolean", showing self-intersecting edges in the reporter's model | closed 2025-07, Archived | [issue](https://projects.blender.org/blender/blender/issues/140590) |
| 144698 | Manifold | vertices/edges only | **`howardt`**: "I confirm the bug and will fix it" — a mesh with one point and zero faces produced "Unknown Boolean Error" instead of a description of the problem | closed 2025-09, Archived | [issue](https://projects.blender.org/blender/blender/issues/144698) |
| 155657 | Manifold | duplicate in edit mode | **Developer-level**: an assert reproduced under a debugger with `-t 1`, plus "I don't always get the assert, but if I scale the cutter in objectmode I nearly always hit a scale where it happens" — a hang requiring a force quit | closed 2026-03, Resolved | [issue](https://projects.blender.org/blender/blender/issues/155657) |
| 154746 | Manifold | coincident vertices | Triage: "Can confirm". A commenter reports "a similar situation with float boolean against perfectly overlapping geometries" — i.e. the same trigger reaching a second solver — and refers it to the boolean's author. Title: multiple vertices on the same point crash Blender | closed 2026-02, Resolved | [issue](https://projects.blender.org/blender/blender/issues/154746) |
| 99892 | (modifier) | extreme scale | Triage confirmed and reproduced at scale "{1e+29, 1e+29, 1e+29}"; the triager's own analysis: "It looks like the membership check function can't check such coordinates", and the proposed fix was to clamp coordinates. Labelled **Type/Known Issue**; open for 3½ years before archiving | closed 2026-01, Archived | [issue](https://projects.blender.org/blender/blender/issues/99892) |
| 158822 | (sculpt trim) | distance from origin | Triage: "related to the fact the geomtry is far away from the object origin" [sic]; *Origin to Geometry* fixes it | open 2026-05, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/158822) |
| 158737 | (mesh unions) | memory | Title: "44x increase in memory usage for geometry nodes + mesh unions", 5.0.1 → 5.1.1. Confirmed by a developer whose **bisection failed to isolate it** ("Bisecting failed to give insights"); another developer suspects "some change in the mesh boolean code". A later commenter reproduces the class of problem on 5.3 alpha | closed 2026-07, Resolved | [issue](https://projects.blender.org/blender/blender/issues/158737) |
| 156584 | (modifier) | re-evaluation | **Developer-confirmed**: "a boolean modifier appears to be needlessly reevaluated"; a slow boolean on one object slows the whole scene when nothing touches it | open 2026-03, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/156584) |
| 105652 | Exact + `use_self` | memory | Not traced; triage speculates about available RAM. Open for ~3 years before archiving | closed 2026-03, Archived | [issue](https://projects.blender.org/blender/blender/issues/105652) |
| 115557 | (modifier) | merged edges/faces | Not traced. Reporter, on union of two watertight shapes: "Because faces are missing, the merged shape is no longer manifold", which then corrupts later booleans. Open since 2023 | open 2023-11, Confirmed | [issue](https://projects.blender.org/blender/blender/issues/115557) |

### What the survey shows, and what it does not

- **The failure classes separate cleanly by solver, which is unusual and useful.** Fast fails on
  overlapping and coplanar geometry (150360, 145491, 150728); Manifold fails by *refusing*, or by
  faithfully reproducing its library's definition of manifold (139370, 140590, 144698); Exact fails
  on degenerate and self-intersecting configurations and on integer-width limits (153708, 108780,
  149112). Three solvers, three envelopes, no single one covering the union.
- **The tracker is healthy, and the boolean's author answers on it by name.** That is a real
  maturity difference from [`occt.md`](occt.md) §Maturity, where 14 of 20 surveyed issues were open
  and several carried "not yet analyzed" as the only response. It is also worth noting what
  "closed" means here: several of these are `Status/Archived`, i.e. closed without a fix
  (140590, 105652, 99892).
- **No issue was found in which a boolean produced a wrong volume silently and a maintainer
  confirmed the mechanism.** The closest are 135135 (labelled a known limitation of floating-point
  precision) and 115557 (untraced since 2023). The silent-wrongness case in this note is one *we*
  measured, below; it is not corroborated by a ticket, and that is stated rather than papered over.
- **The trigger column is our classification** from reading each ticket, not the tracker's. It is
  a catalogue of failure *mechanisms* and must not be read as a frequency distribution.

### The ones we found ourselves

Four, all reproducible from the committed driver.

**1. The Exact solver deleted an operand — silently, and the result passed every check.**
`touching_vertex` is two unit cubes meeting at exactly one point. The Exact union returns a
**closed, manifold, single-shell mesh of volume 1**: one cube, the other gone. `Mesh.validate()`
makes no correction. No warning is printed. Both operand orders behave identically. Moving the
second cube 1 mm away, or 1 mm in, produces the correct volume 2 — so the failure is exactly at the
degenerate contact and nowhere near it. The Fast and Manifold solvers both return 2. *Measured*,
Probe D in [`results/blender.md`](../../../spikes/boolean-torture/results/blender.md).

This is the same failure *shape* as OCCT's `sliver` ([`occt.md`](occt.md) §The one we found
ourselves) reached from the opposite direction: OCCT lost geometry below its tolerance; Blender,
which has no tolerance, lost a component whose contact with the other operand has measure zero. The
lesson generalises past both: **a boolean must report what it consumed, because "valid closed
manifold result" is not evidence that the operands are still in it.**

**2. The volume identity can pass while both answers are wrong.** On `overlap_half` the Fast solver
returned V(∪) = 1 and V(∩) = 1 where 1.5 and 0.5 were expected. The identity
`V(A)+V(B) = V(∪)+V(∩)` residual is **0**. The errors are equal and opposite, so the check the
torture set is built around cannot see them. Anyone building a boolean test suite — including ours,
[`../../../reference/boolean_torture_set.py`](../../../reference/boolean_torture_set.py) — must
compare against the analytic values per operation and treat the identity as a *necessary* condition
only.

**3. The Fast solver is non-deterministic.** Ten runs of `overlap_half` union, operands rebuilt
each time in one process, produced **two distinct results** (32 verts / 14 faces nine times, 32 /
13 once). Volume was the same; topology was not — and an earlier run of the same driver produced
a 32 / 15 variant that this one did not, so at least three topologies exist for this one input. *Measured*, Probe E. Blender's tracker documents
a developer-confirmed threading non-determinism in the *Manifold* solver
([#143644](https://projects.blender.org/blender/blender/issues/143644)); this is the same class in
a different solver, and we did not find a ticket for it. A kernel whose output varies run to run
cannot be diffed, cached, or regression-tested, and in a BIM tool it means two people opening the
same file can get different geometry.

**4. The benchmark's twelve-shell tool is accepted; the T-junction operand is not.**
`wall_with_openings` B — one mesh object with twelve disconnected closed shells — is handled
correctly by all three solvers, including the `DIFFERENCE` the case actually models (3.6 m³
expected, 3.60000053 measured by Exact and Manifold). Multi-shell input is a non-issue for a mesh
kernel, where for OCCT it forced a compound of twelve solids. Conversely
`near_degenerate_triangle` B, whose extra vertex sits *on* an existing edge, is a T-junction and is
therefore **non-manifold as a mesh**: the Manifold solver refuses it with "Cannot execute,
non-manifold inputs" and returns operand A. A representation difference, not a quality difference —
and a reminder that a benchmark case is only fair when its construction is stated for each
candidate, which is why both drivers document theirs.

## Measurements

**Hardware:** Intel Core i9-14900HX (32 threads), 32 GB RAM, Windows 11 Pro 10.0.26200.
**Versions:** Blender **5.0.0**, build hash `a37564c4df7a`, built 2025-11-18 11:06:54, bundled
Python 3.11.13. Run headless with `--background --factory-startup`; the second flag matters,
because without it the user's installed add-ons are loaded into the measured process.
**Benchmark models:** [`reference/boolean_torture_set.py`](../../../reference/boolean_torture_set.py)
(10 cases), [`reference/precision_set.py`](../../../reference/precision_set.py) (3 cases), and
synthetic boxes for the object-count spike.

**Method.** Three drivers, all committed:
[`spikes/boolean-torture/blender_driver.py`](../../../spikes/boolean-torture/blender_driver.py),
[`spikes/precision-set/blender_driver.py`](../../../spikes/precision-set/blender_driver.py),
[`spikes/blender-ceiling/blender_driver.py`](../../../spikes/blender-ceiling/blender_driver.py).
Raw output is in each spike's `results/blender.md`; those files are the reproducible record and
this section is the summary. Nothing appears here that is not in one of them.

Method details that affect the numbers:

- Operands are built with `Mesh.from_pydata` from the reference set **verbatim** — no welding, no
  triangulation, no scaling — and **rebuilt for every solver, every operation and every repeat**.
  The modifier is non-destructive, but reusing objects would also reuse whatever a previous
  `Mesh.validate()` did to them.
- `wall_with_openings` B is built as **one mesh object with twelve disconnected shells**,
  deliberately differing from the OCCT driver's compound of twelve solids, because that is the
  natural reading of the benchmark for a mesh kernel. Whether it is accepted is a finding
  (it is).
- Volume is computed by the driver's own triangulation (`bmesh.ops.triangulate`) fed to
  `reference.signed_volume` — the same function the reference set and the OCCT driver use. Blender
  is never asked for a volume.
- Validity is the driver's own check: closed (no boundary or wire edges), manifold (every edge in
  exactly two faces), no loose vertices, no faces below 1e-14 m², and `Mesh.validate()` making no
  correction. An empty result is judged against the analytic expectation, so a correctly empty
  intersection counts as valid.
- Timing is wall-clock around depsgraph evaluation plus the evaluated-mesh copy, median of 5;
  the modifier's own `execution_time` is recorded beside it in the results file.
- Blender's own console warnings are captured per run by duplicating file descriptor 1, so a
  message can be attributed to the run that produced it rather than to the log as a whole.

### Boolean torture set (R-16)

| Solver | Topologically valid | Numerically correct | Worst identity residual | Time range (ms) |
|---|---|---|---|---|
| Exact | 8 / 10 | **9 / 10** | 1 | 0.41 – 15.6 |
| Fast (float) | 5 / 10 | 7 / 10 | 4.94e-07 | 0.21 – 1.06 |
| Manifold | **10 / 10** | **10 / 10** | 1.42e-14 | 0.26 – 1.43 |

Against R-16 — pass is every case valid with the identity within 1e-9 relative — **Manifold
passes, Exact and Fast fail.** Reading the table needs three cautions, all recorded in the results
file:

- Manifold passes *on the operands Blender gave it*, which for `sliver` were already 19% wrong
  before the boolean ran (§Precision). The identity is computed from measured operand volumes
  precisely so that it isolates the boolean, and here that isolation flatters the whole candidate:
  no solver can be blamed for the representation, and no solver escapes it either.

- *Valid* and *correct* diverge in both directions. The mathematically correct union of two cubes
  sharing an edge is **not** manifold, so the Exact solver's correct `shared_edge` answer is marked
  invalid by the topological check and is not wrong to be; conversely the Fast solver's
  `touching_vertex` answer is valid and correct only because it left the operands unmerged.
- The Exact solver's single numerical failure is `touching_vertex`, and it is a whole operand
  (residual 1.0 on a 2.0 answer), not a rounding error.

### Precision set (R-17) — fails

Worst vertex deviation over the whole set: **0.5 m** (Fast solver, `overlap_half`, where the far
result is a different wrong answer from the near one). Attributable purely to precision:
**0.0348 m** on the twelve-opening wall, for Exact and Manifold alike, against a float32 ULP of
0.03125 m at that distance. R-17's fail line is 1e-4 m. See §Precision.

### Object-count ceiling (R-03, partial)

| Objects | Variant | Build | First full evaluation | One incremental update | Memory |
|---|---|---|---|---|---|
| 1 000 | 1 000 objects | 47 ms | 39 ms | 1.23 ms | 81 MB |
| 1 000 | one 1 000-shell mesh | 8 ms | 6 ms | 0.005 ms | 3 MB |
| 10 000 | 10 000 objects | 494 ms | 473 ms | **16.8 ms** | 619 MB |
| 10 000 | one 10 000-shell mesh | 207 ms | 172 ms | 0.013 ms | — |
| 100 000 | 100 000 objects | 26.8 s | 10.0 s | **295.3 ms** | 6 224 MB |
| 100 000 | one 100 000-shell mesh | 3.1 s | 2.0 s | 0.028 ms | — |

Headless, no viewport, no add-ons, `bpy` only. R-03's criterion is about viewport interactivity, so
this **cannot** deliver its pass verdict — but it is a lower bound on the cost, and the lower bound
already consumes a frame budget at 10k objects for a single moved object.

At **100 000 objects** the same single-object move costs **295.3 ms**, about eighteen frames; the
first full evaluation costs **10.0 s** and the scene occupies **6.2 GB**. The same 1.2 M triangles
as one object cost 0.028 ms per update, so the quantity being measured is per-datablock cost and
not geometry volume. (The single-object rows' memory is left blank above: their measured deltas
came out negative, because the working set was still shrinking from the previous scene's teardown.
The ~62 kB per object quoted here is taken from the *separate* rows alone, where it is consistent
at both 10k and 100k, so it does not depend on that baseline.)

**This settles the part of R-03 the risk register was uncertain about: the ceiling is Blender's,
not Bonsai's.** No add-on can avoid it, because what is being counted is Blender datablocks, and
one IFC element must be one datablock for the element to be selectable and attributable at all.
What the measurement does **not** settle is R-03 as written: it is headless, so draw-call
batching, the outliner and selection are unmeasured — all of which can make the number worse and
none of which can make it better. Changing R-03's status in [`../../risks.md`](../../risks.md) is
not this note's job.

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** **Yes — the only
   candidate read so far that can** — the depsgraph tags per ID *component* and re-runs only
   the affected operation nodes. The qualifier is the cost per object: 16.8 ms at 10k objects for
   one move and 295 ms at 100k, measured, headless.
2. **IFC round trip?** Not applicable — Blender has no IFC. Answered in
   [`../prior-art/bonsai.md`](../prior-art/bonsai.md).
3. **Driven in-process from DynLex without a subprocess or a file?** **No.** `blenlib` and
   `geometry` are internal static libraries with no stable ABI, no C API and no packaging; `bpy`
   embeds the whole application. Every measurement in this note ran as a subprocess, which is the
   seam ADR-0004 Option B exists to avoid.
4. **Threading model, and what is single-threaded by design?** Threaded by default via TBB
   throughout the boolean — including the PWN check and the float32→rational conversion. Nothing
   found that is single-threaded by design. The cost of that default is measured: the Fast solver
   returned two different topologies for identical input in ten runs.
5. **What breaks first at scale?** The **object model**, decisively, and long before geometry:
   16.8 ms per single-object update at 10k objects against 0.013 ms for the same triangles in one
   object, and 6.2 GB of memory for 100k boxes. Memory follows (the tracker's 44× regression, #158737); boolean time is not the
   bottleneck at BIM scale.
6. **Numeric precision internally, and configurable?** **float32 stored, exact rational internally
   in the Exact solver, float32 out.** Not configurable: there is no double-precision mesh in
   Blender and no option that produces one. The Fast solver's `double_threshold` is a distance
   threshold, not a precision setting, and one of the two call paths ignores it.
7. **Operate on a subset — one tile, one region?** Yes at object granularity: a boolean modifier
   touches its own object and its operand. There is no sub-object region concept, and the
   per-object cost of question 5 sets the tile size.
8. **Who maintains it, and what if they stop?** The Blender Foundation, with paid staff, a public
   tracker where the boolean's author answers by name, and a large contributor base. Bus factor on
   the *boolean specifically* looks thinner than on the project: one name recurs on almost every
   ticket in the survey.
9. **Documented failure modes and the design choice behind each?** §Known problems. Three solvers,
   three distinct failure envelopes, and one root cause shared by all three: the representation
   they read and write is float32, so the input to an exact algorithm is already rounded.
10. **Representations held natively, and conversions?** Two mesh forms (`Mesh`, `BMesh`) with
    constant conversion between them — the boolean modifier's own comment calls its round trip
    "utterly non-optimal". Volumes, point clouds and curves are separate datablock types, not a
    shared representation layer. For ADR-0005 this is a partial positive: it shows two
    representations of the *same* kind coexisting with an explicit conversion seam, which is the
    smallest version of the multi-representation bet.
11. **How does geometry reach the GPU and come back?** Through per-buffer extractors to float32
    per-corner vertex buffers, behind a four-backend abstraction. Nothing comes back but
    `{id, depth}` from picking. §GPU.
12. **What would we take, and what would we avoid?** §Verdict.

## Strengths

- **The exact arrangement is a published algorithm with a readable implementation**, in which
  vertex identity is an exact-arithmetic decision rather than a distance comparison. On our set it
  was beaten on both correctness and speed by the Manifold library, so "exact arrangement" is not
  by itself the answer — but it is the design whose failures we can reason about.
- **Adaptive exact predicates with a floating filter**, already separated from the rest
  (`orient3d` vs `orient3d_fast`) — the exact structure kernel spec §5 proposes.
- **The depsgraph** is a working, shipped answer to R-01 at datablock-component granularity.
- **Three solvers behind one enum** is an honest interface: the caller chooses the trade, and the
  choice is one property.
- **Errors are typed**, not boolean: `NoError`, `NonManifold`, `ResultTooBig`, `SolverNotAvailable`,
  `UnknownError`.
- **A healthy tracker** with implementer participation, which is where most of §Known problems
  came from.
- **The GPU module's backend abstraction and explicit usage hints** are a good model for a
  buffer-layout API.

## Weaknesses

- **float32 storage**, which the README's own matrix calls disqualifying for *build on*, and which
  we measured costing 3.5 cm and 0.15 m³ at 500 km.
- **GPL**, which forecloses code reuse in a differently-licensed kernel and would relicense
  anything that linked it.
- **Per-object evaluation cost** — 16.8 ms for one move at 10k objects, 295 ms at 100k, headless;
  and ~62 kB of memory per object, 6.2 GB for a 100k-box scene.
- **Silent operand loss** on exactly-touching input, with a valid, manifold, checker-approved
  result (Probe D).
- **Non-determinism** in the Fast solver, measured; developer-confirmed in the Manifold solver on
  the tracker.
- **Exactness is conditional**: non-PWN input silently downgrades to a float ray-cast heuristic.
- **The Fast solver cannot report failure** — its dispatch branch sets `NoError` unconditionally.
- **A refusal returns the first operand**, so a failed boolean looks like a successful no-op unless
  the caller reads the console.
- **No embedding path** short of running the application.
- **Both robust solvers are build options** (`WITH_GMP`, `WITH_MANIFOLD`), so their availability is
  not guaranteed by the version number.

## Risks

If we built on Blender, the risk that would not surface until too late is **the coordinate
system**. The exact solver's measurements at unit scale are excellent; the failure appears only when the
model is placed where real projects are placed, and it appears as 3 cm of drift rather than as an
error. A BIM tool would ship, look correct in every demo, and produce a model that disagrees with
the survey by a slab thickness. This note found it only because the precision set exists and was
written before the driver.

The second risk is **the object model**, and it is the one that decides R-03. It cannot be fixed by
using Blender differently: the cost is per-datablock, and one IFC element is one datablock.
Modelling a building as few objects with many shells would sidestep it — 0.013 ms instead of
16.8 ms — and would also throw away the per-element identity that makes it BIM.

Both risks are the *reason* to read this note, and neither is an argument that our own kernel will
do better. Blender's boolean is the product of years of work by people who understood the
problem — the exact solver alone has been in the tree since 2020, and its tracker shows what that
bought and what it did not; `problems.md` N-01 remains the honest counterweight.

## Verdict

### Build on — **no**

Three independent disqualifications, each sufficient on its own:

1. **Licence.** GPL. Linking it makes our kernel GPL; copying from it is not permitted at all
   (R-11). This is a decision, not a measurement, and it applies before any technical argument.
2. **float32 storage** (R-17, ADR-0006). Measured failure by two to three orders of magnitude at a
   distance real projects use. There is no configuration that changes it.
3. **No embedding path** (ADR-0004). No stable ABI, no C API, no library packaging. Every number in
   this note was obtained by launching an application.

Two further findings would matter if the three above did not: the per-object evaluation cost
(question 5) and the silent operand loss (Probe D).

The boolean *quality* is not among the reasons — the Manifold solver got every torture case right
and the Exact solver got nine of ten. As with OCCT, the rejection is structural.

### Borrow from — **substantially, as design; never as code**

GPL makes the distinction unusually sharp. Everything below is an idea to reimplement from the
published paper and the documentation, with the citation that justifies it.

| Take | Why | Where it comes from |
|---|---|---|
| **The exact-arrangement approach**: intersect everything into an arrangement, group into patches and cells, decide by winding number per operation | It replaces a long tail of special cases with one uniform decision, and it is the change that actually fixed Blender's coplanar failures where swapping libraries had not (§Carve history) | [Zhou, Grinspun, Zorin, Jacobson, SIGGRAPH 2016](http://www.cs.columbia.edu/cg/mesh-arrangements/mesh-arrangements-for-solid-geometry-siggraph-2016-zhou-et-al.pdf); [`mesh_boolean.cc#L2188-L2266`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L2188-L2266) |
| **Exact predicates behind a floating filter**, with the fast variant kept as a separate named function | Exactly kernel spec §5's "exact arithmetic only in predicates, adaptive with a floating filter", already proven in production — and the naming discipline (`orient3d` vs `orient3d_fast`) makes the choice auditable at every call site | [`BLI_math_boolean.hh#L21-L45`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_math_boolean.hh#L21-L45) |
| **Carry the exact coordinate alongside the approximate one, and define identity and hashing on the exact one** | This is what makes vertex identity a decision rather than a guess, and it is what a tolerance-based kernel cannot do. Our spec's "constructed points are rounded but never decide" is this idea | [`BLI_mesh_intersect.hh#L47-L62`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_intersect.hh#L47-L62), [L186-L192](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/BLI_mesh_intersect.hh#L186-L192) |
| **BMesh's radial-loop half-edge variant**: an edge holds a circular list of loops, so *n* faces may share an edge | A half-edge structure that assumes manifoldness cannot represent a wall junction, a T-junction, or the correct union of two solids sharing an edge — which our own torture set produces. Radial loops cost one pointer pair per loop and remove the assumption | [`bmesh_class.hh#L154-L214`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/bmesh_class.hh#L154-L214), cap at [L706](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/bmesh_class.hh#L706) |
| **Two mesh forms with an explicit conversion seam** — array storage for the common case, half-edge for topological editing | ADR-0005's multi-representation bet in its smallest form, shipped and load-bearing. Take the seam; **do not** take the round trip the modifier calls "utterly non-optimal" | [`DNA_mesh_types.h`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_mesh_types.h) vs [`bmesh_class.hh`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/bmesh/bmesh_class.hh) |
| **The depsgraph's incremental model**: ID → component → operation nodes, component-level dirty flags, evaluation into copies | The concrete answer to R-01, at a granularity fine enough that moving an object does not re-run its geometry. Our version puts the graph in `app/` (spec §3) and must go finer than one node per element | [`deg_node.hh#L46-L110`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/depsgraph/intern/node/deg_node.hh#L46-L110), [`DNA_ID.h#L1050-L1080`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/makesdna/DNA_ID.h#L1050-L1080) |
| **A typed error enum on the boolean, and preconditions stated as assumptions the caller asserts** (`no_self_intersections`, `no_nested_components`, `watertight`) | The caller telling the algorithm what it may assume is better than the algorithm guessing, and better than a flag that only makes it slower. Pair it with OCCT's categorised validity | [`GEO_mesh_boolean.hh#L34-L58`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/GEO_mesh_boolean.hh#L34-L58) |
| **Explicit GPU usage hints and a backend abstraction over vertex/index buffers** | The kernel should say how a buffer will be used and let the backend place it; four backends behind one interface is the proof it is a workable seam | [`GPU_vertex_buffer.hh#L42-L54`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/GPU_vertex_buffer.hh#L42-L54) |
| **Batch-shaped element evaluation** (`MultiFunction`) under an object-granular scheduler | Structure-of-arrays throughput below, dependency scheduling above — the same split our spec proposes between `kernel/` and `app/` | [`FN_multi_function.hh#L9-L17`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/functions/FN_multi_function.hh#L9-L17) |

### Avoid — each failure class mapped to the design choice behind it

| Failure class | Design choice it traces to | Evidence | Our design's answer |
|---|---|---|---|
| An operand disappears from a boolean result, which is nonetheless closed, manifold and checker-approved | Cell selection by winding number decides which *cells* survive; nothing in the contract requires each input shape to be represented in the output, and a measure-zero contact produces no cell to keep | `touching_vertex`: V(∪) = 1 where 2 was expected, both operand orders, correct at ±1 mm (measured, Probe D) | Exact predicates decide topology (spec §5) **and** an operation reports what it consumed: a union that dropped an operand is a reported fact, not a silent one. **P-01** |
| Geometry is quantised before an exact algorithm ever sees it | float32 storage in `Mesh` and `BMesh`, float32 object transforms, with a 1e-6 "hack" to snap transforms back to coplanarity | 0.0348 m deviation and 0.15 m³ volume loss at 500 km (measured); `sliver` operand 19% thick at unit scale (measured); [`clean_transform`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L52-L79) | f64 in tile-local frames with an **f64 frame origin**, camera-relative f32 only at upload (spec §5, ADR-0006). The local-frame probe shows the mitigation works; Blender cannot hold the frame because `loc` is float32. **P-05** |
| Exactness silently degrades to a heuristic on imperfect input | The PWN test gates the exact branch; failing it falls back to float ray casting, with no error and no change of return type | [`mesh_boolean.cc#L3590-L3600`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L3590-L3600), `Array<float> in_shape` at [L2750](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/blenlib/intern/mesh_boolean.cc#L2750); the API's own "may or may not work in the way the user hopes" | A degraded path is a **different result value**, never the same one: the caller learns which algorithm ran (spec §12). Healing is explicit and named (spec §4). **P-01** |
| A boolean returns different geometry for identical input | Threaded arrangement and threaded post-processing without a canonical ordering at every merge point | Probe E: 2 distinct topologies in 10 runs, and a third across runs (Fast, measured); [#143644](https://projects.blender.org/blender/blender/issues/143644) (Manifold, developer-confirmed as threading) | Determinism is an invariant, not an aspiration: parallel work is over independent handles with results merged in a canonical order (spec §6). A determinism test belongs in the kernel's own suite from the first boolean. **P-16 — added by this note** |
| A failed operation returns the unmodified first operand and a console message | The error is reported out-of-band while the return value stays a plausible mesh | Manifold on `near_degenerate_triangle`: "Cannot execute, non-manifold inputs", output = operand A (measured); [`MOD_boolean.cc#L492-L501`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/modifiers/intern/MOD_boolean.cc#L492-L501) | Operations return a result value carrying the failure; there is no "returned the input" path (spec §12). Compare [`occt.md`](occt.md) on IfcOpenShell's first-operand fallback — the same anti-pattern, independently arrived at, which is why it needs an explicit rule. **P-01** |
| One dragged element costs the whole scene | The evaluation graph's unit is the datablock, and its cost per update scales with datablock count | 16.8 ms for one move at 10k objects and 295 ms at 100k, vs 0.013 ms for the same triangles in one object; ~62 kB of memory per object (measured); [#156584](https://projects.blender.org/blender/blender/issues/156584) | Structure-of-arrays with generational handles, instancing-first GPU layouts, and an evaluation graph whose nodes are not forced to be one-per-element (spec §3, §6). **P-07** |
| A solver that cannot fail | The Float branch sets `NoError` unconditionally | [`geometry/intern/mesh_boolean.cc#L1202-L1208`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/geometry/intern/mesh_boolean.cc#L1202-L1208); measured empty unions with no error | Every operation returns a typed result; "no error" is a value that must be justified, not a default. **P-01** |
| The robust algorithm requires manifold input and refuses real models | The Manifold library's correctness proof assumes it | 10/10 on our set, but refused the T-junction operand outright (measured); [#139370](https://projects.blender.org/blender/blender/issues/139370), [#140590](https://projects.blender.org/blender/blender/issues/140590), [#144698](https://projects.blender.org/blender/blender/issues/144698) | Mesh validity is checked explicitly and healing is an explicit operation; the arrangement-based boolean tolerates non-manifold input where the literature allows (spec §4, §12). **P-09** |

### Corrections and additions this note makes to `problems.md`

- **P-01** moves from *partly shown* to **shown**, and its "Seen in" is corrected. The row credited
  "Blender's former Carve boolean"; the accurate statement is that *every* Blender boolean —
  Carve, BMesh/Fast, and the exact one — has failed on touching and coplanar input, and the
  maintainer who removed Carve said the two floating-point implementations shared "the same level
  of limitations about manifold meshes and touching edges". The exact solver fixed the coplanar
  class and left a touching-vertex case that loses an operand.
- **P-05** moves from *shown (phase 1)* — where the evidence was a general argument about float32 —
  to **shown (measured)**, with a number: 0.0348 m at 500 km, against a float32 ULP of 0.03125 m.
- **P-07** moves from *hypothesis* to **shown for the Blender half**. The row's parenthetical
  "(R-03 unresolved whether Blender or Bonsai)" is resolved in one direction: measured with no
  add-on in the process, 10k objects already cost a frame budget per single-object update. What
  remains unresolved is the viewport, which a headless driver cannot measure.
- **P-09** gains its first evidence: Blender's Manifold solver refuses non-manifold input by design
  and returns the first operand, and three tracker issues show the same constraint meeting real
  models.
- **P-16 is new**: "the same operation on the same input returns different geometry on different
  runs". It had no row, we measured it in the Fast solver, and Blender's own developers confirmed
  the same class in the Manifold solver. It is added, following the precedent of
  [`occt.md`](occt.md)'s P-15, because the *avoid* table above needed a target for it.

## Sources

Primary, at commit `a37564c4df7a9b604809e5192918400e46a0205f` (tag `v5.0.0`) — individual file and
line links inline above:

- [Blender repository at the pinned commit](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f)
- [Boolean modifier manual](https://projects.blender.org/blender/blender-manual/src/commit/ce0478a5b9329738e2cde9b7cbc22dd93500a8b8/manual/modeling/modifiers/generate/booleans.rst)
  at `blender-manual` commit `ce0478a5b9329738e2cde9b7cbc22dd93500a8b8`
- [Blender 2.91 release notes — Modeling](https://projects.blender.org/blender/blender-developer-docs/src/commit/fb9a26df737598c4e538ba8f57daf66ba2151057/docs/release_notes/2.91/modeling.md)
  at `blender-developer-docs` commit `fb9a26df7375`
- Commits: [`e0597baed57f`](https://projects.blender.org/blender/blender/commit/e0597baed57fa7a9dfaf6dff6d0fa120784d21ea)
  (Carve removed, 2018-02-07),
  [`9e09b5c418c0`](https://projects.blender.org/blender/blender/commit/9e09b5c418c0a436e3c84ccf38c065527988b0a0)
  (exact boolean merged, 2020-08-28),
  [`de21ab418d69`](https://projects.blender.org/blender/blender/commit/de21ab418d69ca82a07ec7c836b1deca09bbd57f)
  (`Self` option, 2020-09-07),
  [`dd559259d84f`](https://projects.blender.org/blender/blender/commit/dd559259d84f)
  (Manifold solver, 2025-04-22)

The algorithm's source paper, which is what "borrow from" actually refers to:

- Zhou, Grinspun, Zorin, Jacobson, *Mesh Arrangements for Solid Geometry*, SIGGRAPH 2016 —
  <http://www.cs.columbia.edu/cg/mesh-arrangements/mesh-arrangements-for-solid-geometry-siggraph-2016-zhou-et-al.pdf>

Issue tracker — every ticket linked inline in §Known problems; the tracker root is
<https://projects.blender.org/blender/blender/issues>. Its HTML pages return HTTP 403 to automated
fetches, so every issue above was read through the public API at
`https://projects.blender.org/api/v1/repos/blender/blender/issues/<n>` and
`/issues/<n>/comments`. That is a traceability note for anyone re-deriving this section: the URLs
in the table are for humans, the API is what a script must use.

Measurements — the reproducible record, not a summary:

- [`spikes/boolean-torture/results/blender.md`](../../../spikes/boolean-torture/results/blender.md)
- [`spikes/precision-set/results/blender.md`](../../../spikes/precision-set/results/blender.md)
- [`spikes/blender-ceiling/results/blender.md`](../../../spikes/blender-ceiling/results/blender.md)
