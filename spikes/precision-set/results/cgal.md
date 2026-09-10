# Precision set — CGAL raw results

Produced by [`../cgal_driver.py`](../cgal_driver.py). Raw data for
`../FINDINGS.md` and for
[`../../../docs/research/kernels/cgal.md`](../../../docs/research/kernels/cgal.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10
**Offset:** `(500000.0, 500000.0, 0.0)` (500 km east, 500 km north — a plausible distance from a national
projection's false origin to a project site).

## Environment

| Item | Value |
|---|---|
| python | `3.12.10` |
| platform | `Windows 11 (AMD64)` |
| cpu | `Intel(R) Core(TM) i9-14900HX` |
| installed RAM | `32 GB` |
| `cgal` wheel | `6.0.1.post202410241521` |
| `CGAL_VERSION_NR` reported by the binding | `1060010900` (CGAL 6.0.1) |
| `CGAL_RELEASE_DATE` reported by the binding | `20241024` |
| CGAL source tag | `v6.0.1`, commit `50cfbde3b84dbeae8338268db2d78fe4fcb522de` |
| kernel bound | `Exact_predicates_inexact_constructions_kernel` (Epick) |
| repeats per timing | 5 (median reported) |

The kernel behind the binding is `Exact_predicates_inexact_constructions_kernel`
(Epick): **predicates are exact, constructions are rounded to `double`**. Both
settings below run with those exact predicates in force, so whatever the
f32-rounded row loses is lost to the *storage*, not to the arithmetic that
decides topology. That is the ADR-0006 question, asked of CGAL directly.

| Setting | What it does |
|---|---|
| `f64 input` | the reference set's coordinates verbatim into `Point_3` |
| `f32-rounded input` | every coordinate rounded to the nearest float32 and back before the `Point_3` is built; storage is still `double` |

## Storage — the coordinate round trip, before any boolean

A coordinate written into a `Point_3` and read back with `x()`. *ULP* is the
distance to the next representable float32. There is no tolerance column: CGAL
has no per-solid tolerance to report, which is itself the difference from
[`results/manifold.md`](manifold.md), where the same table's tolerance column is
the headline finding.

| Coordinate | float32 ULP | f64 read back | f64 error | f32 read back | f32 error |
|---|---|---|---|---|---|
| `0.0` | 1.4013e-45 | 0 | 0 | 0 | 0 |
| `1.0` | 1.19209e-07 | 1 | 0 | 1 | 0 |
| `0.1` | 7.45058e-09 | 0.10000000000000001 | 0 | 0.10000000149011612 | 1.49012e-09 |
| `1e-07` | 7.10543e-15 | 9.9999999999999995e-08 | 0 | 1.0000000116860974e-07 | 1.16861e-15 |
| `500000.0` | 0.03125 | 500000 | 0 | 500000 | 0 |
| `500000.1` | 0.03125 | 500000.09999999998 | 0 | 500000.09375 | 0.00625 |
| `500000.001` | 0.03125 | 500000.00099999999 | 0 | 500000 | 0.001 |
| `500001.0` | 0.03125 | 500001 | 0 | 500001 | 0 |

Operand round trip per case, worst over all vertices of A and B, matched
nearest-neighbour against the coordinates the reference set specifies:

| Case | Setting | Verts (A+B) | Worst round-trip error at the origin | Worst at 500 km |
|---|---|---|---|---|
| `overlap_half` | f64 input | 16 | 0 | **0** |
| `overlap_half` | f32-rounded input | 16 | 0 | **0** |
| `coplanar_faces` | f64 input | 16 | 0 | **0** |
| `coplanar_faces` | f32-rounded input | 16 | 0 | **0** |
| `wall_with_openings` | f64 input | 104 | 0 | **0** |
| `wall_with_openings` | f32-rounded input | 104 | 3.93255e-07 | **0.0151038** |

## Boolean results near vs far

The offset is applied to the **vertex coordinates**. *Vertex deviation* is the
worst nearest-neighbour distance after translating the far result back by
−offset, taken as the worse of both matching directions. *ΔV* is the far volume
minus the near volume, absolute and relative — the same two forms
[`results/occt.md`](occt.md), [`results/blender.md`](blender.md) and
[`results/manifold.md`](manifold.md) report.

**Comparability caveat**, carried over from
[`results/manifold.md`](manifold.md): the four candidates' *ΔV* columns measure
the same thing (the far solid's volume, near vs. far) but are not computed by one
formula. This driver and the Manifold and Blender drivers use
`reference.signed_volume` over exported triangles; the OCCT driver uses OCCT's own
`BRepGProp` integrator throughout.

**The far volume is computed on the back-translated vertices**, for the reason
the last probe measures: `reference.signed_volume` sums `x0*(y1*z2 − z1*y2)` over
raw coordinates, and at 5e5 m each term is ~1e17 against a sum of ~10, so the
integrand loses ~1e-4 m³ to cancellation *before any library is involved*.
Reporting the raw-coordinate figure here would have charged that to CGAL.

| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation | ms near / far |
|---|---|---|---|---|---|---|---|
| `overlap_half` | f64 input | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 24/24 v | 0.365 / 0.363 |
| `overlap_half` | f64 input | intersection | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 16/16 v | 0.404 / 0.360 |
| `overlap_half` | f32-rounded input | union | yes | 1.5 / 1.5 | 0 (0 rel) | **0 m** over 24/24 v | 0.463 / 0.429 |
| `overlap_half` | f32-rounded input | intersection | yes | 0.5 / 0.5 | 0 (0 rel) | **0 m** over 16/16 v | 0.359 / 0.345 |
| `coplanar_faces` | f64 input | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 0.098 / 0.092 |
| `coplanar_faces` | f64 input | intersection | yes (empty, as expected) | 0 / 0 | 0 (nan rel) | **- m** over 0/0 v | 0.088 / 0.082 |
| `coplanar_faces` | f32-rounded input | union | yes | 2 / 2 | 0 (0 rel) | **0 m** over 18/18 v | 0.090 / 0.088 |
| `coplanar_faces` | f32-rounded input | intersection | yes (empty, as expected) | 0 / 0 | 0 (nan rel) | **- m** over 0/0 v | 0.081 / 0.078 |
| `wall_with_openings` | f64 input | union | yes | 12.6 / 12.5999999999 | -1.397e-10 (-1.10873e-11 rel) | **1.28585e-10 m** over 320/320 v | 7.865 / 6.727 |
| `wall_with_openings` | f64 input | intersection | yes | 5.4 / 5.39999999979 | -2.09545e-10 (-3.88047e-11 rel) | **1.28585e-10 m** over 216/216 v | 7.461 / 6.263 |
| `wall_with_openings` | f32-rounded input | union | yes | 12.6000000179 / 12.7499997485 | 0.15 (0.0119047 rel) | **0.034821 m** over 320/320 v | 6.025 / 4.326 |
| `wall_with_openings` | f32-rounded input | intersection | yes | 5.39999982566 / 5.6249995809 | 0.225 (0.0416666 rel) | **0.034821 m** over 216/216 v | 5.852 / 4.232 |

**Worst vertex deviation over the whole set: 0.034821 m.** R-17's pass line is
1e-6 m and its fail line is 1e-4 m.

## Probe — origin-then-move against move-then-boolean

The local-frame mitigation ADR-0006 proposes, measured on this candidate. The
binding exposes no `Aff_transformation_3` on `Polyhedron_3`, so the 500 km move
is applied by the driver, in `double`, to the exported vertices — the same
arithmetic a tile frame would perform on the way out to a global CRS. Two
distances per row, both against the same pair of results:

* *far, back-translated vs. origin* — the main table's number, repeated here so
  the two columns are read together;
* *origin, moved out vs. far* — the mirror comparison, moving the origin result
  into the far frame instead of bringing the far result home. The two must agree
  to within the arithmetic of one f64 addition and subtraction at 5e5 m
  (an ULP of ~5.8e-11 m); a large disagreement would mean the back-translation
  itself is doing the work, which would invalidate the main table.

| Case | Setting | Op | far → origin | origin → far | V at the origin |
|---|---|---|---|---|---|
| `overlap_half` | f64 input | union | 0 | 0 | 1.5 |
| `overlap_half` | f64 input | intersection | 0 | 0 | 0.5 |
| `overlap_half` | f32-rounded input | union | 0 | 0 | 1.5 |
| `overlap_half` | f32-rounded input | intersection | 0 | 0 | 0.5 |
| `coplanar_faces` | f64 input | union | 0 | 0 | 2 |
| `coplanar_faces` | f64 input | intersection | - | - | - |
| `coplanar_faces` | f32-rounded input | union | 0 | 0 | 2 |
| `coplanar_faces` | f32-rounded input | intersection | - | - | - |
| `wall_with_openings` | f64 input | union | 1.28585e-10 | 1.16415e-10 | 12.6 |
| `wall_with_openings` | f64 input | intersection | 1.28585e-10 | 1.16415e-10 | 5.4 |
| `wall_with_openings` | f32-rounded input | union | 0.034821 | 0.034821 | 12.6000000179 |
| `wall_with_openings` | f32-rounded input | intersection | 0.034821 | 0.034821 | 5.39999982566 |

## Probe — how much of a far-field volume error is the measurement's own

All five columns describe the **same solid**, on the f64 setting. *Near* is
`reference.signed_volume` at the origin. *Near, coords shifted* adds the offset
to every vertex of the near result and re-integrates: no boolean, no library, so
the difference from the first column is pure floating-point cancellation in the
divergence-theorem sum. *Far, raw* is the same function on the far result's own
coordinates; *Far, back-translated* is the number the main table reports.

*Far, `PMP::volume()`* is CGAL's own integrator on the far result. It is reported
as data, not as a reference value: unlike Manifold's `Volume()`, which subtracts a
common origin and applies Kahan compensation
([`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294)),
CGAL's is an uncompensated sum of tetrahedron volumes about the origin and
therefore carries the same cancellation rather than avoiding it.

| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `PMP::volume()` |
|---|---|---|---|---|---|---|
| `overlap_half` | union | 1.5 | 1.5 | 1.5 | 1.5 | 1.49999999992 |
| `overlap_half` | intersection | 0.5 | 0.5 | 0.5 | 0.5 | 0.500000000007 |
| `coplanar_faces` | union | 2 | 2 | 2 | 2 | 1.99999999999 |
| `wall_with_openings` | union | 12.6 | 12.5997471293 | 12.5995943646 | 12.5999999999 | 12.6002807614 |
| `wall_with_openings` | intersection | 5.4 | 5.40016343781 | 5.40009218897 | 5.39999999979 | 5.39990234401 |
