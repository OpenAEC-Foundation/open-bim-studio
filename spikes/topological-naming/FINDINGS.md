# FINDINGS — R-13 / P-04, does a named-face reference survive an earlier parameter change?

This file adds no measurement. Every value below is copied from a named line of
[`results/freecad.txt`](results/freecad.txt), which is the reproducible record.

## The question, restated

When a PartDesign feature stores a reference to a **named face** of an earlier feature, and an
*earlier* parameter changes, does the reference survive — with FreeCAD 1.0's element map doing
the resolution — or does it break? This is the "on" side of the demonstration
[`../../docs/research/kernels/freecad-topological-naming.md`](../../docs/research/kernels/freecad-topological-naming.md)
§Measurements asks for. The "off" side (pre-element-map, raw index) and the failure modes
(topology split/merge) are **not** measured here; the note relies on the cited GitHub issues for
those.

**There is no pass/fail criterion in [`../../docs/risks.md`](../../docs/risks.md) for this spike,
and no numeric one anywhere — it feeds P-04 / R-13 as a worked example, not a gate.** R-13 in the
risk register is a design risk with a mitigation and an action, not a threshold; its entry reads,
verbatim:

> - **Accept:** some breakage is inevitable. Plan for visible, repairable failure rather than
>   silent corruption.

## Hardware, OS and versions

*Measured*, printed by FreeCAD itself at the end of
[`results/freecad.txt`](results/freecad.txt): **FreeCAD 1.0.2, Libs: 1.0.2R39319 (Git)**, run
through `bin/freecadcmd.exe`. The log records that a `FreeCAD MCP addon loaded` in the session —
noted because the run was not a clean `--factory-startup`-equivalent environment. No CPU, RAM or
OS line is recorded by this driver; nothing here is a timing, so none is load-bearing.

## Model and inputs

No file from [`../../reference/`](../../reference/). [`demo.py`](demo.py) builds the document in
process: a `PartDesign::Body` of `Sketch` (a rectangle) → `Pad` → `Sketch001`, whose
`AttachmentSupport` references one **named** face of the Pad (`Face6`, the top face) → `Pocket`.
This mirrors the pattern
[`../../docs/domain/parametric-components.md`](../../docs/domain/parametric-components.md) calls
"the reference problem": a later feature stores a name for an entity an earlier feature's
computation produced. The document is written to `tnp_demo_out.FCStd` next to the script — a spike
artefact, a binary, and not committed.

## Method

[`demo.py`](demo.py), run from the spike directory ([`README.md`](README.md) §Running it). It
reads, for the Pad's top face, both the raw OCCT face index (`Face6`) and the element-map
`MappedName`, via the `TopoShape` Python API exposed at this version (`getElementMappedName`;
mechanism read in `src/App/ElementMap.h` and `src/Mod/Part/App/TopoShapeExpansion.cpp` in the
pinned FreeCAD source for the note). It then widens the **earlier** sketch's rectangle,
**20 mm → 35 mm**, by moving its corner points directly — no constraint solver, to keep the script
simple and avoid an unrelated `Quantity` unit-mismatch bug — forces a recompute, and re-reads the
same two things from the regenerated Pad.

## The numbers

*Measured*, copied from [`results/freecad.txt`](results/freecad.txt). Faces before and after, with
the element-map name and the centre of mass:

| Face | MappedName (before and after — identical) | CoM before | CoM after | Area before | Area after |
|---|---|---|---|---|---|
| Face1 | `#d:1;:G;XTR;:Hb6d:7,F` | (10.0, 0.0, 5.0) | (17.5, 0.0, 5.0) | 200.0 | 350.0 |
| Face2 | `#d:2;:G;XTR;:Hb6d:7,F` | (20.0, 10.0, 5.0) | (35.0, 10.0, 5.0) | 200.0 | 200.0 |
| Face3 | `#d:3;:G;XTR;:Hb6d:7,F` | (10.0, 20.0, 5.0) | (17.5, 20.0, 5.0) | 200.0 | 350.0 |
| Face4 | `#d:4;:G;XTR;:Hb6d:7,F` | (0.0, 10.0, 5.0) | (0.0, 10.0, 5.0) | 200.0 | 200.0 |
| Face5 | `#d:1;FAC;:Hb6d:4,F` | (10.0, 10.0, 0.0) | (17.5, 10.0, 0.0) | 400.0 | 700.0 |
| Face6 | `#14:1;:G0;XTR;:Hb6d:8,F` | (10.0, 10.0, 10.0) | (17.5, 10.0, 10.0) | 400.0 | 700.0 |

The four lines the question turns on, verbatim from the log:

| Line in `results/freecad.txt` | Value |
|---|---|
| `Top face index before change` / `after change` | `Face6` / `Face6` |
| `Top face MappedName before change` / `after change` | `#14:1;:G0;XTR;:Hb6d:8,F` / `#14:1;:G0;XTR;:Hb6d:8,F` |
| `Same raw IndexedName (Face6) before/after?` | `True` |
| `Identical MappedName string before/after?` | `True` |
| `Sketch2.AttachmentSupport after recompute` | `[(<PartDesign::Pad>, ('Face6',))]` |
| `Pocket touched` / `Pocket shape null?` | `unknown` / `False` |
| `Pocket.Shape.Volume` | `6915.176998353077` |

`touched` reads `unknown` for every object in the log because `isTouched()` does not exist on
`Sketcher::SketchObject` in this build; the helper fell back and could not determine it. That is a
**limitation of the driver, not a result** ([`README.md`](README.md) §Two bugs hit while writing
this).

## Verdict

**No pass/fail criterion — this feeds P-04 and R-13 as a worked example.**

*Measured*: **both** the raw `TopAbs` index and the element-map `MappedName` survived the edit,
byte-identical, and the dependent `Sketch001.AttachmentSupport` and `Pocket` recomputed to a
valid, non-null shape of volume `6915.176998353077`.

*Inferred*, and the reason the result is weaker than it looks: **this edit was never going to
exercise the naming problem.** Widening the rectangle does not split, merge or delete any face —
the box stays a box, just wider, as the area column shows (200.0 → 350.0 on two faces, 400.0 →
700.0 on two more, face **count** unchanged at six). It is a "safe" edit, not a topology-changing
one.

The negative result is still worth having: *inferred*, the element map imposes **no visible cost
or instability on the common case** — a dimension change that does not restructure the model —
which is what `freecad-topological-naming.md` §Measurements reports it as.

It is explicitly **not** evidence that the element map survives a topology-changing edit.

## What this does not settle

- **The failure side is unmeasured.** Reproducing a topology-changing edit reliably from a script
  (a fillet, or a profile-shape change that alters face count) needed more of FreeCAD's
  attachment/shadow-reference internals than the spike's time budget allowed; the note relies on
  the **cited GitHub issues** for it instead ([`README.md`](README.md) §Result).
- **The "off" side is unmeasured** — the pre-element-map, raw-index behaviour that the "on" side
  is supposed to be compared against was not run.
- **One version, one shape, one edit.** FreeCAD 1.0.2, a single pad-and-pocket body, a single
  dimension change. Nothing here generalises to other feature types or to chained references.
- **`touched` state is unknown throughout**, so "no touched/error state" is read from `errors=
  None` and a non-null shape, not from a positive touched-flag reading.
- **Handles do not solve this.** The correction already recorded in `problems.md` P-04 stands:
  generational handles (spec §6) are a memory-safety mechanism, stable *within one build*, and do
  not by themselves give recompute-across-rebuilds identity.

## Where this lands

[`../../docs/research/kernels/freecad-topological-naming.md`](../../docs/research/kernels/freecad-topological-naming.md)
§Measurements; `problems.md` **P-04**; [`../../docs/risks.md`](../../docs/risks.md) **R-13**,
whose status this spike does not change.
