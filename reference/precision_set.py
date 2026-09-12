"""Precision set: three cases from boolean_torture_set, each carrying an `offset`
so a spike driver can run the candidate twice -- once at the origin, once
translated by `offset` -- translate the second result back, and compare vertex
positions after matching. This is the test for precision loss at large
coordinates (500 km, a plausible distance from a national projection's false
origin to a project site).

Reuses cases 2 (overlap_half), 3 (coplanar_faces) and 10 (wall_with_openings)
from boolean_torture_set.py verbatim -- same meshes, same expected volumes -- and
adds the offset. The meshes themselves are left at the origin; translating by
`offset` for the second run is the spike driver's job, not this module's.
Dependency-free: standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass

import boolean_torture_set as _torture
from boolean_torture_set import Mesh, Vertex, Face, signed_volume  # re-exported for convenience

OFFSET: tuple[float, float, float] = (500000.0, 500000.0, 0.0)

# Case numbers from the brief are 1-indexed against boolean_torture_set.cases():
# 2 = overlap_half, 3 = coplanar_faces, 10 = wall_with_openings.
_REUSED_NAMES = ("overlap_half", "coplanar_faces", "wall_with_openings")


@dataclass
class Case:
    name: str
    a: Mesh
    b: Mesh
    expected_volume_union: float
    expected_volume_intersection: float
    offset: tuple[float, float, float]


def offset(vertices: list[Vertex], delta: tuple[float, float, float]) -> list[Vertex]:
    """Translate a vertex list by `delta`. A spike driver uses this to build the
    500 km-translated run; `signed_volume` is translation-invariant for a closed
    mesh so the expected volumes are unchanged by this offset.
    """
    dx, dy, dz = delta
    return [(x + dx, y + dy, z + dz) for (x, y, z) in vertices]


def cases() -> list[Case]:
    by_name = {c.name: c for c in _torture.cases()}
    result: list[Case] = []
    for name in _REUSED_NAMES:
        source = by_name[name]
        result.append(
            Case(
                name=source.name,
                a=source.a,
                b=source.b,
                expected_volume_union=source.expected_volume_union,
                expected_volume_intersection=source.expected_volume_intersection,
                offset=OFFSET,
            )
        )
    return result


if __name__ == "__main__":
    tol = 1e-9
    for case in cases():
        v_a = signed_volume(case.a.vertices, case.a.faces)
        v_b = signed_volume(case.b.vertices, case.b.faces)
        lhs = v_a + v_b
        rhs = case.expected_volume_union + case.expected_volume_intersection
        ok = abs(lhs - rhs) < max(tol, 1e-9 * max(abs(lhs), abs(rhs), 1.0))
        print(f"{case.name:20s} offset={case.offset} V(A)+V(B)={lhs:.9f} union+intersection={rhs:.9f} {'OK' if ok else 'MISMATCH'}")
        assert ok, f"{case.name}: V(A)+V(B) != expected_union + expected_intersection"

        # Translation invariance: signed_volume of the offset mesh must match.
        a_shifted = offset(case.a.vertices, case.offset)
        v_a_shifted = signed_volume(a_shifted, case.a.faces)
        assert abs(v_a_shifted - v_a) < 1e-6 * max(1.0, abs(v_a)), (
            f"{case.name}: volume not translation-invariant after offset "
            f"({v_a_shifted} vs {v_a})"
        )
    print(f"{len(cases())} cases OK")
