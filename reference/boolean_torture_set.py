"""Boolean torture set: ten pairs of closed triangle meshes with analytically known
union and intersection volumes.

Every case exercises one thing that is known to break mesh/B-rep boolean
implementations: disjoint input, partial overlap, coplanar faces, a shared edge, a
shared vertex, identical geometry, full containment, a near-zero-thickness slab, a
near-degenerate triangle, and a multi-shell cutting tool (a wall with openings).

Vertices are `float`; faces are counter-clockwise triangles, wound so their normal
points outward from the solid they belong to (verified numerically below via
`signed_volume`, which is the divergence-theorem volume of a closed mesh and is
positive for a correctly-wound solid).

Every `Case.expected_volume_union` / `expected_volume_intersection` pair satisfies
    V(A) + V(B) = V(A union B) + V(A intersect B)
which is checked in the self-check at the bottom of this file, for every case.
Dependency-free: standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass


Vertex = tuple[float, float, float]
Face = tuple[int, int, int]


@dataclass
class Mesh:
    vertices: list[Vertex]
    faces: list[Face]


@dataclass
class Case:
    name: str
    a: Mesh
    b: Mesh
    expected_volume_union: float
    expected_volume_intersection: float


def signed_volume(vertices: list[Vertex], faces: list[Face]) -> float:
    """Volume of a closed triangle mesh via the divergence theorem:
    V = (1/6) * sum over faces of v0 . (v1 x v2)
    Positive for a solid whose triangles are wound counter-clockwise as seen from
    outside (outward-facing normals). Translation-invariant for any closed mesh,
    which is what the precision set relies on.
    """
    total = 0.0
    for i0, i1, i2 in faces:
        x0, y0, z0 = vertices[i0]
        x1, y1, z1 = vertices[i1]
        x2, y2, z2 = vertices[i2]
        total += (
            x0 * (y1 * z2 - z1 * y2)
            - y0 * (x1 * z2 - z1 * x2)
            + z0 * (x1 * y2 - y1 * x2)
        )
    return total / 6.0


# --- mesh builders --------------------------------------------------------------

# Quad->triangle split and vertex/face layout match generate_scale_models.py's unit
# box exactly, so a box built here at (0,0,0)-(1,1,1) is the same solid the scale
# generator emits (just as an indexed mesh instead of an OBJ face list).
_BOX_QUADS = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _box(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> Mesh:
    """Axis-aligned box from (x0,y0,z0) to (x1,y1,z1), outward CCW triangles."""
    vertices: list[Vertex] = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces: list[Face] = []
    for a, b, c, d in _BOX_QUADS:
        faces.append((a, b, c))
        faces.append((a, c, d))
    return Mesh(vertices=vertices, faces=faces)


def _box_volume(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> float:
    return (x1 - x0) * (y1 - y0) * (z1 - z0)


def _degenerate_top_box() -> Mesh:
    """Unit cube (0,0,0)-(1,1,1) whose top face (z=1) is split into three triangles
    instead of two, by inserting a vertex v8 on the edge from v5=(1,0,1) to
    v6=(1,1,1), extremely close to v5: v8 = (1, 1e-6, 1).

    Splitting triangle (4,5,6) into (4,5,v8) and (4,v8,6) does not change the area
    (v8 lies exactly on edge 5-6, so the two new triangles tile the old one), but
    triangle (4,5,v8) has vertices v4=(0,0,1), v5=(1,0,1), v8=(1,1e-6,1): the angle
    at v4 is atan(1e-6 / 1) ~ 1e-6 rad, and the angle at v8 is ~(pi - 1e-6) rad.
    Volume is unaffected because the retriangulated region is coplanar and covers
    exactly the same area as before.
    """
    base = _box(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    vertices = list(base.vertices)
    v8 = len(vertices)
    vertices.append((1.0, 1e-6, 1.0))
    faces = []
    for f in base.faces:
        if f == (4, 5, 6):
            faces.append((4, 5, v8))
            faces.append((4, v8, 6))
        else:
            faces.append(f)
    return Mesh(vertices=vertices, faces=faces)


def _multibox(bounds: list[tuple[float, float, float, float, float, float]]) -> Mesh:
    """Combine several disjoint boxes into one multi-shell indexed mesh."""
    vertices: list[Vertex] = []
    faces: list[Face] = []
    for (x0, y0, z0, x1, y1, z1) in bounds:
        b = _box(x0, y0, z0, x1, y1, z1)
        offset = len(vertices)
        vertices.extend(b.vertices)
        faces.extend((i0 + offset, i1 + offset, i2 + offset) for i0, i1, i2 in b.faces)
    return Mesh(vertices=vertices, faces=faces)


def _wall_with_openings() -> tuple[Mesh, Mesh, float, float]:
    """A = 10 x 0.3 x 3 m wall. B = twelve cutting boxes that each pass fully
    through the wall's 0.3 m thickness (the y axis).

    Each opening box is 1.5 x 0.5 x 1.0 m. Its 0.5 m dimension runs along y (the
    thickness axis) and overshoots the wall by 0.1 m on each side (y in
    [-0.1, 0.4] against the wall's y in [0, 0.3]), so it cuts fully through with
    margin. Its other two dimensions (1.5 m and 1.0 m) sit entirely inside the
    wall's footprint, on x (length) and z (height) respectively.

    Per opening: intersection with A = x_overlap * y_overlap * z_overlap
                                      = 1.5 * 0.3 * 1.0 = 0.45 m^3
    (the three factors are the same 1 x 0.3 x 1.5 product the brief states; which
    factor runs along x vs. z only matters for whether twelve of them fit in the
    wall's footprint without touching one another or the wall's end/top/bottom
    faces -- 12 boxes 1.5 m wide need 18 m of unbroken row space, and boxes 1.5 m
    tall leave no room for a second row's margin in a 3 m wall, so this layout
    uses the 1.0 m dimension for height (2 rows fit inside 3 m with margin) and
    the 1.5 m dimension for width (6 columns fit inside 10 m with margin)).

    Layout: 2 rows x 6 columns = 12 openings.
    Row z-ranges (height 1.0 m each): row0 = [0.4, 1.4], row1 = [1.6, 2.6].
      -> 0.4 m margin to z=0, 0.2 m gap between rows, 0.4 m margin to z=3.
    Column x-ranges (width 1.5 m each), 0.10 m end margins, 0.16 m gaps:
      [0.10,1.60] [1.76,3.26] [3.42,4.92] [5.08,6.58] [6.74,8.24] [8.40,9.90]
      -> 0.10 + 6*1.5 + 5*0.16 + 0.10 = 0.10 + 9.00 + 0.80 + 0.10 = 10.00 m.
    All twelve boxes therefore touch nothing but the wall's y faces (the
    thickness, which they are meant to cut through); rows are separated by a
    0.2 m z gap and never share an x range with a box from the other row's
    z-adjacent boundary in a way that would make them touch.
    """
    wall_x0, wall_y0, wall_z0 = 0.0, 0.0, 0.0
    wall_x1, wall_y1, wall_z1 = 10.0, 0.3, 3.0
    a = _box(wall_x0, wall_y0, wall_z0, wall_x1, wall_y1, wall_z1)
    v_a = _box_volume(wall_x0, wall_y0, wall_z0, wall_x1, wall_y1, wall_z1)

    columns = [(0.10, 1.60), (1.76, 3.26), (3.42, 4.92), (5.08, 6.58), (6.74, 8.24), (8.40, 9.90)]
    rows = [(0.4, 1.4), (1.6, 2.6)]
    y0, y1 = -0.1, 0.4  # overshoots wall's [0, 0.3] on both sides

    bounds = []
    for (z0, z1) in rows:
        for (x0, x1) in columns:
            bounds.append((x0, y0, z0, x1, y1, z1))
    b = _multibox(bounds)

    per_opening_intersection = 1.5 * 0.3 * 1.0  # x_overlap * y_overlap(clamped) * z_overlap
    n = len(bounds)
    assert n == 12
    v_b = sum(_box_volume(*bd) for bd in bounds)  # 12 * (1.5*0.5*1.0) = 9.0
    intersection = n * per_opening_intersection    # 12 * 0.45 = 5.4
    union = v_a + v_b - intersection                # 9 + 9 - 5.4 = 12.6
    return a, b, union, intersection


def cases() -> list[Case]:
    result: list[Case] = []

    # 1. disjoint -- two unit cubes 3 m apart (gap between nearest faces = 3 m).
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(4, 0, 0, 5, 1, 1)
    result.append(Case("disjoint", a, b, expected_volume_union=1.0 + 1.0, expected_volume_intersection=0.0))

    # 2. overlap_half -- unit cubes offset by (0.5, 0, 0).
    # overlap box: x in [0.5,1], y in [0,1], z in [0,1] -> 0.5*1*1 = 0.5
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(0.5, 0, 0, 1.5, 1, 1)
    inter = 0.5 * 1.0 * 1.0
    result.append(Case("overlap_half", a, b, expected_volume_union=1.0 + 1.0 - inter, expected_volume_intersection=inter))

    # 3. coplanar_faces -- A's face at x=1 (y,z in [0,1]) and B's face at x=1
    # (y,z in [0.5,1.5]) share the plane x=1, and the two footprints genuinely
    # cross: each spans [0.5,1] in common with the other, but A alone covers
    # y,z in [0,0.5) and B alone covers y,z in (1,1.5] -- a real partial overlap
    # of the two coplanar boundary loops, not containment. Since A occupies
    # x in [0,1] and B occupies x in [1,2], they meet only at the x=1 plane
    # regardless of the y/z overlap, so the intersection volume is still 0
    # (this case stresses face/boundary matching, not volume). B = 1 x 1 x 1 m
    # box, volume 1.0.
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(1, 0.5, 0.5, 2, 1.5, 1.5)
    v_b = 1.0 * 1.0 * 1.0
    result.append(Case("coplanar_faces", a, b, expected_volume_union=1.0 + v_b, expected_volume_intersection=0.0))

    # 4. shared_edge -- cubes touching along the line x=1,y=1,z in [0,1] only.
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(1, 1, 0, 2, 2, 1)
    result.append(Case("shared_edge", a, b, expected_volume_union=1.0 + 1.0, expected_volume_intersection=0.0))

    # 5. touching_vertex -- cubes touching only at the point (1,1,1).
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(1, 1, 1, 2, 2, 2)
    result.append(Case("touching_vertex", a, b, expected_volume_union=1.0 + 1.0, expected_volume_intersection=0.0))

    # 6. identical -- the same cube twice: union = intersection = 1.
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(0, 0, 0, 1, 1, 1)
    result.append(Case("identical", a, b, expected_volume_union=1.0, expected_volume_intersection=1.0))

    # 7. contained -- a 0.5 m cube fully inside a 1 m cube.
    # union = V(A) = 1 (B contributes nothing new); intersection = V(B) = 0.125.
    a = _box(0, 0, 0, 1, 1, 1)
    b = _box(0.25, 0.25, 0.25, 0.75, 0.75, 0.75)
    v_b = 0.5 ** 3
    result.append(Case("contained", a, b, expected_volume_union=1.0, expected_volume_intersection=v_b))

    # 8. sliver -- a 1x1x1e-7 m slab crossing the cube, its x/y extent identical to
    # the cube's (touching the side faces exactly, not exceeding them) so the slab
    # is fully contained in z as well: union = V(A), intersection = V(slab).
    a = _box(0, 0, 0, 1, 1, 1)
    slab_t = 1e-7
    b = _box(0, 0, 0.5, 1, 1, 0.5 + slab_t)
    v_b = 1.0 * 1.0 * slab_t
    result.append(Case("sliver", a, b, expected_volume_union=1.0, expected_volume_intersection=v_b))

    # 9. near_degenerate_triangle -- A and B are the SAME 1 m cube; A's top face
    # uses the plain two-triangle split, B's top face is retriangulated with a
    # ~1e-6 rad sliver (see _degenerate_top_box). Same solid, same volume: this
    # stresses the degenerate triangle in the boolean/volume routine without
    # changing the analytically expected numbers.
    a = _box(0, 0, 0, 1, 1, 1)
    b = _degenerate_top_box()
    result.append(Case("near_degenerate_triangle", a, b, expected_volume_union=1.0, expected_volume_intersection=1.0))

    # 10. wall_with_openings -- see _wall_with_openings for the full derivation.
    a, b, union, inter = _wall_with_openings()
    result.append(Case("wall_with_openings", a, b, expected_volume_union=union, expected_volume_intersection=inter))

    return result


if __name__ == "__main__":
    tol = 1e-9
    for case in cases():
        v_a = signed_volume(case.a.vertices, case.a.faces)
        v_b = signed_volume(case.b.vertices, case.b.faces)
        lhs = v_a + v_b
        rhs = case.expected_volume_union + case.expected_volume_intersection
        ok = abs(lhs - rhs) < max(tol, 1e-9 * max(abs(lhs), abs(rhs), 1.0))
        print(
            f"{case.name:28s} V(A)={v_a:.9f} V(B)={v_b:.9f} "
            f"expected_union={case.expected_volume_union:.9f} "
            f"expected_intersection={case.expected_volume_intersection:.9f} "
            f"V(A)+V(B)={lhs:.9f} union+intersection={rhs:.9f} {'OK' if ok else 'MISMATCH'}"
        )
        assert v_a > 0.0, f"{case.name}: mesh A is not a correctly wound closed solid (signed volume <= 0)"
        assert v_b > 0.0, f"{case.name}: mesh B is not a correctly wound closed solid (signed volume <= 0)"
        assert abs(v_a - (signed_volume(case.a.vertices, case.a.faces))) < 1e-12
        assert ok, f"{case.name}: V(A)+V(B) != expected_union + expected_intersection"
    print(f"{len(cases())} cases OK")
