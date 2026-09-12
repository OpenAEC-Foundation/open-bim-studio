# `blender-ceiling`

**Question (R-03):** Blender's documented ceiling around 30–80k objects — is it Blender's object
model or Bonsai's implementation? If it is Blender's, a whole branch of the host decision closes.

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-03, written before any
driver ran: pass (for Blender) is *interactive at 100k objects*, fail is *the viewport degrades
regardless*.

## What this spike measures, and what it does not

R-03's criterion names the viewport. This driver runs **headless** (`--background`), so it draws
nothing: no viewport, no outliner, no draw manager, no selection. It therefore **cannot** deliver
the pass verdict, and says so rather than implying otherwise.

What it can deliver is the other half, and the sharper one: a **lower bound**. Everything measured
here is a cost Blender pays before any pixel is drawn, and it is paid by `bpy` alone with no
add-on in the process — so a ceiling that already shows up here is Blender's object model, not
Bonsai's, and adding the interface can only make it worse.

The measurement that matters is not construction time but the **incremental** one: move a single
object and re-run `view_layer.update()` with everything else untouched. That is what a user pays
on every frame of a drag, and an interactive editor has about 16 ms to spend on it.

Each object count is built two ways with the same triangles in both:

* **separate** — one mesh datablock and one object per box, which is how an IFC importer maps
  elements to Blender;
* **single** — the same boxes as disconnected shells inside one mesh, one object.

The difference between them is per-object overhead with geometry volume held constant. That is
the number [`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md)
P-07 is about.

## Layout

```
blender_driver.py      the driver (runs inside Blender's own Python)
FINDINGS.md            the numbers against R-03's criterion, and what they do not settle
results/blender.md     raw results
```

[`FINDINGS.md`](FINDINGS.md) applies R-03's criterion to the rows in `results/blender.md` and adds
no measurement of its own. The candidate-facing reading — what the numbers mean for Blender as a
host — is in
[`../../docs/research/kernels/blender.md`](../../docs/research/kernels/blender.md) §Measurements
and §Incremental evaluation — the depsgraph.

## Running it

```bash
"C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
    --factory-startup --python spikes/blender-ceiling/blender_driver.py -- \
    --counts 1000,10000,100000 --repeats 5
```

from the repository root. `--factory-startup` is not optional: without it the user's add-ons are
loaded into the measured process, which is exactly the confound R-03 is about.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Standard library plus `bpy` only;
nothing here is a design proposal for `kernel/`.
