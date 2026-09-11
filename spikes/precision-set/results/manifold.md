# Precision set — Manifold raw results

Produced by [`../manifold_driver.py`](../manifold_driver.py). Raw data for
`../FINDINGS.md` and for
[`../../../docs/research/kernels/manifold.md`](../../../docs/research/kernels/manifold.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-11
**Offset:** `(500000.0, 500000.0, 0.0)` (500 km east, 500 km north — a plausible distance from a national
projection's false origin to a project site).

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

Two input paths are measured throughout: **f32** is `manifold3d.Mesh` (float32
positions, uint32 indices), the type the C++ `MeshGL` alias resolves to and the one
Blender feeds the library; **f64** is `manifold3d.Mesh64` (float64, uint64).
`Manifold::Impl` stores positions as `vec3`, i.e. double, in both cases — what the
f32 path costs is paid on the way in, not in the algorithm. Every result is exported
through `to_mesh64()` so the readback never rounds.

## Storage — the coordinate round trip, before any boolean

A unit box with its minimum corner at `(c, c, 0)`, read back through
`Manifold.bounding_box()`. *ULP* is the distance to the next representable float32.
*Tolerance* is `Manifold.get_tolerance()`: Manifold derives it from the bounding box
as `kPrecision * Box::Scale()` with `kPrecision = 1e-12`, and `Box::Scale()` is the
**largest absolute coordinate**, not the diagonal — so the tolerance is a function of
distance from the origin even on the f64 path.

| Coordinate | float32 ULP | f32 read back | f32 error | f32 tolerance | f64 read back | f64 error | f64 tolerance |
|---|---|---|---|---|---|---|---|
| `0.0` | 1.4013e-45 | 0 | 0 | 1.19209e-07 | 0 | 0 | 1e-12 |
| `1.0` | 1.19209e-07 | 1 | 0 | 2.38419e-07 | 1 | 0 | 2e-12 |
| `0.1` | 7.45058e-09 | 0.10000000149011612 | 1.49012e-09 | 1.3113e-07 | 0.10000000000000001 | 0 | 1.1e-12 |
| `1e-07` | 7.10543e-15 | 1.0000000116860974e-07 | 1.16861e-15 | 1.19209e-07 | 9.9999999999999995e-08 | 0 | 1e-12 |
| `500000.0` | 0.03125 | 500000 | 0 | 0.0596048 | 500000 | 0 | 5.00001e-07 |
| `500000.1` | 0.03125 | 500000.09375 | 0.00625 | 0.0596048 | 500000.09999999998 | 0 | 5.00001e-07 |
| `500000.001` | 0.03125 | 500000 | 0.001 | 0.0596048 | 500000.00099999999 | 0 | 5.00001e-07 |
| `500001.0` | 0.03125 | 500001 | 0 | 0.0596049 | 500001 | 0 | 5.00002e-07 |

Operand round trip per case, worst over all vertices of A and B, matched
nearest-neighbour against the coordinates the reference set specifies:

| Case | Precision | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |
|---|---|---|---|---|
| `overlap_half` | f32 | 16 | 0 | **0** |
| `overlap_half` | f64 | 16 | 0 | **0** |
| `coplanar_faces` | f32 | 16 | 0 | **0** |
| `coplanar_faces` | f64 | 16 | 0 | **0** |
| `wall_with_openings` | f32 | 104 | 3.93255e-07 | **0.0151038** |
| `wall_with_openings` | f64 | 104 | 0 | **0** |

## Boolean results near vs far

The offset is applied to the **vertex coordinates**. *Vertex deviation* is the worst
nearest-neighbour distance after translating the far result back by −offset, taken as
the worse of both matching directions. *ΔV* is the far volume minus the near volume,
absolute and relative — the same two forms [`results/occt.md`](occt.md) and
[`results/blender.md`](blender.md) report, so the candidates compare column for column.
*Tolerance* is `get_tolerance()` on the near and the far result.

**Comparability caveat.** "Compare column for column" is about what each *ΔV* column
measures (the far solid's volume, near vs. far), not about a shared formula. This
driver's *V near / far* is `reference.signed_volume` over exported triangles;
`results/blender.md`'s precision driver back-translates before integrating, with the
same function (`blender_driver.py#L341`, the `far_back = [...]` assignment feeding
`signed_volume`). `results/occt.md`'s driver never calls `reference.signed_volume` at
all — every volume there is OCCT's own `BRepGProp.VolumeProperties_s` integrator
(`spikes/boolean-torture/occt_common.py#L70-L72`). So this driver's and Blender's
columns share a measurement method; OCCT's does not. `docs/research/kernels/manifold.md`
§A warning about measuring volume at 500 km states this explicitly.

**The far volume is computed on the back-translated vertices**, for the reason the
last probe in this file measures: `reference.signed_volume` sums
`x0*(y1*z2 − z1*y2)` over raw coordinates, and at 5e5 m each term is ~1e17 against a
sum of ~10, so the integrand loses ~1e-4 m³ to cancellation *before any library is
involved*. Reporting the raw-coordinate figure here would have charged that to
Manifold.

| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far | tol near / far |
|---|---|---|---|---|---|---|---|---|
| `overlap_half` | f64 | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 16/16 v | 0.175 / 0.388 | 1.5e-12 / 5e-07 |
| `overlap_half` | f64 | intersection | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 8/8 v | 0.196 / 0.198 | 1.5e-12 / 5e-07 |
| `overlap_half` | f32 | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 16/16 v | 0.211 / 0.270 | 1.788e-07 / 0.0596 |
| `overlap_half` | f32 | intersection | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 8/8 v | 0.182 / 0.107 | 1.788e-07 / 0.0596 |
| `coplanar_faces` | f64 | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 0.210 / 0.168 | 2e-12 / 5e-07 |
| `coplanar_faces` | f64 | intersection | yes | 0 / 0 | 0 (nan rel) | **0 m** over 4/4 v | 0.079 / 0.079 | 2e-12 / 5e-07 |
| `coplanar_faces` | f32 | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 0.144 / 0.169 | 2.384e-07 / 0.0596 |
| `coplanar_faces` | f32 | intersection | yes | 0 / 0 | 0 (nan rel) | **0 m** over 4/4 v | 0.115 / 0.095 | 2.384e-07 / 0.0596 |
| `wall_with_openings` | f64 | union | yes | 12.6 / 12.5999999999 | -1.39659e-10 (-1.1084e-11 rel) | **3.29273e-11 m** over 200/200 v | 1.318 / 1.238 | 1e-11 / 5e-07 |
| `wall_with_openings` | f64 | intersection | yes | 5.4 / 5.39999999979 | -2.0955e-10 (-3.88055e-11 rel) | **2.60313e-11 m** over 96/96 v | 0.981 / 0.855 | 1e-11 / 5e-07 |
| `wall_with_openings` | f32 | union | near: yes; far: **no** — 1 zero-area faces | 12.6000000179 / 12.7499997485 | 0.15 (0.0119047 rel) | **0.0185826 m** over 200/200 v | 1.148 / 1.134 | 1.192e-06 / 0.05961 |
| `wall_with_openings` | f32 | intersection | yes | 5.39999982566 / 5.6249995809 | 0.225 (0.0416666 rel) | **0.0185826 m** over 96/96 v | 0.835 / 0.837 | 1.192e-06 / 0.05961 |

**Worst vertex deviation over the whole set: 0.0185826 m.** R-17's pass line is 1e-6 m
and its fail line is 1e-4 m.

## Probe — the same offset carried by `Manifold.translate()`

Identical geometry built at the origin, then moved 500 km by
`Manifold.translate()` before the boolean, and the result translated back. This is
the local-frame mitigation ADR-0006 proposes, measured on the candidate rather than
assumed. Manifold's transforms are lazy but not symbolic: `Impl::Transform` writes the
moved coordinates into `vertPos_` and then re-derives epsilon from the **new** bounding
box, so the tolerance column is the part to read.

| Case | Setting | Op | Valid? | V | Deviation vs. the origin run | tol origin → translated |
|---|---|---|---|---|---|---|
| `overlap_half` | f64 | union | yes | 1.5 | **0 m** | 1.5e-12 → 5e-07 |
| `overlap_half` | f64 | intersection | yes | 0.5 | **0 m** | 1.5e-12 → 5e-07 |
| `overlap_half` | f32 | union | yes | 1.5 | **0 m** | 1.788e-07 → 5e-07 |
| `overlap_half` | f32 | intersection | yes | 0.5 | **0 m** | 1.788e-07 → 5e-07 |
| `coplanar_faces` | f64 | union | yes | 2 | **0 m** | 2e-12 → 5e-07 |
| `coplanar_faces` | f64 | intersection | yes | 0 | **0 m** | 2e-12 → 5e-07 |
| `coplanar_faces` | f32 | union | yes | 2 | **0 m** | 2.384e-07 → 5e-07 |
| `coplanar_faces` | f32 | intersection | yes | 0 | **0 m** | 2.384e-07 → 5e-07 |
| `wall_with_openings` | f64 | union | yes | 12.5999999999 | **3.29273e-11 m** | 1e-11 → 5e-07 |
| `wall_with_openings` | f64 | intersection | yes | 5.39999999979 | **2.60313e-11 m** | 1e-11 → 5e-07 |
| `wall_with_openings` | f32 | union | yes | 12.6000000179 | **0 m** | 1.192e-06 → 1.192e-06 |
| `wall_with_openings` | f32 | intersection | yes | 5.39999982566 | **0 m** | 1.192e-06 → 1.192e-06 |

## Probe — how much of a far-field volume error is the measurement's own

All five columns describe the **same solid**, on the f64 path. *Near* is
`reference.signed_volume` at the origin. *Near, coords shifted* adds the offset to
every vertex of the near result and re-integrates: no boolean, no library, so the
difference from the first column is pure floating-point cancellation in the
divergence-theorem sum. *Far, raw* is the same function on the far result's own
coordinates; *Far, back-translated* is the number the table above reports; *Far,
`Manifold.volume()`* is the library's own figure, which sums
`dot(cross(v1 − v0, v2 − v0), v0) / 6` with Kahan compensation
([`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294)),
i.e. it subtracts the common offset before multiplying.

| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `Manifold.volume()` |
|---|---|---|---|---|---|---|
| `overlap_half` | union | 1.5 | 1.5 | 1.5 | 1.5 | 1.50000000002 |
| `overlap_half` | intersection | 0.5 | 0.5 | 0.5 | 0.5 | 0.499999999995 |
| `coplanar_faces` | union | 2 | 2 | 2 | 2 | 2.00000000001 |
| `coplanar_faces` | intersection | 0 | 0 | 0 | 0 | 0 |
| `wall_with_openings` | union | 12.6 | 12.5999209454 | 12.5999143333 | 12.5999999999 | 12.5999999999 |
| `wall_with_openings` | intersection | 5.4 | 5.39989759799 | 5.39989759799 | 5.39999999979 | 5.39999999962 |
