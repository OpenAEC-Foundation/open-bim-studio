# Precision set — OCCT raw results

Produced by [`../occt_driver.py`](../occt_driver.py). Raw data for `../FINDINGS.md` and for
[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-11
**Offset:** `(500000.0, 500000.0, 0.0)` (500 km east, 500 km north — a plausible distance from a national
projection's false origin to a project site).

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
| repeats per timing | 5 |
| threading | `SetRunParallel(false)` |

## Construction at both locations

| Case | near A/B valid? | far A/B valid? | ΔV(A)+V(B) far−near | max tol far |
|---|---|---|---|---|
| `overlap_half` | yes / yes | yes / yes | 2.22e-16 | 1e-07 |
| `coplanar_faces` | yes / yes | yes / yes | 2.22e-16 | 1e-07 |
| `wall_with_openings` | yes / yes | yes / yes | 8.39e-10 | 1e-07 |

## Boolean results near vs far

*Vertex deviation* is the worst nearest-neighbour distance after translating the far result
back by −offset, followed by the vertex counts of the near and far results. A kernel that is
translation-invariant at this distance reports a deviation at the level of f64 rounding of
the coordinate itself (5e5 m × 2⁻⁵² ≈ 1.1e-10 m).

| Case | Setting | Op | Valid near+far? | V near / far | ΔV | Vertex deviation |
|---|---|---|---|---|---|---|
| `overlap_half` | default | fuse | yes | 1.5 / 1.5 | 0 (0 rel) | 2.48e-16 m over 24/24 v |
| `overlap_half` | default | common | yes | 0.5 / 0.5 | 0 (0 rel) | 2.48e-16 m over 16/16 v |
| `overlap_half` | fuzzy=1e-5 | fuse | yes | 1.5 / 1.5 | 0 (0 rel) | 2.48e-16 m over 24/24 v |
| `overlap_half` | fuzzy=1e-5 | common | yes | 0.5 / 0.5 | 0 (0 rel) | 2.48e-16 m over 16/16 v |
| `coplanar_faces` | default | fuse | yes | 2 / 2 | 0 (0 rel) | 0 m over 18/18 v |
| `coplanar_faces` | default | common | yes | 0 / 0 | 0 (nan rel) | 0 m over 0/0 v |
| `coplanar_faces` | fuzzy=1e-5 | fuse | yes | 2 / 2 | 0 (0 rel) | 0 m over 18/18 v |
| `coplanar_faces` | fuzzy=1e-5 | common | yes | 0 / 0 | 0 (nan rel) | 0 m over 0/0 v |
| `wall_with_openings` | default | fuse | yes | 12.6 / 12.5999999999 | 1.24e-10 (9.88e-12 rel) | 2.65e-10 m over 320/320 v |
| `wall_with_openings` | default | common | yes | 5.4 / 5.39999999925 | 7.52e-10 (1.39e-10 rel) | 2.65e-10 m over 216/216 v |
| `wall_with_openings` | fuzzy=1e-5 | fuse | yes | 12.6 / 12.5999999999 | 1.09e-10 (8.66e-12 rel) | 3.61e-10 m over 320/320 v |
| `wall_with_openings` | fuzzy=1e-5 | common | yes | 5.4 / 5.39999999925 | 7.52e-10 (1.39e-10 rel) | 3.61e-10 m over 216/216 v |
