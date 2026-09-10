# Boolean torture set — OCCT raw results

Produced by [`../occt_driver.py`](../occt_driver.py). This file is raw data for
`../FINDINGS.md` (assembled once every candidate has run) and for
[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10

## Environment

| Item | Value |
|---|---|
| python | `3.12.10` |
| platform | `Windows 11 (AMD64)` |
| processor | `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel` |
| cadquery-ocp | `8.0.1.0.0` |
| occt | `8.0.1 (bundled by cadquery-ocp 8.0.1.0.0)` |
| Precision::Confusion | `1e-07` |
| Precision::Angular | `1e-12` |
| Precision::Intersection | `1e-09` |
| sewing tolerance | `1e-07` |
| repeats per timing | 5 (fastest reported) |
| threading | `SetRunParallel(false)` — single-threaded, so the timings compare algorithms not core counts |

## Construction of the operands

Triangle soup → planar faces → `BRepBuilderAPI_Sewing` → solid(s), at sewing
tolerance `1e-07`. Construction is part of the measurement: a case whose
operands cannot be built is a finding about OCCT, not a driver error.

| Case | A valid? | V(A) | max tol(A) | B valid? | V(B) | Note |
|---|---|---|---|---|---|---|
| `disjoint` | yes | 1 | 1e-07 | yes | 1 | - |
| `overlap_half` | yes | 1 | 1e-07 | yes | 1 | - |
| `coplanar_faces` | yes | 1 | 1e-07 | yes | 1 | - |
| `shared_edge` | yes | 1 | 1e-07 | yes | 1 | - |
| `touching_vertex` | yes | 1 | 1e-07 | yes | 1 | - |
| `identical` | yes | 1 | 1e-07 | yes | 1 | - |
| `contained` | yes | 1 | 1e-07 | yes | 0.125 | - |
| `sliver` | yes | 1 | 1e-07 | yes | 3.33333333e-08 | - |
| `near_degenerate_triangle` | yes | 1 | 1e-07 | yes | 1 | - |
| `wall_with_openings` | yes | 9 | 1e-07 | yes | 9 | compound of 12 solids |

## Boolean results

`Δ` is the deviation from the analytic expectation in `reference/boolean_torture_set.py`;
it is shown only where it exceeds 1e-12. *Identity* is
`|V(A) + V(B) − (V(A∪B) + V(A∩B))|` computed from the **measured** operand volumes, so it
isolates the boolean from any error already present in the operands. Times are milliseconds,
union / intersection.

| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |
|---|---|---|---|---|---|---|---|
| `disjoint` | default | yes | 2 | 0 | 0 | 0.63 / 0.46 | tol≤1e-07 |
| `disjoint` | fuzzy=1e-5 | yes | 2 | 0 | 0 | 0.60 / 0.42 | tol≤1e-07 |
| `disjoint` | fuzzy=1e-3 | yes | 2 | 0 | 0 | 0.60 / 0.43 | tol≤1e-07 |
| `overlap_half` | default | yes | 1.5 | 0.5 | 6.66e-16 | 4.39 / 3.80 | tol≤1e-07 |
| `overlap_half` | fuzzy=1e-5 | yes | 1.5 | 0.5 | 6.66e-16 | 4.53 / 3.81 | tol≤1e-07 |
| `overlap_half` | fuzzy=1e-3 | yes | 1.5 | 0.5 | 6.66e-16 | 4.21 / 3.81 | tol≤1e-07 |
| `coplanar_faces` | default | yes | 2 | 0 | 4.44e-16 | 1.62 / 1.20 | tol≤1e-07 |
| `coplanar_faces` | fuzzy=1e-5 | yes | 2 | 0 | 4.44e-16 | 1.71 / 1.19 | tol≤1e-07 |
| `coplanar_faces` | fuzzy=1e-3 | yes | 2 | 0 | 4.44e-16 | 1.57 / 1.18 | tol≤1e-07 |
| `shared_edge` | default | yes | 2 | 0 | 2.22e-16 | 1.58 / 1.14 | tol≤1e-07 |
| `shared_edge` | fuzzy=1e-5 | yes | 2 | 0 | 2.22e-16 | 1.51 / 1.06 | tol≤1e-07 |
| `shared_edge` | fuzzy=1e-3 | yes | 2 | 0 | 2.22e-16 | 1.51 / 1.14 | tol≤1e-07 |
| `touching_vertex` | default | yes | 2 | 0 | 2.22e-16 | 1.22 / 0.74 | tol≤1e-07 |
| `touching_vertex` | fuzzy=1e-5 | yes | 2 | 0 | 2.22e-16 | 1.31 / 0.78 | tol≤1e-07 |
| `touching_vertex` | fuzzy=1e-3 | yes | 2 | 0 | 2.22e-16 | 1.18 / 0.77 | tol≤1e-07 |
| `identical` | default | yes | 1 | 1 | 0 | 2.35 / 2.13 | tol≤1e-07 |
| `identical` | fuzzy=1e-5 | yes | 1 | 1 | 0 | 2.26 / 2.22 | tol≤1e-07 |
| `identical` | fuzzy=1e-3 | yes | 1 | 1 | 0 | 2.37 / 2.24 | tol≤1e-07 |
| `contained` | default | yes | 1 | 0.125 | 0 | 1.40 / 1.34 | tol≤1e-07 |
| `contained` | fuzzy=1e-5 | yes | 1 | 0.125 | 0 | 1.37 / 1.28 | tol≤1e-07 |
| `contained` | fuzzy=1e-3 | yes | 1 | 0.125 | 0 | 1.36 / 1.21 | tol≤1e-07 |
| `sliver` | default | yes | 1 | 0 (Δ1e-07) | 3.33e-08 | 3.24 / 2.65 | tol≤1.76e-07 |
| `sliver` | fuzzy=1e-5 | yes | 1 | 0 (Δ1e-07) | 3.33e-08 | 3.05 / 2.70 | tol≤5.1e-06 |
| `sliver` | fuzzy=1e-3 | yes | 1 | 0 (Δ1e-07) | 3.33e-08 | 3.31 / 2.62 | tol≤0.0005 |
| `near_degenerate_triangle` | default | yes | 1 | 1 | 2.22e-16 | 2.62 / 2.42 | tol≤1e-07 |
| `near_degenerate_triangle` | fuzzy=1e-5 | yes | 1 | 1 | 0 | 2.55 / 2.32 | tol≤1.02e-06 |
| `near_degenerate_triangle` | fuzzy=1e-3 | yes | 1 | 1 | 0 | 2.49 / 2.52 | tol≤1.02e-06 |
| `wall_with_openings` | default | yes | 12.6 | 5.4 | 1.42e-14 | 53.97 / 49.24 | tol≤1.5e-07 |
| `wall_with_openings` | fuzzy=1e-5 | yes | 12.6 | 5.4 | 1.42e-14 | 54.47 / 48.72 | tol≤5.1e-06 |
| `wall_with_openings` | fuzzy=1e-3 | yes | 12.6 | 5.4 | 1.42e-14 | 51.64 / 48.32 | tol≤0.0005 |

**Summary:** 30 of 30 case×setting combinations produced results that
`BRepCheck_Analyzer` reports valid for both the union and the intersection.

## Probe A — does tolerance growth compound over chained booleans?

Eight unit boxes fused one at a time, each separated from the previous by a 5e-6 gap
(wider than `Precision::Confusion()`, inside `SetFuzzyValue(1e-5)`), so every step needs
the fuzzy value to glue. *Excess volume* is the measured volume minus the nominal N+1;
it is the gap the tolerance bridged and the volume integral then counted as solid.

| Step | Solids | V | max entity tolerance | Excess volume |
|---|---|---|---|---|
| 0 (input) | 1 | 1 | 1e-07 | - |
| 1 | 1 | 2.000003333 | 5.1e-06 | 3.33e-06 |
| 2 | 1 | 3.000006667 | 5.1e-06 | 6.67e-06 |
| 3 | 1 | 4.00001 | 5.1e-06 | 1e-05 |
| 4 | 1 | 5.000013333 | 5.1e-06 | 1.33e-05 |
| 5 | 1 | 6.000016667 | 5.1e-06 | 1.67e-05 |
| 6 | 1 | 7.00002 | 5.1e-06 | 2e-05 |
| 7 | 1 | 8.000023333 | 5.1e-06 | 2.33e-05 |
| 8 | 1 | 9.000026667 | 5.1e-06 | 2.67e-05 |

## Probe B — does a boolean raise the tolerance of its input shapes?

`BOPAlgo` is destructive by default (`SetNonDestructive(false)`). Measured on the operands
before and after one `BRepAlgoAPI_Fuse`.

| Case | Setting | max tol(inputs) before | after | max tol(result) |
|---|---|---|---|---|
| `overlap_half` | default | 1e-07 | 1e-07 | 1e-07 |
| `overlap_half` | fuzzy=1e-3 | 1e-07 | 1e-07 | 1e-07 |
| `sliver` | default | 1.525e-07 | 1.525e-07 | 1.757e-07 |
| `sliver` | fuzzy=1e-3 | 1.525e-07 | 0.0005001 | 0.0005001 |

## Probe C — is a sewing tolerance below `Precision::Confusion()` honoured?

`BRepBuilderAPI_Sewing::Init` clamps with `std::max(tolerance, Confusion())`. This probe
sews the same operand at 1e-7, 1e-8, 1e-9 and 1e-12 and hashes the ASCII BREP written by
`BRepTools::Write` (triangulation included), so *identical* here means byte-identical
serialised output and not merely equal volume.

| Operand | Requested sewing tolerance | SHA-256 of the BREP (first 16 hex) | Volume | vs. 1e-7 |
|---|---|---|---|---|
| `overlap_half` A (unit cube) | 1e-07 | `672b8c827e805dc8` | 1 | same as 1e-7 |
| `overlap_half` A (unit cube) | 1e-08 | `672b8c827e805dc8` | 1 | same as 1e-7 |
| `overlap_half` A (unit cube) | 1e-09 | `672b8c827e805dc8` | 1 | same as 1e-7 |
| `overlap_half` A (unit cube) | 1e-12 | `672b8c827e805dc8` | 1 | same as 1e-7 |
| `sliver` B (1e-7 m slab) | 1e-07 | `96de201c882ab1ea` | 3.33333333343e-08 | same as 1e-7 |
| `sliver` B (1e-7 m slab) | 1e-08 | `96de201c882ab1ea` | 3.33333333343e-08 | same as 1e-7 |
| `sliver` B (1e-7 m slab) | 1e-09 | `96de201c882ab1ea` | 3.33333333343e-08 | same as 1e-7 |
| `sliver` B (1e-7 m slab) | 1e-12 | `96de201c882ab1ea` | 3.33333333343e-08 | same as 1e-7 |

## Probe D — how thin a solid will `BRepPrimAPI_MakeBox` build?

`BRepPrim_GWedge::IsDegeneratedShape()` rejects any extent `<= Precision::Confusion()`.
Measured by construction; the *exception type* is reported because "throws" and "returns
an invalid shape" are different things for a caller to handle.

| Requested thickness (m) | Built? | Exception | Volume |
|---|---|---|---|
| 1e-06 | yes | - | 1e-06 |
| 1.0001e-07 | yes | - | 1.0001e-07 |
| 1e-07 | **no** | `Standard_DomainError` | - |
| 9.9999e-08 | **no** | `Standard_DomainError` | - |
| 1e-09 | **no** | `Standard_DomainError` | - |
