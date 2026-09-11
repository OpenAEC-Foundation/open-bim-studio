# Precision set — Blender raw results

Produced by [`../blender_driver.py`](../blender_driver.py). Raw data for
`../FINDINGS.md` and for
[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-11
**Offset:** `(500000.0, 500000.0, 0.0)` (500 km east, 500 km north — a plausible distance from a national
projection's false origin to a project site).

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
| solvers measured | `EXACT, FLOAT, MANIFOLD` |
| repeats per timing | 5 (median reported) |
| startup | `--factory-startup` (no add-ons) |

## Storage — the float32 round trip, before any boolean

A `Mesh` stores vertex positions as float32. This probe writes a coordinate into a
mesh and reads it back; nothing else happens to it. *ULP* is the distance to the next
representable float32, computed in Python from the IEEE-754 bit pattern.

| Coordinate | float32 ULP | Written | Read back | Round-trip error |
|---|---|---|---|---|
| `0` | 1.4013e-45 | 0 | 0 | 0 |
| `1` | 1.19209e-07 | 1 | 1 | 0 |
| `0.1` | 7.45058e-09 | 0.10000000000000001 | 0.10000000149011612 | 1.49012e-09 |
| `1e-07` | 7.10543e-15 | 9.9999999999999995e-08 | 1.0000000116860974e-07 | 1.16861e-15 |
| `500000` | 0.03125 | 500000 | 500000 | 0 |
| `500000.1` | 0.03125 | 500000.09999999998 | 500000.09375 | 0.00625 |
| `500000.001` | 0.03125 | 500000.00099999999 | 500000 | 0.001 |
| `500001` | 0.03125 | 500001 | 500001 | 0 |

The 500 km rows are the finding: a float32 near 5e5 has an ULP of 0.03125 m, so **no**
coordinate detail below ~3 cm survives being stored at that distance from the origin,
regardless of what any algorithm does afterwards.

Operand round trip per case, worst over all vertices of A and B:

| Case | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |
|---|---|---|---|
| `overlap_half` | 16 | 0 | **0** |
| `coplanar_faces` | 16 | 0 | **0** |
| `wall_with_openings` | 104 | 3.8147e-07 | **0.01375** |

## Boolean results near vs far

The offset is applied to the **vertex coordinates**, which is what a project does when
it models in a national projection. *Vertex deviation* is the worst nearest-neighbour
distance after translating the far result back by −offset, taken as the worse of both
matching directions. *ΔV* is the far volume minus the near volume, absolute and
relative to the near volume — the same two forms `results/occt.md` reports, so the
candidates can be compared column for column. Times are the median of 5 fresh runs.

| Case | Solver | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far |
|---|---|---|---|---|---|---|---|
| `overlap_half` | Exact | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 24/24 v | 3.01 / 3.48 |
| `overlap_half` | Exact | common | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 16/16 v | 3.22 / 3.57 |
| `overlap_half` | Fast (float) | union | **no** | 1 / 1.91666666667 | 0.916667 (0.916667 rel) | **0.5 m** over 32/43 v | 0.46 / 0.57 |
| `overlap_half` | Fast (float) | common | **no** | 1 / 0.0833333333333 | -0.916667 (-0.916667 rel) | **0.5 m** over 32/17 v | 0.46 / 0.39 |
| `overlap_half` | Manifold | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 16/16 v | 0.56 / 0.51 |
| `overlap_half` | Manifold | common | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 12/12 v | 0.66 / 0.54 |
| `coplanar_faces` | Exact | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 1.23 / 1.55 |
| `coplanar_faces` | Exact | common | yes (empty, as expected) | 0 / 0 | 0 (nan rel) | **- m** over 0/0 v | 1.34 / 1.58 |
| `coplanar_faces` | Fast (float) | union | **no** | 2 / 2 | 0 (0 rel) | **0 m** over 22/23 v | 0.28 / 0.27 |
| `coplanar_faces` | Fast (float) | common | yes (empty, as expected) | 0 / 0 | 0 (nan rel) | **0 m** over 4/4 v | 0.27 / 0.30 |
| `coplanar_faces` | Manifold | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 0.47 / 0.55 |
| `coplanar_faces` | Manifold | common | yes (empty, as expected) | 0 / 0 | 0 (nan rel) | **- m** over 0/0 v | 0.30 / 0.33 |
| `wall_with_openings` | Exact | union | yes | 12.6000000179 / 12.7499997485 | 0.15 (0.0119047 rel) | **0.0348212 m** over 320/320 v | 17.94 / 24.66 |
| `wall_with_openings` | Exact | common | yes | 5.39999982566 / 5.6249995809 | 0.225 (0.0416666 rel) | **0.0348212 m** over 216/216 v | 18.87 / 25.01 |
| `wall_with_openings` | Fast (float) | union | near yes / far **no** | 12.5999999541 / 10.2739276984 | -2.32607 (-0.184609 rel) | **0.13758 m** over 320/272 v | 1.42 / 1.37 |
| `wall_with_openings` | Fast (float) | common | near yes / far **no** | 5.39999939549 / 7.56262934166 | 2.16263 (0.400487 rel) | **0.0947531 m** over 216/264 v | 1.29 / 1.22 |
| `wall_with_openings` | Manifold | union | yes | 12.6000000179 / 12.7499997485 | 0.15 (0.0119047 rel) | **0.0348212 m** over 320/320 v | 1.85 / 1.86 |
| `wall_with_openings` | Manifold | common | yes | 5.39999982566 / 5.6249995809 | 0.225 (0.0416666 rel) | **0.0435011 m** over 216/214 v | 1.57 / 1.65 |

**Worst vertex deviation over the whole set: 0.5 m.** R-17's pass line is 1e-6 m and its
fail line is 1e-4 m.

## Probe — the same offset carried by the object transform

Identical geometry, but the 500 km sits in each object's `location` and the vertex data
stays at the origin: a local frame with the far placement outside it. Both operands
carry the same location, so the modifier evaluates in A's local space. This is the
mitigation ADR-0006 proposes, measured on the candidate rather than assumed.

| Case | Solver | Op | Valid? | V | Vertex deviation vs. the origin run |
|---|---|---|---|---|---|
| `overlap_half` | Exact | union | yes | 1.5 | 0 m |
| `overlap_half` | Exact | common | yes | 0.5 | 0 m |
| `overlap_half` | Fast (float) | union | **no** | 1 | 0 m |
| `overlap_half` | Fast (float) | common | **no** | 1 | 0.5 m |
| `overlap_half` | Manifold | union | yes | 1.5 | 0 m |
| `overlap_half` | Manifold | common | yes | 0.5 | 0 m |
| `coplanar_faces` | Exact | union | yes | 2 | 0 m |
| `coplanar_faces` | Exact | common | yes (empty, as expected) | 0 | - m |
| `coplanar_faces` | Fast (float) | union | **no** | 2 | 0 m |
| `coplanar_faces` | Fast (float) | common | yes (empty, as expected) | 0 | 0 m |
| `coplanar_faces` | Manifold | union | yes | 2 | 0 m |
| `coplanar_faces` | Manifold | common | yes (empty, as expected) | 0 | - m |
| `wall_with_openings` | Exact | union | yes | 12.6000000179 | 0 m |
| `wall_with_openings` | Exact | common | yes | 5.39999982566 | 0 m |
| `wall_with_openings` | Fast (float) | union | yes | 12.5999999541 | 0 m |
| `wall_with_openings` | Fast (float) | common | yes | 5.39999939549 | 0 m |
| `wall_with_openings` | Manifold | union | yes | 12.6000000179 | 0 m |
| `wall_with_openings` | Manifold | common | yes | 5.39999982566 | 0 m |

The modifier evaluates in the modified object's local space, so the result mesh is
expressed in that space too: these deviations are measured against the origin run
directly, with no translation back.

