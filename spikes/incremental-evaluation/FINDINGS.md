# FINDINGS — R-01, incremental evaluation in IfcOpenShell and web-ifc

## The question, restated

Can an existing IFC implementation re-evaluate the geometry of a **single changed element**
without reprocessing the model?

The pass/fail criteria were written before this spike ran and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-01:

> - **Pass:** single-element re-evaluation under 16 ms on a 100k-element model.
> - **Fail:** re-evaluation requires reprocessing the model, or exceeds 100 ms.

## Hardware and versions

| | |
|---|---|
| CPU | Intel(R) Core(TM) i9-14900HX, 32 logical processors |
| RAM | 32 GB |
| OS | Windows 11 Pro, `10.0.26200` |
| Python | 3.12.10; `ifcopenshell` `0.8.4.post1` (native `0.8.0`), bundling **OCCT 7.8.1** and CGAL |
| Node | v24.11.1; `web-ifc` npm `0.0.77` (`IfcAPI.GetVersion()` agrees) |
| xBIM | **not measured** — no .NET SDK on this machine; see [`../../docs/research/kernels/xbim.md`](../../docs/research/kernels/xbim.md) |

## Models

Both from [`../../reference/`](../../reference/), unchanged, with the SHA-256 recorded there:

| Model | Schema | File size | `IfcProduct` | Elements with geometry |
|---|---|---|---|---|
| `AC20-FZK-Haus.ifc` | IFC4 | 2,570,803 bytes | 127 | 107 (IfcOpenShell) / 103 (web-ifc) |
| `IFC_Schependomlaan.ifc` | IFC2X3 | 49,286,967 bytes | 3,822 | 3,654 / 3,643 |

**Neither model is anywhere near 100k elements.** The larger is 3,822 `IfcProduct` — about 4%
of the size the criterion names. This is the central limitation of this spike and it is stated
again in the verdict.

## Method

Five repeats of every timed operation, median reported; each repeat opens a fresh model, so no
object is reused across repeats. Each model runs in its own process. The element-table pass that
computes volumes is separate and untimed. Full method, and how to reproduce it, in
[`README.md`](README.md); the numbers are in
[`results/ifcopenshell.md`](results/ifcopenshell.md), [`results/webifc.md`](results/webifc.md)
and the JSON files beside them.

Two measurements bear on R-01.

**(1) The whole distribution, not one element.** `create_shape(settings, element)` (IfcOpenShell)
and `GetFlatMesh(modelID, expressID)` (web-ifc) are the only public single-element geometry
calls each library offers. Both were timed **separately for every element in the model**, so the
answer is a distribution rather than one convenient sample.

**(2) The edit test.** One `IfcWall`'s `IfcAxis2Placement3D` `Location` is translated 1 m along
X, and its geometry is requested again. The element's bounding-box minimum x is recorded every
time, so a 1 m translation shows as a shift of 1.0 — whether a measured time is a real
re-evaluation or a cache hit is **decided by that number, not assumed**. In IfcOpenShell the test
is run twice per model: on the first suitable wall, and on the element with the largest
`create_shape` time in the model, so the worst case is measured too.

## Results

### IfcOpenShell — per-element evaluation cost

| Model | n | median | p90 | p95 | p99 | max | **under 16 ms** | under 100 ms |
|---|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | 107 | 1.63 ms | 43.40 ms | 238.23 ms | 529.55 ms | 539.59 ms | **83 / 107 (77.6%)** | 100 / 107 |
| IFC_Schependomlaan | 3,654 | 2.06 ms | 6.96 ms | 16.96 ms | 69.34 ms | 553.97 ms | **3,445 / 3,654 (94.3%)** | 3,648 / 3,654 |

Cross-check: the per-element totals (3.216 s, 21.030 s) match the single-threaded whole-model
iteration medians (3.229 s, 21.688 s). The single-element path costs what the batch path costs.

This number is **pessimistic by construction**: `helper_fn_create_shape` builds a fresh
`Converter` — a fresh kernel and a fresh mapping — on every call
([`IfcGeomWrapper.i#L885-L889`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcwrap/IfcGeomWrapper.i#L885-L889)).
A real incremental implementation would hold that setup across edits.

### IfcOpenShell — the edit test

| Model | Element | `GlobalId` | triangles | single re-evaluation | full re-iteration (32 threads) | ratio |
|---|---|---|---|---|---|---|
| AC20-FZK-Haus | first `IfcWallStandardCase` | `2XPyKWY018sA1ygZKgQPtU` | 12 | **1.02 ms** | 1.065 s | 1,044x |
| AC20-FZK-Haus | slowest element | `0knNIAVBPBFvBy_m5QVHsU` | 788 | **530.54 ms** | 0.978 s | 1.8x |
| IFC_Schependomlaan | first `IfcWall` | `3cAt3keOr5IAqWcOfbuNAx` | 12 | **1.46 ms** | 8.025 s | 5,488x |
| IFC_Schependomlaan | slowest element, `IfcWindow` | `3Wp4aZh5H6qPRVFtOem3_A` | 7,604 | **623.59 ms** | 8.683 s | 13.9x |

The edit is visible in both the cold and the warm case (bbox shift 1.0 and 1.0 on both models):
there is no stale-cache hazard, because there is no cache across `create_shape` calls — and
therefore no reuse either.

### web-ifc — per-element evaluation cost

| Model | n | median | p90 | p95 | p99 | max | under 16 ms |
|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | 103 | 0.013 ms | 1.09 ms | 1.83 ms | 30.60 ms | 31.18 ms | 101 / 103 |
| IFC_Schependomlaan | 3,643 | 0.016 ms | 0.072 ms | 0.233 ms | 0.425 ms | 16.76 ms | 3,639 / 3,643 |

These look extraordinary and must not be read as re-evaluation costs. web-ifc caches geometry per
**geometry express id**, so once one element using a representation has been built, every other
element sharing it is a map lookup. The per-element totals (82.3 ms and 244.1 ms) again match
`LoadAllGeometry` (85.3 ms and 296.6 ms): the same total work, distributed very unevenly.

### web-ifc — the edit test

| Case | AC20-FZK-Haus | IFC_Schependomlaan | bbox shift |
|---|---|---|---|
| **warm** — evaluate, edit, request again | 0.033 ms | 0.032 ms | **0.0 — the edit is not in the geometry** |
| **cold** — edit, then first evaluation | 0.145 ms | 2.251 ms | 1.0 |
| **reopen** — `OpenModel` again, edit, `GetFlatMesh` | 15.8 ms | 266.8 ms | 1.0 |
| **full** — `LoadAllGeometry` on the edited model | 89.0 ms | 222.6 ms | — |

The warm case is what a caller in an editing loop actually hits, and it returns **stale**
geometry at 0.03 ms. The write itself reaches the model (`write_took_effect_in_the_model: true`,
value reads back changed); it just never reaches the geometry.

`IfcAPI.ResetCache(modelID)` is the only cache-invalidation call in the API, and its doc comment
names this exact use case. **It throws in the published 0.0.77 build**:

```
IfcAPI has ResetCache: true
wasmModule exports ResetCache: false
call threw TypeError: this.wasmModule.ResetCache is not a function
```

Confirmed twice: at runtime on both models, and in the source at tag `0.77` — the C++ function
exists at
[`web-ifc-wasm.cpp#L881-L885`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L881-L885)
but is **not registered** in that file's
[`EMSCRIPTEN_BINDINGS(my_module)` block, lines 947-1188](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L947-L1188),
in which `ResetCache` occurs zero times. Even if it were reachable it is **model-wide**:
`IfcGeometryProcessor::Clear()` empties the whole `_expressIDToGeometry` map with no per-key
erase.

So the measured cost of making one edit visible in web-ifc 0.0.77 is the **reopen** row: 15.8 ms
and **266.8 ms**, which re-parses the entire file.

## Verdict against the R-01 criterion

The criterion is quoted at the top. Judged against it:

### web-ifc — **fail**

Both clauses of the fail condition are met, and neither depends on model size:

- *"re-evaluation requires reprocessing the model"* — yes. The only working route from an edit
  to updated geometry is to discard and re-open the model. `ResetCache`, the one call designed
  to avoid that, is not exported by the shipped WASM module; and it is model-wide anyway.
- *"or exceeds 100 ms"* — 266.8 ms on a **3,822-element** model. The threshold is exceeded at 4%
  of the size the criterion names.

This verdict is **size-independent** and therefore stands despite the model-size limitation
below: no larger model is needed to establish that the mechanism does not exist.

### IfcOpenShell — **pass on the median, fail on the tail; not decidable at 100k**

- The median element re-evaluates in **1.63 ms** and **2.06 ms**, comfortably under 16 ms, and
  re-evaluation genuinely does not reprocess the model — 1,044x and 5,488x cheaper than a full
  iteration for a typical wall.
- But **5.7%** of elements on the real building (209 of 3,654) exceed 16 ms, and the worst
  exceeds **550 ms** — over five times the *fail* threshold of 100 ms. Six elements exceed 100 ms
  on IFC_Schependomlaan; seven of 107 do on AC20-FZK-Haus.
- A modeller must be interactive when the user drags *the window*, not only when they drag the
  median wall. On this evidence IfcOpenShell would miss a 16 ms frame budget on roughly one
  element in twenty, and miss it by a factor of thirty on the worst.

### What this does **not** settle

1. **The 100k-element criterion is untested.** The larger benchmark model has 3,822
   `IfcProduct` — 4% of 100k. For IfcOpenShell the per-element cost is a property of *that
   element's* representation, not of the model's size, so there is a reasonable expectation it
   would carry (labelled **inferred**, not measured) — but the *full-model* fallback it is
   compared against grows with the model, the parse cost grows with the model (0.136 s to 2.231 s
   for a 19x file), and the process peak grows with the model (227 MB to 1,092 MB). Nothing here
   measures what happens at 100k, and the synthetic scale models in `reference/` exist precisely
   to close that gap.
2. **Neither library was measured with a dependency graph in front of it.** Moving a wall in a
   real modeller re-evaluates the wall *and its openings, its junctions and its 2D views*. This
   spike moved one placement and re-evaluated one element. The realistic cost is higher by
   whatever the dependency fan-out is, and that fan-out is unmeasured. Benchmark case 3 in
   `reference/README.md` ("A parametric change scenario") is still marked *to be written*.
3. **`create_shape`'s cost includes per-call setup** that an incremental implementation would
   amortise, so IfcOpenShell's numbers are an upper bound on what its own machinery could do —
   but nobody has built that, and issue
   [#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386) is where the maintainer
   explains why it is hard (see [`../../docs/research/kernels/ifcopenshell.md`](../../docs/research/kernels/ifcopenshell.md)).
4. **Nothing here is a correctness statement.** A fast wrong answer is measured the same as a
   fast right one; see [`results/compare.md`](results/compare.md) for what the two
   implementations disagree about.
5. **xBIM is absent.** Its answer is read from source and documentation only, and it is a
   clearer *no* than either of these — whole-model regeneration is enforced at the storage
   contract.

## What the risk status should become

**This spike does not edit [`../../docs/risks.md`](../../docs/risks.md).** What the evidence
supports, for whoever does:

- R-01 should stay **open**, because its own criterion has not been tested at its own scale.
- It should no longer be open *for lack of evidence about existing implementations*. For those,
  the answer is now measured: **web-ifc fails outright and the failure is size-independent;
  IfcOpenShell passes at the median and fails in the tail, on a model 4% of the criterion's
  size.**
- The remaining question is narrower and should be written as such: **does a per-element
  re-evaluation cost that is independent of model size survive at 100k elements, and what does
  the dependency fan-out of a single wall move add to it?** That is two measurements — the
  synthetic scale models, and a defined parametric-change scenario — not an open-ended risk.
- The consequence clause in R-01 ("we write our own evaluation layer over a geometry kernel, and
  the semantic kernel becomes I/O only") is **already indicated for both implementations**, on
  different grounds: web-ifc has no invalidation mechanism at all, and IfcOpenShell has
  per-element evaluation but no dependency tracking to drive it — the caching it does have
  "is written with the idea that the underlying model is static", in the words of a maintainer
  (`aothms`, `authorAssociation: MEMBER`,
  [#4386](https://github.com/IfcOpenShell/IfcOpenShell/issues/4386)).
