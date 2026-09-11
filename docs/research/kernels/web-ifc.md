# web-ifc — a fast tape parser, its own boolean, and float32 at the door

**Decision question:** web-ifc is the other implementation
[ADR-0004](../../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md) gives a *build
on* verdict. It converts a 3,643-element building's geometry in 297 ms, an order of magnitude
faster than IfcOpenShell. Can that geometry path be built on for the `ifc/` sub-project — or is
the speed bought with something that disqualifies it?

**Serves:** ADR-0004 (§Verdict, the *build on* row); the `ifc/` sub-project spec; kernel spec
§3–§5, §12; [`problems.md`](problems.md) P-01, P-05, P-06, P-10, P-13; R-01, R-14

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

---

## Summary

web-ifc is genuinely fast — 297 ms for all 3,643 meshes of the real benchmark building against
IfcOpenShell's 9.0 s — and its token-tape parser is the best-designed piece of either
implementation. It is also **disqualified for *build on* by two independent, measured facts**:
every coordinate leaves the library through a `Float32Array`, converted under the source comment
"unfortunately webgl can't do doubles"; and there is **no working way to invalidate its geometry
cache**, because the one API call for it, `ResetCache`, is declared in TypeScript but never
registered in the WASM module's Emscripten bindings, so calling it throws. An in-memory edit
therefore reaches the model but never the geometry: our edit test measured a 0.0 m bounding-box
shift after a verified 1 m translation, at 0.03 ms — a fast, confidently wrong answer.

## What it is

web-ifc is the C++/WebAssembly IFC parser and geometry engine from That Open Company (formerly
IFC.js), the engine under That Open Engine and its three.js viewers. It is **MPL-2.0**
(`LICENSE.md` at the tag, *measured*). Unlike IfcOpenShell it depends on no geometry kernel: the
parser, the swept-solid construction and the boolean are all written in this repository, which is
why it builds to WASM at all and why its failure modes are its own rather than OCCT's.

## What was read, and at which commit

| | |
|---|---|
| Tag | `0.77` |
| Commit | `f26c4beef0a668ebdb180d2b95a94097a1e21cef` |
| npm version at that tag | `0.0.77` (`package.json`) — matches the package measured |
| Runtime check | `IfcAPI.GetVersion()` on the installed package returns `0.0.77` |

Unlike IfcOpenShell's pin, this one is exact: the tag's `package.json` declares the same version
string as the npm package that was measured.

Read: `src/cpp/web-ifc/parsing/` (`IfcLoader.cpp/.h`, `IfcTokenStream.cpp/.h`, `IfcTokenChunk.cpp`,
`IfcFileStream.cpp`), `src/cpp/web-ifc/geometry/` (`IfcGeometryProcessor.cpp/.h`,
`IfcGeometryLoader.cpp`, `representation/`, `operations/`), `src/cpp/wasm/web-ifc-wasm.cpp`,
`src/ts/web-ifc-api.ts`.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | MPL-2.0. File-level copyleft: borrowing a file obliges us to publish changes to that file, but not to the surrounding work — the most permissive of the three | **measured** (`LICENSE.md` read at the tag) | [`LICENSE.md`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/LICENSE.md) |
| **Representations held natively** | Triangle meshes only. `IfcGeometry` is vertices + indices; there is no B-rep, no point cloud, no implicit | **inferred** from [`IfcGeometry.h`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/representation/IfcGeometry.h) |
| **Boolean robustness** | Its own implementation, tolerance-driven, no exact arithmetic. Acknowledged as the weak point by a collaborator: "Booleans is perhaps the most complex problem in our library" (`agviegas`, **COLLABORATOR**, [#927](https://github.com/ThatOpen/engine_web-ifc/issues/927)) | **claimed** + **inferred** | §Known problems |
| **Tolerance and precision model** | Computation in `double`; **output in float32**. Tolerances are 12 loader settings plus hard-coded `EPS_*` constants that are *duplicated across three headers with two different values for the same names* | **measured** (source + our own bbox readings) | §Precision |
| **Incremental evaluation** | Geometry is cached per geometry express id; the only invalidation call, `ResetCache`, **is not exported by the WASM module and throws**. An edit is invisible to any element already evaluated | **measured** (runtime + source) | §Incremental evaluation |
| **Threading model** | Single-threaded. WASM in Node, no worker use in the library | **inferred** from the absence of any threading in the sources read |
| **GPU path** | This is what it is built for: interleaved `[x,y,z,nx,ny,nz]` float32, handed over as a pointer into `HEAPF32` and read as a `Float32Array` — a buffer you upload without touching | **measured** ([`web-ifc-api.ts#L1305-L1307`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1305-L1307)) |
| **IFC coverage** | Both benchmark schemas read correctly (IFC4 and IFC2X3, verified by `GetModelSchema`). Coverage breadth not otherwise measured | **measured**, partial |
| **Performance** | `OpenModel` 16.5 ms / 328.7 ms; `LoadAllGeometry` 85.3 ms / **296.6 ms**. Roughly **30×** faster than IfcOpenShell's OCCT path on the larger model, and ~2.3× faster than IfcOpenShell's own hybrid kernel | **measured** | [results](../../../spikes/incremental-evaluation/results/webifc.md) |
| **Embeddability** | WASM. Embeddable anywhere a WASM runtime is, including in-process from DynLex — but the model must fit the WASM heap. Two different numbers, not to be conflated: the loader's `MEMORY_LIMIT` **setting** defaults to 2 GB and budgets the *token tape's* chunks; the ceiling a maintainer names for the model itself is **4 GB, the WASM address space** (#538) | **measured** (the setting) + **claimed** (the 4 GB ceiling) |
| **2D derivation** | `GetAllCrossSections2D` / `GetAllCrossSections3D` exist on the API; not examined | **unknown** |
| **Maturity** | Active; issues answered by `beachtom` (**COLLABORATOR**), `QuimMoya` (**CONTRIBUTOR**), `agviegas` (**COLLABORATOR**), `HoyosJuan` (**MEMBER**). The REAL write path has been fixed at least four separate times: [#214](https://github.com/ThatOpen/engine_web-ifc/issues/214) (integers emitted as `0`, exponents as `e`), [#454](https://github.com/ThatOpen/engine_web-ifc/issues/454) (scientific notation read back as `0`, "now fixed" twice, three months apart), [#470](https://github.com/ThatOpen/engine_web-ifc/issues/470) (re-export corrupts geometry, "This is now fixed") and [#695](https://github.com/ThatOpen/engine_web-ifc/issues/695) (a trailing `.` after a positive exponent, "Should now be fixed" the next day) | **claimed** |
| **AI familiarity** | Not scored. One column, never a tiebreaker (R-09) | **unknown** |

## The tape parser — the best thing in here

`IfcLoader` does not build an object graph. It writes a **byte tape of typed tokens** and
addresses attributes by offset into it: `GetIntArgument(tapeOffset)`,
`GetDoubleArgument(tapeOffset)`, `GetRefArgument(tapeOffset)`, `GetTokenType(tapeOffset)`
([`IfcLoader.h`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcLoader.h)).
The token type is a one-byte enum with eleven members — `UNKNOWN = 0, STRING, LABEL, ENUM, REAL,
REF, EMPTY, SET_BEGIN, SET_END, LINE_END, INTEGER`
([`IfcTokenStream.h#L18-L30`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcTokenStream.h#L18-L30)).

The tape is **chunked and evictable**. `IfcTokenStream(chunkSize, maxChunks)` holds a vector of
chunks; a read of an unloaded chunk calls `checkMemory()` first, and when the active-chunk count
hits `maxChunks` a loaded chunk is cleared to make room
([`IfcTokenStream.cpp#L102-L117`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcTokenStream.cpp#L102-L117)).
The budget comes straight from the loader settings: `maxChunks = memoryLimit / tapeSize`
([`IfcLoader.cpp#L24-L29`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcLoader.cpp#L24-L29)),
so the defaults `MEMORY_LIMIT` 2,147,483,648 and `TAPE_SIZE` 67,108,864 give **32 chunks of
64 MB**.

This is a paging design, in a parser, with the budget as a caller-visible setting. It is directly
relevant to R-14 (parametric evaluation across unloaded tiles), and it is the single strongest
*borrow from* in this note.

It also has one flaw worth naming: the eviction picks the **first loaded chunk it finds**, not the
least recently used —

```cpp
      for (uint32_t x = 0; x < _chunks.size(); x++) 
      {
        if (_chunks[x].IsLoaded())
        {
          if (_chunks[x].Clear())
          {
            _activeChunks--;
            break;
          }
        }
      }
```

(verbatim, indentation included)

so a working set that spans more than `maxChunks` chunks will evict the chunk it is about to read
again. *(inferred from the loop; no measurement of thrashing was made.)*

## Precision

### float32 at the boundary

`IfcGeometry` stores `std::vector<double> vertexData` and a parallel `std::vector<float>
fvertexData`
([`bim-geometry/geometry.h#L17-L19`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/operations/bim-geometry/geometry.h#L17-L19)).
`GetVertexData()` fills the float copy on demand, under the comment *"unfortunately webgl can't do
doubles"*
([`IfcGeometry.cpp#L220-L238`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/representation/IfcGeometry.cpp#L220-L238)),
and the JS side reads `HEAPF32` and returns a `Float32Array`
([`web-ifc-api.ts#L1305-L1307`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1305-L1307)).

**Measured consequence.** The benchmark wall's bounding-box minimum x reads
`7.410000019073486` where the file says `7.41`, and `4.359756112553707` on the millimetre model.
Every coordinate that leaves web-ifc has been through float32, regardless of the precision that
produced it. Internal double precision does not help a consumer that only ever sees the float
copy.

This is the disqualifying criterion named in the kernels README's weighting matrix —
*"float32-only is disqualifying for build on"* — and it is met, measured, not argued.

### Tolerances: 12 settings and three headers that disagree

The loader settings expose seven named tolerances with their defaults
(`TOLERANCE_PLANE_INTERSECTION` 1e-4, `TOLERANCE_PLANE_DEVIATION` 1e-4,
`TOLERANCE_BACK_DEVIATION_DISTANCE` 1e-4, `TOLERANCE_INSIDE_OUTSIDE_PERIMETER` 1e-10,
`TOLERANCE_SCALAR_EQUALITY` 1e-4, `PLANE_REFIT_ITERATIONS` 1, `BOOLEAN_UNION_THRESHOLD` 150)
alongside `COORDINATE_TO_ORIGIN`, `CIRCLE_SEGMENTS`, `TAPE_SIZE`, `MEMORY_LIMIT` and
`LINEWRITER_BUFFER`
([`web-ifc-api.ts#L442-L459`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L442-L459)).

**`USE_FAST_BOOLS` does not exist at this tag.** `grep -rn USE_FAST_BOOLS src/` returns nothing;
the named `TOLERANCE_*` settings replaced it. Documentation that mentions it is describing an
older version.

Below the settings are hard-coded constants, and they are **duplicated with conflicting values**:

| Constant | `operations/boolean-utils/eps.h` (global scope) | `operations/bim-geometry/epsilons.h` (`bimGeometry`) | `representation/geometry.h` (`webifc::geometry`) |
|---|---|---|---|
| `EPS_MINISCULE` | 1.0e-12 | 1.0e-12 | — |
| `EPS_TINY` | 1.0e-04 | 1.0e-04 | **1e-9** |
| `EPS_SMALL` | 1.0e-04 | 1.0e-04 | **1e-6** |
| `EPS_BIG` | 1.0e-04 | 1.0e-04 | — |
| `EPS_BIG2` | 1.0e-03 | 1.0e-03 | — |

`EPS_SMALL` is 1e-4 in one namespace and 1e-6 in another; `EPS_TINY` is 1e-4 in one and 1e-9 in
another. Which one a call site gets depends on which header it included and which namespace it is
in.

The first of those headers says so itself. Its comment records that `EPS_TINY`, `EPS_SMALL`,
`EPS_BIG`, `EPS_BIG2` and `SCALED_EPS_BIG` were given a new common value, and ends: *"needs to be
rationalised and eliminated!"*
([`eps.h#L14-L26`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/operations/boolean-utils/eps.h#L14-L26)).
Five tolerances that used to mean five different magnitudes now mean one, and the file asks for
that to be fixed. *(new row **P-24** in [`problems.md`](problems.md))*

### Where the maintainers locate precision loss

Not at float32, and this matters. On
[#292](https://github.com/ThatOpen/engine_web-ifc/issues/292) (CLOSED 2023-02-20), where
`IFCLENGTHMEASURE(0.16)` came back as `0.16000000000000003`, `beachtom` (**COLLABORATOR**) closed
it with the diagnosis that the imprecision is introduced in the transfer from C++ to JavaScript —
"but oddly enough not in the opposite direction". The fix was to keep values as **strings** inside
C++ and cast to double only in JS.

That is why our driver edits placements through the typed `GetLine`/`WriteLine` path and its
`_internalValue` string, and it is why
[#1464](https://github.com/ThatOpen/engine_web-ifc/issues/1464) (CLOSED 2025-07-09) replaced
numeric `value` keys with `_internalValue`/`_representationValue` getters — `beachtom`
(**COLLABORATOR**) explains it as "mainly loss of precision across the WASM/JS boundary". The
WASM/JS numeric boundary is, as of 2025, still an active design constraint.

On [#504](https://github.com/ThatOpen/engine_web-ifc/issues/504) (`COORDINATE_TO_ORIGIN` on a very
wide model) `beachtom` (**COLLABORATOR**) calls it "quite tricky because the model is so wide it
is giving a double precision error" — a **double** precision error, before float32 ever happens.
He closed the issue nine days later with "This is now fixed!", so this is a diagnosis of a
mechanism, **not** a standing defect in 0.0.77: what it establishes is that the maintainers
locate a class of precision loss above float32, not that wide models are broken today. So there
are two precision problems in this library's history, and only the float32 one is measured — and
only the float32 one is present in the shipped version by construction.

## Incremental evaluation

### The cache

`IfcGeometryProcessor` holds `_expressIDToGeometry`, an `unordered_map<uint32_t, IfcGeometry>`
keyed on the **geometry** express id, not the product — declared at
[`IfcGeometryProcessor.h#L73`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/IfcGeometryProcessor.h#L73)
and read through
[`IfcGeometryProcessor.cpp#L59-L62`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/IfcGeometryProcessor.cpp#L59-L62)
(`GetGeometry` returns `_expressIDToGeometry[expressID]`).
That is why the per-element distribution is so skewed: 0.016 ms median on the large model, because
most calls are map lookups for a representation an earlier element already built; and why the sum
of all per-element calls (244.1 ms) is within **18%** of `LoadAllGeometry` (296.6 ms) — the same
total work, distributed very unevenly.

### The invalidation call does not work

`IfcAPI.ResetCache(modelID)` is the only cache-invalidation call in the API, and its doc comment
names exactly this use case: "Resets the Cached IFC Data - useful when changing the geometry of a
model"
([`web-ifc-api.ts#L1522-L1529`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1522-L1529)).
In the published 0.0.77 package it throws:

```
IfcAPI has ResetCache: true
wasmModule exports ResetCache: false
call threw TypeError: this.wasmModule.ResetCache is not a function
```

Confirmed twice, independently. **At runtime**, by a probe on both benchmark models. **In the
source at the pinned tag**: `void ResetCache(uint32_t modelID)` exists at
[`web-ifc-wasm.cpp#L881-L885`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L881-L885)
but is **not registered** in that file's
[`EMSCRIPTEN_BINDINGS(my_module)` block, lines 947-1188](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L947-L1188),
in which the string `ResetCache` occurs zero times while every other exported function is listed.
The TypeScript wrapper calls an undefined property.

Even if it were reachable it would be the wrong granularity. `IfcGeometryProcessor::Clear()` does
`_expressIDToGeometry.clear()`, swaps the map to release its storage, and clears `_cache` — there
is no per-key erase anywhere
([`IfcGeometryProcessor.cpp#L64-L69`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/IfcGeometryProcessor.cpp#L64-L69)).
Invalidating one wall would discard every element's geometry.

### What that costs, measured

| Case | AC20-FZK-Haus | IFC_Schependomlaan | bbox shift after a verified 1 m edit |
|---|---|---|---|
| **warm** — evaluate, edit, request the same element again | 0.033 ms | 0.032 ms | **0.0 — the edit is not in the geometry** |
| **cold** — edit, then the element's first evaluation | 0.145 ms | 2.251 ms | 1.0 |
| **reopen** — `OpenModel` again, edit, `GetFlatMesh` | 15.8 ms | **266.8 ms** | 1.0 |
| **full** — `LoadAllGeometry` on the edited model | 89.0 ms | 222.6 ms | — |

The write reaches the model — the value reads back changed,
`write_took_effect_in_the_model: true` — it just never reaches the geometry. The warm row is what
a caller in an editing loop actually gets: 0.03 ms for **stale** geometry, with no error.

The only working route from an edit to correct geometry is to discard and re-open the model:
266.8 ms on a 3,822-element file, which re-parses everything. Against R-01's fail clause —
*"re-evaluation requires reprocessing the model, or exceeds 100 ms"* — both halves are met, and
neither depends on model size. Verdict and full method in
[`FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md).

A user hit the same gap from the other side. On
[#1380](https://github.com/ThatOpen/engine_web-ifc/issues/1380) (CLOSED 2025-04-16) a reporter
needed per-element `GetFlatMesh` in a loop but found memory grew without bound, because
`StreamAllMeshes` clears the processor internally and `GetFlatMesh` does not; his workaround was
to call `StreamMeshes` with a one-element array purely to trigger the clear, which he described as
an abuse of the interface. `beachtom` (**COLLABORATOR**) conceded "I think you are right we
probably need to add a TS hook to force a clear of the geometry loader cache manually", then
pointed at "a ClearCache commad" — a name that does not exist in the codebase.

**The thread was closed satisfied, and it is worth saying why**: the reporter (`avlsoraj`,
**NONE**) closed it himself with "Calling delete() on each geometry helps, thanks for pointing it
out. I had completely missed that method." His problem was per-mesh memory, and `Delete()` on
each returned geometry solved it. So this issue is **not** an open report of the invalidation
gap — no TS clear hook was added, and nobody in the thread was asking for one. It is cited here
only for what a COLLABORATOR conceded in passing about the cache's missing manual clear, which
is a weaker claim than "the gap has been known for over a year" and replaces it.

### The raw write path corrupts REALs

A separate probe, three cases each on its own freshly opened model:

| Case | AC20-FZK-Haus point 14980 | IFC_Schependomlaan point 13454 |
|---|---|---|
| before | `7.41`, `4.25`, `0.` | `5100.`, `3800.`, `250.` |
| `GetRawLineData` → `WriteRawLineData`, **nothing changed** | `nan`, `nan`, `nan` | `nan`, `nan`, `nan` |
| the same, one coordinate replaced by a JS number | `nan`, `nan`, `nan` | `nan`, `nan`, `nan` |
| typed `GetLine` → `WriteLine`, one coordinate changed | `8.41`, `4.25`, `0.` | `8.41`, `3800.`, `250.` |

**An unmodified raw round trip destroys every REAL on the line.** No issue on the tracker reports
this (searched: `WriteRawLineData nan`, `nan`, `NaN`, `IFCREAL nan`, `writes nan`), which is
consistent with almost nobody using web-ifc as an editable in-memory model.

The measurement therefore stands on its own. The nearest thing on the tracker is a PR that went
the *other* way and was merged 54 releases before the version measured here:
[#458](https://github.com/ThatOpen/engine_web-ifc/pull/458), "Preserve null values
when parsing number, boolean and logical" (by `simquat`, MERGED 2023-08-01), whose problem
statement — "null values are not preserved. Numbers … are converted to NaN" — describes the
behaviour it *removed*. It is cited here as a fix, not as the cause: whatever produces the `nan`
in 0.0.77's raw write path, this PR is not evidence of it. *(measured; new row **P-26** in
[`problems.md`](problems.md))*

## Known problems

Each speaker's login and verbatim `authorAssociation`. `beachtom` and `agviegas` are
**COLLABORATOR**; `QuimMoya` is **CONTRIBUTOR**; `HoyosJuan` is **MEMBER**; `pablo-mayrgundter` is
**CONTRIBUTOR**; other reporters are **NONE** unless stated. None of these people is labelled
OWNER by the API.

| Issue | State | What goes wrong | Root cause, and who says so |
|---|---|---|---|
| [#927](https://github.com/ThatOpen/engine_web-ifc/issues/927) — wall not rendered | OPEN, 2024-07-04 | An `IFCWALLSTANDARDCASE` produces no mesh while its window renders | `agviegas` (**COLLABORATOR**): "This is due to a bug in the core booleans", and in the same thread "Booleans is perhaps the most complex problem in our library". A commenter (`SimonSchneider`, **NONE**) traced it to `GetGeometry` returning an empty `IfcGeometry` whose position and bbox are `NaN`/`Inf` — a boolean failure surfacing as NaN vertex data |
| [#1057](https://github.com/ThatOpen/engine_web-ifc/issues/1057) — incorrect geometry with `IfcOpeningElement` | CLOSED 2024-10-20 | Wall geometry becomes wrong when a void relation is present; deleting the relation fixes it | `QuimMoya` (**CONTRIBUTOR**) acknowledged a cause was found but did not name it. A commenter reports the same source model exports correctly in IFC2x3 but not IFC4, and that a floor failed until a vertex **3 mm** from the boundary was hand-edited — near-coincidence sensitivity in the boolean |
| [#1774](https://github.com/ThatOpen/engine_web-ifc/issues/1774) — memory access out of bounds | OPEN, 2026-01-08 | Conversion crashes with a deeply self-recursive WASM stack trace | `beachtom` (**COLLABORATOR**): "There is something recursive in the geometry in this model that the library doesn't like… it is a known issue". `QuimMoya` (**CONTRIBUTOR**) localises it to a recursive `IFCBOOLEANRESULT` and explains it is unfixed because a fix "requires a huge artifact that mixes different logics". **There is no way to skip a failing element and continue** |
| [#1999](https://github.com/ThatOpen/engine_web-ifc/issues/1999) — `GetFlatMesh` crashes on large MEP models | OPEN, 2026-05-19, **zero comments**, version **0.0.77** | On ~400 MB models `GetFlatMesh` intermittently aborts with `memory access out of bounds`. After the abort, subsequent calls and even `CloseModel` throw — the WASM instance is unrecoverable | No maintainer reply. The version is the one measured here |
| [#538](https://github.com/ThatOpen/engine_web-ifc/issues/538) — abnormal exit on a very large model | OPEN, 2023-12-25, but **the reported symptom was addressed in-thread** | Writing 150,000 × 50 `IfcPolyLoop` aborts; 100,000 succeeds | `beachtom` (**COLLABORATOR**) first: "it seems like you are overfilling the WASM memory so we need to write the data out when that happens", then, a week later, "So this should now be fixed. I also added a method to write files out using a callback" — **a streaming write path was added**, followed by two further memory leaks found and fixed in the same thread. The ceiling that remained is named explicitly, and it is **not** the 2 GB `MEMORY_LIMIT` setting: "you are now hitting I think a hard limit of 4GB which is what WASM can hold in memory", and it applies to *created* lines — "if you are loading a model - you cannot add more than 4GB of IFC lines to it". The issue stays open on a later duplicate-line bug, not on the original abort |
| [#504](https://github.com/ThatOpen/engine_web-ifc/issues/504) — `COORDINATE_TO_ORIGIN` on a wide model | CLOSED 2024-01-28 — **"This is now fixed!"** (`beachtom`, **COLLABORATOR**) | Large coordinates cause visible precision problems, and translating to the origin bakes them in | `beachtom` (**COLLABORATOR**), while diagnosing: "this is quite tricky because the model is so wide it is giving a double precision error". **The diagnosis is what this note cites; the defect itself was fixed at the time and is not a standing limit of 0.0.77.** No fix mechanism is given in the thread, and none was verified here |
| [#292](https://github.com/ThatOpen/engine_web-ifc/issues/292) — numeric instability of real values | CLOSED 2023-02-20 | `0.16` reads back as `0.16000000000000003` | `beachtom` (**COLLABORATOR**): the imprecision is introduced in the transfer from C++ to JavaScript, "but oddly enough not in the opposite direction". Fixed by keeping values as strings in C++. Note the false-fix cycle: closed once as already fixed, demonstrated otherwise, reopened |
| [#214](https://github.com/ThatOpen/engine_web-ifc/issues/214) — written REALs are invalid EXPRESS | CLOSED 2023-02-16 | Integers emitted as `0` instead of `0.`, exponents as `e` not `E` | Recurring: the REAL write path has been fixed at least four separate times ([#214](https://github.com/ThatOpen/engine_web-ifc/issues/214), [#454](https://github.com/ThatOpen/engine_web-ifc/issues/454), [#470](https://github.com/ThatOpen/engine_web-ifc/issues/470), [#695](https://github.com/ThatOpen/engine_web-ifc/issues/695)), each closed by a maintainer as fixed and each followed by another case of the same class. Relevant because a modeller's round trip lives on that path |
| [#65](https://github.com/ThatOpen/engine_web-ifc/issues/65) — boolean elements render differently after a version bump | OPEN since 2021-07-23 | Doors and windows stop appearing. `beachtom` (**COLLABORATOR**) compares against another open IFC viewer in-thread | The oldest open geometry issue. Illustrates how these bugs are established at all: by comparison with another implementation, which is what P-10 formalises |
| [#1380](https://github.com/ThatOpen/engine_web-ifc/issues/1380) — `GetFlatMesh` vs `StreamMeshes` memory | CLOSED 2025-04-16 — **resolved by the reporter's own fix**, `Delete()` on each returned geometry | Per-element `GetFlatMesh` in a loop grows memory without bound | §Incremental evaluation. `beachtom` (**COLLABORATOR**) conceded in passing that "we probably need to add a TS hook to force a clear of the geometry loader cache manually" and named "a ClearCache commad", which does not exist. **Not a standing defect** — the reporter's memory problem was solved; the passing concession is all this row carries |

Two more boolean reports were read and are **not** given rows, because neither adds a mechanism
the table does not already carry — they are recorded here so the Sources list has a body
reference. [#398](https://github.com/ThatOpen/engine_web-ifc/issues/398) (CLOSED 2023-05-30,
reporter `andi-bu`, **NONE**) is wall openings disappearing in 0.0.39–0.0.41; `QuimMoya`
(**CONTRIBUTOR**) wrote "with the help of @beachtom we solved the issue" and `beachtom`
(**COLLABORATOR**) closed it with "Fix is merged" — a *fixed* instance of #927's class, useful
only as evidence that this class recurs across versions.
[#2062](https://github.com/ThatOpen/engine_web-ifc/issues/2062) (OPEN, 2026-07-07, reporter
`ShaMan123`, **NONE**) is the current one: boolean output that disagrees with Manifold's on the
same file, which the reporter used to produce the expected result. `agviegas` (**COLLABORATOR**)
re-attached the model; `thbeu` (**CONTRIBUTOR**) reports the same file renders empty in a
third-party viewer, so the input itself is disputed and nothing in the thread is settled. It is
the same evidentiary shape as #65: a defect established by comparison with another
implementation, which is what P-10 formalises.

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** **No.** The cache
   cannot be invalidated (the call throws), and would be model-wide if it could. Measured: the
   warm re-request returns stale geometry. *measured.*
2. **What happens to geometry on an IFC round trip?** The *geometry* round trip is not measured;
   the *attribute* round trip is, and the raw path turns every REAL on a line into `nan`
   (§The raw write path). The REAL writer has been repaired four times. *measured + claimed.*
3. **Driven in-process from DynLex?** Yes — WASM, no subprocess, no file. The constraint is the
   heap: the whole model must fit inside the WASM address space, which `beachtom`
   (**COLLABORATOR**) names as a hard 4 GB in #538. A callback-based *write-out* path was added
   in that thread, so output can stream; the in-memory model still cannot. *inferred +
   claimed.*
4. **Threading model?** Single-threaded. *inferred.*
5. **What breaks first at scale?** WASM memory, with an unrecoverable failure mode: after an
   out-of-bounds abort even `CloseModel` throws (#1999, on 0.0.77). *claimed.*
6. **Numeric precision?** `double` internally, **float32 out**. Two further loss points are
   acknowledged by maintainers, and both were repaired rather than being standing limits: the
   C++/JS boundary (#292, #1464 — the fix is `_internalValue` strings) and a double-precision
   error on a very wide model (#504, closed "This is now fixed!"). Only the float32 conversion is
   both measured here and unavoidable by design. *measured + claimed.*
7. **Operate on a subset of the model?** Reading, yes — `GetFlatMesh` and `StreamMeshes` take
   express ids. The tape's chunked eviction is the strongest subset-of-the-model design seen in
   this research, but it pages the *parse*, not the *evaluation*. *measured + source.*
8. **Who maintains it?** That Open Company. `beachtom` (**COLLABORATOR**) answers nearly every
   geometry and precision question. *claimed.*
9. **Documented failure modes?** §Known problems: ten issues, plus two measured here (`ResetCache`
   and the raw-write `nan`) that have **no** issue at all.
10. **Representations held natively?** Triangle meshes, one representation. *inferred.*
11. **How does geometry reach the GPU?** Interleaved float32 `[x,y,z,nx,ny,nz]`, as a pointer into
    `HEAPF32`. Nothing to convert — which is the whole design, and also the disqualification.
    *measured.*
12. **What would we take, and what would we avoid?** §Verdict.

## Measurements

Everything labelled *measured* is in
[`spikes/incremental-evaluation/results/webifc.md`](../../../spikes/incremental-evaluation/results/webifc.md)
and [`compare.md`](../../../spikes/incremental-evaluation/results/compare.md), produced by
`spikes/incremental-evaluation/webifc_driver.mjs` and `compare.py`. Hardware: Intel Core
i9-14900HX (32 logical processors), 32 GB RAM, Windows 11 `10.0.26200`, Node v24.11.1, `web-ifc`
0.0.77. Five repeats, median reported; each model in its own process.

Headline numbers: `OpenModel` 16.5 ms / 328.7 ms; `LoadAllGeometry` 85.3 ms / 296.6 ms for 103 /
3,643 meshes; process peak RSS 173.4 MB / 614.2 MB (a *process* peak, not a data size).

### And it agrees with IfcOpenShell

Worth stating because it is the opposite of what P-10 assumed. On IFC_Schependomlaan, of the
3,569 products both implementations produce, **3,556 agree on signed volume to within 1e-3
relative** and **3,530 produce identical triangle counts**. Where they disagree they disagree
badly (7 of 13 by more than 0.5 relative), but the disagreement rate between two independently
written engines is 0.36%. Full analysis in
[`compare.md`](../../../spikes/incremental-evaluation/results/compare.md).

## Strengths

- **Speed, measured**: 296.6 ms for a 3,643-mesh building, ~30× IfcOpenShell's OCCT path.
- **The token tape**: typed, offset-addressed, chunked and evictable, with the memory budget as a
  caller-visible setting. A paging design inside a parser.
- **No kernel dependency.** The whole engine is in one repository and builds to WASM, which is why
  it runs where OCCT cannot.
- **A GPU buffer with nothing in between** — interleaved float32, handed over as a heap pointer.
- **MPL-2.0**, the most permissive licence of the three implementations examined.
- **It agrees with IfcOpenShell on 99.6% of shared products**, which is a strong result for an
  independently written geometry engine.

## Weaknesses

- **float32 output**, unconditionally (§Precision).
- **No working cache invalidation**, so an edit is invisible to anything already evaluated, with
  no error (§Incremental evaluation).
- **`ResetCache` is dead code in the shipped build** — a documented API that throws.
- **Tolerance constants duplicated across three headers with conflicting values**, with the source
  itself asking for it to be rationalised.
- **An unmodified raw line round trip destroys every REAL on the line.**
- **Hard WASM heap ceiling** — 4 GB, named by a maintainer (#538) — with no spill for the model
  itself (the *write* path did gain a streaming callback in that thread), no way to skip a
  failing element, and an unrecoverable state after an out-of-bounds abort (#1774, #1999).
- **Single-threaded**, on a machine with 32 logical processors.

## Risks

The risk is not that web-ifc is slow or wrong; it is agreeing 99.6% of the time and failing
*silently* the rest. The stale-geometry case returns a plausible mesh with no error at 0.03 ms —
in an interactive modeller that is a wall that does not move, with nothing in any log. The same
shape appears in #927 (empty geometry with NaN bounds) and #1999 (a WASM instance that is dead but
still answers). Adopting this would mean building our own detection for failures the library does
not report.

## Verdict

### Build on — **no**, for the `ifc/` sub-project and for ADR-0004

Two independent disqualifying assumptions, each measured, each sufficient on its own:

1. **float32 output.** Every coordinate leaves through a `Float32Array`, by design, under a source
   comment naming WebGL as the reason. The kernels README's matrix already calls float32-only
   disqualifying for *build on*, and this note supplies the measurement: `7.410000019073486` for a
   file that says `7.41`. Internal doubles do not help a consumer that never sees them.
2. **No invalidation, therefore no incremental evaluation.** The one API call designed for it is
   not exported by the shipped WASM module and throws; and it is model-wide even in source. The
   measured consequence is a 0.0 m shift after a verified 1 m edit. There is no seam to add
   per-element invalidation from outside the library.

The batch-iterator assumption the brief asks about is *not* the disqualifier here — `GetFlatMesh`
is a genuine single-element call and is documented as one. What is missing is the other half:
knowing when a cached answer has stopped being true.

**web-ifc remains the right thing to read for viewing and for parsing**, and the recommendation
for ADR-0004 is to cite it as a *borrow from* rather than a *build on*.

### Borrow from — pinned

| What | Why | Where |
|---|---|---|
| **The chunked, evictable token tape**: typed one-byte tokens, attributes addressed by tape offset, chunks loaded on demand, evicted against a `maxChunks` budget derived from caller settings (`memoryLimit / tapeSize`) | The strongest answer in this research to "hold a model larger than memory and still answer attribute queries". R-14's tiling problem is the same problem one level up. Take the design, **not** the eviction policy (see Avoid) | [`IfcTokenStream.h`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcTokenStream.h), [`IfcTokenStream.cpp#L102-L131`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcTokenStream.cpp#L102-L131), [`IfcLoader.cpp#L24-L29`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/parsing/IfcLoader.cpp#L24-L29) |
| **Named, caller-settable tolerances as part of the open call** — seven of the twelve loader settings are tolerances with documented defaults, not hidden constants | Our spec §5 wants explicit tolerances; this is the API shape, and it beats a single global `precision`. The *implementation* below it is the counter-example (see Avoid) | [`web-ifc-api.ts#L442-L459`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L442-L459) |
| **Strings across the language boundary for REAL values**, with the numeric cast on the far side (`_internalValue` / `_representationValue`) | `beachtom` (**COLLABORATOR**) located the precision loss at the C++→JS transfer (#292) and this was the fix. Any DynLex FFI carrying coordinates has the identical problem | [#292](https://github.com/ThatOpen/engine_web-ifc/issues/292), [#1464](https://github.com/ThatOpen/engine_web-ifc/issues/1464) |
| **Two geometry-delivery paths with different memory behaviour** — `LoadAllGeometry` (returns everything) and `StreamAllMeshes` (callback per mesh, clears as it goes) | Measured: 296.6 ms vs 237.5 ms, and the streaming path does not accumulate. Our kernel should offer both, and should make the difference in *retention* explicit rather than implicit | [`web-ifc-api.ts#L1341-L1395`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1341-L1395); [results](../../../spikes/incremental-evaluation/results/webifc.md) |

### Avoid — each mapped to a design choice, each with a P-row

| Failure | Design choice it traces to | Our design's answer |
|---|---|---|
| **An edit reaches the model but not the geometry, silently**: 0.0 m shift after a verified 1 m translation, returned in 0.03 ms with no error | A cache with no notion of the input having changed — geometry is keyed on an id that does not change when the geometry's inputs do | Every cached result records what it was derived from; a changed input invalidates its dependents (spec §3). **P-06**, measured |
| **The one invalidation call in the API is not exported by the shipped module and throws** | An API surface whose TypeScript and WASM sides are not checked against each other; the call has no test and is referenced by no issue | Public API is generated from one definition, and a binding that does not resolve is a build failure, not a runtime `TypeError` (spec §12). **P-06** — this is the reason the invalidation mechanism P-06 describes is unavailable in practice rather than merely coarse |
| **float32 output, unconditionally** | The interchange type is chosen for the GPU and doubles as the *only* output type | f64 storage and f64 out; f32 only in the camera-relative upload buffer (spec §5, ADR-0006). **P-05**, measured — the same conclusion [`manifold.md`](manifold.md) reaches about `MeshGL` |
| **The same tolerance name means 1e-4 in one namespace and 1e-6 in another**, and five once-distinct magnitudes were collapsed into one value — the header itself says it "needs to be rationalised and eliminated!" | Tolerances as free constants in headers rather than values carried by the operation | One tolerance authority; a tolerance is a value an operation carries, not a constant a translation unit happens to include (spec §5). **New row P-24** |
| **An unmodified raw read/write round trip turns every REAL on the line into `nan`** | Two parallel attribute APIs, one of which is not exercised by anything the maintainers run | One attribute path. A round trip that changes nothing must produce a byte-identical result, and that is a test, not an aspiration. **New row P-26**, measured |
| **A failing element takes the whole conversion down, with no skip-and-continue** (#1774, #1999), and after an abort even `CloseModel` throws | Failure is an abort of the process, not a value | A failure is a typed result for *that element*; the conversion continues and reports which elements failed (spec §12). **P-01** |
| **The in-memory model must fit the WASM heap — 4 GB, no spill** (#538) — while the *parser's* own tape does page to chunks, and while the *write* path did eventually get a streaming callback in the same thread | The paging design was applied to the token tape, then to the write path when a user hit it, and never to the model or the geometry | The paging budget applies to every large store, not only the ones where it was first needed (spec §8). **P-13.** The retrofit order in #538 is itself the lesson: each store got paged only after someone hit its ceiling |

## Sources

- [ThatOpen/engine_web-ifc](https://github.com/ThatOpen/engine_web-ifc) at tag `0.77`, commit
  `f26c4beef0a668ebdb180d2b95a94097a1e21cef`
- The installed npm package `web-ifc` `0.0.77`; `IfcAPI.GetVersion()` confirms the version
- Issues [#65](https://github.com/ThatOpen/engine_web-ifc/issues/65),
  [#214](https://github.com/ThatOpen/engine_web-ifc/issues/214),
  [#292](https://github.com/ThatOpen/engine_web-ifc/issues/292),
  [#398](https://github.com/ThatOpen/engine_web-ifc/issues/398),
  [#504](https://github.com/ThatOpen/engine_web-ifc/issues/504),
  [#538](https://github.com/ThatOpen/engine_web-ifc/issues/538),
  [#927](https://github.com/ThatOpen/engine_web-ifc/issues/927),
  [#1057](https://github.com/ThatOpen/engine_web-ifc/issues/1057),
  [#1380](https://github.com/ThatOpen/engine_web-ifc/issues/1380),
  [#1464](https://github.com/ThatOpen/engine_web-ifc/issues/1464),
  [#1774](https://github.com/ThatOpen/engine_web-ifc/issues/1774),
  [#1999](https://github.com/ThatOpen/engine_web-ifc/issues/1999),
  [#2062](https://github.com/ThatOpen/engine_web-ifc/issues/2062);
  PR [#458](https://github.com/ThatOpen/engine_web-ifc/pull/458)
- [`spikes/incremental-evaluation/`](../../../spikes/incremental-evaluation/) — drivers, raw
  results, [`FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md),
  [`results/webifc.md`](../../../spikes/incremental-evaluation/results/webifc.md),
  [`results/compare.md`](../../../spikes/incremental-evaluation/results/compare.md)
