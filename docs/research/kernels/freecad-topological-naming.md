# FreeCAD's topological-naming problem — a case study on OCCT

**Decision question:** FreeCAD 1.0 shipped a multi-year, funded fix for the topological naming
problem (TNP) on top of OCCT. What exactly does that fix do, what does it provably not do, and
what does that split mean for a kernel that offers generational handles (spec §6) and an
application layer that references semantic entities (R-13)? Answers the **avoid** verdict axis
only — this note does not evaluate FreeCAD as a candidate to build on or borrow from; OCCT itself
is covered in [`occt.md`](occt.md).

**Serves:** ADR-0004 (design rationale), R-13; problems.md P-04

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

---

## Summary

FreeCAD's element map does not give topological entities a persistent identity; it gives them a
persistent **name string**, reconstructed after every recompute by walking, feature by feature,
which OCCT-reported "generated" or "modified" sub-shape each new sub-shape came from, and
re-encoding the generating feature's tag into the name. That is enough to survive the common
case — a dimension change that does not alter how many faces or edges a shape has — which this
note measures directly. It is **not** enough when a face or edge splits into pieces the algorithm
cannot tell apart except by an arbitrary index, when the set of things that merge into one entity
changes, or when a feature is inserted or deleted earlier in the history: FreeCAD's own 1.0
release notes call the problem "not completely solved," and the five dated issues below, three of
them filed *after* 1.0 shipped, show what "not completely solved" looks like to a user. The
mechanism generalises past FreeCAD: any application that must resolve *"which entity did the
user mean"* after a re-evaluation is solving an identity-matching problem that a memory-safety
handle scheme (kernel spec §6) does not touch — which is the main design implication below.

## What was read, and at which commit

**FreeCAD source**, pinned to **tag `1.0.0`, commit
[`2fcc5317fe3aee96ca73475986a577719fc78e20`](https://github.com/FreeCAD/FreeCAD/tree/2fcc5317fe3aee96ca73475986a577719fc78e20)**,
obtained with `git clone --depth 1 --branch 1.0.0 https://github.com/FreeCAD/FreeCAD`, hash
confirmed with `git rev-parse HEAD`. File paths and line ranges below are at this commit unless
stated otherwise.

| What | Path at the pinned commit |
|---|---|
| `ElementMap` class (the persistent-name store) | [`src/App/ElementMap.h`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.h), [`ElementMap.cpp`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp) |
| `MappedElement` / `MappedName` / `IndexedName` (the two name kinds) | [`src/App/MappedElement.h`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/MappedElement.h) |
| Naming-marker constants (`;:G`, `;:M`, `;:U`, `;:H`, …) | [`src/App/ElementNamingUtils.h`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementNamingUtils.h) |
| `StringHasher` (name-shortening table) | [`src/App/StringHasher.h`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/StringHasher.h) |
| The element-map construction algorithm after a modelling operation | [`src/Mod/Part/App/TopoShapeExpansion.cpp`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp), `makeShapeWithElementMap` at [L1388](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1388) |
| The OCCT seam: `MapperMaker`/`MapperHistory` wrapping `BRepBuilderAPI_MakeShape`/`BRepTools_History` | [`src/Mod/Part/App/TopoShape.h#L2722-L2754`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShape.h#L2722-L2754) |
| Boolean op construction (where element mapping meets OCCT booleans) | [`TopoShapeExpansion.cpp#L5539-L5743`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L5539-L5743) |

The local install used for the §Measurements spike is **FreeCAD 1.0.2**, commit
`256fc7eff3379911ab5daf88e10182c509aa8052` (`FreeCAD.Version()`), a later patch release than the
source pinned above. The element-map mechanism did not change between 1.0.0 and 1.0.2 in any way
this note relies on — the measured `MappedName` format matches what the pinned 1.0.0 source
produces — but the discrepancy is recorded rather than hidden.

Everything about OCCT's own structures (`TopoDS` shape identity, `BRepTools_History`) is read from
[`occt.md`](occt.md) rather than re-derived; see in particular its §Tolerance model and the
**Incremental evaluation** row of its evaluation table, which already states the fact this note
depends on: *"There is no evaluation graph, no dependency tracking and no parametric model in the
kernel; `TopoDS_Shape` is a value with no history. `BRepTools_History` records generated /
modified / removed relations for **one operation's** inputs and outputs only... This is what
FreeCAD builds on top and where its topological-naming problem lives"*
([`occt.md`](occt.md), Incremental evaluation row, citing
[`BRepTools_History.hxx#L27-L41`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRepTools/BRepTools_History.hxx#L27-L41)).
Everything below this point is FreeCAD-side: how a persistent identity gets built, feature by
feature, on top of a kernel that keeps none.

## The mechanism: what a name refers to

### Two kinds of name

FreeCAD's `Data::ElementMap` — *claimed*, from its own class comment — "provides for
ComplexGeoData's ability to provide proper naming"
([`ElementMap.h#L63-L70`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.h#L63-L70)).
It maps between two different kinds of name for the same sub-shape
([`MappedElement.h#L38-L56`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/MappedElement.h#L38-L56)):

- **`IndexedName`** — the raw `Type + Index` FreeCAD gets by walking the `TopoDS_Shape` today,
  e.g. `Face6`. This is exactly the OCCT-level enumeration order `occt.md` describes as having no
  persistence across a rebuild: whatever order `TopExp_Explorer` visits faces in this time.
- **`MappedName`** — a string built by `ElementMap::setElementName` /
  `ElementMap::encodeElementName`
  ([`ElementMap.cpp#L542-L661`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp#L542-L661))
  that threads the **tag** of the generating feature into the name via the `;:H` marker
  (`POSTFIX_TAG`,
  [`ElementNamingUtils.h#L54-L55`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementNamingUtils.h#L54-L55)),
  plus a generated/modified marker (`;:G` / `;:M` / `;:MG`,
  [`ElementNamingUtils.h#L60-L63`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementNamingUtils.h#L60-L63)),
  plus the operation's op-code (e.g. `XTR` for extrude,
  [`TopoShapeOpCode.h#L65`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeOpCode.h#L65)).

**Measured** (§Measurements below): the top face of a Pad in a fresh document mapped to
`#14:1;:G0;XTR;:H988:8,F` — decoded left to right this is a hashed StringID reference (`#14:1`),
the *generated* marker with disambiguating index 0 (`;:G0`), the extrude op-code (`XTR`), and the
generating feature's tag encoded in hex (`;:H988`, where `988` differs between document sessions —
it is a per-document tag salt, not a stable constant). Because `encodeElementName` recurses through
`MappedName::findTagInElementName` whenever the previous level's tag differs
([`ElementMap.cpp#L625-L648`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp#L625-L648)),
a name built several PartDesign features deep chains the tags of every intervening feature that
actually touched that entity — this is how FreeCAD reconstructs a cross-operation history that
OCCT itself never stores (`getElementHistory` /
[`ElementMap.cpp#L1296-L1351`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp#L1296-L1351)
walks exactly this chain back out again).

### Where the raw split/merge information comes from

FreeCAD does not reimplement history tracking — for each modelling operation it asks OCCT what
that *one* operation did, through two adapters over the class hierarchy `occt.md` already names:

- `MapperMaker` wraps `BRepBuilderAPI_MakeShape::Generated()`/`Modified()`
  ([`TopoShape.h#L2722-L2730`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShape.h#L2722-L2730)).
- `MapperHistory` wraps `BRepTools_History::Generated()`/`Modified()` directly
  ([`TopoShape.h#L2746-L2754`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShape.h#L2746-L2754))
  — the same per-operation-only history structure `occt.md`'s Incremental evaluation row
  describes.

So every single boolean, pad, pocket, or fillet gets **one layer** of generated/modified
information from OCCT, valid only for that one operation's inputs and outputs. Everything
persistent is built by FreeCAD chaining these single-operation layers together across the whole
feature tree, in `TopoShape::makeShapeWithElementMap`
([`TopoShapeExpansion.cpp#L1388`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1388)):

1. **Forward pass from OCCT's report.** For every vertex/edge/face of every input shape, look up
   `mapper.modified(...)` and `mapper.generated(...)`
   ([L1459](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1459),
   [L1518](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1518)),
   find the new sub-shape(s) each maps to, and record a candidate name for each.
2. **Names for entities with more than one source, or more than one destination, are built
   specially** — this is the split/merge machinery, see below
   ([L1610-L1745](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1610-L1745)).
3. **Reverse pass, high to low.** Anything still unnamed inherits a name from its already-named
   parent, with an index suffix (`;:U1`, `;:U2`, …) if it appears in more than one parent
   ([L1764-L1849](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1764-L1849)).
4. **Forward pass, low to high.** Anything *still* unnamed gets a name built from the combination
   of its already-named children
   ([L1852 onward](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1852)).
5. **What is left over stays unnamed** — a bare `IndexedName`, logged at warning level:
   `FC_WARN("unnamed lower element " << prevElement)`
   ([L1887](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1887)).
   This is exactly the pre-element-map, index-only reference the whole mechanism exists to avoid,
   and the source falls back to it silently whenever no name can be constructed.

## When the reference breaks

Four distinct failure classes, each traced to a specific place in the mechanism above.

**1. Split — one old element becomes several new ones.** The code disambiguates with a numeric
index appended to the shared base name
([L1518-L1604](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1518-L1604)).
RealThunder's own algorithm documentation is explicit that this only pushes the problem down one
level: *"the middle ones still require[s] the index to disambiguat[e], and [the] problem still
remains"* — claimed, RealThunder fork wiki, [Topological Naming
Algorithm](https://github.com/realthunder/FreeCAD_assembly3/wiki/Topological-Naming-Algorithm). An
index is not an identity; if a later edit changes how many pieces something splits into, the
indices are reassigned and a reference to "the third piece" can silently point at a different
piece — this is a smaller version of the exact problem the whole mechanism exists to solve.

**2. Merge — several old elements become one new element.** The name becomes a composite: the
first source's name, plus a `K`-prefixed, hashed combination of the others' names, built at
[L1655-L1706](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1655-L1706).
The source comments on its own fragility: including the OCCT-reported *position* index in that
combination "is likely to degrade name stability, but is unfortunately a necessity to avoid
duplicate names"
([L1695](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1695)).
Change *which* elements merge, or their order, and the composite name changes — a reference built
against the old merge is now pointing at nothing.

**3. Feature deletion or insertion earlier in the tree.** Both FreeCAD's own documentation and the
algorithm's author agree this is the hard case, in near-identical language:
the FreeCAD wiki states *"When changing the structure, such as by adding or deleting operations in
the middle of a Part Design Body, this kind of automatic repair will be less likely [to
succeed]"* — claimed, [Topological naming
problem](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_naming_problem.md) —
and RealThunder's wiki states the fix *"works poorly when the change happens several steps into
the history."* Structural edits are exactly what a component-definition change is (see
[`parametric-components.md`](../../domain/parametric-components.md), "Definition versioning" —
R-13), so this is the case that matters most for us.

**4. Geometry whose type changes, or whose generation is ambiguous.** Two places in the source
make this concrete rather than hypothetical:

- When OCCT reports a lower-level input (an edge) generating a *higher*-level output (a whole
  solid) — which happens, the comment says, "when extruding" — the algorithm deliberately
  discounts that name in favour of a more specific one if one exists, because "too much
  information is bad for us"
  ([L1537-L1552](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1537-L1552)).
  This is a heuristic tie-break, not a proof that the more specific name is correct.
- When the same new element is reported as *both* generated and modified from different sources,
  the algorithm logs `FC_WARN("element is both generated and modified")` and falls back to a
  neutral, less specific marker
  ([L1706-L1714](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L1706-L1714)).

Two further, structural limits, both explicit in the source rather than inferred:

- **History depth is capped at 50.** `ElementMap::traceElement` walks the tag chain in a
  `for (int index = 0; index < 50; ++index)` loop
  ([`ElementMap.cpp#L1392`](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp#L1392)),
  with a comment explaining why: tracing without a specific owning object is "inherently unsafe,"
  citing a real circular-mapping bug report,
  [`realthunder/FreeCAD_assembly3#968`](https://github.com/realthunder/FreeCAD_assembly3/issues/968)
  ([L1382-L1391](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/App/ElementMap.cpp#L1382-L1391)).
- **The fix and the pre-fix behaviour still coexist in the same source tree.** The Boolean fuse
  path has a comment reading `// Compatible with pre-TNP allowing <null shape>.fuse() behavior`
  ([L5635](https://github.com/FreeCAD/FreeCAD/blob/2fcc5317fe3aee96ca73475986a577719fc78e20/src/Mod/Part/App/TopoShapeExpansion.cpp#L5635)) —
  a small, concrete sign that the element map is a layer added onto older index-based behaviour,
  not a clean replacement of it.

## The mitigation, and what it cannot do

**What the element map does:**

- Survives a topology-preserving edit — the common case — because the operation's own OCCT
  `Generated`/`Modified` report is unambiguous: one new face corresponds to exactly one old face.
  **Measured** below.
- Detects breakage rather than silently substituting the wrong entity: when no name can be
  reconstructed, FreeCAD raises a recompute error on the dependent feature instead of continuing
  with whatever `IndexedName` happens to exist now — *claimed*, FreeCAD wiki: the fix's purpose is
  to *"identify broken references from topological changes and display an error to the user."*
- Attempts automated repair as a second line of defence — `getRelatedElements`/`traceElement`
  search the history for a plausible match and FreeCAD substitutes it — but only "when confidence
  is high," and the wiki adds an explicit caution that this feature "has unintentionally misled
  many users into thinking that it will no longer be helpful to use techniques like datums,
  explicit sketch placement" — i.e., the authors themselves warn that the repair heuristic invites
  the wrong mental model. *Claimed*, [FreeCAD wiki, Topological naming
  problem](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_naming_problem.md).

**What it does not do**, stated as concretely as the source and the evidence allow:

| Case | Why it breaks | Evidence |
|---|---|---|
| A face/edge splits into N pieces and the reference needs a *specific* middle piece | Disambiguated by an arbitrary index, not a stable identity; index assignment shifts if the split count changes | RealThunder wiki quote above; `TopoShapeExpansion.cpp#L1518-L1604` |
| The *set* of elements merging into one changes (one more/fewer source, or reordered) | The composite name is a hash of the current merge set; a different set hashes differently | `TopoShapeExpansion.cpp#L1655-L1706`, comment at L1695 |
| A feature is inserted or deleted earlier in the tree | The tag chain the name depends on is a chain of *specific* feature tags; changing which features exist changes the chain | FreeCAD wiki + RealThunder wiki quotes above |
| History longer than 50 steps, or a reference spanning documents (external links) | Hard-coded depth cap; author calls cross-document tracing "inherently unsafe" | `ElementMap.cpp#L1382-L1392`; realthunder/FreeCAD_assembly3#968 |
| An operation reports ambiguous generation (both generated and modified, or a low-level input generating a high-level output) | Falls back to a heuristic tie-break, not a proof of correctness | `TopoShapeExpansion.cpp#L1537-L1552`, L1706-L1714 |
| Model stability problems that are not topological-naming problems at all (over-constrained sketches, bad tolerancing, non-manifold results) | Out of scope for the fix by construction — it only tracks *names*, not geometric validity | *claimed*, Ondsel, [*FreeCAD's topological naming problem is (officially)
history*](https://www.ondsel.com/blog/toponaming-problem-is-history/), 2024-05-22: "TNP mitigation helps only for a specific kind of model breakage. Models can still break for reasons that have nothing to do with topological naming." |

Even where the mechanism works, it is a **reconstruction**, not a stored identity: nothing in
OCCT persists across the recompute, so every one of the four passes above runs again from
scratch, on the new shape, after every single recompute. That is a real cost (see the "what this
means" section below on why we did not attempt to measure it) and a real fragility surface: it
succeeds only as long as each operation's local `Generated`/`Modified` report stays legible
enough to re-derive the same chain.

## Evidence: user-facing breakage before and after FreeCAD 1.0

**The 1.0 release notes themselves are the first piece of evidence.** *Claimed*, [FreeCAD 1.0
release
notes](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Release_notes_1.0.md):
*"The long-standing Topological naming problem has finally been addressed thanks to the joint
effort and hard work of several developers... The TNP problem is not completely solved and
further improvements will follow in the next version."* ([Pull request
#13705](https://github.com/FreeCAD/FreeCAD/pull/13705)). The same page notes the project's TNP
specialist, bgbsww, died shortly before the release shipped — this was a genuinely large,
multi-year, partly paid effort (Ondsel funded part of it — see below), not a quick patch.

Five dated issues, each stating a concrete thing that broke, three of them filed **after** 1.0
shipped (2024-11):

| # | Date | What broke |
|---|---|---|
| [FreeCAD/FreeCAD#15484](https://github.com/FreeCAD/FreeCAD/issues/15484) | opened 2024-07-17, open | Replacing a rectangular Pad's edge with a zig-zag of lines (a construction-mode toggle), then padding and sketching two circles on the result, then going back and switching the edge's construction mode again, produces a TNP error on the *second* sketch — a split-disambiguation case, reproduced on `main`, works on the separate Link Branch at the time |
| [FreeCAD/FreeCAD#17041](https://github.com/FreeCAD/FreeCAD/issues/17041) | opened 2024-10-05, open, labelled "Confirmed" and "Toponaming fixed in V2" | Face/edge `IndexedName`s themselves change after a plain recompute on a PartDesign model — reported as a regression against FreeCAD 1.0 RC2 / nightly 38871 (2024-09-30) |
| [FreeCAD/FreeCAD#25361](https://github.com/FreeCAD/FreeCAD/issues/25361) | opened 2025-11-16, closed | Body = Pad → Mirror → Pocket, with the Pad's length driven by a `VarSet`. Changing the `VarSet` value raises `"Subshape not found Mirrored.?Face5"` on the Mirror feature and the recompute stops; the reporter notes the face is "always Face5" by eye, i.e. the raw index looks unchanged but the mapped reference still fails; a maintainer pointed the reporter at a development branch (`weekly-2025.10.05`) to test a fix, confirming the report as a real, open regression at time of filing |
| [FreeCAD/FreeCAD#26815](https://github.com/FreeCAD/FreeCAD/issues/26815) | opened 2026-01-10, open, titled "Toponaming regression?" | A Mirror feature using the Base XZ plane fails with a *blank* error message when a Fillet exists earlier in the same Body; using the (geometrically identical) sketch axis as the mirror plane, or removing the earlier Fillet, both make it succeed — an ambiguous-generation case (see class 4 above) with no diagnostic surfaced to the user |
| [FreeCAD/FreeCAD#29154](https://github.com/FreeCAD/FreeCAD/issues/29154) | opened 2026-04-07, open | Shortening a Pad's length by 5 mm on a real (non-toy) part inverts a downstream sketch dimension, breaks two Pockets' external-geometry references (their target faces have to be manually redefined), and requires every Chamfer/Fillet on affected edges to be manually redefined too — reporter states some of those edges "ha[ve] the same designation" (name) but lost the link regardless, i.e. a name matched but the feature still failed to re-attach |

These span nearly two years (2024-07 to 2026-04) and both sides of the 1.0 release (2024-11), and
between them touch three of the four failure classes above: split disambiguation (#15484), a
feature-order/ambiguous-generation case (#26815), and the general "downstream chain breaks after
an early-tree edit" case #29154 is a real-world instance of. #17041 shows that even the raw
`IndexedName` layer regressed at one point. #25361 shows the pattern from an independent (French)
user with a minimal reproducer and a maintainer confirming it as reproducible.

**The community's own assessment, before and after, in its words.** Ondsel — the company that
funded part of the 1.0 TNP work — published two posts that bracket the release:

- Pre-1.0 (2023-02-18), *[Don't hold your breath for FreeCAD's topological naming
  fix](https://www.ondsel.com/blog/freecad-topological-naming/)*: *"The problem cannot be solved
  in the traditional sense. It can only be mitigated and most applications do a good job of
  avoiding the problem by either limiting the user's actions or algorithmically tracking changes
  to the named features... The current state of FreeCAD is weak in this regard."*
- Post-1.0-work, pre-1.0-ship (2024-05-22), *[FreeCAD's topological naming problem is (officially)
  history](https://www.ondsel.com/blog/toponaming-problem-is-history/)*: even while announcing
  the fix as functionally complete, the same post immediately qualifies it — *"let's remember that
  model stability is a complex topic, and TNP mitigation helps only for a specific kind of model
  breakage. Models can still break for reasons that have nothing to do with topological
  naming... all CAD software can be used to design brittle models and there's no substitute for
  good design principles."*

Both quotes are *claimed* (a vendor/community blog, not a measurement), but they are the same
conclusion the source code and the release notes independently support: a mitigation, explicitly
bounded, not a solution.

## Measurements

**Hardware/software:** Windows 11 Pro 10.0.26200; FreeCAD 1.0.2 (`freecadcmd.exe`), commit
`256fc7eff3379911ab5daf88e10182c509aa8052`, OCC 7.8.1 bundled.
**Method:** [`spikes/topological-naming/demo.py`](../../../spikes/topological-naming/demo.py),
run headless with `freecadcmd.exe demo.py`; full output in
[`spikes/topological-naming/results/freecad.txt`](../../../spikes/topological-naming/results/freecad.txt);
method and two unrelated bugs hit while writing the script are in
[`spikes/topological-naming/README.md`](../../../spikes/topological-naming/README.md).

**What was measured.** A `PartDesign::Body`: `Sketch` (20×20 mm rectangle) → `Pad` (10 mm) →
`Sketch001`, whose `AttachmentSupport` references the Pad's top face by name (`Face6`) — the same
"a later feature stores a name for an entity an earlier feature's computation produced" pattern
[`parametric-components.md`](../../domain/parametric-components.md) describes — → `Pocket`. The
base rectangle was then widened from 20 mm to 35 mm (a **topology-preserving** edit: the Pad stays
a six-faced box) and the document recomputed.

| | Before | After |
|---|---|---|
| Raw `IndexedName` of the top face | `Face6` | `Face6` (unchanged) |
| `MappedName` of the top face | `#14:1;:G0;XTR;:Hb6d:8,F` | **byte-identical string** |
| `Sketch001.AttachmentSupport` | `[(Pad, ('Face6',))]` | unchanged; no touched/error state |
| `Pocket.Shape` | valid | valid, `Volume = 6915.18` |

**What this shows, and what it does not.** This is a genuine measurement, not an inference: the
element map's persistent name for the referenced face is literally the same string before and
after a real recompute that regenerated the Pad from scratch. That confirms the mechanism works,
at zero observed cost in correctness, for the case it was built for — a parameter change that does
not restructure the model. It is **not** a measurement of any of the four failure classes above:
reliably forcing a face-count change (a fillet, or a profile whose vertex count changes) from a
script turned out to need more of FreeCAD's attachment/shadow-reference internals than fit the
time budgeted for this spike (see the spike's README for the two bugs that already consumed most
of it). The failure side of this note rests on the five GitHub issues and the source-code
mechanism instead, which is consistent with how this task was scoped: a "not measured, here is
why" is recorded rather than a forced or misleading demonstration.

## What this means for our design

**A generational handle and a persistent element name solve different problems, and our own
documents currently blur that distinction.** The kernel spec's generational handles (§6: "index +
generation... handles stay stable across reallocation, and dangling references are detected
rather than dereferenced") are a **memory-safety** mechanism: they guarantee that if handle `H`
still resolves, the slot it points to has not been freed and reused for something else *within one
arena's lifetime*. They say nothing about whether the face now occupying handle `H` after a full
re-evaluation is the face the caller meant. FreeCAD's element map exists precisely because OCCT's
`TopoDS_Shape` gives *no* handle at all across a rebuild — every recompute is a fresh set of
shapes — so FreeCAD must re-derive identity from scratch each time by chaining single-operation
`Generated`/`Modified` reports. A kernel that hands the caller stable *handles within one build*
has not thereby solved the problem FreeCAD's element map solves; it has solved a narrower,
easier problem one layer down. **`problems.md` P-04's current "Our design's answer" — "the kernel
offers stable generational handles and never renumbers" — reads as though handle stability answers
R-13. It does not, and should be corrected to say so explicitly**; this is a self-review finding
recorded here and applied in the `problems.md` update below.

**The kernel spec's own boundary (§3) already puts this problem in the right place — application,
not kernel — and this case study is evidence that boundary is correct, not just tidy.**
"Semantic BIM model, parameters, evaluation graph" is explicitly `app/`'s territory, not the
kernel's. FreeCAD's ElementMap is exactly this kind of application-layer machinery bolted onto a
kernel (OCCT) that has none of it — a two-thousand-line, multi-pass, heuristic-laden C++ subsystem
that took FreeCAD's community several years and at least one paid engineering effort to build, and
which its own authors say is still incomplete. That is direct evidence for what it costs to build
identity-reconstruction from a kernel that does not offer it, and an argument for not asking the
DynLex kernel to grow an equivalent: `app/` should own this, deliberately, the way FreeCAD's
`Data`/`App` layer does — not `kernel/csg` or `kernel/brep`.

**The R-13 / `parametric-components.md` strategy — reference semantic entities, not derived
topology — is not merely "a nicer API"; it is the one strategy that avoids needing FreeCAD's
machinery at all for the references it covers.** A wall's "exterior face" is a concept the *domain
model* can keep stable across any number of recomputes, however many OCCT (or our own kernel's)
faces the current geometry happens to produce — because it is an input to evaluation, not an
output the kernel has to be asked to identify after the fact. FreeCAD has no equivalent vocabulary
to fall back on (a mechanical face has no name beyond its position in history), which is exactly
why it had to build a general-purpose, heuristic reconstruction mechanism. Every one of the five
issues above is a case where a reference pointed at *derived topology* — a face, an edge — rather
than at a semantic entity a domain model could have kept invariant.

**But the boundary R-13 does not yet locate still needs an answer, and this note sharpens what
that answer has to contain.** `parametric-components.md` already says "the boundary between
'expressible semantically' and 'requires raw topology' is not yet located... anything outside it
inherits the full problem." For whatever falls outside that boundary, `app/`, not the kernel, needs
something FreeCAD-shaped: per-operation generated/modified reporting from the kernel (which
`ops`/`csg`/`brep` can supply cheaply — it is exactly what `BRepTools_History`-style bookkeeping
already gives OCCT, and our own module layout has room for it), and then the tag-chaining,
split/merge disambiguation, and repair-heuristic logic entirely in `app/`. Two concrete
requirements follow directly from the failure classes measured above, and are proposed additions
to the open question list in `parametric-components.md` and to the kernel spec's out-of-scope
list (§14):

1. Whatever `app/` builds for the boundary case must **surface breakage as a visible, logged,
   undoable error — never a silent repair** — matching `onshape.md`'s "assume some breakage" and
   directly avoiding the failure mode the FreeCAD wiki itself warns about: users trusting an
   automatic repair heuristic enough to stop placing datums and explicit references. A repair
   suggestion is acceptable; a repair applied without the user seeing it is not.
2. Any trace/history-walk `app/` builds needs an explicit, documented depth bound and must refuse
   to walk across object boundaries it cannot prove are safe — FreeCAD hard-caps at 50 steps and
   flags cross-document tracing as "inherently unsafe" only after a real circular-mapping bug
   (`realthunder/FreeCAD_assembly3#968`) forced the issue. We should pick that bound deliberately
   instead of discovering it the same way.

**Cost is an open question, flagged rather than assumed.** Ondsel's 2024 post claims the TNP
work's performance impact "appears to be negligible," but this is *claimed*, not measured by
anyone in this research programme, and it describes FreeCAD's specific implementation, not a
general property of history-reconstruction schemes. If `app/` ends up building comparable
machinery for the boundary cases, its cost needs its own measurement before being assumed free —
noted here so it is not silently inherited as an assumption later.

## Verdict (avoid axis only)

1. **Avoid treating derived-topology references as the primary mechanism** for anything an
   application can name semantically instead — this is R-13's existing conclusion, and this note
   supplies the FreeCAD-specific mechanism (§The mechanism) and dated, first-party evidence
   (§Evidence) for why mechanical/general CAD has never gotten this fully right despite a
   multi-year, partly funded effort by a team that clearly wanted to.
2. **Avoid conflating memory-safety handle stability with recompute-identity.** Our own design
   documents currently invite this conflation (`problems.md` P-04, updated below); FreeCAD is
   direct evidence the two are different problems requiring different mechanisms, at different
   layers.
3. **Avoid silent automatic repair for whatever reference the semantic-entity boundary does not
   cover.** FreeCAD's own maintainers warn that a repair heuristic which works "most of the time"
   teaches users to stop defending against the case where it doesn't.
4. **Avoid an unbounded or implicit trace/history walk.** Bound it deliberately; FreeCAD found its
   bound only after a real bug report about circular mapping across external links.

This note does not score FreeCAD, or OCCT, on the *build on* or *borrow from* axes — see
[`occt.md`](occt.md) for OCCT's evaluation on those axes; FreeCAD itself was never a build-on
candidate (it is an application, not a kernel) and its element-map source, while readable for
study, is FreeCAD's own LGPL-2.1-or-later code, not something to copy into a differently designed
system.

## Sources

- FreeCAD source, tag `1.0.0`,
  [`2fcc5317fe3aee96ca73475986a577719fc78e20`](https://github.com/FreeCAD/FreeCAD/tree/2fcc5317fe3aee96ca73475986a577719fc78e20) —
  file paths and lines cited inline above.
- [FreeCAD 1.0 release notes](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Release_notes_1.0.md) —
  TNP section and the [`bgbsww`](https://github.com/bgbsww) dedication.
- [FreeCAD wiki — Topological naming problem](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_naming_problem.md)
  (fetched via its `FreeCAD-documentation` GitHub mirror; the live wiki page blocks automated
  fetches with an Anubis bot challenge).
- [RealThunder fork — Topological Naming Algorithm](https://github.com/realthunder/FreeCAD_assembly3/wiki/Topological-Naming-Algorithm) —
  the naming-marker scheme and its own stated limitations.
- [`realthunder/FreeCAD_assembly3#968`](https://github.com/realthunder/FreeCAD_assembly3/issues/968) —
  the circular-mapping bug `ElementMap.cpp`'s depth-cap comment cites.
- [FreeCAD/FreeCAD#15484](https://github.com/FreeCAD/FreeCAD/issues/15484),
  [#17041](https://github.com/FreeCAD/FreeCAD/issues/17041),
  [#25361](https://github.com/FreeCAD/FreeCAD/issues/25361),
  [#26815](https://github.com/FreeCAD/FreeCAD/issues/26815),
  [#29154](https://github.com/FreeCAD/FreeCAD/issues/29154) — dated user-facing breakage, before
  and after 1.0.
- Ondsel, [*Don't hold your breath for FreeCAD's topological naming
  fix*](https://www.ondsel.com/blog/freecad-topological-naming/), 2023-02-18.
- Ondsel, [*FreeCAD's topological naming problem is (officially)
  history*](https://www.ondsel.com/blog/toponaming-problem-is-history/), 2024-05-22.
- [`occt.md`](occt.md) — OCCT's tolerance model and `BRepTools_History`, cited rather than
  re-derived.
- [`docs/domain/parametric-components.md`](../../domain/parametric-components.md),
  [`docs/research/prior-art/onshape.md`](../../research/prior-art/onshape.md),
  [`docs/risks.md`](../../risks.md) R-13 — the phase-1 material this note connects to.
- [`docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
  §3, §6 — kernel boundary and generational handles.
- [`spikes/topological-naming/`](../../../spikes/topological-naming/) — the measurement in this
  note's §Measurements.
