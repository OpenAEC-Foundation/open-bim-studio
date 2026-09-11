# Open CAD Studio — and `cadkernel`, the geometry it actually runs on

**Decision question:** Open CAD Studio (OCS) is a Rust CAD application with solid primitives,
extrude/revolve/loft/sweep, booleans, ACIS read-write and a wgpu renderer with a browser build.
The maintainer asks whether its geometry is usable **as, or inside, our kernel**. This note
answers: **what is OCS's geometry, where does it live, and which of the three sub-projects — the
kernel, `ui/`, `app/` — could take a dependency on it rather than write the same thing?**

**Serves:** ADR-0003 vs ADR-0004 (build on vs. build our own); ADR-0005 (B-rep representation and
tolerance model), ADR-0006 (precision and the GPU path); kernel spec §3, §4, §5, §12;
[`problems.md`](problems.md) P-01, P-05, P-12, P-14 and two new rows, P-30 and P-31

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

---

## Summary

**OCS has no geometry of its own.** Its solid modelling is a thin application wrapper — primitive
constructors, command plumbing, tessellation-to-GPU — over
[`cadkernel`](https://github.com/HakanSeven12/cadkernel), a separate crate by the same author, and
its DWG/DXF layer is a second separate crate,
[`cadcodec`](https://github.com/HakanSeven12/cadcodec) (package name `acadrust`). The application is
**GPL-3.0-only**; both libraries are **MPL-2.0**, which is the fact that decides this note: the
geometry and the file format are separable from the application and carry a licence a differently
licensed product can link.

`cadkernel` is a single-representation B-rep kernel, f64 throughout, with generational typed
handles, a translation-only local frame lifted at every entry point, a scale-derived operation
tolerance, an imprint-then-classify boolean that returns a typed refusal rather than an approximate
solid, and a provenance model that writes untouched source records back byte-for-byte. Several of
those are things our kernel spec proposes and one — provenance — is better than anything the spec
has. It is also **34 days old** at the pinned commit, single-representation where the spec wants
four, has no exact predicates, no spatial index and no threading, and is consumed by git revision
rather than a release.

**No benchmark was run.** The wiring is feasible and the entry points exist; every `cargo`
invocation in this session was refused by the environment's command policy. §Measurements says
exactly what was and was not established, and names the experiment.

---

## What was read, and at which commit

Everything below is cited at these revisions. Links are pinned; none point at `main`.

| Source | Revision read | How verified |
|---|---|---|
| **Open CAD Studio** | [`798379fbe0eb60025e4f4827441359aed812f5ff`](https://github.com/HakanSeven12/OpenCADStudio/tree/798379fbe0eb60025e4f4827441359aed812f5ff) — `main`, 2026-09-11 19:13 +0300, "Update dependencies after cadcodec PR 44" | *source*, `gh api repos/HakanSeven12/OpenCADStudio/commits/main --jq .sha`, then fetched into the local clone and read with `git show <sha>:<path>` |
| **cadkernel** | [`953d546b68aef4b6692566a1a9b077fc5bd9fb4f`](https://github.com/HakanSeven12/cadkernel/tree/953d546b68aef4b6692566a1a9b077fc5bd9fb4f) — the revision OCS pins, and also `main` at read time (`git rev-list --count 953d546b..origin/main` → `0`) | *source*, cloned and checked out at that revision |
| **cadcodec** (package `acadrust` 0.5.5) | [`70ac6da7cf149cea6398a3d8829dd5e48b485b96`](https://github.com/HakanSeven12/cadcodec/tree/70ac6da7cf149cea6398a3d8829dd5e48b485b96) — the revision OCS pins | *source*, `gh api repos/HakanSeven12/cadcodec/commits/70ac…` resolves; `Cargo.toml` read at that ref |

**About the local clone.** The clone at `C:\Users\rickd\Documents\GitHub\OpenCADStudio` had
`HEAD` = `1490fe4ea91dd83498bc7c280e124a07f194c37f` (`git describe --tags` → `v0.8.2-11-g1490fe4e`,
authored 2026-07-15), with one local modification, to `.gitignore` only (`git status --short` →
` M .gitignore`), so its tracked sources equal that commit. That commit **is** upstream
(`git branch -r --contains HEAD` lists `origin/main`), but it is **1806 commits behind**
`origin/main` (*source count*, `git rev-list --count HEAD..origin/main` after fetching). It predates
releases `v0.9.0`–`v2026.36` and describes a **different kernel**: at `1490fe4e` OCS's solids were
built on the third-party `truck` crates with a boolean tolerance constant of `0.05`
(`src/scene/model/solid_model.rs` at that commit, lines 142–158). None of that survives at `main`.
Reading the clone as checked out would have produced a note about software that no longer exists,
so the clone was fetched and **everything in this note is read at `798379fb`**. The superseded
design is mentioned only where the contrast is the finding.

---

## What it is

Open CAD Studio is a DWG/DXF-native 2D and 3D CAD application written in Rust on `iced`
(git revision `23604ff2`) over `wgpu` 29.0.4, with a desktop build and a Trunk/WASM browser build.
The repository was created **2026-03-22** and has 1,557 stars, 158 forks and 815 issues of
which 144 are open (*source count*, `gh api repos/HakanSeven12/OpenCADStudio`;
`gh issue list --state all --limit 1000`).
Its source is 527 `.rs` files with 941 `#[test]` functions plus 17 integration-test files
(*source count*, `git ls-tree -r --name-only 798379fb -- src | grep -c '\.rs$'`;
`git grep -c '#\[test\]' 798379fb -- src` summed).

The geometry question is not about that repository. It is about the two crates it depends on:

```
OpenCADStudio  (GPL-3.0-only, application)
  ├── cadkernel            MPL-2.0   B-rep topology, booleans, blends, ACIS bridge
  ├── cadkernel-constraints MPL-2.0  (same repository, workspace member)
  └── acadrust / cadcodec  MPL-2.0   DXF + DWG read/write
```

*source*, [`Cargo.toml#L33-L35`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/Cargo.toml#L33-L35),
which pins both by git revision, not from crates.io. Licences *source* from each repository's
`Cargo.toml` `license` field and the GitHub licence API:
OCS [`LICENSE`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/LICENSE)
is GPLv3 and its README states `GPL-3.0 license`
([`README.md#L39`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/README.md#L39));
the root `Cargo.toml` carries no `license` field, but its workspace member
[`crates/ocs_plugin_api/Cargo.toml#L6`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/crates/ocs_plugin_api/Cargo.toml#L6)
does: `license = "GPL-3.0-only"` — the one direct SPDX field in the tree for the application's own
licence, and it settles **-only** against the README's ambiguous "GPL-3.0 license" wording.
*Source*, `git grep -n "GPL-3.0-or-later\|or-later" 798379fb` over `*.toml` → no match in any
`Cargo.toml`; over the whole tree → **one** match, and it is not a licence grant:
[`packaging/io.github.HakanSeven12.OpenCadStudio.metainfo.xml#L5`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/packaging/io.github.HakanSeven12.OpenCadStudio.metainfo.xml#L5)
declares `<project_license>GPL-3.0-or-later</project_license>` in Flatpak/AppStream packaging
metadata, contradicting the `LICENSE` file, the README and `ocs_plugin_api`'s own SPDX field. This
does not change the conclusion — `LICENSE` and the Cargo.toml SPDX field are the authoritative
sources, both say **-only** — but it is the same failure mode `problems.md` P-14 already records for
xBIM: one project describing its own licence two ways in two files.
cadkernel's [`Cargo.toml#L5`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/Cargo.toml#L5)
is `license = "MPL-2.0"`; cadcodec's is `license = "MPL-2.0"` at `Cargo.toml#L7`.

---

## 1. `cadkernel`: what the geometry actually is

*source count*, `find . -name '*.rs' -not -path './.git/*'` over the repository → **102 files, 57,643
lines**, of which `src/` is 83 files and 50,956 lines (`brep` 29,063 / `geom2d` 13,132 / `space`
5,615 / `acis` 2,976, the remainder `lib.rs` and `tessellation.rs`) and the
`cadkernel-constraints` workspace member under `crates/` is 19 files and 6,687 lines. **672
`#[test]` functions in 60 of the 83 `src/` files**; **zero occurrences of `unsafe`** (*source count*,
`grep -rn unsafe --include=*.rs src | wc -l` → 0).

### Layering, and why 2D is underneath

The crate's own statement, and the reason it is worth reading:

> The direction is the point. Splitting a face during a boolean means projecting the intersection
> curve into that face's `(u, v)` space and running a loop boolean there — a 2D problem. The quality
> of `geom2d` therefore caps the quality of `brep`, which is why 2D comes first rather than as an
> afterthought.

([`README.md#L21-L26`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/README.md#L21-L26))
The feature graph enforces it: `acis → brep → geom2d`, with `geom2d` the default and
dependency-free ([`Cargo.toml#L14-L34`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/Cargo.toml#L14-L34)).

### One representation, not four

*source*, reading the two type enums and grepping for the others:

| Representation | Present? | Evidence |
|---|---|---|
| B-rep | Yes — `Surface::{Plane, Cylinder, Cone, Sphere, Torus, Nurbs}` ([`brep/geometry.rs#L31-L47`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/geometry.rs#L31-L47)); `Curve::{Line, Circle, Arc, Ellipse, Polyline, Nurbs, Ray, XLine}` ([`geom2d/curve.rs#L170-L187`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/curve.rs#L170-L187)) | *source* |
| Mesh | **Output only.** `brep::mesh` produces `Mesh`/`BodyMesh` for display; there is no half-edge mesh and no mesh-domain operation ([`brep/mesh.rs`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/mesh.rs), `pub fn tessellate` at L909) | *source* |
| Point cloud | **None** | *source*, `grep -rln 'point_cloud\|PointCloud' --include=*.rs src` → no matches |
| Implicit / SDF | **None** | *source*, `grep -rln 'signed_distance\|sdf\|Sdf\|implicit' --include=*.rs src` → no matches |

Against kernel spec §4's four first-class representations, cadkernel covers one, with the second as
a one-way export. Mesh → B-rep exists in one narrow form: `faceted_solid(vertices, faces) -> Option<Body>`
([`brep/make.rs#L173`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/make.rs#L173)),
alongside `cuboid`, `cylinder`, `sphere`, `cone`, `frustum`, `torus`, `wedge`, `pyramid`,
`pyramid_frustum`, `elliptical_cylinder`.

### Topology: generational typed handles, in an arena — the spec §4 mechanism, independently

`Key<T>` is a `u32` index plus a `u32` generation plus `PhantomData<fn() -> T>`
([`brep/arena.rs#L39-L43`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/arena.rs#L39-L43)).
The module header states the reason, which is the same reason our spec gives:

> A boolean removes faces. If a key were a bare index, the slot it named would be handed to the next
> node created, and a key held across the operation would silently start referring to something else
> — a dangling pointer with none of the symptoms of one, producing topology that validates and is
> wrong.

([`brep/arena.rs#L10-L21`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/arena.rs#L10-L21))
Keys are typed so a `Key<Face>` cannot be passed where a `Key<Edge>` belongs
([`#L23-L28`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/arena.rs#L23-L28)).
This is a third independent arrival at the design our spec §4 proposes, after Fornjot's
append-only store and Truck's `Arc` identity ([`truck-fornjot.md`](truck-fornjot.md)) — and unlike
Fornjot's, it reclaims slots, which is what makes the generation necessary rather than decorative.

`Body::validate() -> Vec<Flaw>` returns every inconsistency rather than the first, over ten named
conditions including `NonManifoldEdge`, `SameSidedEdge`, `OpenLoop`, `DanglingKey` and
`BrokenOwnership` ([`brep/topology.rs#L540-L562`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/topology.rs#L540-L562),
function at [`#L309-L315`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/topology.rs#L309-L315)).
Its doc comment names when to run it: after a lift, so a malformed file is reported where it was
read, and after an edit.

### Precision: f64 everywhere, and a local frame lifted at every entry point

**There is no f32 in the kernel.** *source count*: `grep -rn f32 --include=*.rs src` returns **five**
matches and all five are inside comments explaining why f32 is not used
(e.g. [`geom2d/tessellate.rs#L9-L14`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/tessellate.rs#L9-L14)).

The coordinate policy is stated as an invariant, not a convenience
([`geom2d/frame.rs#L1-L33`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/frame.rs#L1-L33)):
every public operation builds a `Frame`, calls `lift` on each point before any arithmetic, and
`lower` on every point it returns; intermediate values never leave local space. The frame is
**translation-only** — "Rotation and scale are deliberately absent: they buy no conditioning and
would force every caller to reason about orientation"
([`#L35-L43`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/frame.rs#L35-L43)) —
and `Frame::around` anchors at the **midpoint of the input's bounding box**, with the reason given:
the midpoint bounds every lifted coordinate by half the extent, where an arbitrary member leaves the
far side as large as the whole span ([`#L57-L64`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/frame.rs#L57-L64)).

This differs from kernel spec §5 in a way worth naming. The spec puts geometry in a **tile** — a
frame that is project-wide and chosen on a coarse grid. cadkernel's frame is **per operation**,
derived from that operation's own operands. The spec's tiles are needed anyway for spatial
partitioning and streaming; cadkernel's per-operation lift is the belt to that braces, and it is
free, because the bounding box is computed regardless.

### Tolerance: derived from the operands, not a constant

`operation_tolerance(bodies: &[&Body]) -> f64` returns

```
extent * 1e-8 + f64::EPSILON * coordinate_scale * 64.0
```

where `extent` is the largest axis span of the operands' vertices (floored at 1.0) and
`coordinate_scale` is the largest absolute coordinate (floored at 1.0)
([`brep/bounds.rs#L163-L183`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/bounds.rs#L163-L183)).
Every blend, chamfer, boolean-internal step and the ACIS history rebuild calls it
(*source count*, `grep -rn operation_tolerance --include=*.rs src` → 28 lines; minus the definition
([`bounds.rs#L164`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/bounds.rs#L164)),
its re-export ([`mod.rs#L62`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/mod.rs#L62))
and two `use`-only lines ([`blend.rs#L3`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/blend.rs#L3),
[`slice.rs#L8`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/slice.rs#L8))
→ **24 call sites in 12 files**).

So the tolerance has a **size term and a distance-from-origin term**. That is the first tolerance
model in this research programme that responds to *where* the geometry is, and it is directly
comparable to the precision set. See §Measurements for the arithmetic.

Alongside it, the crate carries a scatter of module-local constants: `1e-9` (angle, proximity,
coplanarity, and the `TOL` in six `#[cfg(test)]` modules), `1e-10` (centreline, determinant),
`1e-14` (discriminant), and in the offset path `1e-5` (position) and `1e-4` (join)
(*source*, `grep -rn 'const .*TOL\|const EPS' --include=*.rs src`). There is **no per-entity
tolerance** — no tolerance field on a vertex, edge or face — so kernel spec §4's "a tolerance per
vertex, edge and face" and §5's "an operation may grow but never shrink" have no counterpart here.
This is the same gap [`truck-fornjot.md`](truck-fornjot.md) records for both Rust kernels and is
recorded in [`problems.md`](problems.md) P-24.

### The boolean: imprint, then classify, then refuse if anything is unclear

`combine(a: Body, b: Body, how: Operation, tolerance: f64) -> Result<Body, Snag>`
([`brep/boolean.rs#L53`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/boolean.rs#L53)).
Both bodies are imprinted with the curves they share, after which every face is wholly inside or
wholly outside the other, and the operation reduces to a selection
([`#L1-L16`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/boolean.rs#L1-L16)).
This is the OCCT/`BOPAlgo` family, not a mesh CSG. A shared wall is decided by the two faces'
normals rather than by a containment test, because it is on both sides
([`#L83-L91`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/boolean.rs#L83-L91)).

Failure is a **typed refusal**, three variants
([`brep/imprint.rs#L29-L40`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/imprint.rs#L29-L40)):
`NoClosedForm` (two faces meet along something with no closed form), `Coincident` (two faces on one
surface, whose overlap needs a parameter-space operation of its own), `CutRefused` (a cut crossing
a boundary more than twice, or closing inside the face). The module says why:

> A boolean that half-works produces a solid — one with a wall missing, which looks finished, saves,
> and fails much later in something else's hands. […] Refusing is cheap; a leaking solid is not.

([`brep/boolean.rs#L18-L24`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/boolean.rs#L18-L24))

Contrast with the other Rust B-rep kernel in this directory: `truck-shapeops` panics on shared-face
and shared-edge input ([`truck-fornjot.md`](truck-fornjot.md) §Truck, Booleans;
[`problems.md`](problems.md) P-29). cadkernel returns `Err(Snag::Coincident)` for the same input
class. **Zero `extern "C"`, zero `#[no_mangle]`, zero `#[repr(C)]`, zero `crate-type` override**
across cadkernel (*source count*, one `grep` over `src`, `Cargo.toml` and `crates/`, no matches) — a
pure rlib, like Truck and Fornjot.

**Exact predicates: absent, and known to be absent.** The README's own forward-looking dependency
table lists `robust` — "exact orientation predicates — classification is where naive kernels break"
— as intended but not yet added, together with `rstar` (candidate pruning), `iTriangle` and `curvo`
([`README.md#L115-L124`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/README.md#L115-L124)).
Classification today is tolerance comparison, which is exactly the root cause
[`problems.md`](problems.md) P-01 names.

### Threading and scale

**Single-threaded by design.** *source count*: `grep -rn 'rayon\|thread\|par_iter\|Mutex\|Arc<'` over
`src` returns **one** match, and it is the word "thread" in a sentence about threading a `Frame`
through recursion ([`geom2d/frame.rs#L32`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/frame.rs#L32)).
`Body` is `Clone`, so parallelism is the caller's to arrange.

The imprint's face pairing is an **O(|faces A| × |faces B|) nested loop** with a per-pair AABB
overlap reject, and the face bounds themselves are computed by sampling each coedge's curve
([`brep/imprint.rs#L212-L227`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/imprint.rs#L212-L227),
`face_bounds` at [`brep/bounds.rs#L104-L147`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/bounds.rs#L104-L147)).
There is no spatial index in the crate; the README lists one as intended. For the wall-with-twelve-
openings shape of BIM work this is the term that grows.

---

## 2. Provenance and the ACIS bridge — the part that has no counterpart in our spec

`Provenance` is `Clean(SourceRef) | Dirty(SourceRef) | Synthesized`, on **every** B-rep node
([`brep/mod.rs#L124-L153`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/mod.rs#L124-L153)).
`is_reusable()` is true only for `Clean`; `soil()` demotes `Clean` to `Dirty` on edit. The purpose,
from the crate README:

> Lowering writes clean nodes back as their original bytes, so attributes, parameter-space curves and
> surface types the kernel does not model survive an edit that did not touch them. Only dirtied and
> newly built nodes are re-emitted. Without this, one boolean rewrites every body in the file and
> quietly drops whatever the kernel cannot express.

([`README.md#L67-L73`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/README.md#L67-L73))

The bridge is `acis::lift(&SatDocument) -> (Vec<Body>, Loss)` and `acis::append(&Body, &mut SatDocument)`
([`acis/mod.rs#L10-L14`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/acis/mod.rs#L10-L14)),
where `Loss` is **itemised, not a boolean**: `surfaces: Vec<usize>`, `curves: Vec<usize>`,
`broken: Vec<usize>` — record indices whose surface kind, curve kind, or pointer graph the kernel
could not take ([`acis/lift.rs#L27-L41`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/acis/lift.rs#L27-L41)).
A caller can tell the user *which records* the kernel could not take, by index, before it edits or writes anything.

The same module rebuilds parametric solids from the drawing's own ACIS history records:
`rebuild_history`, `rebuild_body`, `rebuild_extrusion_with_mode`, `rebuild_sweep_with_mode`,
`rebuild_loft_with_options` ([`acis/mod.rs#L11-L12`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/acis/mod.rs#L11-L12)).
OCS drives these from grips and the properties panel — `src/scene/model/solid_history.rs` is 4,134
lines of grip and property definitions over `SolidHistoryBox`/`Cone`/`Cylinder`/`Loft`/`Revolve`/
`Sweep`/`Fillet`/`Chamfer`/`Brep` records
([`solid_history.rs#L1-L11`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/scene/model/solid_history.rs#L1-L11)).
Editing a box's length re-runs its history node; it is **re-evaluation of one element from stored
parameters**, not incremental evaluation of a dependency graph — there is no dependency graph in
cadkernel (*source*, no evaluation-graph or dirty-propagation type exists in `src`).

**The cost of this design, which is the note's sharpest warning.** OCS's document is a DWG, its
solids are ACIS records, and the kernel's topology is a cache lifted on demand
(`Scene::restore_solid_models` is called before every solid command that goes through
`selected_solid_handles` —
[`model_ops.rs#L508-L525`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/app/model_ops.rs#L508-L525)).
So a boolean that the kernel completes is **discarded** if the result cannot be lowered:

```rust
if crate::scene::convert::acis_export::solid_to_sat(&result).is_none() {
    self.command_line
        .push_error(crate::t!("The boolean result could not be encoded as ACIS.").as_ref());
    return Task::none();
}
```

([`model_ops.rs#L1237-L1241`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/app/model_ops.rs#L1237-L1241),
same guard again at [`#L1309-L1314`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/app/model_ops.rs#L1309-L1314)).
The file format's expressiveness gates the modeller. This is [`problems.md`](problems.md) **P-30**,
added by this note.

---

## 3. The GPU path

OCS renders through `iced`'s advanced custom-pipeline API on `wgpu` **29.0.4** (*source*,
`git show 798379fb:Cargo.lock`), the same generation [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md)
read (`wgpu-v29.0.1`). That note's wgpu column already covers what wgpu itself offers and is not
repeated here. What OCS adds is an **implementation of the two-float relative-to-eye scheme in
WGSL**, and that is new evidence for a section of `gpu-paths.md`.

The mesh vertex carries `position: vec3<f32>` and `position_low: vec3<f32>`; the instance carries
three model-matrix rows and its own `translation_low`
([`mesh.wgsl#L101-L125`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/shaders/mesh.wgsl#L101-L125)).
The vertex stage differences both halves against the camera's encoded position:

```wgsl
return (world_high - u.eye_high) + (world_low - u.eye_low);
```

([`mesh.wgsl#L151-L167`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/shaders/mesh.wgsl#L151-L167)).
The split is made once on the CPU when the kernel's f64 tessellation is packed
([`solid_model.rs#L417-L430`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/scene/model/solid_model.rs#L417-L430)),
with the comment "the renderer holds each position as a coarse float plus a fine correction, so a
survey coordinate keeps its last millimetres instead of losing them to f32".

[`gpu-paths.md`](../renderers/gpu-paths.md) §"Camera-relative rendering: what it actually requires"
identifies two families — OCCT and Filament fold the f64 translation into the view matrix before
truncation, Cesium splits each coordinate into two f32 attributes and differences them in the vertex
shader. **OCS is a third production implementation, in the Cesium family, and it is the first one in
this research written against wgpu/WGSL rather than GL.** Its refinement over Cesium is that the
*instance* translation also carries a low half, so the scheme survives instancing — which Cesium's
cited shader does not have to handle. This does not change `gpu-paths.md`'s conclusion (the
OCCT/Filament fold is cheaper for our case because our tiles already exist); it removes the residual
doubt that the two-float family is implementable on a modern explicit API.

Depth is `TextureFormat::Depth32Float` on every pipeline (*source*, `git grep Depth32Float`).

**Picking is CPU, with no GPU readback anywhere** — *source*, `git grep 'copy_texture_to_buffer\|map_async' 798379fb -- src`
returns nothing. A click builds a world-space ray, rejects each mesh on its AABB, then scans that
mesh's triangles linearly
([`pick/hit_test.rs#L840-L885`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/scene/pick/hit_test.rs#L840-L885)).
The spatial broad phase that does exist (`pick/interaction_index.rs`, XY grids and projected BVHs)
is for **wire** sets, by its own module doc
([`interaction_index.rs#L1-L6`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/scene/pick/interaction_index.rs#L1-L6));
meshes get an AABB and nothing more.

---

## 4. DWG/DXF, and STEP

The DWG/DXF layer is **not OCS's** — it is `cadcodec`, package `acadrust` 0.5.5, MPL-2.0
([`Cargo.toml#L1-L12`](https://github.com/HakanSeven12/cadcodec/blob/70ac6da7cf149cea6398a3d8829dd5e48b485b96/Cargo.toml#L1-L12)).
Its README *claims* DXF R12–R2018+ ASCII and binary, DWG R13–R2018+, and 41 entity types
([`README.md`](https://github.com/HakanSeven12/cadcodec/blob/70ac6da7cf149cea6398a3d8829dd5e48b485b96/README.md)).
Those figures are **claimed**, from the project's own README; no round-trip measurement was made
here, and OCS's issue tracker carries reports against them (§Documented failure modes).

STEP export is OCS's own and is **faceted**: `build_step(meshes: &[&MeshModel])` emits one
`ADVANCED_FACE`/`PLANE` per triangle into a single `CLOSED_SHELL`/`MANIFOLD_SOLID_BREP`, from
`MeshModel::verts`, which is the **high** `f32` half only — `verts_low` is never read by the
exporter (*source*, `grep -n verts_low src/io/step.rs` → no matches), and coordinates are printed
with `{:.6}`. The module says so itself: "Because building full B-Rep topology from a triangle soup
is complex, we use a simplified encoding". Read at
[`src/io/step.rs`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/io/step.rs)
(lines 1–13 for the statement, 110 for the point emission, 196–202 for the shell). A STEP file from
OCS is a mesh wearing B-rep clothing, at f32 precision. It is not a route for exact geometry out of
the application, and it is unrelated to cadkernel's exact ACIS path.

---

## 5. Documented failure modes, and what each traces back to

**How the tracker was counted.** *source count*: `gh issue list -R HakanSeven12/OpenCADStudio --state all
--limit 1000` → **815 issues** (144 open). Of those, **45 have a title matching**
`\b(solid|boolean|union|subtract|intersect|extrude|revolve|loft|sweep|fillet|chamfer|brep|b-rep|acis|nurbs|3d|mesh|tessellat|precision|tolerance|slice|presspull|volume)\b`
(case-insensitive) — **12 open, 33 closed**. The regex is the rule; a title-only match under-counts
geometry issues whose titles are generic, and that is its known bias.

| Issue | Reporter (`author_association`) | State | What it shows | Traces to |
|---|---|---|---|---|
| [#816 "Solid operations issue"](https://github.com/HakanSeven12/OpenCADStudio/issues/816) | `jaisekjames` (`NONE`) | open since 2026-08-19 | A user reports union/subtract refusing. The only comment on the thread is the repository's Patreon bot; **no maintainer reply, no file attached**, so the refusal cannot be attributed to a `Snag` variant from the thread | The boolean's refusal policy meeting a user with no way to learn which of three reasons applied — see P-30's second half |
| [#1020 "Faulty solid in DWG"](https://github.com/HakanSeven12/OpenCADStudio/issues/1020) | `schoeller` (`CONTRIBUTOR`) | open since 2026-09-05 | Reporter *states* that a `BOX` saved by OCS v0.9.8 makes two other CAD applications report `"Object improperly read <AdDbShBox> (64)"`, and that reopening in OCS works. A sample file is attached | The ACIS lowering path, or cadcodec's DWG writer. **Not diagnosed here.** Four of the thread's comments (roughly 44,000, 17,000, 15,000 and 15,000 characters) are pasted output of a third-party AI tool comparing two files; that is a third party's analysis, not a source fact, and none of it is used as evidence in this note. The maintainer's only comment is 17 characters |
| [#561 "Connected geometry separates visually at extreme zoom levels"](https://github.com/HakanSeven12/OpenCADStudio/issues/561) | `UserDevtec` (`COLLABORATOR`) | closed same day, 2026-07-29 | Shared endpoints of connected lines visibly separate under deep zoom | Fixed by [`29b15535`](https://github.com/HakanSeven12/OpenCADStudio/commit/29b15535d737f5de995471c28bb4d84e88e93ec9) "Use stored topology vertices at tessellated curve boundaries so floating-point reevaluation cannot open gaps at extreme zoom." — a **distinct sub-cause of P-05**: not float width, but *re-deriving* a shared point independently on each side |
| [#1129 "Native NURBS Surface Modeling"](https://github.com/HakanSeven12/OpenCADStudio/issues/1129) | `klausbu` (`NONE`) | open since 2026-09-10 | A feature request for free-form surfacing | Matches cadkernel's stated boundary: analytic surfaces first, NURBS×NURBS intersection "a separate and much larger problem" ([`README.md#L97-L101`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/README.md#L97-L101)) — P-12 |
| [#1107 "Fillet3d and some others issues"](https://github.com/HakanSeven12/OpenCADStudio/issues/1107) | `RickkGO` (`NONE`) | open since 2026-09-09 | Four separate 3D-fillet defects reported against v2026.36, including a fillet that cannot be applied to intersecting edges | cadkernel's blend layer, whose scope note says corner blends where three or more meet are out ([`README.md#L92-L95`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/README.md#L92-L95)) |
| [#266](https://github.com/HakanSeven12/OpenCADStudio/issues/266), [#267](https://github.com/HakanSeven12/OpenCADStudio/issues/267) "Solids Geometry — dislocation, corruption" | `ZoomerHub` (`NONE`) | both closed within two hours, 2026-07-04 | Two real building models rendering with dislocated and corrupted solids, and further corruption after a save round trip. Both closed by the maintainer (`OWNER`) with "fixed" / "already fixed and will be available on 0.7.5" | Pre-cadkernel code (2026-07-04 predates cadkernel's first commit by five weeks), so these are **not evidence about the current kernel**; they are evidence that whole-building DWG solid sets are a routine source of geometry defects for this application |

**Closure discipline is a finding in itself.** #266, #267 and #561 were each closed within hours by
the maintainer with a one-word comment and, for #561, a referenced commit. #816 has sat open for
three weeks with only a bot comment. Neither pattern is a defect; together they say that the tracker
records what users hit, not a triaged root-cause history — so it cannot be mined for design causes
the way OCCT's and Blender's were.

---

## Evaluation

Scored against [`README.md`](README.md)'s criteria. The subject is split, because the answer is
different for each part.

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | Application **GPL-3.0-only**; `cadkernel`, `cadkernel-constraints` and `cadcodec` **MPL-2.0**. MPL-2.0 is file-level copyleft: linking from a differently licensed program is permitted and modifications to MPL-licensed files must be published (*claimed*, a reading of the licence text, not legal advice) | measured | `LICENSE` + `README.md#L39` (OCS); `Cargo.toml#L5` (cadkernel); `Cargo.toml#L7` (cadcodec); GitHub licence API on all three |
| **Representations held natively** | **One** — B-rep with five analytic surfaces plus NURBS. Mesh is export-only; no point cloud; no implicit. Mesh → B-rep exists only as `faceted_solid` | measured (source) | §1, the representation table |
| **Boolean robustness** | Imprint-then-classify, analytic surfaces only, **typed refusal** (`NoClosedForm`/`Coincident`/`CutRefused`) instead of an approximate result. **No exact predicates** — classification is tolerance comparison; `robust` is listed as intended, not present | measured (source) | `brep/boolean.rs`, `brep/imprint.rs#L29-L40`, cadkernel `README.md#L115-L124` |
| **Tolerance and precision model** | **f64 throughout, zero f32.** Operation tolerance derived as `extent·1e-8 + ε·coordinate_scale·64`. Translation-only local frame lifted at every entry point. **No per-entity tolerance.** Scattered module constants from 1e-14 to 1e-4 | measured (source) | `brep/bounds.rs#L163-L183`; `geom2d/frame.rs`; `grep` for `f32` → 5 comment-only matches |
| **Incremental evaluation** | Not in the kernel — no dependency graph, no dirty propagation. At the application level, a solid is re-evaluated from its stored ACIS history record when a grip or property changes (`acis::rebuild_history`). Whole-body rebuild, not incremental | measured (source) | `acis/mod.rs#L11-L12`; OCS `solid_history.rs`; absence verified by grep over cadkernel `src` |
| **Threading model** | **Single-threaded by design** — one match for any of `rayon`/`thread`/`par_iter`/`Mutex`/`Arc<` anywhere under `src/`, and it is a comment. `Body: Clone`, so parallelism is the caller's | measured | `grep -rn 'rayon\|thread\|par_iter\|Mutex\|Arc<' --include=*.rs src` → 1 |
| **GPU path** | wgpu 29.0.4 through `iced`. f64 → (high f32, low f32) split on the CPU, differenced against the camera in WGSL; per-instance `translation_low` so the scheme survives instancing. `Depth32Float`. **Picking is CPU**: per-mesh AABB then a linear triangle scan; zero GPU readback | measured (source) | §3; `mesh.wgsl#L101-L167`; `pick/hit_test.rs#L840-L885`; `git grep copy_texture_to_buffer` → none |
| **IFC coverage** | None in either crate. cadkernel's README names `acadifc` as a **sibling consumer** that would reach into `brep` and `geom2d` the same way an editor does, and forbids the reverse edge | measured (source) | cadkernel `README.md#L28-L56` |
| **Performance** | **Not measured** — see §Measurements. The one structural fact established from source: the imprint's face pairing is O(n·m) with an AABB reject and no spatial index | not measured / measured (source) | §Measurements; `brep/imprint.rs#L212-L227` |
| **Embeddability** | Pure Rust rlib. **Zero `extern "C"`, zero `#[no_mangle]`, zero `#[repr(C)]`** in cadkernel; OCS's only exported C ABI is the DWG thumbnailer and the plugin `ocs_plugin_register` — nothing geometric. An in-process DynLex↔Rust boundary would be entirely ours to write | measured | `grep` over cadkernel `src`+`Cargo.toml`+`crates`; `git grep 'pub extern "C" fn' 798379fb -- src crates` |
| **2D derivation** | `brep::mesh::silhouette` / `transform_silhouette` produce view-dependent silhouettes; `tessellate_wireframe` produces `BodyWireframe`. Hidden-line and section are the application's (`solid_section`, `solid_flatshot` in OCS) | measured (source) | `brep/mesh.rs#L444-L470`, `#L614-L626`, `#L959`; OCS `model_ops.rs` |
| **Maturity** | cadkernel: first commit **2026-08-08**, 336 commits, **34 days old**, two contributors (`HakanSeven12` 202, `ramox81` 134), **no tags, no crates.io release** — consumed by git rev. OCS: created 2026-03-22, 1,557★, 815 issues, latest release `v2026.36` (2026-09-06), 27 contributors with `HakanSeven12` 2,456 to `ramox81` 362 and 25 below that | measured | `git rev-list --count`, `git log --reverse`, `git tag`, `gh api .../contributors`, `gh release list` |
| **AI familiarity** | Effectively zero public corpus: cadkernel is five weeks old with 5 stars; OCS is six months old. Both are far outside any training set that predates them. One column, never a tiebreaker (R-09) | inferred | Repository creation dates and star counts above |

---

## Measurements

**No benchmark driver was run, and no number in this note comes from running OCS or cadkernel.**

**Why not, precisely.** Two reasons, and only the first is about the software:

1. **The subject would partly be someone else's.** cadkernel exposes exactly what a driver needs —
   `brep::make::faceted_solid(vertices, faces)` to build the torture set's triangle operands,
   `brep::combine(a, b, how, tolerance)` for the operation, `Body::validate() -> Vec<Flaw>` and
   `brep::analytic_mass_properties` beside our own signed volume. Wiring a spike against it by git
   revision is a normal afternoon's work, and it **would** be a measurement of cadkernel. It would
   not be a measurement of "OCS's geometry", because OCS's own contribution to the boolean is a dozen
   lines of enum mapping and a call to `brep::operation_tolerance`
   ([`solid_model.rs#L385-L404`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/scene/model/solid_model.rs#L385-L404)).
2. **The environment refused every build command.** `cargo build --release` on a probe crate was
   denied by this session's command policy, in both available shells, before any code was compiled.
   That is a fact about this session, not about OCS, and it is recorded here rather than dressed up
   as a design reason. No partially-wired driver has been committed: a driver that never ran is
   worse than none, because the `results/` convention in [`../../../spikes/boolean-torture/`](../../../spikes/boolean-torture/)
   implies that a file there was produced by a run.

Consequently **every behavioural claim in this note is labelled *source* or *source count* — read
from the code at a pinned commit — or *claimed*, never *measured* in the sense the sibling notes use
for a driver result.** `spikes/boolean-torture/FINDINGS.md` and `spikes/precision-set/FINDINGS.md` are
unchanged by this note.

### The one thing that could be established without running anything

cadkernel's operation tolerance is a closed-form function of the operands' coordinates, so its
behaviour on the **precision set** can be derived rather than measured. Applying
`extent·1e-8 + f64::EPSILON·coordinate_scale·64` (with both terms floored at 1.0, per
[`brep/bounds.rs#L163-L183`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/bounds.rs#L163-L183))
to the three cases in [`../../../reference/precision_set.py`](../../../reference/precision_set.py)
at the origin and at its `OFFSET` of (500 km, 500 km, 0):

| Case | Extent | Tolerance at origin | Tolerance at 500 km | Ratio |
|---|---|---|---|---|
| `overlap_half` | 1.5 | 1.500e-8 | 2.211e-8 | ×1.474 |
| `coplanar_faces` | 2.0 | 2.000e-8 | 2.711e-8 | ×1.355 |
| `wall_with_openings` | 10.0 | 1.000e-7 | 1.071e-7 | ×1.071 |

*Inferred* — arithmetic on the cited formula and the committed benchmark coordinates, not a run of
the kernel. Reproducible from the repository root with:

```bash
cd reference && python -c "
import boolean_torture_set as t
cs = {c.name: c for c in t.cases()}
EPS = 2.220446049250313e-16
for n in ('overlap_half', 'coplanar_faces', 'wall_with_openings'):
    c = cs[n]; v = list(c.a.vertices) + list(c.b.vertices)
    ext = max(1.0, max(max(p[i] for p in v) - min(p[i] for p in v) for i in range(3)))
    s0 = max(1.0, max(abs(p[i]) for p in v for i in range(3)))
    s1 = max(abs(p[i] + d) for p in v for i, d in zip(range(3), (5e5, 5e5, 0.0)))
    print(n, ext*1e-8 + EPS*s0*64, ext*1e-8 + EPS*s1*64)"
```

**What this does and does not show.** It shows that the *declared* metric threshold grows by a
bounded factor of 1.07–1.47 over a 500 km translation — a designed, visible degradation rather than
a silent one, and one that stays four to five orders of magnitude below a millimetre. It shows
nothing about whether the boolean *produces the same geometry* at both positions, which is what
R-16's precision criterion actually asks and what only a driver can answer.

### The experiment that would settle it

Per [`_template.md`](../_template.md), naming it rather than writing "more research needed":

> **Spike `boolean-torture/ocs_driver` and `precision-set/ocs_driver`** — a Rust crate depending on
> `cadkernel` at `953d546b…` with `features = ["brep"]`, building each benchmark operand through
> `brep::make::faceted_solid`, running `brep::combine` for union and intersection with
> `brep::operation_tolerance` (the value OCS passes) and, as a second setting, a fixed 1e-9,
> rebuilding operands per repeat, validity from the driver's own closed/manifold/zero-area check
> cross-checked against `Body::validate()`, volume from the driver's own signed-volume function
> cross-checked against `analytic_mass_properties`, median of five. Same columns as the four sibling
> result files. **Pass/fail:** unchanged, R-16 as written.
> **Blocked on:** permission to run `cargo` in this environment. Nothing else.

This belongs in [`../../risks.md`](../../risks.md) R-16's candidate list; it is not added there by this note.

---

## The twelve questions

1. **Re-evaluate one changed element without reprocessing the model?** At the application level yes,
   from stored ACIS history parameters — change a box's length, `acis::rebuild_body` rebuilds that
   body. In the kernel, no: there is no dependency graph, and `combine` takes bodies by value and
   clones them. *source*.
2. **IFC round trip?** Not applicable — no IFC in either crate. The **ACIS** round trip is
   unusually good and is the transferable idea: clean nodes lower back as their original bytes, and
   `Loss` itemises every record the kernel could not take. *source*.
3. **Driven in-process from DynLex, without a subprocess or a file?** Only by writing the boundary
   ourselves. Zero C ABI exists anywhere in cadkernel. Same answer as Truck and Fornjot. *source count*.
4. **Threading model, and what is single-threaded by design?** All of it. One threading-related token
   in the 50,956 lines of `src/`, and it is in a comment. *source count*.
5. **What breaks first at scale?** Evaluation time in the imprint: O(|faces A| × |faces B|) pair
   testing with only an AABB reject and no spatial index, and face bounds obtained by sampling
   curves. Second, mesh picking, which is linear in the triangles of every mesh whose box the ray
   hits. *source*; neither has been timed.
6. **Internal numeric precision, configurable?** f64, not configurable, and there is no f32 path to
   fall into. Tolerance is a per-call `f64` argument, with a derived default. *source*.
7. **Operate on a subset — one tile, one region? (R-14)** No tiling; the unit of work is a `Body`.
   But the per-operation local frame means an operation on a distant body is already conditioned as
   if it were at the origin, which is most of what R-14 wants from a kernel. *source*.
8. **Who maintains it, and what if they stop?** One person with a second substantial contributor:
   cadkernel 202:134, OCS 2,456:362. Both repositories are 2026 creations; cadkernel is five weeks
   old and has never been released. If the author stops, an MPL-2.0 fork is legally trivial and
   technically expensive — 57,643 lines with no external users to share the burden. *source count*.
   **Bus factor**, by [`gpu-paths.md`](../renderers/gpu-paths.md)'s rule (§Maturity and AI
   familiarity there): the smallest number of a repository's top contributors, from the GitHub
   `contributors` API's first page (10 entries, bot accounts excluded), whose summed contributions
   reach half the page's total. cadkernel: `HakanSeven12` (202) alone already exceeds half of
   202 + 134 = 336 (168) — **bus factor 1**. OCS: the note's own two named contributors
   (`HakanSeven12` 2,456, `ramox81` 362) are not enough on their own to apply the rule, since the
   remaining eight of the top ten are only described in aggregate ("25 below that"); the full
   first page, read the same way as `gpu-paths.md`'s table (*source*, `gh api
   repos/HakanSeven12/OpenCADStudio/contributors`, read 2026-09-11, dated like that table's own
   numbers): `HakanSeven12` 2,458, `ramox81` 362, `KarimJerbi` 105, `gianlucafiore` 86, `schoeller`
   75, `mechpanos` 67, `felixriestra` 25, `KevinGriffin-new` 21, `UserDevtec` 20,
   `NgoQuocViet2001` 17 — page total 3,236, half 1,618, and `HakanSeven12` alone (2,458) clears it —
   **bus factor 1**. Both kernels this note evaluates have the same bus factor as DynLex itself.
9. **Documented failure modes, with issue links, and the design choice each traces back to?**
   §Documented failure modes. The tracker is a young user-report stream, not a triaged root-cause
   history; the strongest causal chain in it is #561 → commit `29b15535` → P-05's re-derivation
   sub-cause. *source and tracker*.
10. **Which representations natively, and how does it convert?** One — B-rep — plus a one-way
    tessellation to mesh and one narrow mesh → B-rep entry (`faceted_solid`). §1. *source*.
11. **How does geometry reach the GPU and come back?** Out: f64 → (high f32, low f32) pairs
    differenced against the camera in WGSL, instanced, `Depth32Float`. Back: **it does not** —
    there is no readback of any kind; picking is CPU. §3. *source*.
12. **What would we take, and what would we avoid?** §Verdict.

---

## Strengths

- **The licence split is the single most useful fact in this note.** The application is GPL-3.0 and
  the geometry and file-format layers are MPL-2.0, in separate repositories, with the kernel
  depending on the codec and not the reverse. Someone has already done the separation work that
  usually has to be argued for after the fact.
- **A boolean that refuses is worth more than a boolean that mostly works**, and the three `Snag`
  variants are the taxonomy of *why*, not a bare error.
- **The local-frame invariant is stated as a contract with a stated failure mode**, not as a helper
  someone might remember to call.
- **Provenance solves a problem our spec has not addressed**: how an edit avoids rewriting — and
  silently degrading — everything the kernel does not model.
- Typed generational handles with a written justification that matches ours.
- f64 with no f32 anywhere, which is the disqualifier our README applies to *build on* and which
  cadkernel passes cleanly.

## Weaknesses

- **Five weeks old, no release, no tag, no crates.io publication**, consumed by git revision. Its own
  README opens with "Early. The structure and the invariants are settled; most of the operations are
  not written yet."
- **One representation of the four** the kernel spec wants, and no route to the other three.
- **No exact predicates.** Classification is tolerance comparison, which is the root cause
  [`problems.md`](problems.md) P-01 names; `robust` is a plan.
- **No per-entity tolerance**, so tolerant-modelling growth cannot be expressed.
- **No spatial index and no threading**, with an O(n·m) face pairing in the operation that matters
  most for BIM shapes.
- **Nothing about it is measured** — by us, and, as far as the repositories show, by anyone: there is
  no benchmark suite in either crate.
- OCS's STEP export is a triangle soup at f32; it is not a route for exact geometry out.

## Risks

- **A young single-author kernel can change shape under us.** 336 commits in 34 days, and its own
  scope note lists what is not written. Pinning a revision fixes the code and not the maintenance.
- **MPL-2.0 is file-level copyleft, not permissive.** Any file of cadkernel we modify must be
  published under MPL-2.0. That is a mild and acceptable obligation, but it is an obligation, and it
  applies per file to *modifications*, which is exactly the shape [`problems.md`](problems.md) P-14
  records for CGAL's per-package licensing.
- **The thing we would not find out until too late:** whether the imprint-then-classify boolean
  holds up on the torture set's coplanar, shared-edge and twelve-opening cases. The typed refusals
  make a failure *visible*, which is the good outcome; a kernel that refuses 4 of 10 benchmark cases
  is still a kernel we cannot ship a wall-opening tool on. This is precisely the gap that the spike
  above closes, and it is the reason this note's *build on* verdict is conditional rather than
  positive.

---

## Verdict

### Build on — answered separately for the three sub-projects

**(a) The kernel — `cadkernel` is the first genuine candidate this directory has produced for the
B-rep *layer*, and the verdict is conditional shortlist, not recommend.**

Concretely, what taking it would mean:

- **Which crates.** `cadkernel` with `features = ["brep"]` (which pulls `geom2d` and `spade`), optionally `acis` (which pulls `cadcodec`) and `offset` (which pulls
  `cavalier_contours`, version-pinned because the offset path reaches into its internals —
  [`Cargo.toml#L24-L41`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/Cargo.toml#L24-L41)).
  `cadkernel-constraints` is a workspace member of the same repository, depended on separately by OCS and not needed for the B-rep layer.
- **What it commits us to.** One representation, f64, no per-entity tolerance, no exact predicates,
  single-threaded, no spatial index. Our kernel spec's mesh, point-cloud and implicit
  representations (§4) and its exact-predicate rule (§5) would sit **beside** cadkernel, not inside
  it, and the four-representation `boolean(A, B, op)` dispatch of §4 would be ours with cadkernel
  filling one of its four arms.
- **The Rust ↔ DynLex boundary.** There is none and there is nothing to extend: **zero `extern "C"`,
  zero `#[no_mangle]`, zero `#[repr(C)]`, no `cdylib`** in the crate. The boundary would be a C ABI
  shim we write and maintain over `Body`, `Key<T>`, `Surface`, `Curve`, `Snag`, `Flaw`, `Loss` and
  the tessellation structs — an opaque-handle FFI with an error enum, plus a build of cadkernel as a
  `staticlib`. That is a real, ongoing cost on **our** side of a dependency whose API is five weeks
  old, and it is the same cost [`truck-fornjot.md`](truck-fornjot.md) priced for Truck. The
  difference is that here the API is small enough to wrap (`combine`, `imprint`, the `make`
  constructors, `tessellate`, `validate`, `lift`/`append`) and its error type is already `Result`.
- **The condition.** The spike in §Measurements. If cadkernel passes R-16 on the torture set, it is a
  serious *build on* candidate for the B-rep arm and this note should be revised to *recommend for
  that arm*. If it refuses several benchmark cases, it remains an excellent *borrow from* and the
  B-rep arm is ours — and we will have learned that from three typed refusals rather than from
  debugging a leaking shell, which is itself worth the spike.

ADR-0003 and ADR-0004 are both unaffected today: nothing here settles "build on an existing kernel"
either way, because the measurement that would settle it has not been run.

**(b) `ui/` — no on the code, yes on one design.**

OCS's renderer is GPL-3.0 and is welded to `iced` 0.14-git, whose custom-pipeline API it uses for
every pipeline. There is nothing here to take as a dependency: `ui/` is a DynLex Vulkan library and
OCS is a Rust `iced`/wgpu application. What transfers is §3's confirmation that the two-float
relative-to-eye scheme works on a modern explicit API **with instancing**, which removes a residual
doubt in [`gpu-paths.md`](../renderers/gpu-paths.md) without changing its recommendation. OCS's
CPU-only picking is a thing to avoid, not adopt.

DWG/DXF is different, and it is the second useful answer in this note: **`cadcodec` is MPL-2.0, is
already a standalone crate with no dependency on OCS or on the kernel, and claims DXF R12–R2018+ and
DWG R13–R2018+ read and write.** If DWG interoperability ever enters scope, it is the only
permissively licensed native-DWG implementation this research has encountered, and it should be
evaluated on its own terms — against its own round-trip claims, which this note has not tested and
against which OCS's tracker already carries reports (#1020).

**(c) `app/` — no, and the reason is instructive.**

OCS's command system, undo and scene caches are GPL-3.0 and are shaped around a DWG document. Two
things in them are worth knowing about rather than taking:

- **Entity-delta undo.** The `perf(undo)` commit in the clone's history replaced a full ~800k-entity
  document clone per edit (~46 ms) with a per-handle before/after record, a self-inverting
  `HistorySnapshot::Delta` that moves between undo and redo stacks without re-capturing, and a
  single `bump_entities` so the derived caches patch instead of re-tessellating
  ([`1490fe4e`](https://github.com/HakanSeven12/OpenCADStudio/commit/1490fe4ea91dd83498bc7c280e124a07f194c37f)).
  The design is right and the numbers in the commit message are the author's, *claimed*, not ours.
- **A per-edit render arena.** The preceding commit
  ([`aea1fd2c`](https://github.com/HakanSeven12/OpenCADStudio/commit/aea1fd2caa9ad8ec7486d7c669751e23ac64b50d))
  enables an in-place GPU wire arena by default and replaces a whole-document draw-order rescan with
  a walk of the recorded assembled order. Same status: the author's figures, *claimed*.

Both are the same lesson our spec §6 already states — patch derived state, do not rebuild it — now
with a second project having paid for it. Neither is a reason to depend on `app/`-layer code.

### Borrow from — pinned

1. **The typed refusal with a named cause.** `Snag::{NoClosedForm, Coincident, CutRefused}`
   ([`brep/imprint.rs#L29-L40`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/imprint.rs#L29-L40))
   and the rationale at [`brep/boolean.rs#L18-L24`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/boolean.rs#L18-L24).
   Kernel spec §12 already forbids aborting on user input; this adds the positive half — **the error
   must name which class of input defeated the operation**, because "boolean failed" is unactionable
   and the caller cannot recover a cause the kernel discarded. Spec §12 to be amended.
2. **Provenance.** `Clean(SourceRef) | Dirty(SourceRef) | Synthesized` on every node, with lowering
   reusing clean records byte-for-byte
   ([`brep/mod.rs#L124-L153`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/mod.rs#L124-L153)).
   **This is the best idea in this note.** It is the correct answer to "an edit to one wall must not
   silently rewrite the IFC representation of every other object", it is cheap (two words per node),
   and our spec does not have it. Proposed for spec §4 and for the `ifc/` sub-project.
3. **Itemised loss on import.** `Loss { surfaces, curves, broken }` as record indices
   ([`acis/lift.rs#L27-L41`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/acis/lift.rs#L27-L41)).
   Every format bridge we write should return this shape rather than a success flag.
4. **A scale- and position-derived operation tolerance.**
   `extent·1e-8 + ε·coordinate_scale·64` ([`brep/bounds.rs#L163-L183`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/bounds.rs#L163-L183)).
   ADR-0006 proposes a fixed 1e-6 m default. A fixed absolute default is wrong at both ends — too
   loose for a 10 mm detail, too tight for a 200 m span — and this formula is a concrete alternative
   to test. Note it is a *default*, not a replacement for the per-entity tolerance cadkernel lacks.
5. **`validate()` returning every flaw, not the first**, over a named enum
   ([`brep/topology.rs#L540-L562`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/brep/topology.rs#L540-L562)),
   with the doc comment's rule: run it after a lift so a malformed file is reported where it was read.
6. **The local frame as a stated contract** rather than a convenience
   ([`geom2d/frame.rs#L1-L33`](https://github.com/HakanSeven12/cadkernel/blob/953d546b68aef4b6692566a1a9b077fc5bd9fb4f/src/geom2d/frame.rs#L1-L33)),
   and specifically the **midpoint-of-bounding-box** anchor rule and the deliberate exclusion of
   rotation. An addition to spec §5, whose tiles are chosen for partitioning and not for
   conditioning.
7. **The shared-vertex rule at tessellation boundaries** — commit
   [`29b15535`](https://github.com/HakanSeven12/OpenCADStudio/commit/29b15535d737f5de995471c28bb4d84e88e93ec9):
   use the stored topology vertex at a tessellated curve's endpoints instead of re-evaluating the
   curve there. Cheap, and it removes a visible-gap class our tessellator would otherwise rediscover.

### Avoid — with the rows in `problems.md`

| Avoid | Why | Row |
|---|---|---|
| Letting the persistence format gate the modeller — a kernel result discarded because it cannot be lowered | OCS refuses a completed boolean when `solid_to_sat` returns `None` ([`model_ops.rs#L1237-L1241`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/app/model_ops.rs#L1237-L1241)) | **P-30** (new) |
| Tolerance-comparison classification without exact predicates | cadkernel's boolean classifies by tolerance; `robust` is planned, not present | P-01 |
| Re-deriving a shared point independently on each side of a boundary | OCS #561, fixed by using the stored topology vertex | P-05 |
| Promising curved-surface booleans the kernel cannot do | cadkernel refuses NURBS×NURBS by design and says so; the request arrives anyway (#1129) | P-12 |
| Assuming an application's licence is its libraries' | OCS is GPL-3.0; its kernel and codec are MPL-2.0 in separate repositories | P-14 |
| A typed error discarded at the application boundary | Two of six boolean call sites in `model_ops.rs` (`#L1229`, `#L1900`) use `solid_model::boolean`, which drops the `Snag`; the other four (`#L162`, `#L229`, `#L232`, `#L315`) propagate it via `boolean_result(...)?` to sites that match on all three variants and name the cause (`#L1055`, `#L1289`, `#L1542`, `#L1731`) | P-30, second half |
| Filling a format's exact-geometry entity types with tessellated f32 data | OCS's STEP writer emits one `ADVANCED_FACE` per triangle into a `MANIFOLD_SOLID_BREP`, from the renderer's high-half `f32` buffer ([`io/step.rs`](https://github.com/HakanSeven12/OpenCADStudio/blob/798379fbe0eb60025e4f4827441359aed812f5ff/src/io/step.rs)) — the fork that matters for `ifc/` is `IfcAdvancedBrep` vs `IfcFacetedBrep` | **P-31** (new) |

---

## Connection to hosts and engines

[`../hosts-and-engines/README.md`](../hosts-and-engines/README.md) lists "**Standalone — Rust core
with a separate UI layer**" as an untested candidate. Open CAD Studio is that candidate **built and
shipping**: a Rust core over `iced`/wgpu, one binary, a WASM build, DWG-native, six months old, with
1,557 stars and 815 issues from real users. It demonstrates that the shape works — that a Rust core
with a separate UI layer reaches a usable CAD application quickly, and that its geometry, file format
and application can be cleanly separated into three repositories with two licences. It does **not**
transfer to us as a host, for the reason that decides the whole hosts question: the core is Rust and
ours is DynLex, so "standalone — Rust core" as a *host* option would mean writing our application in
Rust, which is a different decision from the one this directory is researching. What OCS actually
supplies to that page is the counter-evidence to its own premise: the attractive part of the
"standalone Rust core" option is not the host at all, it is `cadkernel` and `cadcodec` — two MPL-2.0
libraries that can be linked from a standalone application in *any* language with a C ABI we write.
The host question and the kernel question, as that page says in its third line, are independent, and
OCS is the cleanest illustration of it this research has found.

---

## Sources

- [Open CAD Studio](https://github.com/HakanSeven12/OpenCADStudio) at [`798379fb`](https://github.com/HakanSeven12/OpenCADStudio/tree/798379fbe0eb60025e4f4827441359aed812f5ff) — GPL-3.0-only
- [cadkernel](https://github.com/HakanSeven12/cadkernel) at [`953d546b`](https://github.com/HakanSeven12/cadkernel/tree/953d546b68aef4b6692566a1a9b077fc5bd9fb4f) — MPL-2.0
- [cadcodec](https://github.com/HakanSeven12/cadcodec) (package `acadrust` 0.5.5) at [`70ac6da7`](https://github.com/HakanSeven12/cadcodec/tree/70ac6da7cf149cea6398a3d8829dd5e48b485b96) — MPL-2.0
- Issue tracker: [#266](https://github.com/HakanSeven12/OpenCADStudio/issues/266), [#267](https://github.com/HakanSeven12/OpenCADStudio/issues/267), [#561](https://github.com/HakanSeven12/OpenCADStudio/issues/561), [#816](https://github.com/HakanSeven12/OpenCADStudio/issues/816), [#1020](https://github.com/HakanSeven12/OpenCADStudio/issues/1020), [#1107](https://github.com/HakanSeven12/OpenCADStudio/issues/1107), [#1129](https://github.com/HakanSeven12/OpenCADStudio/issues/1129)
- Commits: [`29b15535`](https://github.com/HakanSeven12/OpenCADStudio/commit/29b15535d737f5de995471c28bb4d84e88e93ec9) (shared curve endpoints), [`aea1fd2c`](https://github.com/HakanSeven12/OpenCADStudio/commit/aea1fd2caa9ad8ec7486d7c669751e23ac64b50d) (render arena), [`1490fe4e`](https://github.com/HakanSeven12/OpenCADStudio/commit/1490fe4ea91dd83498bc7c280e124a07f194c37f) (entity-delta undo)
- Within this repository: [`truck-fornjot.md`](truck-fornjot.md), [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md), [`problems.md`](problems.md), [`../hosts-and-engines/README.md`](../hosts-and-engines/README.md), [`../../superpowers/specs/2026-09-09-geometry-kernel-design.md`](../../superpowers/specs/2026-09-09-geometry-kernel-design.md), [`../../../reference/precision_set.py`](../../../reference/precision_set.py)
