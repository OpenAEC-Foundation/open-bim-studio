# CGAL — exact predicates as a design, exact constructions as a cost

**Decision question:** ADR-0006 rests on two claims about CGAL that no note has yet supported:
that exact *predicates* with a floating filter are the right way to decide topology, and that
exact *constructions* everywhere are too slow to build on. Which of the two can we show, and what
does CGAL's own boolean actually do?

**Serves:** ADR-0005, ADR-0006 (Option B and Option C); kernel spec §5, §7, §12; R-16, R-17;
`problems.md` P-03, P-14

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> **Scope, stated before anything else.** What is measured here is **CGAL 6.0.1's
> `Polygon_mesh_processing` corefinement boolean through the official SWIG bindings, on
> `Exact_predicates_inexact_constructions_kernel` (Epick)**. The `cgal` PyPI wheel exposes no
> `Nef_polyhedron_3` module and no Epeck-based mesh type, and a C++ build with GMP/MPFR/Boost was
> outside this task's time budget. **`Nef_3` and the Epeck user-facing path are therefore not
> measured anywhere in this note**, and every claim about them is labelled *claimed* or
> *inferred* with a source. That matters more than usual, because `problems.md` P-03 and
> ADR-0006's Option B are *about* the unmeasured path — see §What P-03 asks and what this note
> can answer.

---

## Summary

CGAL's corefinement boolean got **8 of 10** torture cases right on both ingest settings, in
**0.011–8.21 ms**, and at 500 km from the origin it held the result to **1.29e-10 m**, passing
R-17 on the same case where feeding it float32-rounded coordinates — with the identical exact
predicates still in force — cost **0.0348 m** and 0.15 m³. The two failures are refusals, not
wrong answers, and one of them is the most interesting result in the note: `shared_edge`'s
**union** is refused while the *intersection* of the same pair succeeds, because a halfedge mesh
cannot hold the non-manifold edge the union would need — a per-operation `impossible_operation`
bit, not a generic error. The central finding is about the design, not the score: **CGAL's
boolean is already the hybrid ADR-0006 proposes** — it computes intersection points in Epeck,
keeps them exact for the duration so downstream predicates on constructed points stay exact, and
rounds to `double` on the way out. Exactness is a phase, not a storage class.

## What it is

CGAL is a C++ library of computational-geometry algorithms — the oldest copyright line in the
kernel package reads 1997 — developed by a consortium (INRIA, MPI Saarbrücken, ETH Zurich, Tel
Aviv University, Utrecht, and GeometryFactory, which maintains it commercially) and organised as
**146 packages** (measured: directories at the tag carrying their own `package_info/<name>/`),
each with its own maintainer, manual chapter and **its own licence** — **110 of them GPL**, per
the count of entries in
[`gpl_package_list.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Installation/include/CGAL/license/gpl_package_list.txt). It is the reference implementation of the exact-geometric-
computation paradigm: predicates are evaluated so that the combinatorial answer is never wrong,
while the arithmetic underneath is as cheap as it can be for the case at hand.

Three parts of it matter to this programme, and they are three different things:

* the **kernels** — `Epick` and `Epeck` — which decide what a coordinate is and how a predicate
  is evaluated;
* **`Polygon_mesh_processing`'s corefinement**, a boolean on triangulated surface meshes —
  `Copyright (c) 2016 GeometryFactory (France)`, `Author(s) : Sebastien Loriot`
  ([`corefinement.h#L1-L11`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L1-L11)) —
  and the only CGAL boolean this note measures;
* **`Nef_polyhedron_3`**, the exact boundary representation of a point set closed under boolean
  operations, from the Saarbrücken group — the design ADR-0006's Option B is named after, and the
  one this note could not run.

For the geometry that matters to us, CGAL is also the ancestor of two candidates already in this
directory: IfcOpenShell ships a CGAL-based kernel option as an alternative to OCCT, and Blender's
exact boolean descends from libigl's arrangement work, which is built on CGAL's exact predicates.

## What was read, and at which commit

Source read at tag `v6.0.1`, commit `50cfbde3b84dbeae8338268db2d78fe4fcb522de` — the tag matching
the measured wheel, whose `CGAL_VERSION_NR` is `1060010900` and `CGAL_RELEASE_DATE` `20241024`.

| Area | Source, pinned |
|---|---|
| Epick: `Simple_cartesian<double>` + filtered predicates, static filters on by default | [`Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L29-L34`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L29-L34), [`#L54-L70`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L54-L70) |
| Epeck: a lazy kernel over an exact field type, with an interval approximation | [`Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L39-L40`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L39-L40), [`#L56-L76`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L56-L76) |
| The filter itself: interval first, exact only on failure | [`Filtered_kernel/include/CGAL/Filtered_predicate.h#L87-L110`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_predicate.h#L87-L110) |
| Static filters: on by default, `Has_static_filters` detectable by client code | [`Filtered_kernel/include/CGAL/Filtered_kernel.h#L98-L125`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_kernel.h#L98-L125) |
| The manual on Epick vs Epeck, on the boolean's representability limit, and on Nef's kernel requirement | [`Kernel_23/doc/Kernel_23/Kernel_23.txt#L303-L308`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/doc/Kernel_23/Kernel_23.txt#L303-L308), [`Polygon_mesh_processing/doc/Polygon_mesh_processing/Polygon_mesh_processing.txt#L403-L433`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/doc/Polygon_mesh_processing/Polygon_mesh_processing.txt#L403-L433), [`Nef_3/doc/Nef_3/Nef_3.txt#L446-L454`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/doc/Nef_3/Nef_3.txt#L446-L454) |
| The boolean's preconditions, `throw_on_self_intersection`, and what its `bool` return means | [`Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L516-L519`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L516-L519), [`#L566-L573`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L566-L573), [`#L597-L599`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L597-L599) |
| The internal exact kernel and the exact node store | [`internal/Corefinement/intersection_nodes.h#L29-L47`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L29-L47), [`#L142-L173`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L142-L173), [`#L192-L196`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L192-L196) |
| That the boolean asks for exact predicates on constructed points | [`internal/Corefinement/Visitor.h#L453-L456`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Visitor.h#L453-L456), [`#L482-L484`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Visitor.h#L482-L484), wired at [`corefinement.h#L474-L475`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L474-L475) |
| `impossible_operation`: the per-operation refusal | [`internal/Corefinement/Face_graph_output_builder.h#L544-L548`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L544-L548), [`#L787-L802`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L787-L802), set at [`#L1740-L1751`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L1740-L1751) and [`#L1664-L1681`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L1664-L1681), returned at [`corefinement.h#L498-L501`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L498-L501) |
| `Nef_3`'s data structure: a vertex *is* a sphere map; seven linked lists | [`Nef_3/include/CGAL/Nef_3/SNC_structure.h#L131-L135`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_3/SNC_structure.h#L131-L135), [`#L1042-L1049`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_3/SNC_structure.h#L1042-L1049) |
| Licences (SPDX, per package) | see §Licence |

Measurements are in
[`spikes/boolean-torture/results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md)
and
[`spikes/precision-set/results/cgal.md`](../../../spikes/precision-set/results/cgal.md),
produced by
[`spikes/boolean-torture/cgal_driver.py`](../../../spikes/boolean-torture/cgal_driver.py)
and
[`spikes/precision-set/cgal_driver.py`](../../../spikes/precision-set/cgal_driver.py)
against the `cgal` 6.0.1 wheel on an Intel Core i9-14900HX with 32 GB of RAM.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | **Split per package, and the split runs straight through what we would want.** The kernel, the filtering and the number types are LGPL — every one of the 92 headers under `Kernel_23/include/`, the 39 under `Filtered_kernel/include/` and the 92 under `Number_types/include/` carries `SPDX-License-Identifier: LGPL-3.0-or-later OR LicenseRef-Commercial`. The **boolean, the mesh type and `Nef_3` are GPL**: all 58 headers under `Nef_3/include/`, 22 of 23 under `Polyhedron/include/` (`Polyhedron_3.h` included) and 88 of 89 under `Polygon_mesh_processing/include/` carry `GPL-3.0-or-later OR LicenseRef-Commercial`. Borrowing the *predicate* design as code is legally possible; borrowing the *boolean* — or even the mesh class it operates on — as code is not, for a product we do not intend to ship under GPL. | source | SPDX lines, §Licence |
| **Representations held natively** | **Several, but not as one kernel.** Separate packages hold a halfedge B-rep (`Polyhedron_3`, `Surface_mesh`), a Nef point set (`Nef_polyhedron_3`), point sets (`Point_set_3`), and 3D triangulations/meshes (`Mesh_3`). There is no single object that holds more than one, and conversions are package-level free functions, not a conversion module. It is a *library of representations*, not a multi-representation kernel. | source + inferred | binding module list; package layout at the tag |
| **Boolean robustness** | Measured on the torture set, **Epick input only** (Epeck/Nef unmeasured — see the scope box): **8 of 10 cases valid and numerically correct on both settings**, worst identity residual **7.11e-15** on f64 input (0 on f32-rounded input) — the tightest of any candidate measured. The two failures are **refusals**: `near_degenerate_triangle` (the T-junction operand violates two documented preconditions) and, more interestingly, `shared_edge`'s **union only**, where the intersection of the same pair succeeds. Algorithm class: exact predicates throughout, plus exact *constructions internally, discarded on output* (§The hybrid). | measured + source | [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md); `intersection_nodes.h`, `Face_graph_output_builder.h` |
| **Tolerance and precision model** | **There is no tolerance.** Epick stores `double` and has no per-entity or global epsilon anywhere — the driver's storage table has no tolerance column because there is nothing to put in it, which is the exact opposite of OCCT's tolerant B-rep and of Manifold's box-derived epsilon. Metric questions are answered by exact comparison of stored doubles; combinatorial questions by exact predicates. The cost of that purity is that a near-coincidence is *not* a coincidence, and nothing merges it. | measured + source | [`precision results`](../../../spikes/precision-set/results/cgal.md); `Epick` header |
| **Incremental evaluation** | **None at kernel level.** The boolean is a free function over two meshes; there is no dependency graph, no operation history, no handle that survives a recompute. Worse for our purposes: corefinement **modifies both operands in place** (measured: the wall's A goes 8v/12f → 224v/444f), so "re-run with one operand changed" means rebuilding both. | measured + inferred | [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md) Probe F |
| **Threading model** | **Unmeasured.** CGAL has TBB-based parallelism in some packages behind a `CGAL::Parallel_tag` concurrency tag; the corefinement API measured here takes no such tag, so there is no parallel mode to switch on from this binding. This note did not measure thread usage or a speedup, and claims neither. | inferred | corefinement API at the tag; binding surface |
| **GPU path** | **None.** CGAL has no GPU backend and no upload path; a caller exports triangles itself. | source | package layout |
| **IFC coverage** | Not applicable — no schema layer. CGAL reaches IFC only through IfcOpenShell's CGAL kernel option, which is a separate note. | source | — |
| **Performance** | Measured, **Epick input only** (Epeck/Nef unmeasured), median of 5, fresh operands per repeat: **0.011–8.21 ms** over the forty timings (ten cases × two settings × two operations). Twelve-opening wall union **8.21 ms**, intersection 7.84 ms. On the identical case, for scale across harnesses: Manifold 0.837 / 0.588 ms, Blender's Manifold solver 1.76 / 1.33 ms, Blender's exact solver 15.95 / 15.90 ms, OCCT's `BRepAlgoAPI_Fuse` 53.97 / 49.24 ms. **Read these as orders of magnitude, not as a benchmark**: four harnesses, four data structures, and no attempt to isolate the arithmetic. | measured | [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md), and the same tables for the other candidates |
| **Embeddability** | **Weak for our case.** Header-only for much of the kernel, but Epeck needs GMP/MPFR and PMP needs Boost; the Python binding is a 25 MB SWIG wheel. A DynLex FFI would face a C++ template API with no C ABI — the opposite of Manifold's `bindings/c`. | inferred | wheel contents; `Epeck_ft` selecting `Gmpq` |
| **2D derivation** | Strong in kind: `Polygon_mesh_slicer` is in the binding, and CGAL has 2D arrangements, Boolean set operations and Minkowski sums as separate packages. **No hidden-line removal and no drawing layer** — a section is a polyline set. | source | binding module list |
| **Maturity** | Nearly three decades (oldest kernel copyright line 1997), a consortium plus a commercial maintainer (GeometryFactory), and an active release train — `git ls-remote --tags` shows the line reaching **v6.2.1** while this note measures v6.0.1, with four patch releases on the 6.0 branch alone. Bus factor is high for the library and **low per package**: the corefinement tickets in §Known problems are answered by essentially one person. | source + inferred | tag list; issue survey |
| **AI familiarity** | Very large public corpus: 30 years of source, a full manual per package, and a heavily used tracker. One column, never a tiebreaker (R-09). | inferred | repository and manual size |

## Licence — the split runs through the middle of what we want

CGAL is not "the GPL one" or "the LGPL one". Each file carries its own SPDX identifier — the
top-level licence says so itself, that it is "specified in each file of the CGAL library which
license applies to it"
([`Installation/LICENSE#L10-L11`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Installation/LICENSE#L10-L11)) —
and the boundary falls exactly between the part this note recommends borrowing and the part it
does not.

| Package | Representative file | `SPDX-License-Identifier` | Package declaration |
|---|---|---|---|
| `Kernel_23` (Epick) | [`Exact_predicates_inexact_constructions_kernel.h#L12`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L12) | `LGPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/package_info/Kernel_23/license.txt): `LGPL (v3 or later)` |
| `Kernel_23` (Epeck) | [`Exact_predicates_exact_constructions_kernel.h#L12`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L12) | `LGPL-3.0-or-later OR LicenseRef-Commercial` | as above |
| `Filtered_kernel` | [`Filtered_predicate.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_predicate.h#L8) | `LGPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/package_info/Filtered_kernel/license.txt): `LGPL (v3 or later)` |
| `Number_types` | [`Lazy_exact_nt.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Number_types/include/CGAL/Lazy_exact_nt.h#L8) | `LGPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Number_types/package_info/Number_types/license.txt): `LGPL (v3 or later)` |
| `Polyhedron` (the mesh class the boolean runs on) | [`Polyhedron_3.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polyhedron/include/CGAL/Polyhedron_3.h#L8) | `GPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polyhedron/package_info/Polyhedron/license.txt): `GPL (v3 or later)` |
| `Polygon_mesh_processing` (corefinement) | [`corefinement.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L8) | `GPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/package_info/Polygon_mesh_processing/license.txt): `GPL (v3 or later)` |
| `Polygon_mesh_processing` (the exact node store) | [`intersection_nodes.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L8) | `GPL-3.0-or-later OR LicenseRef-Commercial` | as above |
| `Nef_3` | [`Nef_polyhedron_3.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_polyhedron_3.h#L8) | `GPL-3.0-or-later OR LicenseRef-Commercial` | [`license.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/package_info/Nef_3/license.txt): `GPL (v3 or later)` |
| `Nef_3` (the SNC structure) | [`SNC_structure.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_3/SNC_structure.h#L8) | `GPL-3.0-or-later OR LicenseRef-Commercial` | as above |

*(source; each SPDX cell is the literal identifier at that file and line at the pinned commit,
and a whole-tree sweep of every header in those six packages found exactly two files that deviate
from their package's identifier:
[`Polyhedron_3_to_lcc.h`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polyhedron/include/CGAL/Polyhedron_3_to_lcc.h)
is LGPL inside a GPL package, and
[`Polyhedral_envelope.h#L8`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polyhedral_envelope.h#L8)
reads `( GPL-3.0-or-later OR LicenseRef-Commercial ) AND MIT`, which is the whole reason PMP's
`license.txt` has a second line. **Neither is on the corefinement path.**)*

CGAL also enforces this at compile time, and the enforcement list is itself citable: the GPL
packages are enumerated in
[`Installation/include/CGAL/license/gpl_package_list.txt`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Installation/include/CGAL/license/gpl_package_list.txt),
where `Nef_3`, `Polygon_mesh_processing/corefinement` and `Polyhedron` all appear. There is no
corresponding `lgpl_package_list.txt` — the mechanism only tracks the copyleft side.

The consequence is specific and it is the first hard licence datum `problems.md` P-14 has had:
**the design we want to borrow is in the LGPL half, and every line of the implementation we might
have wanted to lift — the boolean, its exact node store, and even `Polyhedron_3` itself — is in
the GPL half.** Borrowing the filtered-predicate *idea* is free; it is published literature
(§Sources), and its implementation in `Filtered_predicate.h` is LGPL, so linking it is an LGPL
question rather than a GPL one. Copying corefinement's code into our kernel would put the kernel
under GPL, which R-11 rules out. `LicenseRef-Commercial` is the dual-licence escape and is a
purchasing decision, not a technical one; this note does not evaluate it.

## The design ADR-0006 rests on, measured

### Filtered predicates, and the Epick/Epeck distinction in one page

The two kernels differ in exactly one place, and each header says so in a handful of lines.

**Epick** is `Simple_cartesian<double>` — plain doubles — with the *predicates* replaced by
filtered ones:

```
template <typename NT, typename Kernel>
using Epick_with_filtered_predicates =
    Filtered_kernel_adaptor<Epick_base_with_type_equality<NT, Kernel>, epick_use_static_filter>;
...
class Epick : public internal::Epick_with_filtered_predicates<double, Epick> {};
```

([`Exact_predicates_inexact_constructions_kernel.h#L54-L63`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L54-L63).)
Static filters are **on unless you switch them off**: `epick_use_static_filter` is `true` unless
`CGAL_NO_STATIC_FILTERS` is defined
([`#L29-L34`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L29-L34)).
A construction — an intersection point, a midpoint — is a plain double operation and rounds. CGAL's
own manual puts the same sentence the other way round: Epick has exact "geometric predicates, but
geometric constructions may be inexact due to round-off errors", and is "faster than the kernels
with exact constructions below"
([`Kernel_23.txt#L303-L306`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/doc/Kernel_23/Kernel_23.txt#L303-L306) —
*claimed*, for the "faster" half, which this note does not measure).

The **filter** itself is twenty lines and worth reading once, because it is the whole idea:

```
Protect_FPU_rounding<Protection> p;
try
  {
    Ares res = ap(c2a(args)...);
    if (is_certain(res))
      return get_certain(res);
  }
catch (Uncertain_conversion_exception&) {}
...
return ep(c2e(args)...);
```

([`Filtered_predicate.h#L87-L110`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_predicate.h#L87-L110).)
Convert the arguments to intervals, run the approximate predicate, return if the answer is
*certain*; otherwise convert to the exact type and run the exact predicate. The exact path is the
fallback, not the default, and the FPU rounding mode is set around the interval block rather than
globally. `Filtered_kernel_adaptor` then decides whether the cheaper *static* filters are layered
on top, and exposes `Has_static_filters` so client code can tell which it got
([`Filtered_kernel.h#L98-L125`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_kernel.h#L98-L125)).

**Epeck** replaces the number *type*, not the predicate. `Epeck_ft` is an exact field type
selected at compile time, and the kernel is a *lazy* kernel: every object carries an interval
approximation plus a DAG of the exact construction that made it.

```
using Epeck_ft = internal::Exact_field_selector<double>::Type;
...
using Epeck_interval = Simple_cartesian<Interval_nt_advanced>;
...
using Epeck_lazy_base = Lazy_kernel_base<Epeck_sc<FT>, Epeck_interval, Epeck_converter<FT>, Kernel>;
```

([`Exact_predicates_exact_constructions_kernel.h#L39-L40`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L39-L40),
[`#L56-L72`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L56-L72);
the header's own comment says Epeck is "equivalent to `Lazy_kernel<Simple_cartesian<Epeck_ft>>`",
[`#L71`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L71).)

That DAG is where the cost of exact constructions lives, and it is why the cost is not a constant
factor but a function of *how many operations a coordinate has been through* — the mechanism a
CGAL maintainer named on [#8074](https://github.com/CGAL/cgal/issues/8074), where 360 successive
`Nef_polyhedron_3::transform()` calls exhausted memory: `sloriot` (**MEMBER**) attributes it to
"you are generating a deep DAG", and warns that flattening it is not enough because "memory will
still increase as the exact number type will nonetheless require more precision"
(*claimed*, maintainer statement).

### The predicate is worth having: measured, 2164 wrong answers out of 4096

The claim ADR-0006 makes — that a floating-point comparison is not a safe way to decide which
side of a plane a point is on — is the kind of claim that gets asserted more often than shown.
It is shown here, in the one probe that measures the *predicate* rather than the boolean.

A lattice of query points `p_ij = (0.5 + i·u, 0.5 + j·u)` with `u = 2⁻⁵³`, `i, j ∈ [0, 64)`, is
tested for orientation against the fixed, exactly representable pair `q = (12, 12)`,
`r = (24, 24)`. Over the rationals the determinant is exactly `12·u·(j − i)`, so the right answer
is `sign(j − i)`. What breaks the plain double evaluation is the *subtraction*: `12 − (0.5 + i·u)`
must round, because 11.5 lives in a binade whose ULP is 2⁻⁴⁹ — sixteen times the lattice spacing
— so the rounding error is the same size as the quantity being computed.

| Answer | Disagreements with an exact-rational oracle, out of 4096 |
|---|---|
| plain `double` determinant | **2164** |
| `CGAL_Kernel.orientation` (Epick's filtered predicate) | **0** |

*(measured, [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md) Probe H. The
oracle is the same determinant over `fractions.Fraction`; every coordinate is a dyadic rational,
so `Fraction(float)` is lossless. The oracle was independently checked against the closed form
`sign(j − i)`: 0 disagreements out of 4096.)*

**53% of the plain-double answers are wrong, and the exact predicate is never wrong.** This is
the evidence row "floating-point topology decisions cause invalid booleans" in ADR-0006's table
has been missing. Two honest limits on it: the lattice is constructed to be hard, so the *rate*
is a property of the construction and not of building geometry; and no timing is reported,
because each call crosses the SWIG boundary and builds two Python objects, so a ratio measured
here would describe the binding rather than the filter. The filter's cost is *claimed* in
§Sources, from the paper CGAL's own implementation follows.

### f32-rounded input, with the exact predicates still on

This is the cleanest form of ADR-0006's question that any candidate has allowed. Both settings
run the same exact predicates on the same algorithm; the only difference is that one ingests the
reference set's coordinates verbatim and the other rounds each coordinate to the nearest float32
first (and still stores a `double`).

| Setting | Wall union V near / far | ΔV (relative) | Worst vertex deviation | R-17 |
|---|---|---|---|---|
| **f64 input** | 12.6 / 12.5999999999 | −1.1e-11 | **1.29e-10 m** | **pass** (line 1e-6 m) |
| **f32-rounded input** | 12.6000000179 / 12.7499997485 | +0.0119 | **0.0348 m** | **fail** (line 1e-4 m) |

*(measured, [`precision results`](../../../spikes/precision-set/results/cgal.md).)*

**Exact predicates do not rescue float32 storage.** The f32-rounded row's +0.15 m³ and 0.0348 m
are the same numbers `blender.md` §Precision reports for Blender's exact solver on this case, and
the +0.15 m³ is the same figure `manifold.md` reports on its f32 path. Three independent
implementations, three different algorithms, one storage type, one answer. The loss happens
before any predicate is consulted, and no amount of exactness downstream can recover a coordinate
that was never delivered.

Two further readings from the same file. The `overlap_half` and `coplanar_faces` cases show
**0 m** deviation even on the f32-rounded row, because every coordinate they use (0, 0.5, 1, 1.5,
500000) is exactly representable in float32 — a reminder that a precision test passes trivially
on round numbers, and that the wall is the case that matters. And on the f64 path CGAL's own
far-field figure sits in the middle of the field on the identical case: **3.3e-11 m** for Manifold
on `Mesh64`, **1.29e-10 m** for CGAL, **2.65e-10 m** for OCCT. All three are within a factor of
four of each other and all three pass R-17 by four orders of magnitude; **none of them is where
the risk is** — the f32 row is.

## The hybrid: what CGAL's boolean actually does with exact arithmetic

This is the finding that changes how ADR-0006 should be written, and it is entirely in source.

The user's kernel is Epick, so every stored coordinate is a `double`. But the boolean does not
compute its intersection points in doubles. `Intersection_nodes` is specialised on whether the
*input* kernel already has exact constructions —

```
bool Has_exact_constructions =
!std::is_floating_point<
  typename Kernel_traits<
    typename boost::property_traits<VertexPointMap1>::value_type
  >::Kernel::FT
 >::value
```

([`intersection_nodes.h#L32-L37`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L32-L37))

— and when it does not, the specialisation used by the boolean is the one whose own comment reads
"store an exact copy of the points so that we can answer exactly predicates"
([`#L142-L143`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L142-L143)).
It hard-codes the exact kernel —

```
typedef CGAL::Exact_predicates_exact_constructions_kernel        Exact_kernel;
...
typedef std::vector <Exact_kernel::Point_3>                       Exact_nodes;
Exact_nodes enodes;
```

([`#L149`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L149),
[`#L166-L168`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L166-L168))

— and rounds only at the boundary, where the caller asks for a point:

```
Point_3 operator[](std::size_t i) const { return exact_to_double(enodes[i]); }
```

([`#L192-L196`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L192-L196).)

That the *boolean* takes this branch rather than the cheaper "store only the double version"
one ([`#L40-L47`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L40-L47))
is decided by a flag on its visitor, `static const bool Predicates_on_constructions_needed = true`
([`Visitor.h#L453-L456`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Visitor.h#L453-L456)),
which is the visitor `corefine_and_compute_union` instantiates
([`corefinement.h#L474-L475`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L474-L475)).

**One qualification, because the maintainer's shorthand is not unconditional.** The hard-coded
Epeck applies only when the *input* kernel's `FT` is a floating-point type — Epick,
`Simple_cartesian<double>`, `Cartesian<double>`. A caller who already supplies Epeck (whose `FT`
is a `Lazy_exact_nt`, not a `float` or `double`) selects a third specialisation whose comment
reads "The kernel already has exact constructions" and whose `Exact_kernel` is simply the user's
own
([`intersection_nodes.h#L322-L345`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L322-L345)).
So: Epeck is hard-coded *for the Epick case*, which is the case measured here and the case most
callers are in — not for every case.

A CGAL maintainer states the same thing in one sentence. On
[#9154](https://github.com/CGAL/cgal/issues/9154), asked directly whether corefinement uses the
user's inexact kernel internally, `sloriot` (**MEMBER**) answers: "As soon as a construction
occurs, an internal exact representation is stored". On
[#5119](https://github.com/CGAL/cgal/issues/5119), asked to make the internal Epeck optional so
the code can run under WebAssembly, he confirms it is deliberate — "The use of EPECK is here for
robustness issues. In practice I could get rid of it but this requires a major effort" — and
warns what removing the interval filter would cost: "without interval you have no filter at all",
concluding "I'm afraid the runtime will be a killer for your application" (*claimed*, maintainer
statements; roles are the `author_association` the API reports for those comments).

**Why this matters more than the score.** ADR-0006's options are written as a binary: Option B is
"exact rational arithmetic everywhere ... the CGAL Nef-polyhedra approach", Option C is exact
predicates with floating construction. CGAL's own production boolean is neither. It is:

* exact **predicates**, always;
* exact **constructions**, held for the duration of one operation so that predicates *on
  constructed points* are also exact;
* rounded to `double` at the operation's boundary, so nothing exact is ever *stored*.

That third position — exactness as a phase, not a storage class — is what kernel spec §5 should
say, and it is what the measured 8.21 ms on the twelve-opening wall is the price of. It also
explains a failure mode a maintainer describes as inherent rather than fixable: on
[#9154](https://github.com/CGAL/cgal/issues/9154) `sloriot` (**MEMBER**) says the output "contains
self-intersections created when the exact intersection points are rounded to double". **The
rounding at the boundary is where CGAL's residual defects live**, and any design that copies the
hybrid inherits exactly that seam.

## What P-03 asks, and what this note can and cannot answer

`problems.md` P-03 reads: *"Exact boolean is correct but too slow or memory-hungry for interactive
use"*, root cause *"Exact rational arithmetic on every construction, not only on predicates"*,
seen in *"CGAL Nef polyhedra"*. ADR-0006 cites `kernels/cgal.md` §Measurements for it.

**That citation cannot be honoured as written, and the ADR must be amended rather than
satisfied.** We did not measure `Nef_polyhedron_3`, and nothing in this note's §Measurements
speaks to it. What we have instead is four things, of three different strengths:

1. **The mechanism, shown in source (inferred).** `Nef_3`'s Selective Nef Complex allocates
   *seven* separately-allocated doubly-linked item lists — vertices, halfedges, halffacets,
   volumes, shalfedges, shalfloops, sfaces
   ([`SNC_structure.h#L1042-L1049`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_3/SNC_structure.h#L1042-L1049)) —
   and, crucially, **a Nef vertex *is* a complete 2D sphere map**, not a point:
   `typedef Sphere_map Vertex_base;`
   ([`#L131-L135`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/include/CGAL/Nef_3/SNC_structure.h#L131-L135)).
   Each of those vertices then carries exact rational coordinates: the class documentation
   requires "one of the following exact kernels" and lists only ℤ- and ℚ-based ones
   ([`Nef_polyhedron_3.h#L29-L34`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/doc/Nef_3/CGAL/Nef_polyhedron_3.h#L29-L34)),
   and the manual recommends Epeck among them because it "uses filtering"
   ([`Nef_3.txt#L446-L454`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/doc/Nef_3/Nef_3.txt#L446-L454)).
   Both halves of P-03's root cause — the arithmetic and the structure — are visible; neither is
   timed by us. The manual's own nearest thing to a cost statement is that restricting to
   *bounded* Nef polyhedra "improves considerably space requirements (plain number type instead of
   polynomial), and runtime performance"
   ([`Nef_3.txt#L277-L280`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Nef_3/doc/Nef_3/Nef_3.txt#L277-L280) —
   *claimed*, and a relative statement with no absolute number attached).
2. **Maintainer statements that exact constructions are non-negotiable there (claimed).** On
   [#5490](https://github.com/CGAL/cgal/issues/5490) `sloriot` (**MEMBER**): "Nef (and Minkowski)
   requires exact constructions so it cannot work with floating point based number type." On
   [#8074](https://github.com/CGAL/cgal/issues/8074) he attributes a memory blow-up to the lazy
   DAG's depth. Neither is a measurement.
3. **Third-party measurements, all by non-maintainers (claimed).** On
   [#5379](https://github.com/CGAL/cgal/issues/5379) `GilesBathgate` (**CONTRIBUTOR**) reports
   **50.498 s** to convert one `Polyhedron_3` (`refined_elephant.off`) into a
   `Nef_polyhedron_3`, and **29.798 s** after his own optimisations — merged, and the ticket
   closed by `lrineau` (**MEMBER**). On [#7271](https://github.com/CGAL/cgal/issues/7271)
   `kintel` (**CONTRIBUTOR**) reports that the Surface_mesh-to-Nef conversion using
   `CGAL::Cartesian<CGAL::Gmpq>` takes "~1 minute on an Apple M1" for a "relatively simple
   checkerboard model", after separately finding the `Nef_nary_union_3` approach — unioning each
   face of the polygon soup individually — "prohibitively expensive" on its own, with no figure
   given for it. These are reporters' numbers on their own models, not ours, and
   they are construction cost rather than boolean cost — a distinction `afabri` (**MEMBER**) makes
   on the same ticket with his own profile of two Nef spheres: "I spend 80% in the Boolean
   operation and only 20% in the initial construction."
4. **One measurement of ours that bears on the trade indirectly (measured).** CGAL's corefinement
   holds exact constructions *for the duration of the operation* and ran the twelve-opening wall
   in 8.21 ms — 9.8× Manifold's 0.837 ms on the same case through a different harness, 1.9×
   faster than Blender's exact-rational solver, and 6.6× faster than OCCT's B-rep fuse. So
   transient exact constructions are affordable at building scale on this case. **Nothing here
   shows that persistent ones are not**, and the ratio is across harnesses, so it bounds nothing
   tightly.

**Verdict on P-03: partly shown, and mis-scoped as written.** The exactness/speed trade has more
than the two positions the row implies — `manifold.md` already added a third (double predicates
with a symbolic tie-break), and this note adds a fourth (exact constructions held transiently and
rounded on output) which is what CGAL's own shipped boolean does. The row's claim about *Nef* is
supported by mechanism and by third-party reports, not by our measurement, and P-03's status
should say so.

## Known problems

### Issue-tracker survey

Twenty-two tickets read on corefinement failures, precondition violations, Nef time and memory,
and kernel choice. Every speaker's role below is the `author_association` the GitHub REST API
reports **for that comment**, not an assumption from the login. In this repository
`sloriot`, `afabri`, `lrineau`, `mglisse` and `MaelRL` all report as **MEMBER**; several logins
that read like insiders — `dpapavas`, `GilesBathgate`, `kintel`, `pentacular`, `benlaurie` — report
as **CONTRIBUTOR**, and `petrasvestartas`, `ochafik` and others as **NONE**. (`gh issue view` has
no `authorAssociation` field; these were read through `gh api repos/CGAL/cgal/issues/N` and
`.../comments`, which return it per comment.)

| # | Trigger | Traced cause, and by whom | State | Link |
|---|---|---|---|---|
| 5119 | corefinement's internal Epeck blocks a WebAssembly build (no rounding-mode control) | **Maintainer, by design.** `sloriot` (MEMBER): "The use of EPECK is here for robustness issues. In practice I could get rid of it but this requires a major effort", and on dropping the interval filter: "without interval you have no filter at all" | **open** 2020-10 | [issue](https://github.com/CGAL/cgal/issues/5119) |
| 9154 | two self-intersection-free meshes corefined into a self-intersecting result | **Maintainer, inherent.** `sloriot` (MEMBER): the output "contains self-intersections created when the exact intersection points are rounded to double", and "As soon as a construction occurs, an internal exact representation is stored". `remove_almost_degenerate()` recommended; closed by `MaelRL` (MEMBER) | closed 2025-12 | [issue](https://github.com/CGAL/cgal/issues/9154) |
| 9467 | `corefine_and_compute_intersection` fails where union and difference succeed | **Maintainer, and the same shape as our own `shared_edge` finding.** `sloriot` (MEMBER): the meshes are "oriented in such a way that the volumes they bound are infinite", and separately "the intersection contains some non-manifold edges and is not representable as 2-manifold" | closed 2026-05 | [issue](https://github.com/CGAL/cgal/issues/9467) |
| 9486 | two facets sharing all three edges pass `does_self_intersect`, then `does_bound_a_volume` segfaults (Epeck) | **Maintainer, self-reported regression.** `sloriot` (MEMBER): "I did fix does-self-intersect that I broke while adding support for triangle soup" | closed 2026-06, fixed by PR 9506 | [issue](https://github.com/CGAL/cgal/issues/9486) |
| 9139 | coincident triangles on watertight solids → assertion in `Corefinement/Visitor.h` | **Maintainer, retracted then re-diagnosed.** `sloriot` (MEMBER) first: "It seems that you found a bug! I'll update the ticket when I have a fix"; six weeks later: "Actually the problem comes from the fact that you are using a kernel with inexact predicates" — the reporter's meshes used `Simple_cartesian<double>`, i.e. *no filter*, not Epick | closed 2025-12 | [issue](https://github.com/CGAL/cgal/issues/9139) |
| 6481 | 5000-step machining simulation; fails at step 3 on a collinearity assertion | **Maintainers, and unresolved.** `sloriot` (MEMBER): "You are having issues with rounding to double", then of the exact-point workaround: "you then have the runtime issue I was mentioning earlier". `afabri` (MEMBER) supplies the structural cause: each pass adds "a new layer of vertical faces" that are cut again | **open** 2022-04 | [issue](https://github.com/CGAL/cgal/issues/6481) |
| 6363 | the *same* Epeck corefinement union gives different output at `-O0` and `-O2` | **Maintainer, flagged as a suspicion and never investigated.** `sloriot` (MEMBER): "I suspect that `std::unordered_map` and `boost::unordered_map` have different ordering". Reported by `ochafik` (NONE) | **open** 2022-02 | [issue](https://github.com/CGAL/cgal/issues/6363) |
| 7071 | `corefine_and_compute_union` asserts in debug, returns `false` in release | **Maintainer.** `sloriot` (MEMBER): "Your meshes have some self-intersections and boundary edges"; fixed caller-side by "A simple call to `stitch_borders()` on each mesh". The reporter (NONE) first denied the border edges, then confirmed them | closed 2023-03 | [issue](https://github.com/CGAL/cgal/issues/7071) |
| 5264 | `Intersection_of_constraints_exception` from near-coincident vertices | **Maintainer, plus a gap he names himself.** `sloriot` (MEMBER): "This is due to points being very closed but not equal", and "There are several functions in CGAL to fix your input but they are not documented" | closed 2021-12 | [issue](https://github.com/CGAL/cgal/issues/5264) |
| 8395 | `corefine_and_compute_union` returns `false`; no diagnosis available to the caller | **Not traced — no maintainer ever commented.** The only two comments are the reporter `ankofl`'s (NONE) own; he moved to a repair pipeline and reported that "performance was hit" | closed 2024-08 | [issue](https://github.com/CGAL/cgal/issues/8395) |
| 9455 | chain of three Epick difference operations; segfault on the third | **Reporter's diagnosis, never endorsed.** `petrasvestartas` (NONE) attributes it to inexact constructions and reports the chain succeeding under Epeck; `afabri` (MEMBER) replies only with a documentation pointer, and `sloriot` (MEMBER) with "Shall we close this issue or are you still expecting something from us?" The reporter closed it himself | closed 2026-06 | [issue](https://github.com/CGAL/cgal/issues/9455) |
| 9282 | repeated difference operations stop producing the expected result | **Maintainer, and an explicit refusal to blame the kernel.** `MaelRL` (MEMBER): "One of the CC is not triangulated, maybe it creates some issue". Asked how to switch kernels from Python, `afabri` (MEMBER): "I don't see the need for switching kernels. Just triangulate faces." | closed 2026-04 | [issue](https://github.com/CGAL/cgal/issues/9282) |
| 4522 | infinite loop when the output mesh aliases an input mesh | **Not narrated; fixed in two days.** `sloriot` (MEMBER) wrote only "Fixed by #4524"; `lrineau` (MEMBER) closed it | closed 2020-02, fixed by PR 4524 | [issue](https://github.com/CGAL/cgal/issues/4522) |
| 8074 | 360 successive `Nef_polyhedron_3::transform()` calls exhaust memory | **Maintainer.** `sloriot` (MEMBER): "you are generating a deep DAG"; the mitigation is partial — "memory will still increase as the exact number type will nonetheless require more precision". **No numeric memory figure appears in the ticket text**; the evidence is an attached profiler screenshot | closed 2024-03, not fixed | [issue](https://github.com/CGAL/cgal/issues/8074) |
| 5490 | `Nef_polyhedron_3` and `minkowski_sum_3` assert under an inexact kernel | **Maintainer, won't-fix in effect.** `sloriot` (MEMBER): "Nef (and Minkowski) requires exact constructions so it cannot work with floating point based number type" | **open** 2021-02 | [issue](https://github.com/CGAL/cgal/issues/5490) |
| 7271 | Nef construction from "two cubes sharing an edge" asserts | **Maintainer, input-side — and the damage is upstream.** `sloriot` (MEMBER): "it's a self-intersection that Nef does not accept as input", and "once you have a Surface_mesh, it is already too late". Filed by `GilesBathgate` (CONTRIBUTOR) on a related self-intersecting-triangles case; `kintel` (CONTRIBUTOR) raised the "two cubes sharing an edge" case in a later comment, which is what the quoted replies answer | **open** 2023-02 | [issue](https://github.com/CGAL/cgal/issues/7271) |
| 6738 | a Nef join asserts where **the same join succeeds through corefinement** | **Reporter's, after a maintainer pointer.** `sloriot` (MEMBER) supplied only "`Nef_polyhedron::is_valid()` says it is not valid"; the causal account is `dpapavas`'s (CONTRIBUTOR) | closed 2022-07 | [issue](https://github.com/CGAL/cgal/issues/6738) |
| 5379 | `polygon_mesh_to_nef_3` construction performance | **Reporter's, entirely.** `GilesBathgate` (CONTRIBUTOR) profiled and patched it: **50.498 s → 29.798 s** on `refined_elephant.off`. `afabri` (MEMBER) qualified the framing with his own measurement: "I spend 80% in the Boolean operation and only 20% in the initial construction" | closed 2021-03, fixed | [issue](https://github.com/CGAL/cgal/issues/5379) |
| 2781 | `Nef_polyhedron_3` intersection of three half-space planes asserts, even with plain `Gmpq` | **Maintainer accepted it as a defect and never investigated.** `sloriot` (MEMBER): "you're right that there shouldn't be an assertion. I'll investigate when I find time"; `lrineau` (MEMBER): "unless you come up with a fix really soon, I will delay it" | **open since 2018-02** | [issue](https://github.com/CGAL/cgal/issues/2781) |
| 9497 | consecutive difference operations leave ~1e-14 gaps on axis-aligned CAD input | **Maintainer.** `sloriot` (MEMBER): "you create a non-manifold connection between two red volumes"; of the offered workaround, "you will end up with something that is a polygon soup" | **open** 2026-05 | [issue](https://github.com/CGAL/cgal/issues/9497) |
| 9360 | union reported self-intersecting; a further assertion in `isotropic_remeshing` | **Split: input-side for the first, a confirmed CGAL bug for the second.** `sloriot` (MEMBER) traced the self-intersections to low-precision OFF output, then confirmed "There is actually a bug in `isotropic_remeshing()`" which he could not minimise. Reported by `dpapavas` (CONTRIBUTOR) | **open** 2026-03 | [issue](https://github.com/CGAL/cgal/issues/9360) |
| 5900 | Nef union then corefinement union; degenerate facets, unclosed result | **Maintainer, input-side.** `sloriot` (MEMBER) on the Nef path: it "is performed using a number type with arbitrary precision", and the degeneracies come from "a rounding to double" at file-write time. The reporter (NONE) adds a comparison: corefinement was "noticeably quicker" than Nef but "does not produce a closed mesh" on his input | **open** 2021-08 | [issue](https://github.com/CGAL/cgal/issues/5900) |

### What the survey shows, and one thing it does not

1. **Almost every corefinement failure is traced to the input, and traced by one person.**
   Self-intersections (7071, 5264, 9154), non-closed or wrongly-oriented meshes (9467, 9497),
   untriangulated faces (9282), low-precision file I/O (9360, 5900). `sloriot` (MEMBER) answers
   nearly all of them. That is a maintenance risk (bus factor at package level) and an
   endorsement of the algorithm at the same time: in twenty-two tickets, only **two** are
   maintainer-confirmed defects in the boolean itself (4522, fixed in two days; 9486, fixed by
   PR 9506) and one in a neighbouring PMP function (9360, open).
2. **The manual and the tracker give different advice about Epeck, and both are right.** The
   *manual* recommends it, narrowly: with an inexact-constructions kernel "the embedding of the
   output surface mesh might have self-intersections", and "In case of consecutive operations" it
   advises Epeck
   ([`Polygon_mesh_processing.txt#L423-L433`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/doc/Polygon_mesh_processing/Polygon_mesh_processing.txt#L423-L433) —
   *claimed*). In the twenty-two tickets read here, **no maintainer tells a reporter to make that
   switch**; the advice runs the other way — `afabri` (MEMBER) on 9282, "I don't see the need for
   switching kernels. Just triangulate faces", and on 8074 `sloriot` (MEMBER) suggests moving
   *away* from Epeck. #9139 looks like a counter-example and is not: the kernel change there is
   from `Simple_cartesian<double>` (no filter at all) to a filtered one — inexact predicates to
   exact predicates, a different axis. The two are consistent because §The hybrid explains both:
   corefinement is already exact internally, so the user-facing kernel changes nothing about *one*
   operation, and matters only when the rounded output of one operation becomes the input of the
   next. Our set runs one boolean per case, so it cannot see the case the manual is warning
   about.
3. **Exact arithmetic does not buy determinism.** #6363 reports the same **Epeck** boolean
   producing different output at `-O0` and `-O2`, and the maintainer's only comment is a
   suspicion about hash-map ordering. Our own Probe E measures the same class independently
   (§What we measured ourselves).
4. **Nef's tickets are older, sparser and less answered than corefinement's.** #2781 has been open
   since 2018 with a maintainer's acknowledgement and no fix; #5490 and #7271 are open with
   won't-fix answers; the one performance improvement (#5379) was written by an outside
   contributor. Corefinement is where the maintenance is.

The absence: **no ticket in this survey reports a wrong *volume* from an accepted input.** As with
Manifold, the failures are of contract (refusal), of precondition, of output quality after
rounding, or of ordering — not of arithmetic. That is consistent with everything we measured.

### What we measured ourselves

Three findings. The first is a documented limitation reproduced exactly; the other two are not in
the tracker in this form.

**1. A refusal that is per-operation and reasoned — and the manual names our case.** `shared_edge`
— two unit cubes touching along the line x=1, y=1 — has its **union refused**
(`corefine_and_compute_union` returns `False`, empty output) while the **intersection of the same
pair succeeds** and correctly returns empty (measured,
[`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md) main table and Probe D).

That the reference set walked straight into a case CGAL documents by name is worth recording:
the PMP manual states that "the operation is possible only if the output can be bounded by a
manifold triangulated surface mesh" and gives as its example that it is "not possible to compute
the union of two cubes that are disjoint but sharing an edge", pointing such cases at the `Nef_3`
package instead
([`Polygon_mesh_processing.txt#L403-L411`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/doc/Polygon_mesh_processing/Polygon_mesh_processing.txt#L403-L411) —
*claimed*, and *measured* here). The same page also states what Probe F measures: "In case the
Boolean operation is not possible, the input mesh will nevertheless be corefined"
([`#L415-L416`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/doc/Polygon_mesh_processing/Polygon_mesh_processing.txt#L415-L416)).

The mechanism is not an error path; it is a `std::bitset<4>` with one bit per operation
([`Face_graph_output_builder.h#L544-L548`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L544-L548)),
set with a reason at the point the non-manifold configuration is recognised —
`impossible_operation.set(UNION); // tm1 U tm2 is non-manifold`
([`#L1750`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L1740-L1751);
the intersection has its own bit at
[`#L1680`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L1664-L1681))
— and read back as four separate booleans
([`#L787-L802`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L787-L802)).
The cause is the representation, not the arithmetic: the union's boundary would have four facets
meeting along one edge, and a halfedge mesh cannot hold that. The contrast within our own set is
what makes it useful — `touching_vertex`'s union **succeeds**, returning 16 vertices in **two**
components (measured, Probe D), because a point contact *can* be represented by duplicating the
vertex. A maintainer describes the identical limitation on
[#9467](https://github.com/CGAL/cgal/issues/9467): the result "is not representable as
2-manifold".

**Compare the siblings, on the two cases separately.** On `touching_vertex`, Blender's exact
solver returned a valid closed union of **one** cube, silently losing an operand
([`blender.md`](blender.md) §Known problems); Manifold returned 2 / 0 correctly
([`results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md)); CGAL returned 2 in
two components, also correctly. On the *refusal contract*, the three refuse different things:
Manifold refuses non-manifold **input** at ingest, with a typed status on an empty result; Blender
refuses by printing a warning and handing back the first operand; CGAL accepts the input and
refuses **the one output that cannot be represented**, leaving the other three operations
available. Of the three, CGAL's is the contract kernel spec §12 should copy — with the
correction that its refusal must not also consume the operands (finding 2).

**2. A failed boolean leaves an operand modified.** Corefinement mutates both operands in place,
which the documentation states — "If `false` is returned and if `tm_out` is one of the input
surface meshes, then `tm_out` is only corefined"
([`corefinement.h#L597-L599`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L597-L599)) —
and which Probe F measures case by case: the twelve-opening wall's A goes 8v/12f → **224v/444f**
and its B 96v/144f → **312v/576f**. The finding is the row where the boolean *failed*:
`near_degenerate_triangle` returns `False` **and still leaves operand A at 9v/14f instead of
8v/12f**. A caller who retries, or who reuses the operand elsewhere, is no longer working with the
mesh it passed in. This is the concrete form of the rule `blender.md` first drew — a refusal must
be a distinguishable return value — extended: *a refusal must also leave the inputs alone*.

**3. The geometry is deterministic; the emission order is not, on every single run.** Ten runs of
each of four case/operation pairs, operands rebuilt each time. The number of distinct
`(verts, tris, volume)` signatures is between one and four depending on the pair (1, 2, 4 and 3 on
the committed run) — but the number of distinct **sorted** vertex-coordinate multisets is **1 in
all four**, and the number of distinct **emission orders** is **10 out of 10 in all four**
(measured, Probe E). The solid is identical every time; CGAL hands it back in a different vertex
order every time, and `reference.signed_volume`, summing in that order, then differs in its last
bits — on the committed run, 12.600000000000003 seven times and 12.6 three times for the same
twelve-opening wall. This is a
milder defect than Blender's — where ten runs produced two genuinely **different topologies** at
equal volume ([`blender.md`](blender.md) §Known problems) — and a real one all the same: **an
output that cannot be hashed reproducibly cannot be cached, diffed or regression-tested**, and any
order-dependent reduction over it is not reproducible either. It is also, independently, the class
`sloriot` (MEMBER) suspected in [#6363](https://github.com/CGAL/cgal/issues/6363) and never
investigated. We did not trace the cause and do not claim one.

Two smaller findings from the same run. **`PMP::stitch_borders` does not repair the T-junction**:
operand B stays 9v/13f, not closed, still self-intersecting (Probe C) — the same negative result
Manifold's `Merge` gave, and for the same reason, since neither welds a vertex to the interior of
an edge. And **`does_bound_a_volume` is not in the binding's surface at all**, though it is one of
the four documented preconditions
([`corefinement.h#L516-L519`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L516-L519)),
so a Python caller cannot check the precondition the library asks of them — and
[#9486](https://github.com/CGAL/cgal/issues/9486) shows that even in C++ that function and its
neighbour `does_self_intersect` disagreed with each other until PR 9506.

## Measurements

- **Hardware:** Intel Core i9-14900HX, 32 GB RAM, Windows 11 Pro.
- **Versions:** `cgal` 6.0.1.post202410241521 (the official CGAL SWIG bindings from PyPI;
  `CGAL_VERSION_NR` 1060010900, `CGAL_RELEASE_DATE` 20241024); source read at tag `v6.0.1`,
  commit `50cfbde3b84dbeae8338268db2d78fe4fcb522de`. Python 3.12.10. No numpy: the drivers are
  standard library plus the binding.
- **Benchmark:** `reference/boolean_torture_set.py` and `reference/precision_set.py`, verbatim.
- **Method:** operands built by `PMP::polygon_soup_to_polygon_mesh` from the reference meshes with
  no welding, no `orient_polygon_soup` and no repair; preconditions recorded per operand
  (`is_closed`, `is_pure_triangle`, `does_self_intersect`, `is_outward_oriented`; the fourth
  documented precondition `does_bound_a_volume` is absent from the binding and is recorded as
  such). Validity is the driver's own check on the *exported* triangles — closed, every directed
  edge used once with a matching opposite halfedge, no loose vertices, no triangle below 1e-14 m²
  — the same check the Manifold and Blender drivers apply, plus `Polyhedron_3::is_closed()` and
  the boolean's own `bool` return. Volumes by `reference.signed_volume` over those triangles, with
  `PMP::volume()` recorded beside them and reported in the row when the two disagree by more than
  1e-12 relative. Timing `time.perf_counter`, five repeats, median; **both operands are rebuilt
  inside every repeat**, because corefinement modifies them in place.
- **Reproducibility caveat, and it is a finding rather than a nuisance:** because CGAL emits the
  result's vertices in a different order on every run (§What we measured ourselves, Probe E) and
  `reference.signed_volume` sums in emission order, the **last two or three digits** of any volume
  in these files move between runs, and so does a residual that is already at the 1e-15 level.
  A re-run that reports 12.600000000000003 where the committed file says 12.6, or 0 where it says
  7.11e-15, has reproduced the measurement. Nothing above the 1e-12 level moves.
- **Two settings, and why there are only two:** CGAL exposes no tolerance parameter, so there is
  no equivalent of Manifold's tolerance sweep. The axis that exists is the ingest precision —
  `Epick, f64 input` (verbatim) and `Epick, f32-rounded input` (each coordinate through the
  nearest float32 and back, still stored as a `double`). Both run the same exact predicates.

### Boolean torture set (R-16)

| Setting | Valid (closed manifold) | Numerically correct | Worst identity residual |
|---|---|---|---|
| Epick, f64 input | 8 / 10 | 8 / 10 | 7.11e-15 |
| Epick, f32-rounded input | 8 / 10 | 8 / 10 | 0 |

*(Figures re-synced to the 2026-09-11 run recorded in
[`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) — the
`wall_with_openings` f64 identity residual moved between runs, inside the file's own documented
non-determinism, from 3.55e-15 to 7.11e-15; see that file's §Run-to-run reproduction.)*

R-16's pass line is *every* case valid with the identity within 1e-9 relative. **CGAL does not
pass, and both failures are refusals rather than wrong answers** — one at a documented
precondition (`near_degenerate_triangle`, the T-junction operand: not closed, self-intersecting),
one because the requested operation's result is not representable in a halfedge mesh
(`shared_edge`'s union). On the eight it accepts it is numerically correct on both settings, and
the worst identity residual on f64 input, **7.11e-15**, is the tightest of the four candidates
measured. Compared like for like — the worst residual each candidate produced over the cases *it*
accepted — Blender's Manifold solver is 1.42e-14, the standalone Manifold library 3.55e-14, OCCT
3.33e-08 (driven by its `sliver` intersection returning 0 where 1e-07 m³ was expected; 1.42e-14
without that case), and Blender's exact solver 1 (driven by its silently deleting an operand on
`touching_vertex`).

Three details worth carrying:

* **The twelve-shell cutting tool is a non-issue.** One mesh of twelve disconnected closed shells
  is accepted as one `Polyhedron_3`; `PMP::connected_components` reports 12; union, intersection
  and difference are all exact, the difference landing at **3.6 m³** against the analytic 3.6
  (Probe A). The intersection correctly comes back as **12 components**.
* **The 1e-7 m slab survives everything.** With no tolerance to raise there is nothing to delete
  it: the slab arrives 9.99999999474e-08 m thick on the f64 setting and the intersection comes
  back at 9.99999999612e-08 m³ (Probe B). Compare Manifold, where raising the tolerance to 1e-6
  silently removed the same operand and reported `NoError`. **No tolerance means no silent
  simplification** — which is a strength here and the same property that makes CGAL refuse
  near-coincident input elsewhere (#5264).
* **The f32-rounded setting changes nothing about *which* cases pass.** Same 8/10, same
  refusals; only the volumes move (Δ∪ = 1.79e-08 on the wall). Its worst identity residual reads
  0 rather than 7.11e-15, which is not an improvement — both are below the noise floor the
  reproducibility caveat above describes. Exact predicates keep the *combinatorics* right on
  rounded coordinates; they cannot keep the *geometry* right.

### Precision set (R-17) — passes on f64, fails on f32-rounded

Worst vertex deviation over the whole set: **1.29e-10 m on f64 input**, **0.0348 m on
f32-rounded input**. R-17's pass line is 1e-6 m and its fail line 1e-4 m.

A probe was added to make sure the back-translation is not doing the work: the same pair of
results compared in the other direction (moving the origin result *out* to the far frame instead
of bringing the far result home) gives 1.16e-10 m against the main table's 1.29e-10 m on f64, and
0.034821 m against 0.034821 m on f32-rounded — agreement at the level of one f64 addition at
5e5 m, as it should be (measured, [`precision results`](../../../spikes/precision-set/results/cgal.md)).

### A note on measuring volume at 500 km, confirming `manifold.md`

[`manifold.md`](manifold.md) §A warning about measuring volume at 500 km found that
`reference.signed_volume` loses volume to cancellation at 500 km with no library involved, and
mitigated it by integrating on back-translated vertices. This driver does the same and measures
the artefact again on CGAL's own output: on the wall union, the origin result's own vertices
re-integrated with the offset added give **12.5997471293** against **12.6** — a loss of
**2.53e-04 m³** to pure summation. (The figure differs from `manifold.md`'s 7.9e-05 m³ because
the two results are triangulated differently — 320v/636f here against 200v/396f there — so it is
a different sum, not a different conclusion.)

**CGAL's own integrator does not avoid it either**, which is the addition this note makes:
`PMP::volume()` on the far wall union returns **12.6002807614**, *worse* than the naive raw sum's
12.5995943646, because it is an uncompensated sum of tetrahedron volumes about the world origin.
Manifold's `Volume()` differences against a vertex first and applies Kahan compensation and
returns 12.5999999999 on the same solid. **So the design point in `manifold.md`'s borrow-from
table now has a counter-example as well as an example**: one library's mass-property integrator
is conditioned for national-grid coordinates and the other's is not. OCCT's `BRepGProp` was not
put through this probe, so it is not counted on either side.

## Strengths

- **The tightest arithmetic of any candidate on the cases it accepts.** Worst identity residual
  7.11e-15 on f64 input (2026-09-11 run;
  [`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md)) — roughly
  two times tighter than the next best (Blender's Manifold solver at 1.42e-14) — and correct to
  the 1e-6 criterion on both settings.
- **Exact predicates that demonstrably decide what doubles cannot** — 2164 of 4096 plain-double
  answers wrong, 0 of 4096 for the filtered predicate, against an exact-rational oracle.
- **A refusal that is per-operation and carries a reason.** Four independent bits, one per boolean
  operation, set at the point the non-representable configuration is recognised.
- **No tolerance, therefore no silent simplification.** Nothing in CGAL can delete a 1e-7 m
  feature because a global epsilon grew.
- **A far-field result that is not the differentiator, which is the point** (1.29e-10 m on f64, against Manifold's 3.3e-11 m and OCCT's 2.65e-10 m on the same case). All three pass R-17 by four orders of magnitude; only the storage type separates pass from fail.
- **The hybrid itself**: exact constructions held for one operation and rounded at its boundary is
  a shipped, production design for the thing kernel spec §5 proposes, and its cost is measured.
- **Preconditions are documented as preconditions**, with a named diagnostic
  (`throw_on_self_intersection` + `Corefinement::Self_intersection_exception`), rather than being
  implicit.

## Weaknesses

- **The boolean, the mesh class it runs on, and `Nef_3` are all GPL.** The design may be borrowed;
  the code may not, for a product that is not GPL. Only the kernel, the filtering and the number
  types are LGPL.
- **It is not a kernel, it is a library of packages.** No model, no handles, no incremental
  evaluation, no operation history, and each package with its own maintainer and licence.
- **The boolean destroys its operands**, and does so *even when it fails*.
- **Emission order is non-deterministic on every run**, so the output cannot be hashed
  reproducibly.
- **Preconditions are the caller's problem, and the binding cannot check one of them.**
  `does_bound_a_volume` is absent from the Python surface; violating a precondition is undefined
  behaviour, and #9486 shows the C++ checkers disagreeing with each other.
- **Near-coincidence is not coincidence.** With no tolerance model, input that is *nearly* clean
  is refused rather than healed, and the healing functions a maintainer points at are, in his own
  words on #5264, "not documented".
- **Rounding at the boundary is a real seam**: a maintainer states that corefinement can produce
  self-intersecting output from self-intersection-free input because the exact points are rounded
  to double (#9154).
- **Bus factor at package level.** Twenty-two tickets; one person answers almost all of them.
- **Embedding cost.** Template-heavy C++, GMP/MPFR for Epeck, Boost for PMP, no C ABI.
- **No GPU path, threading unmeasured / inferred (the corefinement API measured here takes no
  concurrency tag), no cancellation or progress API** — the same P-15 gap OCCT has.

## Risks

- **The unmeasured half is the half ADR-0006 cites.** If the ADR is to keep Option B's rejection
  as written, someone must measure `Nef_polyhedron_3` — or the option must be re-described as what
  CGAL actually does. **The specific experiment:** build CGAL with GMP/MPFR, convert
  `reference/models/AC20-FZK-Haus.ifc`'s solids to `Nef_polyhedron_3` under Epeck, and record
  construction time, boolean time and peak RSS against the same solids through PMP corefinement.
  Until then this note supports the *mechanism* of P-03 and not its magnitude.
- **The Epick path's residual defect class is invisible until it bites.** The output rounds; on
  chained operations the rounded output becomes the next operation's input, and #6481 and #9497
  are two reports of exactly that compounding. Our set runs one boolean per case and cannot see
  it. **A second experiment:** run the twelve openings as twelve chained differences instead of
  one twelve-shell operand and check whether the result stays valid.
- **Adopting the hybrid means owning the seam.** If our kernel computes exactly and stores f64,
  it inherits CGAL's failure mode — a result that is exactly computed and then rounded into
  self-intersection — and needs an answer to it that CGAL does not have.

## The twelve questions

1. **Re-evaluate one changed element without reprocessing the model?** No, and worse than most:
   the boolean consumes its operands, so even re-running the *same* operation needs both rebuilt.
   *(measured, Probe F.)*
2. **IFC round trip?** Not applicable; no schema layer. CGAL reaches IFC only through
   IfcOpenShell's CGAL kernel option, evaluated separately.
3. **Driven in-process from DynLex?** Not easily. A template-heavy header C++ API with no C ABI;
   Epeck pulls in GMP/MPFR and PMP pulls in Boost. The SWIG wheel is a 25 MB binary. The weakest
   embeddability of any candidate measured. *(inferred.)*
4. **Threading model, and what is single-threaded by design?** **Unmeasured.** CGAL has TBB
   parallelism in other packages behind `CGAL::Parallel_tag`; the corefinement API measured here
   takes no such tag. This note claims no speedup. *(inferred.)*
5. **What breaks first at scale?** **Unmeasured by us**, and the tracker points at two different
   answers for the two paths. For corefinement it is *chained* operations: #6481's machining
   simulation fails at step 3 of 5000 with the compounding `afabri` (MEMBER) describes. For Nef
   it is memory and construction time: #8074, #5379, #7271. *(tracker.)*
6. **Numeric precision, configurable?** Yes, and this is CGAL's defining feature: the kernel is a
   template parameter, and Epick (`double` storage, exact predicates) and Epeck (exact rational
   storage through a lazy DAG) are the two supplied choices. The binding measured here offers only
   Epick. *(source + measured.)*
7. **Operate on a subset — one tile, one region?** Yes in the trivial sense that a free function
   over two meshes has no notion of a model at all, so the caller decides what to pass. There is
   no region concept to help with it either. *(inferred.)*
8. **Who maintains it, what if they stop?** A consortium of research institutions plus
   GeometryFactory commercially, for ~30 years. Institutionally the safest of the candidates; at
   *package* level the boolean has an alarming bus factor of about one. *(source + tracker.)*
9. **Documented failure modes and their design cause?** §Known problems: twenty-two tickets, with
   the dominant class being precondition violations the caller must detect, tracing to a design
   that states preconditions rather than checking them; plus one inherent class — output rounded
   from exact constructions into self-intersection (#9154). *(tracker + source.)*
10. **Representations held natively, and conversions?** Several, in separate packages with no
    common object: halfedge B-rep, Nef point set, point sets, 3D triangulations. Conversions are
    package-level free functions. *(source.)*
11. **How does geometry reach the GPU?** It does not. *(source.)*
12. **What would we take, and what avoid?** §Verdict.

## Verdict

### Build on — **no**

Not as the kernel, and not as the boolean.

Not as the kernel because CGAL is not one: it is 146 packages with their own maintainers and two
licences, no model, no handles, no evaluation graph and no incremental anything. Kernel spec
§3–§4 describes an object CGAL deliberately does not provide.

Not as the boolean, for a reason that is decisive and not a matter of quality: **`corefinement.h`
is GPL-3.0-or-later**, and R-11 rules out a GPL kernel. That would remain true even if every
other column were the best in the matrix — and several of them are. Linking Epick as an LGPL
library for its predicates is a *different* question and is not closed here; it is a live option
against writing Shewchuk's predicates ourselves (spec §7), and the trade is licence obligation and
build weight against maintenance.

### Borrow from — the exact-predicate design, in detail, because ADR-0006 rests on it

| What | Why | Where |
|---|---|---|
| **Exact predicates with a floating filter, as the default and not an option** | The measured case: 2164 of 4096 plain-double orientation answers wrong against an exact oracle, 0 of 4096 for the filtered predicate. This is ADR-0006's premise, shown rather than asserted | Probe H in [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md); design in [`Epick header#L54-L63`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L54-L63). **P-01, P-03** |
| **Static filters on by default, disabled only by an explicit macro** | `epick_use_static_filter` is `true` unless `CGAL_NO_STATIC_FILTERS` is defined. The cheap filter is not an optimisation the caller opts into; the *absence* of it is what you opt into | [`Epick header#L29-L34`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L29-L34) |
| **The Epick/Epeck distinction as a *type-level* choice, not a runtime flag** | Two kernels differing in the number type and nothing else, each declared in a handful of lines, both selectable per algorithm. Our kernel needs the same seam: one predicate implementation, two arithmetic backings, chosen where the cost is worth it | [`Epick`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_inexact_constructions_kernel.h#L54-L70) and [`Epeck`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Kernel_23/include/CGAL/Exact_predicates_exact_constructions_kernel.h#L56-L76) headers. **P-03** |
| **Exactness as a *phase*, not a storage class: compute intersections exactly, keep them exact for the operation so predicates on constructed points stay exact, round at the boundary** | This is the single most important thing in the note. It is what CGAL's shipped boolean does, and it is what kernel spec §5 currently under-specifies. Its price on our hardest case is 8.21 ms | [`intersection_nodes.h#L142-L173`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L142-L173), [`#L192-L196`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_nodes.h#L192-L196); [`Visitor.h#L453-L456`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Visitor.h#L453-L456). **P-03** |
| **A per-operation refusal with a reason, not a per-call error** | `std::bitset<4>`, one bit per boolean operation, set where the non-representable configuration is found. `A ∪ B` can be impossible while `A ∩ B` is fine — measured on `shared_edge` | [`Face_graph_output_builder.h#L544-L548`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L544-L548), [`#L787-L802`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/Face_graph_output_builder.h#L787-L802). **P-01, P-09** |
| **Preconditions stated as preconditions, with a named opt-in check and a typed exception** | `\pre !does_self_intersect(tm)`, `\pre does_bound_a_volume(tm)`, plus `throw_on_self_intersection` raising `Corefinement::Self_intersection_exception`. Our kernel should copy the shape and go two steps further: check by default, and make the check *the same check* the precondition names — CGAL's opt-in check is narrower than its precondition, covering only "the set of triangles close to the intersection" | [`corefinement.h#L516-L519`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L516-L519), [`#L566-L573`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L566-L573); the exception at [`intersection_callbacks.h#L31-L37`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/internal/Corefinement/intersection_callbacks.h#L31-L37). **P-09** |
| **The filter's structure, verbatim: interval → certain? → return; otherwise exact** | Twenty lines that contain the entire idea, with the FPU rounding mode protected around the interval block rather than set globally, and the exact path as the fallback. It is LGPL, so this one may be read *and* linked | [`Filtered_predicate.h#L87-L110`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Filtered_kernel/include/CGAL/Filtered_predicate.h#L87-L110). **P-01** |
| **No global tolerance at all** | With nothing to raise, nothing can be silently simplified away: the 1e-7 m slab survives every setting. The contrast with Manifold's tolerance-triggered deletion and OCCT's tolerance growth is total | Probe B in [`results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md). **P-02** |

### Avoid — each one mapped to the design choice behind it

| Failure | Design choice it traces to | Our design's answer |
|---|---|---|
| **The boolean consumes its operands, and does so even when it returns `False`.** Measured: the wall's A goes 8v/12f → 224v/444f; `near_degenerate_triangle` fails *and* leaves A at 9v/14f | Corefinement is defined as an in-place operation on both meshes, with extraction as a second step; the failure path returns after the corefinement has already happened ([`corefinement.h#L597-L599`](https://github.com/CGAL/cgal/blob/50cfbde3b84dbeae8338268db2d78fe4fcb522de/Polygon_mesh_processing/include/CGAL/Polygon_mesh_processing/corefinement.h#L597-L599)) | Operations return a new result value and never mutate their inputs; a failed operation leaves the model bit-identical (spec §4, §12). **P-01**, measured (Probe F) |
| **Emission order differs on every run** — 10 distinct vertex orders in 10 runs, on identical geometry | No canonical output ordering; the maintainer's own suspicion on [#6363](https://github.com/CGAL/cgal/issues/6363) is hash-map iteration order. Exact arithmetic does not fix this, because it is not an arithmetic problem | Determinism is an invariant with a test in the suite from the first boolean, and it covers the *serialisation order*, not only the geometry — otherwise a result cannot be hashed, cached or diffed (spec §6). **P-16**, measured (Probe E) |
| **Exactly computed, then rounded into self-intersection.** A maintainer states corefinement can turn self-intersection-free input into self-intersecting output because "the exact intersection points are rounded to double" (#9154) | Exact constructions are discarded at the operation boundary, so the invariant they guaranteed does not survive into the stored result | The rounding step is part of the operation's contract: a result that had to be rounded says so, and validity is re-established (or reported as lost) before the result is returned (spec §12). **P-01, P-02**, tracker-verified |
| **Near-coincident input is refused, not healed, and the repair functions are undocumented** — `sloriot` (MEMBER) on [#5264](https://github.com/CGAL/cgal/issues/5264): "There are several functions in CGAL to fix your input but they are not documented" | No tolerance model at all, which removes silent simplification and removes tolerant matching with it | Validity is an explicit query and healing an explicit, *documented* operation with its own parameters and failure modes (spec §4, §12). **P-09** |
| **A documented precondition that a caller cannot check.** `does_bound_a_volume` is absent from the Python binding; and [#9486](https://github.com/CGAL/cgal/issues/9486) shows it and `does_self_intersect` disagreeing until PR 9506 | Preconditions are a documentation contract enforced nowhere, with checking left to separate functions that are themselves not covered by the same tests | Every precondition an operation states is a callable query on the same object, tested against the operation that requires it (spec §12). **P-01** |
| **No cancellation, no progress, no memory or time budget** on an operation whose cost the tracker shows can be unbounded (#6481, #8074) | The operation owns the whole computation, as in OCCT | Unchanged from [`manifold.md`](manifold.md)'s answer: a permanent cancel flag on a context object, a typed cancelled result, polled at phase boundaries. **P-15** — CGAL is a second candidate lacking it, against Manifold's counter-example |
| **`PMP::volume()` is an uncompensated sum about the world origin** — 12.6002807614 on the far wall, worse than the naive `signed_volume`'s 12.5995943646 | The integrand is written for correctness at unit scale, not for conditioning at national-grid coordinates | Mass properties use the differenced-and-compensated form (spec §5). **P-05** — restating [`manifold.md`](manifold.md)'s borrow-from item, now with a counter-example as well as an example |

### Corrections and additions this note makes to `problems.md` and to ADR-0006

- **P-03 → partly shown, and re-scoped.** The mechanism of the Nef cost is shown in source (a
  vertex *is* a sphere map; seven allocated item lists; an Epeck lazy DAG) and attested by
  maintainers and by third-party timings, but **we measured none of it** and this note's
  §Measurements cannot be cited for it. In exchange the row gains a *fourth* position on the
  exactness/speed trade, measured: exact constructions held for one operation and rounded at its
  boundary, at 8.21 ms on the twelve-opening wall.
- **ADR-0006's evidence row "Exact rational everywhere is too slow" cannot cite
  `kernels/cgal.md` §Measurements.** It should cite this note's §What P-03 asks — labelled
  *inferred + claimed* — or the ADR should rewrite Option B, since CGAL's own production boolean
  is neither of the two options the ADR names.
- **ADR-0006's evidence row "Floating-point topology decisions cause invalid booleans" gains a
  direct measurement** it did not have: Probe H, 2164 of 4096 plain-double answers wrong, 0 of
  4096 for the exact predicate, against an exact-rational oracle.
- **P-14 gains its first hard evidence.** The licence question is not per-project but per
  *package*, and CGAL's split falls exactly across the boundary: the kernel we would want to link
  is LGPL, the boolean we would have wanted to read is GPL.
- **P-16 gains a third form.** Blender's non-determinism changed the topology; Manifold's was
  fixed ticket by ticket; CGAL's changes only the *emission order* — the geometry is identical on
  all ten runs — which is milder and still fatal for hashing, caching and diffing. Determinism
  must be an invariant on the serialised output, not only on the solid.
- **P-05 gains a counter-example.** Two of three measured kernels compute far-field volume with an
  uncompensated sum about the world origin; only Manifold does not.
- **P-09 gains its best positive example.** CGAL refuses the *operation* that cannot be
  represented and only that one, with the reason recorded per operation.

## Sources

- [CGAL](https://github.com/CGAL/cgal), source read at tag `v6.0.1`, commit
  `50cfbde3b84dbeae8338268db2d78fe4fcb522de`; package `cgal` 6.0.1.post202410241521 from PyPI
  (the official CGAL SWIG bindings), whose `CGAL_VERSION_NR` is `1060010900`.
- Licences, read as SPDX identifiers at that commit: `LGPL-3.0-or-later OR LicenseRef-Commercial`
  for `Kernel_23`'s Epick and Epeck headers; `GPL-3.0-or-later OR LicenseRef-Commercial` for
  `Polygon_mesh_processing`'s `corefinement.h` and `intersection_nodes.h`, and for `Nef_3`'s
  `Nef_polyhedron_3.h` and `SNC_structure.h`. See §Licence for the per-file links.
- Issue tracker, twenty-two tickets cited:
  [#2781](https://github.com/CGAL/cgal/issues/2781),
  [#4522](https://github.com/CGAL/cgal/issues/4522),
  [#5119](https://github.com/CGAL/cgal/issues/5119),
  [#5264](https://github.com/CGAL/cgal/issues/5264),
  [#5379](https://github.com/CGAL/cgal/issues/5379),
  [#5490](https://github.com/CGAL/cgal/issues/5490),
  [#5900](https://github.com/CGAL/cgal/issues/5900),
  [#6363](https://github.com/CGAL/cgal/issues/6363),
  [#6481](https://github.com/CGAL/cgal/issues/6481),
  [#6738](https://github.com/CGAL/cgal/issues/6738),
  [#7071](https://github.com/CGAL/cgal/issues/7071),
  [#7271](https://github.com/CGAL/cgal/issues/7271),
  [#8074](https://github.com/CGAL/cgal/issues/8074),
  [#8395](https://github.com/CGAL/cgal/issues/8395),
  [#9139](https://github.com/CGAL/cgal/issues/9139),
  [#9154](https://github.com/CGAL/cgal/issues/9154),
  [#9282](https://github.com/CGAL/cgal/issues/9282),
  [#9360](https://github.com/CGAL/cgal/issues/9360),
  [#9455](https://github.com/CGAL/cgal/issues/9455),
  [#9467](https://github.com/CGAL/cgal/issues/9467),
  [#9486](https://github.com/CGAL/cgal/issues/9486),
  [#9497](https://github.com/CGAL/cgal/issues/9497).
  Speaker roles are the `author_association` values the GitHub REST API returns for the
  individual issue or comment (`gh api repos/CGAL/cgal/issues/<n>` and `.../comments`); `gh issue
  view --json` does not expose that field.
- Olivier Devillers and Sylvain Pion, *Efficient Exact Geometric Predicates for Delaunay
  Triangulations*, ALENEX 2003 — the semi-static and dynamic filtering scheme CGAL's filtered
  predicates implement. INRIA research report RR-4351,
  [https://inria.hal.science/inria-00072237](https://inria.hal.science/inria-00072237).
  *Claimed*: cited for the design and for the cost of filtering, which this note does not measure.
- Peter Hachenberger, Lutz Kettner and Kurt Mehlhorn, *Boolean Operations on 3D Selective Nef
  Complexes: Data Structure, Algorithms, Optimized Implementation and Experiments*, Computational
  Geometry: Theory and Applications 38(1–2), 2007,
  [https://doi.org/10.1016/j.comgeo.2006.11.009](https://doi.org/10.1016/j.comgeo.2006.11.009).
  *Claimed*: the design behind `Nef_3`'s sphere-map-per-vertex structure, which §What P-03 asks
  reads in source but does not run.
- Our measurements:
  [`spikes/boolean-torture/results/cgal.md`](../../../spikes/boolean-torture/results/cgal.md),
  [`spikes/precision-set/results/cgal.md`](../../../spikes/precision-set/results/cgal.md).
- Comparison numbers for the same benchmark:
  [`spikes/boolean-torture/results/blender.md`](../../../spikes/boolean-torture/results/blender.md),
  [`spikes/boolean-torture/results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md),
  [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md),
  [`spikes/precision-set/results/blender.md`](../../../spikes/precision-set/results/blender.md),
  [`spikes/precision-set/results/manifold.md`](../../../spikes/precision-set/results/manifold.md),
  [`spikes/precision-set/results/occt.md`](../../../spikes/precision-set/results/occt.md).
