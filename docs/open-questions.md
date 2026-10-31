# Open questions for the maintainer

**Decision question:** which decisions does work in this repository wait on, and where is each
one asked?

Collected on 31 October 2026 from the roadmap, the ADRs, the risk register, the work board and
every open issue. Each question links to where it is asked; the answer belongs there (an issue
comment, an ADR or the plan), and the line here is then struck through or removed. Questions an
implementer can settle alone are not listed.

Ordered by how much work they unblock.

## A. Direction of the repository

1. **ADR-0004 (our own kernel, in DynLex):** accept it, or supersede it with an ADR that records
   what ADR-0007 and ADR-0008 already assume? Its three conditions (R-18 on a clean compiler pin;
   the GPU compute path decided; the `-O` flag demonstrated in the real build) are not met.
   ([ADR-0004](architecture/decisions/0004-build-our-own-kernel-in-dynlex.md) §What must be true)
2. **The B-rep arm:** written ourselves, ported from `cadkernel` (Option D) or linked (Option E)?
   D and E change the licence position (MPL-2.0) and need their own ADR. Must be decided before M1.
3. **GPU compute:** commit to a DynLex `GLCompute` change on the DynLex tracker, or run that work
   on CPU threads for good? (ADR-0004 condition 2, P-28, R-20)
4. **Roadmap phases 4–6:** rewrite the roadmap around the product track now that the build lives
   here, or keep the research phases and the build brief as the formal endpoint?
   ([roadmap](roadmap.md#where-the-plan-stands-31-october-2026))
5. **The MVP slice:** confirm the thin vertical slice (one wall type, one opening, one storey, one
   plan, one section, one parametric component, one IFC export), or replace it with the
   structural plan as the first end-to-end target? ([roadmap](roadmap.md) phase 4)

## B. Phase 1 and the risk register

6. **Unbounded extent only, or streaming too?** Blocks R-14. ([roadmap](roadmap.md) phase 1)
7. **Browser support:** a requirement or not? To be recorded as an ADR. (R-08)
8. **Scripting escape hatch for parametric components:** designed in from the start, or not?
   (R-06; relates to #40, families with parametric references)
9. **The free-modelling / semantic-correctness boundary:** where does it sit? (R-07,
   [`vision/non-goals.md`](vision/non-goals.md))
10. **Licence review of the whole stack:** who does it, and is it a precondition for the next
    release? (R-11)
11. **Remaining phase-1 research** (prior art on Archicad, FreeCAD, Speckle; 3D Tiles; the IFC
    data model at the needed depth; 2D drawing scope R-05; BIM Basis ILS): still wanted, and in
    which order — or superseded by the product track?

## C. Views, grids, levels and georeferencing (epic #67)

The five questions the planning round says block the start:

12. **Where each layer of the drawing properties lives** — project settings, drawing type, view
    (#56, #57). The structural plan design §6 proposes: project = defaults, drawing type = what
    the discipline fixes, view = overrides. Confirm or overrule.
13. **Acceptance of the structural plan** (#58). The design proposes its §3. Confirm or overrule.
14. **Grid pattern syntax** (#59): `4 x 5400`, `4*5400`, `5400 6000 5400`, or all; metres or
    project units; which way new lines go (away from the previous line, or by which end the plus
    sits at)?
15. **KW and FB frame codings** (#68): which standard or convention does each refer to?
16. **IFC4 or IFC4.3** as the reference schema (#66)?

Also confirm the calls the structural plan design made after the builder's reading (§10, seven
items: hybrid `plan.dl` only for planar, linear and grids; no canvas or exporter change; generated
tags only under structural types; reuse of the existing "Structural plan" type; level elevation as
cut datum; pilot house under `--house` in `views/drawings`; below/above from records, cut from the
kernel). Step 0 was merged on these calls.

Further questions on the individual issues:

17. **#56** — Does a detail stay a view with a crop and a scale, or carry its own extra lines?
18. **#57** — How does a user see whether a value is inherited or overridden? Can the view type
    map to IFC presentation entities, or is it native only?
19. **#59** — Should levels get the same plus handle (add storeys with a height pattern)?
20. **#60** — Renumbering from a grid properties panel, a right-click, or both? Are grid names
    unique per direction or per model?
21. **#61** — Handle distance from the bubble in paper millimetres or model metres? Default
    extent per view (2D) or per model (3D)?
22. **#62** — One height for the whole grid or per line? In IFC as placement plus extruded
    representation, or as a property set?
23. **#63** — Is a level's extent a property of the level (model) or of the view? In IFC as a
    native property set or as the storey's representation?
24. **#65** — A list of known CRSs per country in `localisation/`, or free entry? Is the CRS
    picked by hand or derived from latitude/longitude?
25. **#66** — Under which property set name do native-only properties travel?
26. **#4** — The discipline switch (Design, Architecture, Structure, MEP, Fabrication): does the
    view's discipline property of #56 follow it, and is the "show everything" escape wanted?

## D. Building systems (Nino, #22)

27. **#68** — A frame as one IfcWindow with its parts as IfcMember/IfcPlate inside, or one
    IfcWindow with a property set describing the division? Coding per frame or per project?
28. **#69** — Whole system on first click and part on the second, or a modifier key? What does a
    side handle do on a system with a fixed bay width: stretch the bays or add one?
29. **#70** — Edit sketch also for the carrier line in plan, and for a level ceiling? At a
    sloped edge: cut panels, or a rule per system type?
30. **#71** — Does "round panel" mean a circular panel or a panel with rounded corners? How do two
    round mullions meet at a corner (mitre, one through)?
31. **#72** — Does "open hoek" mean a corner without a post (glass-to-glass or a gap), or an
    outline that stops short? With glass-to-glass, which system's panel runs through?

## E. Bugs waiting on the reporter

32. **#43** — Shift+move: which behaviour was missing — the horizontal/vertical constraint, the
    snap to another element's point, or a snap to the grid?
33. **#45** — When exactly does the blue level edge disappear, and should dragging a grip change
    only that storey? (A still image with the steps before it is enough.)
34. **#41, #42, #44, #46, #47, #38, #79** — fixed and merged; each waits on a look at a Windows
    build before it can be closed. Who checks, and on which build?

## F. Release, build and coordination

35. **Version scheme** (#3, #29): adopt `YYYY.W.N` (for example `2026.44.0`) for the next release,
    with the commit shown in development builds?
36. **Installer signing** (#39): make signing a hard condition in the release workflow, and which
    platforms (Windows, Linux) at the next release?
37. **#5 IFCCAD export pilot:** in scope now, and which owner (`views/export` is computer 2)?
38. **Work board** ([WERKBORD](WERKBORD.md#review-of-the-board--31-october-2026)): may the
    pre-module-split claims of 23–27 October be closed, and should the board move to English
    like the rest of the repository?
39. **Leftover branches:** keep or delete `restructure/one-tree` (one commit with build times,
    already reflected in `notes/build-times.md`?) and the probe commit on
    `mod/elements-connection/fastener-components`?
40. **Compiler memory and installers on computer 2** — the two proposed `pc2/*` tasks: still
    wanted, and by whom?

## G. Module work: connections, building systems, structure (#6, #11, #13, #22, #30, #76, #77)

Connections (#6, #77):

41. A connection type: a parameter schema plus a DynLex recipe, or data users edit in the UI?
42. Review of AI-filled connection recipes: which process, and against which reference set (the
    Bouwen met Staal and SCI sources posted on #6 on 30 October)?
43. IFC mapping of a connection: which of IfcElementAssembly, IfcMechanicalFastener, IfcPlate
    and IfcRelConnectsWithRealizingElements?
44. Which member features may a connection refer to (flange, web, centreline, reference side),
    given R-13?
45. Extend the fastener catalogue past M40 (a reference preset needs M42), or keep M40 as limit?
46. PR #78 grew to the whole steel gallery: keep it in one PR or split it? Approve its
    `ui/shell` hooks (input gestures, `OBS_MODEL_VIEW` startup hook) and the shader shipped via
    `build.sh`? Who signs off the native visual, HiDPI and input checks?
47. Whole-scene analytic CSG renderer and rounded B-rep export: wanted as follow-ups?
48. `structural/steel` is owned by Elize, but the steel recipes are written under #6: does the
    module move, or stay with Elize as reviewer?

Building systems (#22, #30, #76):

49. May a pattern-only regeneration API change a system in place within one transaction
    (keeping its id, refusing on drift)? This is the main blocker on #22; it touches `bim/`.
50. InputV1: creation-only, or kept in sync by native edits?
51. Move the curtain geometry from `viewer/bim_scene.dl` to `pattern/facade`? Move the 27 Dutch
    recipe literals to `localisation/nl`?
52. The 183 concept presets (#26): ever live, sourced recipes, and under which provenance rule?
53. #30 acceptance: Shift-add in the sketch pick tool instead of a vertex mode; no promise of LED
    identity until #49 is answered; faces in a later slice; generated panel corners
    inspect-only. Agree?
54. #30/#69: the eight-handle whole-system selection or the contour-vertices slice first?
55. #76: start the large-model measurement, and approve the LOD slice (screen-size proxies,
    culling before evaluation)? Who builds it, now that #82 fixed the zoom rebuild?

Architecture and tests (#11, #13):

56. `exchange/step` below `ifc` in the layer order, or an extension point?
57. Which extension point after the scene point, and who designs the dispatchers for tools,
    API elements and native read/write? Who moves the shape functions out of the viewer?
58. Is compiler patch #27 (libm) part of the official pin?
59. Who owns the 23 known non-passing tests (15 FAILs) from stage 1, and may #11 be closed?
60. Record as ADRs: order-free hubs keyed by element id (#13); product code uses `kernel/api`
    only (#13); detail levels and caches never change IFC or native data (#76, #77)?
61. A central registry of command and property codes, instead of reservations spread over the
    work board and notes?

## Verdict

Provisional. The answers to A1, A4 and A5 decide what this repository's plan *is*; C12–C16
unblock the current planning round; G49 unblocks building systems. Everything else can be answered issue by issue.
