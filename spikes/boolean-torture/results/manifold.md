# Boolean torture set — Manifold raw results

Produced by [`../manifold_driver.py`](../manifold_driver.py). This file is raw data for
`../FINDINGS.md` (assembled once every candidate has run) and for
[`../../../docs/research/kernels/manifold.md`](../../../docs/research/kernels/manifold.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-11

## Environment

| Item | Value |
|---|---|
| python | `3.12.10` |
| platform | `Windows 11 (AMD64)` |
| cpu | `Intel(R) Core(TM) i9-14900HX` |
| installed RAM | `32 GB` |
| manifold3d | `3.5.3` |
| manifold source tag | `v3.5.3`, commit `0edd9d54876f3135e431575214dd6d8a72866fee` |
| build flags of the wheel | `MANIFOLD_PAR=ON` (TBB), `MANIFOLD_CROSS_SECTION=ON`, `MANIFOLD_PYBIND=ON` (`pyproject.toml` at the tag) |
| numpy | `2.3.5` (required by manifold3d) |
| repeats per timing | 5 (median reported) |

The standalone library measured here is **v3.5.3**. Blender 5.0, whose Manifold
solver rows are in [`results/blender.md`](blender.md), bundles **v3.2.1**
(`MANIFOLD_VERSION v3.2.1` in Blender's `build_files/build_environment/cmake/versions.cmake`
at the build's own commit), and feeds it float32 vertex positions. Both differences are
held constant here by measuring the f32 and the f64 input path separately.

## Construction of the operands

`manifold3d.Mesh` (float32 positions, uint32 indices) and `manifold3d.Mesh64`
(float64, uint64) into `Manifold(...)`, from `reference/boolean_torture_set.py`
verbatim: no welding, no merge vectors, no repair. *Components* is
`Manifold.decompose()`, i.e. how many disconnected solids the one input mesh
became. *Volume* is `reference.signed_volume` over the triangles exported by
`to_mesh64()`. *Tolerance* is `Manifold.get_tolerance()` after construction.

| Case | Operand | Precision | Status | Verts | Tris | Components | Volume | Tolerance |
|---|---|---|---|---|---|---|---|---|
| `disjoint` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `disjoint` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `disjoint` | B | f64 | NoError | 8 | 12 | 1 | 1 | 5e-12 |
| `disjoint` | B | f32 | NoError | 8 | 12 | 1 | 1 | 5.96e-07 |
| `overlap_half` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `overlap_half` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `overlap_half` | B | f64 | NoError | 8 | 12 | 1 | 1 | 1.5e-12 |
| `overlap_half` | B | f32 | NoError | 8 | 12 | 1 | 1 | 1.788e-07 |
| `coplanar_faces` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `coplanar_faces` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `coplanar_faces` | B | f64 | NoError | 8 | 12 | 1 | 1 | 2e-12 |
| `coplanar_faces` | B | f32 | NoError | 8 | 12 | 1 | 1 | 2.384e-07 |
| `shared_edge` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `shared_edge` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `shared_edge` | B | f64 | NoError | 8 | 12 | 1 | 1 | 2e-12 |
| `shared_edge` | B | f32 | NoError | 8 | 12 | 1 | 1 | 2.384e-07 |
| `touching_vertex` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `touching_vertex` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `touching_vertex` | B | f64 | NoError | 8 | 12 | 1 | 1 | 2e-12 |
| `touching_vertex` | B | f32 | NoError | 8 | 12 | 1 | 1 | 2.384e-07 |
| `identical` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `identical` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `identical` | B | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `identical` | B | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `contained` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `contained` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `contained` | B | f64 | NoError | 8 | 12 | 1 | 0.125 | 7.5e-13 |
| `contained` | B | f32 | NoError | 8 | 12 | 1 | 0.125 | 8.941e-08 |
| `sliver` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `sliver` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `sliver` | B | f64 | NoError | 8 | 12 | 1 | 9.99999999474e-08 | 1e-12 |
| `sliver` | B | f32 | NoError | 8 | 12 | 1 | 1.19209289551e-07 | 1.192e-07 |
| `near_degenerate_triangle` | A | f64 | NoError | 8 | 12 | 1 | 1 | 1e-12 |
| `near_degenerate_triangle` | A | f32 | NoError | 8 | 12 | 1 | 1 | 1.192e-07 |
| `near_degenerate_triangle` | B | f64 | **NotManifold** | - | - | - | - | - |
| `near_degenerate_triangle` | B | f32 | **NotManifold** | - | - | - | - | - |
| `wall_with_openings` | A | f64 | NoError | 8 | 12 | 1 | 9 | 1e-11 |
| `wall_with_openings` | A | f32 | NoError | 8 | 12 | 1 | 9.00000035763 | 1.192e-06 |
| `wall_with_openings` | B | f64 | NoError | 96 | 144 | 12 | 9 | 9.9e-12 |
| `wall_with_openings` | B | f32 | NoError | 96 | 144 | 12 | 8.99999948591 | 1.18e-06 |

## Boolean results

One row per case × setting. *Valid?* is this driver's own check on the exported
result mesh — every directed edge used once with a matching opposite halfedge
(closed, manifold and consistently wound), no loose vertices, no triangle below
1e-14 m² — plus `Manifold.status()` and `is_empty()`. *Identity* is
`|V(A) + V(B) − (V(∪) + V(∩))|` computed from the **measured** operand volumes.
Times are milliseconds, median of the repeats, union / intersection; each repeat
rebuilds both operands and the timing includes the `status()` call that forces
the deferred CSG node to evaluate.

| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |
|---|---|---|---|---|---|---|---|
| `disjoint` | f64, default tolerance | yes | 2 | 0 | 0 | 0.015 / 0.003 | tol(A)=1e-12, tol(B)=5e-12 |
| `disjoint` | f64, tolerance=1e-9 | yes | 2 | 0 | 0 | 0.023 / 0.002 | tol(A)=1e-09, tol(B)=1e-09 |
| `disjoint` | f64, tolerance=1e-6 | yes | 2 | 0 | 0 | 0.013 / 0.002 | tol(A)=1e-06, tol(B)=1e-06 |
| `disjoint` | f32, default tolerance | yes | 2 | 0 | 0 | 0.013 / 0.002 | tol(A)=1.192e-07, tol(B)=5.96e-07 |
| `overlap_half` | f64, default tolerance | yes | 1.5 | 0.5 | 0 | 0.293 / 0.093 | tol(A)=1e-12, tol(B)=1.5e-12 |
| `overlap_half` | f64, tolerance=1e-9 | yes | 1.5 | 0.5 | 0 | 0.171 / 0.125 | tol(A)=1e-09, tol(B)=1e-09 |
| `overlap_half` | f64, tolerance=1e-6 | yes | 1.5 | 0.5 | 0 | 0.194 / 0.074 | tol(A)=1e-06, tol(B)=1e-06 |
| `overlap_half` | f32, default tolerance | yes | 1.5 | 0.5 | 0 | 0.148 / 0.109 | tol(A)=1.192e-07, tol(B)=1.788e-07 |
| `coplanar_faces` | f64, default tolerance | yes | 2 | 0 | 0 | 0.125 / 0.043 | ∩ is a non-empty zero-volume shell (4 tris); tol(A)=1e-12, tol(B)=2e-12 |
| `coplanar_faces` | f64, tolerance=1e-9 | yes | 2 | 0 | 0 | 0.116 / 0.064 | ∩ is a non-empty zero-volume shell (4 tris); tol(A)=1e-09, tol(B)=1e-09 |
| `coplanar_faces` | f64, tolerance=1e-6 | yes | 2 | 0 | 0 | 0.229 / 0.059 | ∩ is a non-empty zero-volume shell (4 tris); tol(A)=1e-06, tol(B)=1e-06 |
| `coplanar_faces` | f32, default tolerance | yes | 2 | 0 | 0 | 0.139 / 0.063 | ∩ is a non-empty zero-volume shell (4 tris); tol(A)=1.192e-07, tol(B)=2.384e-07 |
| `shared_edge` | f64, default tolerance | yes | 2 | 0 | 0 | 0.113 / 0.090 | tol(A)=1e-12, tol(B)=2e-12 |
| `shared_edge` | f64, tolerance=1e-9 | yes | 2 | 0 | 0 | 0.169 / 0.073 | tol(A)=1e-09, tol(B)=1e-09 |
| `shared_edge` | f64, tolerance=1e-6 | yes | 2 | 0 | 0 | 0.114 / 0.072 | tol(A)=1e-06, tol(B)=1e-06 |
| `shared_edge` | f32, default tolerance | yes | 2 | 0 | 0 | 0.122 / 0.086 | tol(A)=1.192e-07, tol(B)=2.384e-07 |
| `touching_vertex` | f64, default tolerance | yes | 2 | 0 | 0 | 0.106 / 0.087 | tol(A)=1e-12, tol(B)=2e-12 |
| `touching_vertex` | f64, tolerance=1e-9 | yes | 2 | 0 | 0 | 0.083 / 0.071 | tol(A)=1e-09, tol(B)=1e-09 |
| `touching_vertex` | f64, tolerance=1e-6 | yes | 2 | 0 | 0 | 0.091 / 0.056 | tol(A)=1e-06, tol(B)=1e-06 |
| `touching_vertex` | f32, default tolerance | yes | 2 | 0 | 0 | 0.069 / 0.065 | tol(A)=1.192e-07, tol(B)=2.384e-07 |
| `identical` | f64, default tolerance | yes | 1 | 1 | 0 | 0.173 / 0.054 | tol(A)=1e-12, tol(B)=1e-12 |
| `identical` | f64, tolerance=1e-9 | yes | 1 | 1 | 0 | 0.142 / 0.046 | tol(A)=1e-09, tol(B)=1e-09 |
| `identical` | f64, tolerance=1e-6 | yes | 1 | 1 | 0 | 0.169 / 0.066 | tol(A)=1e-06, tol(B)=1e-06 |
| `identical` | f32, default tolerance | yes | 1 | 1 | 0 | 0.157 / 0.053 | tol(A)=1.192e-07, tol(B)=1.192e-07 |
| `contained` | f64, default tolerance | yes | 1 | 0.125 | 0 | 0.011 / 0.014 | tol(A)=1e-12, tol(B)=7.5e-13 |
| `contained` | f64, tolerance=1e-9 | yes | 1 | 0.125 | 0 | 0.011 / 0.010 | tol(A)=1e-09, tol(B)=1e-09 |
| `contained` | f64, tolerance=1e-6 | yes | 1 | 0.125 | 0 | 0.011 / 0.010 | tol(A)=1e-06, tol(B)=1e-06 |
| `contained` | f32, default tolerance | yes | 1 | 0.125 | 0 | 0.012 / 0.014 | tol(A)=1.192e-07, tol(B)=8.941e-08 |
| `sliver` | f64, default tolerance | yes | 1 | 9.99999999474e-08 | 4.44e-16 | 0.224 / 0.137 | tol(A)=1e-12, tol(B)=1e-12 |
| `sliver` | f64, tolerance=1e-9 | yes | 1 | 9.99999999474e-08 | 4.44e-16 | 0.178 / 0.099 | tol(A)=1e-09, tol(B)=1e-09 |
| `sliver` | f64, tolerance=1e-6 | ∪ ok; ∩: **no** — empty result | 1 | 0 | 0 | 0.004 / 0.002 | Δ∩=-1e-07; tol(A)=1e-06, tol(B)=1e-06 |
| `sliver` | f32, default tolerance | yes | 1 | 1.19209289551e-07 | 0 | 0.186 / 0.137 | Δ∩=1.92e-08; tol(A)=1.192e-07, tol(B)=1.192e-07 |
| `near_degenerate_triangle` | f64, default tolerance | ∪: **no** — status `NotManifold`; ∩: **no** — status `NotManifold` | 0 | 0 | 1 | 0.003 / 0.003 | Δ∪=-1; Δ∩=-1; operand B rejected: `NotManifold`; tol(A)=1e-12, tol(B)=0 |
| `near_degenerate_triangle` | f64, tolerance=1e-9 | ∪: **no** — status `NotManifold`; ∩: **no** — status `NotManifold` | 0 | 0 | 1 | 0.003 / 0.002 | Δ∪=-1; Δ∩=-1; operand B rejected: `NotManifold`; tol(A)=1e-09, tol(B)=-1 |
| `near_degenerate_triangle` | f64, tolerance=1e-6 | ∪: **no** — status `NotManifold`; ∩: **no** — status `NotManifold` | 0 | 0 | 1 | 0.002 / 0.002 | Δ∪=-1; Δ∩=-1; operand B rejected: `NotManifold`; tol(A)=1e-06, tol(B)=-1 |
| `near_degenerate_triangle` | f32, default tolerance | ∪: **no** — status `NotManifold`; ∩: **no** — status `NotManifold` | 0 | 0 | 1 | 0.002 / 0.002 | Δ∪=-1; Δ∩=-1; operand B rejected: `NotManifold`; tol(A)=1.192e-07, tol(B)=0 |
| `wall_with_openings` | f64, default tolerance | yes | 12.6 | 5.4 | 3.55e-14 | 0.997 / 0.650 | tol(A)=1e-11, tol(B)=9.9e-12 |
| `wall_with_openings` | f64, tolerance=1e-9 | yes | 12.6 | 5.4 | 3.55e-14 | 1.000 / 0.604 | tol(A)=1e-09, tol(B)=1e-09 |
| `wall_with_openings` | f64, tolerance=1e-6 | yes | 12.6 | 5.4 | 3.55e-14 | 1.104 / 0.670 | tol(A)=1e-06, tol(B)=1e-06 |
| `wall_with_openings` | f32, default tolerance | yes | 12.6000000179 | 5.39999982566 | 2.49e-14 | 0.990 / 0.556 | Δ∪=1.79e-08; Δ∩=-1.74e-07; tol(A)=1.192e-06, tol(B)=1.18e-06 |

**Summary:** 35 of 40 case×setting combinations produced a result this
driver's check accepts for both the union and the intersection.

*Valid* and *correct* are different questions and are counted separately, on the
same definitions [`results/blender.md`](blender.md) uses. *Correct* is both volumes
within `1e-06 * max(1.0, abs(expected))` of the analytic expectation — relative above
1 m³, an absolute floor below it, so a case whose expected volume is 0 or 1e-07 m³
is not judged on a relative error it cannot meet. The Δ notes above use 1e-09 instead.

| Setting | Valid (closed manifold) | Numerically correct | Worst identity residual (refusals excluded) |
|---|---|---|---|
| f64, default tolerance | 9 / 10 | 9 / 10 | 3.55e-14 |
| f64, tolerance=1e-9 | 9 / 10 | 9 / 10 | 3.55e-14 |
| f64, tolerance=1e-6 | 8 / 10 | 9 / 10 | 3.55e-14 |
| f32, default tolerance | 9 / 10 | 9 / 10 | 2.49e-14 |

The `tol(B)` values on the refused rows are not driver artefacts. `0` is the
`tolerance` field of the input `Mesh` (the binding's default), kept by the
`Mesh -> Impl` constructor before it reaches `MakeEmpty(NotManifold)`; `-1` is the
uninitialised `Impl::tolerance_`, which is what `SetTolerance` on an already-errored
Manifold returns via `PropagateStatus`
([`manifold.cpp#L367-L383`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/manifold.cpp#L367-L383),
[`impl.h#L57-L58`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/impl.h#L57-L58)).

## Probe A — the twelve-shell operand

`wall_with_openings` B is **one mesh with twelve disconnected closed shells**, the
same construction `results/blender.md` used. This probe records whether Manifold
accepts it as a single `Manifold` and what `decompose()` then reports, including
the `DIFFERENCE` operation the case actually models. The analytic expectation for
the difference is V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.

| Precision | Operation | Components in B | V(result) | Verts | Tris | Components in result | Valid? |
|---|---|---|---|---|---|---|---|
| f64 | union | 12 | 12.6 | 200 | 396 | 1 | yes |
| f64 | intersection | 12 | 5.4 | 96 | 144 | 12 | yes |
| f64 | difference | 12 | 3.6 | 104 | 252 | 1 | yes |
| f32 | union | 12 | 12.6000000179 | 200 | 396 | 1 | yes |
| f32 | intersection | 12 | 5.39999982566 | 96 | 144 | 12 | yes |
| f32 | difference | 12 | 3.60000053197 | 104 | 252 | 1 | yes |

## Probe B — the 1e-7 m slab against the tolerance

`sliver` B is a 1 m × 1 m × 1e-7 m slab. Manifold's default epsilon is
`kPrecision * bBox.Scale()` with `kPrecision = 1e-12`, and `Box::Scale()` is the
largest absolute coordinate, not the diagonal. `set_tolerance` above that value
runs simplification. This probe raises the tolerance past the slab's thickness on
both input paths and reports what survives.

| Precision | Requested tolerance | tol(B) after | V(B) | V(A∩B) | Tris in A∩B |
|---|---|---|---|---|---|
| f64 | default | 1e-12 | 9.99999999474e-08 | 9.99999999474e-08 | 12 |
| f64 | 1e-09 | 1e-09 | 9.99999999474e-08 | 9.99999999474e-08 | 12 |
| f64 | 1e-08 | 1e-08 | 9.99999999474e-08 | 9.99999999474e-08 | 12 |
| f64 | 1e-07 | - | **empty**, status `NoError` | - | - |
| f64 | 1e-06 | - | **empty**, status `NoError` | - | - |
| f64 | 0.0001 | - | **empty**, status `NoError` | - | - |
| f32 | default | 1.192e-07 | 1.19209289551e-07 | 1.19209289551e-07 | 12 |
| f32 | 1e-09 | 1e-09 | 1.19209289551e-07 | 1.19209289551e-07 | 12 |
| f32 | 1e-08 | 1e-08 | 1.19209289551e-07 | 1.19209289551e-07 | 12 |
| f32 | 1e-07 | 1e-07 | 1.19209289551e-07 | 1.19209289551e-07 | 12 |
| f32 | 1e-06 | - | **empty**, status `NoError` | - | - |
| f32 | 0.0001 | - | **empty**, status `NoError` | - | - |

## Probe C — the T-junction operand

`near_degenerate_triangle` B has a vertex lying *on* an edge (the reference set
splits the cube's top face by inserting a vertex on the edge v5→v6), so one
halfedge has no twin: a T-junction, and not a manifold mesh. Blender's Manifold
solver refuses it and returns the unmodified first operand
([`results/blender.md`](blender.md)). This probe records what the standalone
library does, and whether the `Merge` helper the README offers for "slightly
non-manifold meshes" repairs it.

| Precision | Input | `status()` | `is_empty()` | Tris |
|---|---|---|---|---|
| f64 | operand B alone | `NotManifold` | True | 0 |
| f64 | A + B | `NotManifold` | True | 0 |
| f64 | A ^ B | `NotManifold` | True | 0 |
| f32 | operand B alone | `NotManifold` | True | 0 |
| f32 | A + B | `NotManifold` | True | 0 |
| f32 | A ^ B | `NotManifold` | True | 0 |
| f64 | operand B after `Mesh64.merge()` | `NotManifold` | True | 0 |

`Mesh64.merge()` reported that it changed the mesh: **True**.

## Probe D — run-to-run determinism

The same operands, rebuilt from the reference set and run N times in one process,
on the f64 path at default tolerance. *Signatures* is the number of distinct
`(verts, tris, volume)` triples observed; a deterministic library produces exactly
one. This is asked because Blender's tracker carries a non-determinism that was
reproduced in this library and fixed upstream
([#143644](https://projects.blender.org/blender/blender/issues/143644)), and
because a kernel whose output depends on thread scheduling cannot be diffed,
cached or regression-tested. The wheel is built with `MANIFOLD_PAR=ON`, so TBB is
in the process.

| Case | Op | Runs | Signatures | Distinct results |
|---|---|---|---|---|
| `overlap_half` | union | 10 | 1 | 16v/28f/V=1.5 x10 |
| `wall_with_openings` | union | 10 | 1 | 200v/396f/V=12.6 x10 |
| `wall_with_openings` | difference | 10 | 1 | 104v/252f/V=3.6 x10 |
| `sliver` | intersection | 10 | 1 | 8v/12f/V=9.99999999474e-08 x10 |

## Probe E — cancellation and progress

`ExecutionContext` (`Cancel`, `Cancelled`, `Progress`,
[`common.h#L250-L299`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/common.h#L250-L299))
is the API `problems.md` P-15 asks every candidate for: a way to bound a runaway
operation from outside it. Booleans are deferred, so the context is attached to the
tree and consumed by `Status()`. This probe runs the twelve-opening wall's union with
a context attached, and again with the context cancelled beforehand. `Progress()`
returns 1.0 when no work has been scheduled, which is why the uncancelled row starts
at 1.0 — that is documented behaviour, not a reading error.

| Run | `status()` | `is_empty()` | Tris | `progress()` before → after |
|---|---|---|---|---|
| union, context attached, not cancelled | `NoError` | False | 396 | 1 → 1 |
| union, context cancelled before evaluation | `Cancelled` | True | 0 | 1 → 0 |
