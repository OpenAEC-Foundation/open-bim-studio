# FINDINGS — R-03, Blender's object-count ceiling

This file adds no measurement. Every number below is copied from a named row of
[`results/blender.md`](results/blender.md), which is the reproducible record.

## The question, restated

Blender's documented ceiling around 30–80k objects — is it **Blender's object model** or
**Bonsai's implementation**? If it is Blender's, a whole branch of the host decision closes.

The criteria were fixed before the driver ran and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-03:

> - **Spike:** `spikes/blender-ceiling/` — generate 100k trivial objects directly via `bpy`,
>   bypassing Bonsai. Measure viewport interactivity and selection.
> - **Pass (for Blender):** interactive at 100k objects → the ceiling is Bonsai's, Blender reopens.
> - **Fail:** viewport degrades regardless → architectural, Blender is out.

## Hardware, OS and versions

*Measured*, recorded by the driver itself ([`results/blender.md`](results/blender.md)
§Environment): Blender `5.0.0`, build hash `a37564c4df7a`, build date `2025-11-18 11:06:54`;
platform `Windows 10.0.26200 (AMD64)`; Intel Core i9-14900HX (`Intel64 Family 6 Model 183
Stepping 1`); 32 GB installed RAM. Startup `--factory-startup`, `--background` — no interface,
no drawing. Five repeats per incremental timing, median reported. **Run date:** 2026-09-10.

## Model and inputs

No file from [`../../reference/`](../../reference/). The driver generates its own input inside
Blender: **N unit boxes of 12 triangles each**, at N = 1 000, 10 000, 100 000, built two ways
with the triangle count held identical between them —

- **separate** — one mesh datablock and one object per box, which is how an IFC importer maps
  elements to Blender;
- **single** — the same boxes as disconnected shells inside **one** mesh, one object.

## Method

[`blender_driver.py`](blender_driver.py), run inside Blender's own Python under
`--background --factory-startup` (see [`README.md`](README.md) §Running it). For each count and
variant it builds the scene, times the **first full evaluation**, then times the measurement that
matters: move a **single** object and re-run `view_layer.update()` with everything else untouched
— the cost a user pays on every frame of a drag, against a frame budget of roughly 16 ms.
`--factory-startup` is not optional: without it the user's add-ons are in the measured process,
which is the exact confound R-03 is about. The difference between *separate* and *single* at the
same triangle count is per-object overhead with geometry volume held constant.

## The numbers

Copied from [`results/blender.md`](results/blender.md) §Results (all six rows) — *measured*:

| Objects | Variant | Datablocks (obj / mesh) | Triangles | Build ms | First full eval ms | Incremental ms | Memory |
|---|---|---|---|---|---|---|---|
| 1000 | separate | 1000 / 1000 | 12000 | 44.95 | 34.38 | **1.138** | 81 MB |
| 1000 | single | 1 / 1 | 12000 | 7.896 | 6.259 | **0.0054** | 3 MB |
| 10000 | separate | 10000 / 10000 | 120000 | 480.1 | 446.8 | **16.29** | 619 MB |
| 10000 | single | 1 / 1 | 120000 | 228.9 | 197.7 | **0.0128** | -29 MB |
| 100000 | separate | 100000 / 100000 | 1200000 | 3.529e+04 | 1.147e+04 | **332.1** | 6232 MB |
| 100000 | single | 1 / 1 | 1200000 | 2457 | 4409 | **0.018** | 2900 MB |

And §Per-object overhead, the same file — *measured*, arithmetic over the rows above:

| Objects | Δ build ms | Δ full eval ms | Δ incremental ms | Δ memory / object |
|---|---|---|---|---|
| 1000 | 37.06 | 28.12 | 1.133 | 77578 B |
| 10000 | 251.2 | 249.2 | 16.27 | 64755 B |
| 100000 | 3.284e+04 | 7058 | 332.1 | 33313 B |

## Verdict

**R-03 as written is not answered by this spike, and cannot be.** Its criterion names *viewport*
interactivity and selection; this driver runs headless and draws nothing, so neither the pass
("interactive at 100k objects") nor the fail ("viewport degrades regardless") can be evaluated
from it. It is recorded as **half answered**, which is how
[`../../docs/risks.md`](../../docs/risks.md) R-03 carries it.

**The half that is answered is the half the register was uncertain about: the ceiling is
Blender's, not Bonsai's.** *Measured*, headless, through `bpy` with no add-on in the process, one
moved object costs **16.29 ms at 10 000 objects** — the whole of a 16 ms frame — and **332.1 ms at
100 000**, about twenty frames. The 100k scene's first full evaluation costs **11.47 s** and it
occupies **6232 MB**, ≈65 kB per object at 10k (64 755 B) falling to 33 313 B at 100k.

*Inferred*, from the two variants at equal triangle count: what is being counted is **Blender
datablocks, not geometry volume**. The same 1 200 000 triangles held as **one** object cost
**0.018 ms** per update against 332.1 ms, and no add-on can avoid that, because one IFC element
must be one datablock for the element to be selectable and attributable at all.

Because every number here is paid before any pixel is drawn, it is a **lower bound**: the
interface can only make it worse. A lower bound that already consumes the frame budget at 10 000
objects is the finding.

**What R-03's status should become** is a judgement for the risk register, not for this file, and
[`../../docs/risks.md`](../../docs/risks.md) is deliberately left unedited by this spike.

## What this does not settle

- **The viewport, the outliner, the draw manager and selection are unmeasured** — all of which
  can make the numbers worse and none of which can make them better. A headless driver cannot
  close that gap; a viewport measurement would be a different spike ([`README.md`](README.md)
  §What this spike measures, and what it does not).
- **Blender's disqualification does not rest on this.** Blender is out as a *build on* candidate
  on three independent grounds — GPL licence, float32 vertex storage, no embedding path
  ([`../../docs/research/kernels/blender.md`](../../docs/research/kernels/blender.md) §Verdict) —
  so this measurement does not decide the host question by itself.
- **The boxes are synthetic and uniform.** Nothing here measures modifier stacks, materials,
  drivers, or a real IFC import, each of which adds per-object cost this driver does not pay.

## Where this lands

[`../../docs/research/kernels/blender.md`](../../docs/research/kernels/blender.md)
§Object-count ceiling (R-03, partial) and §Incremental evaluation — the depsgraph;
[`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md) **P-07**,
for which this is the evidence that per-object overhead is the scale ceiling to design against.
