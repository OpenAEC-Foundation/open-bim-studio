# Structural floor plans from the model

Status: design note, written after the brainstorm with the maintainer on
2026-10-29 and 2026-10-30, corrected after an independent builder's reading
(§10), and fitted to the planning round of 29 October on computer 1
(`docs/superpowers/plans/2026-10-29-views-grids-levels-plan.md`, epic #67):
this note is the design of issue #58, the structural plan as the first view
type, with the parts of #56 (one view object) and #57 (layered drawing
properties) it needs (§6). The first and later scope of §3 is approved. It is
the first drawing the application must produce that somebody can build from,
and the honest scoping that risk R-05 asks for
(`docs/domain/drawings-from-model.md`) begins with it. The plan follows in
`docs/superpowers/plans/`.

## 1. Intent

A structural engineer models a small house and issues its structural floor
plans (constructieplattegronden) from Open BIM Studio: one plan per storey at
1:50 on a sheet, as a PDF, drawn by the office's rules, with every tag,
dimension and level read from the model so that the plan follows the model
when it changes. Today the application cuts walls and plates, draws linear
elements, grids, section marks, single dimensions and manual tags on screen
and on sheets alike; beam labels, pile numbers, the pile table, the floors and
the storey below exist on screen only, and nothing reads the office's rules
for what a structural plan shows and how. The distance from there to an
issuable plan is annotation, conventions and control, not geometry, and this
note scopes that distance.

## 2. Decided by the maintainer

- The first issuable drawing is the structural floor plan, as Dutch practice
  draws it. The office's drawing rules (summarised in §4) are the standard; the
  source material stays outside this repository, as does every project and
  client name in it.
- The pilot model is a small house: piles, foundation beams and footings,
  load-bearing masonry, a non-bearing partition, hollow-core floors, a few
  steel beams and columns, a roof. It is built synthetically, as the example
  house in the editor is.
- Drawings and views are developed on computer 2 (the maintainer's Windows
  machine) from now on; the five `views/*` modules move to that owner.
- IFC first (#66): every native object maps to an IFC entity, and the rules
  that select or style objects on a drawing are keyed by IFC entity type and
  predefined type, not by native category names. The view is layered (#57): a
  discipline view type fixes a set of rules, the view fixes others, project
  defaults sit below both.

## 3. Scope

**First version** (the deliverable of the plan that follows):

- the plan of each storey at 1:50: grids with their bubbles, a chain dimension
  along each grid direction with the total;
- cut walls and columns hatched by material, with their tags;
- beams as centrelines with profile and top level, dotted or not by the rules;
- floor fields with their type, a span arrow and their top level;
- the level circle (floor thickness over level);
- section marks;
- the sheet with its title block, exported as PDF;
- the same drawing on screen and on paper;
- the acceptance of #58: a new plan with the structural discipline shows
  exactly the structural classes with their pens and hatches; the grid appears
  with bubbles as the drawing properties say; a column cut at the view's cut
  height shows its section and tag and a beam above the cut shows dashed with
  its tag; the view switched to the architectural discipline and back keeps
  its other properties.

**Later**, not in this plan: the pile plan with its pile table, the legend
tables (loads and assumptions, materials, anchorage lengths), details at 1:20,
a 3D picture on the sheet, revision clouds with a revision list, DWG output,
architectural plans, moving a generated tag by hand (and so per-view
overrides), collision avoidance between tags.

**Anti-goals**, what makes this a failure even if it draws:

- annotation that goes stale silently when the model changes;
- annotation that exists on screen but not on the sheet, or the reverse;
- a second geometry pipeline for the cut next to the kernel's;
- hand-placed text for anything the model knows.

## 4. The drawing rules the plan follows

The rules below are the office's; they are the specification the builder
implements, and the defaults in brackets are this note's calls.

What is drawn: only what bears or is loaded — piles, foundations, load-bearing
walls and columns, beams, lintels, bracing, the structural floor. Not drawn:
finish floors, insulation, light partitions, stairs. Non-bearing masonry is
invisible on the plan.

The cut: the plane lies 50 mm above the top of the storey's structural floor.
One looks down through the floor at what lies under it, to the top of the
storey below; what lies above the cut up to the next storey is drawn dashed.

| Element (IFC) | Rule |
|---|---|
| Column (IfcColumn) | hatched by material when cut; tag at the top right unless there is no room |
| Load-bearing wall, cut (IfcWall, LoadBearing) | hatched by material; concrete walls below and above the floor each have their own hatch |
| Foundation beam (IfcFooting.STRIP_FOOTING) | tag above or to the left |
| Steel beam (IfcBeam) | centreline at 1:100 and 1:50, dashed web at 1:20; tag "HEA300 bk. -250" (profile, top level); a beam above the floor says so in its tag |
| Beam under an in-situ concrete floor | concrete beam dotted, steel beam not dotted |
| Beam under a system floor (hollow-core, rib-cassette) | not dotted |
| Floor field (IfcSlab.FLOOR) | type and span arrow, top level ("KPV 200 bk. -70") |
| Level circle | floor thickness over the level ("200 / +2800") |
| Lintel (IfcBeam.LINTEL) | tag with its profile |
| Vertical wind bracing (IfcMember.BRACE) | dashed 0.35 mm with the text "WVB" and its section |
| Pile (IfcPile) | outline with a cross (as today); numbered on the pile plan (later) |
| Footing (IfcFooting.PAD_FOOTING, PILE_CAP) | outline below the cut, tag |
| Existing work | hatch without outlines; demolished work dashed and unhatched |
| Grid (IfcGrid) | bubbles at both ends unless the head mask says otherwise; chain dimensions per direction with the total |

Pens [defaults, by class and state, in millimetres on paper; the builder may
tune them against the examples]: cut outline 0.50, cut hatch 0.13, projected
below 0.25, dashed above 0.25 (dash 3/1 mm), dotted beam 0.25 (dot 1/1 mm),
grid 0.18 (dash-dot), dimension 0.13 with 2.5 mm text, tag text 2.5 mm, level
circle 0.25. Text follows the drawing standard: under NEN 47 the abbreviations
are Dutch ("bk." for top level, decimal comma); under the other standards
English.

## 5. How it is made

These are this note's calls, within the module split
(`2026-10-28-module-split-design.md`) and the kernel seam.

**The drawing moves down, it is not duplicated.** One set of drawing
functions exists today, in `ui/panels/bim_plan_panel.dl` (layer 6), taking the
editor record; the plan panel calls them for the screen and the sheet calls
them for its viewports through the same `bim canvas record`. The work is to
take the editor record off those functions and move them to the modules that
own the elements (extension point, below) and to `views/drawings`, so that the
screen-only parts (beam labels, pile numbers, floors, the storey below) reach
the sheet because there is nothing else to call. What this plan does not move
(openings, stairs, spaces, sketches, components, reinforcement, imported
drawings) stays in `ui/panels` and is called by both surfaces as today; the
structural plan hides most of it anyway. The other modules move their drawing
when their owners do.

**Pens in today's canvas.** The canvas keeps triangle batches and texts; it
has no pen widths and one text size, and the exporters write filled triangles.
A pen table (§4) is therefore applied when the plan items are recorded: a line
becomes quads of the pen's width at the recording's scale, a dash pattern
becomes its segments. On a sheet the recording is at paper scale, as sheet
recordings are. On screen the plan is recorded at the current screen scale
with each pen converted to pixels and clamped to one pixel, and re-recorded
when the zoom changes. `viewer/bim_canvas.dl` and `views/export` are not
changed by this plan; their golden tests stand.

**Each module draws its own elements.** `views/drawings` (layer 2) cannot
import the element modules (layer 3), so the plan gets an extension point like
the scene's: a `plan` entry in the composer's point table and a `plan.dl` in a
module with a function that appends its plan items for one view to a list; the
composer writes the dispatcher into `generated/compose.dl`, which the drawings
module calls as the scene does. In this plan `elements/planar` (walls, floors,
footings), `elements/linear` (columns, beams, piles, lintels, braces) and
`pattern/grids` (grid lines and bubbles) get a `plan.dl`, written on computer 2
as additive files, each a pull request its owner reviews. A plan item is one
of a small set of records defined in `views/drawings`: a cut face with a
material, a projected or dashed outline, a centreline with a style, a tag
(text, anchor, placement rule, element id), a span arrow, a level circle, a
dimension request along a grid direction; every item names the IFC entity
type and predefined type of its element, which is what the view's rules key
on. The drawings module lays the items out, places the tags by their rules,
builds the chain dimensions from the grid lines, and records everything with
the pen table.

**Cut from the kernel, projected from the records.** The cut state uses the
evaluation's bodies through `kernel/api/kernel.dl`, as the wall cut does
today. What lies below or above the cut is drawn from the element's own
record — a beam's axis and width, a slab's outline, a pile's point and
diameter, a footing's outline — as linear elements are drawn today, not from
meshes or kernel wire sets: the records are exact and need no hidden-line
removal, which the kernel does not offer.

**Three states per element: cut, below, above.** The view gains a view range
(the properties #56 names): the cut height above the level (the structural
plan's default 0.05 m, the architectural plan's 1.2 m as today), the depth
below (default: to the elevation of the level below, else without limit) and
the height above (default: to the elevation of the level above, else without
limit). The level's elevation is the datum: the pilot sets its floor tops at
the level, and a slab that sits elsewhere is still cut by the level's plane.
The state decides the pen and the hatch; the module's `plan.dl` reports the
state's drawing by the rules of §4.

**The layered properties live where they live today.** Project defaults in
the project settings; the view type in the existing `bim drawing type record`
(the library's "Structural", "Structural plan" and "Pile plan" types, their
inheritance and their annotation rules), which gains the discipline, the view
range defaults and the pen set; the view's own overrides in the `bim view
definition record`, which already carries `automatic` (follow the type) and
its own rules. The category rules move from native categories to IFC entity
types and predefined types as their key (#57's consequence), with the
load-bearing property (`Pset_WallCommon.LoadBearing` and its kin) as one more
key, so a reader of the file can tell from the IFC classes alone what a view
shows. The plan, the section and the model tab stay separate kinds in this
plan; #56's one view object is the next step and nothing here stands in its
way, since every property added is a property of a view.

**Derived annotation is not stored.** Tags, chain dimensions, span arrows and
level circles are generated per view on every evaluation and never saved, as
the existing "beam labels" rule already is. The tag store and the tag tool
stay for manual tags (the architectural opening tags among them), and so does
the manual dimension store. The screen-only `draw bim annotations in plan`
retires into the items. `ensure bim drawing types` updates the library of
existing models; the new rules default to on for the structural types and to
off elsewhere, so no other drawing changes. The first version places tags by
the placement rule and a fixed offset; moving a tag by hand, its per-view
override and collision avoidance are later (§3), so the native format does not
change in this plan.

**The model gains what the rules name**, in IFC terms, in small changes to the
element modules, each a pull request reviewed by their owner: linear roles for
the lintel (IfcBeam.LINTEL) and the brace (IfcMember.BRACE) next to column,
beam and pile; the foundation beam (IfcFooting.STRIP_FOOTING) as a linear
role and the footing (IfcFooting.PAD_FOOTING, PILE_CAP) as a plate role next
to floor and roof; a span direction and a floor system (in situ, hollow-core,
composite) on the slab; the load-bearing property on wall types (masonry and
concrete true by default, timber-frame false), written to IFC as
`Pset_WallCommon.LoadBearing`. Strength classes wait for the legend tables.

**The pilot house** is a generator in `views/drawings/bim_demo_house.dl`,
built with the model-level constructors (no editor import), as the pavilion is
in `ui/shell`; the application loads it with a new `--house` argument. The
example house behind `--example`, which twenty-two tests reference, stays as
it is. Each step of the plan ends in a test whose expected text lists the
plan's items (counts, tag texts, pen widths) for the house; the sheet's PDF is
the maintainer's acceptance: "issuable" is a judgement a person makes with the
examples beside it.

**The drawings module becomes model-level first.** Today
`views/drawings/bim_drawing_rules.dl` imports the editor (it holds the Drawing
Rules window and its commands) and `bim_drawing.dl` imports the planar
evaluator (a baselined edge). Before the items arrive, the window moves to
`ui/panels` and the wall cut becomes the planar module's plan item, so that
every test of the drawings module compiles in a model-level closure (about
half a minute) instead of the editor's (four minutes).

## 6. Fit with the planning round of 29 October

| Issue | This note |
|---|---|
| #58 structural plan as the first view type | §3 (content and acceptance), §4 (rules), §5, §7 (sequence) |
| #57 layered drawing properties, IFC-keyed | §5, "the layered properties": project settings → drawing type → view; rules keyed by IFC entity and predefined type; tag and grid appearance are properties of the type |
| #56 one view object | not built here; the view range and the discipline are added as view properties, so the merger of plan, section and model into one object finds them in place |
| #66 IFC first | the model additions and the rule keys of §5 are IFC entities and property sets |
| #59–#62 grids | read only: the plan draws the grids it finds; grid editing stays with the owner of `pattern/` |
| #63–#65 levels and georeferencing | the level's elevation is this plan's datum; nothing else is touched |

Of the five questions the planning round says block the start, this note
proposes answers to the first two, as calls the maintainer can overrule:
(1) a property lives in the project settings when it is a default, in the
drawing type when the discipline fixes it, in the view when the view
overrides it, each layer falling through to the next as `automatic` does
today; (2) the acceptance of the structural plan is §3. The third (grid
pattern syntax) and the fourth (the KW and FB codings) are not this plan's;
the fifth (IFC4 or IFC4.3) does not touch it, since every entity and
predefined type named above exists in both. The views that this note's plan
builds are built on computer 2, as decided; the plan of 29 October keeps
grids, levels, georeferencing and building systems with their owners.

## 7. Sequence, coarse

0. `views/drawings` sheds its editor and element imports (rules window to
   `ui/panels`, the wall cut to `elements/planar`); its tests go model-level.
1. The model additions of §5 (roles, span, floor system, load-bearing).
2. The `plan` extension point in the composer, the item records and the pen
   table; the panel's drawing functions move into `plan.dl` files and the
   drawings module, the editor record comes off them; screen and sheet record
   the same items.
3. The view range, the three states and the IFC-keyed rules on the drawing
   type.
4. The structural items by the rules: hatch states, centrelines and tags,
   floor fields with span arrows, level circles, chain dimensions, tag
   placement; the load-bearing rule.
5. The pilot house, its structural plans and the sheet; the maintainer's look.

Step 1 can run beside 0 and 2 on another machine; 3 and 4 can interleave.

## 8. Risks and what is left open

- Step 2 touches functions the plan panel, the sheet and other modules' tests
  call; their outputs must stay byte-identical until step 4 changes them on
  purpose.
- Tag collisions on a dense plan are real and deferred; the first version
  accepts overlaps.
- The span arrow needs the slab's direction, which the model does not hold; a
  slab without one draws no arrow rather than a wrong one.
- Existing-work hatching without outlines needs a hatch the materials module
  does not have; halftone stands in until it does.
- Screen recording per zoom change costs a re-record; if that is felt, the
  panel keeps a small set of recordings by zoom band.
- Re-keying the category rules by IFC class changes how existing models'
  views are read; the migration maps each native category to its class once.

## 9. Left to the builder

Exact pen widths and text sizes within §4's defaults; the arrow and bubble
shapes; tag offsets; the names of the item records and functions; the order of
the plan items on the canvas; how the panel caches recordings.

## 10. Calls made after the builder's reading

The builder's reading corrected §1 and §5 (one set of drawing functions, not
two pipelines; a canvas without pens; a drawings module that imports the
editor; the structural drawing types and `--example` that already exist;
model-wide tag and dimension stores). These calls settled the questions it
raised, and the maintainer can overrule any of them:

1. Hybrid, not a multi-owner refactor: only planar, linear and grids get a
   `plan.dl` in this plan; the rest stays in `ui/panels` for now.
2. No change to the canvas or the exporters: pens are applied when recording,
   on screen at screen scale with a one-pixel floor.
3. Generated tags only under the structural drawing types' rules; the tag tool
   and store stay; no per-view overrides and no format change in this plan.
4. The existing "Structural plan" type is reused and gains the load-bearing
   rule; its rules are re-keyed by IFC class.
5. The level's elevation is the cut datum; the view range defaults to the
   levels below and above.
6. The pilot house stands beside the example house, under `--house`, as
   product code in `views/drawings`.
7. Below and above are drawn from the records, the cut from the kernel.
