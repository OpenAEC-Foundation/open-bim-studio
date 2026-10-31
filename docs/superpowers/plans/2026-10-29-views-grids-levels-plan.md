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

1. Per view, per view type or per project: which property lives where (#56, #57)?
2. The acceptance of the structural plan (#58).
3. The grid pattern syntax and where the plus handle adds (#59).
4. Which conventions the KW and FB codings refer to (#68).
5. IFC4 or IFC4.3 as the reference schema (#66).

Status on 31 October: the structural plan design
([`../specs/2026-10-30-structural-plan-design.md`](../specs/2026-10-30-structural-plan-design.md) §6)
proposes answers to questions 1 and 2, awaiting the maintainer's confirmation; it does not depend
on question 5. Questions 3 to 5 are open. All five are also listed in
[`../../open-questions.md`](../../open-questions.md), together with the open questions on the
individual issues.

## Verdict

Provisional: start with A1–A3 and B once questions 1–3 are answered; C and D can follow in
parallel; E is Nino's to schedule after #30. Missing evidence before any building starts: the
maintainer's answers to the five questions above.
