# `boolean-torture`

**Question (R-16):** does a candidate kernel's boolean survive coplanar faces, shared edges,
touching vertices, identical operands, containment, a near-zero-thickness slab, a near-degenerate
triangle and a wall cut by twelve openings — producing a valid closed result each time, with
`V(A∪B) + V(A∩B) = V(A) + V(B)`?

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-16, written before any
driver ran: pass is every case valid and the volume identity within 1e-9 relative; fail is any
invalid result or a volume error above 1e-6 relative.

The cases are fixed in [`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py)
and are the same ten pairs for every candidate. A driver may not add, drop or adjust a case.

## Layout

```
occt_common.py        shared OCCT helpers (mesh -> solid, boolean, volume, tolerance)
occt_driver.py        the OCCT driver
blender_driver.py     the Blender driver (runs inside Blender's own Python)
manifold_driver.py    the standalone Manifold driver
cgal_driver.py        the CGAL driver (Epick corefinement)
results/<candidate>.md raw results, one file per candidate, written by that candidate's driver
results/run-<date>.log stdout of one session in which all four drivers ran
FINDINGS.md           assembled across candidates once they have all run
```

`FINDINGS.md` is written from the `results/` files, not from a single run.

## Running the OCCT driver

```bash
pip install cadquery-ocp==8.0.1.0.0      # bundles OCCT 8.0.1
python spikes/boolean-torture/occt_driver.py
```

from the repository root. It writes [`results/occt.md`](results/occt.md) and prints a one-line
summary. `--repeats N` changes how many times each boolean is timed (the fastest is reported);
**each repeat rebuilds its operands**, because `BOPAlgo` mutates its arguments by default and a
loop over one pair would time progressively degraded input (Probe B measures exactly that).

Besides the torture set the driver runs four probes into the same results file:

| Probe | Question |
|---|---|
| A | Does fuzzy tolerance growth compound over a chain of booleans? |
| B | Does a boolean raise the tolerance of its *input* shapes? |
| C | Is a sewing tolerance below `Precision::Confusion()` honoured? (BREP output hashed) |
| D | How thin a solid will `BRepPrimAPI_MakeBox` build? |

The construction method — triangle soup to `TopoDS_Solid` — is documented in `occt_common.py` and
is part of the measurement: a case whose operands OCCT cannot build is a finding about OCCT.

## Running the Blender driver

```bash
"C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
    --factory-startup --python spikes/boolean-torture/blender_driver.py -- --repeats 5
```

from the repository root. It writes [`results/blender.md`](results/blender.md).
`--factory-startup` is **not optional**: without it every add-on in the user's configuration is
loaded into the measured process. Blender's boolean modifier is non-destructive, but the driver
still **rebuilds both operand objects for every solver, every operation and every repeat**, so no
measurement can inherit state — including anything a previous `Mesh.validate()` changed.

Each case runs against all three solvers the 5.0 RNA exposes (`EXACT`, `FLOAT`, `MANIFOLD`) for
union and intersection. Besides the torture set the driver runs five probes into the same file:

| Probe | Question |
|---|---|
| A | Does the Fast solver's *Overlap Threshold* change what happens to the 1e-7 m `sliver`? |
| B | What does each solver do with a twelve-shell cutting tool, including `DIFFERENCE`? |
| C | What do `use_self` and `use_hole_tolerant` cost when the input does not need them? |
| D | `touching_vertex`: which solver loses an operand, and does perturbing the contact fix it? |
| E | Is a solver's output identical across repeated runs of identical input? |

The construction method is part of the measurement here too, and differs deliberately from the
OCCT driver where the representations differ: `wall_with_openings` B is built as **one mesh object
with twelve disconnected shells** — the natural reading of the benchmark for a mesh kernel —
where the OCCT driver had to sew it into a compound of twelve solids.

## Running the Manifold driver

```bash
pip install manifold3d==3.5.3
python spikes/boolean-torture/manifold_driver.py
```

from the repository root. It writes [`results/manifold.md`](results/manifold.md). `--repeats N` and
`--determinism-runs N` change the timing and Probe D loop counts. Every case runs on four settings
— `Mesh64` (f64) at the default tolerance, at 1e-9 and at 1e-6, and `Mesh` (f32) at the default —
because the tolerance and the input precision are the two axes this library actually exposes.
Operands are rebuilt for every setting and every repeat: Manifold does not mutate its inputs, but
the rebuild re-runs the `Mesh -> Manifold` constructor, which is where the epsilon, the tolerance
and the float32 rounding are decided.

| Probe | Question |
|---|---|
| A | What does the twelve-shell cutting tool become, including `DIFFERENCE`? |
| B | At what tolerance does the 1e-7 m slab silently disappear? |
| C | What do the library and its `Merge` helper do with the T-junction operand? |
| D | Is the output identical across repeated runs of identical input, on a TBB build? |
| E | Does `ExecutionContext` actually cancel a running boolean? |

## Running the CGAL driver

```bash
pip install cgal==6.0.1.post202410241521
python spikes/boolean-torture/cgal_driver.py
```

from the repository root. It writes [`results/cgal.md`](results/cgal.md). CGAL exposes no tolerance
parameter, so the two settings are ingest precisions — the reference coordinates verbatim, and the
same coordinates rounded through the nearest float32 and back. `orient_polygon_soup` is deliberately
**not** called: whether the reference set's operands are already consistently oriented is part of
what is measured. Both operands are rebuilt inside every repeat because PMP corefinement modifies
them in place (Probe F).

| Probe | Question |
|---|---|
| A | What does the twelve-shell cutting tool become, including `DIFFERENCE`? |
| B | Does a 1e-7 m feature survive ingest and the boolean with no tolerance to raise? |
| C | What happens to the T-junction operand, and does `stitch_borders` repair it? |
| D | The three contact cases side by side — which one is refused, and why? |
| E | Is the output identical across runs? Distinct geometries vs. distinct emission orders |
| F | How much does corefinement change its own operands? |
| G | Which kernel is actually bound — Epick or Epeck? |
| H | Do the exact predicates decide cases plain doubles get wrong? |

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Standard library plus the candidate's
own bindings only; nothing here is a design proposal for `kernel/`.
