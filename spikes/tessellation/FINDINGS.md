# FINDINGS — P-11, what tessellating 10k elements costs, and what the quality parameter changes

This file adds no measurement. Every number below is copied from a named row of
[`results/occt.md`](results/occt.md), which is the reproducible record.

## The question, restated

What does it cost a candidate kernel to turn 10k elements into triangles, and how much does the
**quality parameter** change that cost? This is the number behind
[`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md) **P-11** —
"tessellation quality vs. speed: chords too coarse for drawings, too fine for the viewport" —
which is only a real problem if the two qualities actually cost different amounts. A second
question rides along, and is the architectural half of P-11: **is a second tessellation of an
already-meshed shape skipped, a full re-mesh, or a replacement of the cached triangulation?**

**There is no pass/fail criterion in [`../../docs/risks.md`](../../docs/risks.md) for this spike**
— it is a cost measurement feeding the kernel spec's conversion design (spec §4), not a risk gate.
It feeds **P-11** and the *Performance* criterion in
[`../../docs/research/kernels/README.md`](../../docs/research/kernels/README.md), quoted verbatim:

> | **Performance** | Measured on the benchmark set: load, boolean, tessellation, pick at 10k / 100k / 1M | High |

## Hardware, OS and versions

*Measured*, recorded by the driver ([`results/occt.md`](results/occt.md) §Environment): Python
`3.12.10`; platform `Windows 11 (AMD64)`; processor `Intel64 Family 6 Model 183 Stepping 1,
GenuineIntel`; `cadquery-ocp` `8.0.1.0.0`; OCCT `8.0.1` (bundled by that wheel).
`OSD_ThreadPool::DefaultPool()->NbThreads()` reports **32** on this machine. **Run date:**
2026-09-10.

## Model and inputs

`build/scale_10k.obj` — **10 000 unit boxes** from
[`../../reference/generate_scale_models.py`](../../reference/generate_scale_models.py)
`--count 10000`, generated rather than committed, parsed in **49 ms**. The model is **entirely
planar**, which is why the triangle count is constant across deflections and only the time moves.
Two controls use different inputs: **400 spheres** at deflection 0.0005, and **one sphere** in the
re-meshing probe, because a planar face meshes to the same two triangles at every deflection and
so cannot show whether a cache was replaced.

## Method

[`occt_driver.py`](occt_driver.py), run from the repository root with `--parallel`
([`README.md`](README.md) §Running the OCCT driver). It sweeps `BRepMesh_IncrementalMesh`'s
`theLinDeflection` over four decades (1, 0.1, 0.01, 0.001) with angular deflection held at 0.5 rad,
each deflection run twice — once single-threaded, once with `isInParallel` — and always runs the
sphere control so that a null result from the parallel flag can be told apart from a build with no
working threading. A third probe re-meshes an already-meshed shape and compares against a
**rebuilt** compound. **Construction-method note, from the README:** each box is a native
`BRepPrimAPI_MakeBox` rather than sewn from twelve triangles, because otherwise construction
rather than tessellation would dominate the wall clock — so these build times are **not**
comparable with the boolean spikes' construction numbers.

## The numbers

*Measured*, copied from [`results/occt.md`](results/occt.md) §Results — all eight rows:

| Linear deflection | Mode | Done? | Build ms | Mesh ms | Triangles | µs / triangle |
|---|---|---|---|---|---|---|
| 1 | single | yes | 243 | 4171 | 120,000 | 34.8 |
| 1 | parallel | yes | 255 | 4732 | 120,000 | 39.4 |
| 0.1 | single | yes | 260 | 4489 | 120,000 | 37.4 |
| 0.1 | parallel | yes | 252 | 4856 | 120,000 | 40.5 |
| 0.01 | single | yes | 255 | 4453 | 120,000 | 37.1 |
| 0.01 | parallel | yes | 258 | 4899 | 120,000 | 40.8 |
| 0.001 | single | yes | 253 | 4741 | 120,000 | 39.5 |
| 0.001 | parallel | yes | 259 | 4804 | 120,000 | 40.0 |

§Control — does the parallel flag work at all?

| Model | Mode | Done? | Mesh ms | Triangles |
|---|---|---|---|---|
| 400 spheres, deflection 0.0005 | single | yes | 77431 | 12,881,600 |
| 400 spheres, deflection 0.0005 | parallel | yes | 8149 | 12,881,600 |

§Probe — is re-meshing an already-meshed shape a no-op? (*Nodes* is the node count of the first
face's cached triangulation.)

| Step | Mesh ms | Triangles | Nodes (first face) | Note |
|---|---|---|---|---|
| 1. mesh fresh compound at 1 | 901 | 24,000 | 4 | - |
| 2. mesh the **same** shape again at 0.001 | 894 | 24,000 | 4 | first face's triangulation unchanged: yes |
| 3. mesh a **rebuilt** compound at 0.001 | 914 | 24,000 | 4 | - |
| 4. one sphere, meshed at 0.1 | 0.9 | 306 | 168 | - |
| 5. the **same** sphere, meshed again at 0.001 | 32.2 | 10,108 | 5106 | cached triangulation **replaced** |
| 6. the same sphere, back to 0.1 | 0.2 | 10,108 | 5106 | **fine mesh kept — a coarser request is ignored** |

## Verdict

**No pass/fail criterion — this feeds P-11 and the *Performance* row of the kernels README. The
finding splits P-11 in two, and only one half survives.**

**The cost half does not hold on planar geometry** — *measured*. Four decades of linear deflection
(1 → 0.001) changed the mesh time from **4171 ms to 4741 ms**, about **14 %**, and changed the
triangle count **not at all**: 120 000 at every setting. 34.8–39.5 µs per triangle single-threaded.
P-11 is therefore a **curved-geometry** problem, not a general one; on the BIM-typical planar case
there is no coarse-versus-fine cost to trade.

**The architectural half holds, and is the sharper finding** — *measured*, from the probe. OCCT
caches one `Poly_Triangulation` per face, so **one shape cannot hold two qualities at once**. On
the sphere: a finer request **replaces** the cached triangulation at full cost (0.9 ms → 32.2 ms,
306 → 10 108 triangles, 168 → 5106 nodes), and a subsequent **coarser** request is **silently
ignored** — step 6 returns 10 108 triangles in 0.2 ms, the fine mesh kept. *Inferred*: a viewer
that asks for a coarse mesh after a drawing has asked for a fine one gets the fine one and pays
for it on every frame, with no error to notice.

**The parallel flag is real but does not pay on this model** — *measured*, and the control is what
makes that statement possible. On 10 000 boxes `isInParallel` costs time rather than saving it
(4171 → 4732 ms at deflection 1), while on 400 spheres it is **9.5× faster** (77 431 → 8 149 ms).
*Inferred*: threading works in this build; the per-face work on a six-face box is simply too small
to pay for the parallel path.

**Order of magnitude for the product:** 10 000 planar elements cost about **4.2–4.9 s** of
tessellation on one core, plus 0.24–0.26 s of construction — *measured*, on synthetic boxes.

## What this does not settle

- **OCCT 8.0.1 only.** No other candidate was tessellated; this is not a comparison.
- **The model is synthetic and entirely planar**, which is precisely why the cost half of P-11
  could not be tested on it. The curved case is measured only by the sphere controls, which are
  not the 10k benchmark model and are not a substitute for it.
- **`build/scale_10k.obj` is generator output and is not committed** ([`README.md`](README.md)
  §Rules), so reproducing these numbers means re-running the generator first.
- **Build times here are not comparable with the boolean spikes'**, because boxes are built as
  native `BRepPrimAPI_MakeBox` rather than sewn from triangles.
- **Nothing here measures quality**, only cost and cache behaviour: no chord-error or
  drawing-fidelity measurement was made, so "too coarse for drawings" remains a claim from P-11's
  statement rather than a measured one.

## Where this lands

[`../../docs/research/kernels/occt.md`](../../docs/research/kernels/occt.md) §Measurements;
`problems.md` **P-11**, which records the split as "partly shown"; spec §4, where tessellation is
a conversion with explicit deflection parameters and multiple results per object are allowed.
