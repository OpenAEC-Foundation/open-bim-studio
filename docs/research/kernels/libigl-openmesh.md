# libigl and OpenMesh — design reference for the mesh arrangement and the half-edge layout

**Decision question:** Our kernel spec proposes a half-edge mesh with structure-of-arrays
attributes (spec §4, §6) and an exact-arrangement mesh boolean (spec §4). libigl ships the
research lineage of that boolean and OpenMesh is a twenty-year-old reference half-edge kernel.
Neither is a candidate to build on — both are libraries, not kernels — so the only question this
note answers is: **what, specifically, should our design borrow from each, with a citation, and
what should it avoid?**

**Serves:** ADR-0005 (evidence row "Exact arrangement is the robust mesh boolean" cites this file
directly); kernel spec §4 (mesh representation, exact arrangement for booleans), §6
(structure-of-arrays, generational handles); `problems.md` P-01, P-09

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

> This is a **design-reference note**, not a candidate evaluation. Neither library is scored for
> *build on* — both are answered "no, library scope" up front — and no benchmark or torture-set
> measurement was run against either. The verdict axis in scope is *borrow from*, with a short
> *avoid* list. Where a README criterion does not apply to a library rather than a kernel, the row
> says so rather than being scored.

---

## Summary

libigl's `copyleft::cgal::mesh_boolean` is a working implementation of the algorithm our kernel
spec's mesh boolean is modelled on — the same lineage [`blender.md`](blender.md) §Exact boolean
traces for Blender's Exact solver — and reading its source is more precise than reading the paper
alone: the whole pipeline runs in CGAL's `Epeck` exact-constructions kernel end to end, not only
in its predicates, and its "valid" return value is an honest, checked-but-ignorable signal that
the input was not piecewise-constant-winding-number (PWN) — a signal the library's own tutorial
discards. OpenMesh is the second reference: a half-edge connectivity of four four-byte handles per
halfedge, a vertex and a face that store one handle each, and a property system that is already
the parallel-arrays-keyed-by-index pattern spec §6 wants — undercut by handles that are plain
`int` indices with no generation, renumbered on every garbage collection. Both licences are
mixed: libigl's own files are MPL2, but the boolean pipeline pulls in `CGAL::Polyhedron_3`, which
[`problems.md`](problems.md) P-14 already establishes as GPL-3.0-or-later; OpenMesh is BSD-3-Clause
outright.

## What was read, and at which commit

| Library | Pinned at | Commit | Obtained with |
|---|---|---|---|
| libigl | tag `v2.6.3` | [`f68f01c23ac82351e2543ce8c529b6d4c89fdf16`](https://github.com/libigl/libigl/tree/f68f01c23ac82351e2543ce8c529b6d4c89fdf16) | `git clone --depth 1 --branch v2.6.3 https://github.com/libigl/libigl.git`, confirmed with `git rev-parse HEAD` |
| OpenMesh | tag `OpenMesh-9.0` | [`adebfb1ec0c14a43f5503a2dfea3d76599eb28ab`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/tree/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab) | `git clone --depth 1 --branch OpenMesh-9.0 https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh.git`. Git reports the tag ref itself (`b0b1620f…`) is an annotated tag object, not a commit; the clone resolves it to the commit above, confirmed with `git rev-parse HEAD` |

Both tags were selected as the most recent from `git ls-remote --tags` at time of writing. libigl's
tag is dated 2026-08-31 (nine days before this note), so it is actively maintained. OpenMesh's tag
is dated 2022-01-18; the GitLab default branch HEAD is
[`8d527cd1e733889c49d14ebc7a7da9294995b3ef`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/commit/8d527cd1e733889c49d14ebc7a7da9294995b3ef),
which differs from the tagged commit — there is post-9.0 activity on the default branch that this
note did not read. Everything below is pinned to the tag, not to that later commit.

| Area | Path at the pinned commit |
|---|---|
| Boolean entry point and pipeline orchestration | [`include/igl/copyleft/cgal/mesh_boolean.cpp`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp) |
| Self-intersection resolution | [`remesh_self_intersections.h`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/remesh_self_intersections.h), [`SelfIntersectMesh.h`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/SelfIntersectMesh.h) (938 lines), [`CGAL_includes.hpp`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/CGAL_includes.hpp) |
| Cell extraction | [`extract_cells.h`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/extract_cells.h), [`extract_cells.cpp`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/extract_cells.cpp) (394 lines) |
| Winding-number propagation | [`propagate_winding_numbers.h`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/propagate_winding_numbers.h), `.cpp` (328 lines) |
| Outer facet (robust, normal-free) | [`outer_facet.h`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/outer_facet.h) |
| Licence split | [`copyleft/README.md`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/README.md), `LICENSE.MPL2`, `LICENSE.GPL` at repo root |
| Tutorial usage of the boolean | [`tutorial/609_Boolean/main.cpp#L27`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/tutorial/609_Boolean/main.cpp#L27) |
| Per-element connectivity structs | [`src/OpenMesh/Core/Mesh/ArrayItems.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayItems.hh) |
| Handle type | [`Handles.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/Handles.hh) |
| Connectivity kernel, opposite-halfedge, garbage collection | [`ArrayKernel.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayKernel.hh), [`ArrayKernel.cc`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayKernel.cc), [`ArrayKernelT_impl.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayKernelT_impl.hh) |
| Euler operators, manifold query | [`PolyConnectivity.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/PolyConnectivity.hh) (1716 lines) |
| Property system | [`BaseProperty.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/BaseProperty.hh), [`Property.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/Property.hh), [`PropertyContainer.hh`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/PropertyContainer.hh) |
| Default coordinate type | [`Traits.hh#L121-L128`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/Traits.hh) |

**Naming note:** `PropertyT.hh` (as commonly referenced) is `Property.hh` at this tag — its own
doxygen comment still says `\class PropertyT Property.hh <OpenMesh/Core/Utils/PropertyT.hh>`
([`Property.hh#L68`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/Property.hh)),
a stale self-reference from a since-renamed file; the class inside is still `PropertyT<T>`.

## The paper

Qingnan Zhou, Eitan Grinspun, Denis Zorin, Alec Jacobson, **"Mesh Arrangements for Solid
Geometry"**, ACM Transactions on Graphics 35(4), SIGGRAPH 2016.
DOI: [10.1145/2897824.2925901](https://doi.org/10.1145/2897824.2925901).
*Claimed*, quoted from the paper PDF:

- Guarantee: "Our method guarantees as output a solid mesh. Informally, a solid mesh is the
  non-degenerate boundary of a solid subregion of R3. Our method also guarantees that the output
  is exact, i.e., interpreting the input positions as exact rationals, all intersections result
  from exact construction. The output coordinates may optionally be converted to floating point in
  a post-process."
- Scope of the guarantee: "We introduce mesh arrangements constructed from a restricted class of
  meshes: those with piecewise-constant winding number, or PWN. […] By robust, we mean that
  algorithms successfully produce output for all PWN meshes."
- What the *arrangement stage itself* tolerates, before that guarantee is asked for: "A mesh
  arrangement, built from a collection of (possibly non-manifold, open-boundary, self-intersecting,
  with degenerate triangles, etc.) meshes, partitions space into a number of cells."

Qingnan Zhou — the paper's first author — is also the author on the copyright header of
`extract_cells.h`, `propagate_winding_numbers.h`, `outer_facet.h` and most of the other
`copyleft/cgal` boolean files: this is the paper's own author's implementation, not a third
party's, which is why libigl is read here rather than a re-implementation.

## The arrangement pipeline, read from source

Traced through `igl::copyleft::cgal::mesh_boolean` at
[`mesh_boolean.cpp#L192-L415`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L192-L415):

1. **Combine and resolve self-intersections.** The two (or more) inputs are concatenated into one
   `(V,F)` and passed to `remesh_self_intersections` with `stitch_all=true`
   ([`#L217-L222`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L217-L222)),
   which "subdivide[s]" any self-intersecting triangles "so that the self-intersection contour
   lies exactly on edges", and states its own manifold-preservation guarantee: "if the input
   triangle mesh is a closed manifold the output will be too"
   ([`remesh_self_intersections.h#L21-L27`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/remesh_self_intersections.h#L21-L27))
   — phrased as a conditional, not a requirement: a non-closed or non-manifold input is accepted
   and stays that way.
2. **Patches.** `igl::extract_manifold_patches` groups the resolved triangles into maximal
   2-manifold pieces via the unique-edge map
   ([`#L228-L234`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L228-L234)).
3. **Cells.** `extract_cells` partitions the ambient space bounded by the patches into connected
   3D cells, by convention cell 0 is the unbounded outer cell
   ([`extract_cells.h#L21-L38`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/extract_cells.h#L21-L38)).
4. **Winding numbers.** `propagate_winding_numbers` assigns an integer winding number to each side
   of each patch with respect to each input mesh
   ([`#L274-L282`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L274-L282)).
   This is the step with the input requirement, stated twice in its own header, once at file scope
   and once on the function: "The input mesh is valid if it splits the ambient space, R^3, into
   subspaces with constant integer winding numbers. That is the input mesh should be closed and
   for each directed edge the number of clockwise facing facets should equal the number of
   counterclockwise facing facets"
   ([`propagate_winding_numbers.h#L15-L20`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/propagate_winding_numbers.h#L15-L20)),
   and "The input mesh must represent the boundary of a valid 3D volume, which means it is closed,
   consistently oriented and induces integer winding numbers"
   ([`#L29-L32`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/propagate_winding_numbers.h#L29-L32)).
   The function **returns a `bool`** that is false when this does not hold.
5. **Classify and extract.** A caller-supplied `keep` function turns the per-side winding-number
   pair into "keep as-is / keep flipped / discard" per face
   ([`#L296-L338`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L296-L338)).
   **This step runs unconditionally, whether or not step 4 returned `false`.** There is no
   ray-cast or other fallback branch in this file for the non-PWN case — unlike
   [`blender.md`](blender.md) §Exact boolean, whose dispatcher falls back to a float ray-cast per
   patch when its own PWN test fails. libigl's contract is narrower and more honest about it: a
   `false` return means "the winding numbers may not mean what you think", and it is the caller's
   job to check the flag, not the library's job to guess a better answer.
6. **Exactness is a chosen kernel, not only chosen predicates.** `mesh_boolean`'s five-argument
   overload declares `typedef CGAL::Epeck Kernel;` and stores the merged mesh's coordinates as
   `MatrixXES` — a matrix of `CGAL::Epeck::FT` exact rationals
   ([`#L206-L214`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L206-L214)),
   and `extract_cells.cpp` independently includes the same
   `CGAL/Exact_predicates_exact_constructions_kernel.h`. Every stage above — resolution, patches,
   cells, winding numbers — runs on exact rational coordinates, not on doubles filtered by exact
   predicates. Only the very last step converts back: `assign_scalar(V(J(i),c), slow_and_more_precise, VC(i,c))`
   with `slow_and_more_precise = false` by default
   ([`#L398-L406`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L398-L406)).
   This is a stricter (and, per §How it compares below, more expensive) choice than Blender's,
   whose `Vert` carries `mpq3 co_exact` and `double3 co` *side by side* and uses `_fast`
   double-only predicates until they are inconclusive
   ([`blender.md`](blender.md) §How exactness is actually implemented). libigl instead commits the
   whole pipeline's storage to `Epeck::FT`. `SelfIntersectMesh` itself is templated on the kernel
   and its own doc comment names both options —
   `CGAL::Exact_predicates_inexact_constructions_kernel` (Epick, filtered) or
   `CGAL::Exact_predicates_exact_constructions_kernel` (Epeck, exact storage)
   ([`SelfIntersectMesh.h#L37-L42`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/SelfIntersectMesh.h#L37-L42))
   — but `mesh_boolean` itself instantiates it with Epeck only.
7. **The output precondition, one step further out.** `outer_facet` — used to seed cell
   classification — states a precondition rather than tolerating a violation: "The input mesh must
   have all self-intersection resolved. I.e there is no duplicated vertices, no overlapping edge
   and no intersecting faces"
   ([`outer_facet.h#L20-L26`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/outer_facet.h#L20-L26)),
   satisfied by construction because step 1 always runs first. It is also, by its own comment,
   more robust than `igl::outer_facet` "because it does not rely on facet normals" — a
   normal-independent design point worth noting for degenerate-triangle input, where a computed
   normal can be unreliable.

**The `valid` flag is real, and it is easy to ignore.** libigl's own tutorial calls the four-return
overload and discards the boolean entirely: `igl::copyleft::cgal::mesh_boolean(VA,FA,VB,FB,boolean_type,VC,FC,J);`
([`tutorial/609_Boolean/main.cpp#L27`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/tutorial/609_Boolean/main.cpp#L27)),
and the header declares no `[[nodiscard]]` on any overload. The library tells the truth about
non-PWN input; its own example does not act on being told.

## OpenMesh's half-edge layout, read from source

`ArrayItems` defines the connectivity struct per element type — no position, no attribute, only
topology handles:

```cpp
class Vertex   { HalfedgeHandle halfedge_handle_; };                              // 1 handle
class Halfedge { FaceHandle face_handle_; VertexHandle vertex_handle_;
                 HalfedgeHandle next_halfedge_handle_; HalfedgeHandle prev_halfedge_handle_; }; // 4 handles
class Edge     { Halfedge halfedges_[2]; };                                       // 2 halfedges
class Face     { HalfedgeHandle halfedge_handle_; };                              // 1 handle
```

— [`ArrayItems.hh#L64-L118`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayItems.hh#L64-L118).
`BaseHandle` is a bare `int idx_`
([`Handles.hh#L62-L102`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/Handles.hh#L62-L102)),
4 bytes, no generation. **Counting rule** for the byte figures below: one `int` handle field = 4
bytes; a struct's size is its listed fields only (position/normal/colour live in separate
per-vertex properties, not in `ArrayItems::Vertex`). Vertex = 4 B, halfedge = 16 B, edge = 2×16 =
32 B (it stores its own two halfedges, not a reference to them), face = 4 B. An edge's two
halfedges are always adjacent in the array: halfedge index = `2*edge_index + {0,1}`, and the
opposite of a halfedge is `index ^ 1` — computed, **never stored**
([`ArrayKernel.hh#L460-L461`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayKernel.hh#L460-L461)).

Attributes (position, normal, colour, texcoord, and any user-defined channel) are **not** part of
`ArrayItems`; they are `PropertyT<T>` instances, each a plain `std::vector<T>` behind a
`BaseProperty` interface with virtual `reserve`, `resize`, `swap(i0,i1)`, `n_elements`
([`Property.hh#L92-L131`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/Property.hh#L92-L131)),
held in a `PropertyContainer`'s `std::vector<BaseProperty*>`
([`PropertyContainer.hh#L58-L72`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Utils/PropertyContainer.hh#L58-L72))
that resizes and swaps in lock-step with the connectivity array it is keyed against. This is
already the parallel-arrays-keyed-by-handle pattern spec §6 wants for structure-of-arrays storage.

**Deletion renumbers.** `garbage_collection` swaps every element with a `deleted` status flag to
the end of its `std::vector` and resizes — which moves surviving elements to new indices — then
walks the mesh updating every stored handle to match, and optionally patches caller-supplied
handle-pointer lists
([`ArrayKernelT_impl.hh#L104-L131`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayKernelT_impl.hh#L104-L131)
for the vertex pass; edges and faces follow immediately after in the same file). A handle held
outside that patch list silently points at the wrong element after garbage collection — there is
no generation to detect it.

### Comparing the three half-edge layouts

| Dimension | OpenMesh `ArrayKernel` | BMesh (per [`blender.md`](blender.md)) | Kernel spec §4, §6 |
|---|---|---|---|
| Storage | connectivity struct per element type in one `std::vector` each; attributes as separate `PropertyT<T>` vectors keyed by the same index | "non-manifold-tolerant half-edge structure with radial loops, per-element allocated from pools" (`blender.md` §What it is) — per-element byte layout is not stated there and is out of scope for this note, which read no Blender source | half-edge mesh, f64 positions, per-vertex/per-corner/per-face named attribute channels (spec §4); structure-of-arrays, contiguous storage (spec §6) |
| Bytes/vertex (connectivity only) | 4 (one `HalfedgeHandle`) — see counting rule above | not stated in `blender.md` | not itemized in the spec at field level |
| Bytes/halfedge | 16 (face + to-vertex + next + prev) | not stated in `blender.md` | not itemized |
| Edge model | fixed at exactly 2 halfedges per edge (32 B); a third face on one edge cannot be represented without splitting the edge | "radial loop" is the standard term for a non-2-manifold edge's ring of incident face-corners; that a radial structure exists is what "non-manifold-tolerant" in `blender.md` §What it is means by construction, but `blender.md` does not itself spell out the linked-list detail — *inferred*, not read from Blender source in this note | not specified — an open design question this note surfaces rather than settles |
| Handle stability under deletion | plain `int` index; `garbage_collection` swaps-to-end, resizes, **renumbers** survivors unless the caller tracks handle pointers itself | not characterized in `blender.md` | generational handles (index + generation): O(1) deletion, indices stay stable across reallocation, stale access is detected, never dereferenced (spec §6) |
| Attribute mechanism | `PropertyT<T>` parallel arrays keyed by handle index, coordinated resize/swap via `PropertyContainer` | `Mesh` (the separate, non-BMesh storage form) is described as structure-of-arrays attributes; BMesh's own attribute mechanism is not detailed in `blender.md` | per-vertex, per-corner, per-face named channels (spec §4) |

Unmarked cells above are *measured* (OpenMesh column, from the source read in §OpenMesh's
half-edge layout) or *source* (kernel spec column, quoting spec §4/§6 directly); the BMesh column
is *claimed*, from `blender.md`'s own text, except where marked *inferred*.

## Licence

libigl's own source under `copyleft/cgal/` is **not** GPL by its own file headers — *measured*:
`grep -rl "Mozilla Public License" include/igl/copyleft/cgal/ | wc -l` → **122** files with an MPL2
header, `grep -rl "GNU General Public\|GPL"` → **0**. The `copyleft/README.md` is explicit about
why the namespace still carries a GPL warning: "this subdirectory includes code that is under GPL
[…] If you do obtain such a license for the dependencies employed here, you are free to use the
libigl functions here as per their MPL2 license"
([`copyleft/README.md#L1-L14`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/README.md)).
The GPL is inherited from the dependency, not authored here — and, per
[`problems.md`](problems.md) P-14's rule that licence must be checked at the granularity of the
file actually pulled in: `CGAL_includes.hpp`, included by `SelfIntersectMesh.h`, includes
`#include <CGAL/Polyhedron_3.h>`
([`CGAL_includes.hpp#L40`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/CGAL_includes.hpp#L40)).
[`problems.md`](problems.md) P-14 already establishes, from `cgal.md`'s header-by-header audit at
CGAL tag `v6.0.1`, that `Polyhedron/include/CGAL/Polyhedron_3.h` is licensed
`GPL-3.0-or-later OR LicenseRef-Commercial`. That single include is sufficient: the arrangement
pipeline cannot be compiled without a GPL (or commercially licensed) CGAL package, whatever
licence libigl's own files carry. The rest of the pipeline's CGAL includes — `Exact_predicates_*`,
`AABB_tree`, `box_intersection_d`, `Constrained_Delaunay_triangulation_2` — were not individually
re-audited here; `Polyhedron_3.h` alone already settles the question, so re-deriving the others
would not change the answer and is left to `cgal.md` if a future note needs the full package list.

OpenMesh is **BSD-3-Clause** — *measured*, `LICENSE` at the tag, restated verbatim at the top of
every source file's header comment
([`ArrayItems.hh#L1-L40`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/ArrayItems.hh)).
Permissive: code and design may both be taken, same class of licence as Manifold's Apache-2.0
([`manifold.md`](manifold.md) §Evaluation).

## The Python binding — measured

The task brief asks for a cheap check rather than a claim. Installed in a clean venv:

```
python -m venv igl_venv
./igl_venv/Scripts/python.exe -m pip install libigl
./igl_venv/Scripts/python.exe -c "import igl; print(igl.__file__)"
```

`pip show libigl` reports **version 2.6.3** — the same version as the pinned core tag — but a
**different repository**: `Home-page: https://github.com/libigl/libigl-python-bindings`, not
`libigl/libigl` itself. That second repository's own source was not read; only the installed
wheel's exposed surface was.

*Measured*: `dir(igl)` lists 302 public names. None of `mesh_boolean`, `remesh_self_intersections`,
`extract_cells`, `propagate_winding_numbers`, `outer_facet`, or anything under a `copyleft`
sub-namespace is present — the CGAL-dependent boolean pipeline is **not exposed** by the PyPI
package at this version. What is exposed and boolean-adjacent is geometric-query-only:
`winding_number`, `fast_winding_number`, `fast_winding_number_precompute`,
`FastWindingNumberBVH`, `ray_mesh_intersect`, `ray_triangle_intersect`,
`tri_tri_intersection_test_3d`. A caller wanting the exact arrangement boolean from Python needs
the C++ pipeline directly, not this wheel.

## Evaluation

Criteria from [`README.md`](README.md). Both libraries are libraries, not kernels — several rows
are marked not applicable and say why, per the task's instruction.

| Criterion | libigl (`copyleft/cgal` boolean) | OpenMesh | Evidence type |
|---|---|---|---|
| **License** | MPL2 own files; GPL via `CGAL::Polyhedron_3` dependency (§Licence) | BSD-3-Clause | measured |
| **Representations held natively** | **None of its own** — `mesh_boolean` takes `Eigen::MatrixBase<Derived...>` (`V`, `F`) and returns the same; there is no persistent libigl mesh class, only free functions over matrices | **One**: a half-edge polygon mesh (`PolyMesh`/`TriMesh`). No B-rep, point cloud, or implicit — confirmed by the `src/OpenMesh/Core/` layout (`Geometry`, `IO`, `Mesh`, `System`, `Templates`, `Utils`; no B-rep or volume module) | inferred (matrix-API signature read directly; OpenMesh directory listing) |
| **Boolean robustness** | Not measured against the torture set in this note (no spike required by the brief). Algorithm class and input contract are read from source: §The arrangement pipeline | not applicable — OpenMesh ships no boolean | source; not applicable (OpenMesh) |
| **Tolerance and precision model** | No tolerance: identity is exact-rational equality throughout the pipeline, same design point as Blender's `Vert::co_exact` (§How it compares) | No fixed tolerance; `Point` is a traits typedef, default `Vec3f` (float32) — *measured*, [`Traits.hh#L121-L128`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/blob/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab/src/OpenMesh/Core/Mesh/Traits.hh) `struct DefaultTraits { typedef Vec3f Point; … }` — overridable to `Vec3d` (f64) or any type by supplying a custom traits struct, unlike Blender's hardwired `float3` | measured + source |
| **Incremental evaluation** | **None.** Every call rebuilds the arrangement of the full combined input; no dependency graph, no partial re-run | **Local edits are local**: `collapse`, `split_edge`, `insert_edge` touch a bounded neighbourhood of handles (`PolyConnectivity.hh`), but there is no dependency graph above that — a caller must track what changed itself | inferred from source |
| **Threading model** | `igl::parallel_for` used once, for the final coordinate copy ([`mesh_boolean.cpp#L400-L406`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L400-L406)); the arrangement stages themselves were not traced for internal CGAL threading in this note | Not verified; `ArrayKernel`/`PropertyContainer` show no locking or atomics in the files read, consistent with a single-writer assumption, but this was not exhaustively checked | inferred, low confidence — flagged rather than asserted |
| **GPU path** | Not applicable — no GPU code in this pipeline | Not applicable — no GPU code | not applicable |
| **IFC coverage** | Not applicable | Not applicable | not applicable |
| **Performance** | Not measured — no spike required for a design-reference note | Not measured | not applicable |
| **Embeddability** | Header-only core; the CGAL boolean additionally needs CGAL, GMP and MPFR linked — heavier than Manifold's zero-dependency C ABI ([`manifold.md`](manifold.md) §Evaluation) but still in-process, no subprocess, unlike Blender (`blender.md` §Embeddability) | Plain C++ static/shared library, no exotic dependency; in-process | inferred |
| **2D derivation** | Not applicable to this pipeline | Not applicable | not applicable |
| **Maturity** | Active: tag `v2.6.3` dated 2026-08-31; NYU/Columbia geometry-processing group plus a wide external contributor base (*inferred* from repository activity, not a tracker survey) | Twenty-one years old (`Copyright (c) 2001-2022` in every header); last tag `OpenMesh-9.0` is 2022-01-18, default branch has since moved past it (§What was read). RWTH Aachen Computer Graphics and Multimedia group | claimed/inferred |
| **AI familiarity** | High: public C++ since ~2013, the SIGGRAPH paper is public. One column, never a tiebreaker (R-09) | High: two decades of public C++ and academic use | inferred |

## The twelve questions

Answered briefly, most by pointer to a section above rather than restated; "not applicable" is
given where it is a library-vs-kernel mismatch rather than a gap.

1. Re-evaluate one changed element? No for both — §Evaluation, Incremental evaluation.
2. IFC round trip? Not applicable.
3. Driven in-process from DynLex? Architecturally yes for both (no subprocess, no file) —
   §Evaluation, Embeddability; not exercised from DynLex, a design observation not a spike.
4. Threading model? §Evaluation — not exhaustively characterized for either.
5. What breaks first at scale? Not measured. Inferred: libigl's Epeck pipeline holds exact
   rational coordinates for the whole merged mesh for one call, the cost class
   [`cgal.md`](cgal.md) §What P-03 asks already shows; OpenMesh's `PropertyContainer` is plain
   `std::vector` storage with no chunking, bounded by RAM like any in-core structure.
6. Numeric precision, configurable? libigl: exact rational internally, `double` on output (§The
   arrangement pipeline, step 6). OpenMesh: per-mesh via traits, default float32 (§Evaluation).
7. Operate on a subset — one tile, one region? No for either; both take the whole mesh.
8. Who maintains it? §Evaluation, Maturity.
9. Documented failure modes, with issue links? Out of scope — no tracker survey was run, unlike
   [`occt.md`](occt.md) or [`blender.md`](blender.md). The one failure mode here is a source fact,
   not a tracker finding: the PWN-validity flag is honest but easy to ignore (§The arrangement
   pipeline, last paragraph).
10. Representations held natively? §Evaluation.
11. GPU path? Not applicable to either.
12. What would we take, what would we avoid? §Verdict, below.

## Verdict

### Build on

**No — library scope, for both.** libigl is a header-and-function library over caller-owned
matrices with no persistent mesh, no incremental evaluation and a GPL dependency in the one
pipeline this note cares about; OpenMesh is a single-representation (half-edge mesh only) library
with no spatial index, no GPU path and no boolean of its own. Neither is a candidate kernel or
kernel layer under ADR-0004's question; both are read for design and algorithm only.

### Borrow from

1. **The five-stage arrangement pipeline as a pipeline shape**: resolve self-intersections → patch
   → extract cells → propagate winding numbers → classify by a caller-supplied keep function.
   This is the concrete shape spec §4's "exact arrangement of the two triangle sets using exact
   predicates, then classification" should follow — libigl's source is the reference
   implementation of that sentence.
   Source: [`mesh_boolean.cpp#L192-L415`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/mesh_boolean.cpp#L192-L415).
2. **An explicit, machine-checkable PWN-validity signal returned from the winding-number stage
   itself**, distinct from the classification step that runs regardless. Our kernel's error model
   (spec §12: a result value, never a silent repair) should attach the PWN check's outcome to the
   boolean's *result*, not leave it as a return value a caller can discard the way libigl's own
   tutorial does.
   Source: [`propagate_winding_numbers.h#L15-L32`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/propagate_winding_numbers.h#L15-L32);
   the ignored case: [`tutorial/609_Boolean/main.cpp#L27`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/tutorial/609_Boolean/main.cpp#L27).
3. **A normal-independent outer-facet test** for seeding cell classification, worth taking as a
   robustness detail for the degenerate-triangle cases in the torture set, where a computed face
   normal is unreliable.
   Source: [`outer_facet.h#L20-L32`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/include/igl/copyleft/cgal/outer_facet.h).
4. **Properties as parallel, independently-typed arrays keyed by one handle-index space** — the
   `PropertyT<T>`/`PropertyContainer` pattern of §OpenMesh's half-edge layout above — is exactly
   the structure-of-arrays direction spec §6 already commits to; worth taking directly, not just
   as an analogy.
5. **The paired-halfedge index trick for the opposite pointer** (§OpenMesh's half-edge layout,
   `index ^ 1`). Removes one `HalfedgeHandle` field (4 bytes) from every halfedge and one class of
   corruption (an opposite pointer that disagrees with its twin). Worth weighing for the kernel's
   mesh module, conditional on choosing an edge-pair-contiguous layout — it does not apply if a
   design allows an edge's two halfedges to live apart.

### Avoid

- **Plain-index handles with garbage-collection renumbering** (§OpenMesh's half-edge layout,
  "Deletion renumbers"). The opposite of spec §6's generational handles, whose stated purpose is
  that "handles stay stable across reallocation, and dangling references are detected rather than
  dereferenced." It is also the mechanism [`problems.md`](problems.md) P-04 names as the general
  failure class ("a kernel with no cross-operation history … forces the application to reconstruct
  identity from scratch") — OpenMesh's GC is a second, independent source of the same symptom, at
  the connectivity layer rather than the naming layer.
- **GPL-by-dependency in anything meant to be linked.** `copyleft/cgal`'s own files are MPL2, but
  the arrangement pipeline cannot build without `CGAL::Polyhedron_3` (§Licence), which is GPL. The
  design may be read and reimplemented; the code may not be linked into a kernel that is not
  itself GPL (R-11) — the same posture [`blender.md`](blender.md) §What it is takes toward
  Blender's own GPL boolean sources.
- **A validity signal a caller is free to discard.** libigl's own tutorial ignores the PWN-`bool`
  ([`tutorial/609_Boolean/main.cpp#L27`](https://github.com/libigl/libigl/blob/f68f01c23ac82351e2543ce8c529b6d4c89fdf16/tutorial/609_Boolean/main.cpp#L27)).
  Our kernel's result-value error model (spec §12) exists specifically so this cannot happen: a
  caller that does not branch on a result cannot silently get best-effort geometry, because there
  is no separate "keep going anyway" code path to fall into — the value itself carries the
  outcome.

## Sources

- [libigl repository, tag `v2.6.3`](https://github.com/libigl/libigl/tree/f68f01c23ac82351e2543ce8c529b6d4c89fdf16)
- [OpenMesh repository, tag `OpenMesh-9.0`](https://gitlab.vci.rwth-aachen.de:9000/OpenMesh/OpenMesh/-/tree/adebfb1ec0c14a43f5503a2dfea3d76599eb28ab)
- Zhou, Grinspun, Zorin, Jacobson, "Mesh Arrangements for Solid Geometry", ACM TOG 35(4), SIGGRAPH
  2016. DOI: [10.1145/2897824.2925901](https://doi.org/10.1145/2897824.2925901)
- [`libigl` on PyPI, version 2.6.3](https://pypi.org/project/libigl/) — a different repository
  (`libigl/libigl-python-bindings`) from the core library pinned above
- [`blender.md`](blender.md) §Exact boolean, §What it is — the same algorithm lineage, read
  independently; cited rather than repeated
- [`manifold.md`](manifold.md) §Evaluation, §Embeddability — licence and embeddability comparison
- [`cgal.md`](cgal.md), [`problems.md`](problems.md) P-14 — the `Polyhedron_3.h` GPL classification
  this note relies on rather than re-deriving
