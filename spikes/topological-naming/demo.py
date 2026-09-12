"""Minimal, reproducible topological-naming demonstration on FreeCAD 1.0.2.

Run headless with:
    "<FreeCAD install>/bin/freecadcmd.exe" demo.py

What it does:
1. Builds a PartDesign Body: Sketch (rectangle) -> Pad -> a second Sketch
   attached to one *named* face of the Pad ("the top face") -> Pocket.
   The second Sketch's `AttachmentSupport` stores a sub-element reference
   (a face name) the same way a hosted opening or a dimension would store
   a reference to derived topology (see docs/domain/parametric-components.md
   and docs/research/prior-art/onshape.md, "the reference problem").
2. Reads the raw OCCT face index and the element-map MappedName of the
   referenced face before and after the change, using the TopoShape Python
   API exposed at this commit (`getElementMappedName`) -- see
   src/App/ElementMap.h / src/Mod/Part/App/TopoShape.cpp in the pinned
   FreeCAD source.
3. Changes an *earlier* parameter (widens the base rectangle by directly
   moving a sketch point -- no unit-typed constraint datum is touched, to
   keep the script simple), forcing recompute, and checks:
   a. Does the raw OCCT face index the top face had before the change still
      point at the same geometric face afterwards (this is what pre-element-
      map FreeCAD stored, and what a bare `Face6`-style reference relies on)?
   b. Does Sketch2's AttachmentSupport -- which FreeCAD 1.0 stores as an
      element-map MappedName, not a bare index -- still resolve to a face,
      and is the document free of touched/error state after recompute?

This is a demonstration of the mechanism on one change to one reference,
not a statistical study.
"""
import sys
import traceback

import FreeCAD
import Part

def touched(obj):
    """Best-effort touched/error state across FreeCAD API variations."""
    for attr in ("isTouched", "mustExecute"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return getattr(obj, "Touched", "unknown")


doc = FreeCAD.newDocument("tnp_demo")

body = doc.addObject("PartDesign::Body", "Body")

# --- Sketch 1: base rectangle on the XY plane, defined directly by geometry ---
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch")
sketch1.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]  # XY_Plane
sketch1.MapMode = "FlatFace"

L = 20.0
W = 20.0
sketch1.addGeometry(Part.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(L, 0, 0)), False)
sketch1.addGeometry(Part.LineSegment(FreeCAD.Vector(L, 0, 0), FreeCAD.Vector(L, W, 0)), False)
sketch1.addGeometry(Part.LineSegment(FreeCAD.Vector(L, W, 0), FreeCAD.Vector(0, W, 0)), False)
sketch1.addGeometry(Part.LineSegment(FreeCAD.Vector(0, W, 0), FreeCAD.Vector(0, 0, 0)), False)
doc.recompute()
print("Sketch1 wire closed?:", sketch1.Shape.Wires[0].isClosed() if sketch1.Shape.Wires else "NO WIRES")

pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch1
pad.Length = 10.0
doc.recompute()

print("=== Pad faces (before change) ===")
padShape = pad.Shape
for i, f in enumerate(padShape.Faces, start=1):
    idx = "Face%d" % i
    mapped = padShape.getElementMappedName(idx)
    com = f.CenterOfMass
    print(idx, "->", mapped, " CoM=", (round(com.x, 2), round(com.y, 2), round(com.z, 2)), " Area=", round(f.Area, 2))

# The "top" face is the one at z == pad.Length, area L*W.
top_face_idx_before = None
for i, f in enumerate(padShape.Faces, start=1):
    com = f.CenterOfMass
    if abs(com.z - float(pad.Length)) < 1e-6 and abs(f.Area - (L * W)) < 1e-3:
        top_face_idx_before = i
        break
print("Top face index before change: Face%d" % top_face_idx_before)
top_face_name_before = padShape.getElementMappedName("Face%d" % top_face_idx_before)
print("Top face MappedName before change:", top_face_name_before)

# --- Sketch 2: attached to the top face of the Pad by NAME (a hosted-opening-style reference) ---
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch001")
try:
    sketch2.AttachmentSupport = [(pad, "Face%d" % top_face_idx_before)]
    sketch2.MapMode = "FlatFace"
except Exception:
    print("EXCEPTION setting Sketch2 attachment:")
    traceback.print_exc(file=sys.stdout)
try:
    sketch2.addGeometry(Part.Circle(FreeCAD.Vector(L / 2, W / 2, 0), FreeCAD.Vector(0, 0, 1), 3.0), False)
except Exception:
    print("EXCEPTION adding circle geometry:")
    traceback.print_exc(file=sys.stdout)
try:
    doc.recompute()
except Exception:
    print("EXCEPTION during recompute after Sketch2:")
    traceback.print_exc(file=sys.stdout)
print("Sketch2 AttachmentSupport after creation:", sketch2.AttachmentSupport)
print("Sketch2 touched after creation?:", touched(sketch2))

pocket = body.newObject("PartDesign::Pocket", "Pocket")
pocket.Profile = sketch2
pocket.Length = 3.0
doc.recompute()
print("Pocket touched after creation?:", touched(pocket), " shape null?:", pocket.Shape.isNull())

# --- Now change an EARLIER parameter: widen the base rectangle in Sketch1 ---
# Move point 2 of line 1 and point 1 of line 2 (the shared corner at (L,0))
# out to (L2, 0), and the corresponding corner of line2/line3 to (L2, W).
# This is a plain geometry edit -- no constraint solver involved -- but it
# is exactly the kind of "earlier parameter changed, later geometry must be
# recomputed" edit that R-13 is about.
L2 = 35.0
print("\n=== Widening Sketch1's rectangle: L=%.1f -> L2=%.1f ===" % (L, L2))
sketch1.movePoint(0, 2, FreeCAD.Vector(L2, 0, 0), 0)   # end of line0
sketch1.movePoint(1, 1, FreeCAD.Vector(L2, 0, 0), 0)   # start of line1
sketch1.movePoint(1, 2, FreeCAD.Vector(L2, W, 0), 0)   # end of line1
sketch1.movePoint(2, 1, FreeCAD.Vector(L2, W, 0), 0)   # start of line2
doc.recompute()

print("Objects touched/errored after recompute:")
for obj in doc.Objects:
    print(" ", obj.Name, "touched=", touched(obj), "errors=", getattr(obj, "Errors", None))

padShape2 = pad.Shape
print("\n=== Pad faces (after change) ===")
for i, f in enumerate(padShape2.Faces, start=1):
    idx = "Face%d" % i
    mapped = padShape2.getElementMappedName(idx)
    com = f.CenterOfMass
    print(idx, "->", mapped, " CoM=", (round(com.x, 2), round(com.y, 2), round(com.z, 2)), " Area=", round(f.Area, 2))

top_face_idx_after = None
for i, f in enumerate(padShape2.Faces, start=1):
    com = f.CenterOfMass
    if abs(com.z - float(pad.Length)) < 1e-6 and abs(f.Area - (L2 * W)) < 1e-3:
        top_face_idx_after = i
        break
print("Top face index after change: Face%s" % top_face_idx_after)
if top_face_idx_after:
    top_face_name_after = padShape2.getElementMappedName("Face%d" % top_face_idx_after)
    print("Top face MappedName after change:", top_face_name_after)
    print("Same raw IndexedName (Face%d) before/after?" % top_face_idx_before,
          top_face_idx_before == top_face_idx_after)
    print("Identical MappedName string before/after?", top_face_name_before == top_face_name_after)

print("\nSketch2.AttachmentSupport after recompute:", sketch2.AttachmentSupport)
print("Sketch2 touched:", touched(sketch2), "errors:", getattr(sketch2, "Errors", None))
print("Sketch2 shape null?:", sketch2.Shape.isNull())
print("Pocket touched:", touched(pocket), " Pocket shape null?:", pocket.Shape.isNull())
if not pocket.Shape.isNull():
    print("Pocket.Shape.Volume:", pocket.Shape.Volume)

doc.saveAs("tnp_demo_out.FCStd")
print("\nDone. Document saved as tnp_demo_out.FCStd for inspection.")
