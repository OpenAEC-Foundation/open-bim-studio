# `tessellation`

**Question:** what does it cost a candidate kernel to turn 10k elements into triangles, and how
much does the quality parameter change that cost? This is the number behind
[`problems.md`](../../docs/research/kernels/problems.md) P-11 — "tessellation quality vs. speed:
chords too coarse for drawings, too fine for the viewport" — which is only a real problem if the
two qualities actually cost different amounts.

There is no pass/fail line in [`../../docs/risks.md`](../../docs/risks.md) for this one: it is a
cost measurement feeding the kernel spec's conversion design, not a risk gate. The
[kernels README](../../docs/research/kernels/README.md) *Performance* criterion is what it serves.

**Model:** the 10k synthetic scale model, generated rather than committed:

```bash
python reference/generate_scale_models.py --count 10000 --out build/scale_10k.obj
```

## Running the OCCT driver

```bash
pip install cadquery-ocp==8.0.1.0.0      # bundles OCCT 8.0.1
python spikes/tessellation/occt_driver.py --parallel
```

from the repository root. It writes [`results/occt.md`](results/occt.md). `--parallel` adds a
second row per deflection using `BRepMesh_IncrementalMesh`'s `isInParallel` flag, and the driver
always runs a sphere control so that a null result from that flag can be told apart from a build
with no working threading.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). `build/` is generator output and is
not committed.
