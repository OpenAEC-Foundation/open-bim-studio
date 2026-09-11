# FINDINGS — R-16, boolean robustness across four candidates

## The question, restated

Does a candidate kernel's boolean survive the ten cases in
[`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py) — coplanar
faces, a shared edge, a touching vertex, identical operands, containment, a 1e-7 m slab, a
T-junction operand and a wall cut by twelve openings — producing a valid closed result each
time, with `V(A∪B) + V(A∩B) = V(A) + V(B)`?

The pass/fail criteria were written before any driver ran and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-16:

> - **Spike:** `spikes/boolean-torture/` — the cases in `reference/boolean_torture_set.py` run
>   through OCCT, Blender (exact), Manifold and CGAL; each result checked for closed manifold
>   output and V(A∪B) + V(A∩B) = V(A) + V(B).
> - **Pass (per candidate):** every case produces a valid closed result and the volume identity
>   holds within 1e-9 relative.
> - **Fail:** any invalid result, or a volume error above 1e-6 relative; each failure recorded
>   with the input, the version and the traced cause in `problems.md`.

This file assembles the four per-candidate raw result files into one comparison and applies that
criterion literally. It adds no measurement of its own: every number below is copied from a named
row of a named file, all eight of them regenerated in **one session on one machine on
2026-09-11**.

## Hardware, OS and versions

*Measured.* Recorded by each driver in its own environment table, so this section has a source
rather than being asserted here.

| | |
|---|---|
| CPU | `Intel(R) Core(TM) i9-14900HX` (32 logical processors) |
| RAM | 32 GB |
| OS | Windows 11 Pro, `10.0.26200` |
| Python (OCCT, Manifold, CGAL drivers) | 3.12.10 |
| OCCT | `cadquery-ocp` 8.0.1.0.0, bundling **OCCT 8.0.1**; `Precision::Confusion` 1e-7, `Angular` 1e-12, `Intersection` 1e-9, confirmed at runtime |
| Blender | **5.0.0**, build hash `a37564c4df7a`, built 2025-11-18 11:06:54, bundled Python 3.11.13, run `--background --factory-startup` |
| Manifold (standalone) | `manifold3d` **3.5.3**, source tag `v3.5.3`, commit `0edd9d54876f3135e431575214dd6d8a72866fee`, wheel built `MANIFOLD_PAR=ON` (TBB); numpy 2.3.5 |
| Manifold (inside Blender) | **v3.2.1**, per Blender's `build_files/build_environment/cmake/versions.cmake` at the build's own commit — *claimed* by that source file, not measured here |
| CGAL | `cgal` wheel **6.0.1**.post202410241521, `CGAL_VERSION_NR` 1060010900, source tag `v6.0.1`, commit `50cfbde3b84dbeae8338268db2d78fe4fcb522de`; the bound kernel is `Exact_predicates_inexact_constructions_kernel` (Epick) |

Raw stdout of the whole session: [`results/run-2026-09-11.log`](results/run-2026-09-11.log).

## The model

[`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py), verbatim, at
commit `52d633dcd342faca70daf8c8f28ce64c5dd7fc56` ("Fix review findings on the benchmark set:
coplanar overlap and README size claim"). Ten pairs, the same ten for every candidate; no driver
adds, drops or adjusts a case.

## Method, per driver

One paragraph per driver, because the construction path is part of the measurement and the four
paths are **not identical**. Full method in each driver's README section and in the candidate
note's §Measurements.

- **OCCT** ([`README.md`](README.md) §Running the OCCT driver;
  [`occt.md`](../../docs/research/kernels/occt.md) §Measurements). Each benchmark triangle becomes
  a planar face, the faces are sewn (`BRepBuilderAPI_Sewing` at `Precision::Confusion()` = 1e-7)
  and each resulting shell becomes a solid. Validity is `BRepCheck_Analyzer`; volume is OCCT's own
  `BRepGProp` integrator. Timings are the fastest of five runs with `SetRunParallel(false)`, and
  **every repeat rebuilds its operands**, because `BOPAlgo` mutates its arguments by default.
- **Blender** ([`README.md`](README.md) §Running the Blender driver;
  [`blender.md`](../../docs/research/kernels/blender.md) §Measurements). `Mesh.from_pydata` from
  the reference set verbatim, no welding and no triangulation, with operands rebuilt for every
  solver, every operation and every repeat. Validity is the driver's own check — closed, every
  edge in exactly two faces, no loose vertices, no face below 1e-14 m², and `Mesh.validate()`
  making no correction. Volume is `reference.signed_volume` over the driver's own triangulation;
  Blender is never asked for a volume. Timings are the median of five, wall clock around depsgraph
  evaluation plus the evaluated-mesh copy.
- **Manifold** ([`manifold_driver.py`](manifold_driver.py) module docstring;
  [`manifold.md`](../../docs/research/kernels/manifold.md) §Measurements). `manifold3d.Mesh`
  (float32) and `Mesh64` (float64) into `Manifold(...)`, with no merge vectors and no repair.
  Validity is the driver's own check on the *exported* triangles plus `status()` and `is_empty()`.
  Volume is `reference.signed_volume`, with `Manifold.volume()` compared beside it. Median of five,
  with the `status()` call that forces the deferred CSG node inside the timed region.
- **CGAL** ([`cgal_driver.py`](cgal_driver.py) module docstring;
  [`cgal.md`](../../docs/research/kernels/cgal.md) §Measurements).
  `PMP::polygon_soup_to_polygon_mesh` into a `Polyhedron_3`, deliberately **without**
  `orient_polygon_soup`. Validity is the same exported-triangle check plus
  `Polyhedron_3::is_closed()` and the boolean's own `bool` return. Median of five; **both operands
  are rebuilt inside every repeat**, because PMP corefinement modifies them in place
  ([`results/cgal.md`](results/cgal.md) Probe F).

### Comparability caveats — read these before the tables

These are not hedges. Each was established by a reviewed per-candidate note, and each limits what
a row of the assembled table may be read to mean.

1. **`wall_with_openings` operand B is four different constructions.** OCCT builds it as a
   **compound of twelve solids** — one solid with twelve shells is what a naive translation
   produces and `BRepCheck_Analyzer` rejects it
   ([`occt.md`](../../docs/research/kernels/occt.md) §Measurements, construction bullet). Blender
   builds it as **one mesh object with twelve disconnected shells**
   ([`results/blender.md`](results/blender.md) §Construction of the operands). Manifold accepts
   that same multi-component mesh as **one `Manifold` with `decompose() == 12`**
   ([`results/manifold.md`](results/manifold.md) Probe A). CGAL accepts it as one `Polyhedron_3`
   with `PMP::connected_components` reporting 12 ([`results/cgal.md`](results/cgal.md) Probe A).
   The four `wall_with_openings` rows are therefore the same benchmark *case* but not the same
   input *object*.
2. **The `sliver` row must not be compared as "the same input".** OCCT's operand is degraded
   during construction — measured volume **3.33e-08 m³** against the specified 1e-07, with an
   entity tolerance that exceeds the slab's own thickness
   ([`results/occt.md`](results/occt.md) §Construction of the operands, `sliver` row). Blender's
   operand is float32-rounded before the boolean runs — **1.19209289551e-07 m³**, 19% too thick,
   because `0.5 + 1e-7` is not representable in float32
   ([`results/blender.md`](results/blender.md) §Construction of the operands, second bullet) — so
   that row measures the representation, not the boolean. Manifold at tolerance 1e-6 **deletes the
   slab silently and reports `NoError`** ([`results/manifold.md`](results/manifold.md) Probe B).
   CGAL, having no tolerance to raise, carries it through at 9.99999999474e-08 m³
   ([`results/cgal.md`](results/cgal.md) Probe B).
3. **`near_degenerate_triangle` operand B contains a T-junction** — the reference set splits the
   cube's top face by inserting a vertex *on* the edge v5→v6. OCCT sews it into a valid solid;
   Blender-Exact handles it; Blender-Manifold **returns operand A unchanged** with the console
   warning `Cannot execute, non-manifold inputs`
   ([`results/blender.md`](results/blender.md) main table, `near_degenerate_triangle` Manifold
   row); standalone Manifold refuses on both f32 and f64 with `NotManifold` and an empty result
   ([`results/manifold.md`](results/manifold.md) Probe C); CGAL builds the operand but reports it
   **not closed and self-intersecting**, and both booleans return `False` with 0 facets
   ([`results/cgal.md`](results/cgal.md) Probe C). Neither `PMP::stitch_borders` nor
   `Mesh64.merge()` repairs it.
4. **Fuzzy and tolerance settings are not a common axis**, and nothing below is averaged across
   them. OCCT has `default`, `SetFuzzyValue(1e-5)` and `1e-3`; Blender has three *solvers*
   (Exact, Fast, Manifold) rather than a tolerance; Manifold has a per-solid tolerance (default,
   1e-9, 1e-6) *and* two input precisions; CGAL has no tolerance at all, and its two settings are
   ingest precisions. The setting column stays in every table.
5. **Timings come from three harnesses** — a Python binding around C++ (OCCT, Manifold, CGAL) and
   Blender's modifier stack including an evaluated-mesh copy. Read cross-candidate ratios as orders
   of magnitude, not as benchmarks. OCCT's tessellation timings belong to a different spike
   ([`../tessellation/`](../tessellation/)) and are out of scope for this file.

## Results

*Measured.* Cell format: **validity** · **identity residual** · **ms ∪ / ∩**. *Identity* is
`|V(A) + V(B) − (V(A∪B) + V(A∩B))|` computed from each driver's **measured** operand volumes, so
it isolates the boolean from error already present in the operands. Every row below is the
correspondingly named row of the named file's §Boolean results table.

### OCCT 8.0.1 — [`results/occt.md`](results/occt.md) §Boolean results

Validity is `yes` and the identity residual is identical across all three settings on every case
except `near_degenerate_triangle`, so the residual is given once and the settings differ only in
time — and in the result's entity tolerance, which the source file records per row.

| Case | Valid? (all 3 settings) | Identity | ms ∪/∩, default | ms, fuzzy=1e-5 | ms, fuzzy=1e-3 |
|---|---|---|---|---|---|
| `disjoint` | yes | 0 | 0.69 / 0.47 | 0.65 / 0.51 | 0.64 / 0.49 |
| `overlap_half` | yes | 6.66e-16 | 4.62 / 3.96 | 4.38 / 4.06 | 4.39 / 4.54 |
| `coplanar_faces` | yes | 4.44e-16 | 1.75 / 1.17 | 1.70 / 1.25 | 1.62 / 1.18 |
| `shared_edge` | yes | 2.22e-16 | 1.67 / 1.16 | 1.66 / 1.19 | 1.73 / 1.11 |
| `touching_vertex` | yes | 2.22e-16 | 1.24 / 0.78 | 1.24 / 0.80 | 1.21 / 0.86 |
| `identical` | yes | 0 | 2.45 / 2.40 | 2.57 / 2.40 | 2.48 / 2.25 |
| `contained` | yes | 0 | 1.42 / 1.26 | 1.43 / 1.34 | 1.50 / 1.34 |
| `sliver` | yes | **3.33e-08** — ∩ returns 0 where 1e-07 m³ was expected | 3.33 / 2.99 | 3.17 / 2.81 | 3.17 / 2.96 |
| `near_degenerate_triangle` | yes | 2.22e-16 default; **0** on both fuzzy settings | 2.92 / 2.59 | 2.68 / 2.81 | 3.01 / 2.66 |
| `wall_with_openings` | yes | 1.42e-14 | 58.52 / 50.21 | 54.27 / 51.20 | 54.03 / 50.65 |

**The negative result is that fuzzy changed nothing.** Every volume, every residual and every
validity verdict is identical across the three settings; what moves is the result's maximum entity
tolerance, to roughly fuzzy/2 wherever an interference had to be resolved (`sliver`: tol ≤ 1.76e-07
→ 5.1e-06 → 5e-04). Fuzzy repaired nothing here; it made the answer vaguer.

### Blender 5.0.0 — [`results/blender.md`](results/blender.md) §Boolean results

| Case | Exact | Fast (float) | Manifold (v3.2.1) |
|---|---|---|---|
| `disjoint` | yes · 0 · 0.74/0.66 | yes · 0 · 0.31/0.32 | yes · 0 · 0.48/0.32 |
| `overlap_half` | yes · 0 · 3.21/3.31 | **invalid both** (26 non-manifold + 26 wire edges ∪; 25 + 25 ∩); V∪=1, V∩=1, Δ∪=−0.5, Δ∩=+0.5 · 0 · 0.55/0.48 | yes · 0 · 0.63/0.66 |
| `coplanar_faces` | yes · 0 · 1.43/1.21 | **∪ invalid** (4 non-manifold, 4 wire edges); ∩ ok · 0 · 0.38/0.36 | yes · 0 · 0.49/0.38 |
| `shared_edge` | **∪ invalid** (1 non-manifold edge); ∩ ok · 0 · 1.71/1.73 | yes · 0 · 0.27/0.26 | yes · 0 · 0.46/0.30 |
| `touching_vertex` | yes, **but V∪=1** — one operand silently gone, Δ∪=−1 · **1** · 1.59/1.30 | yes · 0 · 0.26/0.25 | yes · 0 · 0.57/0.42 |
| `identical` | yes · 0 · 2.81/2.91 | **invalid both** (8 boundary + 8 non-manifold edges); V∪=0, V∩=2 · 0 · 0.29/0.30 | yes · 0 · 0.44/0.50 |
| `contained` | yes · 0 · 0.48/0.47 | yes · 0 · 0.32/0.25 | yes · 0 · 0.39/0.52 |
| `sliver` | **invalid both** (4 zero-area faces) · 0 · 3.45/3.62 | **invalid both** (16 non-manifold, 16 wire edges) · 0 · 0.37/0.41 | yes · 0 · 0.43/0.48 |
| `near_degenerate_triangle` | yes · 0 · 3.31/3.15 | **invalid both** (8 and 11 boundary edges); V∪=0, V∩=2 · 0 · 0.33/0.40 | yes · 0 · 0.45/0.35, with `WARNING … Cannot execute, non-manifold inputs` — **the unmodified operand A is returned** |
| `wall_with_openings` | yes · 3.2e-14 · 17.80/18.26 | yes · 4.94e-07 · 1.13/1.18 | yes · 1.42e-14 · 1.91/1.43 |

Two readings the source file states, which this table must not lose. First, *valid* and *correct*
are different questions: the mathematically correct union of two cubes meeting at an edge or at a
point is **not** a manifold mesh, so the Exact solver's correct `shared_edge` answer is marked
invalid by the topological check and is not wrong to be. Second, the identity residual is
necessary but not sufficient — the Fast solver's `overlap_half` returns V∪=1 and V∩=1, a residual
of exactly 0 with **both** volumes wrong by 33%.

### Manifold 3.5.3, standalone — [`results/manifold.md`](results/manifold.md) §Boolean results

| Case | f64, default tol | f64, tol=1e-9 | f64, tol=1e-6 | f32, default tol |
|---|---|---|---|---|
| `disjoint` | yes · 0 · 0.015/0.003 | yes · 0 · 0.023/0.002 | yes · 0 · 0.013/0.002 | yes · 0 · 0.013/0.002 |
| `overlap_half` | yes · 0 · 0.293/0.093 | yes · 0 · 0.171/0.125 | yes · 0 · 0.194/0.074 | yes · 0 · 0.148/0.109 |
| `coplanar_faces` | yes · 0 · 0.125/0.043 | yes · 0 · 0.116/0.064 | yes · 0 · 0.229/0.059 | yes · 0 · 0.139/0.063 |
| `shared_edge` | yes · 0 · 0.113/0.090 | yes · 0 · 0.169/0.073 | yes · 0 · 0.114/0.072 | yes · 0 · 0.122/0.086 |
| `touching_vertex` | yes · 0 · 0.106/0.087 | yes · 0 · 0.083/0.071 | yes · 0 · 0.091/0.056 | yes · 0 · 0.069/0.065 |
| `identical` | yes · 0 · 0.173/0.054 | yes · 0 · 0.142/0.046 | yes · 0 · 0.169/0.066 | yes · 0 · 0.157/0.053 |
| `contained` | yes · 0 · 0.011/0.014 | yes · 0 · 0.011/0.010 | yes · 0 · 0.011/0.010 | yes · 0 · 0.012/0.014 |
| `sliver` | yes · 4.44e-16 · 0.224/0.137 | yes · 4.44e-16 · 0.178/0.099 | **∩ invalid — empty result**, Δ∩=−1e-07, status `NoError` · 0 · 0.004/0.002 | yes · 0 · 0.186/0.137; ∩ = 1.19209289551e-07 (the f32 slab), Δ∩=1.92e-08 |
| `near_degenerate_triangle` | **invalid both — `NotManifold`**, Δ∪=−1, Δ∩=−1 · **1** · 0.003/0.003 | **invalid both — `NotManifold`** · **1** · 0.003/0.002 | **invalid both — `NotManifold`** · **1** · 0.002/0.002 | **invalid both — `NotManifold`** · **1** · 0.002/0.002 |
| `wall_with_openings` | yes · 3.55e-14 · 0.997/0.650 | yes · 3.55e-14 · 1.000/0.604 | yes · 3.55e-14 · 1.104/0.670 | yes · 2.49e-14 · 0.990/0.556 |

`coplanar_faces`'s intersection is a **non-empty zero-volume shell** of four triangles at every
setting — closed, manifold, correctly wound, volume 0. Mathematically right; a caller testing
`is_empty()` to mean "no intersection" gets the wrong answer.

### CGAL 6.0.1, Epick corefinement — [`results/cgal.md`](results/cgal.md) §Boolean results

| Case | Epick, f64 input | Epick, f32-rounded input |
|---|---|---|
| `disjoint` | yes · 0 · 0.020/0.010 | yes · 0 · 0.018/0.012 |
| `overlap_half` | yes · 0 · 0.380/0.528 | yes · 0 · 0.481/0.388 |
| `coplanar_faces` | yes · 0 · 0.102/0.075 | yes · 0 · 0.141/0.086 |
| `shared_edge` | **∪ invalid — the boolean returned `False`**, Δ∪=−2; ∩ ok · **2** · 0.103/0.087 | **∪ invalid — returned `False`**, Δ∪=−2 · **2** · 0.086/0.090 |
| `touching_vertex` | yes · 0 · 0.071/0.063 | yes · 0 · 0.071/0.066 |
| `identical` | yes · 0 · 0.329/0.287 | yes · 0 · 0.260/0.277 |
| `contained` | yes · 0 · 0.022/0.021 | yes · 0 · 0.020/0.021 |
| `sliver` | yes · 0 · 1.174/1.237; ∩ = 9.99999999566e-08 m³ | yes · 0 · 1.089/0.959; ∩ = 1.19209289551e-07, Δ∩=1.92e-08 |
| `near_degenerate_triangle` | **invalid both — returned `False`**; operand B not closed and self-intersecting · **2** · 0.313/0.269 | **invalid both — returned `False`** · **2** · 0.300/0.282 |
| `wall_with_openings` | yes · 7.11e-15 · 8.183/8.082 | yes · 0 · 6.627/6.474; Δ∪=1.79e-08, Δ∩=−1.74e-07 |

**CGAL exposes no tolerance parameter**, so there is nothing here corresponding to the tolerance
sweeps above and nothing that could delete the slab: the 1e-7 m feature survives ingest and the
boolean on both settings. The two settings are ingest precisions; they change *which volumes* come
out, never *which cases* pass.

## Summary — candidate × setting

*Measured.* Counts and worst residuals are copied from each file's own summary table; the time
range is the minimum and maximum ∪/∩ cell of that setting in its main table. *Correct* is both
volumes within `1e-6 * max(1, |expected|)` of the analytic expectation — relative above 1 m³, an
absolute floor below it — the definition [`results/blender.md`](results/blender.md) fixes and that
the Manifold and CGAL files adopt verbatim. The OCCT driver reports no *correct* count of its own;
its column is derived here from its Δ annotations and is labelled *inferred*.

| Candidate | Setting | Valid /10 | Correct /10 | Worst identity residual | Time range (ms) |
|---|---|---|---|---|---|
| OCCT 8.0.1 | default | **10** | 9 *(inferred)* | 3.33e-08 (`sliver`) | 0.47 – 58.52 |
| OCCT 8.0.1 | fuzzy=1e-5 | **10** | 9 *(inferred)* | 3.33e-08 (`sliver`) | 0.51 – 54.27 |
| OCCT 8.0.1 | fuzzy=1e-3 | **10** | 9 *(inferred)* | 3.33e-08 (`sliver`) | 0.49 – 54.03 |
| Blender 5.0 | Exact | 8 | 9 | **1** (`touching_vertex`) | 0.47 – 18.26 |
| Blender 5.0 | Fast (float) | 5 | 7 | 4.94e-07 | 0.25 – 1.18 |
| Blender 5.0 | Manifold (v3.2.1) | **10** | **10** | 1.42e-14 | 0.30 – 1.91 |
| Manifold 3.5.3 | f64, default tol | 9 | 9 | 3.55e-14 | 0.003 – 0.997 |
| Manifold 3.5.3 | f64, tol=1e-9 | 9 | 9 | 3.55e-14 | 0.002 – 1.000 |
| Manifold 3.5.3 | f64, tol=1e-6 | 8 | 9 | 3.55e-14 | 0.002 – 1.104 |
| Manifold 3.5.3 | f32, default tol | 9 | 9 | 2.49e-14 | 0.002 – 0.990 |
| CGAL 6.0.1 | Epick, f64 input | 8 | 8 | 7.11e-15 | 0.010 – 8.183 |
| CGAL 6.0.1 | Epick, f32-rounded | 8 | 8 | 0 | 0.012 – 6.627 |

The worst-residual column is **not** a like-for-like ranking on its own: Manifold's and CGAL's
figures exclude the cases they refused, and OCCT's 3.33e-08 is driven entirely by `sliver`
(1.42e-14 without it). *Valid* and *Correct* are where the criterion is decided.

## Verdict against R-16

R-16 says, verbatim: **"Pass (per candidate): every case produces a valid closed result and the
volume identity holds within 1e-9 relative."** and **"Fail: any invalid result, or a volume error
above 1e-6 relative."** Applied literally, per candidate × setting:

| Candidate × setting | Verdict | Why, against the words of the criterion |
|---|---|---|
| OCCT — default, fuzzy=1e-5, fuzzy=1e-3 | **Neither pass nor fail** | All ten cases are valid per `BRepCheck_Analyzer` at every setting, so the fail clause "any invalid result" does not fire. But `sliver`'s identity residual is 3.33e-08 against `V(A)+V(B)` ≈ 1, i.e. **3.33e-08 relative** — above the 1e-9 pass line and below the 1e-6 fail line. The criterion as written leaves this state unnamed, and it is reported as unnamed rather than rounded into either verdict. |
| Blender — Exact | **FAIL** | Two invalid results (`shared_edge` ∪, `sliver` both), and a volume error of 1 m³ on a 2 m³ answer at `touching_vertex` — 50% relative, five hundred thousand times the 1e-6 fail line. |
| Blender — Fast (float) | **FAIL** | Five of ten cases invalid, with volume errors of 33% (`overlap_half`) and 100% (`identical`, `near_degenerate_triangle`). |
| Blender — Manifold (v3.2.1) | **PASS**, on the operands Blender gave it | 10/10 valid, 10/10 correct, worst identity residual 1.42e-14 absolute — 7.9e-16 relative to the `V(A)+V(B)` = 18 that produced it. Three qualifications below. |
| Manifold — f64, default tol | **FAIL** | `near_degenerate_triangle` is invalid (`NotManifold`, empty result) and the resulting volume error is 1 m³ on a 1 m³ answer. |
| Manifold — f64, tol=1e-9 | **FAIL** | The same case, the same cause. |
| Manifold — f64, tol=1e-6 | **FAIL** | The same, and additionally `sliver`'s intersection is empty where 1e-07 m³ was expected: the slab was removed at ingest, with status `NoError`. |
| Manifold — f32, default tol | **FAIL** | The same refusal as the f64 default row. |
| CGAL — Epick, f64 input | **FAIL** | Two invalid results: `shared_edge`'s union and both `near_degenerate_triangle` booleans return `False` with 0 facets. |
| CGAL — Epick, f32-rounded input | **FAIL** | Identical — the same two refusals on the same two cases. |

**Exactly one candidate × setting passes the criterion as written, and it is Blender's embedded
Manifold solver.** Three qualifications, each traceable:

1. *Measured.* Its `sliver` operand was already **19% too thick** before the boolean ran
   (1.19209289551e-07 m³ against the specified 1e-07), because Blender stores vertex positions in
   float32 and `0.5 + 1e-7` is not representable there
   ([`results/blender.md`](results/blender.md) §Construction of the operands). The identity is
   computed from measured operand volumes precisely so that it isolates the boolean — which here
   flatters the candidate: no solver can be blamed for the representation, and none escapes it.
2. *Measured.* Its `near_degenerate_triangle` row is scored valid and correct while the modifier
   logged `Cannot execute, non-manifold inputs` and **returned operand A unchanged**. *Inferred:*
   the expected answer for that case happens to *be* operand A's volume — 1 m³ for both the union
   and the intersection, the two operands being the same solid with a different top-face
   triangulation — so a refusal is arithmetically indistinguishable from a success, and had the
   reference set used two different solids this row would have failed. The standalone library at
   v3.5.3 refuses the identical operand with a typed `NotManifold` status and an empty mesh; the
   difference is the binding's refusal convention, not the algorithm
   ([`manifold.md`](../../docs/research/kernels/manifold.md) §Cross-harness check, which finds the
   two harnesses agreeing to the digit on the other nine cases).
3. *Measured.* Its `wall_with_openings` operand was the twelve-shell mesh, not OCCT's compound of
   twelve solids (caveat 1).

**Read together: no candidate passes R-16 on a construction identical to every other candidate's,
and the single nominal pass rests on a refusal the criterion cannot see.** That is a finding about
the criterion as much as about the candidates, and it is why R-16's status is now `in progress`
rather than `resolved`.

### Failures, traced causes, and the `problems.md` row each supports

Every entry is an invalid result or a volume error above 1e-6 relative, recorded with the input,
the version and the traced cause, as R-16's fail clause requires. Rows are in
[`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md).

| Candidate × setting | Case | What happened | Traced cause | Supports |
|---|---|---|---|---|
| Blender 5.0 Exact | `touching_vertex` | A valid, closed, single-shell result of volume **1** — one of the two cubes, the other silently gone. No warning, no error | The Exact solver's handling of a single-point contact merges the pair to one shell. Perturbing the contact by ±1 mm in either direction restores volume 2 ([`results/blender.md`](results/blender.md) Probe D) | **P-01** — boolean wrong on touching input |
| Blender 5.0 Exact | `shared_edge` ∪ | 1 non-manifold edge — though the mathematically correct union *is* non-manifold there | A 2-manifold mesh cannot hold four faces meeting on one line | **P-01**, as a representation limit rather than an algorithm defect |
| Blender 5.0 Exact | `sliver` ∪ and ∩ | 4 zero-area faces in both results | The float32 operand is 19% too thick and the solver emits degenerate faces at that scale | **P-05** (precision loss, float32 storage), **P-02** (result slightly wrong) |
| Blender 5.0 Fast | `overlap_half`, `identical`, `near_degenerate_triangle` | Wrong volumes, 33% to 100%, with non-manifold and wire edges | Float-threshold topology decisions (`double_threshold` 1e-6): topology decided on rounded values | **P-01** |
| Blender 5.0 Fast | `overlap_half` ∪ | **Non-deterministic** — 3 distinct signatures of verts, faces and volume over 10 identical runs ([`results/blender.md`](results/blender.md) Probe E) | Parallel evaluation with no canonical merge order; Blender's own tracker carries it ([#143644](https://projects.blender.org/blender/blender/issues/143644)) | **P-16** — same input, different geometry per run |
| Manifold 3.5.3, all four settings | `near_degenerate_triangle` | `Error::NotManifold`, empty result, both operations | The T-junction leaves a halfedge with no twin, and the ingest checks its correctness precondition before anything else. `Mesh64.merge()` reports it changed the mesh, and the status is still `NotManifold` ([`results/manifold.md`](results/manifold.md) Probe C) | **P-09** — mesh boolean requires manifold input and rejects real models |
| Manifold 3.5.3, f64 tol=1e-6 | `sliver` ∩ | Empty result where 1e-07 m³ was expected, status **`NoError`** | The slab is thinner than the requested tolerance and simplification removes it. The sweep puts the threshold between 1e-8 and 1e-7 on f64 and between 1e-7 and 1e-6 on f32 ([`results/manifold.md`](results/manifold.md) Probe B) | **P-02** (silently wrong result), **P-24** (one named tolerance, different magnitudes by scope) |
| CGAL 6.0.1, both settings | `shared_edge` ∪ | `corefine_and_compute_union` returns `False` with 0 facets | The requested result has a non-manifold edge — four facets along x=1, y=1 — which a `Polyhedron_3` halfedge structure cannot hold. The *intersection* of the same pair succeeds ([`results/cgal.md`](results/cgal.md) Probe D) | **P-01**, again as a representation limit |
| CGAL 6.0.1, both settings | `near_degenerate_triangle` | Both booleans return `False` with 0 facets; operand B is **not closed** and **self-intersects** (3 border halfedges); `PMP::stitch_borders` does not repair it | Two documented corefinement preconditions violated. A third documented precondition, `does_bound_a_volume`, is **absent from the binding** and could not be checked at all | **P-09** |
| CGAL 6.0.1, f64 input | run-to-run | **Non-deterministic emission order**: 10 identical runs of the `wall_with_openings` difference give 5 distinct volume signatures but **1 distinct geometry** ([`results/cgal.md`](results/cgal.md) Probe E) | The vertex *order* varies between runs; `reference.signed_volume` sums in emission order, so the last digits move. The solid does not | **P-16**, in its weaker form — the output is stable, its serialisation is not |
| OCCT 8.0.1, all three settings | `sliver` | The intersection returns **0** where 1e-07 m³ was expected, and the result is reported valid | The operand never existed at the specified thickness: sewing at `Precision::Confusion()` = 1e-7 produced a solid of 3.33e-08 m³ whose own tolerance exceeds its thickness. `BRepPrimAPI_MakeBox` refuses any extent at or below 1e-7 outright with `Standard_DomainError` ([`results/occt.md`](results/occt.md) Probe D) | **P-24** (a tolerance acting as a floor on representable size), **P-02** |
| OCCT 8.0.1, fuzzy=1e-5 | chained fuse, Probe A | Eight boxes fused one at a time across 5e-6 m gaps accumulate **2.67e-05 m³** of excess volume, monotonically | Fuzzy tolerance bridges each gap and the volume integral counts the bridge as solid; the growth is inherited downstream — Probe B shows one fuse raising the *input* shapes' tolerance to 5.001e-04 | **P-02** (tolerance growth), **P-24** |

## Run-to-run reproduction: what moved between 2026-09-10 and 2026-09-11

*Measured.* All eight drivers were re-run for this assembly and every regenerated file was diffed
against the committed, per-candidate-reviewed version. **No validity verdict, no pass/fail verdict
and no volume above the 1e-12 level moved.** What did move, in full:

| File | Cell | 2026-09-10 | 2026-09-11 | Explanation, from the file itself |
|---|---|---|---|---|
| `results/occt.md` | none | - | - | Timing only; every volume, residual, tolerance and validity cell is unchanged |
| `results/manifold.md` | none | - | - | Timing only |
| `results/blender.md` | `overlap_half` Fast ∪ edge counts | 24 / 24 | 26 / 26 | The Fast solver's measured non-determinism on this exact case (Probe E); the result is invalid either way |
| `results/blender.md` | Probe A, Fast, threshold 0 | 19 edges, `validate()` corrected | 15 edges, no correction | The same non-determinism; invalid either way |
| `results/blender.md` | Probe E signatures | 2 | 3 | That probe's own subject: this *is* the measurement, not noise in it |
| `results/cgal.md` | `sliver` f64 ∩ volume | 9.99999999612e-08 | 9.99999999566e-08 | One of the three values the **committed** file's own Probe E already lists for this case |
| `results/cgal.md` | `wall_with_openings` f64 identity | 3.55e-15 | 7.11e-15 | Emission-order summation; both are about 3e-16 relative |
| `results/cgal.md` | Probe E, difference signatures | 4 | 5 | Distinct *geometries* still 1 |

[`cgal.md`](../../docs/research/kernels/cgal.md) §Measurements anticipated exactly this and calls
it a finding rather than a nuisance: a re-run that reports 12.600000000000003 where the committed
file says 12.6, or 0 where it says 3.55e-15, has reproduced the measurement, and nothing above the
1e-12 level moves. Nothing did. Timings moved by roughly minus 15% to plus 25% across the board,
the largest being Blender's Exact solver on the twelve-opening wall (15.95 to 17.80 ms union).

## What this does not settle

- **Only planar geometry was tested.** All ten cases are boxes and box-like solids. Curved-surface
  booleans are where OCCT's own issue tracker concentrates — `problems.md` row **P-12** — and this
  set contains none. A candidate's score here says nothing about surface-surface intersection.
- **Only single operations were tested.** Each case is one union and one intersection on fresh
  operands. Real modelling chains dozens of booleans, and OCCT's Probe A already shows tolerance
  growth compounding monotonically over a chain of eight. Chained behaviour for Blender, Manifold
  and CGAL was not measured at all.
- **No real IFC input.** Ten synthetic pairs, none imported, none carrying the self-intersections,
  duplicated faces and inconsistent winding that real files do. The two refusals that decided three
  candidates' verdicts — `near_degenerate_triangle` and `shared_edge` — suggest the refusal *rate*
  on real input is the number that actually matters, and it is unmeasured.
- **The constructions are not identical**, per caveats 1 to 3: four candidates were handed four
  different objects for `wall_with_openings` and three materially different ones for `sliver`. The
  per-candidate verdicts are sound; a cross-candidate ranking on those two rows is not.
- **Exactness and a lucky tie-break are indistinguishable on this set.** Blender's Manifold solver
  scores 10/10 partly because its refusal on `near_degenerate_triangle` coincides with the right
  answer, and standalone Manifold's `coplanar_faces` intersection is a non-empty zero-volume shell
  that a naive `is_empty()` caller would misread. A pass here is not a proof of exactness.
- **Tessellation is out of scope.** OCCT's meshing numbers live in
  [`../tessellation/`](../tessellation/), and no other candidate has an equivalent measurement.
- **Our own kernel has not been measured.** R-16 exists to be run against the kernel we build.
  This file is the baseline that comparison will use, and nothing more.
