# Commercial B-rep reference — what "engineering accuracy" means in industry practice

**Decision question:** ADR-0006 sets the kernel's default tolerances at 1e-6 m linear and 1e-9 rad
angular. Relative to what? This note answers **what "engineering accuracy" is documented to mean
in industry CAD practice** — the default precision, the tolerant-modelling mechanism, and the
model-size limit two widely-deployed commercial B-rep kernels state in their own public
documentation — so ADR-0006's numbers can be judged against a real, cited baseline rather than
an assumption.

**Serves:** ADR-0006 (evidence row "tolerant B-rep accumulates tolerance", and a new comparison
row this note supplies); kernel spec §5; `problems.md` P-02

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> This is a **documentation-only note**: no source code was obtained (neither kernel publishes its
> source), no spike was run, and nothing here is measured. Every figure is **claimed** — but the
> pages it is claimed from are **not the vendors' own sites**. Siemens (Parasolid) and Spatial/
> Dassault Systèmes (ACIS) both gate their current documentation behind a customer login; every
> figure in this note is read instead from third-party mirrors that host older public copies of
> that documentation — q-solid.com (Parasolid v35; ACIS, explicitly labelled "R17" in its own URL
> path and carrying the footer "© 1989-2007 Spatial Corp., a Dassault Systèmes company") and
> www-isl.ece.arizona.edu (ACIS, an older, undated-by-release-number snapshot — its pages carry an
> internal page timestamp of "Spatial Technology Wed Nov 20 11:14:14 MST 2002", the company's name
> before the "Spatial Corp." branding q-solid's R17 pages use, and no release number is stated on
> the page itself). The ACIS row below therefore draws on **two mirrors of two different ACIS
> releases**, not one; each citation in the table and prose states which. URL and access date are
> given for every mirror page read (all 2026-09-11, this note's date). No competing geotechnical or
> structural calculation software is named anywhere in this note, per the repository's naming rule;
> Parasolid and ACIS are B-rep CAD kernels, the subject this repository's exception explicitly
> permits.

---

## Summary

Both kernels define "engineering accuracy" the same way: a single linear distance below which two
points are the same point, a single angle below which two directions are parallel, and a hard
ceiling on how large a model can be relative to that distance — not a philosophy, a pair of
numbers and a ratio. Parasolid's defaults are 1.0e-8 units linear and 1.0e-11 rad angular, inside a
1000×1000×1000-unit box (recommended as 1 km at 1 model-unit = 1 m) — a ratio of roughly **10¹¹**
between model extent and linear precision. ACIS's `SPAresabs` defaults to 1e-6 (application-defined
units) with `SPAresnor` = 1e-10; the vendor states the model space directly in prose while deriving
a third constant from it — "our model space is 10⁴ and the smallest geometric feature that can be
modeled is 10⁻⁶" (`SPAresmch`, §ACIS below) — which is also algebraically forced by the stated
`SPAresnor = SPAresabs/largest` definition: `SPAresabs / SPAresnor` = 1e4 units — a ratio of
**10¹⁰**. Both then layer a second mechanism, tolerant modelling, on top of the fixed precision: a
per-edge and per-vertex tolerance value, attached only to imported or otherwise imprecise geometry,
that both vendors describe in near-identical language — Parasolid as edges-as-tubes and
vertices-as-spheres, ACIS as a `TEDGE`/`TCOEDGE` pair of subclasses derived from `EDGE`/`COEDGE`
carrying an explicit tolerance field (tolerant vertices are named only in the same page's prose,
not as a third derived class). This is the same design OCCT ships as its *only* tolerance model,
not an add-on (`occt.md` §Tolerance model). ADR-0006's 1e-6 m default ties ACIS's `SPAresabs`
default exactly, two orders of magnitude looser than Parasolid's 1e-8-unit linear precision, and
one order looser than OCCT's `Precision::Confusion()` (1e-7 m) — it ties the loosest of the four,
but by no more than two decades, not an outlier by orders of magnitude.

## The numbers, sourced

| Kernel | Linear precision default | Angular precision default | Tolerant-modelling mechanism | Model-size limit | Source · date |
|---|---|---|---|---|---|
| **Parasolid** | 1.0e-8 units ("session precision") | 1.0e-11 rad ("session angle precision") | Local precision set per edge/vertex ("Tolerant Modelling"); edges as tubes, vertices as spheres; the SP-curve geometry attached to the edge replaces the exact 3-space curve | 1000×1000×1000-unit size box, centred at origin; recommended unit = 1 m → ≈1 km max extent | [Session And Local Precision, Parasolid v35 docs](http://www.q-solid.com/Parasolid_Docs_V35/chapters/fd_chap.017.html), accessed 2026-09-11 |
| **ACIS** | 1.0e-6 (`SPAresabs`, application-defined units — "[o]ne could think of the numbers as being inches, or millimeters, or any other unit") | none stated as a separate angular constant — see §ACIS below for how ACIS folds angle into the same resolution family | `TEDGE`/`TCOEDGE` classes derived from `EDGE`/`COEDGE`, storing an explicit tolerance; loops need not close within `SPAresabs` | Largest representable quantity = `SPAresabs / SPAresnor` = 1e-6 / 1e-10 = **1e4** units, also stated directly in prose ("our model space is 10⁴", §ACIS below) | [Tolerance Variables, ACIS user guide (R17 mirror, q-solid.com)](http://www.q-solid.com/ACIS_Docs_R17/online/SPAacisuserTechArticles/SPAacisuser_totol.htm); [Units and Sharing Model Data (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0006.HTM); [SPAresabs (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0002.HTM); [Tolerant Edges (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/KERN/KERN/06TMOD/0002.HTM), accessed 2026-09-11 |
| **OCCT** (for comparison — already in this directory, not re-derived here) | `Precision::Confusion()` = 1e-7 m | `Precision::Angular()` = 1e-12 rad | Per-entity tolerance on `TopoDS` vertex/edge/face; grows, monotone by convention, never a required floor other than the constants | None found in the source read for `occt.md` — no size-box constant located | [`occt.md`](occt.md) §Tolerance model |
| **Our kernel spec (ADR-0006)** | 1e-6 m | 1e-9 rad | Explicit per-entity tolerance, grows but never shrinks (spec §5) | No fixed box — f64 local coordinates in tile frames; the precision-set spike tested 500 km at 1e-6 m (ratio ≈5e11) | [ADR-0006](../../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md); [kernel spec §5](../../superpowers/specs/2026-09-09-geometry-kernel-design.md) |

All four rows use the same two-number-plus-ratio shape, which is itself a finding: none of the
three prior-art kernels states "engineering accuracy" as a single number — each states a distance,
an angle, and a bound on how far the distance can be trusted, together.

## Parasolid — session precision and Tolerant Modelling

*Claimed*, read from the Parasolid v35 user documentation, "Session And Local Precision" chapter
(link above). Quoted directly:

> "Parasolid performs all calculations to fixed accuracies called the session precision and
> session angle precision… A Parasolid model is very precise; typically points are not considered
> coincident unless they are less than 1.0e-8 units apart (linear precision). Also, directions are
> considered to be parallel if they differ by less than 1.0e-11 radians."

The size box is stated as a hard modelling constraint, not a recommendation: "all parts of a body
must be within a box… whose size is 1000 by 1000 by 1000, and is centered at the origin," with the
application advised to use 1 metre as the default unit, "giving 1 kilometer as the maximum distance,
in any one direction, that can be modelled." The documentation is explicit about the *safety
margin* it expects applications to keep, not just the hard floor: vertices not intended to be
coincident should be separated by "more than 100 times linear precision," and non-parallel edges
by more than 100 times angular precision. *Inferred* from that stated ratio: the working precision
a well-behaved model should target is roughly 1e-6 units (100 × 1e-8), one order of magnitude
above the hard 1e-8 floor — this multiplication is this note's own arithmetic, not the vendor's.

**Tolerant Modelling** is presented as the mechanism for anything below that floor, used both for
imported parts and internally by Parasolid's own operations: "Setting local precision in this way
is known as Tolerant Modelling… think of edges as tubes, and vertices as spheres. The lower the
precision, the thicker the tube or the larger the diameter of the sphere." Local precision is
stored *per edge and vertex*, not globally — the exact per-entity model OCCT also uses — and the
documentation states a propagation rule directly analogous to OCCT's monotone tolerance growth
(`occt.md` §Per-entity tolerance): "The vertices V1 and V2 automatically have their local precision
set to the same as that of edge E1… The precision of a vertex must always be at least as large as
the largest precision of any edge ending at that vertex." This is the same invariant OCCT's boolean
specification states for vertex/edge interference (`occt.md` §Tolerance model, `Tol(Vi) = Max(...)`)
— independently documented by two unrelated commercial kernels, which sharpens `problems.md` P-02
(below).

A performance warning is stated for tight local precision: "Precision in the range 1.0e-6 to
1.0e-8 modeller units is likely to result in the generation of SP-curves with large numbers of
segments, these can result in a corresponding drop in performance" — the same class of trade-off
OCCT's own documentation names for fuzzy tolerance (`occt.md` §Known problems).

## ACIS — the resolution family and tolerant edges

*Claimed*, read from the ACIS Kernel documentation's "Tolerance Variables" article and the
"SPAresabs"/"Tolerant Edges" reference pages (links above, R17 mirror and older-release mirror
respectively — see the preamble for which page is which). ACIS names five related constants, all
quoted directly.

Units first, since the table above calls `SPAresabs` "application-defined units": ACIS documents
itself as historically unitless — "ACIS was designed around the concept that all parts are modeled
in a single *unitless* number space (object space). One could think of the numbers as being
inches, or millimeters, or any other unit" — while separately choosing millimetres as the default
*save-file* unit for interchange between applications ([Units and Sharing Model Data, ACIS Kernel
documentation](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0006.HTM),
accessed 2026-09-11, older-release mirror).

- **`SPAresabs`** — "resolution absolute… the smallest meaningful quantity representable in
  ACIS… the distance below which ACIS considers two points to be coincident… also represents the
  smallest feature being modeled… The default value is 10⁻⁶. The default value was chosen assuming
  that at least an order of magnitude guard band around `SPAresabs` is required."
- **`SPAresnor`** — "resolution normalized… the ratio of the smallest meaningful quantity
  representable in ACIS (`SPAresabs`) to the largest… The default value is 10⁻¹⁰." The
  documentation states the relationship in text — "From the definition `SPAresnor` =
  `SPAresabs`/largest, the largest quantity representable in ACIS is:" — followed by a formula
  rendered as an inline image this note could not read. Algebraically forced by that stated
  definition: `SPAresabs / SPAresnor` = 1e-6 / 1e-10 = **1e4**, the model-size limit in the table
  above — stated by the vendor as a formula rather than a fixed box the way Parasolid states its
  size box. This figure is not only this note's own arithmetic: the `SPAresmch` derivation quoted
  below independently states the same 1e4 in readable prose on the same page ("our model space is
  10⁴"), so the model-size limit is a **claimed** figure, read directly, not solely an inference
  from the unreadable image.
- **`SPAresfit`** — "resolution fit… used as a guide to the fitting algorithms for the fit
  tolerance of an approximate curve or surface. The default value is 10⁻³" — three orders of
  magnitude looser than `SPAresabs`, consistent with a fitted approximation needing far less
  precision than a coincidence test.
- **`SPAresmch`** — "resolution machine… the precision at which the machine is operating." The
  documentation derives this one arithmetically from the other two and states the derivation in
  the text: "our model space is 10⁴ and the smallest geometric feature that can be modeled is
  10⁻⁶, we need the machine to ensure a resolution of 10⁻⁶/10⁴ = 10⁻¹⁰. To provide algorithms…
  a bit more computational freedom, we actually set `SPAresmch` to 10⁻¹¹." This is the clearest
  explicit statement found in either vendor's documentation of the *model-extent-to-precision
  ratio* as the quantity that actually constrains a kernel's internal arithmetic, rather than
  either number alone.

Tolerant modelling in ACIS is a distinct pair of subclasses, not a field on the base topology
types: "Tolerant modeling derives a new `TEDGE` class from `EDGE` and `TCOEDGE` from `COEDGE`, and
stores the tolerance as well as the explicit parameterization to limit the edge. The tolerance for
the edge is defined as the maximum distance from the 2D parametric coedges of the adjacent faces…
Loops with tolerant edges and vertices are not required to close to within `SPAresabs`." A
`TEDGE`'s tolerance is compared against `SPAresabs` itself when deciding coincidence: "If the
tolerance value is less than `SPAresabs`, then `SPAresabs` is used for coincidence checking" — the
tolerance can only widen the comparison, never tighten it below the global floor, the same one-way
relationship OCCT's constants enforce as a clamp (`occt.md` §The constants, "They are floors, not
defaults").

## What "tolerant B-rep" means across three kernels — the shared shape

Reading Parasolid, ACIS and OCCT (`occt.md`) side by side, "tolerant B-rep" is the same idea
independently arrived at three times: attach a small, explicit distance (a tolerance) to
individual topological entities, so that geometry which is *almost* consistent can still form a
valid model, at the cost of a comparison that is no longer against zero but against that stored
value. All three describe the mechanism with the same two properties:

1. **It is opt-in per entity, not a global relaxation.** Parasolid's local precision is set on
   specific edges/vertices via `PK_EDGE_set_precision_2`; ACIS's `TEDGE`/`TCOEDGE` are distinct
   subclasses an entity becomes only when it needs the mechanism; OCCT's tolerance field exists on
   every entity but is only *raised above the floor* where an operation actually needed it
   (`occt.md` §Per-entity tolerance, "growth happens only where an interference actually had to be
   resolved").
2. **It only widens, never narrows, below a hard floor.** Parasolid's exact entities are fixed at
   half the session precision and local precision cannot make an entity *more* exact than the
   session precision allows; ACIS's `SPAresabs` is always the floor a `TEDGE`'s own tolerance is
   compared against when it would otherwise be tighter; OCCT's `Precision::Confusion()` is a
   `constexpr` floor every tolerance-accepting API clamps upward to (`occt.md` §The constants).

The one place the three diverge is **scope**: Parasolid and ACIS both impose a hard, documented
ceiling on total model extent relative to the fixed precision (the size box; the
`SPAresabs`/`SPAresnor` ratio). No equivalent constant was found anywhere in the OCCT source read
for `occt.md` — OCCT's own documented limit is different in kind, a *parametrisation* ceiling
("[p]ast roughly a 1e6 scale factor, p-curve angles… become indistinguishable in double precision,"
`occt.md` §Known problems, item 4) rather than a fixed extent-to-precision ratio stated as a
product requirement. This is a genuine difference in what "engineering accuracy" is scoped to mean
between OCCT and its two commercial peers, not merely a documentation gap — inferred from the
absence, not confirmed by an OCCT source that explicitly disclaims a size box.

## Open CASCADE's own tolerance philosophy, and the tolerant-modelling literature

*Claimed*, one paragraph each, per the brief's optional item. Open CASCADE Technology's own
documentation frames its per-entity tolerance model as the deliberate generalisation of exact
B-rep, not a compromise bolted on afterward — the boolean specification's "Algorithm Limitations"
chapter states plainly that shape validity (`BRepCheck_Analyzer`) is "a necessary but insufficient
requirement" for a boolean argument (`occt.md` §Known problems, quoting
`boolean_operations.md#L2477`), which only makes sense as a design statement if tolerance is
understood as load-bearing throughout the topology, not a fallback path. This matches the
tolerant-modelling literature's own framing: David J. Jackson's **"Boundary representation
modelling with local tolerances"** (Proceedings of the Third ACM Symposium on Solid Modeling and
Applications, 1995, DOI [10.1145/218013.218067](https://doi.org/10.1145/218013.218067)) is the
paper most frequently cited as the origin of exactly this idea — a tolerance value attached to
each B-rep entity rather than one global epsilon — which both OCCT and, independently, ACIS's
`TEDGE`/`TCOEDGE` design and Parasolid's local-precision mechanism converge on in production
kernels roughly contemporaneously. An earlier paper, Shuming Fang and Beat Brüderlin's
**"Robustness in geometric modeling — tolerance-based methods"** (in *Computational Geometry:
Methods, Algorithms and Applications*, Springer LNCS 553, 1991, DOI
[10.1007/3-540-54891-2_7](https://doi.org/10.1007/3-540-54891-2_7)), predates Jackson's paper by
four years and is cited in the tolerance-based-modelling literature as an earlier statement of the
same family of methods. Neither paper's full text was read for this note — both sit behind a
publisher paywall from this environment (`dl.acm.org` returned a Cloudflare challenge page to an
automated fetch; the Springer chapter was not attempted for the same reason) — so both citations
are to the paper's existence, title and DOI only, not to a verified quotation from the text.

## Verdict

**Comparison with ADR-0006, and what the kernel spec should take from it.** *Inferred* — this
section draws conclusions the sources above do not state themselves.

**ADR-0006's 1e-6 m linear default ties the loosest of the four, but not by an order that stands
out:** it matches ACIS's `SPAresabs` default (1e-6) to the digit — the two tie exactly, neither
looser than the other — though ACIS's units are application-defined rather than fixed at metres;
ADR-0006 is two orders of magnitude looser than Parasolid's 1e-8-unit session precision, and one
order looser than OCCT's 1e-7 m `Precision::Confusion()`. By the standard "what do working kernels
ship" test the README's weighting matrix implicitly asks, this is a defensible default within the
documented range, not an outlier by orders of magnitude — but it is worth ADR-0006 stating plainly
that its default ties the loosest of the three prior-art numbers gathered here (with ACIS), not
the tightest or the median, since a reader skimming only the headline number could otherwise
assume the opposite.

**ADR-0006's angular default (1e-9 rad) is looser than either commercial kernel's**, by two orders
against Parasolid (1e-11 rad) and by three against OCCT (1e-12 rad, `Precision::Angular()`). No
angular constant was found in ACIS's documentation to compare directly (§ACIS, above) — the
closest ACIS analogue, `SPAresmch` (1e-11), is a general machine-precision floor rather than an
angle-specific tolerance, so it is not a like-for-like comparison. This is the one row in the
table where ADR-0006's number is not close to any of the three prior-art defaults; it is not
evidence the choice is wrong — a looser angular tolerance is a reasonable trade against a planar-
dominant BIM geometry set with far fewer curved-surface tangency decisions than a mechanical-CAD
model — but it is a gap between ADR-0006's evidence table and what this note found, worth a
one-line note in ADR-0006 rather than silence.

**The model-extent-to-precision ratio is where ADR-0006's design diverges most from both
commercial kernels, deliberately.** Parasolid and ACIS both fix a hard ceiling (ratio ≈1e11 and
≈1e10 respectively) because both use a single global coordinate frame with a fixed precision. The
kernel spec's tile-frame architecture (spec §5) sidesteps the ceiling itself — precision is local
to a tile, not global to the model — but the precision-set spike's own 500 km test case, at the
1e-6 m default tolerance, implies an *effective* ratio of ≈5e11 within a single tile: roughly 5×
Parasolid's ceiling and roughly 50× ACIS's. This is not a defect: OCCT measured translation-
invariance to 3.6e-10 m at 500 km (`occt.md` §Precision set), an f64 result the commercial
kernels' own fixed-precision design does not need to reach because their size box is two to three
orders of magnitude smaller than 500 km to begin with. The kernel spec should record this
explicitly as the reason a tile-frame architecture can sustain a *larger* extent-to-precision ratio
than either commercial kernel without loosening the tolerance: **the ratio these vendors document
is a consequence
of picking float-friendly single-frame session precision, not a property of "engineering accuracy"
itself** — our tile architecture buys the same or better accuracy at 500 km by changing what the
ratio is taken over (a tile, not the whole projected CRS), which is a different lever from the one
either commercial kernel's documentation exposes.

## Update to `problems.md`

- **P-02** (tolerance growth): Parasolid's local-precision propagation rule — "the precision of a
  vertex must always be at least as large as the largest precision of any edge ending at that
  vertex" — is added as commercial-kernel evidence that the monotone-growth pattern `problems.md`
  already documents for OCCT booleans is not an OCCT-specific artefact; it is the same invariant
  independently stated for a different operation (setting local precision, not booleans) by an
  unrelated commercial kernel. This strengthens the row's "shown" status without changing its
  content — the row's existing conclusion (tolerances are explicit, per-entity, monotone) is now
  supported by three independently-documented kernels rather than one measured and one claimed.

## Sources

- [Session And Local Precision, Parasolid v35 user documentation, third-party mirror](http://www.q-solid.com/Parasolid_Docs_V35/chapters/fd_chap.017.html), accessed 2026-09-11
- [Tolerance Variables, ACIS user guide (R17, q-solid.com mirror)](http://www.q-solid.com/ACIS_Docs_R17/online/SPAacisuserTechArticles/SPAacisuser_totol.htm), accessed 2026-09-11
- [Units and Sharing Model Data, ACIS Kernel documentation (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0006.HTM), accessed 2026-09-11
- [SPAresabs, ACIS Kernel reference (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0002.HTM), accessed 2026-09-11
- [SPAresabs scaling, ACIS Kernel reference (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/ACIS/FCG/08TOL/0008.HTM), accessed 2026-09-11
- [Tolerant Edges, ACIS Kernel Tolerant Modeling chapter (older release, arizona.edu mirror)](http://www-isl.ece.arizona.edu/ACIS-docs/HTM/DATA/KERN/KERN/06TMOD/0002.HTM), accessed 2026-09-11
- Jackson, D.J., "Boundary representation modelling with local tolerances," Proc. 3rd ACM Symposium
  on Solid Modeling and Applications, 1995. DOI: [10.1145/218013.218067](https://doi.org/10.1145/218013.218067) — title and DOI only, full text not read (paywalled)
- Fang, S., Brüderlin, B., "Robustness in geometric modeling — tolerance-based methods," in
  *Computational Geometry: Methods, Algorithms and Applications*, Springer LNCS 553, 1991. DOI:
  [10.1007/3-540-54891-2_7](https://doi.org/10.1007/3-540-54891-2_7) — title and DOI only, full text not read (paywalled)
- [`occt.md`](occt.md) §Tolerance model, §Known problems — the OCCT comparison this note builds on
  rather than re-derives
- [ADR-0006](../../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md) — the
  decision this note supplies a comparison baseline for
- [`problems.md`](problems.md) P-02
