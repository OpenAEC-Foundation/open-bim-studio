# Disagreement analysis (P-10) — measured

**The question:** [`problems.md`](../../../docs/research/kernels/problems.md) P-10 says "IFC
geometry interpreted differently by different implementations", and until now carried no
evidence. How much do they actually disagree, on what, and by how much?

Written from `compare_raw.json` in this directory, produced by `../compare.py` from the
per-GUID element tables the two drivers wrote. Every number below appears in that file.

## What is compared, and how

One row per `GlobalId`. Where an implementation emits several meshes for one product, the
triangle counts and volumes are summed so that the unit of comparison is the product. Both
drivers compute the signed volume with the **same formula** —
`1/6 · Σ a · (b × c)` over the triangles, in world coordinates — implemented separately in
Python and in JavaScript. A difference in the number is therefore a difference in the triangles
each implementation produced, not a difference in how they were measured.

Relative difference is `|v_a − v_b| / max(|v_a|, |v_b|)`; the threshold is **1e-3**, taken from
the brief. Rows with zero triangles are counted and reported separately from rows with geometry,
because counting an empty entry as "produced by one and not the other" would overstate the
disagreement.

Three pairings:

| Pairing | What it isolates |
|---|---|
| **IfcOpenShell (opencascade) vs web-ifc** | Two implementations, two parsers, two schema mappings, two kernels. Everything can differ. |
| **IfcOpenShell (opencascade) vs IfcOpenShell (cgal-simple)** | **One implementation, one parser, one schema mapping, two kernels.** Anything this pair disagrees on cannot be blamed on a different reading of the schema. |
| **IfcOpenShell (cgal-simple) vs web-ifc** | For completeness. |

The second pairing is what replaces the third implementation the brief asked for. xBIM was not
measured — no .NET SDK on this machine, see
[`xbim.md`](../../../docs/research/kernels/xbim.md) — and it would in any case have been a
near-duplicate of IfcOpenShell's geometry opinion, since both wrap **OCCT 7.8.1**.

The GUID join is sound: neither model has an `IfcProduct` GlobalId used more than once (127 of
127 distinct, 3,822 of 3,822), so no two products collapse into one row.

## Element counts checked against `reference/README.md`

`compare.py` parses the element counts out of `reference/README.md` rather than having them
retyped, and compares them with what the drivers counted on this run:

| Model | `IfcProduct`, README | `IfcProduct`, measured now | per-class counts checked | mismatches |
|---|---|---|---|---|
| AC20-FZK-Haus | 127 | 127 | 12 | **0** |
| IFC_Schependomlaan | 3,822 | 3,822 | 15 | **0** |

`reference/README.md` lists only the larger classes, so classes it omits are not checked; every
class it does list agrees exactly.

## IfcOpenShell (OCCT) vs web-ifc

| | AC20-FZK-Haus | IFC_Schependomlaan |
|---|---|---|
| Rows, IfcOpenShell / web-ifc | 107 / 103 | 3,654 / 3,643 |
| Rows with zero triangles | 0 / 20 | 65 / 139 |
| GUIDs in both | 83 | 3,569 |
| Only in IfcOpenShell (all with geometry) | 24 | 85 |
| Only in web-ifc (all with **zero** triangles) | 20 | 74 |
| **Volume agrees within 1e-3 relative** | **82 of 83** | **3,556 of 3,569** |
| Volume differs by more than 1e-3 relative | 1 | 13 |
| Identical triangle count | 73 | 3,530 |

**The headline is agreement, not disagreement.** On the real building, 3,556 of 3,569 shared
products agree on volume to within one part in a thousand, and 3,530 of them — 98.9% — produce
*byte-for-byte identical triangle counts* from two independently written geometry engines. P-10
as stated ("interpreted differently") is far weaker than the hypothesis assumed.

### What each side produces that the other does not

Neither list is a disagreement about geometry; both are differences in **what counts as an
element**.

| Only in IfcOpenShell | AC20 | Schependomlaan |
|---|---|---|
| `IfcOpeningElement` | 17 | 79 |
| `IfcSpace` | 7 | 6 |

IfcOpenShell's iterator emits openings and spaces as elements in their own right. web-ifc does
not. Both are defensible; they are different answers to "what is a product with geometry".

| Only in web-ifc (every one with zero triangles) | AC20 | Schependomlaan |
|---|---|---|
| `IfcAnnotation` | 14 | — |
| `IfcCovering` | — | 48 |
| `IfcVirtualElement` | 3 | 14 |
| `IfcBuildingStorey` | 2 | 6 |
| `IfcWall` | — | **4** |
| `IfcBuilding` | 1 | 1 |
| `IfcSite` | — | 1 |

web-ifc emits an entry for products that have no geometry to give, including spatial containers
(`IfcBuildingStorey`, `IfcBuilding`, `IfcSite`) and `IfcVirtualElement`. The 48 `IfcCovering` are
exactly the coverings that carry no `Representation` at all (IFC_Schependomlaan has 1,262
`IfcCovering`, of which 1,214 have one).

The four `IfcWall` are the interesting row. IfcOpenShell's `create_shape` raises `RuntimeError`
on exactly **four** `IfcWall` in this model (see [`ifcopenshell.md`](ifcopenshell.md) §Failures
by entity type), and web-ifc emits exactly four `IfcWall` with zero triangles that IfcOpenShell's
table lacks. The counts agree; that these are the same four walls is **inferred**, not measured —
the driver records the failing class, not the failing GlobalId, and `compare_raw.json` names the
four GUIDs on web-ifc's side only. What is measured is that **both implementations fail to
produce geometry for four walls**, and that they fail differently: one raises, the other returns
an empty mesh with no error.

### The disagreements that do exist are severe

Grouped by magnitude:

| Relative difference | AC20 | Schependomlaan |
|---|---|---|
| 1e-3 to 1e-2 | 1 | 2 |
| 1e-2 to 1e-1 | 0 | 4 |
| 1e-1 to 0.5 | 0 | 0 |
| **over 0.5** | 0 | **7** |

By class on IFC_Schependomlaan: `IfcDistributionElement` 5, `IfcWindow` 4, `IfcCovering` 2,
`IfcWall` 1, `IfcSlab` 1. AC20-FZK-Haus's single disagreement is one `IfcStair`, 0.00159
relative (0.20758 vs 0.20791 with 2,614 vs 2,628 triangles) — a tessellation difference, nothing
more.

The five largest on IFC_Schependomlaan:

| GlobalId | Class | IfcOpenShell | web-ifc | rel. diff | triangles |
|---|---|---|---|---|---|
| `3Wp4aZh5H6qPRVFtOem3_A` | `IfcWindow` | **−0.2476** | +0.0874 | 1.353 | 7,604 / 7,676 |
| `11RySdoR58kP5miKc_WA6F` | `IfcWindow` | **−0.00442** | +0.1142 | 1.039 | 7,604 / 7,674 |
| `3AuBloy8rB2eQ0HbTV6Kmm` | `IfcWall` | **96.550** | 0.3268 | 0.997 | 39 / 42 |
| `15m0CeBGfECerYsUDbEOge` | `IfcWindow` | 0.3352 | 0.00301 | 0.991 | 7,604 / 7,674 |
| `2GKCxEc8DCcQXZmul0WfvP` | `IfcSlab` | 0.01102 | 0.1967 | 0.944 | 41 / 44 |

Two observations that matter more than the counts:

1. **Negative volumes.** Two of the five are negative on IfcOpenShell's side. A signed volume is
   negative only if the shell is not closed and consistently outward-oriented. The metric is
   still a deterministic function of the triangles — which is all the comparison needs — but
   these particular numbers say the *shell* is broken, not merely that the two disagree. The
   comparison detects the defect; it does not quantify it, and a relative difference of 1.35
   between a wrong number and another number should not be read as "35% off".
2. **`3AuBloy8rB2eQ0HbTV6Kmm`: 96.55 m³ against 0.33 m³, from 39 triangles against 42.** Two
   engines produced almost the same triangle *count* and volumes three orders of magnitude
   apart. That is a wildly misplaced vertex, not a tessellation difference.

The `IfcWindow` rows are consistent with the per-element timings: the same windows are
IfcOpenShell's three slowest elements at 530–554 ms each, with 7,604 triangles apiece. Expensive
and wrong travel together here.

## IfcOpenShell (OCCT) vs IfcOpenShell (cgal-simple) — one parser, two kernels

| | AC20-FZK-Haus | IFC_Schependomlaan |
|---|---|---|
| Rows, opencascade / cgal-simple | 107 / 103 | 3,654 / 3,646 |
| Rows with zero triangles | 0 / 7 | 65 / 71 |
| GUIDs in both | 103 | 3,646 |
| Only in opencascade (with geometry) | 4 (`IfcWallStandardCase`) | 8 (`IfcDistributionElement` 6, `IfcCovering` 2) |
| Only in cgal-simple | 0 | 0 |
| Volume agrees within 1e-3 relative | 95 of 103 | 3,626 of 3,646 |
| **Volume differs by more than 1e-3** | **8** | **20** |
| of which over 0.5 relative | **7** | **17** |
| Identical triangle count | 95 | 3,614 |

**This pairing disagrees more than the cross-implementation one** — 20 against 13 on
IFC_Schependomlaan, and 17 of the 20 over 0.5 relative against 7 of 13. One parser, one schema
mapping, one set of settings; only the kernel differs. Whatever P-10 is about, **it is not
primarily about implementations reading the schema differently**.

The mechanism is visible in the numbers and confirmed in the source. Every one of the large
disagreements has the same shape:

| GlobalId | Class | opencascade | cgal-simple | triangles |
|---|---|---|---|---|
| `0uG931DjD31hhRwgBkGmit` | `IfcWallStandardCase` | 0.1061 | **0.0** | 48 / **0** |
| `1J9G$AMj5D8ePpFewsM_ee` | `IfcWallStandardCase` | 0.0137 | **0.0** | 12 / **0** |
| `16DNNqzfP2thtfaOflvsKA` (AC20) | `IfcWallStandardCase` | 6.6049 | **0.0** | 84 / **0** |
| `2RGlQk4xH47RHK93zcTzUL` (AC20) | `IfcSlab` | 19.967 | **0.0** | 32 / **0** |

`cgal-simple` returns an **empty result** where `opencascade` returns a solid. The reason is in
the hybrid kernel's own source: it skips a kernel for an element that has openings when that
kernel does not support boolean operations, with the comment that the resulting
`SimpleCgalShape` "cannot be used on a kernel that supports booleans"
([`hybrid_kernel.h#L83-L107`](https://github.com/IfcOpenShell/IfcOpenShell/blob/158fe92644cfe2bc37be513d9838c95d9f2233cf/src/ifcgeom/hybrid_kernel.h#L83-L107)).
`cgal-simple` has no booleans, so a wall with an opening comes back empty — silently, with no
error and no exception.

That is also why `hybrid-cgal-simple-opencascade` exists, why it produces the full 107 / 3,654
elements, and why it is 13× faster than `opencascade` on the larger model (see
[`ifcopenshell.md`](ifcopenshell.md)): it runs the cheap kernel on everything that does not need
booleans and falls back to OCCT for everything that does.

Not every disagreement in this pairing is an empty result, though. The two largest on
IFC_Schependomlaan are the same `IfcWindow` products as in the cross-implementation table, with
**identical triangle counts** and different volumes:

| GlobalId | Class | opencascade | cgal-simple | triangles |
|---|---|---|---|---|
| `0qOSzz4qrCIO8I0BFBBwg9` | `IfcWindow` | 0.1456 | **−0.0526** | 7,604 / 7,676 |
| `3Wp4aZh5H6qPRVFtOem3_A` | `IfcWindow` | **−0.2476** | 1.1534 | 7,604 / 7,676 |

Three engines — OCCT, CGAL-simple and web-ifc's own — give three different answers for
`3Wp4aZh5H6qPRVFtOem3_A`: −0.2476, 1.1534 and 0.0874. Two of the three are negative somewhere in
the set, so at least two of the three shells are not closed. This element is the sharpest single
piece of P-10 evidence in the run, and it is worth keeping as a named regression case.

## IfcOpenShell (cgal-simple) vs web-ifc

Reported for completeness; it mostly reproduces the two pairings above.

| | AC20-FZK-Haus | IFC_Schependomlaan |
|---|---|---|
| GUIDs in both | 79 | 3,561 |
| Volume agrees within 1e-3 | 72 | 3,545 |
| Volume differs by more than 1e-3 | 7 | 16 |
| of which over 0.5 relative | 7 | 15 |
| Identical triangle count | 63 | 3,528 |

## What this settles, and what it does not

**Settled:**

- Two independently written IFC geometry implementations agree on volume to 1e-3 relative for
  **99.6%** of the products they both produce on the real building (3,556 / 3,569), and produce
  identical triangle counts for 98.9% of them.
- Where they disagree, they disagree **badly**: 7 of 13 by more than 0.5 relative, including a
  wall off by three orders of magnitude.
- The disagreements are **not** mainly caused by different readings of the schema. Two kernels
  behind *one* parser disagree on more products (20) than two full implementations do (13).
- A kernel without booleans returns an empty solid for a wall with an opening, with no error.
- Both implementations fail to produce geometry for four `IfcWall` in IFC_Schependomlaan, and
  fail differently — one raises, the other returns an empty mesh silently.

**Not settled:**

- **Which one is right.** Nothing here has a ground truth. The benchmark set's boolean torture
  cases have known volumes; these building models do not. "They disagree" is measured; "web-ifc
  is wrong about `3AuBloy8rB2eQ0HbTV6Kmm`" is not.
- **Whether the rate generalises.** Two models, one IFC4 and one IFC2x3, both from open test
  sets. 13 disagreements in 3,569 products is a rate on *these* files.
- **Whether a third implementation would agree.** xBIM was not measured, and would have shared
  OCCT 7.8.1 with IfcOpenShell if it had been.
- **The identity of the four failing walls** across the two implementations — counts agree,
  GUIDs are recorded on one side only.
