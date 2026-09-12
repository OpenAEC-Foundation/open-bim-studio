# `topological-naming`

**Question:** when a PartDesign feature stores a reference to a named face of an earlier feature,
and an *earlier* parameter changes, does the reference survive — with FreeCAD 1.0's element map
doing the resolution — or does it break? This is the "on" side of the demonstration
[`docs/research/kernels/freecad-topological-naming.md`](../../docs/research/kernels/freecad-topological-naming.md)
§Measurements asks for; the "off" (pre-element-map, raw-index) side and the failure modes
(topology split/merge) are not measured here and are covered by the cited GitHub issues instead —
see that note for why.

There is no pass/fail line in [`../../docs/risks.md`](../../docs/risks.md) for this spike: it
feeds R-13 and `problems.md` P-04 as a worked example, not a gate.

## Running it

Requires a local FreeCAD 1.0.x install (tested against 1.0.2, `bin/freecadcmd.exe`):

```bash
"<FreeCAD install>/bin/freecadcmd.exe" demo.py
```

Run from this directory — it writes `tnp_demo_out.FCStd` next to itself (not committed; a spike
artefact, and a binary). Raw output from the run this note cites is committed at
[`results/freecad.txt`](results/freecad.txt).

## What it does

1. Builds a `PartDesign::Body`: `Sketch` (rectangle) → `Pad` → a second `Sketch001` whose
   `AttachmentSupport` references one *named* face of the Pad (`Face6`, the top face) → `Pocket`.
   This mirrors the reference pattern `docs/domain/parametric-components.md` calls "the reference
   problem": a later feature stores a name for an entity an earlier feature's computation
   produced.
2. Reads the raw OCCT face index (`Face6`) and the element-map `MappedName`
   (`#14:1;:G0;XTR;:H<hash>:8,F`) for that face, via the `TopoShape` Python API exposed at this
   commit (`getElementMappedName`; see `src/App/ElementMap.h`,
   `src/Mod/Part/App/TopoShapeExpansion.cpp` in the pinned FreeCAD source read for the note).
3. Widens the *earlier* sketch's rectangle (20 mm → 35 mm) by moving its corner points directly
   (no constraint solver involved, to keep the script simple and avoid an unrelated `Quantity`
   unit-mismatch bug hit while iterating on this script — noted below), forces a recompute, and
   re-reads the same two things for the regenerated Pad.

## Two bugs hit while writing this, worth recording

- `pad.Length` returns an `App.Units.Quantity` from the FreeCAD 1.0.2 Python API, not a bare
  `float`; `com.z - pad.Length` raises `Quantity::operator-(): Unit mismatch in minus operation`.
  Fixed by `float(pad.Length)`.
- `sketch.isTouched()` does not exist on `Sketcher::SketchObject` in this build (it does on plain
  `App::DocumentObject` in other FreeCAD versions/docs). Worked around with a `touched()` helper
  that tries `isTouched`/`mustExecute` and falls back to the `Touched` property.

Neither bug is a topological-naming finding; both are recorded so a second run does not waste time
rediscovering them.

## Result (see `results/freecad.txt` for the full log)

The edit made in step 3 does **not** change the Pad's face count or their outer-boundary topology
(the box stays a box, just wider) — so this is a "safe" edit, not a topology-changing one.
Measured outcome:

| | Before | After |
|---|---|---|
| Raw index of the top face | `Face6` | `Face6` |
| Element-map `MappedName` of the top face | `#14:1;:G0;XTR;:H<hash>:8,F` | **identical string** |
| `Sketch001.AttachmentSupport` | `[(Pad, ('Face6',))]` | unchanged, no touched/error state |
| `Pocket.Shape` | valid | valid, `Volume = 6915.18` |

Both the raw `TopAbs` index and the element-map name survived — this particular edit was never
going to exercise the naming problem, because it does not split, merge, or delete any face. That
negative result is still useful: it shows the element map imposes no visible cost or instability
on the common case (a dimension change that does not restructure the model), which is what
`freecad-topological-naming.md` §Measurements reports it as. It is explicitly **not** evidence
that the element map survives a topology-changing edit — reproducing that reliably from a script
(a fillet or a profile-shape change that alters face count) turned out to need more of FreeCAD's
attachment/shadow-reference internals than fit in the time budgeted for this spike; the note relies
on the cited GitHub issues for the failure side instead.
