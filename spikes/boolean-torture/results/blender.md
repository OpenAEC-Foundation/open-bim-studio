# Boolean torture set — Blender raw results

Produced by [`../blender_driver.py`](../blender_driver.py). This file is raw data for
`../FINDINGS.md` (assembled once every candidate has run) and for
[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-11

## Environment

| Item | Value |
|---|---|
| blender | `5.0.0` |
| build hash | `a37564c4df7a` |
| build date | `2025-11-18 11:06:54` |
| bundled python | `3.11.13` |
| platform | `Windows 10.0.26200 (AMD64)` |
| processor | `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel` |
| cpu | `Intel(R) Core(TM) i9-14900HX` |
| installed RAM | `32 GB` |
| solver enum | `FLOAT, EXACT, MANIFOLD` |
| solvers measured | `EXACT, FLOAT, MANIFOLD` |
| default solver | `EXACT` |
| default `double_threshold` | `9.99999997475e-07` |
| repeats per timing | 5 (median reported) |
| startup | `--factory-startup` (no add-ons) |

Vertex positions are **float32** in Blender's mesh storage; this driver reads them
back into f64 Python floats for the volume computation, so every number below carries
whatever float32 already cost. At unit scale that is ~6e-8 relative; the precision set
([`../../precision-set/results/blender.md`](../../precision-set/results/blender.md))
is where it stops being negligible.

## Construction of the operands

`Mesh.from_pydata` from `reference/boolean_torture_set.py` verbatim, no welding and no
triangulation. *Shells* is the number of connected components — the `wall_with_openings`
tool is **one mesh object with twelve disconnected shells**, not a compound of twelve
objects. `validate()` is Blender's own `Mesh.validate()`; it returns True when it
*changed* the mesh, and it ran on throwaway copies that never fed a boolean.

| Case | Operand | Verts | Faces | Shells | Closed? | Manifold? | Volume | `validate()` changed? |
|---|---|---|---|---|---|---|---|---|
| `disjoint` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `disjoint` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `overlap_half` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `overlap_half` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `coplanar_faces` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `coplanar_faces` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `shared_edge` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `shared_edge` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `touching_vertex` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `touching_vertex` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `identical` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `identical` | B | 8 | 12 | 1 | yes | yes | 1 | no |
| `contained` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `contained` | B | 8 | 12 | 1 | yes | yes | 0.125 | no |
| `sliver` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `sliver` | B | 8 | 12 | 1 | yes | yes | 1.19209289551e-07 | no |
| `near_degenerate_triangle` | A | 8 | 12 | 1 | yes | yes | 1 | no |
| `near_degenerate_triangle` | B | 9 | 13 | 1 | no | no | 1 | no |
| `wall_with_openings` | A | 8 | 12 | 1 | yes | yes | 9.00000035763 | no |
| `wall_with_openings` | B | 96 | 144 | 12 | yes | yes | 8.99999948591 | no |

Two operand rows are findings in themselves and are read, not assumed:

* `near_degenerate_triangle` B is **not manifold as a mesh**. The reference set splits
  the cube's top face by inserting a vertex *on* the edge v5→v6, which leaves that edge
  bounded by one face on the side quad and by two shorter edges on the top: a T-junction.
  A B-rep kernel sews it into a valid solid; a mesh kernel sees non-manifold input. Which
  solvers refuse it is recorded in the table below.
* `sliver` B has volume 1.19209289551e-07, not the 1e-7 the reference set specifies.
  Nothing has run yet: `0.5 + 1e-7` is not representable in float32, and the slab
  became 19% thicker on its way into the mesh. This is P-05 at **unit** scale.

## Boolean results

One row per case × solver. *Valid?* is this driver's own check on the result mesh:
closed (no boundary or wire edges), manifold (every edge shared by exactly two faces),
no loose vertices, no faces below 1e-14 m², and `Mesh.validate()` making no correction.
*Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` computed from the **measured** operand
volumes, so it isolates the boolean from the operands. Times are milliseconds, median of
5 fresh runs, union / intersection; the parenthesised value is the modifier's own
self-reported `execution_time`, which excludes the evaluated-mesh copy.

| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |
|---|---|---|---|---|---|---|---|
| `disjoint` | Exact | yes | 2 | 0 | 0 | 0.74 / 0.66 (0.328 / 0.195) | - |
| `disjoint` | Fast (float) | yes | 2 | 0 | 0 | 0.31 / 0.32 (0.0751 / 0.0717) | threshold=1e-06 |
| `disjoint` | Manifold | yes | 2 | 0 | 0 | 0.48 / 0.32 (0.188 / 0.108) | - |
| `overlap_half` | Exact | yes | 1.5 | 0.5 | 0 | 3.21 / 3.31 (3 / 3.1) | - |
| `overlap_half` | Fast (float) | ∪: **no** — 0 boundary edges, 26 non-manifold edges, 26 wire edges; ∩: **no** — 0 boundary edges, 25 non-manifold edges, 25 wire edges | 1 | 1 | 0 | 0.55 / 0.48 (0.302 / 0.278) | Δ∪=-0.5, Δ∩=0.5, threshold=1e-06 |
| `overlap_half` | Manifold | yes | 1.5 | 0.5 | 0 | 0.63 / 0.66 (0.408 / 0.418) | - |
| `coplanar_faces` | Exact | yes | 2 | 0 | 0 | 1.43 / 1.21 (1.21 / 1.02) | - |
| `coplanar_faces` | Fast (float) | ∪: **no** — 0 boundary edges, 4 non-manifold edges, 4 wire edges; ∩ ok | 2 | 0 | 0 | 0.38 / 0.36 (0.143 / 0.118) | threshold=1e-06 |
| `coplanar_faces` | Manifold | yes | 2 | 0 | 0 | 0.49 / 0.38 (0.261 / 0.137) | - |
| `shared_edge` | Exact | ∪: **no** — 1 non-manifold edges; ∩ ok | 2 | 0 | 0 | 1.71 / 1.73 (1.51 / 1.48) | - |
| `shared_edge` | Fast (float) | yes | 2 | 0 | 0 | 0.27 / 0.26 (0.0848 / 0.0773) | threshold=1e-06 |
| `shared_edge` | Manifold | yes | 2 | 0 | 0 | 0.46 / 0.30 (0.252 / 0.122) | - |
| `touching_vertex` | Exact | yes | 1 | 0 | 1 | 1.59 / 1.30 (1.24 / 1.09) | Δ∪=-1 |
| `touching_vertex` | Fast (float) | yes | 2 | 0 | 0 | 0.26 / 0.25 (0.0818 / 0.0618) | threshold=1e-06 |
| `touching_vertex` | Manifold | yes | 2 | 0 | 0 | 0.57 / 0.42 (0.296 / 0.218) | - |
| `identical` | Exact | yes | 1 | 1 | 0 | 2.81 / 2.91 (2.6 / 2.69) | - |
| `identical` | Fast (float) | ∪: **no** — 8 boundary edges, 8 non-manifold edges; ∩: **no** — 8 boundary edges, 8 non-manifold edges | 0 | 2 | 0 | 0.29 / 0.30 (0.106 / 0.105) | Δ∪=-1, Δ∩=1, threshold=1e-06 |
| `identical` | Manifold | yes | 1 | 1 | 0 | 0.44 / 0.50 (0.252 / 0.309) | - |
| `contained` | Exact | yes | 1 | 0.125 | 0 | 0.48 / 0.47 (0.281 / 0.273) | - |
| `contained` | Fast (float) | yes | 1 | 0.125 | 0 | 0.32 / 0.25 (0.0686 / 0.0628) | threshold=1e-06 |
| `contained` | Manifold | yes | 1 | 0.125 | 0 | 0.39 / 0.52 (0.181 / 0.27) | - |
| `sliver` | Exact | ∪: **no** — 4 zero-area faces; ∩: **no** — 4 zero-area faces | 1 | 1.19209289551e-07 | 0 | 3.45 / 3.62 (3.24 / 3.4) | Δ∩=1.92e-08 |
| `sliver` | Fast (float) | ∪: **no** — 0 boundary edges, 16 non-manifold edges, 16 wire edges; ∩: **no** — 0 boundary edges, 16 non-manifold edges, 16 wire edges | 1 | 1.19209289551e-07 | 0 | 0.37 / 0.41 (0.176 / 0.204) | Δ∩=1.92e-08, threshold=1e-06 |
| `sliver` | Manifold | yes | 1 | 1.19209289551e-07 | 0 | 0.43 / 0.48 (0.235 / 0.279) | Δ∩=1.92e-08 |
| `near_degenerate_triangle` | Exact | yes | 1 | 1 | 0 | 3.31 / 3.15 (3.03 / 2.95) | - |
| `near_degenerate_triangle` | Fast (float) | ∪: **no** — 8 boundary edges, 8 non-manifold edges; ∩: **no** — 11 boundary edges, 11 non-manifold edges | 0 | 2 | 0 | 0.33 / 0.40 (0.124 / 0.202) | Δ∪=-1, Δ∩=1, threshold=1e-06 |
| `near_degenerate_triangle` | Manifold | yes | 1 | 1 | 0 | 0.45 / 0.35 (0.231 / 0.131) | `WARNING Object: "A", Modifier: "bool", Cannot execute, non-manifold inputs`, `WARNING Object: "A", Modifier: "bool", Cannot execute, non-manifold inputs` |
| `wall_with_openings` | Exact | yes | 12.6000000179 | 5.39999982566 | 3.2e-14 | 17.80 / 18.26 (17.4 / 17.9) | Δ∪=1.79e-08, Δ∩=-1.74e-07 |
| `wall_with_openings` | Fast (float) | yes | 12.5999999541 | 5.39999939549 | 4.94e-07 | 1.13 / 1.18 (0.88 / 0.918) | Δ∪=-4.59e-08, Δ∩=-6.05e-07, threshold=1e-06 |
| `wall_with_openings` | Manifold | yes | 12.6000000179 | 5.39999982566 | 1.42e-14 | 1.91 / 1.43 (1.68 / 1.18) | Δ∪=1.79e-08, Δ∩=-1.74e-07 |

**Summary:** 23 of 30 case×solver combinations produced a closed manifold result for
both the union and the intersection.

*Valid* and *correct* are different questions and are counted separately. A result can
be a perfectly valid closed manifold mesh of the wrong volume, and — the `shared_edge`
and `touching_vertex` cases show it — the mathematically correct union of two solids
meeting at an edge or a point is **not** manifold, so a solver that returns the right
volume there is marked invalid by the topological check and is not wrong to be.
*Correct* is both volumes within `1e-6 * max(1.0, abs(expected))` of the analytic
expectation — relative for expectations above 1 m³, and an absolute floor of 1e-6 m³
below it, so a case whose expected volume is 0 or 1.2e-07 m³ is not judged on a
relative error it cannot meet. The Δ notes in the table above use the same shape with
1e-9 instead of 1e-6.

| Solver | Valid (closed manifold) | Numerically correct | Worst identity residual |
|---|---|---|---|
| Exact | 8 / 10 | 9 / 10 | 1 |
| Fast (float) | 5 / 10 | 7 / 10 | 4.94e-07 |
| Manifold | 10 / 10 | 10 / 10 | 1.42e-14 |

Cases each solver got numerically wrong:

* **Exact** — `touching_vertex`
* **Fast (float)** — `overlap_half`, `identical`, `near_degenerate_triangle`
* **Manifold** — none

## Probe A — the `sliver` slab against the overlap threshold

`sliver` B is a 1 m × 1 m × 1e-7 m slab: **thinner than the Fast solver's default
`double_threshold` of 1e-6 m** (the manual's *Overlap Threshold*). This probe varies the
threshold on the Fast solver only — the Exact and Manifold solvers ignore it — and
reports what the intersection returns. Expected intersection volume is 1e-7 m³.

| Solver | `double_threshold` | V(intersection) | Faces | Valid? | ms |
|---|---|---|---|---|---|
| Fast (float) | 1e-06 | 1.19209289551e-07 | 12 | **no** — 0 boundary edges, 16 non-manifold edges, 16 wire edges | 0.41 |
| Fast (float) | 1e-07 | 1.19209289551e-07 | 12 | **no** — 0 boundary edges, 16 non-manifold edges, 16 wire edges | 0.39 |
| Fast (float) | 1e-08 | 1.98682149251e-07 | 21 | **no** — 8 boundary edges, 16 non-manifold edges, 3 zero-area faces | 0.39 |
| Fast (float) | 0 | 1.19209289551e-07 | 12 | **no** — 0 boundary edges, 15 non-manifold edges, 15 wire edges, 1 loose verts | 0.43 |
| Exact | 1e-06 | 1.19209289551e-07 | 20 | **no** — 4 zero-area faces | 3.73 |
| Manifold | 1e-06 | 1.19209289551e-07 | 12 | yes | 0.59 |

## Probe B — the twelve-shell cutting tool

`wall_with_openings` B is one mesh object holding twelve disconnected closed shells.
This probe records what each solver does with it, including the `DIFFERENCE` operation
the case actually models (a wall with twelve openings cut out), which the torture set's
union/intersection identity does not exercise.

| Solver | Operation | V(result) | Verts | Faces | Shells | Valid? | ms | Blender's own message |
|---|---|---|---|---|---|---|---|---|
| Exact | UNION | 12.6000000179 | 320 | 264 | 1 | yes | 19.79 | - |
| Exact | INTERSECT | 5.39999982566 | 216 | 132 | 12 | yes | 18.16 | - |
| Exact | DIFFERENCE | 3.60000053197 | 224 | 120 | 1 | yes | 19.03 | - |
| Fast (float) | UNION | 12.5999999541 | 320 | 256 | 1 | yes | 1.34 | - |
| Fast (float) | INTERSECT | 5.39999939549 | 216 | 132 | 12 | yes | 1.19 | - |
| Fast (float) | DIFFERENCE | 3.60000139556 | 224 | 112 | 1 | yes | 1.21 | - |
| Manifold | UNION | 12.6000000179 | 320 | 261 | 1 | yes | 1.88 | - |
| Manifold | INTERSECT | 5.39999982566 | 216 | 132 | 12 | yes | 1.23 | - |
| Manifold | DIFFERENCE | 3.60000053197 | 224 | 117 | 1 | yes | 1.50 | - |

The analytic expectation for `DIFFERENCE` is V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.

## Probe C — the Exact solver's `use_self` and `use_hole_tolerant` options

Both default to off. This probe re-runs two cases with each enabled, to record what
they cost when the input does not need them — the cost a caller pays for turning on a
robustness option defensively.

| Case | Options | V(union) | Valid? | ms |
|---|---|---|---|---|
| `wall_with_openings` | none | 12.6000000179 | yes | 17.76 |
| `wall_with_openings` | `use_self` | 12.6000000179 | yes | 31.67 |
| `wall_with_openings` | `use_hole_tolerant` | 12.6000000179 | yes | 17.67 |
| `wall_with_openings` | both | 12.6000000179 | yes | 32.09 |
| `near_degenerate_triangle` | none | 1 | yes | 3.28 |
| `near_degenerate_triangle` | `use_self` | 1 | yes | 5.09 |
| `near_degenerate_triangle` | `use_hole_tolerant` | 1 | yes | 3.13 |
| `near_degenerate_triangle` | both | 1 | yes | 4.92 |

## Probe D — `touching_vertex`, where the Exact solver loses an operand

Two unit cubes meeting at exactly one point. The Exact solver's union returns a
**closed, manifold, single-shell mesh of volume 1**: one of the two cubes, with the
other silently gone. This probe pins that down — both operand orders, and the same
pair perturbed by ±1 mm so the contact is no longer exact. The perturbed rows are a
deliberate modification of the case and are reported apart from the torture set
proper; the unperturbed rows are the case verbatim.

| Input | Solver | Verts | Faces | Shells | V(union) | Valid? |
|---|---|---|---|---|---|---|
| A ∪ B (the case) | Exact | 8 | 12 | 1 | 1 | yes |
| A ∪ B (the case) | Fast (float) | 16 | 24 | 2 | 2 | yes |
| A ∪ B (the case) | Manifold | 16 | 24 | 2 | 2 | yes |
| B ∪ A (operands swapped) | Exact | 8 | 12 | 1 | 1 | yes |
| B ∪ A (operands swapped) | Fast (float) | 16 | 24 | 2 | 2 | yes |
| B ∪ A (operands swapped) | Manifold | 16 | 24 | 2 | 2 | yes |
| B moved +1 mm away (no contact) | Exact | 16 | 24 | 2 | 1.99999964237 | yes |
| B moved +1 mm away (no contact) | Fast (float) | 16 | 24 | 2 | 1.99999964237 | yes |
| B moved +1 mm away (no contact) | Manifold | 16 | 24 | 2 | 1.99999964237 | yes |
| B moved −1 mm in (real overlap) | Exact | 20 | 24 | 1 | 1.99999982019 | yes |
| B moved −1 mm in (real overlap) | Fast (float) | 20 | 24 | 1 | 1.99999982019 | yes |
| B moved −1 mm in (real overlap) | Manifold | 20 | 24 | 1 | 1.99999982019 | yes |
| `shared_edge` A ∪ B (for comparison) | Exact | 14 | 24 | 1 | 2 | **no** — 1 non-manifold edges |
| `shared_edge` A ∪ B (for comparison) | Fast (float) | 16 | 24 | 2 | 2 | yes |
| `shared_edge` A ∪ B (for comparison) | Manifold | 16 | 24 | 2 | 2 | yes |

The expected union volume is 2 in the first four rows and 2 in the `shared_edge` row.
Nothing is reported by the modifier in the rows that return 1: no warning, no error,
and a result the validity check likes.

## Probe E — run-to-run determinism

The same operands, rebuilt from the reference set and run 10 times in one process.
*Signatures* is the number of distinct `(verts, faces, volume)` triples observed. A
deterministic solver produces exactly one. This is asked because Blender's own tracker
carries a confirmed threading non-determinism in one of these solvers
([#143644](https://projects.blender.org/blender/blender/issues/143644)), and because a
kernel whose output depends on thread scheduling cannot be diffed, cached or
regression-tested.

| Case | Solver | Op | Runs | Signatures | Distinct results |
|---|---|---|---|---|---|
| `overlap_half` | Exact | UNION | 10 | 1 | identical every run |
| `overlap_half` | Fast (float) | UNION | 10 | **3** | 32v/15f/V=1 ×1; 32v/13f/V=1 ×4; 32v/14f/V=1 ×5 |
| `overlap_half` | Manifold | UNION | 10 | 1 | identical every run |
| `wall_with_openings` | Exact | UNION | 10 | 1 | identical every run |
| `wall_with_openings` | Fast (float) | UNION | 10 | 1 | identical every run |
| `wall_with_openings` | Manifold | UNION | 10 | 1 | identical every run |
| `wall_with_openings` | Exact | DIFFERENCE | 10 | 1 | identical every run |
| `wall_with_openings` | Fast (float) | DIFFERENCE | 10 | 1 | identical every run |
| `wall_with_openings` | Manifold | DIFFERENCE | 10 | 1 | identical every run |
| `sliver` | Exact | INTERSECT | 10 | 1 | identical every run |
| `sliver` | Fast (float) | INTERSECT | 10 | 1 | identical every run |
| `sliver` | Manifold | INTERSECT | 10 | 1 | identical every run |

