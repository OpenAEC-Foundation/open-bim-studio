# Spike: incremental evaluation (R-01) and implementation disagreement (P-10)

**The question this spike answers:** can an existing IFC implementation re-evaluate the
geometry of a *single changed element* without reprocessing the model — and do two
implementations reading the same file produce the same geometry?

Two risks, one driver set, because both need the same thing: per-element geometry from more
than one implementation on the same benchmark model.

- **R-01** (see [`../../docs/risks.md`](../../docs/risks.md)) — *"single-element
  re-evaluation under 16 ms on a 100k-element model"* is the pass criterion. Our benchmark
  models are far smaller than 100k elements, so this spike **cannot** settle R-01 as written;
  what it can and cannot conclude is stated in [`FINDINGS.md`](FINDINGS.md).
- **P-10** (see [`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md))
  — "IFC geometry interpreted differently by different implementations" was a hypothesis with
  no evidence. `compare.py` replaces it with counts.

This is a **throwaway spike**. It is not a foundation for anything; see
[`../README.md`](../README.md).

## What is measured

Per model, per implementation:

| | IfcOpenShell | web-ifc |
|---|---|---|
| Parse / load | `ifcopenshell.open` | `IfcAPI.OpenModel` |
| Whole-model geometry | `geom.iterator`, `num_threads` 1 and 32, for all four geometry libraries the wheel exposes | `LoadAllGeometry` and `StreamAllMeshes` |
| Single-element geometry | `geom.create_shape(settings, element)` | `GetFlatMesh(modelID, expressID)` |
| Per-element distribution | every element timed separately: median, p95, max, and how many fall under 16 ms | the same |
| Edit test | translate one `IfcWall`'s `IfcAxis2Placement3D` by 1 m, then re-evaluate | the same, through `WriteLine` |
| Element table | GUID, IfcClass, triangles, signed volume, bbox — per geometry library | the same |
| Process peak memory | `psutil` `peak_wset` | `process.memoryUsage().rss`, running maximum |

Process peak memory is a **process** peak. It is not the size of the data, and it is not
presented as one. Each model runs in its own process so the number is not inflated by a
previous model.

Both drivers compute the signed volume with the same formula — `1/6 · Σ a · (b × c)` over
triangles, in world coordinates — implemented separately in each language. A difference in
the number is therefore a difference in the triangles each implementation produced, not a
difference in how they were measured.

xBIM is **not** measured: no .NET SDK is installed on this machine (`dotnet --list-sdks`
prints nothing; only runtimes are present), and XbimGeometry needs a C++/CLI build. The
xBIM note is documentation-and-source only, and `compare.py` is therefore a two-way
comparison, not a three-way one.

## How to run it

Requires the two benchmark models in `../../reference/models/` (gitignored — see
[`../../reference/README.md`](../../reference/README.md) for acquisition and SHA-256),
Python with `ifcopenshell` and `psutil`, and Node with `web-ifc` installed here.

```bash
cd spikes/incremental-evaluation
npm install                                   # web-ifc 0.0.77, into ./node_modules

python ifcopenshell_driver.py --model AC20-FZK-Haus       --repeats 5
python ifcopenshell_driver.py --model IFC_Schependomlaan  --repeats 5
node   webifc_driver.mjs     --model AC20-FZK-Haus       --repeats 5
node   webifc_driver.mjs     --model IFC_Schependomlaan  --repeats 5
python compare.py
```

The web-ifc driver also takes `--collect-only`, which runs nothing but the untimed element-table
pass and rewrites `results/webifc_<model>_elements.csv`, leaving `results/webifc_<model>.json`
and every timing in it untouched:

```bash
node   webifc_driver.mjs     --model AC20-FZK-Haus       --collect-only
node   webifc_driver.mjs     --model IFC_Schependomlaan  --collect-only
```

Use it only for the element table. Any change to a *timed* path means re-running the driver in
full, and then every number quoted from that JSON has to be re-checked.

Each driver takes one model per run on purpose — see the memory note above. The IfcOpenShell
driver re-invokes itself as a child process for each geometry library, because constructing
iterators for more than one geometry library inside a single process crashes that process
(recorded in the results; the crash is itself a finding).

Runtimes on the hardware in the results files: a few minutes for `AC20-FZK-Haus`, roughly
ten minutes for `IFC_Schependomlaan`. Nothing here needs a network connection.

## Output

Raw, machine-written, one file per driver per model:

- `results/ifcopenshell_<model>.json`, `results/webifc_<model>.json`, `results/compare_raw.json`
- `results/ifcopenshell-<library>_<model>_elements.csv`, `results/webifc_<model>_elements.csv`
- `results/*_run_<model>.txt` — the console transcript of the run that produced the JSON

Written by hand from those files, and citing them:

- [`results/ifcopenshell.md`](results/ifcopenshell.md), [`results/webifc.md`](results/webifc.md),
  [`results/compare.md`](results/compare.md) — the tables, with hardware and versions
- [`FINDINGS.md`](FINDINGS.md) — the R-01 verdict against the criterion, quoted verbatim

Every number in the three notes in `docs/research/kernels/` that is labelled *measured*
comes from a file in `results/`, and can be traced to it by name.
