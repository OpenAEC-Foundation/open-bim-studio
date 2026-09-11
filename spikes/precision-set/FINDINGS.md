# FINDINGS — R-17, precision 500 km from the origin, across four candidates

## The question, restated

Does a candidate kernel give the same answer for the same geometry placed 500 km from the origin
as it does at the origin? 500 km is a plausible distance from a national projection's false origin
to a project site, so this is not a synthetic extreme.

The pass/fail criteria were written before any driver ran and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-17:

> - **Spike:** `spikes/precision-set/` — identical geometry at the origin and at 500 km, through
>   each candidate's boolean and tessellation, then re-centred and compared.
> - **Pass:** maximum deviation below 1e-6 m in f64 paths.
> - **Fail:** deviation above 1e-4 m — which for a float32 path is the expected outcome and the
>   evidence ADR-0006 needs.

This file assembles the four per-candidate raw result files and applies that criterion literally.
It adds no measurement of its own: every number is copied from a named row of a named file, all
four regenerated in **one session on one machine on 2026-09-11**, in the same session as the
boolean-torture drivers.

## Hardware, OS and versions

*Measured*, recorded by each driver in its own environment table. Identical to
[`../boolean-torture/FINDINGS.md`](../boolean-torture/FINDINGS.md) §Hardware — same machine, same
session, same wheels: Intel Core i9-14900HX (32 logical processors), 32 GB RAM, Windows 11 Pro
`10.0.26200`; Python 3.12.10; `cadquery-ocp` 8.0.1.0.0 (OCCT 8.0.1); Blender 5.0.0 build
`a37564c4df7a`; `manifold3d` 3.5.3; `cgal` 6.0.1.post202410241521 (Epick).

Raw stdout of the session: [`results/run-2026-09-11.log`](results/run-2026-09-11.log).

## The model

[`../../reference/precision_set.py`](../../reference/precision_set.py) at commit
`cab6d247bd4ebdfe91c1ff86cd37b7157316745c`: **three** cases — `overlap_half`, `coplanar_faces`
and `wall_with_openings` — reused verbatim from
[`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py) (commit
`52d633dcd342faca70daf8c8f28ce64c5dd7fc56`), each carrying
`OFFSET = (500000.0, 500000.0, 0.0)`.

## Method

Every driver builds each case twice — once at the origin, once with the offset applied to the
**input coordinates**, which is what a project modelling in a national projection actually does —
runs the boolean at both locations, translates the far result back by −offset, and reports the
worst nearest-neighbour vertex distance and the volume difference. Matching is nearest-neighbour
rather than by index, because a kernel may emit vertices in any order, and it is taken as the
worse of both matching directions. Operands are rebuilt for every repeat at both locations.

Each driver additionally measures the **local-frame mitigation ADR-0006 proposes** — the same
offset carried by an object transform (Blender), by `Manifold.translate()` (Manifold), or applied
by the driver in `double` to the exported vertices (CGAL) — so the mitigation is measured on the
candidate rather than assumed.

### Two caveats that decide how the table may be read

1. **The volume columns are computed by two different integrators.** The Blender, Manifold and
   CGAL drivers use `reference.signed_volume` over exported triangles; the OCCT driver never calls
   it at all and reports OCCT's own `BRepGProp.VolumeProperties_s`
   (`../boolean-torture/occt_common.py`, lines 70-72, imported by `occt_driver.py`). The columns
   are comparable in **what they measure** — the far solid's volume, near against far — and not in
   **how they are computed**. This is stated as a requirement on this file by
   [`manifold.md`](../../docs/research/kernels/manifold.md) §A warning about measuring volume at
   500 km.
2. **`reference.signed_volume` itself loses volume at 500 km, before any library is involved.** It
   sums `x0*(y1*z2 − z1*y2)` over raw coordinates; at 5e5 m each term is about 1e17 against a sum
   of about 12.6. Measured by shifting the *origin* result's own vertices and re-integrating: the
   wall union loses **7.91e-05 m³** on Manifold's 200v/396f triangulation (face count from
   [`../boolean-torture/results/manifold.md`](../boolean-torture/results/manifold.md) Probe E,
   volume loss from [`results/manifold.md`](results/manifold.md), last probe) and **1.55e-04 m³**
   on CGAL's 320v/636f triangulation of the same solid (face count from
   [`../boolean-torture/results/cgal.md`](../boolean-torture/results/cgal.md) Probe E, volume loss
   from [`results/cgal.md`](results/cgal.md), last probe) —
   a different sum, not a different conclusion, and a quantity that moves between runs because
   CGAL's vertex emission order does. Every far volume in the tables below is therefore integrated
   **after** back-translation. Neither library's own integrator is a way out for free: Manifold's
   `Volume()` differences against a vertex and applies Kahan compensation and returns
   12.5999999999; CGAL's `PMP::volume()` is an uncompensated sum of tetrahedra about the world
   origin and returns **12.6002807617**, worse than the naive raw sum. OCCT's `BRepGProp` was not
   put through this probe and is counted on neither side.
3. **`wall_with_openings` is the case this file's whole R-17 finding rests on, and the four
   candidates were not handed the same input object for it.** `overlap_half` and `coplanar_faces`
   are unit cubes, identically constructed for every candidate, and return 0 m deviation on every
   candidate and setting, f32 included (§What this does not settle) — they discriminate nothing.
   `wall_with_openings` is the only case that separates the f64 and f32 populations below, and its
   operand B is **four different constructions**, exactly as
   [`../boolean-torture/FINDINGS.md`](../boolean-torture/FINDINGS.md) caveat 1 establishes: OCCT
   builds it as a compound of twelve solids
   ([`../../docs/research/kernels/occt.md`](../../docs/research/kernels/occt.md) §Measurements,
   construction bullet), Blender as one mesh object with twelve disconnected shells
   ([`../boolean-torture/results/blender.md`](../boolean-torture/results/blender.md) §Construction
   of the operands), Manifold as one `Manifold` with `decompose() == 12`
   ([`../boolean-torture/results/manifold.md`](../boolean-torture/results/manifold.md) Probe A),
   and CGAL as one `Polyhedron_3` with `PMP::connected_components` reporting 12
   ([`../boolean-torture/results/cgal.md`](../boolean-torture/results/cgal.md) Probe A). The four
   `wall_with_openings` rows below are therefore the same benchmark *case*, not the same input
   *object* — the R-16 finding's caveat applies here with the same force, because it is the same
   operand construction.

## Results

*Measured.* One row per case × operation; *ΔV* is the far volume minus the near volume, absolute
and relative to the near volume; *deviation* is the worst nearest-neighbour vertex distance after
translating the far result back. Every row is the correspondingly named row of the named file's
§Boolean results near vs far table.

### OCCT 8.0.1, f64 B-rep — [`results/occt.md`](results/occt.md)

Volumes here are OCCT's own `BRepGProp` figures (caveat 1).

| Case | Setting | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation |
|---|---|---|---|---|---|---|
| `overlap_half` | default | fuse | yes | 1.5 / 1.5 | 0, 0 | **2.48e-16 m** |
| `overlap_half` | default | common | yes | 0.5 / 0.5 | 0, 0 | **2.48e-16 m** |
| `overlap_half` | fuzzy=1e-5 | fuse | yes | 1.5 / 1.5 | 0, 0 | **2.48e-16 m** |
| `overlap_half` | fuzzy=1e-5 | common | yes | 0.5 / 0.5 | 0, 0 | **2.48e-16 m** |
| `coplanar_faces` | default | fuse | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | default | common | yes | 0 / 0 | 0, n/a | **0 m** (0 verts) |
| `coplanar_faces` | fuzzy=1e-5 | fuse | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | fuzzy=1e-5 | common | yes | 0 / 0 | 0, n/a | **0 m** (0 verts) |
| `wall_with_openings` | default | fuse | yes | 12.6 / 12.5999999999 | 1.24e-10, 9.88e-12 | **2.65e-10 m** |
| `wall_with_openings` | default | common | yes | 5.4 / 5.39999999925 | 7.52e-10, 1.39e-10 | **2.65e-10 m** |
| `wall_with_openings` | fuzzy=1e-5 | fuse | yes | 12.6 / 12.5999999999 | 1.09e-10, 8.66e-12 | **3.61e-10 m** |
| `wall_with_openings` | fuzzy=1e-5 | common | yes | 5.4 / 5.39999999925 | 7.52e-10, 1.39e-10 | **3.61e-10 m** |

The f64 ULP of 5e5 m is about 1.1e-10 m, so 3.61e-10 m is roughly three ULP of the coordinate
itself: at this distance OCCT's boolean is translation-invariant to within the representation.

### Blender 5.0.0, float32 mesh storage — [`results/blender.md`](results/blender.md)

| Case | Solver | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation |
|---|---|---|---|---|---|---|
| `overlap_half` | Exact | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** |
| `overlap_half` | Exact | common | yes | 0.5 / 0.5 | 0, 0 | **0 m** |
| `overlap_half` | Fast (float) | union | **no** | 1 / 1.91666666667 | 0.916667, 0.916667 | **0.5 m** |
| `overlap_half` | Fast (float) | common | **no** | 1 / 0.0833333333333 | −0.916667, −0.916667 | **0.5 m** |
| `overlap_half` | Manifold | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** |
| `overlap_half` | Manifold | common | yes | 0.5 / 0.5 | 0, 0 | **0 m** |
| `coplanar_faces` | Exact | union | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | Exact | common | yes (empty, as expected) | 0 / 0 | 0, n/a | n/a (0 verts) |
| `coplanar_faces` | Fast (float) | union | **no** | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | Fast (float) | common | yes (empty, as expected) | 0 / 0 | 0, n/a | **0 m** |
| `coplanar_faces` | Manifold | union | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | Manifold | common | yes (empty, as expected) | 0 / 0 | 0, n/a | n/a (0 verts) |
| `wall_with_openings` | Exact | union | yes | 12.6000000179 / 12.7499997485 | 0.15, 0.0119047 | **0.0348212 m** |
| `wall_with_openings` | Exact | common | yes | 5.39999982566 / 5.6249995809 | 0.225, 0.0416666 | **0.0348212 m** |
| `wall_with_openings` | Fast (float) | union | near yes / far **no** | 12.5999999541 / 10.2739276984 | −2.32607, −0.184609 | **0.13758 m** |
| `wall_with_openings` | Fast (float) | common | near yes / far **no** | 5.39999939549 / 7.56262934166 | 2.16263, 0.400487 | **0.0947531 m** |
| `wall_with_openings` | Manifold | union | yes | 12.6000000179 / 12.7499997485 | 0.15, 0.0119047 | **0.0348212 m** |
| `wall_with_openings` | Manifold | common | yes | 5.39999982566 / 5.6249995809 | 0.225, 0.0416666 | **0.0435011 m** |

**Blender has no f64 path to measure.** `Mesh` stores vertex positions in float32, and the
storage round trip alone — write a coordinate, read it back, no algorithm involved — costs
**0.00625 m** at 500000.1 and **0.01375 m** over the wall's operands, against a float32 ULP of
**0.03125 m** at that distance ([`results/blender.md`](results/blender.md) §Storage). The question
is decided before any boolean runs, and the 0.0348 m figure for Exact and Manifold alike is that
storage cost, not a property of either solver.

### Manifold 3.5.3 — [`results/manifold.md`](results/manifold.md)

| Case | Setting | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation | tol near / far |
|---|---|---|---|---|---|---|---|
| `overlap_half` | f64 (`Mesh64`) | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** | 1.5e-12 / 5e-07 |
| `overlap_half` | f64 | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** | 1.5e-12 / 5e-07 |
| `overlap_half` | f32 (`Mesh`) | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** | 1.788e-07 / 0.0596 |
| `overlap_half` | f32 | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** | 1.788e-07 / 0.0596 |
| `coplanar_faces` | f64 | union | yes | 2 / 2 | 0, 0 | **0 m** | 2e-12 / 5e-07 |
| `coplanar_faces` | f64 | intersection | yes | 0 / 0 | 0, n/a | **0 m** | 2e-12 / 5e-07 |
| `coplanar_faces` | f32 | union | yes | 2 / 2 | 0, 0 | **0 m** | 2.384e-07 / 0.0596 |
| `coplanar_faces` | f32 | intersection | yes | 0 / 0 | 0, n/a | **0 m** | 2.384e-07 / 0.0596 |
| `wall_with_openings` | f64 | union | yes | 12.6 / 12.5999999999 | −1.39659e-10, −1.1084e-11 | **3.29273e-11 m** | 1e-11 / 5e-07 |
| `wall_with_openings` | f64 | intersection | yes | 5.4 / 5.39999999979 | −2.0955e-10, −3.88055e-11 | **2.60313e-11 m** | 1e-11 / 5e-07 |
| `wall_with_openings` | f32 | union | near yes / far **no** — 1 zero-area face | 12.6000000179 / 12.7499997485 | 0.15, 0.0119047 | **0.0185826 m** | 1.192e-06 / 0.05961 |
| `wall_with_openings` | f32 | intersection | yes | 5.39999982566 / 5.6249995809 | 0.225, 0.0416666 | **0.0185826 m** | 1.192e-06 / 0.05961 |

The `tol` column is the second finding in this file. Manifold derives a solid's tolerance as
`kPrecision * Box::Scale()` with `Box::Scale()` the **largest absolute coordinate**, not the
diagonal — so the tolerance is a function of distance from the origin **even on the f64 path**:
1e-11 at the origin becomes 5e-07 at 500 km, and on f32 it becomes **0.0596 m**. The f64 path
still passes, but its safety margin shrinks by five orders of magnitude purely from position.

### CGAL 6.0.1, Epick — [`results/cgal.md`](results/cgal.md)

Both settings run the **same exact predicates**; what the f32-rounded row loses is lost to the
storage, not to the arithmetic that decides topology. That is the ADR-0006 question asked of one
candidate directly, with everything else held constant.

| Case | Setting | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation |
|---|---|---|---|---|---|---|
| `overlap_half` | f64 input | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** |
| `overlap_half` | f64 input | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** |
| `overlap_half` | f32-rounded | union | yes | 1.5 / 1.5 | 0, 0 | **0 m** |
| `overlap_half` | f32-rounded | intersection | yes | 0.5 / 0.5 | 0, 0 | **0 m** |
| `coplanar_faces` | f64 input | union | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | f64 input | intersection | yes (empty, as expected) | 0 / 0 | 0, n/a | n/a (0 verts) |
| `coplanar_faces` | f32-rounded | union | yes | 2 / 2 | 0, 0 | **0 m** |
| `coplanar_faces` | f32-rounded | intersection | yes (empty, as expected) | 0 / 0 | 0, n/a | n/a (0 verts) |
| `wall_with_openings` | f64 input | union | yes | 12.6 / 12.5999999999 | −1.397e-10, −1.10873e-11 | **1.28585e-10 m** |
| `wall_with_openings` | f64 input | intersection | yes | 5.4 / 5.39999999979 | −2.09545e-10, −3.88047e-11 | **1.28585e-10 m** |
| `wall_with_openings` | f32-rounded | union | yes | 12.6000000179 / 12.7499997485 | 0.15, 0.0119047 | **0.034821 m** |
| `wall_with_openings` | f32-rounded | intersection | yes | 5.39999982566 / 5.6249995809 | 0.225, 0.0416666 | **0.034821 m** |

A probe checks that the back-translation is not doing the work: comparing the same pair of results
in the other direction — moving the origin result *out* to the far frame instead of bringing the
far result home — gives 1.16415e-10 m against the table's 1.28585e-10 m on f64, and 0.034821 m
against 0.034821 m on f32-rounded. Agreement at the level of one f64 addition at 5e5 m, as it
should be.

## Summary — worst deviation per candidate × precision path

*Measured*, from each file's own "worst vertex deviation over the whole set" line, except OCCT's,
which is the maximum of its table above.

| Candidate | Path / setting | Float width of vertex storage | Worst deviation over the set | Worst relative ΔV |
|---|---|---|---|---|
| OCCT 8.0.1 | default, B-rep | f64 | **2.65e-10 m** | 1.39e-10 |
| OCCT 8.0.1 | fuzzy=1e-5, B-rep | f64 | **3.61e-10 m** | 1.39e-10 |
| CGAL 6.0.1 | Epick, f64 input | f64 | **1.28585e-10 m** | 3.88e-11 |
| Manifold 3.5.3 | `Mesh64` | f64 | **3.29273e-11 m** | 3.88e-11 |
| Manifold 3.5.3 | `Mesh` | f32 on ingest, f64 internally | **0.0185826 m** | 0.0417 |
| CGAL 6.0.1 | Epick, f32-rounded input | f32 on ingest, f64 storage | **0.034821 m** | 0.0417 |
| Blender 5.0 | Exact | f32 throughout | **0.0348212 m** | 0.0417 |
| Blender 5.0 | Manifold | f32 throughout | **0.0435011 m** | 0.0417 |
| Blender 5.0 | Fast (float) | f32 throughout | **0.5 m** | 0.917 |

Read as two populations, which is what this set was built to produce:

- **Every f64 path is between 3.3e-11 m and 3.6e-10 m** — one to three ULP of a 5e5 m coordinate
  (1.1e-10 m). Three independent kernels, three representations (B-rep, halfedge mesh, indexed
  triangle mesh), the same answer.
- **Every f32 path is between 0.0186 m and 0.5 m** — at or above the float32 ULP of 0.03125 m at
  that distance. Two of the three f32 figures (Blender Exact and CGAL f32-rounded) agree to four
  significant figures at **0.0348 m** despite sharing no code, because both are measuring the same
  thing: the rounding of the input coordinates.

**The cleanest single comparison in the set is Manifold's**, because one library, one algorithm and
one machine separate the two rows: `Mesh64` gives 3.3e-11 m and `Mesh` gives 0.0186 m on identical
geometry. **CGAL's is the cleanest statement about predicates**: exact predicates in force on both
its settings, and the f32-rounded setting still deviates by 0.0348 m. Exact predicates keep the
combinatorics right on rounded coordinates; they cannot keep the geometry right.

## Verdict against R-17

R-17 says, verbatim: **"Pass: maximum deviation below 1e-6 m in f64 paths."** and **"Fail:
deviation above 1e-4 m — which for a float32 path is the expected outcome and the evidence
ADR-0006 needs."** Applied literally:

| Candidate × setting | Verdict | Margin against the line |
|---|---|---|
| OCCT, default (f64) | **PASS** | 2.65e-10 m against a 1e-6 m pass line — inside it by 3 770 times |
| OCCT, fuzzy=1e-5 (f64) | **PASS** | 3.61e-10 m — inside it by 2 770 times; fuzzy changed the worst deviation from 2.65e-10 to 3.61e-10 m and nothing else |
| CGAL, Epick f64 input | **PASS** | 1.28585e-10 m — inside by 7 800 times |
| Manifold, `Mesh64` (f64) | **PASS** | 3.29273e-11 m — inside by 30 000 times |
| Manifold, `Mesh` (f32) | **FAIL** | 0.0185826 m against a 1e-4 m fail line — outside it by 186 times |
| CGAL, Epick f32-rounded input | **FAIL** | 0.034821 m — outside by 348 times |
| Blender, Exact (f32) | **FAIL** | 0.0348212 m — outside by 348 times |
| Blender, Manifold (f32) | **FAIL** | 0.0435011 m — outside by 435 times |
| Blender, Fast (f32) | **FAIL** | 0.5 m — outside by 5 000 times; the far result is a *different wrong answer* from the near one, not a rounded version of it |

**Every f64 path passes and every float32 path fails, with three orders of magnitude of clear air
between the two populations and no candidate anywhere in between.** R-17's fail clause anticipated
this in writing — "which for a float32 path is the expected outcome and the evidence ADR-0006
needs" — and the measurement supplies it. The evidence is stronger than a single failing candidate
would have been, because the two populations are separated *within* one library (Manifold `Mesh64`
against `Mesh`) and *within* one set of exact predicates (CGAL f64 against f32-rounded), not only
across libraries with different algorithms.

### The local-frame mitigation, measured

ADR-0006 proposes f64 local coordinates in tile frames — the far placement carried outside the
geometry rather than inside it. Each driver measured that arrangement rather than assuming it:

| Candidate | How the offset was carried | Result |
|---|---|---|
| Blender | the object's `location`, vertex data at the origin | **0 m** deviation against the origin run on every case and every solver, Exact, Fast and Manifold alike, **with one exception**: `overlap_half`, Fast (float), **common** still deviates **0.5 m** ([`results/blender.md`](results/blender.md) §The local-frame mitigation). That row is not a counter-example to the mitigation — the Fast solver's `overlap_half` result is already invalid and wrong in both frames before the mitigation is applied (main table above: near V=1 against an expected 1.5, far equally wrong), so the local frame changes an already-wrong answer's error term, not its validity; R-17's verdict for Blender Fast was already **FAIL** on this case regardless. Every case the mitigation actually rescues, including the twelve-opening wall, where carrying the offset in the vertices had cost 0.0348 m, reaches 0 m ([`results/blender.md`](results/blender.md), last probe) |
| Manifold | `Manifold.translate()` before the boolean, result translated back | **0 m** on `overlap_half` and `coplanar_faces` at both precisions; 3.29e-11 m / 2.60e-11 m on the wall at f64; **0 m** on the wall at f32. But the tolerance is re-derived from the moved bounding box: 1e-11 → 5e-07 at f64, and 1.192e-06 unchanged at f32 |
| CGAL | the driver applies it in `double` to the exported vertices, as a tile frame would on the way out | the mirror comparison agrees with the main table to 1.2e-11 m, confirming the back-translation is not itself doing the work |

*Inferred:* the mitigation works on every candidate measured, and on Blender it is the difference
between a 0.0348 m error and none. What it does not do is remove the tolerance coupling Manifold's
column shows — a local frame fixes the *coordinates*, and a tolerance derived from a global
bounding box still tracks the global position.

## Run-to-run changes against the committed files

*Measured.* All four drivers were re-run for this assembly and every regenerated file was diffed
against the committed, per-candidate-reviewed version — the same re-run
[`../boolean-torture/FINDINGS.md`](../boolean-torture/FINDINGS.md) §Run-to-run reproduction
describes for the boolean-torture files. **No verdict in this file moves**: every cell that changed
is either a non-reference probe column the R-17 verdicts do not read, or a case the mitigation
table already marks as invalid regardless of the number. In full:

| File | Cell | Committed (2026-09-10 basis) | Regenerated (2026-09-11) | Explanation, from the file itself |
|---|---|---|---|---|
| `results/cgal.md` | Last probe, `wall_with_openings` union, "Near, coords shifted" | 12.5997471293 | 12.5998451544 | Pure floating-point cancellation in `reference.signed_volume`'s raw sum at 5e5 m (caveat 2 above); no boolean and no library are involved in this column at all |
| `results/cgal.md` | Last probe, `wall_with_openings` union, "Far, raw" | 12.5995943646 | 12.5999895013 | Same cause: this column is CGAL's vertex emission order feeding the same cancellation-prone sum, and the emission order is the driver's own documented non-determinism ([`../boolean-torture/results/cgal.md`](../boolean-torture/results/cgal.md) Probe E) |
| `results/cgal.md` | Last probe, `wall_with_openings` intersection, "Near, coords shifted" | 5.40016343781 | 5.4002605346 | Same cancellation artefact on the intersection solid |
| `results/cgal.md` | Last probe, `wall_with_openings` intersection, "Far, raw" | 5.40009218897 | 5.40003036136 | Same cause, emission-order dependent |
| `results/cgal.md` | Last probe, `wall_with_openings` union, "Far, `PMP::volume()`" | 12.6002807614 | 12.6002807617 | `PMP::volume()` is an uncompensated tetrahedron sum about the world origin (caveat 2) — the same emission-order noise, one level further from the raw coordinates |
| `results/cgal.md` | Last probe, `coplanar_faces` union, "Far, `PMP::volume()`" | 1.99999999999 | 2 | Same integrator, same noise floor, on a solid whose true volume is exactly 2 |
| `results/blender.md` | Local-frame mitigation table, `overlap_half` / Fast (float) / **union** | 0.5 m | 0 m | The Fast solver's documented run-to-run non-determinism (P-16; [`../boolean-torture/FINDINGS.md`](../boolean-torture/FINDINGS.md) §Failures, `overlap_half` ∪ row) — the result is invalid in both frames either way, so this cell moving does not change which cases the mitigation table's readers may trust |

None of these seven cells is a number the R-17 verdicts above are computed from: the last-probe
table exists to characterise `reference.signed_volume`'s own error, not to report a candidate's
deviation, and the local-frame mitigation table's `overlap_half`/Fast/union row was already invalid
before this run and stays invalid after it. **No pass/fail verdict and no deviation figure in the
main results tables or the summary above moved.**

## What this does not settle

- **Tessellation was not measured at 500 km.** R-17's spike sentence names "each candidate's
  boolean **and tessellation**". These drivers run booleans only; no driver calls
  `BRepMesh_IncrementalMesh` or any equivalent at the far location. Curved geometry, where
  tessellation would actually be tested, is absent from the set altogether. **This is the specific
  missing evidence that keeps R-17 at `in progress` rather than `resolved`.**
- **Three cases, all planar, all boxes.** `overlap_half` and `coplanar_faces` are unit cubes and
  return 0 m deviation on every candidate and every setting, f32 included — they discriminate
  nothing. The whole finding rests on `wall_with_openings`, which is one case.
- **One distance, one direction.** 500 km east and north, z = 0. Nothing measured at 5 km, 50 km
  or 5000 km, so the shape of the degradation curve is unknown; only its value at one point is.
- **The volume columns are not one measurement** (caveat 1), and `reference.signed_volume` is
  itself unusable at these coordinates (caveat 2). Volume is the weaker of the two columns here;
  the vertex deviation is the number the verdict rests on.
- **f64 sufficiency is shown; f64 *necessity* is shown only for these candidates' f32 paths.** That
  a float32 *mesh* fails does not by itself prove a hypothetical fixed-point or offset-double
  scheme would. ADR-0006's premise is supported, not proven exhaustively.
- **Our own kernel has not been measured.** R-17 exists to be run against the kernel we build, and
  against the tile frame ADR-0006 specifies. This file is the baseline.
