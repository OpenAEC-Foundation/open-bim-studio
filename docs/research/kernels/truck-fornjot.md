# Truck and Fornjot — small B-rep kernels in Rust

**Decision question:** Our kernel spec proposes a B-rep module with generational handles, a
per-entity tolerance model and exact predicates for topology (spec §4, §5, §6), written in DynLex.
Truck and Fornjot are the two well-documented from-scratch B-rep kernels written in Rust — small
enough to read whole, and both written without twenty years of accretion (Fornjot's own
documentation and repository are archived as of this note's pinned commit; see §Fornjot, below,
for what that means for this note's findings). This note answers:
**what does a clean B-rep data model look like when it is built once, in a memory-safe language,
rather than inherited — and where does each one stop (booleans, tolerances, maintenance)?**

**Serves:** ADR-0004 (build on vs. build our own — Rust is not DynLex, so the *build on* axis is a
check, not a real option); ADR-0005 (B-rep representation, tolerance model), kernel spec §4, §6;
`problems.md` P-02, P-04, and a new row P-29

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> Both candidates are read primarily for *borrow from* and *avoid*, per
> [`README.md`](README.md)'s listing ("useful for design clarity"), but the twelve questions are
> answered in full, including *build on*, because the README requires every note to.

---

## Summary

Truck and Fornjot both chose the same topology skeleton as OCCT — vertex/edge/wire/face/shell/
solid with an orientation flag rather than duplicated reversed geometry — but arrived at opposite
identity mechanisms: Truck gives every topological element a fresh `Arc<Mutex<_>>` per
construction call (identity is the allocation, sharing is `Arc::clone`, mutation is real and
visible to every clone), while Fornjot's objects hold no data at all and exist only to be
referenced through a `Handle` whose identity is its position in an **append-only** store — nothing
is ever freed, so a handle can never dangle, at the cost of never reclaiming memory. Neither has a
per-entity tolerance model: Truck has one global `TOLERANCE = 1.0e-6` constant used everywhere;
Fornjot has one process-wide `ValidationConfig` tolerance (default 0.001) from which two derived
distance thresholds are computed. Truck's boolean is real and tested but is documented as
transversal-only (no tangency) and panics via internal `.unwrap()` on some coincident-geometry
input rather than returning an error — three independent GitHub reports confirm this, one with a
maintainer-adjacent fix already published as a fork. Fornjot never shipped a 3D boolean at all:
issue #42 tracked partial implementation for one year and ten months before its owner closed it,
unresolved, as the whole repository was archived. Both are read for design, not to be built on.

## What was read, and at which commit

| Project | Pinned at | Commit | Obtained with |
|---|---|---|---|
| Truck | `master` HEAD, 2026-09-07 | [`8d03d8f7900d6aaff784d02092bf5126c1425749`](https://github.com/ricosjp/truck/tree/8d03d8f7900d6aaff784d02092bf5126c1425749) | `git clone --depth 1 https://github.com/ricosjp/truck.git`, confirmed with `git rev-parse HEAD` |
| Fornjot | `main` HEAD, 2026-06-19 | [`7e856686b8105d21ce4673c10622f6ef206b89af`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af) | `git clone --depth 1 https://github.com/hannobraun/fornjot.git`, confirmed with `git rev-parse HEAD` |

**Truck has no single repository-wide release tag** — *measured*, `git ls-remote --tags | grep -v
'\^{}' | wc -l` returns 73 tags, each `<crate>-v<version>`, cut independently per crate. The
CHANGELOG states "the version
is of the bottom crate `truck-rendimpl`"
([`CHANGELOG.md#L1-L3`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/CHANGELOG.md#L1-L3)),
and that tag, `truck-rendimpl-v0.6.0`, is dated 2024-09-20 — two years stale against a workspace
that commits weekly through the date this note was written. `master` was read instead, disclosed
rather than silently substituted, so the findings below reflect the code as it is today.

**Fornjot's own README carries a shutdown notice at the pinned commit**: "This project has been
shut down. Its goals were never reached"
([`README.md#L1`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/README.md#L1)).
The repository is archived on GitHub — *measured*, `gh api repos/hannobraun/fornjot --jq
.archived` → `true`. The last version tag is `v0.49.0`, 2024-03-21; `main` HEAD (the pinned commit)
is three months more recent but is a documentation-only commit to the warning banner, "Make
warning signs bold too" — *measured*, `git log --oneline`. `crates/fj-core` is a deprecated stub:
"This library has been deprecated. Its contents have moved into `fj`"
([`fj-core/src/lib.rs#L1-L9`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj-core/src/lib.rs#L1-L9)) —
so this note reads the `fj` crate's `src/core/` tree, where the topology, storage and validation
code the brief asks for now actually lives.

| Area | Truck path | Fornjot path |
|---|---|---|
| Topology elements | [`truck-topology/src/lib.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/lib.rs) | [`crates/fj/src/core/topology/objects/`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects) |
| Handles / object identity | [`truck-topology/src/lib.rs#L221`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/lib.rs#L221) (`VertexID`) | [`crates/fj/src/core/storage/handle.rs`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs), [`store.rs`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/store.rs), [`blocks.rs`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/blocks.rs) |
| NURBS curves/surfaces | [`truck-geometry/src/nurbs/`](https://github.com/ricosjp/truck/tree/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-geometry/src/nurbs) (bspcurve.rs, bspsurface.rs, nurbscurve.rs, nurbssurface.rs, knot_vec.rs) | none — see §Geometry layer |
| Builder API | [`truck-modeling/src/builder.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-modeling/src/builder.rs) | [`crates/fj/src/core/operations/`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/operations) (`build/`, `sweep/`) |
| Tessellation | [`truck-meshalgo/src/tessellation/`](https://github.com/ricosjp/truck/tree/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-meshalgo/src/tessellation) | not applicable — no working solid to tessellate at this commit (§Operations) |
| Boolean (`and`/`or`) | [`truck-shapeops/src/transversal/integrate/mod.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/integrate/mod.rs) | none shipped — see §Operations |
| Tolerance constant / config | [`truck-base/src/tolerance.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/tolerance.rs) | [`crates/fj/src/core/validation/config.rs`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs) |
| Validation | not a separate module — `BoundingBox`/`Result` checks inline | [`crates/fj/src/core/validate/`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validate), [`crates/fj/src/core/validation/`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation) |
| Precision type | [`truck-base/src/cgmath64.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/cgmath64.rs) | [`crates/fj/src/core/math/scalar.rs`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs) |
| Licence | [`LICENSE`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/LICENSE) (Apache-2.0) | [`LICENSE.md`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/LICENSE.md) (0BSD) |

## Truck

### Crate layout

A Cargo workspace of 15 published crates plus tooling
([`Cargo.toml#L1-L21`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/Cargo.toml#L1-L21)):
`truck-base` (tolerance, generic-precision math types), `truck-geometry` (NURBS curves/surfaces),
`truck-topology` (the B-rep graph), `truck-modeling` (the builder API — vertex/line/circle_arc,
`tsweep`/`rsweep` for extrude/revolve —
[`builder.rs#L484`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-modeling/src/builder.rs#L484),
[`#L596`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-modeling/src/builder.rs#L596)),
`truck-polymesh` (the mesh type and OBJ/STL IO), `truck-meshalgo` (tessellation and mesh
analysis/filtering), `truck-shapeops` (boolean `and`/`or`, healing, fillet), `truck-stepio` (STEP
read/write), `truck-platform`/`truck-rendimpl` (wgpu rendering), `truck-js` (WASM bindings). All
NURBS, tessellation and topology types are generic over `f64` via `truck-base`'s `cgmath64`
wrapper, which re-exports `cgmath`'s vector/point/matrix types instantiated at `f64`
([`cgmath64.rs#L9`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/cgmath64.rs#L9))
— *measured*, there is no float32 path anywhere in the workspace's geometry crates.

### Topology: shared allocation, not shared handles

Truck's six topological structs, read whole and reformatted here onto one line each (fields and
types unchanged, nothing added or removed)
([`truck-topology/src/lib.rs#L109-L176`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/lib.rs#L109-L176)):

```rust
pub struct Vertex<P> { point: Arc<Mutex<P>> }
pub struct Edge<P, C> { vertices: (Vertex<P>, Vertex<P>), orientation: bool, curve: Arc<Mutex<C>> }
pub struct Wire<P, C> { edge_list: VecDeque<Edge<P, C>> }
pub struct Face<P, C, S> { boundaries: Vec<Wire<P, C>>, orientation: bool, surface: Arc<Mutex<S>> }
pub struct Shell<P, C, S> { face_list: Vec<Face<P, C, S>> }
pub struct Solid<P, C, S> { boundaries: Vec<Shell<P, C, S>> }
```

Orientation is a `bool` on `Edge` and `Face` — the reversed direction shares the same `Arc`-held
geometry, exactly the OCCT/kernel-spec pattern of an orientation flag rather than duplicated
geometry. **Identity is the allocation, not a value.** `Vertex::new()` (and `Edge::new`,
`Face::new`) allocate a fresh `Arc<Mutex<_>>` every call, "even if the end vertices are the same
one" for two edges — the doc-tested example constructs `edge0`/`edge1` between the same two
vertices and asserts `edge0.id() != edge1.id()`
([`lib.rs#L113-L124`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/lib.rs#L113-L124) —
the doc-comment quote is at L116, the `assert_ne!` at L123).
`id()` is `ID::new(Arc::as_ptr(&self.point))`
([`vertex.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/vertex.rs), method `id`),
so identity is the pointer, sharing is `Arc::clone`, and — unlike Fornjot — the geometry **is
mutable in place**: `Vertex::set_point` writes through the `Mutex` and every clone observes the
new value immediately (doc-tested at
[`vertex.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/vertex.rs), method `set_point`).
This is the opposite identity model from generational handles: there is no index, no generation,
no arena — identity, sharing and mutation are all folded into one `Arc<Mutex<_>>` per element, and
the type system (not a runtime check) prevents a dangling reference, at the cost of a lock on every
geometry read.

**A second, explicitly separate representation exists for exchange.** `truck-topology::compress`
states its own rationale: the live `Arc<Mutex<_>>` graph "is not suitable for direct serialization
and must be converted to lighter and simpler data structures"
([`compress.rs#L1-L9`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/compress.rs#L1-L9)).
`CompressedShell<P, C, S>` holds flat `Vec<P>`/`Vec<CompressedEdge<C>>`/`Vec<CompressedFace<S>>`,
with edges referencing vertices by `usize` index and faces referencing edges by
`{index, orientation}` pairs
([`compress.rs#L17-L91`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/compress.rs#L17-L91))
— an index-addressed, structure-of-arrays-shaped format explicitly kept separate from the editable
graph, converted in both directions. This is a working, shipped precedent for exactly the
live-graph/exchange-format split our kernel's `io/` module needs (spec §7).

### Geometry: NURBS, no analytic-surface shortcut visible at this layer

`truck-geometry::nurbs` holds B-spline/NURBS curve and surface types — *measured*, `wc -l`:
`bspcurve.rs` (`BSplineCurve`) 1,406, `nurbscurve.rs` (`NurbsCurve`) 561, `bspsurface.rs`
(`BSplineSurface`) 2,041, `nurbssurface.rs` (`NurbsSurface`) 889, `knot_vec.rs` (`KnotVec`) 717 —
with evaluate, derivative, closest-point and split operations. `truck-geometry`
does not itself hold OCCT-style analytic primitives as their own types; `truck-modeling::
geom_impls` builds plane/cylinder/cone/sphere shapes as `RevolutedCurve`/`ExtrudedCurve` wrappers
over line and circle-arc curves instead
([`geom_impls.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-modeling/src/geom_impls.rs)) —
a swept-curve representation of what the kernel spec (§4) treats as distinct analytic surface
types. Not independently verified for evaluation cost; recorded as inferred from the module
layout, not measured.

### Tolerance: one global constant, not per-entity

```rust
pub const TOLERANCE: f64 = 1.0e-6;
pub const TOLERANCE2: f64 = TOLERANCE * TOLERANCE;
pub trait Tolerance: AbsDiffEq<Epsilon = f64> + Debug {
    fn near(&self, other: &Self) -> bool { self.abs_diff_eq(other, TOLERANCE) }
    fn near2(&self, other: &Self) -> bool { self.abs_diff_eq(other, TOLERANCE2) }
}
```
— [`truck-base/src/tolerance.rs#L6-L17`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/tolerance.rs#L6-L17),
*measured* by reading the whole 130-line file. `TOLERANCE` is a single process-wide `f64`
constant, blanket-implemented for every type that satisfies `AbsDiffEq<Epsilon = f64>`
([`#L20`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/tolerance.rs#L20))
— there is no per-vertex, per-edge or per-face tolerance field anywhere in the `Vertex`/`Edge`/
`Face` structs quoted above, and no way to raise or lower it for one entity or one operation
without recompiling. This answers question 6 directly: f64, and the constant is not overridable
per call. `and`/`or` (below) do take a `tol: f64` parameter, so *boolean* tolerance is at least
per-call, but nothing propagates it back onto the resulting shapes' geometry the way OCCT's
per-entity tolerance does — there is no entity-level tolerance to propagate into.

Coincidentally, `TOLERANCE = 1.0e-6` is the same number as ADR-0006's default linear tolerance
(1e-6 m) and one decade looser than OCCT's `Precision::Confusion()` (1e-7,
[`occt.md`](occt.md) §Tolerance model) — worth noting as a data point on what "reasonable default"
means across three independent kernels, not as evidence either way for ADR-0006's choice.

### Booleans: transversal only, and they can panic

The crate's own doc comment states the boolean's scope directly: "Boolean operations are currently
supported only for shapes where faces intersect transversally. Cases where faces are tangent to
each other are not yet supported"
([`truck-shapeops/src/lib.rs#L5-L9`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/lib.rs#L5-L9)),
and fillet is scoped just as narrowly: "a single edge whose end vertices are each adjacent to
exactly three faces. Continuous edges are currently unsupported"
([`#L11-L14`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/lib.rs#L11-L14)).
Only `and` and `or` are public
([`transversal/mod.rs`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/mod.rs)) —
difference is not a third function; it is expressed as `and(a, b.not())`, where `Solid::not`
inverts every face's orientation in place
([`truck-topology/src/solid.rs#L81`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/solid.rs#L81)).
Both return `Option<Solid<...>>`, with `tol: f64` as an explicit per-call parameter
([`transversal/integrate/mod.rs#L135-L155`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/integrate/mod.rs#L135-L155),
[`#L158-L178`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/integrate/mod.rs#L158-L178))
— failure is `None`, with **no message and no offending handles**, unlike the kernel spec's §12
result-value-with-message contract.

**The panic is a tracker finding, not source-reading speculation.**
[Issue #128](https://github.com/ricosjp/truck/issues/128) (`NONE`, `stefangolas`) reports STEP
files that panic during tessellation with a misleading message ("tolerance must be no less than
1e-6") that is actually a `NaN` transform propagating from a degenerate `Axis2Placement3d` (axis
parallel to `ref_direction`, so Gram-Schmidt normalizes a zero vector). `CONTRIBUTOR` `virtualritz`
confirms the same root cause independently with a proposed fix, and cross-links
[#123](https://github.com/ricosjp/truck/issues/123) as the same defect reported earlier by a third,
`NONE`-association reporter (`yuunnn-w`). Separately,
[#114](https://github.com/ricosjp/truck/issues/114) (`NONE`, `LdotJdot`) reports `and`/`or`
panicking outright (not returning `None`) on solids with a shared face or shared vertex/edge.
**Verified in source, not only from the tracker:** `and` and `or` each call `.unwrap()` on the
first element of the input solids' boundary iterators before any tolerance-based work begins
([`transversal/integrate/mod.rs#L142-L143`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/integrate/mod.rs#L142-L143)
for `and`,
[`#L165-L166`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-shapeops/src/transversal/integrate/mod.rs#L165-L166)
for `or`) — `grep -rn 'expect('` across every `.rs` file under `truck-shapeops/` at the pinned
commit returns zero matches, so the panicking call is `.unwrap()`, not `.expect()`.
**`NONE`-association `joeblew999` claims, in a comment on #114, that the panic comes from
`.expect()`** ("internally it uses `.expect()` in places where a proper error would be safer") and
points to a maintained fork, [monstertruck](https://github.com/virtualritz/monstertruck), that
changes every boolean function's signature from `Option<Solid>` to `Result<Solid, ShapeOpsError>`
to fix exactly this class of crash — a working counter-design under the same licence (Apache-2.0),
not merely a complaint, but the `.expect()` wording itself is this commenter's claim, contradicted
by the source read above, not a verified fact.

### Issue tracker, roles

`gh api search/issues` (the only path that exposes `author_association`) for "boolean",
"tolerance" and "precision" returned the issues cited above plus:
[#17](https://github.com/ricosjp/truck/issues/17) "Boolean", opened by `NONE`-association
`rustythirsty` and **still open**. `CONTRIBUTOR` `ytanimura`, the maintainer, is a commenter on the
thread, not its author, posting three progress updates in five and a half weeks (2021-08-25,
2021-08-30, 2021-10-02) — "unstable so that the unit tests fail 30% of the time" during
development, then five days later a progress update describing the intersection-curve and
loop-wire implementation, then "reasonably stable, although not yet at the enterprise level" —
followed by two further `NONE`-association
comments in 2024 asking about status, unanswered by a maintainer;
[#65](https://github.com/ricosjp/truck/issues/65) "Boolean operations
improvements" (`NONE`); [#68](https://github.com/ricosjp/truck/issues/68) "Boolean Operations take
a long time" (`NONE`); [#6](https://github.com/ricosjp/truck/issues/6) "Make it possible to
specify the meshing precision" (`CONTRIBUTOR` `ytanimura`, closed). Every role seen is `NONE`
(issue authors, including #17's) or `CONTRIBUTOR` (`ytanimura`'s own comments and issues, or one of
two other one-off contributors); no `OWNER` or `MEMBER` appears — the repo has no organization, and
GitHub's `author_association` for a personal repo's own committer is `CONTRIBUTOR`, not `OWNER`.

### Maintainer and bus factor

*Measured*, `gh api repos/ricosjp/truck/contributors`: `ytanimura` — 2,591 contributions; the next
highest, `virtualritz` (also the maintainer of the `monstertruck` fork cited above, §Booleans), 9
contributions to this repository directly — the API counts commits to `ricosjp/truck` itself, not
activity on the fork. `gh
api repos/ricosjp/truck` reports 36 open issues and a push four days before this note was written
(2026-09-07). The project is active and single-maintainer at a ratio (2,591:9) that makes it a bus
factor of one by the same rule `problems.md` and the kernel spec apply elsewhere (question 8).

## Fornjot

### Topology: empty structs, identity lives entirely in the Handle

Read whole: seven of `topology/objects/`'s eleven files (`cycle.rs`, `face.rs`, `half_edge.rs`,
`region.rs`, `shell.rs`, `solid.rs`, `vertex.rs` — 471 lines; `curve.rs`, `mod.rs`, `sketch.rs` and
`surface.rs` were not individually read) and all three substantive files of `storage/`
(`handle.rs`, `store.rs`, `blocks.rs` — 520 lines; `storage/mod.rs`, 10 lines of re-exports, was
not read). The
half-edge model the brief asks about is real: `HalfEdge` holds a `curve: Handle<Curve>` and a
`start_vertex: Handle<Vertex>` only — "each `HalfEdge` only refers to its start vertex. The vertex
where it ends is referred to by the next `HalfEdge` in the [`Cycle`]"
([`half_edge.rs#L10-L37`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/half_edge.rs#L10-L37)).
`Cycle` wraps an `ObjectSet<HalfEdge>`
([`cycle.rs#L12-L14`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/cycle.rs#L12-L14)),
`Region` an exterior `Cycle` plus interior (hole) cycles
([`region.rs#L17-L20`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/region.rs#L17-L20)),
`Face` a `surface`/`region` pair with orientation carried as which side the exterior cycle winds
counter-clockwise on
([`face.rs#L33-L69`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/face.rs#L33-L69)),
`Shell` a set of `Face`s
([`shell.rs#L8-L10`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/shell.rs#L8-L10)),
`Solid` a set of `Shell`s, with the topology doc-comment itself flagging a gap: "the shells that
form the boundaries of the solid must not intersect. This is not currently validated"
([`solid.rs#L9-L17`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/solid.rs#L9-L17)).

`Vertex` is the sharpest design statement in the crate: **an empty struct**.

```rust
#[derive(Clone, Debug, Default)]
pub struct Vertex {}
```

Its doc comment explains why deliberately: "this struct does not contain any data at all… As
such, `Vertex` is solely intended to be used through a `Handle`, which provides the vertex with a
unique identity" — and states the motivating failure mode directly: "we can't just rely on the
value of points to compare them… we might very well end up *thinking* that our code computed a
single point, when in fact it does not"
([`vertex.rs#L1-L87`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/vertex.rs#L1-L87)).
Position is not a field of any topological object; it is looked up separately, per-context, in a
`Geometry` side table keyed by handle (`geometry.of_vertex(handle).local_on(curve)` — used
throughout the validation checks below). A vertex genuinely can have several positions (2D-on-one-
surface, 2D-on-another, 3D) simultaneously, by design, with validation responsible for checking
they agree within tolerance rather than the data model preventing disagreement by construction.

### Storage: append-only, pointer-is-identity, never freed

`Handle<T>` carries a `store: StoreInner<T>` (an `Arc<RwLock<...>>`), an `Index`, and a raw
`ptr: *const Option<T>`
([`handle.rs#L49-L53`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs#L49-L53)).
`id()` is `ObjectId::from_ptr(self.ptr)` — the pointer value itself, cast to `u64`
([`#L56-L59`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs#L56-L59),
[`#L186-L190`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs#L186-L190)).
This is safe only because `Store<T>` is **append-only**: `Blocks<T>` grows by pushing new
16,384-element blocks and never deallocates one, and `reserve`/`insert` never overwrite or remove a
slot ([`store.rs#L57-L89`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/store.rs#L57-L89),
the `reserve`/`insert` methods,
[`blocks.rs#L17-L60`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/blocks.rs#L17-L60)).
The module doc-comment names the trade explicitly: "no limitations on performance… best possible
convenience… `Handle`s can be owned, cloned, and dereference to the object they are referencing.
This is made possible by the append-only nature of our object storage"
([`store.rs#L1-L22`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/store.rs#L1-L22)).
The `Handle` doc comment states the design rule this buys: "To prevent situations where everything
looks fine during development, but you end up with a bug in production, any validation code that
compares objects and expects them to be the same, must do that comparison based on identity, not
equality" ([`handle.rs#L42-L48`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs#L42-L48)) —
independently-derived `#[derive(Eq, PartialEq)]` structural equality is available and different
from identity, and the doc comment warns against confusing the two.

This is a genuinely different point in the design space from the kernel spec's generational
handles (index + generation, spec §6): Fornjot buys "a handle never dangles" by never freeing
memory at all, rather than by detecting reuse through a generation counter. There is no deletion
API on `Store` anywhere in the file. A long editing session accumulates every version of every
object it ever created; nothing here bounds that.

### Validation: six checks, a tolerance config, deferred-panic error handling

`ValidationConfig` holds `tolerance: Tolerance`, `identical_max_distance: Scalar` and
`distinct_min_distance: Scalar`
([`config.rs#L22-L38`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs#L22-L38)),
and `from_tolerance` derives the latter two from the first: `let identical_max_distance =
tolerance.inner() * 10.;` then `let distinct_min_distance = identical_max_distance * 2.;`
([`#L47-L54`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs#L47-L54)),
with the comment "this factor was chosen pretty arbitrarily and might need to be tuned"
([`#L53`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs#L53))
attached to the ×2 gap between the two thresholds. `Default` is `from_tolerance(0.001)`
([`#L65-L69`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs#L65-L69))
— three orders of magnitude looser than ADR-0006's 1e-6 m default and four looser than OCCT's
`Precision::Confusion()` (1e-7, [`occt.md`](occt.md) §Tolerance model). Like Truck, this is a
single process-wide value, not per-entity.

Six checks exist, all read: `CoincidentHalfEdgesAreNotSiblings`, `FaceHasNoBoundary`,
`InteriorCycleHasInvalidWinding`, `AdjacentHalfEdgesNotConnected`, `HalfEdgeHasNoSibling`,
`MultipleReferencesToObject`
([`checks/mod.rs#L5-L19`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/checks/mod.rs#L5-L19)) —
a fraction of OCCT's 37-category `BRepCheck_Analyzer` ([`occt.md`](occt.md) §What it is), consistent
with a much smaller topology surface (no NURBS, no curved-surface intersection to check). The
module doc comment says the whole `validation/` tree is mid-migration, "a new module whose goal is
to replace `crate::core::validate`. While this transition is ongoing, both modules will be
incomplete"
([`validation/mod.rs#L13-L21`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/mod.rs#L13-L21)) —
an unfinished rewrite at the moment the project shut down, not a settled design.

Errors accumulate in a `Validation { errors: Vec<ValidationError>, config: ValidationConfig }`
meant to be checked by the caller, but its `Drop` implementation prints every unhandled error and
then **panics** if any remain and the thread is not already panicking
([`validation.rs#L23-L51`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/validation.rs#L23-L51)).
This is a third position on the spectrum the kernel spec's §12 rejects at both ends: not a
`Result` the caller must branch on, but not silent either — an invariant violation surfaces as a
**panic triggered by when a value happens to go out of scope**, not by the call that produced it.
A caller who holds `Validation` open (which the `panic_on_error: false` default encourages) defers
the crash to an arbitrary later point in the program.

**A real precision failure was reported and fixed this way.**
[Issue #2227](https://github.com/hannobraun/fornjot/issues/2227) (`CONTRIBUTOR` `IamTheCarl`)
reports a validation false-positive after a unit-conversion scale-up (metres to Fornjot's internal
millimetres): a circle's two boundary positions differ by `6.8e-13`, correctly below any sane
tolerance, but `identical_max_distance` was `0.0` at the version in use, so the check fired. `OWNER`
`hannobraun` confirms the fix already existed and closes the issue — the same failure class as
`problems.md` P-24 (a tolerance meaning different things by context) in a new mechanism: the value
was left at a hazard default (`0.0`) before being wired up to configuration.

### Geometry layer: lines and circles, no NURBS

`Path<D>` is a two-variant enum: `Circle(Circle<D>)` or `Line(Line<D>)`
([`path.rs#L8-L15`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/geometry/path.rs#L8-L15)).
`Surface` is built from `swept_curve` (a line or circle swept along an axis — planes and cylinders)
and `transformed_surface`
([`geometry/surfaces/`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/geometry/surfaces)) —
*measured*, no `nurbs`, `bspline`, or free-form curve/surface type exists anywhere under
`geometry/`. This is the direct cause named in the project's own tracker for why booleans stayed
out of reach (§Operations, below): a union of two cylinders in a cross shape needs a face that is
not a plane or a cylinder, and the representation cannot express it.

`Scalar` is `#[repr(transparent)]` around a single `value: f64` field
([`scalar.rs#L20-L24`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L20-L24)),
restricted to finite, non-NaN values by its constructor, `from_f64`, which panics on either
condition
([`#L53-L55`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L53-L55),
the NaN check; the infinite check follows immediately after). `decorum::R64` is not the struct's
storage type — it is used only inside the `Eq`/`Hash` impls, converting `self.value` to `R64` for
the comparison or hash so the two stay consistent with each other
([`#L192-L199`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L192-L199),
the `Eq`/`PartialEq` impl;
[`#L222-L228`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L222-L228),
the `Hash` impl — both comments state this is deliberate, "to make sure that this matches the
`Eq`/`PartialEq` implementation, as required by `Hash`"). `Ord` is implemented directly on the
`f64` via `partial_cmp`, not through `R64`. This is a structurally different answer to Truck's
NaN-propagation defect (§Truck, Booleans):
where Truck's `NaN` silently flows through a `Matrix4` until an unrelated assertion misreports it,
Fornjot's numeric type cannot represent a `NaN` at all once constructed — the failure mode moves
from "silent wrong value" to "construction fails or panics earlier", which is closer to the kernel
spec's own posture (§12) than Truck's, on this one point. `crates/fj`'s `Cargo.toml` also depends
on the `robust` crate (Sinha/Shewchuk-family adaptive-precision predicates,
[`Cargo.toml`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/Cargo.toml)),
and `Triangle::orient2d` calls `robust::orient2d` directly for winding decisions
([`triangle.rs#L196-L200`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/triangle.rs#L196-L200))
— *measured*, this is a real, if narrow, instance of exactly the exact-adaptive-predicate design
the kernel spec's §5 proposes, already shipping for one combinatorial decision, sitting alongside
the plain-tolerance-comparison design used everywhere else in the validation layer.

### Operations: sweep exists, booleans never shipped

`operations/sweep/` covers vertex, half-edge, cycle, face, region, sketch and shell-face sweeps —
translation-only, no revolve found in this tree. There is no `boolean`, `csg`, `union`,
`intersection`, or `difference` module anywhere under `crates/fj/src/core/`. The project's own
issue tracker settles why, in the owner's own words, across two issues:

- [Issue #42](https://github.com/hannobraun/fornjot/issues/42), "Implement union operation",
  `OWNER` `hannobraun`, open 2022-01-19 to 2023-11-24 — one year and ten months — closed unresolved:
  "I've decided to add boolean operations to the feature wishlist… There are just too many moving
  parts (some of which I've implemented, many of which are still missing) to make this
  actionable." An earlier comment in the same thread, replying to a contributor's cross-shaped-
  cylinder-union example, names the representation gap directly: "the way we represent geometry is
  pretty limited… maybe we're going to need a better geometry representation… or… full NURBS" —
  confirming the connection to §Geometry layer from the maintainer himself, not inferred.
- [Issue #943](https://github.com/hannobraun/fornjot/issues/943), "Implement 2D boolean
  operations", `OWNER` `hannobraun`, closed 2023-11-30 for the same reason.

No 3D or 2D boolean operation exists in this codebase at the pinned commit, was ever released in
any of the 51 published versions — *measured*, `git ls-remote --tags | grep -v '\^{}' | wc -l` —
(`v0.1.0`–`v0.49.0`), or was completed before the project's
archival. This is the clearest possible instance of question 9 ("documented failure modes"): the
absence itself is documented, by the maintainer, in his own closing comments.

### Issue tracker, roles

Beyond the two closed above, the `tolerance`/`precision` searches on Fornjot's own tracker returned:
[#2440](https://github.com/hannobraun/fornjot/issues/2440) "Add default tolerance to `Core`"
(`OWNER` `hannobraun`, closed), [#2441](https://github.com/hannobraun/fornjot/issues/2441) "Make
tolerance value available in `ValidationConfig`" (`OWNER`, closed),
[#2227](https://github.com/hannobraun/fornjot/issues/2227) (`CONTRIBUTOR` `IamTheCarl`, closed,
read in full above), [#2376](https://github.com/hannobraun/fornjot/issues/2376) "CI failure on
Windows" (`OWNER`, open — the repository's only open issue returned by either search, consistent
with an archived project). Every substantive issue read carries either `OWNER` (`hannobraun`
himself) or `CONTRIBUTOR`; no `MEMBER` appears, consistent with a single-maintainer personal
project rather than an organization.

### Maintainer and bus factor

*Measured*, `gh api repos/hannobraun/fornjot/contributors`: `hannobraun` — 18,972 contributions;
the next-highest human, `hendrikmaus`, 94 (`dependabot[bot]`, 473, is not a person). `gh api
repos/hannobraun/fornjot` reports `"archived": true` and 20 open issues. This is a bus factor of
one taken to its conclusion: the "if they stop" question the kernels README asks (question 8) has
already happened, on the record, in the repository's own README.

## Evaluation

Every criterion in [`README.md`](README.md), labelled. Both candidates are library-scope Rust
crates with no DynLex bindings; the *build on* verdict below explains why that axis is answered
"no" for both rather than scored per-criterion.

| Criterion | Truck | Fornjot | Evidence type |
|---|---|---|---|
| **License** | Apache-2.0 (§What was read table) | 0BSD (§What was read table) | measured |
| **Representations held natively** | One: B-rep (analytic surfaces as swept curves, NURBS curves/surfaces). Mesh (`truck-polymesh`) is a separate, converted-to representation, not modelled in | One: B-rep, lines and circles only, no NURBS, no mesh module | measured (source) |
| **Boolean robustness** | Real, shipped, transversal-only by the crate's own doc; panics on some coincident/tangent input (§Booleans) | None shipped; owner-confirmed representation gap blocks it (§Operations) | measured (source + tracker) |
| **Tolerance and precision model** | f64 throughout; one global `TOLERANCE = 1e-6` constant, no per-entity value, `tol: f64` per boolean call only | f64 (`decorum`-wrapped, NaN excluded by construction); one process-wide `ValidationConfig.tolerance`, default 0.001, no per-entity value | measured (source) |
| **Incremental evaluation** | Absent — no dependency graph found in any crate read; a changed vertex mutates in place but nothing tracks what depended on it | Absent — `Store` is append-only with no invalidation; a rebuild constructs new objects and new handles | inferred from source |
| **Threading model** | Not evaluated in depth; `Arc<Mutex<_>>` throughout implies safe but lock-contended concurrent access, not parallelism designed in | `Store`'s `StoreInner` is `Arc<RwLock<_>>` (§Storage) — safe concurrent reads, same caveat | inferred from source |
| **GPU path** | `truck-platform`/`truck-rendimpl`: wgpu-based, not evaluated here — out of this note's scope, see [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md) for the GPU-path survey's own candidates | `crates/fj/src/viewer/graphics/`: wgpu-based; not evaluated here for the same reason | not applicable to this note |
| **IFC coverage** | None | None | — |
| **Performance** | Not measured — no spike required for a design-reference note; issue #68 ("Boolean Operations take a long time", `NONE`) is a third-party complaint, not a benchmark | Not applicable — no boolean to measure | not applicable |
| **Embeddability** | Pure Rust, in-process; **zero `extern "C" fn` and zero `#[no_mangle]`** anywhere in the workspace — *measured*, `grep -rn 'extern "C" fn'` → 0. `truck-js` targets WASM via `wasm-bindgen`, not a C ABI | Pure Rust, in-process; **zero `extern "C" fn`, zero `#[no_mangle]`** — *measured*, same grep, 0. `#[repr(C)]` appears on small math structs for predictable layout, not as an exported ABI | measured |
| **2D derivation** | `truck-drafting` crate exists (2D constraint/circle-arc drawing helpers per the CHANGELOG); not evaluated in depth | None found | inferred |
| **Maturity** | Single-maintainer (2,591:9 contribution ratio), active, weekly commits, 36 open issues | Single-maintainer (18,972:94), **archived**, shut down (§Fornjot, §What was read) | measured |
| **AI familiarity** | Moderate — public since ~2020, ~1,500 stars; smaller corpus than OCCT/Blender/CGAL. One column, never a tiebreaker (R-09) | Moderate — public since ~2020, ~2,500 stars, archived. Same caveat | inferred |

## The twelve questions

1. Re-evaluate one changed element? No for both — Truck mutates a vertex's point in place but
   propagates nothing; Fornjot has no dependency graph at all (§Topology, §Storage).
2. IFC round trip? Not applicable to either.
3. Driven in-process from DynLex? Architecturally yes (pure Rust, no subprocess) but **no C ABI
   exists in either crate** — *measured*, zero `extern "C" fn` in both workspaces (§Evaluation,
   Embeddability). A DynLex FFI would need a hand-written `extern "C"` shim crate over Rust types,
   the same shape of work OCCT and CGAL need over C++ (`occt.md`, `cgal.md`), but without the
   added difficulty of C++ templates — a narrower, more tractable shim than either.
4. Threading model? Not exhaustively characterized for either; `Arc<Mutex<_>>` (Truck) and
   `Arc<RwLock<_>>` (Fornjot) give safe concurrent access, not designed-in parallelism.
5. What breaks first at scale? Not measured for either. Inferred: Fornjot's append-only store
   (§Storage) grows without bound across an editing session — the mechanism, not the number, is in
   source. Truck has no such structural ceiling found in the crates read.
6. Numeric precision, configurable? Both f64, neither configurable to float32 or to a different
   type without recompiling. Tolerance: both single global values (§Tolerance sections above), not
   per-entity, not per-operation except Truck's boolean `tol` parameter.
7. Operate on a subset — one tile, one region? No for either; both operate on whole objects passed
   by value/handle, no chunking or spatial index found in either.
8. Who maintains it? §Maintainer and bus factor, both sections — a bus factor of one for both,
   one of which has already happened.
9. Documented failure modes, with issue links? Truck: boolean panics on coincident/tangent input,
   three tracker reports, one with a working fork-based fix (§Booleans). Fornjot: the boolean
   never shipped, documented by the maintainer's own closing comments on two issues (§Operations).
10. Representations held natively? §Evaluation — one each, B-rep only, neither with a native mesh
    or point-cloud type.
11. GPU path? Both wgpu-based; out of this note's scope (§Evaluation, GPU path).
12. What would we take, what would we avoid? §Verdict, below.

## Verdict

### Build on

**No, for both — and the check is explicit, not assumed.** Rust is not DynLex, so *build on* here
means: is either crate embeddable in-process behind a stable ABI DynLex could call? Neither exposes
one. `grep -rn 'extern "C" fn'` and `grep -rn '#\[no_mangle\]'` return **zero** matches across both
workspaces, and neither `Cargo.toml` configures `cbindgen` or a `crate-type = ["staticlib"]`/
`["cdylib"]` target for a C-callable surface — Truck's only `cdylib` target is `truck-js`, built
for `wasm-bindgen`, not a C ABI
([`truck-js/Cargo.toml#L15-L16`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-js/Cargo.toml#L15-L16)).
Building on either would mean writing and maintaining our own `extern "C"` shim crate over Rust
types we do not control, in a project one of the two has already stopped maintaining entirely.
Independent of the ABI question: neither candidate's representation breadth, tolerance model or
maturity would clear the bar `README.md`'s weighting matrix sets for *build on* — Truck's boolean
is real but scoped narrower than OCCT's, and Fornjot has no boolean at all.

### Borrow from

1. **An explicit, separate exchange format kept apart from the live editable graph** — Truck's
   `Compressed*` structs, index-addressed and structure-of-arrays-shaped, converted in both
   directions from the `Arc<Mutex<_>>` graph. A shipped precedent for the kernel's `io/` boundary
   (spec §7): editable and on-disk representations as two distinct types with an explicit
   conversion, never one serialized directly as the other.
   Source: [`compress.rs#L1-L91`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-topology/src/compress.rs#L1-L91).
2. **Topological objects that hold no geometric data of their own** — Fornjot's empty `Vertex`
   struct, with position looked up through a side table keyed by handle. Forces every piece of code
   that wants a position through the same lookup path, so there is exactly one place where
   positions for different contexts can be compared for consistency, rather than several structs
   each carrying a copy that can silently drift. Worth weighing for `brep/`'s vertex type.
   Source: [`vertex.rs#L1-L87`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/vertex.rs#L1-L87).
3. **Identity-vs-equality stated as an explicit rule, not left implicit** — Fornjot's `Handle` doc
   comment states plainly that validation must compare by identity, never structural equality,
   because the latter can accidentally hold for test data and silently fail for real models. Worth
   adopting as a documented rule for our handle type regardless of storage mechanism.
   Source: [`handle.rs#L22-L48`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/storage/handle.rs#L22-L48).
4. **An unenforced precondition named in the struct's own doc comment, not silently assumed** —
   Fornjot's `Solid`: "the shells... must not intersect. This is not currently validated." A habit
   worth copying: naming a gap next to the type it constrains, visible to whoever extends
   validation next.
   Source: [`solid.rs#L9-L13`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/topology/objects/solid.rs#L9-L13).
5. **A numeric type that cannot represent NaN once constructed** — Fornjot's `Scalar` wraps a plain
   `f64`, but its `from_f64` constructor panics on a `NaN` or infinite input, so a `NaN`-producing
   computation fails at construction rather than propagating silently, as it does in Truck's
   `Matrix4` (§Truck, Booleans; Truck issue #128) — the exact failure mode Truck's own tracker
   documents.
   Source: [`scalar.rs#L20-L24`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L20-L24) (struct);
   [`#L53-L55`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/math/scalar.rs#L53-L55) (the NaN/infinite panic).

### Avoid

- **A single global tolerance constant with no per-entity value, in both candidates** (`problems.md`
  [P-02](problems.md)). Truck's `TOLERANCE` (a `const`) and Fornjot's `ValidationConfig.tolerance`
  (a runtime value, but one per process) both repeat the gap OCCT's per-entity tolerance closes and
  spec §5 commits to closing. Neither can express "this edge came from a coarse import and needs a
  looser tolerance."
  Source: [`tolerance.rs#L6-L9`](https://github.com/ricosjp/truck/blob/8d03d8f7900d6aaff784d02092bf5126c1425749/truck-base/src/tolerance.rs#L6-L9);
  [`config.rs#L22-L38`](https://github.com/hannobraun/fornjot/blob/7e856686b8105d21ce4673c10622f6ef206b89af/crates/fj/src/core/validation/config.rs#L22-L38).
- **A boolean that fails via `Option`/`.unwrap()` instead of a typed error with a message**
  (`problems.md` [P-29](problems.md)) — Truck's `and`/`or` return `Option<Solid>` with no message
  and no offending handles, and internally panic via `.unwrap()` on some coincident-geometry input
  (§Truck, Booleans) — exactly what spec §12 exists to prevent. `monstertruck` demonstrates the fix
  is a mechanical `Option → Result<T, E>` change, evidence this is an API choice, not an
  algorithmic necessity.
- **An error service whose failure surfaces on `Drop`, at an arbitrary later point, not at the
  call that produced it** (`problems.md` [P-29](problems.md), same row as the `Option`/`.unwrap()`
  pair above) — Fornjot's `Validation::drop` panic (§Fornjot, Validation). Less severe than Truck's
  `.unwrap()`, but still not a `Result` the operation returns — spec §12's model exists so a caller
  learns of failure from the return value, not from a service object's scope.
- **Unbounded accumulation traded for handle safety** (`problems.md` [P-04](problems.md)) —
  Fornjot's append-only `Store` buys "a handle never dangles" at the cost of never reclaiming
  memory. Spec §6's generational handles choose the other point on this trade — O(1) deletion,
  stable indices, dangling access detected rather than dereferenced — and this candidate shows what
  the alternative costs.

## Update to `problems.md`

- **P-02** (tolerance growth): added a data point from commercial-B-rep documentation — see
  [`commercial-brep-reference.md`](commercial-brep-reference.md) for the Parasolid propagation
  rule this row now also cites.
- **P-04** (references break after an edit): Fornjot's handle identity (§Storage) is added as a
  second, independent illustration — a handle can never silently dangle *within one build* because
  nothing is freed, but a rebuild still produces new handles with new identity, so it does not
  solve cross-rebuild reference stability either.
- **New row P-29**: Truck's `.unwrap()`-based boolean panics and Fornjot's `Drop`-triggered
  validation panic, added as two independent instances of "a library's error-handling API choice,
  not its algorithm, decides whether a bad input can crash the caller's process" — the conclusion
  P-01/P-09 already draw for OCCT/Blender/libigl, now shown to hold in a memory-safe language too.

## Sources

- [Truck repository, commit `8d03d8f7`](https://github.com/ricosjp/truck/tree/8d03d8f7900d6aaff784d02092bf5126c1425749)
- [Fornjot repository, commit `7e856686`](https://github.com/hannobraun/fornjot/tree/7e856686b8105d21ce4673c10622f6ef206b89af)
- Truck issues [#17](https://github.com/ricosjp/truck/issues/17), [#65](https://github.com/ricosjp/truck/issues/65), [#68](https://github.com/ricosjp/truck/issues/68), [#114](https://github.com/ricosjp/truck/issues/114), [#123](https://github.com/ricosjp/truck/issues/123), [#128](https://github.com/ricosjp/truck/issues/128), [#6](https://github.com/ricosjp/truck/issues/6)
- Fornjot issues [#42](https://github.com/hannobraun/fornjot/issues/42), [#943](https://github.com/hannobraun/fornjot/issues/943), [#2227](https://github.com/hannobraun/fornjot/issues/2227), [#2440](https://github.com/hannobraun/fornjot/issues/2440), [#2441](https://github.com/hannobraun/fornjot/issues/2441), [#2376](https://github.com/hannobraun/fornjot/issues/2376)
- [monstertruck](https://github.com/virtualritz/monstertruck) — third-party fork cited for the
  `Option → Result` boolean-error-handling comparison, Apache-2.0
- [`occt.md`](occt.md) §Tolerance model, §What it is — the per-entity tolerance and 37-category
  check comparison
- [`libigl-openmesh.md`](libigl-openmesh.md) — the sibling design-reference note this one matches
  in shape
- [`problems.md`](problems.md) P-01, P-02, P-04, P-09, P-14, P-29
