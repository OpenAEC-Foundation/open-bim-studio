# Precision set — `cadkernel` raw results

Written by [`../../boolean-torture/ocs_driver/src/main.rs`](../../boolean-torture/ocs_driver/src/main.rs) (`precision` mode), the same driver and the same construction path as [`../../boolean-torture/results/opencadstudio.md`](../../boolean-torture/results/opencadstudio.md).

**Offset:** `(500000, 500000, 0)` — 500 km east, 500 km north, applied to the **input coordinates**, which is what a project modelling in a national projection does. The far result is translated back by −offset before any comparison or any volume integral.

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


## Does the 500 km offset reach the boolean?

**This question has to be answered before the table below can be read.** `cadkernel`'s crate documentation states a coordinate policy in `src/lib.rs`: *"Every entry point lifts its input into a local frame before doing any math, and shifts results back to world coordinates on the way out."* `geom2d::Frame` implements exactly that — a translation-only frame, `Frame::around` anchoring at the **midpoint of the bounding box** rather than at an arbitrary member, documented as bounding every lifted coordinate by half the extent.

*Measured, at commit `953d546b68aef4b6692566a1a9b077fc5bd9fb4f`:* `Frame::around`, `Frame::at` and `Frame::identity` are constructed **nowhere outside `src/geom2d/frame.rs` itself**, and inside that file only in its own unit tests. `grep -rn 'Frame::around\|Frame::at\|Frame::identity\|\.lift(\|\.lower('` over `src/` returns no call site in `src/brep/`. The B-rep boolean path — `make::faceted_solid`, `bounds::operation_tolerance`, `imprint::imprint`, `boolean::combine`, `brep::mesh` — does its arithmetic on the world coordinates it is handed.

So **the 500 km offset reaches the boolean in full**, and the deviations below are the unmitigated f64 answer, not a lifted one. The lift is written, documented and unwired; the `space::planar` `lift`/`lower` pair that *is* used throughout is a different operation — the 3D↔2D map onto a face's plane, not a translation for conditioning.


## `operation_tolerance` near vs far

*Measured.* `extent * 1e-8 + f64::EPSILON * coordinate_scale * 64.0`, where `coordinate_scale` is the largest absolute coordinate. The second term is what the offset moves.

| Case | Derived tolerance at the origin | at 500 km | Ratio |
|---|---|---|---|
| `overlap_half` | 1.50000213163e-8 | 2.21054486739e-8 | 1.474 |
| `coplanar_faces` | 2.00000284217e-8 | 2.71054557793e-8 | 1.355 |
| `wall_with_openings` | - | - | - (operand refused) |

The tolerance a boolean runs at is therefore **a function of where the model sits**, not only of how big it is — the same coupling the Manifold file records for its own derived tolerance. A local frame in the caller fixes the coordinates and leaves this coupling alone, because the tolerance is derived after the coordinates are handed over.


## Boolean results near vs far

*Measured.* *Vertex deviation* is the worst nearest-neighbour distance between the origin result's welded tessellation vertices and the far result's, after translating the far result back by −offset, taken as the worse of both matching directions. **The far volume is computed on the back-translated vertices**, because `signed_volume` sums products of raw coordinates and at 5e5 m the cancellation in that sum is larger than anything the kernel does — charging it to the candidate would be a measurement artefact, which is the reason the Manifold and CGAL drivers back-translate too.

| Case | Setting | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation | ms near / far | tol near / far |
|---|---|---|---|---|---|---|---|---|
| `overlap_half` | derived | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** | 30.212 / 28.373 | 1.5e-8 / 2.211e-8 |
| `overlap_half` | derived | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** | 26.841 / 31.067 | 1.5e-8 / 2.211e-8 |
| `overlap_half` | tol=1e-9 | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** | 32.363 / 32.331 | 1e-9 / 1e-9 |
| `overlap_half` | tol=1e-9 | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** | 30.379 / 28.602 | 1e-9 / 1e-9 |
| `coplanar_faces` | derived | union | yes | 2 / 2 | 0, 0 | **0 m** | 9.636 / 9.367 | 2e-8 / 2.711e-8 |
| `coplanar_faces` | derived | intersection | yes | 0 / 0 | 0, n/a | n/a (0 verts) | 9.145 / 9.608 | 2e-8 / 2.711e-8 |
| `coplanar_faces` | tol=1e-9 | union | yes | 2 / 2 | 0, 0 | **0 m** | 9.554 / 9.448 | 1e-9 / 1e-9 |
| `coplanar_faces` | tol=1e-9 | intersection | yes | 0 / 0 | 0, n/a | n/a (0 verts) | 9.290 / 9.152 | 1e-9 / 1e-9 |
| `wall_with_openings` | derived | union | **n/a — operand not built** | - | - | - | - | - |
| `wall_with_openings` | derived | intersection | **n/a — operand not built** | - | - | - | - | - |
| `wall_with_openings` | tol=1e-9 | union | **n/a — operand not built** | - | - | - | - | - |
| `wall_with_openings` | tol=1e-9 | intersection | **n/a — operand not built** | - | - | - | - | - |

**Worst vertex deviation over the whole set: 0 m**, worst relative ΔV 0. R-17's pass line is 1e-6 m and its fail line 1e-4 m.


## Probe — the tile-frame mitigation, measured

**Question:** ADR-0006 proposes f64 local coordinates in tile frames — the far placement carried *outside* the geometry. `cadkernel` does not carry it for the caller (see the first section), so the mitigation here is the caller's own: run the boolean at the origin, then move the result out to 5e5 m with `brep::place::transform` and back again, which is what a tile frame does on the way to and from the world. What does the round trip cost?

| Case | Op | Valid after the round trip? | V | Deviation vs. the origin result |
|---|---|---|---|---|
| `overlap_half` | union | yes | 1.5 | **0 m** |
| `overlap_half` | intersection | yes | 0.5 | **0 m** |
| `coplanar_faces` | union | yes | 2 | **0 m** |
| `coplanar_faces` | intersection | yes | 0 | n/a (0 verts) |
| `wall_with_openings` | union | - | - | operand refused |
| `wall_with_openings` | intersection | - | - | operand refused |

## Probe — what a 0 m deviation can and cannot show

**Question:** the main table's deviations are exactly 0 m. Is that a result about the kernel, or about the coordinates?

*Measured.* Worst `|((v + offset) − offset) − v|` over every operand vertex of the case, in `f64`, with no kernel involved — the exactness of the offset itself — beside whether the case reached the boolean at all.

| Case | Operand vertices | Offset round-trip error | Reached the boolean? |
|---|---|---|---|
| `overlap_half` | 16 | 0 | yes |
| `coplanar_faces` | 16 | 0 | yes |
| `wall_with_openings` | 104 | 2.32832e-11 | **no — `faceted_solid` refused operand B** |

The two cases that reach the boolean are built from coordinates that are multiples of 0.5 m, and 500000 ± those values is exact in `f64`, so the offset introduces no error before the boolean starts. **Every other f64 candidate also measured exactly 0 m on these two cases** — see [`../FINDINGS.md`](../FINDINGS.md) §Results, the `overlap_half` and `coplanar_faces` rows for OCCT, Manifold `Mesh64` and CGAL Epick f64. The case that separated those candidates from each other, `wall_with_openings`, is the one `faceted_solid` refuses. So this file's 0 m is **consistent with an f64 path and adds no evidence beyond the three candidates already measured**; it is not a tighter result than theirs.


## Probe — how much of a far-field volume error is the measurement's own

*Measured.* The same far solid, integrated four ways, so the back-translation in the main table is shown not to be doing the work. *Near, coords shifted* moves the **origin** result out to 5e5 m in `double` and integrates there — no boolean, no kernel, just the sum — and is the floor on what any far-field volume can be worth.

| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `Mesh::mass_properties()` |
|---|---|---|---|---|---|---|
| `overlap_half` | union | 1.5 | 1.5 | 1.5 | 1.5 | 1.5 |
| `overlap_half` | intersection | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| `coplanar_faces` | union | 2 | 2 | 2 | 2 | 2 |
| `coplanar_faces` | intersection | 0 | 0 | 0 | 0 | - |
