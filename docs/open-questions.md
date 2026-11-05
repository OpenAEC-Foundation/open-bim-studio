# Open questions for the maintainer

**Decision question:** which decisions does work in this repository wait on, and where is each
one asked?

Collected on 31 October 2026 from the roadmap, the ADRs, the risk register, the work board and
every open issue. The maintainer answered the first round the same day and the second on
5 November; the answers are recorded below and carried into the ADRs, the roadmap, the plans and
the risk register. Questions an
implementer can settle alone are not listed.

## Round 3 — still open

1. **Signing through the GitHub organisation** (R2-13): the answer was "the GitHub organisation".
   Does that mean signing in GitHub Actions with keys held as organisation secrets, or GitHub's own
   artifact attestations? And where does the Windows Authenticode certificate come from?
2. **KW and FB codings** (#68, taken up again in R2-16): which source or example defines each
   coding?
3. **InputV1** (#22, #30, taken up again in R2-16): after a native edit, is the system detached,
   kept in sync, or does the application ask?
4. **Whole-scene analytic renderer and rounded B-rep export** (#77, taken up again in R2-16): build
   now, or measure at 1, 100 and 1,000 connections first?
5. **The map tile source** (R2-7): which OpenStreetMap-based provider, or a tile set hosted by
   OpenAEC?

## Round 2 — answered 5 November 2026

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 1 | ADR-0004 | Accept it now; its three conditions become open risks with their own measurement. | [ADR-0004](architecture/decisions/0004-build-our-own-kernel-in-dynlex.md) (accepted; ADR-0003 superseded) |
| 2 | CPU and GPU per operation | Chosen per call by problem size; every GPU operation has a CPU twin. | [ADR-0014](architecture/decisions/0014-choose-cpu-or-gpu-per-call-by-problem-size.md) |
| 3 | The full app in the browser | A long-term goal, not a release requirement; keep the door open (own render layer, OS code only in `platform/`). | [ADR-0015](architecture/decisions/0015-the-browser-is-a-long-term-goal.md) |
| 4 | Designing for streaming | An ADR with the full tile model now, the R-14 spike later. | [ADR-0016](architecture/decisions/0016-tile-model-for-extent-and-streaming.md) (`proposed`) |
| 5 | Bridges to other languages | A separate process over JSON-RPC (stdio); Python first. | [ADR-0017](architecture/decisions/0017-scripting-bridge-is-a-separate-process.md) |
| 6 | Default STEP export | IFC4 by default, IFC4X3_ADD2 as a choice. | [ADR-0010](architecture/decisions/0010-ifcx-as-the-reference-schema.md) |
| 7 | Map and CRS list | An OpenStreetMap-based tile source through a provider with an app licence, everywhere. | #65; round 3, question 5 |
| 8 | Round edges in building systems | Arcs and free curves (NURBS) together. | #71 |
| 9 | Joins as objects | One join object for all element kinds, with a type and properties; IfcRelConnectsPathElements or IfcRelConnectsElements; each module makes its own geometry. | #72 |
| 10 | The real structural drawing | The maintainer compares it themselves, on a build of `main`, at the end. | #58, [views plan](superpowers/plans/2026-10-29-views-grids-levels-plan.md) |
| 11 | Licence of new code | MPL-2.0 for everything, with a root `LICENSE`. | [`LICENSE`](../LICENSE), ADR-0009 |
| 12 | Licence check of the existing stack | REUSE lint in CI plus a one-off list in `docs/notes/licences.md`, by computer 2. | R-11 |
| 13 | Signing certificate and key | "The GitHub organisation" — to be made precise. | #39; round 3, question 1 |
| 14 | Who assembles and publishes the release | The maintainer, together with the installers. | [work board](WERKBORD.md) |
| 15 | The 183 concept presets | They stay concept, visibly marked in the application; a preset becomes real with a source, a working recipe and a review, one family at a time, in the order the MVP needs. | #22 |
| 16 | The three parked questions | Take all three up now. | Round 3, questions 2–4 |

## Round 1 — answered 31 October 2026

R1-n is question n of round 1. "Recorded in" names where the answer now lives.

### A. Direction of the repository

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 1 | Accept ADR-0004 or supersede it? | **Not answered** — the maintainer asked for a fuller explanation with pros and cons. | Round 2, question 1 |
| 2 | The B-rep arm: own, port (D) or link (E)? | The port of `cadkernel` (Option D); MPL-2.0 per file; new non-derived files may carry another licence. | [ADR-0009](architecture/decisions/0009-port-cadkernel-as-the-b-rep-arm.md) |
| 3 | GPU compute in DynLex, or CPU threads for good? | Neither alone: the best combination of CPU and GPU, chosen per operation. | ADR-0004 condition 2 note; round 2, question 2 |
| 4 | Rewrite the roadmap around the product track? | Yes: phases 0–3 stay as closed history; the roadmap continues in epics, modules and releases. | [roadmap](roadmap.md) |
| 5 | The MVP: thin vertical slice, or the structural plan? | The structural plan end to end: grid, levels, columns, beams, walls, floors, tags, sheet, IFC export. | [roadmap](roadmap.md) |

### B. Phase 1 and the risk register

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 6 | Unbounded extent only, or streaming too? | Design both now, so the data model does not rule streaming out. | R-14; round 2, question 4 |
| 7 | Browser support a requirement? | The full app in the browser (WASM/WebGPU) is a goal. | R-08; round 2, question 3 |
| 8 | Scripting escape hatch? | DynLex by default, plus bridges to Python, Java and other languages. | R-06; round 2, question 5 |
| 9 | Free modelling vs semantic correctness? | Free geometry is always allowed; unclassified it exports as IfcBuildingElementProxy and the app asks for a class. | R-07 |
| 10 | Who does the licence check, when? | Continuously: every PR that adds a dependency carries its licence check. | R-11; round 2, question 12 |
| 11 | Remaining phase-1 research? | Only the IFC data model (with #66) and BIM Basis ILS; the rest is dropped. | [roadmap](roadmap.md) phase 1 |

### C. Views, grids, levels and georeferencing (epic #67)

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 12 | Where each layer of drawing properties lives | Confirmed: project → drawing type → view, falling through. | [views plan](superpowers/plans/2026-10-29-views-grids-levels-plan.md) |
| 13 | Acceptance of the structural plan (#58) | Design §3 plus a comparison with one real structural drawing the maintainer supplies (kept private, outside the repository). | views plan |
| 14 | Grid pattern syntax (#59) | Both `4x5400` (also `4*5400`) and `5400 6000 5400`, in mm; the direction follows from the end where the plus sits. | views plan |
| 15 | KW and FB codings (#68) | **Parked.** | Round 2, question 15 |
| 16 | IFC4 or IFC4.3? | IfcX as the reference, taking as much as possible from IFC4.3. | [ADR-0010](architecture/decisions/0010-ifcx-as-the-reference-schema.md) |
| 17 | #56 detail | A view with crop and scale, plus its own 2D detail lines and annotations that exist only in that view. | #56 |
| 18 | #57 inherited or overridden | The properties panel shows the origin per value (grey inherited, bold overridden, with a reset); the view type is native only, in its own property set. | #57 |
| 19 | #59 plus handle for levels | No; levels are added one at a time. | #59 |
| 20 | #60 renumbering | Both a panel for the whole direction and a right-click for one line; names unique per direction. | #60 |
| 21 | #61 handle distance and extent | Paper millimetres; extent 3D by default with a 2D override per view. | #61 |
| 22 | #62 grid height | One height for the grid, overridable per line; in IFC as placement plus the plane's representation. | #62 |
| 23 | #63 level extent | A property of the level with a per-view override, in a native property set; the level's contour must be editable. | #63 |
| 24 | #65 choosing the CRS | From the world location the app offers a shortlist of systems; a built-in map shows where the project sits; coordinates are stored both in WGS-84 and in the local system. | #65; round 2, question 7 |
| 25 | #66 property set name | Prefix `OpenAEC_`, shared with other OpenAEC tools. | ADR-0010 |
| 26 | #4 discipline of a view | A new view takes the discipline chosen at the top and can be changed afterwards; "show all" is added. | #4 |

### D. Building systems (#22)

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 27 | #68 frame to IFC | IfcWindow as an assembly with IfcMember and IfcPlate inside (IfcRelAggregates); coding per project, overridable per frame, in a property set. | #68 |
| 28 | #69 selecting a system | First click selects the system, second click or Tab the part; a side handle adds or removes bays at a fixed bay width. | #69 |
| 29 | #70 edit sketch | The plane in its own plane, and for a ceiling the outline in plan; the carrier line separately; panels are trimmed at a sloped edge. | #70 |
| 30 | #71 round panels | A system's sketch may have round edges; panels and members must then be able to follow them. | #71; round 2, question 8 |
| 31 | #72 open corner | More general: connections between two systems are selectable objects with properties (butt, mitre, join); in a masonry wall the bricks turn the corner. | #72; round 2, question 9 |

### E. Bugs waiting on the reporter

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 32 | #43 Shift+move | Drop it. | #43 |
| 33 | #45 blue level edge | All levels together is right; only the edge disappearing is the bug. | #45 |
| 34 | Windows check of merged fixes | Computer 2 (Windows) tests each merge and closes the issue. | [work board](WERKBORD.md) |

### F. Release, build and coordination

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 35 | Version scheme | `YYYY.W.N` from the next release, set by the release workflow; development builds also show the short commit. | #3, #29 |
| 36 | Installer signing | A hard condition from the next release for Linux (`.asc`) and Windows (Authenticode); an unsigned release fails. | #39; round 2, question 13 |
| 37 | #5 IFCCAD export pilot | After the structural plan, on computer 2. | #5 |
| 38 | Old claims and language of the board | Close the old claims and translate the board to English; claims are made per module in issues, the board keeps only reservations and handovers. | [work board](WERKBORD.md) |
| 39 | Leftover branches | Delete `restructure/one-tree` once its build times are in `docs/notes/build-times.md`; leave the probe commit to its owner. | work board |
| 40 | The two `pc2/*` tasks | Compiler memory stays with computer 2 (it bears on R-18 and ADR-0004); installers go to the maintainer. | work board |

### G. Module work (#6, #11, #13, #22, #30, #76, #77)

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 41 | Connection type | A parameter schema plus a DynLex recipe in code, with a UI to set the parameters. | #6 |
| 42 | Review of AI-filled recipes | Each recipe PR names its source; a structural engineer checks it against the Bouwen met Staal and SCI sources; until then the recipe is "concept". | #6 |
| 43 | IFC mapping of a connection | IfcElementAssembly with IfcPlate and IfcMechanicalFastener inside, linked to the members through IfcRelConnectsWithRealizingElements. | #6 |
| 44 | Member features a connection may use | Only semantic features: flange, web, centreline, reference side and end. | #6 |
| 45 | Fastener catalogue | Extend to M42 and M48, with sources. | #6 |
| 46 | Sign-off after PR #78 | The maintainer signs off visually on a build of `main`; the shell hooks stay, behind a flag or environment variable. | #77 |
| 47 | Whole-scene analytic renderer, rounded B-rep export | **Parked.** | Round 2, question 15 |
| 48 | `structural/steel` | The steel recipes move to `elements/connection` (the intern); the rest of `structural/steel` stays with Elize. | [OWNERS](OWNERS.md) |
| 49 | Regenerating a system in place | Yes, within one transaction, refused on manual changes, with undo. | #22 |
| 50 | InputV1 | **Parked.** | Round 2, question 15 |
| 51 | Curtain geometry and Dutch recipe texts | Both move: the geometry to `pattern/facade`, the texts to `localisation/nl`. | #22 |
| 52 | The 183 concept presets | **Not answered** — needs an explanation. | Round 2, question 10 |
| 53 | #30 acceptance | Agreed. | #30 |
| 54 | Eight handles or contour vertices first | The eight handles first (four corners and four mid-sides), then the vertices. | #30, #69 |
| 55 | Large-model measurement and LOD slice | Measure first (open, first frame, orbit), then the LOD slice, built by Elize (viewer) with Nino. | #76 |
| 56 | `exchange/step` in the layer order | Below `ifc` in the layer order. | `docs/notes/layering.md` |
| 57 | Extension point after the scene point | `tools` first; Elize designs the dispatcher; each module owner moves their own shape functions. | #13 |
| 58 | Compiler patch #27 (libm) | Part of the pin, and offered upstream. | [DynLex upstream note](notes/dynlex-upstream.md) |
| 59 | The 23 known failing tests, #11 | Per module owner, with one issue listing them; close #11 after a look at the pavilion. | #11 |
| 60 | Three decisions from the issues as ADRs | All three. | [ADR-0011](architecture/decisions/0011-hubs-are-order-free-and-keyed-by-element-id.md), [ADR-0012](architecture/decisions/0012-product-code-uses-only-the-kernel-api.md), [ADR-0013](architecture/decisions/0013-detail-levels-and-caches-never-change-model-data.md) |
| 61 | Central code registry | Yes, generated from the `MODULE` manifests by `tools/compose_modules.py`. | #13 |

### H. DynLex upstream

| # | Question | Answer | Recorded in |
|---|---|---|---|
| 62 | Stay on the pin or move to DynLex master? | Stay on the pin until the cache fix, libm, the two Windows patches and `json.dl` are upstream; then move. | [DynLex upstream note](notes/dynlex-upstream.md) |
| 63 | Who offers our patches upstream, in which order? | Computer 2: the cache fix with a regression test, then libm and the Windows patches, then `json.dl`, then the shader patch. | DynLex upstream note |
| 64 | DynLex PR #8 | Split it: compute dispatch and float64 to master; close the kernel part, which now lives here. | DynLex upstream note |
| 65 | `--incremental` | Yes, for `build.sh dev` and the tests, after a measurement on computer 2 of time, memory and new diagnostics. | DynLex upstream note |
| 66 | One compiler pin for Windows CI and Linux | Yes, from one file that `build.sh` and CI both read. | DynLex upstream note |
| 67 | Close DynLex issue #13 | Yes, with a comment naming both commits; update issue #7 with what is done. | DynLex upstream note |

## Verdict

After two rounds the architecture is settled: ADR-0004 is accepted and supersedes ADR-0003, and
ADR-0009 to ADR-0017 record the choices that follow from it. Only ADR-0016, the tile model, is
`proposed`, because it waits on the R-14 spike. What remains open (round 3) is detail: how signing
works through the organisation, the KW/FB sources, InputV1, the analytic renderer and the map
provider.
