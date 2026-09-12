# Boolean torture set — `cadkernel` raw results

Written by [`../ocs_driver/src/main.rs`](../ocs_driver/src/main.rs). `cadkernel` is the MPL-2.0 B-rep kernel that Open CAD Studio's solid modelling runs on; see [`../../../docs/research/kernels/opencadstudio.md`](../../../docs/research/kernels/opencadstudio.md).

The ten cases are [`../../../reference/boolean_torture_set.py`](../../../reference/boolean_torture_set.py) verbatim, carried into Rust as JSON by [`../ocs_driver/dump_cases.py`](../ocs_driver/dump_cases.py). No case is added, dropped or adjusted.

## Environment

*Measured.*

| | |
|---|---|
| Run date | 2026-09-12 |
| CPU | `Intel(R) Core(TM) i9-14900HX (32 logical processors)` |
| RAM | 32 GB |
| OS | Windows 11 Pro, 10.0.26200 |
| Toolchain | `cargo 1.94.0 (85eff7c80 2026-01-15)` / `rustc 1.94.0 (4a4ef493e 2026-03-02)` |
| `cadkernel` | commit `953d546b68aef4b6692566a1a9b077fc5bd9fb4f`, <https://github.com/HakanSeven12/cadkernel>, `default-features = false`, `features = ["brep"]` |
| Build profile | `--release`; `spade` 2.15.1 and `rustc-hash` 2.x resolved through `Cargo.lock`, committed beside this driver |
| Tessellation | `brep::mesh::tessellate` with `TessellationTolerance::new(max_angle = 0.2 rad, linear = 0.000000001 m)`; positions welded at 0.000000000001 m before the topology check |
| Repeats | 5, median reported, operands rebuilt inside every repeat |


## Construction of the operands

*Measured.* Every operand goes through `brep::make::faceted_solid(&vertices, &faces)`, which takes the reference triangle soup as-is. **Its refusal is an `Option::None`, not a typed error** — the kernel's typed refusal (`Snag`) exists only on the boolean, so a construction failure here carries no machine-readable reason and the cause below is read out of the source, not out of the return value.

*Volume* is this driver's `signed_volume` over the tessellation; *kernel V* is `Mesh::mass_properties()`. *Flaws* is `Body::validate()`.

| Case | Operand | Built? | Lumps/shells/faces | Volume | kernel V | Specified V | Flaws | Derived tolerance |
|---|---|---|---|---|---|---|---|---|
| `disjoint` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 5.00000710543e-8 |
| `disjoint` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 5.00000710543e-8 |
| `overlap_half` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 1.50000213163e-8 |
| `overlap_half` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 1.50000213163e-8 |
| `coplanar_faces` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `coplanar_faces` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `shared_edge` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `shared_edge` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `touching_vertex` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `touching_vertex` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 2.00000284217e-8 |
| `identical` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 1.00000142109e-8 |
| `identical` | B | yes | 1/1/12 | 1 | 1 | 1 | none | 1.00000142109e-8 |
| `contained` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 1.00000142109e-8 |
| `contained` | B | yes | 1/1/12 | 0.125 | 0.125 | 0.125 | none | 1.00000142109e-8 |
| `sliver` | A | yes | 1/1/12 | 1 | 1 | 1 | none | 1.00000142109e-8 |
| `sliver` | B | yes | 1/1/12 | 9.99999999474e-8 | 9.99999999474e-8 | 9.99999999474e-8 | none | 1.00000142109e-8 |
| `near_degenerate_triangle` | A | yes | 1/1/12 | 1 | 1 | 1 | none | - |
| `near_degenerate_triangle` | B | **no — `faceted_solid` returned `None`** | - | - | - | 1 | - | - |
| `wall_with_openings` | A | yes | 1/1/12 | 9 | 9 | 9 | none | - |
| `wall_with_openings` | B | **no — `faceted_solid` returned `None`** | - | - | - | 9 | - | - |

## Boolean results

*Measured.* *Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` from the **measured** operand volumes in the table above, so it isolates the boolean from error already in the operands. A case whose operands cannot be built has no boolean to measure and its row says so. `ms (∪ / ∩)` is the median of 5 runs, operands rebuilt inside every repeat. **Read the ms column as an order of magnitude and not as a benchmark** — the paragraph under the table measures why, from this table's own rows.

| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |
|---|---|---|---|---|---|---|---|
| `disjoint` | derived | yes | 2 | 0 | 0 | 1.270 / 0.740 | ∩ empty, as expected; derived tol 5.00000710543e-8 |
| `overlap_half` | derived | yes | 1.5 | 0.5 | 0 | 32.256 / 30.544 | derived tol 1.50000213163e-8 |
| `coplanar_faces` | derived | yes | 2 | 0 | 0 | 10.874 / 10.469 | ∩ empty, as expected; derived tol 2.00000284217e-8 |
| `shared_edge` | derived | **no** | - | 0 | - | 6.485 / 4.125 | ∪ refused: `Snag::CutRefused`; ∩ empty, as expected; derived tol 2.00000284217e-8 |
| `touching_vertex` | derived | yes | 2 | 0 | 0 | 3.097 / 2.925 | ∩ empty, as expected; derived tol 2.00000284217e-8 |
| `identical` | derived | yes | 1 | 1 | 0 | 15.984 / 16.796 | derived tol 1.00000142109e-8 |
| `contained` | derived | yes | 1 | 0.125 | 0 | 1.348 / 0.831 | derived tol 1.00000142109e-8 |
| `sliver` | derived | yes | 1 | 9.99999999474e-8 | 0 | 50.716 / 50.748 | derived tol 1.00000142109e-8 |
| `near_degenerate_triangle` | derived | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |
| `wall_with_openings` | derived | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |
| `disjoint` | tol=1e-9 | yes | 2 | 0 | 0 | 0.736 / 0.497 | ∩ empty, as expected |
| `overlap_half` | tol=1e-9 | yes | 1.5 | 0.5 | 0 | 34.235 / 38.321 | - |
| `coplanar_faces` | tol=1e-9 | yes | 2 | 0 | 0 | 11.798 / 11.501 | ∩ empty, as expected |
| `shared_edge` | tol=1e-9 | **no** | - | 0 | - | 4.782 / 4.051 | ∪ refused: `Snag::CutRefused`; ∩ empty, as expected |
| `touching_vertex` | tol=1e-9 | yes | 2 | 0 | 0 | 4.426 / 2.771 | ∩ empty, as expected |
| `identical` | tol=1e-9 | yes | 1 | 1 | 0 | 13.257 / 13.017 | - |
| `contained` | tol=1e-9 | yes | 1 | 0.125 | 0 | 0.504 / 0.706 | - |
| `sliver` | tol=1e-9 | yes | 1 | 9.99999999474e-8 | 0 | 50.391 / 47.508 | - |
| `near_degenerate_triangle` | tol=1e-9 | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |
| `wall_with_openings` | tol=1e-9 | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |
| `disjoint` | tol=1e-6 | yes | 2 | 0 | 0 | 0.764 / 0.522 | ∩ empty, as expected |
| `overlap_half` | tol=1e-6 | yes | 1.5 | 0.5 | 0 | 32.199 / 29.672 | - |
| `coplanar_faces` | tol=1e-6 | yes | 2 | 0 | 0 | 10.126 / 9.378 | ∩ empty, as expected |
| `shared_edge` | tol=1e-6 | **no** | - | 0 | - | 3.441 / 3.189 | ∪ refused: `Snag::CutRefused`; ∩ empty, as expected |
| `touching_vertex` | tol=1e-6 | yes | 2 | 0 | 0 | 2.592 / 2.482 | ∩ empty, as expected |
| `identical` | tol=1e-6 | yes | 1 | 1 | 0 | 11.983 / 15.541 | - |
| `contained` | tol=1e-6 | yes | 1 | 0.125 | 0 | 0.522 / 0.916 | - |
| `sliver` | tol=1e-6 | **no** | - | - | - | 27.522 / 25.720 | ∪ refused: `Snag::CutRefused`; ∩ refused: `Snag::CutRefused` |
| `near_degenerate_triangle` | tol=1e-6 | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |
| `wall_with_openings` | tol=1e-6 | **n/a — operand B not built** | - | - | - | - | `faceted_solid` refused; no boolean ran |

### How much of that ms column is the machine

*Measured, from the rows above and nothing else.* Every case except `sliver` runs the same geometry through the same code path at all three settings — the tolerances differ by orders of magnitude but none of them changes what is classified — so **the spread between one case's three rows is this machine's noise, not a tolerance effect**. `sliver` is excluded because its 1e-6 row genuinely does different work (it refuses).

| Case | Op | ms at the three settings | Spread |
|---|---|---|---|
| `disjoint` | ∪ | 1.270 / 0.736 / 0.764 | ×1.73 |
| `disjoint` | ∩ | 0.740 / 0.497 / 0.522 | ×1.49 |
| `overlap_half` | ∪ | 32.256 / 34.235 / 32.199 | ×1.06 |
| `overlap_half` | ∩ | 30.544 / 38.321 / 29.672 | ×1.29 |
| `coplanar_faces` | ∪ | 10.874 / 11.798 / 10.126 | ×1.17 |
| `coplanar_faces` | ∩ | 10.469 / 11.501 / 9.378 | ×1.23 |
| `shared_edge` | ∪ | 6.485 / 4.782 / 3.441 | ×1.88 |
| `shared_edge` | ∩ | 4.125 / 4.051 / 3.189 | ×1.29 |
| `touching_vertex` | ∪ | 3.097 / 4.426 / 2.592 | ×1.71 |
| `touching_vertex` | ∩ | 2.925 / 2.771 / 2.482 | ×1.18 |
| `identical` | ∪ | 15.984 / 13.257 / 11.983 | ×1.33 |
| `identical` | ∩ | 16.796 / 13.017 / 15.541 | ×1.29 |
| `contained` | ∪ | 1.348 / 0.504 / 0.522 | ×2.68 |
| `contained` | ∩ | 0.831 / 0.706 / 0.916 | ×1.3 |

Worst spread over identical work in this session: **×2.68**. Any cross-candidate timing comparison in [`../FINDINGS.md`](../FINDINGS.md) has to survive that factor before it means anything.


## Summary

*Measured.* *Correct* is both volumes within `1e-6 * max(1, |expected|)` of the analytic expectation — the definition [`blender.md`](blender.md) fixes and the Manifold and CGAL files adopt. A case whose operands `faceted_solid` refused counts as neither valid nor correct.

| Setting | Valid /10 | Correct /10 | Worst identity residual | Time range (ms) |
|---|---|---|---|---|
| derived | **7** | 7 | 0 | 0.740 – 50.748 |
| tol=1e-9 | **7** | 7 | 0 | 0.497 – 50.391 |
| tol=1e-6 | **6** | 6 | 0 | 0.522 – 32.199 |

## Probe A — the twelve-shell cutting tool

**Question:** what does `faceted_solid` do with `wall_with_openings` operand B — twelve disconnected closed boxes in one triangle soup, the object every other candidate was handed as a single multi-component solid?

*Measured.* `faceted_solid` on the twelve-shell soup: **`None`**.

*Measured, by splitting the soup into its connected components in this driver and offering each one separately:*

| Shell | Verts | Faces | Built? | Volume |
|---|---|---|---|---|
| 1 | 8 | 12 | yes | 0.75 |
| 2 | 8 | 12 | yes | 0.75 |
| 3 | 8 | 12 | yes | 0.75 |
| 4 | 8 | 12 | yes | 0.75 |
| 5 | 8 | 12 | yes | 0.75 |
| 6 | 8 | 12 | yes | 0.75 |
| 7 | 8 | 12 | yes | 0.75 |
| 8 | 8 | 12 | yes | 0.75 |
| 9 | 8 | 12 | yes | 0.75 |
| 10 | 8 | 12 | yes | 0.75 |
| 11 | 8 | 12 | yes | 0.75 |
| 12 | 8 | 12 | yes | 0.75 |

12 of 12 shells build individually, total volume 9. The whole soup does not: `brep::make::faceted_solid` counts the connected components of the face graph and returns `None` unless there is exactly one, with the reason stated in its own source — *"A disconnected or nested shell needs explicit lump/cavity containment. Until that topology is represented, accept only one closed shell so a cavity can never be silently converted into filled material."* This is a **refusal, not a wrong answer**, and it is the reason `wall_with_openings` has no boolean row above.


## Probe B — the T-junction operand

**Question:** `near_degenerate_triangle` operand B splits the cube's top face by inserting a vertex *on* the edge v5→v6, leaving a T-junction. Manifold refuses it with `NotManifold`; CGAL builds it but reports it not closed. What does `faceted_solid` do?

*Measured.* Operand A: **built**. Operand B: **`None`**.

*Inferred, from the source:* `faceted_solid` builds an undirected edge-use map and requires `entries.len() == 2` for **every** edge before it will proceed. A T-junction leaves the unsplit side of v5→v6 used once and the two split halves used once each, so the map fails and the constructor returns `None` — the same precondition Manifold enforces, reported without a name.


## Probe C — the 1e-7 m slab against the tolerance

**Question:** OCCT's sewing tolerance degraded the slab at construction and Manifold deleted it at tolerance 1e-6. Does `cadkernel` keep it, and at which boolean tolerance does it stop keeping it?

| Boolean tolerance | ∩ valid? | V(∩) | Δ vs. 1e-07 | Note |
|---|---|---|---|---|
| 1e-12 | yes | 9.99999999474e-8 | -5.26356e-17 | - |
| 1e-9 | yes | 9.99999999474e-8 | -5.26356e-17 | - |
| 1e-8 | yes | 9.99999999474e-8 | -5.26356e-17 | - |
| 1e-7 | **refused** | - | - | `Snag::CutRefused` |
| 1e-6 | **refused** | - | - | `Snag::CutRefused` |
| 1e-5 | **refused** | - | - | `Snag::CutRefused` |

The slab's own thickness is 1e-07 m. A tolerance at or above it is a tolerance larger than the feature, which is the state that deleted the slab silently on one other candidate; a typed refusal instead of a deletion is the behaviour this column is checking for.


## Probe D — what `operation_tolerance` derives

**Question:** `brep::operation_tolerance(&[&a, &b])` is `extent * 1e-8 + f64::EPSILON * coordinate_scale * 64.0` over the two bodies' vertices. What does it actually come to on this set, and how does it compare with the smallest feature in the case?

| Case | Derived tolerance | Smallest feature in the case |
|---|---|---|
| `disjoint` | 5.00000710543e-8 | 0.5 m or larger |
| `overlap_half` | 1.50000213163e-8 | 0.5 m or larger |
| `coplanar_faces` | 2.00000284217e-8 | 0.5 m or larger |
| `shared_edge` | 2.00000284217e-8 | 0.5 m or larger |
| `touching_vertex` | 2.00000284217e-8 | 0.5 m or larger |
| `identical` | 1.00000142109e-8 | 0.5 m or larger |
| `contained` | 1.00000142109e-8 | 0.25 m |
| `sliver` | 1.00000142109e-8 | 1e-07 m (the slab thickness) |
| `near_degenerate_triangle` | - (operand refused) | - |
| `wall_with_openings` | - (operand refused) | - |

On a unit-scale case the derived value is around 1e-08 m — one order **below** the `sliver`'s 1e-07 m thickness, which is why the slab is not at risk from the default setting here. It is a bounding-box-derived number, so it tracks the model's size and, as the precision file's own probe shows, its distance from the origin.


## Probe E — run-to-run determinism

**Question:** does the same input give the same output? Two other candidates emit run-to-run variation (`problems.md` P-16).

| Case | Op | Runs | Distinct (verts, tris, volume) signatures |
|---|---|---|---|
| `disjoint` | union | 10 | 1 — 16v/24t/V=2 |
| `disjoint` | intersection | 10 | 1 — 0v/0t/V=0 |
| `overlap_half` | union | 10 | 1 — 24v/44t/V=1.5 |
| `overlap_half` | intersection | 10 | 1 — 16v/28t/V=0.5 |
| `coplanar_faces` | union | 10 | 1 — 30v/56t/V=2 |
| `coplanar_faces` | intersection | 10 | 1 — 0v/0t/V=0 |
| `shared_edge` | union | 10 | 1 — Snag::CutRefused |
| `shared_edge` | intersection | 10 | 1 — 0v/0t/V=0 |
| `touching_vertex` | union | 10 | 1 — 15v/24t/V=2 |
| `touching_vertex` | intersection | 10 | 1 — 0v/0t/V=0 |
| `identical` | union | 10 | 1 — 8v/12t/V=1 |
| `identical` | intersection | 10 | 1 — 8v/12t/V=1 |
| `contained` | union | 10 | 1 — 8v/12t/V=1 |
| `contained` | intersection | 10 | 1 — 8v/12t/V=0.125 |
| `sliver` | union | 10 | 1 — 28v/52t/V=1 |
| `sliver` | intersection | 10 | 1 — 20v/36t/V=9.9999999947364415e-8 |
