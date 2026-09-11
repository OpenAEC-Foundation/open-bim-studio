# IfcOpenShell — four kernels behind one IFC mapping, and no dependency tracking

**Decision question:** IfcOpenShell is the reference open-source IFC implementation and
[ADR-0004](../../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md) gives it a
*build on* verdict. Can its geometry path actually be built on for the `ifc/` sub-project — in
particular, can it re-evaluate one changed element cheaply enough for an interactive modeller
(R-01) — and if not, what must our design take from it and what must it not repeat?

**Serves:** ADR-0004 (§Verdict, the *build on* row); the `ifc/` sub-project spec; kernel spec
§3–§6; [`problems.md`](problems.md) P-01, P-02, P-05, P-06, P-08, P-10, P-16; R-01, R-15

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> Geometry here runs on **OCCT 7.8.1**, so every OCCT boolean and tolerance finding in
> [`occt.md`](occt.md) applies underneath this note and is not repeated. What is new here is the
> *IFC* layer above it — the schema mapping, the iterator, the caching, and the three
> alternative kernels the same wheel also ships.

---

## Summary

IfcOpenShell can produce one element's geometry on its own, and on the real benchmark building
the median element costs **2.06 ms** against **8.0 s** for a full re-iteration — so
re-evaluation does not require reprocessing the model, and R-01's *fail* clause is not met at
the median. But 5.7% of elements exceed 16 ms and the worst exceeds 550 ms, and there is **no
dependency tracking at all**: the caching that exists is keyed on instance identity with no
invalidation path, which a maintainer describes as written on the assumption that the model is
static. The surprise of this note is not the timing but the shipping surface — the Python wheel
contains **four** selectable geometry libraries, and `hybrid-cgal-simple-opencascade` produces
*the same 3,654 elements* as OCCT **13× faster** (0.687 s vs 9.013 s) while being neither the
Python default nor documented as the fast path.

## What it is

IfcOpenShell is a C++ library with Python bindings for reading, writing and converting IFC,
whose wheel names Dion Moult as author (`Author-email` in `METADATA`, *measured*) and whose
geometry design questions on the tracker are answered by Thomas Krijnen (`aothms`,
`authorAssociation: MEMBER`). It is the engine
under Bonsai (the Blender IFC add-on), IfcConvert and much of the open BIM toolchain. It is
**LGPL-3.0-or-later** (`License :: OSI Approved :: GNU Lesser General Public License v3 or
later (LGPLv3+)` in the installed wheel's `METADATA`, *measured*). Its own README claims complete
parsing support for IFC2x3 TC1, IFC4 Add2 TC1, IFC4x1, IFC4x2 and IFC4x3 Add2, with **extensive
geometric support for IFC2x3 TC1 and IFC4 Add2 TC1** only (*claimed*, wheel `METADATA`) — the
geometry coverage is narrower than the parsing coverage, and the README says so.

## What was read, and at which commit

**There is no `v0.8.4` tag.** `git ls-remote --tags https://github.com/IfcOpenShell/IfcOpenShell`
shows the library's own release tags stopping at `v0.7.1`; the 0.8 line is tagged only through
the Bonsai add-on (`bonsai-0.8.4` and a long run of `bonsai-0.8.4-alphaYYMMDDHHMM`). The pin used
throughout this note is therefore:

| | |
|---|---|
| Tag | `bonsai-0.8.4` |
| Commit | `158fe92644cfe2bc37be513d9838c95d9f2233cf` |
| Measured against | the `ifcopenshell` PyPI wheel `0.8.4.post1`, native version string `0.8.0` |

The wheel is **not provably built from that commit**; it is the closest published tree to the
version string. Every source citation below is to that commit, and this caveat applies to all of
them.

Read: `src/ifcgeom/` (`Iterator.h`, `mapping/mapping.cpp`, `hybrid_kernel.h`, `abstract_mapping.h`,
`kernels/opencascade/`, `kernels/cgal/`, the 200-odd files in `mapping/`),
`src/ifcwrap/IfcGeomWrapper.i`, and
`src/ifcopenshell-python/ifcopenshell/api/georeference/`.

### Which OCCT, and how we know

The wheel links statically — no OCCT DLLs, just a 55.7 MB
`_ifcopenshell_wrapper.cp312-win_amd64.pyd`. The version is in the strings of that binary, in a
build-machine include path baked into an OCCT assertion message:

```
D:\a\IfcOpenShell\IfcOpenShell\_deps-vs2022-x64-installed\opencascade-7.8.1\inc\BVH_QueueBuilder.hxx
```

**OCCT 7.8.1** (*measured* — the string is in the installed binary; the version-from-path
reading is *inferred*). The same scan finds `_deps-vs2022-x64-installed\cgal\include\CGAL`,
`_deps\boost_1_86_0`, `_deps\hdf5-1_13_1`, `_deps\mpfr`, `_deps\mpir`, `_deps\rocksdb`, and
mangled `CGAL::Lazy_exact_nt<Gmpq>` symbols — **CGAL is compiled into the same wheel**, with
GMP/MPFR behind it. Method and full output in
[`spikes/incremental-evaluation/results/ifcopenshell.md`](../../../spikes/incremental-evaluation/results/ifcopenshell.md)
§Which OCCT.

This matters beyond bookkeeping: [`xbim.md`](xbim.md) shows XbimGeometry pins the same **OCCT
7.8.1**. Two of the three IFC implementations the research programme named would have been
running the same kernel version.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | LGPL-3.0-or-later. Usable as a library from a differently-licensed product if dynamically linked; *borrowing code* into our kernel would make that code LGPL | **measured** (wheel `METADATA`) | installed `ifcopenshell-0.8.4.post1.dist-info/METADATA` |
| **Representations held natively** | OCCT B-rep, CGAL polyhedra (two flavours), and triangulated output. `iterator-output` selects TRIANGULATED / NATIVE / SERIALIZED. No point cloud, no implicit | **measured** (the four `GEOMETRY_LIBRARY` values are returned by the installed wheel) + **claimed** | `typing.get_args(ifcopenshell.geom.GEOMETRY_LIBRARY)` |
| **Boolean robustness** | OCCT's, plus an IFC-specific retry ladder ("Used fuzziness" appears 139× in one run's log) and a refusal to accept non-manifold boolean results. Failure is frequently **silent**: 49 `[Error] Failed to convert:` logged on a model where zero exceptions were raised | **measured** (log summaries) + **claimed** (tracker, see §Known problems) | [results](../../../spikes/incremental-evaluation/results/ifcopenshell.md) §What the log says |
| **Tolerance and precision model** | One global `precision` (default 1e-05), clamped at **1e-7 m**: `Precision lower than 0.0000001 meter not enforced` was logged **3,654 times** on IFC_Schependomlaan — once per element. Precision is read from the file's `IfcGeometricRepresentationContext` | **measured** (log) + **claimed** (#6127) | [results](../../../spikes/incremental-evaluation/results/ifcopenshell.md) |
| **Incremental evaluation** | Single-element evaluation exists (`create_shape`) and is cheap at the median; **dependency tracking does not exist**, and the two caches that do exist have no invalidation path | **measured** + **claimed** (#4386) | §Incremental evaluation |
| **Threading model** | `Iterator` holds a `kernel_pool` of one `Converter` per thread; `num_threads` is explicit. Measured **3.1×** and **2.4×** on 32 logical processors. Contradicts P-08 for this implementation | **measured** | [results](../../../spikes/incremental-evaluation/results/ifcopenshell.md) |
| **GPU path** | None in-library; triangulated output with vertices, faces, normals and material ids, which the caller uploads | **inferred** from the `iterator-output` options |
| **IFC coverage** | Parsing: IFC2x3 TC1, IFC4 Add2 TC1, IFC4x1, IFC4x2, IFC4x3 Add2. **Geometry: IFC2x3 TC1 and IFC4 Add2 TC1 only** | **claimed** | wheel `METADATA` |
| **Performance** | Full geometry: 1.038 s / 9.013 s at 32 threads (OCCT); **0.666 s / 0.687 s** with the hybrid kernel for the same element counts. Parse 0.136 s / 2.231 s | **measured** | [results](../../../spikes/incremental-evaluation/results/ifcopenshell.md) |
| **Embeddability** | C++ library with a SWIG Python binding; in-process use from DynLex means an FFI boundary to a C++ library, not a subprocess. LGPL shapes how | **inferred** |
| **2D derivation** | `ifcopenshell.draw` exists and `iterator-output` has a CURVES dimensionality; not examined | **unknown** |
| **Maturity** | The reference implementation of open-source IFC; active tracker with maintainer engagement on design questions (see #4386, #6905, #2025). Bus factor is concentrated on `aothms` for the geometry core | **claimed** + **inferred** |
| **AI familiarity** | Not scored. One column, never a tiebreaker (R-09) | **unknown** |

## Four geometry libraries, and the one nobody mentions

`ifcopenshell.geom.GEOMETRY_LIBRARY` on the installed wheel is
`Literal['cgal', 'cgal-simple', 'opencascade', 'hybrid-cgal-simple-opencascade']`, and both
`geom.iterator(...)` and `geom.create_shape(...)` accept it, defaulting to `opencascade`
(*measured*). All four were run.

| Model | library | threads | median | elements |
|---|---|---|---|---|
| AC20-FZK-Haus | opencascade | 1 | 3.229 s | 107 |
| AC20-FZK-Haus | opencascade | 32 | 1.038 s | 107 |
| AC20-FZK-Haus | cgal | 32 | **crashed** | — |
| AC20-FZK-Haus | cgal-simple | 32 | 0.086 s | **103** |
| AC20-FZK-Haus | hybrid-cgal-simple-opencascade | 32 | **0.666 s** | **107** |
| IFC_Schependomlaan | opencascade | 1 | 21.688 s | 3,654 |
| IFC_Schependomlaan | opencascade | 32 | 9.013 s | 3,654 |
| IFC_Schependomlaan | cgal | 32 | **crashed** | — |
| IFC_Schependomlaan | cgal-simple | 32 | 0.651 s | **3,646** |
| IFC_Schependomlaan | hybrid-cgal-simple-opencascade | 32 | **0.687 s** | **3,654** |

Full runs, repeats and per-configuration process peaks in
[the results file](../../../spikes/incremental-evaluation/results/ifcopenshell.md).

**The hybrid kernel produces the same element count as OCCT, 13.1× faster on the real building.**
That is the single largest performance lever measured anywhere in this note, and it is not the
Python API's default.

The mechanism is in its source, and it is a design worth taking whole. `HybridKernel::convert`
asks the mapping whether the element has openings, skips any kernel that does not support boolean
operations when it does, and otherwise tries each kernel in order inside a `try`, returning on the
first success:

```cpp
auto ops = mapping_->find_openings(item->instance->as<IfcUtil::IfcBaseEntity>());
bool has_openings = ops && ops->size();
for (auto& k : kernels_) {
#ifdef IFOPSH_WITH_CGAL
	if (has_openings && !k->supports_boolean_operations()) {
		// @todo [four comment lines elided]
		continue;
	}
#endif
	bool success = false;
	try {
		success = k->convert(item, rs);
	} catch (...) {}
	if (success) {
		return true;
	}
}
return false;
```

(verbatim apart from the four `@todo` comment lines marked as elided, and the leading
indentation, which is five tabs in the original)

([`hybrid_kernel.h#L83-L107`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/hybrid_kernel.h#L83-L107))

The measured consequence of *not* having that guard is in
[`compare.md`](../../../spikes/incremental-evaluation/results/compare.md): run `cgal-simple`
alone and a wall with an opening comes back with **zero triangles and zero volume**, silently.
Four `IfcWallStandardCase` on AC20-FZK-Haus and eight rows on IFC_Schependomlaan disappear that
way, and 17 of the 20 volume disagreements between the two kernels are over 0.5 relative.

### The CGAL kernel corrupts the heap, sometimes

`geometry_library="cgal"` killed the child process on both models, with no Python traceback and
nothing on stderr: return code `0xC0000374` (`STATUS_HEAP_CORRUPTION`) on AC20-FZK-Haus and
`0xC0000005` (`STATUS_ACCESS_VIOLATION`) on IFC_Schependomlaan.

It is **not deterministic**. In an earlier run of the identical command on AC20-FZK-Haus, `cgal`
completed all five repeats (107 elements, median 2.508 s); in the run that produced the committed
JSON it crashed. A separate probe completed three times in a row. The honest statement is that
**`cgal` completes sometimes and corrupts the heap sometimes**, on the same file and the same
command — a rate and a trigger are not established here. It is also why the spike driver runs
each geometry library in its own child process: building iterators for two libraries in one
process reliably killed it. *(measured; new row **P-25** in [`problems.md`](problems.md))*

## Incremental evaluation

### What exists

`geom.create_shape(settings, element)` produces one element's geometry. Timed for **every**
element in each model:

| Model | n | median | p95 | max | under 16 ms |
|---|---|---|---|---|---|
| AC20-FZK-Haus | 107 | **1.63 ms** | 238.23 ms | 539.59 ms | 83 / 107 (77.6%) |
| IFC_Schependomlaan | 3,654 | **2.06 ms** | 16.96 ms | 553.97 ms | 3,445 / 3,654 (94.3%) |

The edit test — translate one wall's `IfcAxis2Placement3D` by 1 m, verified visible by a 1.0
bounding-box shift — gives 1.02 ms and 1.46 ms against 1.065 s and 8.025 s for a full
re-iteration: **1,044× and 5,488×**. Re-evaluating *the worst* element instead costs 530.54 ms and
623.59 ms. Method, repeats and the R-01 verdict in
[`FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md).

### Why it is cheap, and why nothing is reused

Both facts have the same cause. `helper_fn_create_shape` constructs a fresh `Converter` — and
therefore a fresh kernel and a fresh mapping — on **every call**:

```cpp
ifcopenshell::geometry::Converter kernel(
    ifcopenshell::geometry::kernels::construct(file, geometry_library, st), file, st);
```

([`IfcGeomWrapper.i#L885-L889`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcwrap/IfcGeomWrapper.i#L885-L889))

So there is no stale-cache hazard — the measured warm and cold shifts are both exactly 1.0, where
web-ifc's warm shift is 0.0 — and equally there is nothing carried between two re-evaluations of
the same element. The measured per-element cost is an **upper bound** on what IfcOpenShell's own
machinery could achieve; per-call setup is charged every time.

### What does not exist: invalidation

Two caches exist. Neither can be invalidated.

1. **The mapping cache**, keyed on `inst->identity()`, looked up and inserted under a mutex, with
   no erase and no dirty flag anywhere in the file
   ([`mapping.cpp#L693-L721`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/mapping/mapping.cpp#L693-L721)).
   It lives for one `Converter`'s lifetime, and `use_caching_` defaults to `true`
   ([`abstract_mapping.h#L50`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/abstract_mapping.h#L50)).
2. **The iterator's shape cache**, `decorate_with_cache_`, keyed on GlobalId plus representation
   id, read-then-write against an HDF5 store
   ([`Iterator.h#L161-L194`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/Iterator.h#L161-L194)).
   It is a *re-run* cache, not a change-driven one: a hit is decided by identity, never by whether
   the instance changed. `cache-shapes` was off for every measurement here.

The maintainer has stated the design assumption directly. On
[#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386) (OPEN, created 2024-03-03;
reporter `RickBrice`, `authorAssociation: CONTRIBUTOR`), where mutating a placement in memory and
re-mapping returns the stale cached matrix, `aothms` (**MEMBER**) writes that **"the caching is
written with the idea that the underlying model is static"**. He then enumerates the options —
caching on a recursive tree of values instead of identity, manual invalidation, automatic
invalidation on setters, a runtime switch — and names why it is hard: a cache entry must know
which sub-items it was built from, *including inverse attributes*, so that changing one point
invalidates the parent polyline. The issue is still open with nothing implemented.

That is the clearest statement in this research programme of what a dependency-tracked kernel has
to do, written by the person who decided not to do it.

Two further datapoints:

- [#1785](https://github.com/IfcOpenShell/IfcOpenShell/issues/1785) (CLOSED 2023-02-13; opened by
  `aothms`, **MEMBER**) is the HDF5 shape cache, announced to "reuse the interpreted geometry for
  building elements with minimal effort", measured there at 4.9 s → 0.57 s on a second pass. It
  is keyed per GlobalId plus representation id and nothing in the thread detects that an element
  changed — whole-file re-run caching, confirming the reading above.
- [#5696](https://github.com/IfcOpenShell/IfcOpenShell/issues/5696) (OPEN; opened by `theoryshaw`,
  **MEMBER**) reports, in a measurement by `BIMvoice` (**CONTRIBUTOR**, not a maintainer), that
  iterator `initialize()` "costs ~0.19s even when the iterator includes a single element" — a
  fixed whole-file setup cost independent of what was asked for. Re-importing N representations
  one at a time pays it N times. This is a concrete argument against building incremental
  regeneration on the *iterator*; our measurements use `create_shape`, which does not pay it.

## Known problems

Each speaker's login and verbatim `authorAssociation`. `aothms` and `theoryshaw` are **MEMBER**;
`Moult`, `BIMvoice`, `Andrej730`, `RickBrice`, `Vanuan`, `johanrd`, `andy-5` are **CONTRIBUTOR**
on the threads cited; `JR-Morgan`, `philong6297`, `tgranie`, `scottmcnab` are **NONE**. `BIMvoice`
is prolific in 2026 triage but is **not** a maintainer, and two of the sharpest root causes below
are his and are not confirmed in-thread by a MEMBER — they are labelled accordingly.

| Issue | State | What goes wrong | Root cause, and who says so |
|---|---|---|---|
| [#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386) — bug in geometry mapping cache | OPEN, 2024-03-03 | Mutate a placement in memory, re-map, get the stale cached matrix back | `aothms` (**MEMBER**): "the caching is written with the idea that the underlying model is static". Invalidation would need per-entry constituent sets including inverse attributes. **Unimplemented** |
| [#992](https://github.com/IfcOpenShell/IfcOpenShell/issues/992) — opening subtractions fail | OPEN, 2020-09-08, reporter `johanrd` (**CONTRIBUTOR**) | A wall with 10 openings renders **completely solid**; log shows "Boolean operation yields non-manifold result" then "No longer attempting boolean operation with higher fuzziness" for all 10 | `aothms` (**MEMBER**): operands share an edge so the result is non-manifold, and non-manifold results are rejected because they usually indicate an error — "I have not found a way yet to distinguish valid non-manifold results from invalid ones". The polyhedral workaround fails on cylinders because in OCCT a cylindrical edge is three edges, so overlap detection never fires |
| [#7815](https://github.com/IfcOpenShell/IfcOpenShell/issues/7815) — void not voiding at certain positions | OPEN, 2026-03-18, reporter `theoryshaw` (**MEMBER**) | Moving an opening a fraction of an inch flips voiding on and off | Analysis by `BIMvoice` (**CONTRIBUTOR**, *not* a maintainer, not MEMBER-confirmed in-thread): "the opencascade kernel returns the roof uncut (volume unchanged) while reporting IsDone" — the no-op passes every validity check so the higher-fuzziness retry never fires, and the same operands through the CGAL kernel cut correctly. **Silent** boolean failure |
| [#487](https://github.com/IfcOpenShell/IfcOpenShell/issues/487) — opening subtraction failed, curved wall | OPEN, 2018-10-16 | Curved walls: loose faces, self-intersections, openings not subtracted | `aothms` (**MEMBER**) attributes it to missing edge parametrisations after sewing, required by the boolean; improved in one commit "but that wall on the right remains problematic" |
| [#6127](https://github.com/IfcOpenShell/IfcOpenShell/issues/6127) — unit conversion misses `Precision` | CLOSED 2026-07-27 | Thin fins vanish from converted output while rendering elsewhere | `aothms` (**MEMBER**): "The width of these fins is below the precision marked in the file". The schema trap: `IfcGeometricRepresentationContext.Precision` is an `IfcReal`, not an `IfcLengthMeasure`, so a millimetre→metre conversion silently left the tolerance 1000× too large |
| [#6142](https://github.com/IfcOpenShell/IfcOpenShell/issues/6142) — geometry differs between the Python API and Bonsai | OPEN, 2025-02-11 | Same file, same version: a slab produces no geometry through `ifcopenshell.geom` but renders in Bonsai and elsewhere | `Andrej730` (**CONTRIBUTOR**) narrowed it to the `context-ids` setting plus the kernel choice. `BIMvoice` (**CONTRIBUTOR**, not MEMBER-confirmed) argues the real mechanism is that `context-ids` changes the derived **boolean precision** — 1e-7 m by default versus 1e-5 m when the subcontext id is passed, 100× coarser |
| [#7063](https://github.com/IfcOpenShell/IfcOpenShell/issues/7063) — 0.8.3 much slower than 0.7.1 | OPEN, 2025-08-27 | ~2 min → ~30 min when calling `as_compound()` for `TopoDS_Shape` | `aothms` (**MEMBER**): "Overall performance should have slightly improved, but in particular because of the hybrid kernel" — and the hybrid kernel is exactly what you cannot use if you need a `TopoDS_Shape` back. He later points at the wire-intersection check and `no-wire-intersection-check` |
| [#6905](https://github.com/IfcOpenShell/IfcOpenShell/issues/6905) — high memory multi-threaded | CLOSED 2025-07-22 | >60 GB peak at `num_threads=32` vs ~25 GB single-threaded on a ~1 GB file | `aothms` (**MEMBER**): "I guess we never expected the triangulated geometry to take up so much RAM." Closed by the reporter, not fixed; a rocksdb-backed streaming conversion was in progress |
| [#2025](https://github.com/IfcOpenShell/IfcOpenShell/issues/2025) — large datasets | OPEN, 2022-02-05 | A 2 GB SPF file exhausts 16 GB on `ifcopenshell.open()` | `aothms` (**MEMBER**): "A factor 5 memory vs file size is not atypical for SPF-parsers", and doing better "requires a complete rewrite of the parser to store attribute values with static types based on the schema instead of runtime type variants" |
| [#8431](https://github.com/IfcOpenShell/IfcOpenShell/issues/8431) — automatic regeneration of voided elements | OPEN, 2026-07-09, reporter `Vanuan` (**CONTRIBUTOR**) | Application-level: the void/filling relation needs a manual "Regen" instead of being a live dependency | The reporter proposes comparing "the cached matrix and profile hash against current values". No MEMBER comment on the thread. Listed because it is the same missing mechanism one layer up |

### The measured counterpart

Two of these are visible in our own logs, which makes them properties of the shipped wheel and
not only of a reporter's file:

- **The precision floor is hit on every element.** `Precision lower than 0.0000001 meter not
  enforced` appears **3,654 times** on IFC_Schependomlaan — exactly once per element. The file
  asks for a finer tolerance than the library will honour, universally, and the only signal is a
  warning. That is #6127's and #6142's subject matter, on our benchmark, at default settings.
- **Errors are logged and swallowed.** AC20-FZK-Haus logged **49** `[Error] Failed to convert:`
  while `create_shape` raised **zero** exceptions and the iterator's
  `had_error_processing_elements()` returned False on every run. A caller who checks the return
  value sees success. That is #7815's silent-failure shape, measured.

## Georeferencing (R-15)

`ifcopenshell.api.georeference` is five functions —
`add_georeferencing`, `edit_georeferencing`, `edit_true_north`, `edit_wcs`,
`remove_georeferencing` — and `add_georeferencing` is the interesting one because it branches on
schema exactly where R-15 says the problem is
([`add_georeferencing.py`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcopenshell-python/ifcopenshell/api/georeference/add_georeferencing.py)):

- **IFC2X3** (lines 47-64): two property sets, `ePSet_ProjectedCRS` and `ePSet_MapConversion`,
  added to the **`IfcProject`**, with `Eastings`, `Northings` and `OrthogonalHeight` created as
  `IfcLengthMeasure`.
- **IFC4 and later** (lines 66-99): an `IfcProjectedCRS` plus one of `IfcMapConversion`,
  `IfcMapConversionScaled` or `IfcRigidOperation`, with `SourceCRS` set to the
  `IfcGeometricRepresentationContext` whose `ContextType == "Model"`.

Two things to carry into R-15. First, this is a **single API that degrades**: the caller asks for
georeferencing and the library decides which convention the schema supports — the right shape for
our own IFC layer. Second, **[`docs/risks.md`](../../risks.md) R-15 says the IFC2x3 convention
lives on `IfcSite`; IfcOpenShell writes it on `IfcProject`.** That discrepancy is recorded here,
not resolved — R-15 is not this note's to edit, and which placement real exporters use is a
separate measurement.

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** **Yes** — 2.06 ms
   median against an 8.0 s full pass, edit verified visible. But no dependency tracking decides
   *which* element, and the tail reaches 554 ms. *measured.*
2. **What happens to geometry on an IFC round trip?** Not measured; this spike read and edited in
   memory, it did not write files back. *unknown.*
3. **Driven in-process from DynLex?** Yes in principle — a C++ library with a stable C++ API — at
   the cost of an FFI boundary and an LGPL obligation on anything statically linked. *inferred.*
4. **Threading model, and what is single-threaded by design?** The iterator holds a `kernel_pool`
   of one `Converter` per thread and `num_threads` is explicit
   ([`Iterator.h#L131-L138`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/Iterator.h#L131-L138)).
   Measured 3.1× / 2.4× on 32 logical processors. The mapping cache is behind one mutex and the
   HDF5 cache behind another — those are the serialised points. *measured + source.*
5. **What breaks first at scale?** Memory, on the evidence of the tracker (#6905's 60 GB, #2025's
   "factor 5 memory vs file size") and of our own 227 MB → 1,092 MB for a 19× file. Time grows
   less than linearly with threads available. *claimed + measured.*
6. **Numeric precision?** double, with one global tolerance, configurable via `precision` but
   **floored at 1e-7 m** — measured, once per element, on the benchmark. *measured.*
7. **Operate on a subset of the model?** Yes: the iterator takes `include`/`exclude` lists of
   `IfcProduct`, and `create_shape` needs nothing but the element. The obstacle to using it that
   way is #5696's fixed ~0.19 s `initialize()` cost, which `create_shape` avoids. *source +
   claimed.*
8. **Who maintains it, and what if they stop?** `aothms` answers every geometry design question
   on the tracker, including the ones about why invalidation is hard. Concentrated. *inferred.*
9. **Documented failure modes?** §Known problems: ten issues, plus two reproduced in our own logs.
10. **Representations held natively?** OCCT B-rep, two CGAL flavours, triangulated output; the
    hybrid switches per element. No point cloud, no implicit. *measured + source.*
11. **How does geometry reach the GPU?** It does not; the library hands back triangles and the
    caller uploads them. *inferred.*
12. **What would we take, and what would we avoid?** §Verdict.

## Measurements

Everything in this note that is labelled *measured* is in
[`spikes/incremental-evaluation/results/ifcopenshell.md`](../../../spikes/incremental-evaluation/results/ifcopenshell.md)
and
[`compare.md`](../../../spikes/incremental-evaluation/results/compare.md), produced by
`spikes/incremental-evaluation/ifcopenshell_driver.py` and `compare.py`, with the raw JSON and the
run transcripts beside them. Hardware: Intel Core i9-14900HX (32 logical processors), 32 GB RAM,
Windows 11 `10.0.26200`, Python 3.12.10, `ifcopenshell` 0.8.4.post1. Five repeats, median
reported.

## Strengths

- **A single-element geometry call that genuinely does not touch the rest of the model**, cheap
  at the median, with no stale-cache hazard. Neither of the other two implementations has this.
- **Pluggable kernels behind one schema mapping**, selectable per call, with a hybrid that falls
  back per element. This is a better answer to "which kernel" than picking one.
- **The schema mapping itself**: ~200 `mapping/Ifc*.cpp` files, one per entity type, is the most
  complete open record of how IFC representations become geometry.
- **A georeferencing API that degrades across schema versions behind one call** (§Georeferencing).
- **Honest maintainers on design questions.** #4386 is a maintainer explaining, in detail, why the
  feature we most need is hard — which is worth more than a feature list.

## Weaknesses

- **No dependency tracking, and the caches that exist assume an immutable model** (#4386). Cheap
  per-element evaluation without invalidation is half a mechanism.
- **A long tail**: 5.7% of elements over 16 ms, worst 554 ms, and the expensive elements
  (`IfcWindow`, `IfcWallStandardCase` with many openings) are exactly the ones users drag.
- **Silent failure.** 49 logged conversion errors with zero exceptions raised and
  `had_error_processing_elements()` False; and #7815's uncut-but-`IsDone` boolean.
- **One global tolerance, floored at 1e-7 m**, hit once per element on a real file.
- **`cgal` crashes non-deterministically** with heap corruption, and two kernels cannot coexist in
  one process.
- **Geometry coverage is narrower than parsing coverage** — IFC4x3 parses but is not claimed for
  geometry.

## Risks

The risk in adopting this for `ifc/` is not performance, it is **the gap between what we would use
it for and what it is**. We would be using `create_shape` as an evaluation primitive under our own
dependency graph — a use nobody upstream has, with no test coverage upstream, and with the
per-call `Converter` construction sitting in our hot path by design rather than by accident. If
upstream ever adds caching *inside* `create_shape` (which #4386 contemplates), our correctness
would depend on an invalidation mechanism that does not exist yet. That is a dependency on an
unwritten design.

## Verdict

### Build on — **yes for parsing and representation mapping; qualified yes for geometry**

**For the `ifc/` sub-project: yes.** Parsing, schema handling, the representation mapping and the
georeferencing API are the best available and nothing in this note argues against them.

**For ADR-0004's geometry path: yes, but not as the evaluation layer.** There is no disqualifying
assumption of the kind web-ifc has — no batch-only iterator (there is `create_shape`), no float32
output (doubles throughout), no tolerant-B-rep inheritance that cannot be worked around (the
hybrid kernel already routes per element). The qualification is what is **missing** rather than
what is wrong: no dependency tracking, so *we* decide what is stale, and the per-element cost we
pay is a full evaluation with per-call setup. That is exactly the shape R-01's "if it fails"
clause describes — "we write our own evaluation layer over a geometry kernel, and the semantic
kernel becomes I/O only" — and this note's measurements say that clause is **indicated**.

The one thing that could still disqualify it is the tail: 554 ms for an `IfcWindow` is not an
interactive drag, and no evaluation layer above it fixes that. Whether that is OCCT's cost or
IfcOpenShell's mapping is not established here; the fact that the same window gives three
different volumes on three kernels (see [`compare.md`](../../../spikes/incremental-evaluation/results/compare.md))
suggests the representation, not the kernel, is the problem.

### Borrow from — pinned

| What | Why | Where |
|---|---|---|
| **The per-element kernel-fallback loop with a capability predicate.** Ask whether the element needs booleans, skip kernels that cannot do them, try the rest in order, first success wins | Measured: same 3,654 elements, **13.1× faster** than OCCT alone. It is also the correct answer to "exact or fast?" — per element, not per product | [`hybrid_kernel.h#L83-L107`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/hybrid_kernel.h#L83-L107) |
| **The iterator model**: explicit `num_threads`, a `kernel_pool` of one converter per thread, `include`/`exclude` filters on the element set, and a pull interface (`initialize` / `get` / `next`) rather than a callback | Measured 3.1× and 2.4×. The per-thread converter is why: no shared mutable kernel state, so the parallelism needs no lock on the hot path. **Refutes P-08 for this implementation** | [`Iterator.h#L120-L245`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/Iterator.h#L120-L245) |
| **The representation-mapping tables**: one translation unit per IFC entity type, bound by a generated dispatch include (`bind_convert_impl.i`) | ~200 files, each a self-contained statement of how one entity becomes geometry. Our `ifc/` layer wants exactly this shape, and this is the reference for what belongs in each | [`src/ifcgeom/mapping/`](https://github.com/IfcOpenShell/IfcOpenShell/tree/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/mapping) |
| **The georeference API's schema-degrading contract**: one call, IFC4 entities or the IFC2x3 property-set convention chosen by the library | R-15 is a decision about export targets; this is the API shape that makes the decision survivable. Note the discrepancy on `IfcProject` vs `IfcSite` recorded in §Georeferencing | [`add_georeferencing.py`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcopenshell-python/ifcopenshell/api/georeference/add_georeferencing.py) |
| **`aothms`'s statement of what invalidation requires** (#4386): per-entry constituent sets, propagated dirty marks, and traversal of **inverse** attributes so that changing one point invalidates the parent polyline | This is the specification of the thing our kernel spec §3 claims to build, written by someone who decided it was too expensive to retrofit. Retrofitting is the expensive case; we are not retrofitting | [#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386) |

### Avoid — each mapped to a design choice, each with a P-row

| Failure | Design choice it traces to | Our design's answer |
|---|---|---|
| **Cached geometry goes stale after an in-memory edit** (#4386), and the whole-model pass is the only reliable way to be correct | The cache is keyed on instance *identity*, which cannot express "this instance changed"; the model is assumed static | Cache keys are content-derived and every entry records its constituents, so a change invalidates exactly its dependents (spec §3). **P-06** |
| **A conversion error is logged and the call returns success.** 49 logged errors, 0 exceptions, `had_error_processing_elements()` False on every run | Logging is the error channel; the return value carries no failure information | A result is a value that can *be* a typed failure, and a partial success says which parts failed (spec §12). **P-01**, measured |
| **A boolean reports success and removes nothing** (#7815, `BIMvoice` **CONTRIBUTOR**, not MEMBER-confirmed) | "Did the operation run?" is checked instead of "did the operation do what it claimed?" | Operands that provably overlap and a result whose volume is unchanged is an error condition, not a result (spec §12). **P-01** |
| **One global tolerance, floored at 1e-7 m, warned about once per element** | Tolerance is a property of the model container, read from `IfcGeometricRepresentationContext`, then clamped globally | Tolerances are per-entity and explicit, and a request the kernel will not honour is a refusal, not a warning in a log nobody reads (spec §5). **P-05**, measured |
| **`Precision` survives a unit conversion unscaled** because the schema types it as `IfcReal` (#6127) | A tolerance carried as a bare number, so nothing knows it is a length | Tolerances carry the dimension of what they bound (spec §5). **P-05**, and the new row **P-24**, which [`xbim.md`](xbim.md) reaches from the other direction (#578's radians-vs-length) |
| **A kernel without booleans returns an empty solid for a wall with an opening, silently** — measured, 4 and 8 rows | Capability is discovered by failure, and "no geometry" is a valid return value | A kernel declares its capabilities and a request it cannot serve is refused by name, never answered with an empty result (spec §12). **P-01** |
| **`cgal` corrupts the heap non-deterministically**, and two kernels cannot share a process | Kernel-global state that is neither reentrant nor isolated | Kernels are values with no global state; an unstable backend is quarantined per call, not per process (spec §6). **New row P-25** |

## Sources

- [IfcOpenShell/IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell) at tag `bonsai-0.8.4`,
  commit `158fe92644cfe2bc37be513d9838c95d9f2233cf`
- The installed `ifcopenshell` wheel `0.8.4.post1` (native `0.8.0`), its `METADATA`, and the
  strings of `_ifcopenshell_wrapper.cp312-win_amd64.pyd`
- Issues [#487](https://github.com/IfcOpenShell/IfcOpenShell/issues/487),
  [#992](https://github.com/IfcOpenShell/IfcOpenShell/issues/992),
  [#1785](https://github.com/IfcOpenShell/IfcOpenShell/issues/1785),
  [#2025](https://github.com/IfcOpenShell/IfcOpenShell/issues/2025),
  [#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386),
  [#5696](https://github.com/IfcOpenShell/IfcOpenShell/issues/5696),
  [#6127](https://github.com/IfcOpenShell/IfcOpenShell/issues/6127),
  [#6142](https://github.com/IfcOpenShell/IfcOpenShell/issues/6142),
  [#6905](https://github.com/IfcOpenShell/IfcOpenShell/issues/6905),
  [#7063](https://github.com/IfcOpenShell/IfcOpenShell/issues/7063),
  [#7815](https://github.com/IfcOpenShell/IfcOpenShell/issues/7815),
  [#8431](https://github.com/IfcOpenShell/IfcOpenShell/issues/8431)
- [`spikes/incremental-evaluation/`](../../../spikes/incremental-evaluation/) — drivers, raw
  results, [`FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md),
  [`results/ifcopenshell.md`](../../../spikes/incremental-evaluation/results/ifcopenshell.md),
  [`results/compare.md`](../../../spikes/incremental-evaluation/results/compare.md)
- [`occt.md`](occt.md) — the kernel underneath, measured separately
