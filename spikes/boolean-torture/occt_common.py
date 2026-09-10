"""Shared OCCT helpers for the boolean-torture and precision-set drivers.

THROWAWAY SPIKE CODE. Standard library plus OCP (cadquery-ocp) only. See
`../README.md`. Nothing here is a design proposal; it exists to produce numbers.

The construction method is part of the measurement, so it is stated once here and
cited from both notes: every triangle of a benchmark mesh becomes a planar face
(`BRepBuilderAPI_MakePolygon` closed -> `BRepBuilderAPI_MakeFace`), the faces are
sewn into a shell (`BRepBuilderAPI_Sewing` at a stated tolerance), the shell is
wrapped in a solid (`BRepBuilderAPI_MakeSolid`) and reoriented
(`BRepLib.OrientClosedSolid_s`). No healing is applied unless a driver asks for it,
because "does the input survive construction at all" is one of the things measured.
"""
from __future__ import annotations

import platform
import sys
import time
from dataclasses import dataclass

from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_Sewing,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepLib import BRepLib
from OCP.GProp import GProp_GProps
from OCP.Precision import Precision
from OCP.TopAbs import TopAbs_ShapeEnum
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Compound, TopoDS_Shape
from OCP.collections import List_TopoDS_Shape
from OCP.gp import gp_Pnt

# Sewing tolerance used for every construction in these drivers. Precision::Confusion()
# is OCCT's own "two points are the same point" default (1e-7 m), so using it means the
# input meshes are handed to OCCT at OCCT's own idea of coincidence rather than at a
# value tuned to make the benchmark pass. The `sliver` case is 1e-7 thick, i.e. exactly
# at this tolerance -- that is deliberate and its outcome is a finding, not a bug in the
# driver.
SEW_TOLERANCE = Precision.Confusion_s()


@dataclass
class Built:
    shape: TopoDS_Shape | None
    valid: bool
    volume: float
    n_faces: int
    max_tolerance: float
    note: str = ""


@dataclass
class OpResult:
    ok: bool
    valid: bool
    volume: float
    ms: float
    max_tolerance: float
    note: str = ""
    shape: TopoDS_Shape | None = None


def volume(shape: TopoDS_Shape) -> float:
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def max_tolerance(shape: TopoDS_Shape) -> float:
    """Largest tolerance carried by any vertex, edge or face of the shape.

    This is the number that makes OCCT's tolerance model visible: it is per-entity,
    it is stored on the entity, and a boolean may raise it.
    """
    worst = 0.0
    for enum, caster in (
        (TopAbs_ShapeEnum.TopAbs_VERTEX, TopoDS.Vertex),
        (TopAbs_ShapeEnum.TopAbs_EDGE, TopoDS.Edge),
        (TopAbs_ShapeEnum.TopAbs_FACE, TopoDS.Face),
    ):
        exp = TopExp_Explorer(shape, enum)
        while exp.More():
            worst = max(worst, BRep_Tool.Tolerance_s(caster(exp.Current())))
            exp.Next()
    return worst


def count(shape: TopoDS_Shape, enum: TopAbs_ShapeEnum) -> int:
    n = 0
    exp = TopExp_Explorer(shape, enum)
    while exp.More():
        n += 1
        exp.Next()
    return n


def build_solid(vertices, faces, sew_tolerance: float = SEW_TOLERANCE) -> Built:
    """Triangle soup -> TopoDS_Solid. See the module docstring for the method."""
    try:
        sewing = BRepBuilderAPI_Sewing(sew_tolerance)
        made = 0
        for i0, i1, i2 in faces:
            poly = BRepBuilderAPI_MakePolygon(
                gp_Pnt(*vertices[i0]), gp_Pnt(*vertices[i1]), gp_Pnt(*vertices[i2]), True
            )
            if not poly.IsDone():
                continue
            face = BRepBuilderAPI_MakeFace(poly.Wire(), True)
            if not face.IsDone():
                continue
            sewing.Add(face.Face())
            made += 1
        sewing.Perform()
        sewed = sewing.SewedShape()
        if sewed.IsNull():
            return Built(None, False, 0.0, 0, 0.0, "sewing produced a null shape")
        n_shells = count(sewed, TopAbs_ShapeEnum.TopAbs_SHELL)
        if n_shells == 0:
            return Built(None, False, 0.0, 0, 0.0, "sewing produced no shell")
        # One shell -> one solid. Several disjoint shells (the `wall_with_openings`
        # tool is twelve separate opening boxes) -> a compound of solids, NOT one
        # solid holding twelve shells: OCCT's own argument rules require each
        # argument to be valid in terms of BRepCheck_Analyzer, and a solid with
        # twelve outer shells is not. This is measured, not assumed -- see the
        # construction-diagnostics table in `results/occt.md`.
        solids = []
        exp = TopExp_Explorer(sewed, TopAbs_ShapeEnum.TopAbs_SHELL)
        while exp.More():
            maker = BRepBuilderAPI_MakeSolid()
            maker.Add(TopoDS.Shell(exp.Current()))
            one = maker.Solid()
            BRepLib.OrientClosedSolid_s(one)
            solids.append(one)
            exp.Next()
        if len(solids) == 1:
            shape = solids[0]
        else:
            builder = BRep_Builder()
            comp = TopoDS_Compound()
            builder.MakeCompound(comp)
            for one in solids:
                builder.Add(comp, one)
            shape = comp
        valid = BRepCheck_Analyzer(shape).IsValid()
        note = ""
        if made != len(faces):
            note = f"{len(faces) - made} of {len(faces)} triangles rejected"
        if n_shells != 1:
            note = (note + "; " if note else "") + f"compound of {n_shells} solids"
        return Built(
            shape, valid, volume(shape), count(shape, TopAbs_ShapeEnum.TopAbs_FACE),
            max_tolerance(shape), note,
        )
    except Exception as exc:  # noqa: BLE001 - a spike records failures, it does not raise
        return Built(None, False, 0.0, 0, 0.0, f"{type(exc).__name__}: {exc}")


def _run(op_class, a, b, fuzzy: float | None, parallel: bool):
    op = op_class()
    la, lb = List_TopoDS_Shape(), List_TopoDS_Shape()
    la.Append(a)
    lb.Append(b)
    op.SetArguments(la)
    op.SetTools(lb)
    op.SetRunParallel(parallel)
    if fuzzy is not None:
        op.SetFuzzyValue(fuzzy)
    op.Build()
    return op


def boolean(kind: str, a, b, fuzzy: float | None = None, parallel: bool = False,
            repeats: int = 3) -> OpResult:
    """Run one boolean `repeats` times, keep the fastest, report the last result.

    Timing is min-of-repeats because that is the number least polluted by the OS
    scheduler; the reported shape is from the final run, which is identical to the
    others (the operation is deterministic on identical input).
    """
    op_class = {"fuse": BRepAlgoAPI_Fuse, "common": BRepAlgoAPI_Common}[kind]
    best = float("inf")
    op = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        try:
            op = _run(op_class, a, b, fuzzy, parallel)
        except Exception as exc:  # noqa: BLE001
            return OpResult(False, False, 0.0, 0.0, 0.0, f"{type(exc).__name__}: {exc}")
        best = min(best, (time.perf_counter() - t0) * 1000.0)
    assert op is not None
    # These bindings do not expose HasErrors()/HasWarnings(); IsDone() is
    # BRepAlgoAPI_Algo's own !HasErrors().
    if not op.IsDone():
        return OpResult(False, False, 0.0, best, 0.0, "not IsDone()")
    shape = op.Shape()
    if shape.IsNull():
        return OpResult(True, False, 0.0, best, 0.0, "null result shape")
    valid = BRepCheck_Analyzer(shape).IsValid()
    return OpResult(True, valid, volume(shape), best, max_tolerance(shape), "", shape)


def environment() -> dict[str, str]:
    import importlib.metadata as md

    try:
        ocp_version = md.version("cadquery-ocp")
    except Exception:  # noqa: BLE001
        ocp_version = "unknown"
    return {
        "python": sys.version.split()[0],
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "processor": platform.processor(),
        "cadquery-ocp": ocp_version,
        "occt": "8.0.1 (bundled by cadquery-ocp 8.0.1.0.0)",
        "Precision::Confusion": repr(Precision.Confusion_s()),
        "Precision::Angular": repr(Precision.Angular_s()),
        "Precision::Intersection": repr(Precision.Intersection_s()),
        "sewing tolerance": repr(SEW_TOLERANCE),
    }
