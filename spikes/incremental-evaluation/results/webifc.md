# web-ifc — measurements

Written from `webifc_AC20-FZK-Haus.json` and `webifc_IFC_Schependomlaan.json` in this
directory, produced by `../webifc_driver.mjs`. Console transcripts of the runs that produced
them: `webifc_run_AC20-FZK-Haus.txt`, `webifc_run_IFC_Schependomlaan.txt`. Every number below
appears in one of those files.

## Hardware, versions, settings

| | |
|---|---|
| CPU | Intel(R) Core(TM) i9-14900HX, 32 logical processors |
| RAM | 32 GB |
| OS | Windows_NT 10.0.26200 |
| Node | v24.11.1 |
| web-ifc | npm `0.0.77`; `IfcAPI.GetVersion()` also reports `0.0.77` |
| Source read at | tag `0.77`, commit `f26c4beef0a668ebdb180d2b95a94097a1e21cef` (that tag's `package.json` declares version `0.0.77`) |
| Repeats | 5 per timed operation, median reported |

Loader settings passed to `OpenModel`, which are web-ifc's own defaults restated verbatim
from `CreateSettings()` in [`src/ts/web-ifc-api.ts#L442-L459`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L442-L459):

`COORDINATE_TO_ORIGIN` false · `CIRCLE_SEGMENTS` 12 · `TAPE_SIZE` 67108864 ·
`MEMORY_LIMIT` 2147483648 · `LINEWRITER_BUFFER` 10000 ·
`TOLERANCE_PLANE_INTERSECTION` 1.0e-4 · `TOLERANCE_PLANE_DEVIATION` 1.0e-4 ·
`TOLERANCE_BACK_DEVIATION_DISTANCE` 1.0e-4 · `TOLERANCE_INSIDE_OUTSIDE_PERIMETER` 1.0e-10 ·
`TOLERANCE_SCALAR_EQUALITY` 1.0e-4 · `PLANE_REFIT_ITERATIONS` 1 ·
`BOOLEAN_UNION_THRESHOLD` 150.

`USE_FAST_BOOLS`, which older documentation mentions, does not exist at this tag —
`grep -rn USE_FAST_BOOLS src/` returns nothing. The named `TOLERANCE_*` settings above are
what the version actually exposes.

## Load and whole-model geometry

| Model | Schema | Lines | `OpenModel` median | `LoadAllGeometry` median | meshes | `StreamAllMeshes` median | callbacks |
|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | IFC4 | 44,249 | 16.5 ms | 85.3 ms | 103 | 81.6 ms | 83 |
| IFC_Schependomlaan | IFC2X3 | 714,485 | 328.7 ms | 296.6 ms | 3,643 | 237.5 ms | 3,569 |

`StreamAllMeshes` calls back fewer times than `LoadAllGeometry` returns meshes: 83 vs 103 on
the small model, 3,569 vs 3,643 on the large one. The two paths are therefore **not**
interchangeable if the count matters — a caller who streams sees 74 fewer elements on
IFC_Schependomlaan than one who calls `LoadAllGeometry`.

The shortfall is 20 and 74. The element tables record 20 and **139** rows with zero
triangles. On the small model those two numbers coincide, on the large one they do not, so
"the missing callbacks are exactly the empty meshes" is **not** established by these
measurements — on IFC_Schependomlaan at least 65 rows with zero triangles must still reach
the callback. What is measured is the shortfall itself; its cause is not.

**Process peak RSS**, a running maximum of `process.memoryUsage().rss` sampled after each
phase. This is a *process* peak — it includes the WASM heap, the Node heap and the driver's
own arrays — and is not the size of the model data:

| Model | Process peak RSS | File size |
|---|---|---|
| AC20-FZK-Haus | 173.4 MB | 2,570,803 bytes |
| IFC_Schependomlaan | 614.2 MB | 49,286,967 bytes |

Each model was measured in its own process (`--model` is required), so the larger model's
figure does not contain the smaller one's.

## Per-element evaluation

One freshly opened model on which nothing has been evaluated, then `GetFlatMesh(modelID,
expressID)` timed once per element in express-id order — so each call is the first
evaluation of that element. `GetFlatMesh` is documented as "Load geometry for a single
element" ([`web-ifc-api.ts#L1397-L1405`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1397-L1405)).

| Model | n | median | p90 | p95 | p99 | max | sum | under 16 ms |
|---|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | 103 | 0.013 ms | 1.09 ms | 1.83 ms | 30.60 ms | 31.18 ms | 82.3 ms | 101 / 103 |
| IFC_Schependomlaan | 3,643 | 0.016 ms | 0.072 ms | 0.233 ms | 0.425 ms | 16.76 ms | 244.1 ms | 3,639 / 3,643 |

**Cross-check:** the sum of the per-element times (82.3 ms, 244.1 ms) is close to the
`LoadAllGeometry` median for the same model (85.3 ms, 296.6 ms). The per-element path does
the same total work as the batch path; it is not a cheaper route to the same result.

The distribution is extremely skewed because web-ifc caches geometry **per geometry express
id, not per product**: the first element using a representation pays for it and every later
element sharing it is served from `_expressIDToGeometry`
([`IfcGeometryProcessor.cpp#L59-L62`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/IfcGeometryProcessor.cpp#L59-L62)).
On AC20-FZK-Haus the two slowest elements (31.18 ms and 30.60 ms, both
`IfcWallStandardCase`) account for 75% of the total; on IFC_Schependomlaan the three slowest
are `IfcDistributionElement` at 16.76, 16.69 and 16.29 ms. The median is therefore the cost
of a **cache hit**, not of an evaluation.

## The R-01 edit test

One `IfcWall`'s `IfcAxis2Placement3D` `Location` is translated 1 m along X by rewriting the
`IfcCartesianPoint` through `GetLine` / `WriteLine`, and the element's geometry is requested
again. The element's bounding-box minimum x is recorded each time, so a 1 m translation
shows as a shift of 1.0 — whether a measured time is a regeneration or a cache hit is
**decided by that number, not assumed**.

| Model | Element | `GlobalId` | Express id |
|---|---|---|---|
| AC20-FZK-Haus | IfcWallStandardCase | `2XPyKWY018sA1ygZKgQPtU` | 15042 (placement point 14980) |
| IFC_Schependomlaan | IfcWall | `3cAt3keOr5IAqWcOfbuNAx` | 13529 (placement point 13454) |

The write itself takes effect in the model in both cases: the value reads back as the new
one (`write_took_effect_in_the_model: true`; 7.41 → 8.41 in metres, 5100 → 6100 in
millimetres).

| Case | AC20-FZK-Haus | IFC_Schependomlaan | bbox shift |
|---|---|---|---|
| **warm** — evaluate, edit, re-request the same element | 0.033 ms | 0.032 ms | **0.0 — the edit is not in the geometry** |
| **cold** — edit first, then the element's first evaluation | 0.145 ms | 2.251 ms | 1.0 |
| **reopen** — `OpenModel` again, apply the edit, then `GetFlatMesh` | 15.8 ms | 266.8 ms | 1.0 |
| **full** — `LoadAllGeometry` over the whole edited model | 89.0 ms | 222.6 ms | (103 / 3,643 meshes) |

The warm case is the one a caller in an editing loop actually hits, and it returns the
**stale** geometry: 0.033 ms for a result that does not contain the edit. There is no cheap,
correct single-element re-evaluation here.

### `ResetCache` is unreachable in this build

`IfcAPI.ResetCache(modelID)` is the only cache-invalidation call the API exposes, and its
doc comment names exactly this use case — "Resets the Cached IFC Data - useful when changing
the geometry of a model" ([`web-ifc-api.ts#L1522-L1529`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1522-L1529)). It does not work in the published 0.0.77 package:

```
IfcAPI has ResetCache: true
wasmModule exports ResetCache: false
call threw TypeError: this.wasmModule.ResetCache is not a function
```

Confirmed twice, independently:

1. **At runtime**, by the probe above, on both models (`reset_cache_probe` in both JSON
   files).
2. **In the source at the pinned tag**: the C++ function exists at
   [`web-ifc-wasm.cpp#L881-L885`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L881-L885)
   but is **not registered** in that file's `EMSCRIPTEN_BINDINGS` block
   ([`EMSCRIPTEN_BINDINGS(my_module)`, lines 947-1188](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/wasm/web-ifc-wasm.cpp#L947-L1188)),
   which lists every other exported function; `ResetCache` occurs zero times inside it. The TS wrapper
   therefore calls an undefined property.

Even if it were reachable, it is **model-wide**: `IfcGeometryProcessor::Clear()` does
`_expressIDToGeometry.clear()` and `_cache.Clear()` with no per-key erase
([`IfcGeometryProcessor.cpp#L64-L69`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/IfcGeometryProcessor.cpp#L64-L69)).
Invalidating one wall would discard every element's geometry.

So the measured cost of making one edit visible in web-ifc 0.0.77 is the **reopen** row:
15.8 ms on the small model and 266.8 ms on the larger one — which re-parses the entire file.

### The raw write path corrupts REALs

A separate probe, three cases each on its own freshly opened model:

| Case | AC20-FZK-Haus (`IfcCartesianPoint` 14980) | IFC_Schependomlaan (13454) |
|---|---|---|
| before | `7.41`, `4.25`, `0.` | `5100.`, `3800.`, `250.` |
| A — `GetRawLineData` → `WriteRawLineData`, **nothing changed** | `nan`, `nan`, `nan` | `nan`, `nan`, `nan` |
| B — the same, one coordinate replaced by a JS number | `nan`, `nan`, `nan` | `nan`, `nan`, `nan` |
| C — typed `GetLine` → `WriteLine`, one coordinate changed | `8.41`, `4.25`, `0.` | `8.41`, `3800.`, `250.` |

An unmodified raw round trip destroys every REAL on the line. This is why the edit test uses
the typed `GetLine`/`WriteLine` path, and the reason is measured rather than assumed. (Case
C writes the literal 8.41 in both models, including the millimetre one — that is the probe's
fixed test value, not a unit conversion.)

## Element tables

`webifc_<model>_elements.csv`: one row per mesh returned by `LoadAllGeometry`, with GUID,
IfcClass, express id, triangle count, signed volume and bounding box. Built in a separate,
untimed pass.

| Model | Rows | Rows with zero triangles |
|---|---|---|
| AC20-FZK-Haus | 103 | 20 |
| IFC_Schependomlaan | 3,643 | 139 |

The signed volume is `1/6 · Σ a · (b × c)` over the triangles, in world coordinates, after
applying each placed geometry's `flatTransformation`. It is a well-defined function of the
triangles either way, but it is only a *volume* for a closed, consistently oriented shell —
negative values in the tables mark shells that are not.

## Vertex precision: float32 at the boundary

web-ifc computes in `double` internally (`std::vector<double> vertexData`) and converts to
`float` for export. `IfcGeometry::GetVertexData()` resizes a parallel `std::vector<float>
fvertexData` and copies each entry, under the comment "unfortunately webgl can't do doubles"
([`IfcGeometry.cpp#L220-L238`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/cpp/web-ifc/geometry/representation/IfcGeometry.cpp#L220-L238)).
On the JS side `GetVertexArray` reads `HEAPF32` and returns a `Float32Array`
([`web-ifc-api.ts#L1305-L1307`](https://github.com/ThatOpen/engine_web-ifc/blob/f26c4beef0a668ebdb180d2b95a94097a1e21cef/src/ts/web-ifc-api.ts#L1305-L1307)).

The measurement shows the consequence directly: the wall's reference bounding-box minimum x
reads `7.410000019073486` where the file says `7.41`, and `4.359756112553707` on the
millimetre model. Every coordinate that leaves web-ifc has been through float32, whatever
precision produced it.
