# Kernel Research Programme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the evidence on which ADR-0004 (own kernel in DynLex), ADR-0005 (four equal representations) and ADR-0006 (f64 local coordinates, exact predicates, tolerance model) are accepted, amended or withdrawn — a completed candidate matrix, a filled problem→root-cause index, measured spikes with pass/fail criteria written in advance, and evidence tables in every ADR.

**Architecture:** Research notes in `docs/research/kernels/` (one per candidate, template `docs/research/_template.md`), cross-cutting index `docs/research/kernels/problems.md`, measurements in `spikes/<name>/` with `FINDINGS.md`, benchmark set fixed in `reference/`. Order: measuring stick first (benchmark set, ADRs as proposed, risks with criteria), then candidates grouped by representation, then spikes, then synthesis and ADR acceptance. Kernel milestone M0 (`2026-09-09-m0-repository-restart.md`) starts only after Task 16.

**Tech Stack:** Markdown; Python 3 for spike drivers where a library has bindings (`cadquery-ocp` for OCCT, `manifold3d`, `open3d`, `ifcopenshell`); Blender's `bpy` for Blender measurements; Node.js for web-ifc; the DynLex compiler at `../dynlex` for the DynLex spikes. Spike code is throwaway per `spikes/README.md`.

## Global Constraints

- Everything on disk is English (ADR-0002). Competing geotechnical or structural calculation software is never named; BIM and 3D software is named explicitly. No conversation transcripts anywhere.
- Every note opens with its decision question, names the decision it serves, labels every claim **claimed / measured / inferred**, records the version or commit hash it read, and ends with a verdict on all three axes (*build on / borrow from / avoid*) — `docs/research/kernels/README.md`.
- Every measurement records hardware, OS, library versions, benchmark model and method in `FINDINGS.md`; pass/fail criteria are written in `docs/risks.md` **before** the spike runs.
- No product code. Spikes are throwaway and live only in `spikes/`. Nothing is written under `kernel/` during this plan.
- Reference model binaries are never committed; `reference/README.md` records URL, licence, checksum and characteristics.
- ADR-0004, 0005, 0006 stay `proposed` until their evidence tables have no empty cell.
- Commit messages describe the change and end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

---

## File structure

```
docs/architecture/decisions/0004-build-our-own-kernel-in-dynlex.md          proposed, evidence table empty
docs/architecture/decisions/0005-multi-representation-kernel.md             proposed, evidence table empty
docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md    proposed, evidence table empty
docs/risks.md                                                               R-16..R-19 added with criteria
reference/README.md                                                         benchmark set fixed (5 parts)
reference/generate_scale_models.py                                          synthetic 10k/100k/1M generator
reference/boolean_torture_set.py                                            generates the torture cases + expected volumes
reference/precision_set.py                                                  same geometry at origin and at 500 km
docs/research/kernels/occt.md, freecad-topological-naming.md, truck-fornjot.md, commercial-brep-reference.md
docs/research/kernels/blender.md, manifold.md, cgal.md, libigl-openmesh.md
docs/research/kernels/pointclouds.md (PCL, Open3D, PDAL, Potree), implicit.md (OpenVDB, libfive)
docs/research/kernels/ifcopenshell.md, web-ifc.md, xbim.md
docs/research/renderers/gpu-paths.md
spikes/boolean-torture/, spikes/precision-set/, spikes/incremental-evaluation/, spikes/dynlex-performance/, spikes/dynlex-scale/
docs/research/kernels/synthesis.md
```

---

### Task 1: Record the hypothesis as proposed ADRs and the new risks

**Files:**
- Create: `docs/architecture/decisions/0004-build-our-own-kernel-in-dynlex.md`
- Create: `docs/architecture/decisions/0005-multi-representation-kernel.md`
- Create: `docs/architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md`
- Modify: `docs/risks.md` (add R-16..R-19 under Critical; add R-01 note)
- Modify: `docs/roadmap.md` (phase 2 status)

**Interfaces:**
- Produces: three ADRs with `**Status:** proposed`, each with the Evidence table from `_template.md` whose *Where shown* cells name the note or spike expected to fill them (from spec §15) and whose *Evidence type* cells are empty.
- Produces: risk ids R-16 (boolean robustness), R-17 (precision far from origin), R-18 (DynLex compile scale), R-19 (DynLex runtime performance) used by later tasks.

- [ ] **Step 1: Write ADR-0004 as proposed**

Use `docs/architecture/decisions/_template.md`. Context: ADR-0003's premise and what changed (DynLex exists; research-phase finding that candidates impose assumptions — cite `docs/research/kernels/problems.md` P-05, P-06). Decision: "We build our own geometry kernel in DynLex" stated as the proposed decision. Options: build on existing (ADR-0003), own kernel in an established systems language, own kernel in DynLex. Evidence table rows, *Where shown* pre-filled, *Evidence type* empty:

| Claim | Where shown | Evidence type |
|---|---|---|
| No candidate can be built on without a disqualifying assumption | `kernels/occt.md` §Verdict, `kernels/ifcopenshell.md` §Verdict, `kernels/web-ifc.md` §Verdict, `kernels/manifold.md` §Verdict, `kernels/cgal.md` §Verdict | |
| DynLex compiles kernel-shaped code within the compile-time budget | `spikes/dynlex-scale/FINDINGS.md` (R-18) | |
| DynLex runs kernel-shaped code within 1.5× of C++ -O2 | `spikes/dynlex-performance/FINDINGS.md` (R-19) | |
| DynLex can be extended for threading and memory mapping | `kernels/dynlex-readiness` section of `spikes/dynlex-scale/FINDINGS.md` | |
| Per-object overhead is the cause of scale ceilings we must avoid | `kernels/problems.md` P-07, `spikes/blender-ceiling/FINDINGS.md` (R-03) | |

- [ ] **Step 2: Write ADR-0005 as proposed**

Same template. Evidence rows: "single-representation kernels fail on the other geometry classes" (`kernels/occt.md` §Weaknesses, `kernels/blender.md` §Weaknesses, `kernels/manifold.md` §Weaknesses); "explicit conversions avoid documented loss" (`kernels/ifcopenshell.md` §IFC geometry mapping, `kernels/web-ifc.md` same, `problems.md` P-10, P-11); "exact arrangement is the robust mesh boolean" (`spikes/boolean-torture/FINDINGS.md` R-16, `kernels/blender.md` §Exact boolean, `kernels/libigl-openmesh.md`); "implicit representation earns its place" (`kernels/implicit.md` §Verdict).

- [ ] **Step 3: Write ADR-0006 as proposed**

Evidence rows: "float32 local coordinates fail the precision set" (`spikes/precision-set/FINDINGS.md` R-17); "floating-point topology decisions cause invalid booleans" (`problems.md` P-01, `kernels/occt.md` §Known problems, `kernels/blender.md` §Carve history); "exact rational everywhere is too slow" (`kernels/cgal.md` §Measurements, `problems.md` P-03); "tolerant B-rep accumulates tolerance" (`kernels/occt.md` §Tolerance model, `kernels/freecad-topological-naming.md`); "camera-relative f32 is sufficient on the GPU" (`renderers/gpu-paths.md`).

- [ ] **Step 4: Add the risks with criteria written now**

Append under *Critical* in `docs/risks.md`:

```markdown
### R-16 · Boolean robustness — ours and theirs
No boolean algorithm is trusted until it survives the torture set. The same set measures the
candidates we might build on or borrow from, and later our own kernel.

- **Spike:** `spikes/boolean-torture/` — the cases in `reference/boolean_torture_set.py` run
  through OCCT, Blender (exact), Manifold and CGAL; each result checked for closed manifold
  output and V(A∪B) + V(A∩B) = V(A) + V(B).
- **Pass (per candidate):** every case produces a valid closed result and the volume identity
  holds within 1e-9 relative.
- **Fail:** any invalid result, or a volume error above 1e-6 relative; each failure recorded
  with the input, the version and the traced cause in `problems.md`.
- **Status:** open

### R-17 · Precision far from the origin
The tile-frame design assumes f64 local coordinates are necessary and sufficient.

- **Spike:** `spikes/precision-set/` — identical geometry at the origin and at 500 km, through
  each candidate's boolean and tessellation, then re-centred and compared.
- **Pass:** maximum deviation below 1e-6 m in f64 paths.
- **Fail:** deviation above 1e-4 m — which for a float32 path is the expected outcome and the
  evidence ADR-0006 needs.
- **Status:** open

### R-18 · DynLex may not compile a kernel-sized program acceptably
The kernel will be the largest DynLex program. Compile time is on the inner loop of every
kernel developer.

- **Spike:** `spikes/dynlex-scale/` — generate synthetic DynLex programs of 5k, 20k and 50k
  lines in the kernel's style (classes, patterns, intrinsics); measure compile time and memory.
- **Pass:** 20k lines compile in under 30 s on the reference machine.
- **Fail:** over 120 s, or the compiler exhausts memory — a blocker to fix in dynlex before M1.
- **Status:** open

### R-19 · DynLex runtime performance may fall short of native
The performance targets assume native-speed code.

- **Spike:** `spikes/dynlex-performance/` — triangle–triangle intersection over 10⁶ random
  pairs, BVH build over 10⁶ boxes, and an f64 orient3d loop, each in DynLex and C++ -O2.
- **Pass:** DynLex within 1.5× of C++ on every workload.
- **Fail:** over 3× on any — a codegen issue to root-cause in dynlex before M1.
- **Status:** open
```

Under R-01, add the sentence: "Now also measured for IfcOpenShell and web-ifc as evidence for ADR-0004's *build on* verdicts."

- [ ] **Step 5: Update the roadmap**

In `docs/roadmap.md`, set the phase 2 row to `**in progress**` and add under *Phase 2 — kernel research*: "Revised 2026-09-09: the question now includes what each kernel teaches a kernel of our own. Method: `research/kernels/README.md`. Order of work: `superpowers/plans/2026-09-09-kernel-research-programme.md`." Add a row after phase 5: "**6** | Kernel build milestones M0–M8 | working kernel | blocked on phase 4".

- [ ] **Step 6: Verify and commit**

Run: `grep -n '^\*\*Status:\*\*' docs/architecture/decisions/000[456]*.md && grep -c '^### R-1[6-9]' docs/risks.md`
Expected: three `proposed` lines; `4`.

```bash
git add docs/architecture/decisions docs/risks.md docs/roadmap.md
git commit -m "Record the own-kernel hypothesis as proposed ADRs with open evidence tables

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Fix the benchmark set

**Files:**
- Modify: `reference/README.md`
- Create: `reference/generate_scale_models.py`
- Create: `reference/boolean_torture_set.py`
- Create: `reference/precision_set.py`

**Interfaces:**
- Produces: `boolean_torture_set.py` exposing `cases() -> list[Case]` where `Case` has `name`, `a` and `b` as indexed triangle meshes (`vertices: list[tuple[float,float,float]]`, `faces: list[tuple[int,int,int]]`), and `expected_volume_union`, `expected_volume_intersection` as floats. Every spike driver imports this module.
- Produces: `precision_set.py` exposing `cases() -> list[Case]` with the same shape plus `offset: tuple[float,float,float]` = `(500000.0, 500000.0, 0.0)`.
- Produces: `generate_scale_models.py --count N --out path.obj` writing N unit boxes on a grid.

- [ ] **Step 1: Choose the realistic IFC model and record it**

Candidates with open licences: the KIT "AC20-FZK-Haus" and "AC20-Institute-Var-2" sample models (IFC4), and the Schependomlaan dataset (IFC2x3, a real Dutch housing project). Record in `reference/README.md` §1 for each chosen file: URL, licence, SHA-256, schema version, element count (measured with `ifcopenshell`), notable features. Choose one IFC2x3 and one IFC4 model so both schema paths are exercised.

- [ ] **Step 2: Write the scale generator**

```python
"""Generate N unit boxes on a square grid as OBJ. Measures scaling, not geometry."""
import argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    side = math.ceil(math.sqrt(a.count))
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.count):
            x, y = (i % side) * 2.0, (i // side) * 2.0
            for dx, dy, dz in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]:
                f.write(f"v {x+dx} {y+dy} {dz}\n")
            b = 8 * i + 1
            for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
                f.write("f " + " ".join(str(b + k) for k in q) + "\n")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write the boolean torture set**

Cases, each two closed triangle meshes with analytically known union and intersection volumes:

1. `disjoint` — two unit cubes 3 m apart.
2. `overlap_half` — unit cubes offset by (0.5, 0, 0).
3. `coplanar_faces` — cubes sharing the plane x = 1 with partial face overlap.
4. `shared_edge` — cubes touching along one edge only.
5. `touching_vertex` — cubes touching at one vertex.
6. `identical` — the same cube twice.
7. `contained` — a 0.5 m cube inside a 1 m cube.
8. `sliver` — a cube and a 1 × 1 × 1e-7 m slab crossing it.
9. `near_degenerate_triangle` — a cube whose top face is split into triangles with one angle of 1e-6 rad.
10. `wall_with_openings` — a 10 × 0.3 × 3 m box minus twelve 1 × 0.5 × 1.5 m boxes, as one A and a multi-shell B.

Store vertices as `float` and faces as counter-clockwise outward-facing triangles; compute expected volumes by formula in the module (document each formula in a comment). Add `signed_volume(vertices, faces)` for spike drivers to check results.

- [ ] **Step 4: Write the precision set**

Reuse cases 2, 3 and 10 from the torture set; `cases()` returns each with `offset = (500000.0, 500000.0, 0.0)`. Spike drivers run every candidate twice — at the origin and translated by `offset` — translate the result back, and compare vertex positions after matching.

- [ ] **Step 5: Verify the generators**

Run: `python reference/generate_scale_models.py --count 10000 --out build/scale_10k.obj && python -c "import sys; sys.path.insert(0,'reference'); import boolean_torture_set as b, precision_set as p; print(len(b.cases()), len(p.cases()))"`
Expected: a 10k-box OBJ under `build/`, then `10 3`.

- [ ] **Step 6: Commit**

```bash
git add reference/README.md reference/generate_scale_models.py reference/boolean_torture_set.py reference/precision_set.py
git commit -m "Fix the benchmark set: models, scale generator, boolean torture and precision cases

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: OCCT note

**Files:**
- Create: `docs/research/kernels/occt.md`
- Modify: `docs/research/kernels/problems.md` (P-01, P-02, P-08, P-11, P-12 evidence cells)

**Interfaces:**
- Consumes: `reference/boolean_torture_set.py`, `reference/precision_set.py`.
- Produces: verdicts on *build on / borrow from / avoid*; the tolerance-model description ADR-0006 cites (§Tolerance model); the boolean failure catalogue (§Known problems).

- [ ] **Step 1: Pin the version**

Record the OCCT release tag studied (the latest 7.x release at the time) and its commit hash from the OCCT GitHub mirror. All source links in the note use that commit.

- [ ] **Step 2: Read the primary sources**

At the pinned commit read and cite by path: `src/BOPAlgo/` (the general fuse / boolean algorithm and its options such as fuzzy value and `SetRunParallel`), `src/BRepAlgoAPI/`, `src/BRepCheck/` (validity), `src/ShapeFix/` (healing), `src/BRep/BRep_Tool.cxx` (per-entity tolerance access), `src/BRepMesh/` (tessellation and its deflection parameters), `src/IntPatch/` and `src/GeomInt/` (surface–surface intersection). Read the "Boolean Operations" and "Shape Healing" user guides in `dox/`. From the issue tracker collect at least ten boolean or tolerance failures with links; classify each by trigger (coplanar, tangent, tolerance growth, curved intersection) and by traced cause.

- [ ] **Step 3: Measure**

Install `cadquery-ocp` (pins an OCCT build; record its version). Write `spikes/boolean-torture/occt_driver.py` that runs every torture case through `BRepAlgoAPI_Fuse` and `BRepAlgoAPI_Common` with default and fuzzy settings, checks `BRepCheck_Analyzer`, computes volumes with `GProp`, records timings; and `spikes/precision-set/occt_driver.py` for the precision cases. Also time tessellation (`BRepMesh_IncrementalMesh`) of the 10k scale model. Record in the spike `FINDINGS.md` (Tasks 12–13 assemble them) and summarise in the note's §Measurements.

- [ ] **Step 4: Fill the matrix and write the verdict**

Score every criterion in `kernels/README.md`; answer the twelve questions; write the three-axis verdict. *Borrow from* must list concrete things (for example: the per-entity tolerance concept, the fuzzy-value option, the shape-check categories) with links. *Avoid* must map each documented failure class to the design choice behind it and to the `problems.md` row.

- [ ] **Step 5: Update problems.md and commit**

Fill the *Evidence* and *Status* cells of the rows the note supports.

```bash
git add docs/research/kernels/occt.md docs/research/kernels/problems.md spikes/boolean-torture spikes/precision-set
git commit -m "Add the OCCT research note with torture-set and precision measurements

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: FreeCAD topological-naming case study

**Files:**
- Create: `docs/research/kernels/freecad-topological-naming.md`
- Modify: `docs/research/kernels/problems.md` (P-04)

- [ ] **Step 1: Sources**

The FreeCAD wiki page on the topological naming problem; the RealThunder fork's naming algorithm and its integration into FreeCAD 1.0 (release notes, source under the pinned FreeCAD tag); forum threads documenting user-facing breakage; the OCCT structures the names are derived from.

- [ ] **Step 2: Analysis**

Explain the mechanism: what a name refers to, when the reference breaks, what the mitigation does (element maps, history-based naming) and what it cannot do. State what this means for a kernel that offers generational handles and for an application that references semantic entities (R-13). Verdict on the *avoid* axis only.

- [ ] **Step 3: Commit**

```bash
git add docs/research/kernels/freecad-topological-naming.md docs/research/kernels/problems.md
git commit -m "Add the FreeCAD topological-naming case study

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Blender note

**Files:**
- Create: `docs/research/kernels/blender.md`
- Modify: `docs/research/kernels/problems.md` (P-01, P-07 evidence cells)

**Interfaces:**
- Consumes: torture and precision sets; Blender installed locally (record version and commit from `bpy.app.build_hash`).
- Produces: the exact-boolean description ADR-0005 cites (§Exact boolean), the Carve history (§Carve history), the GPU module summary consumed by Task 11.

- [ ] **Step 1: Pin and read**

Blender release tag and commit. Read at that commit: the exact boolean in `source/blender/blenlib/intern/mesh_boolean.cc` and `mesh_intersect.cc` (arrangement with exact arithmetic via GMP rationals, its manifold and non-manifold handling), the BMesh boolean tool, the BMesh data structure headers, the GPU module (`source/blender/gpu/`, the Vulkan backend directory), and the Geometry Nodes evaluation (depsgraph, `source/blender/functions/`). Read the design documents on the developer site for the exact boolean and for BMesh. Collect issue-tracker reports for both the exact and the fast boolean.

- [ ] **Step 2: Measure**

`spikes/boolean-torture/blender_driver.py` run with `blender --background --python`: build both meshes from the torture set, apply the Boolean modifier with `solver='EXACT'` and `'FAST'`, validate (`bmesh` validity, `mesh.validate()`), compute volumes, time each. Precision set likewise. Record versions.

- [ ] **Step 3: Matrix, verdict, problems.md, commit**

Three-axis verdict. *Borrow from* candidates: the exact-arrangement approach, BMesh's half-edge variant (radial loops), the depsgraph's incremental evaluation model. *Avoid*: per-object overhead behind P-07 (cite R-03 spike when it exists), float32 mesh storage.

```bash
git add docs/research/kernels/blender.md docs/research/kernels/problems.md spikes/boolean-torture/blender_driver.py spikes/precision-set/blender_driver.py
git commit -m "Add the Blender research note with exact-boolean measurements

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Manifold note

**Files:**
- Create: `docs/research/kernels/manifold.md`
- Modify: `docs/research/kernels/problems.md` (P-09)

- [ ] **Step 1: Pin and read**

Manifold release tag; read the boolean implementation and the manifoldness requirements in its README and source; its precision handling; its threading (TBB) and its GPU history. Collect issues on rejected input.

- [ ] **Step 2: Measure**

`pip install manifold3d`; `spikes/boolean-torture/manifold_driver.py` and `spikes/precision-set/manifold_driver.py`. Record which torture cases are rejected as non-manifold input versus solved.

- [ ] **Step 3: Verdict, problems.md, commit**

```bash
git add docs/research/kernels/manifold.md docs/research/kernels/problems.md spikes/boolean-torture/manifold_driver.py spikes/precision-set/manifold_driver.py
git commit -m "Add the Manifold research note with measurements

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: CGAL note

**Files:**
- Create: `docs/research/kernels/cgal.md`
- Modify: `docs/research/kernels/problems.md` (P-03)

- [ ] **Step 1: Pin and read**

CGAL release; read the kernel concepts (exact predicates inexact constructions vs exact everything), `Nef_3`, `Polygon_mesh_processing/corefinement` (the boolean on surface meshes and its preconditions), and the licence per package (GPL vs LGPL). Collect documentation on performance and memory of Nef polyhedra.

- [ ] **Step 2: Measure if bindings allow**

If a maintained Python binding for corefinement booleans is available, run the torture set; otherwise write a minimal C++ driver only if CGAL builds on the reference machine within an hour, else record every performance claim as *claimed* with URL and say so in the verdict.

- [ ] **Step 3: Verdict, problems.md, commit**

*Borrow from* must cover the exact-predicate design (filtered predicates, the `Epeck`/`Epick` distinction) since ADR-0006 rests on it.

```bash
git add docs/research/kernels/cgal.md docs/research/kernels/problems.md spikes/boolean-torture
git commit -m "Add the CGAL research note

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: libigl and OpenMesh note

**Files:**
- Create: `docs/research/kernels/libigl-openmesh.md`

- [ ] **Step 1: Sources**

libigl's mesh arrangement and boolean code and the papers behind it ("Mesh Arrangements for Solid Geometry", Zhou et al. 2016); OpenMesh's half-edge data structure design and property system.

- [ ] **Step 2: Note and commit**

Design-reference note: what the half-edge layout should look like in a structure-of-arrays kernel, what the arrangement algorithm requires from predicates, and the licences. *Borrow from* only.

```bash
git add docs/research/kernels/libigl-openmesh.md
git commit -m "Add the libigl and OpenMesh design-reference note

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Point cloud note

**Files:**
- Create: `docs/research/kernels/pointclouds.md`
- Modify: `docs/research/kernels/problems.md` (P-13)

- [ ] **Step 1: Sources**

PCL (octree, kd-tree, normal estimation, in-core storage), Open3D (tensor-based geometry, octree, IO), PDAL (pipeline model, LAS/LAZ/E57 readers, out-of-core), Potree (the out-of-core octree LOD format and its converter). Pin versions.

- [ ] **Step 2: Measure**

`pip install open3d`; generate 10⁷ and 10⁸ random points (record whether 10⁸ fits in RAM on the reference machine); time octree build and nearest-neighbour queries; record memory. If 10⁸ does not fit, that is the finding for P-13.

- [ ] **Step 3: Verdict, problems.md, commit**

*Borrow from*: Potree's chunked octree layout for the kernel's `pointcloud` module.

```bash
git add docs/research/kernels/pointclouds.md docs/research/kernels/problems.md spikes/pointcloud-scale
git commit -m "Add the point cloud libraries research note with scale measurements

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Implicit representation note

**Files:**
- Create: `docs/research/kernels/implicit.md`

- [ ] **Step 1: Sources**

OpenVDB (sparse volume tree, level sets, CSG on level sets, meshing), libfive (function trees, dual/manifold contouring, its licence), and the dual contouring and manifold dual contouring papers. Pin versions.

- [ ] **Step 2: Note and commit**

Answer: does an implicit representation earn a place in the kernel (spec §4), what does meshing cost, and what does the SDF-from-mesh conversion require. Verdict on *build on* (as a library for the implicit module) and *borrow from*.

```bash
git add docs/research/kernels/implicit.md
git commit -m "Add the implicit representation research note

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: IFC implementations — IfcOpenShell, web-ifc, xBIM

**Files:**
- Create: `docs/research/kernels/ifcopenshell.md`, `docs/research/kernels/web-ifc.md`, `docs/research/kernels/xbim.md`
- Create: `spikes/incremental-evaluation/` (R-01) with `ifcopenshell_driver.py` and `webifc_driver.mjs`
- Modify: `docs/research/kernels/problems.md` (P-06, P-10)

**Interfaces:**
- Consumes: the two benchmark IFC models from Task 2.
- Produces: per-implementation geometry output for the same model (as OBJ per element GUID) so P-10 disagreements are measured, not asserted.

- [ ] **Step 1: IfcOpenShell**

Pin version; read `src/ifcgeom/` (the OCCT-based kernel and the CGAL-based alternative, the iterator model, settings such as `USE_BREP_DATA`, threading in the iterator), the georeferencing API. Measure: load and full geometry iteration on both models (time, memory, threads); export per-element OBJ. **R-01 spike:** change one wall's placement through the API and measure the cost of regenerating only that element's geometry versus re-iterating the model.

- [ ] **Step 2: web-ifc (That Open Company)**

Pin version; read the C++ geometry code under `src/cpp/` (its own boolean and swept-solid implementation, its precision settings, WASM constraints), the loader API. Measure in Node.js on both models: load, geometry generation, per-element OBJ export; the same single-element change scenario as far as the API allows.

- [ ] **Step 3: xBIM**

Pin version; read its geometry engine approach and IFC coverage; measure on Windows via the .NET tooling if it installs within an hour; otherwise documentation-only, labelled.

- [ ] **Step 4: Disagreement analysis**

Compare the per-element OBJ output of the three implementations on the same model: volumes per GUID, elements missing in one, elements whose volume differs by more than 1e-3 relative. Record the entity types involved. This fills P-10 with measured evidence.

- [ ] **Step 5: Verdicts, problems.md, FINDINGS.md, commit**

*Build on* verdict per implementation for `ifc/` (this feeds the later IFC library spec as much as ADR-0004). *Borrow from*: the iterator model, the representation mapping tables.

```bash
git add docs/research/kernels/ifcopenshell.md docs/research/kernels/web-ifc.md docs/research/kernels/xbim.md docs/research/kernels/problems.md spikes/incremental-evaluation
git commit -m "Add the IFC implementation notes with incremental-evaluation and disagreement measurements

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: GPU paths note

**Files:**
- Create: `docs/research/renderers/gpu-paths.md`

- [ ] **Step 1: Sources**

Blender's GPU module and Vulkan backend (from Task 5), OCCT's visualisation layer (`src/OpenGl/`, its tessellation-to-buffer path), wgpu / bevy's mesh and instancing pipeline, Filament's renderable and instancing API, That Open's three.js-based fragments viewer (its instanced-mesh and BVH picking approach), and the DynLex graphics runtime (`../dynlex/src/runtime/graphicsRuntime*.c`, `lib/graphics.dl`, `lib/shader.dl` at the pinned commit): what buffer layouts it accepts, how it uploads, whether compute dispatch exists.

- [ ] **Step 2: Note and commit**

Answer for the kernel's `gpu` module: which vertex layouts and instancing schemes are common to the engines, what camera-relative rendering requires of the kernel, what DynLex already provides and what it lacks (compute dispatch, readback). Verdict feeds ADR-0004's design rationale and spec §3/§6.

```bash
git add docs/research/renderers/gpu-paths.md
git commit -m "Add the GPU paths research note

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 13: Assemble the boolean-torture and precision-set findings

**Files:**
- Create: `spikes/boolean-torture/README.md`, `spikes/boolean-torture/FINDINGS.md`
- Create: `spikes/precision-set/README.md`, `spikes/precision-set/FINDINGS.md`
- Modify: `docs/risks.md` (R-16, R-17 status)

- [ ] **Step 1: Run all drivers on one machine in one session**

Record hardware, OS, every library version. Produce one table per spike: rows = cases, columns = candidates, cells = valid/invalid, volume error, time.

- [ ] **Step 2: Verdict against R-16 and R-17 per candidate**

Write the verdicts exactly against the criteria in `docs/risks.md`; for each failure, the traced cause and the `problems.md` row it supports. Update the risk statuses.

- [ ] **Step 3: Commit**

```bash
git add spikes/boolean-torture spikes/precision-set docs/risks.md
git commit -m "Record boolean-torture and precision-set findings

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: DynLex readiness spikes

**Files:**
- Create: `spikes/dynlex-scale/` (README, generator script, FINDINGS)
- Create: `spikes/dynlex-performance/` (README, `.dl` and `.cpp` sources, FINDINGS)
- Modify: `docs/risks.md` (R-18, R-19 status)

**Interfaces:**
- Consumes: the DynLex compiler at `../dynlex` at the pinned commit (`metadata/DYNLEX_COMMIT` will be created by M0; until then record the commit hash in `FINDINGS.md`).

- [ ] **Step 1: dynlex-scale**

Write `generate.py` producing DynLex programs of 5k, 20k and 50k lines built from repeated kernel-shaped units: a class with three f64 members, ten patterns operating on it, and a main that calls them. Compile each with `-o`; record wall time and peak memory. Verdict against R-18.

- [ ] **Step 2: dynlex-performance**

Write the three workloads in both languages: triangle–triangle intersection test (Möller) over 10⁶ random pairs; BVH build over 10⁶ AABBs; f64 `orient3d` (non-adaptive, plain determinant) over 10⁷ inputs. Compile C++ with `clang++ -O2`; DynLex with the default optimised build. Record times over five runs, report the median. Verdict against R-19. Any DynLex shortfall is minimised and reported as a dynlex issue per its `AGENTS.md`, not patched in the spike.

- [ ] **Step 3: Commit**

```bash
git add spikes/dynlex-scale spikes/dynlex-performance docs/risks.md
git commit -m "Record DynLex compile-scale and runtime-performance findings

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 15: Truck / Fornjot and commercial reference notes

**Files:**
- Create: `docs/research/kernels/truck-fornjot.md`
- Create: `docs/research/kernels/commercial-brep-reference.md`

- [ ] **Step 1: Truck and Fornjot**

Pin versions; read their topology and geometry module layout — small enough to read whole. Note what a clean B-rep data model looks like without twenty years of accretion, and where they stop (booleans, tolerances). *Borrow from* only.

- [ ] **Step 2: Commercial reference**

From public documentation only: what Parasolid-class kernels document about tolerant modelling, precision, and boolean options. Everything *claimed*. Purpose: define what "engineering accuracy" means in industry terms so ADR-0006's tolerances are relative to something.

- [ ] **Step 3: Commit**

```bash
git add docs/research/kernels/truck-fornjot.md docs/research/kernels/commercial-brep-reference.md
git commit -m "Add the small-kernel and commercial-reference notes

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 16: Synthesis and ADR acceptance

**Files:**
- Create: `docs/research/kernels/synthesis.md`
- Modify: `docs/research/kernels/README.md` (candidate checkboxes, completed matrix link)
- Modify: `docs/research/kernels/problems.md` (no row left `hypothesis` without a stated reason)
- Modify: `docs/architecture/decisions/0004`, `0005`, `0006` (evidence tables; status)
- Modify: `docs/architecture/decisions/0003-build-on-an-existing-kernel.md` (status)
- Modify: `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` (status; amended sections)
- Modify: `docs/roadmap.md`, `docs/risks.md`

- [ ] **Step 1: Write the synthesis**

The completed matrix (one row per candidate, every cell labelled), the three-axis verdict per candidate, and the list of design elements the kernel spec adopts from each candidate with citations. Then the honest part: which spec sections the evidence contradicts, and the proposed amendment for each.

- [ ] **Step 2: Fill the evidence tables**

For every row in ADR-0004/0005/0006, the *Where shown* cell now points at an existing section and *Evidence type* is filled. Where evidence is missing, the row says so and the ADR stays `proposed` — record what would fill it.

- [ ] **Step 3: Decide**

For each ADR: `accepted`, or amended (edit Decision and Evidence, keep `proposed` for another round), or `withdrawn` with the reason. If ADR-0004 is accepted, ADR-0003's status becomes `superseded by [ADR-0004](0004-build-our-own-kernel-in-dynlex.md)`; if withdrawn, ADR-0003 is reaffirmed and the M0 plan is retired. Update the spec status and amend sections the synthesis marked.

- [ ] **Step 4: Verify traceability**

Run: `grep -n '^| .* | .* | *|$' docs/architecture/decisions/000[456]*.md; echo "exit=$?"`
Expected: no output and `exit=1` for any ADR marked `accepted` (no empty evidence-type cell).

- [ ] **Step 5: Commit**

```bash
git add docs/research docs/architecture/decisions docs/superpowers/specs docs/roadmap.md docs/risks.md
git commit -m "Synthesise the kernel research and decide ADR-0004, 0005 and 0006 on the evidence

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Verification of the whole programme

- Every file under `docs/research/kernels/` opens with a decision question and names the ADR or spec section it serves.
- `grep -rn "claimed\|measured\|inferred" docs/research/kernels/*.md` shows every evaluation row labelled.
- `docs/research/kernels/problems.md` has no `hypothesis` row without a stated reason for the missing evidence.
- Every `spikes/*/FINDINGS.md` records hardware, versions, model, method, numbers and a verdict against a criterion that appears verbatim in `docs/risks.md`.
- Each ADR marked `accepted` has a complete evidence table; the M0 plan is unblocked only then.
