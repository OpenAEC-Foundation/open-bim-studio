# IfcOpenShell — measurements

Written from `ifcopenshell_AC20-FZK-Haus.json` and `ifcopenshell_IFC_Schependomlaan.json` in
this directory, produced by `../ifcopenshell_driver.py`. Console transcripts of the runs that
produced them: `ifcopenshell_run_AC20-FZK-Haus.txt`, `ifcopenshell_run_IFC_Schependomlaan.txt`.
Every number below appears in one of those files.

## Hardware, versions, settings

| | |
|---|---|
| CPU | Intel(R) Core(TM) i9-14900HX, 32 logical processors |
| RAM | 32 GB |
| OS | Windows 11, `10.0.26200` |
| Python | 3.12.10 |
| `ifcopenshell` (Python) | `0.8.4.post1` |
| `ifcopenshell` (native) | `ifcopenshell_wrapper.version()` reports `0.8.0` |
| `psutil` | 7.2.2 |
| Repeats | 5 per timed **whole-model** operation and per edit test, median reported. The per-element pass is **one sample per element** — see §Per-element evaluation |

### Which OCCT the wheel bundles, and how we know

The wheel statically links its dependencies — there are no OCCT DLLs in the package, only
`_ifcopenshell_wrapper.cp312-win_amd64.pyd` (55,774,720 bytes). The version was read out of
the strings in that binary:

```
strings -n 5 _ifcopenshell_wrapper.cp312-win_amd64.pyd | grep -iE "7\.[0-9]\.[0-9]"
  *** ERROR: ASSERT in file 'D:\a\IfcOpenShell\IfcOpenShell\_deps-vs2022-x64-installed\
      opencascade-7.8.1\inc\BVH_QueueBuilder.hxx':
```

The build-machine include path names the version: **OCCT 7.8.1**. The same scan shows
`_deps-vs2022-x64-installed\cgal\include\CGAL`, `_deps\boost_1_86_0`, `_deps\hdf5-1_13_1`,
`_deps\mpfr`, `_deps\mpir` and `_deps\rocksdb`, plus mangled `CGAL::Lazy_exact_nt<Gmpq>`
symbols — so **CGAL is compiled into the same wheel**, with GMP/MPFR behind it. That is what
makes the four-way kernel comparison below possible without building anything.

*Labelled: measured (the strings are in the installed binary); the mapping from the include
path to the shipped version is inferred from that path.*

### Source pin

There is **no `v0.8.4` tag** on `IfcOpenShell/IfcOpenShell` — `git ls-remote --tags` shows the
library's own release tags stop at `v0.7.1`, and the 0.8 line is tagged only through the Bonsai
add-on. The nearest tag carrying this version number is **`bonsai-0.8.4`**, commit
`158fe92644cfe2bc37be513d9838c95d9f2233cf`, and that is what every source citation in
[`../../../docs/research/kernels/ifcopenshell.md`](../../../docs/research/kernels/ifcopenshell.md)
points at. The wheel is not provably built from that commit; the pin is the closest published
tree to the version string, and is labelled that way wherever it is used.

### Settings

`ifcopenshell.geom.settings()` with three values set explicitly —
`use-world-coords` True (so vertices are comparable with web-ifc's), `weld-vertices` True and
`apply-default-materials` True (both already the default, stated for the record). Everything
else is the library default. The JSON files carry the full dump of all 52 setting names; the
ones that matter here:

`precision` 1e-05 · `mesher-linear-deflection` 0.001 · `mesher-angular-deflection` 0.5 ·
`circle-segments` 16 · `disable-boolean-result` False · `disable-opening-subtractions` False ·
`convert-back-units` False · `cache-shapes` False · `no-parallel-mapping` False ·
`iterator-output` 0 (TRIANGULATED).

`cache-shapes` being **off** matters for the R-01 numbers: no `create_shape` call below returns
a cached result.

## Four geometry libraries, not one

`typing.get_args(ifcopenshell.geom.GEOMETRY_LIBRARY)` on the installed wheel returns
`('cgal', 'cgal-simple', 'opencascade', 'hybrid-cgal-simple-opencascade')`, and both
`geom.iterator(...)` and `geom.create_shape(...)` take a `geometry_library` argument
defaulting to `opencascade`. All four were measured.

**Full geometry iteration, whole model, median of 5 runs:**

| Model | library | threads | median | runs (s) | elements | process peak |
|---|---|---|---|---|---|---|
| AC20-FZK-Haus | opencascade | 1 | **3.229 s** | 3.295, 3.493, 3.229, 3.163, 3.135 | 107 | 126 MB |
| AC20-FZK-Haus | opencascade | 32 | **1.038 s** | 1.068, 1.038, 1.034, 1.014, 1.043 | 107 | 204 MB |
| AC20-FZK-Haus | cgal | 32 | — **crashed** | — | — | — |
| AC20-FZK-Haus | cgal-simple | 32 | **0.086 s** | 0.080, 0.100, 0.091, 0.086, 0.084 | 103 | 130 MB |
| AC20-FZK-Haus | hybrid-cgal-simple-opencascade | 32 | **0.666 s** | 0.666, 0.663, 0.666, 0.654, 0.731 | 107 | 172 MB |
| IFC_Schependomlaan | opencascade | 1 | **21.688 s** | 21.566, 22.213, 21.688, 24.788, 20.798 | 3,654 | 602 MB |
| IFC_Schependomlaan | opencascade | 32 | **9.013 s** | 9.229, 9.013, 9.924, 8.316, 8.268 | 3,654 | 759 MB |
| IFC_Schependomlaan | cgal | 32 | — **crashed** | — | — | — |
| IFC_Schependomlaan | cgal-simple | 32 | **0.651 s** | 0.649, 0.637, 0.651, 0.682, 0.700 | 3,646 | 676 MB |
| IFC_Schependomlaan | hybrid-cgal-simple-opencascade | 32 | **0.687 s** | 0.655, 0.680, 0.687, 0.712, 0.737 | 3,654 | 686 MB |

Parse time (`ifcopenshell.open`, median of 5): **0.136 s** for AC20-FZK-Haus (44,249
instances, IFC4) and **2.231 s** for IFC_Schependomlaan (714,485 instances, IFC2X3).

**Process peak working set** is `psutil`'s `peak_wset` — a *process* peak, not the size of the
data. Each geometry library runs in its own child process (see below), so each row's figure is
that configuration's own. The whole-run peaks were 226.8 MB and 1,091.6 MB.

Three things in that table are worth stating plainly:

1. **Threading works and is worth about 3.1× and 2.4×** (3.229 → 1.038 s; 21.688 → 9.013 s on
   32 logical processors). Element counts are identical at both thread counts.
2. **`hybrid-cgal-simple-opencascade` produces the same 107 / 3,654 elements as
   `opencascade`, 1.6× and 13.1× faster.** On the larger model that is 9.013 s → 0.687 s for
   the same element count. It is **not** the default of the Python API (*measured* — the
   `geometry_library` argument defaults to `opencascade`), and it is the single largest
   performance lever measured here. That Bonsai uses it is *claimed*, not verified here:
   `Andrej730` (`authorAssociation: CONTRIBUTOR`) states on
   [IfcOpenShell#6142](https://github.com/IfcOpenShell/IfcOpenShell/issues/6142) that the
   default Python settings differ from Bonsai's in two ways, one of them "using 'opencascade'
   geometry library while Bonsai is using 'hybrid-cgal-simple-opencascade'". No Bonsai source
   was read for this spike.
3. **`cgal-simple` is faster still (0.651 s) but produces fewer elements** — 103 vs 107, and
   3,646 vs 3,654 — and the elements it does produce are not all the same geometry. See
   [`compare.md`](compare.md): it returns an *empty* result for walls with openings. The
   hybrid kernel is what reconciles the two.

### The CGAL kernel crashes the process, non-deterministically

`geometry_library="cgal"` killed the child process on both models, with no Python traceback and
nothing on stderr:

| Model | return code | hex | meaning |
|---|---|---|---|
| AC20-FZK-Haus | 3221226356 | `0xC0000374` | `STATUS_HEAP_CORRUPTION` |
| IFC_Schependomlaan | 3221225477 | `0xC0000005` | `STATUS_ACCESS_VIOLATION` |

It is **not** a deterministic refusal. In an earlier run of the same command on
AC20-FZK-Haus the `cgal` library completed all five repeats, 107 elements, median 2.508 s;
in the run that produced the committed JSON it crashed. Same file, same command, same machine.
A one-off probe of `cgal` at `num_threads` 32 and 1 outside the driver also completed three
times in a row (107 elements, 2.3–2.5 s at 32 threads, 6.0 s at 1). So the correct statement is:
**`cgal` completes sometimes and corrupts the heap sometimes**, and the committed run is one of
each. Neither a rate nor a trigger is established here.

This is also why the driver runs every geometry library in its own child process: constructing
iterators for more than one library inside a single process reliably killed that process, taking
the completed measurements with it.

## Per-element evaluation — the R-01 measurement

`geom.create_shape(settings, element)` is the only public way IfcOpenShell offers to produce the
geometry of **one** element, so it is the cost of re-evaluating one element after a change. It
was timed separately for **every** element the iterator produced.

**Sampling: once per element, not five times.** The five-repeat rule stated at the top of this
file applies to the whole-model and edit-test operations. This pass times each element **once**
(`per_element_create_shape` walks `produced_ids` and times one `create_shape` call per id), so
the median below is a median over 107 or 3,654 elements, and **p90 / p95 / p99 / max are single
measurements of single elements**. What corroborates the tail is the slowest-element edit test
further down, which re-times the worst element five times, and the sum-versus-whole-model
cross-check immediately after the table.

This is a *pessimistic* proxy, and the source says why: `helper_fn_create_shape` constructs a
fresh `Converter` — and therefore a fresh kernel and a fresh mapping — on every call
([`IfcGeomWrapper.i#L885-L889`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcwrap/IfcGeomWrapper.i#L885-L889)).
Any setup an incremental implementation would hold across edits is charged to every number below.

| Model | n | min | median | p90 | p95 | p99 | max | sum | **under 16 ms** | under 100 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | 107 | 1.03 ms | **1.63 ms** | 43.40 ms | 238.23 ms | 529.55 ms | 539.59 ms | 3.216 s | **83 / 107 (77.6%)** | 100 / 107 |
| IFC_Schependomlaan | 3,654 | 0.59 ms | **2.06 ms** | 6.96 ms | 16.96 ms | 69.34 ms | 553.97 ms | 21.030 s | **3,445 / 3,654 (94.3%)** | 3,648 / 3,654 |

**Cross-check:** the sum of the per-element times (3.216 s, 21.030 s) is close to the
single-threaded whole-model iteration median for the same model (3.229 s, 21.688 s). The
per-element path costs what the batch path costs; it is not a cheaper route to the same result,
and the two measurements corroborate each other.

The slowest elements, which are what the tail is made of:

| Model | Slowest three |
|---|---|
| AC20-FZK-Haus | `IfcWallStandardCase` 539.6 ms, `IfcWallStandardCase` 529.5 ms, `IfcStair` 362.0 ms |
| IFC_Schependomlaan | `IfcWindow` 554.0 ms, `IfcWindow` 530.0 ms, `IfcWindow` 529.8 ms |

Two `IfcWallStandardCase` alone account for a third of AC20-FZK-Haus's total.

## Element counts, and failures by entity type

The counting rule is in the driver and repeated in the JSON: an `IfcProduct` is counted if its
`Representation` is set, excluding `IfcOpeningElement`, `IfcOpeningStandardCase`, `IfcSpace`,
`IfcGrid` and `IfcAnnotation`.

| Model | `IfcProduct` | with `Representation` | counted by the rule | iterator produced |
|---|---|---|---|---|
| AC20-FZK-Haus | 127 | 121 | 83 | 107 |
| IFC_Schependomlaan | 3,822 | 3,752 | 3,573 | 3,654 |

The `IfcProduct` totals match `reference/README.md` exactly (127 and 3,822), and every one of
the 12 and 15 per-class counts that file lists matches too — checked mechanically by
`compare.py`, which parses those numbers out of the README rather than having them retyped
(`reference_count_check` in `compare_raw.json`, zero mismatches).

The iterator produces **more** than the rule counts because it also emits openings and spaces,
which the rule excludes; that is the same 24 and 85 rows [`compare.md`](compare.md) reports as
"only in IfcOpenShell".

**Failures by entity type**, from running `create_shape` on every `IfcProduct` that has a
`Representation` and that the iterator did *not* produce:

| Model | Entity type | n | Outcome |
|---|---|---|---|
| AC20-FZK-Haus | `IfcAnnotation` | 14 | filtered by the default context/type filter — not attempted |
| IFC_Schependomlaan | `IfcSpace` | 94 | filtered by the default context/type filter — not attempted |
| IFC_Schependomlaan | **`IfcWall`** | **4** | **`create_shape` raised `RuntimeError`** |

Four `IfcWall` in IFC_Schependomlaan cannot be converted at all. `compare_raw.json` names four
`IfcWall` GUIDs that web-ifc emitted (with zero triangles) and IfcOpenShell's table lacks; the
counts agree, and the identification of those four with these four is *inferred*, not measured —
the driver records the failing class, not the failing GlobalId.

No element that the iterator *did* produce raised on a standalone `create_shape`
(`create_shape_raised` is empty for both models).

## What the log says

`ifcopenshell_wrapper.get_log()`, read after the per-element and failure passes. **Scope
caveat:** the library accumulates into this log throughout the process, not only while detailed
logging is on, so the summary covers the per-element pass as well. Detailed logging is never
enabled inside a timed region — it writes parser progress to stdout and would distort the
timings — which is why no per-iteration log files are written.

| Model | lines | Warning | Notice | Error |
|---|---|---|---|---|
| AC20-FZK-Haus | 247 | 21 | 108 | 49 |
| IFC_Schependomlaan | 5,158 | 4,086 | 725 | 57 |

Messages are grouped with digit runs replaced by `<n>`. The five most frequent on
IFC_Schependomlaan:

| Count | Message |
|---|---|
| 3,654 | `[Warning] Precision lower than <n>.<n> meter not enforced` |
| 161 | `[Warning] No material and surface styles for:` |
| 139 | `[Notice] Used fuzziness: <n>.<n>` |
| 128 | `[Warning] Degenerate face boundary in normal estimation` |
| 79 | `[Notice] Min OBB dimension of operand = <n>.<n>` |

and further down, 45 × `[Warning] Self-intersections with <n> cycles detected` and 57 ×
`[Error] Failed to convert:`.

Three readings:

1. **The precision floor is 1e-7 m and it is hit on every single element.** The message is
   `Precision lower than 0.0000001 meter not enforced`, and it appears exactly 3,654 times — once
   per element. The file asks for a finer tolerance than the library will honour, on every
   element, and the only signal is a warning nobody reads.
2. **Errors are logged and swallowed.** AC20-FZK-Haus logs 49 `[Error] Failed to convert:` while
   `create_shape` raised **zero** exceptions and the iterator's
   `had_error_processing_elements()` returned False on every run. "Failed to convert" is written
   for a sub-item and the element still produces geometry. A caller who checks only the return
   value sees success.
3. **The entity is on the next line, not the message line.** `[Error] Failed to convert:` is
   followed by an untagged line such as `#<n>=IfcMaterial('Solid',$,$)`. The driver's grouping
   counts each line once and therefore does not join the two, which is why the instance lines
   appear as their own `<none>`-severity group rather than as an entity-type attribution.

## The R-01 edit test

One element's `ObjectPlacement.RelativePlacement` (`IfcAxis2Placement3D`) `Location` is
translated 1 m along X by rewriting the `IfcCartesianPoint` in place, and its geometry is
produced again. Each of the five repeats re-opens the file, so the edit is applied to a fresh
model every time and no shape or file object is reused across repeats.

Two elements per model: the first suitable `IfcWall`, and the element with the **largest**
`create_shape` time from the per-element pass — so the worst case is measured, not only a
convenient one.

| Model | Element | `GlobalId` | Express id | triangles | single re-evaluation (median of 5) | individual runs | full re-iteration (32 threads) | ratio |
|---|---|---|---|---|---|---|---|---|
| AC20-FZK-Haus | first `IfcWallStandardCase` | `2XPyKWY018sA1ygZKgQPtU` | 15042 | 12 | **1.02 ms** | 1.08, 0.96, 0.94, 1.02, 1.70 | 1.065 s | 1,044× |
| AC20-FZK-Haus | slowest element, `IfcWallStandardCase` | `0knNIAVBPBFvBy_m5QVHsU` | 60012 | 788 | **530.54 ms** | 552.2, 531.6, 530.5, 516.6, 525.3 | 0.978 s | 1.8× |
| IFC_Schependomlaan | first `IfcWall` | `3cAt3keOr5IAqWcOfbuNAx` | 13529 | 12 | **1.46 ms** | 1.53, 1.46, 1.43, 1.28, 1.49 | 8.025 s | 5,488× |
| IFC_Schependomlaan | slowest element, `IfcWindow` | `3Wp4aZh5H6qPRVFtOem3_A` | 948940 | 7,604 | **623.59 ms** | 677.3, 685.5, 565.4, 623.6, 536.2 | 8.683 s | 13.9× |

The spread between the two rows per model is the whole finding. Re-evaluating *a* wall costs
1–1.5 ms against a 1.1–8.0 s whole-model pass — three to four orders of magnitude. Re-evaluating
*the worst* element costs 530–624 ms, which is 33–39× the 16 ms R-01 threshold, and on the small
model is within a factor of two of re-converting the entire building.

### There is no stale-cache hazard, and no reuse either

The edit-visibility probe runs three cases, each on its own freshly opened file: no edit;
edit-then-first-evaluation ("cold"); evaluate-then-edit-then-evaluate-again ("warm"). The
element's bounding-box minimum x is recorded, so a 1 m translation shows as 1.0.

| Model | cold shift | warm shift |
|---|---|---|
| AC20-FZK-Haus | 1.0 | **1.0** |
| IFC_Schependomlaan | 1.0 | **1.0** |

The edit is always visible. That is the opposite of web-ifc's result (warm shift 0.0, see
[`webifc.md`](webifc.md)) and it has the same cause as the pessimistic timing above: because
`create_shape` builds a fresh `Converter` per call, there is no cache to go stale — and equally,
nothing is reused between two re-evaluations of the same element.

The mapping layer *does* cache, but only inside one converter's lifetime:
`mapping::map` looks up `inst->identity()` in `cache_` under a mutex and inserts on miss, with
no invalidation path
([`mapping.cpp#L693-L721`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/mapping/mapping.cpp#L693-L721)).
The iterator has a second, persistent cache keyed on GlobalId plus representation id
([`Iterator.h#L161-L194`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/Iterator.h#L161-L194)),
with no *automatic* invalidation — its HDF5 serializer does expose a manual
`remove(GlobalId)`, which Bonsai calls
([IfcOpenShell#1785](https://github.com/IfcOpenShell/IfcOpenShell/issues/1785), `Moult`,
`authorAssociation: CONTRIBUTOR`), so the caller can evict an entry it has itself decided is
stale. Neither cache is exercised by `create_shape`, and `cache-shapes` was off for every
measurement here.

## Element tables

`ifcopenshell-<library>_<model>_elements.csv`: one row per element the iterator produced, with
GUID, IfcClass, express id, triangle count, vertex count, signed volume and bounding box. Built
in a separate, untimed pass — the volume function is plain Python and is never inside a timed
region.

| Model | library | rows | rows with zero triangles |
|---|---|---|---|
| AC20-FZK-Haus | opencascade | 107 | 0 |
| AC20-FZK-Haus | cgal-simple | 103 | 7 |
| IFC_Schependomlaan | opencascade | 3,654 | 65 |
| IFC_Schependomlaan | cgal-simple | 3,646 | 71 |

The signed volume is `1/6 · Σ a · (b × c)` over the triangles in world coordinates — the same
formula the web-ifc driver implements separately, so the two are comparable. It is a volume only
for a closed, consistently oriented shell; negative values in the tables mark shells that are
not, and IFC_Schependomlaan's tables contain several.

**The GUID join is sound for these files:** both models have zero `IfcProduct` GlobalIds used
more than once (127 distinct of 127, 3,822 of 3,822), so no two products can collapse into one
row in [`compare.md`](compare.md). (IfcOpenShell does log one non-unique-GlobalId warning on
IFC_Schependomlaan; the count above covers `IfcProduct` only, which is what the join uses.)
