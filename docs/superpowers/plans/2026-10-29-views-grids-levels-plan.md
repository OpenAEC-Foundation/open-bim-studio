# Views, grids, levels, georeferencing and building systems: the planning round

**Status:** planning only. Nothing here is being built yet. Each item is a GitHub issue that
carries its open questions; building starts per group once those questions are answered.
Epic: [#67](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/67).

**Decision question:** what must the view, grid, level, georeferencing and building-system
model look like so that a structural plan can be drawn from the model, IFC-based throughout,
before any of it is coded?

**Principle:** IFC first ([#66](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/66)).
Every native object maps to an IFC entity; properties are IFC property sets where IFC defines
them, native property sets only for what IFC lacks. Rules that select or style objects are keyed
by IFC entity type and predefined type, not by native category names.

**Order of attack:** the structural plan first (A3), which needs the one view object (A1), the
layered drawing properties (A2) and the grid work (B).

## A. Views

One kind of object, a **view**, covers plan, section, elevation and detail; the drawing kind
follows from its properties (projection, cut plane and view range, view depth, scale, discipline,
drawing rules). The view is **layered**: a discipline view type (architectural, structural, …)
fixes a set of rules, the view one layer deeper fixes others, and project defaults sit below
both. What each layer fixes is expressed in IFC categories.

| Issue | Item |
|---|---|
| [#56](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/56) | One view object; the drawing kind follows from its properties |
| [#57](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/57) | Layered drawing properties: automated drawing layout (tags, tag sizes, grid appearance) as view properties, keyed by IFC categories |
| [#58](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/58) | Structural plan as the first view type |

Today: `views/common/bim_view.dl` has three kinds (plan, section, model) with their own code
paths and category rules keyed by native categories.

## B. Grids

| Issue | Item |
|---|---|
| [#59](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/59) | Add lines with a plus handle and a spacing pattern (`4 x 5400`); the numbering continues |
| [#60](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/60) | Renumber and rename lines easily |
| [#61](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/61) | The shape handle at a set distance from the bubble end; extent handles |
| [#62](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/62) | Grid lines are IfcGrid/IfcGridAxis with a height: vertical planes in 3D |

The grid's appearance (bubbles, sizes, line pattern) is one of the drawing properties of A2.

## C. Levels

| Issue | Item |
|---|---|
| [#63](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/63) | A non-rectangular, editable extent per level (relates to #45) |
| [#64](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/64) | Levels are IfcBuildingStorey with their elevation relative to the datum (NAP through the CRS) |

## D. Georeferencing

| Issue | Item |
|---|---|
| [#65](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/65) | Latitude and longitude on the project (worldwide), plus a local CRS where one exists (RD/NAP in the Netherlands) as IfcProjectedCRS and IfcMapConversion |
| [#66](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/66) | IFC first: a table in `docs/domain/` of native object → IFC entity → property sets, gaps marked |

Today: `bim/bim_project_settings.dl` has a CRS setting and true north; latitude, longitude and
the map conversion are missing.

## E. Building systems

Owner of `pattern/`: Nino (see `docs/OWNERS.md`).

| Issue | Item |
|---|---|
| [#68](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/68) | A building system as a window frame (*kozijn*) → IfcWindow, with the KW or FB coding as an option |
| [#69](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/69) | Select a whole system with shape handles around it (with #30) |
| [#70](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/70) | Edit sketch of a whole system: change its outline |
| [#71](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/71) | Round mullions and round panels |
| [#72](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/72) | An open corner: two systems meeting without a corner mullion |

## Questions that block the start

Answered by the maintainer on 31 October 2026 ([`open-questions.md`](../../open-questions.md),
round 1, C):

1. **Where each property lives (#56, #57):** project → drawing type → view, each layer falling
   through to the one below. The properties panel shows per value whether it is inherited (grey)
   or overridden (bold, with a reset). The view type is native only, in its own property set.
2. **Acceptance of the structural plan (#58):** the design's §3, plus a comparison with one real
   structural drawing that the maintainer supplies and that stays outside this repository.
3. **Grid pattern syntax (#59):** both `4x5400` (also `4*5400`) and `5400 6000 5400`, in
   millimetres; new lines go in the direction of the end where the plus handle sits. Levels get
   no plus handle; they are added one at a time.
4. **KW and FB codings (#68):** parked. #68 can be built without the coding; the coding is a
   property set to add later.
5. **Reference schema (#66):** IfcX, taking entity names and property sets from IFC4.3 as far as
   possible; native-only property sets carry the prefix `OpenAEC_`
   ([ADR-0010](../../architecture/decisions/0010-ifcx-as-the-reference-schema.md)).

The answers to the per-issue questions (#56–#65, #68–#72) are in the same table and go to each
issue.

## Verdict

A1–A3 and B can be built: questions 1–3 are answered. C and D follow in parallel, with the CRS
chosen from a shortlist by world location and stored in both WGS-84 and the local system (#65).
E is Nino's to schedule after #30; #68 starts without its coding, which is parked.
