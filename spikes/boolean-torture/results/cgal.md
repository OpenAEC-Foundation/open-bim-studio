# Boolean torture set — CGAL raw results

Produced by [`../cgal_driver.py`](../cgal_driver.py). This file is raw data for
`../FINDINGS.md` (assembled once every candidate has run) and for
[`../../../docs/research/kernels/cgal.md`](../../../docs/research/kernels/cgal.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10

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
| kernel bound | `Exact_predicates_inexact_constructions_kernel` (Epick) — see Probe G |
| repeats per timing | 5 (median reported) |

**What is measured here is the Epick corefinement path and nothing else.** The
`cgal` wheel exposes no `Nef_polyhedron_3` module and no
`Exact_predicates_exact_constructions_kernel` mesh type, so CGAL's
exact-*construction* path — the one `problems.md` P-03 is about — is **not**
measured in this file. Every claim about it in the note is labelled *claimed*.

## Settings

CGAL exposes no tolerance parameter, so there is nothing here corresponding to
the tolerance sweep in [`results/manifold.md`](manifold.md). The axis that is
available, and the one ADR-0006 asks about, is the precision of the coordinates
handed in:

| Setting | What it does |
|---|---|
| `Epick, f64 input` | the reference set's coordinates verbatim into `Point_3` |
| `Epick, f32-rounded input` | every coordinate rounded to the nearest float32 (`struct.pack('<f', …)`) and back before the `Point_3` is built; storage is still `double` |

The second setting asks a question no other candidate can answer as cleanly: do
exact predicates rescue coordinates that were rounded to float32 on the way in?
It changes no case — the same ten pairs, the same analytic expectations.

## Construction of the operands

`reference/boolean_torture_set.py` verbatim into a `PMP::Point_3_Vector` /
`PMP::Polygon_Vector` soup, then `polygon_soup_to_polygon_mesh` into a
`Polyhedron_3`. `orient_polygon_soup` is deliberately **not** called: whether the
reference set's operands are already consistently oriented is part of what is
being measured. *Volume* is `reference.signed_volume` over the exported
triangles; *PMP::volume* is CGAL's own integrator, `PMP::volume()`, which has
`is_closed` as a precondition and is therefore blank for an open surface.

The corefinement functions document four preconditions on each operand: it is a
triangulated surface mesh, it does not self-intersect, and it bounds a volume
(which implies closed and outward-oriented). The binding exposes
`is_closed`, `is_pure_triangle`, `does_self_intersect` and `is_outward_oriented`
— but **not** `does_bound_a_volume`, so the last precondition cannot be checked
through this binding at all. That absence is recorded, not worked around.

| Case | Operand | Setting | Closed | Pure triangle | Self-intersects | Outward | Volume | PMP::volume |
|---|---|---|---|---|---|---|---|---|
| `disjoint` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `disjoint` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `disjoint` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `disjoint` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `overlap_half` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `overlap_half` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `overlap_half` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `overlap_half` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `coplanar_faces` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `coplanar_faces` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `coplanar_faces` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `coplanar_faces` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `shared_edge` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `shared_edge` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `shared_edge` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `shared_edge` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `touching_vertex` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `touching_vertex` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `touching_vertex` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `touching_vertex` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `identical` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `identical` | B | Epick, f64 input | True | True | False | True | 1 | 1 |
| `identical` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `identical` | B | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `contained` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `contained` | B | Epick, f64 input | True | True | False | True | 0.125 | 0.125 |
| `contained` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `contained` | B | Epick, f32-rounded input | True | True | False | True | 0.125 | 0.125 |
| `sliver` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `sliver` | B | Epick, f64 input | True | True | False | True | 9.99999999474e-08 | 9.99999999474e-08 |
| `sliver` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `sliver` | B | Epick, f32-rounded input | True | True | False | True | 1.19209289551e-07 | 1.19209289569e-07 |
| `near_degenerate_triangle` | A | Epick, f64 input | True | True | False | True | 1 | 1 |
| `near_degenerate_triangle` | B | Epick, f64 input | False | True | True | n/a | 1 | - |
| `near_degenerate_triangle` | A | Epick, f32-rounded input | True | True | False | True | 1 | 1 |
| `near_degenerate_triangle` | B | Epick, f32-rounded input | False | True | True | n/a | 1 | - |
| `wall_with_openings` | A | Epick, f64 input | True | True | False | True | 9 | 9 |
| `wall_with_openings` | B | Epick, f64 input | True | True | False | True | 9 | 9 |
| `wall_with_openings` | A | Epick, f32-rounded input | True | True | False | True | 9.00000035763 | 9.00000035763 |
| `wall_with_openings` | B | Epick, f32-rounded input | True | True | False | True | 8.99999948591 | 8.99999948591 |

## Boolean results

One row per case × setting. *Valid?* is this driver's own check on the exported
result mesh — every directed edge used once with a matching opposite halfedge
(closed, manifold and consistently wound), no loose vertices, no triangle below
1e-14 m² — plus `Polyhedron_3::is_closed()` and the boolean's own `bool` return
value. *Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` computed from the
**measured** operand volumes. Times are milliseconds, median of the repeats,
union / intersection; both operands are rebuilt inside every repeat (PMP
corefinement modifies its operands in place — Probe F) but outside the timed
region, so what is timed is the boolean call.

| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |
|---|---|---|---|---|---|---|---|
| `disjoint` | Epick, f64 input | yes | 2 | 0 | 0 | 0.019 / 0.011 | - |
| `disjoint` | Epick, f32-rounded input | yes | 2 | 0 | 0 | 0.019 / 0.012 | - |
| `overlap_half` | Epick, f64 input | yes | 1.5 | 0.5 | 0 | 0.389 / 0.405 | - |
| `overlap_half` | Epick, f32-rounded input | yes | 1.5 | 0.5 | 0 | 0.374 / 0.376 | - |
| `coplanar_faces` | Epick, f64 input | yes | 2 | 0 | 0 | 0.105 / 0.092 | - |
| `coplanar_faces` | Epick, f32-rounded input | yes | 2 | 0 | 0 | 0.092 / 0.088 | - |
| `shared_edge` | Epick, f64 input | ∪: **no** — the boolean returned `False`; ∩ ok | 0 | 0 | 2 | 0.104 / 0.102 | Δ∪=-2 |
| `shared_edge` | Epick, f32-rounded input | ∪: **no** — the boolean returned `False`; ∩ ok | 0 | 0 | 2 | 0.100 / 0.098 | Δ∪=-2 |
| `touching_vertex` | Epick, f64 input | yes | 2 | 0 | 0 | 0.065 / 0.062 | - |
| `touching_vertex` | Epick, f32-rounded input | yes | 2 | 0 | 0 | 0.067 / 0.061 | - |
| `identical` | Epick, f64 input | yes | 1 | 1 | 0 | 0.273 / 0.272 | - |
| `identical` | Epick, f32-rounded input | yes | 1 | 1 | 0 | 0.284 / 0.273 | - |
| `contained` | Epick, f64 input | yes | 1 | 0.125 | 0 | 0.024 / 0.024 | - |
| `contained` | Epick, f32-rounded input | yes | 1 | 0.125 | 0 | 0.023 / 0.022 | - |
| `sliver` | Epick, f64 input | yes | 1 | 9.99999999612e-08 | 0 | 1.034 / 1.113 | - |
| `sliver` | Epick, f32-rounded input | yes | 1 | 1.19209289551e-07 | 0 | 0.997 / 1.009 | Δ∩=1.92e-08 |
| `near_degenerate_triangle` | Epick, f64 input | ∪: **no** — the boolean returned `False`; ∩: **no** — the boolean returned `False` | 0 | 0 | 2 | 0.285 / 0.306 | Δ∪=-1; Δ∩=-1; operand B is **not closed**; operand B **self-intersects** |
| `near_degenerate_triangle` | Epick, f32-rounded input | ∪: **no** — the boolean returned `False`; ∩: **no** — the boolean returned `False` | 0 | 0 | 2 | 0.303 / 0.307 | Δ∪=-1; Δ∩=-1; operand B is **not closed**; operand B **self-intersects** |
| `wall_with_openings` | Epick, f64 input | yes | 12.6 | 5.4 | 3.55e-15 | 8.206 / 7.838 | - |
| `wall_with_openings` | Epick, f32-rounded input | yes | 12.6000000179 | 5.39999982566 | 0 | 6.388 / 6.021 | Δ∪=1.79e-08; Δ∩=-1.74e-07 |

**Summary:** 16 of 20 case×setting combinations produced a result this
driver's check accepts for both the union and the intersection.

*Valid* and *correct* are different questions and are counted separately, on the
same definitions [`results/blender.md`](blender.md) and
[`results/manifold.md`](manifold.md) use. *Correct* is both volumes within
`1e-06 * max(1.0, abs(expected))` of the analytic expectation — relative above
1 m³, an absolute floor below it, so a case whose expected volume is 0 or 1e-07 m³
is not judged on a relative error it cannot meet. The Δ notes above use 1e-09 instead.

| Setting | Valid (closed manifold) | Numerically correct | Worst identity residual (refusals excluded) |
|---|---|---|---|
| Epick, f64 input | 8 / 10 | 8 / 10 | 3.55e-15 |
| Epick, f32-rounded input | 8 / 10 | 8 / 10 | 0 |

## Probe A — the twelve-shell operand

`wall_with_openings` B is **one mesh with twelve disconnected closed shells**, the
same construction [`results/blender.md`](blender.md) and
[`results/manifold.md`](manifold.md) used. *Components* is
`PMP::connected_components`. The analytic expectation for the difference is
V(A) − V(A∩B) = 9 − 5.4 = **3.6 m³**.

| Setting | Operation | Components in B | Returned | V(result) | Verts | Tris | Components in result | Valid? |
|---|---|---|---|---|---|---|---|---|
| Epick, f64 input | union | 12 | True | 12.6 | 320 | 636 | 1 | yes |
| Epick, f64 input | intersection | 12 | True | 5.4 | 216 | 384 | 12 | yes |
| Epick, f64 input | difference | 12 | True | 3.6 | 224 | 492 | 1 | yes |
| Epick, f32-rounded input | union | 12 | True | 12.6000000179 | 320 | 636 | 1 | yes |
| Epick, f32-rounded input | intersection | 12 | True | 5.39999982566 | 216 | 384 | 12 | yes |
| Epick, f32-rounded input | difference | 12 | True | 3.60000053197 | 224 | 492 | 1 | yes |

## Probe B — the 1e-7 m slab

`sliver` B is a 1 m × 1 m × 1e-7 m slab. CGAL has no tolerance to raise, so the
question [`results/manifold.md`](manifold.md) Probe B asks (at what tolerance does
the slab vanish?) has no CGAL form. What can be asked instead is whether a feature
seven orders of magnitude below the operand's size survives ingest and the boolean
at all. *Thickness as stored* is read back from the constructed `Polyhedron_3`.

| Setting | Operation | Thickness as stored | V(B) as stored | Returned | V(result) | Tris |
|---|---|---|---|---|---|---|
| Epick, f64 input | union | 9.99999999474e-08 | 9.99999999474e-08 | True | 1 | 52 |
| Epick, f64 input | intersection | 9.99999999474e-08 | 9.99999999474e-08 | True | 9.99999999612e-08 | 36 |
| Epick, f32-rounded input | union | 1.19209289551e-07 | 1.19209289551e-07 | True | 1 | 52 |
| Epick, f32-rounded input | intersection | 1.19209289551e-07 | 1.19209289551e-07 | True | 1.19209289551e-07 | 36 |

## Probe C — the T-junction operand

`near_degenerate_triangle` B has a vertex lying *on* an edge (the reference set
splits the cube's top face by inserting a vertex on the edge v5→v6), so three
halfedges have no twin. Manifold refuses it outright with `Error::NotManifold`
and an empty result; Blender's Manifold solver returns the unmodified first
operand. This probe records what the CGAL corefinement path does — whether the
operand is even *built*, which precondition it violates, what the boolean returns,
and whether `PMP::stitch_borders` (the repair the manual points at for meshes
whose borders should be joined) repairs it.

*Border halfedges* is `size_of_border_halfedges()` after `normalize_border()`;
without that call `Polyhedron_3` does not maintain the count.

| Setting | Input | Closed | Self-intersects | Outward | Border halfedges | Boolean |
|---|---|---|---|---|---|---|
| Epick, f64 input | operand B as built | False | True | n/a (not closed) | 3 | - |
| Epick, f64 input | A ∪ B | - | - | - | - | returned `False`, 0 facets |
| Epick, f64 input | A ∩ B | - | - | - | - | returned `False`, 0 facets |
| Epick, f32-rounded input | operand B as built | False | True | n/a (not closed) | 3 | - |
| Epick, f32-rounded input | A ∪ B | - | - | - | - | returned `False`, 0 facets |
| Epick, f32-rounded input | A ∩ B | - | - | - | - | returned `False`, 0 facets |
| Epick, f64 input | operand B after `stitch_borders` | False | True | n/a (not closed) | 3 | 9v/13f → 9v/13f |

## Probe D — the three contact cases

Three cases in the set have operands that touch without overlapping, and the
main table shows CGAL refusing exactly one of them. This probe puts the three
side by side so the refusal is read in context. `shared_edge` is the case whose
union would have a **non-manifold edge** — four facets meeting along the line
x=1, y=1 — which a `Polyhedron_3`, a halfedge data structure, cannot hold;
`touching_vertex` and `coplanar_faces` touch in ways a 2-manifold surface can
represent. *Components* is the distinct-id count from `PMP::connected_components`.

| Case | Op | Returned | Verts | Tris | Components | V(result) | This driver's check |
|---|---|---|---|---|---|---|---|
| `coplanar_faces` | union | True | 18 | 32 | 1 | 2 | valid |
| `coplanar_faces` | intersection | True | 0 | 0 | - | - | empty result |
| `shared_edge` | union | False | 0 | 0 | - | - | empty result |
| `shared_edge` | intersection | True | 0 | 0 | - | - | empty result |
| `touching_vertex` | union | True | 16 | 24 | 2 | 2 | valid |
| `touching_vertex` | intersection | True | 0 | 0 | - | - | empty result |

## Probe E — run-to-run determinism

The same operands, rebuilt from the reference set and run N times in one process.
*Signatures* is the number of distinct `(verts, tris, volume)` triples observed; a
deterministic library produces exactly one. Asked of every candidate because a
kernel whose output depends on scheduling cannot be diffed, cached or
regression-tested.

Two further columns separate two different things a varying signature could mean.
*Distinct geometries* counts distinct **sorted** multisets of vertex coordinates —
order-independent, so it changes only if the solid itself changed. *Distinct
emission orders* counts distinct vertex lists in the order CGAL emitted them.
`reference.signed_volume` sums in emission order, so a pure reordering moves the
last bits of the sum without moving a single vertex; the two columns say which of
the two happened.

| Case | Op | Runs | Signatures | Distinct geometries | Distinct emission orders | Distinct results |
|---|---|---|---|---|---|---|
| `overlap_half` | union | 10 | 1 | 1 | 10 | 24v/44f/V=1.5 x10 |
| `wall_with_openings` | union | 10 | 2 | 1 | 10 | 320v/636f/V=12.600000000000003 x7; 320v/636f/V=12.6 x3 |
| `wall_with_openings` | difference | 10 | 4 | 1 | 10 | 224v/492f/V=3.600000000000017 x6; 224v/492f/V=3.6000000000000143 x2; 224v/492f/V=3.6000000000000205 x1; 224v/492f/V=3.600000000000018 x1 |
| `sliver` | intersection | 10 | 3 | 1 | 10 | 20v/36f/V=9.99999999612422e-08 x3; 20v/36f/V=9.999999995661628e-08 x4; 20v/36f/V=9.999999995199034e-08 x3 |

## Probe F — corefinement modifies its operands

`corefine_and_compute_union(A, B, out)` corefines A and B against each other
*in place* before extracting the result: after the call, A and B carry the
intersection polylines as new vertices and facets. Every driver loop in this file
rebuilds both operands per repeat because of it. This probe measures the effect
once per case, on the f64 setting, with the union.

| Case | Returned | A before | A after | B before | B after | Operands changed |
|---|---|---|---|---|---|---|
| `disjoint` | True | 8v/12f | 8v/12f | 8v/12f | 8v/12f | no |
| `overlap_half` | True | 8v/12f | 20v/36f | 8v/12f | 20v/36f | **yes** |
| `coplanar_faces` | True | 8v/12f | 11v/18f | 8v/12f | 11v/18f | **yes** |
| `shared_edge` | False | 8v/12f | 8v/12f | 8v/12f | 8v/12f | no |
| `touching_vertex` | True | 8v/12f | 8v/12f | 8v/12f | 8v/12f | no |
| `identical` | True | 8v/12f | 8v/12f | 8v/12f | 8v/12f | no |
| `contained` | True | 8v/12f | 8v/12f | 8v/12f | 8v/12f | no |
| `sliver` | True | 8v/12f | 28v/52f | 8v/12f | 20v/36f | **yes** |
| `near_degenerate_triangle` | False | 8v/12f | 9v/14f | 9v/13f | 9v/13f | **yes** |
| `wall_with_openings` | True | 8v/12f | 224v/444f | 96v/144f | 312v/576f | **yes** |

## Probe G — the bound kernel is Epick

`Point_3::x()` returns a Python `float`, so the bound kernel's number type is
`double`: `Exact_predicates_inexact_constructions_kernel`. If the binding were
built on `Exact_predicates_exact_constructions_kernel` the coordinate would be a
lazy exact number, and a construction such as the boolean's intersection points
would be exact rather than rounded. The volume column of the construction table
shows the consequence directly: `PMP::volume()` of the reference set's **unit
cube** is not 1.

- `Point_3(1/3, 0, 0).x()` returns `0.3333333333333333`, a Python `float`.
- `PMP::volume()` of the reference set's unit cube A (`disjoint` A): `0.9999999999999999`.

## Probe H — do the exact predicates actually decide what plain doubles cannot?

This is the probe [`../../../docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md`](../../../docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md)
needs, and the one thing in this file that measures the *predicate* rather than
the boolean. A lattice of query points `p_ij = (0.5 + i·u, 0.5 + j·u)` with
`u = 2⁻⁵³` (one ULP of 0.5), `i, j ∈ [0, 64)`, is tested for orientation
against the fixed, exactly representable pair `q = (12.0, 12.0)`, `r = (24.0, 24.0)`.

Over the rationals the determinant is exactly `12·u·(j − i)`, so the correct
answer is `sign(j − i)`. What breaks the plain double evaluation is the
*subtraction*: `12 − (0.5 + i·u)` must be rounded, because 11.5 sits in a binade
whose ULP is 2⁻⁴⁹ — sixteen times the lattice spacing — so the rounding error is
the same size as the determinant being computed. Three answers per point:

1. the sign of the determinant `(qx−px)(ry−py) − (qy−py)(rx−px)` in plain
   `double` — what a boolean without an exact predicate computes;
2. `CGAL_Kernel.orientation(Point_2, Point_2, Point_2)` — Epick's filtered
   predicate;
3. the same determinant over `fractions.Fraction` — exact, and therefore the
   **oracle**. Every input coordinate is a dyadic rational, so `Fraction(float)` is
   lossless and the oracle is not itself an approximation. The oracle was also
   checked against the closed form `sign(j − i)`: **0** disagreements out of
   4096.

| Answer | Disagreements with the exact oracle, out of 4096 |
|---|---|
| plain `double` determinant | **2164** |
| `CGAL_Kernel.orientation` (Epick) | **0** |

Three of the points where the plain determinant disagrees with the oracle:

| Query point `p` | Exact sign | Plain `double` sign |
|---|---|---|
| `(0.5, 0.5000000000000001)` | 1 | 0 |
| `(0.5, 0.5000000000000002)` | 1 | 0 |
| `(0.5, 0.5000000000000003)` | 1 | 0 |

The sign mapping used above is not assumed; `CGAL_Kernel.orientation` was called
on three known configurations and its return value recorded:

| Configuration | `orientation()` returns | Sign of the plain determinant |
|---|---|---|
| left turn | `1` | 1 |
| right turn | `-1` | -1 |
| collinear | `0` | 0 |

**No timing is reported for this probe.** Each `orientation` call crosses the SWIG
boundary and constructs two Python objects, which costs far more than the predicate
does; a ratio measured here would describe the binding, not the filter. The cost of
the filtered predicate itself is a *claimed* number in the note, with a citation.
