# ADR-0010 — IfcX is the reference schema, with IFC4.3 as its vocabulary

**Status:** accepted
**Date:** 2026-10-31
**Deciders:** the maintainer

## Context

The planning round for views, grids and levels (epic #67) works "IFC first" (#66): every native
object maps to an IFC entity, and properties are IFC property sets where IFC defines them. It left
open which schema that mapping is written against (blocking question 5 of
[the plan](../../superpowers/plans/2026-10-29-views-grids-levels-plan.md)).

Today the application writes three things: IfcX (`exchange/ifcx/bim_ifcx.dl`, the IFC5
development format `ifcx_alpha`, as JSON and as the compact `.ifcxb`), and STEP files in IFC4 or
`IFC4X3_ADD2` (`ifc/bim_ifc.dl`). It reads IFC2X3, IFC4 and IFC4X3 (`ifc/bim_ifc_read.dl`).

## Decision

- **IfcX is the reference** for the native data model: object identity, composition by path and
  the way native data travels are designed against IfcX.
- **IFC4.3 (IFC4X3_ADD2, ISO 16739-1:2024) supplies the vocabulary** wherever IfcX does not fix it
  itself: entity names, predefined types and standard property sets are taken from IFC4.3 as far as
  possible.
- STEP export in IFC4 and IFC4X3_ADD2 stays, for exchange with other software.
- Native-only properties use property sets with the prefix `OpenAEC_`, shared with other OpenAEC
  tools (decision of 31 October 2026 on #66).

## Options considered

### IfcX with IFC4.3 vocabulary (chosen)
IfcX is where buildingSMART is taking IFC, and its path composition fits a model that is edited
rather than exported once. IFC4.3 is the current ISO standard, so its vocabulary is the most
durable source of names.

### IFC4.3 as the reference, IfcX as one more export
Most stable today, because IfcX is still alpha; but it designs the native model against a file
format that is being replaced.

### IFC4 ADD2 TC1 as the reference
The widest support in other software, but it lacks infrastructure entities and is not the current
ISO edition.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| The application writes IfcX (`ifcx_alpha`) and STEP IFC4/IFC4X3_ADD2 | `exchange/ifcx/bim_ifcx.dl`, `ifc/bim_ifc.dl` | measured (the repository) |
| IfcX is still a development format | [buildingSMART IFC5 development](https://github.com/buildingSMART/IFC5-development) | claimed |
| IFC4.3 is ISO 16739-1:2024 | [ISO 16739-1:2024](https://www.iso.org/standard/84123.html) | claimed |

## Consequences

**What this makes easier:** the #66 mapping table has one column of entity names; there is no
choice per object.

**What this makes harder:** IfcX is alpha, so its own changes reach the native model; where IfcX
and IFC4.3 disagree, the mapping must say which wins.

**What this commits us to:** following IfcX releases, and keeping the STEP exporters in step with
the mapping table.

**What we would have to change to reverse it:** a new ADR naming another reference; the mapping
table in `docs/domain/` and the IfcX exporter.
