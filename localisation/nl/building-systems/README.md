# Dutch building-system authoring catalogue

**Decision question:** which reusable assembly families and product facts should the generic
generator support for Dutch building practice, without confusing an example with an approved
construction system?

Status: **authoring data, version 0.2.0; not exposed in the live placement interface**. The
[catalogue](catalogue.json) contains 183 conceptual presets in 43 families, 83 substitution
interface templates and 13 primary-source references. The [complete index](INDEX.md) lists
every family, preset, layer role, boundary and component interface. The live application's
43 legacy recipe indices are unchanged. See the [generator contract](../../../docs/domain/building-system-generator.md).

## Scope and use

| Family | Included presets | Main rules and missing project inputs |
|---|---|---|
| HSB | 140/184/235 mm frame zones, 600/610 centres; interior variant | Frame/insulation share a zone; plywood, gypsum, membranes and service zone; opening subsystems; prefab maximum; confirm member sizing, moisture design, board format and fixing schedule |
| Metal-stud partitions | 75/100 frame zones; one/two 12.5 mm linings per side | Board-edge support, displaced seams and head deflection; choose a complete manufacturer's wall system |
| Suspended ceilings | T24 600 square and 1200×600, T15 and concealed square | Main/cross members, hangers, borders and compatible substitutions; panel edge, weight, support distances and access remain product inputs |
| Frames | Timber/aluminium/PVC × fixed, single/double opening, transom, door+sidelight | Nested leaves/panels, head/jamb/sill water interfaces, profile orientation, seals, sweep and hardware; generic layouts have no certified performance |
| Brick masonry | Waal-format half, quarter and stack bond | Brick-plus-joint pitch, returns, openings, movement joints; choose product, supports, ties and lintels |
| Sand-lime | Supplier-defined glued elements | Unit size and joint deliberately unresolved; lifting, bearings and cut limitations required |
| Tiling | 300/600 modules, no/straight/curved border, running bond | Actual calibre, direction, joint, border offset, cut edges and remnants; 300 mm manufacturing size deliberately unresolved |
| Cladding | Horizontal/vertical timber, HPL, standing-seam zinc | Ventilated subframe, fixings, expansion, grain and stock; supplier working widths and seam geometry required |
| Timber cassettes | Floor and roof | Framing/deck/insulation/lining, prefab joints, bearings and trimmed openings; structural/membrane design required |
| Hollow-core | 320 mm depth, nominal 1200 width example | Supplier-controlled infills, strands/webs, bearings, engineered openings; no arbitrary site tile-style cutting |

Version 0.2 adds cavity walls, mass timber, precast/block/insulated-formwork walls, sandwich
panels, light steel framing, curtain facades, demountable partitions and external insulation;
overlapping roof coverings, standing-seam and flat roofs, vegetated/water-retention roofs;
raised floors, beam-and-block, precast and composite floors, screeds, timber/resilient/modular
finishes, paving and decking; boarded, baffle/raft/linear and tensioned ceilings; solar mounting,
shading, green facades, guarding, modular interiors and service carriers. These are construction
and interface templates. Electrical/fluid calculations, engineered load capacity and product
approval remain with their disciplines and supplied evidence.

The set is extensible rather than claimed exhaustive. Nested families and typed substitutions
represent new combinations without creating one solver per material or every permutation.
An unspecified product is represented by required inputs and null dimensions, not invented
technical values. A child must satisfy its parent's ports, supports and exposure constraints.
Layer suppression is stored under family `operations`, never as an imaginary replacement product.

Every `concept` recipe has an empty `performance_claims` array and `manufacturer_system: false`.
The dimensions are editable authoring examples. In particular 38 mm timber width, 3300 mm
prefab maximum, 18 mm plywood, 45 mm service zone and the 600/610 alternatives are not asserted
to be national requirements or sufficient structural specifications. Source facts apply only
to the product and parameter described in their `scope`. A sourced module dimension does not
validate an entire recipe.

## Data contract

The JSON uses millimetres. IDs and rule keys are English; `label_nl` is display text. Family
records describe layer functions, opening/boundary roles, substitution roles, stock kinds,
required rules and unresolved inputs. A recipe references a family and supplies parameter
overlays. These records are declarative authoring specifications, not executable expressions.
`pattern/common/bim_system_catalogue.dl` provides bounded read-only native metadata loading,
stable-ID lookup and an explicit capability check. It owns its parsed JSON until released;
lookup results borrow that storage. It does not create model elements or validate full
product assemblies. The live placement interface is not connected to this reader yet.
The future importer must reject unknown keys/rules or unavailable capabilities and show the
missing input. It must never silently approximate an unsupported concealed ceiling as T24.

Family layer thicknesses are example defaults. Recipe depth/material/count parameters must be
resolved before geometry: HSB `stud_depth_mm` sets frame and insulation zone depths;
`insulation_depth_mm` must agree with its selected zone policy. Partition `profile_depth_mm`
sets frame depth and insulation zone; `lining_count_per_side` creates separately keyed lining
layers. Window `frame_material` overrides the generic family material; profile dimensions
remain unresolved. T15/concealed variants require their own product profile/edge definitions;
the family's T24 example grid dimensions cannot be inherited as verified product geometry.
The internal HSB variant removes weather/air-control exterior defaults and adds the second
lining explicitly; it is not a moisture-designed exterior wall.

Layer order is schematic until an actual project variant defines datum, outward direction,
offsets and moisture strategy. `shares_zone_with` means complementary coverage (insulation
between framing), not two full solids occupying one volume. `null` means required product or
project input; it is never zero. Footprints and overall dimensions come from placed domains,
not catalogue-wide guessed room dimensions.

Library updates are immutable versions. Keep existing versions available to placed models.
Stable catalogue IDs are independent of legacy integer indices; a future migration table
must be append-only, reviewed and tested against saved fixtures. Product packs can replace
concept inputs only with explicit product IDs, provenance and applicability rules.

## Evidence register

The catalogue stores retrieval date, URL, locator and scope for every source. Useful checks:

- [Mosa modularity](https://www.mosa.com/application/files/8115/6751/1853/Lastenboek-toelichting-MOSA.pdf)
  separates module and manufacturing dimensions; the 600/597 example underlies the tile
  preset. Verify actual calibre rather than deriving every tile from nominal dimensions.
- [Mosa processing advice](https://www.mosa.com/application/files/1815/6041/7468/Mosa-verwerkingsadvies-algemeen.pdf)
  identifies surface direction and cutting considerations. It is dated 2018; obtain current
  product advice before using its processing recommendations for a project.
- [Rockfon's T24 Impact installation guide](https://www.rockfon.nl/siteassets/commerce/nl/grids/documents/documentation/installatierichtlijnen/nl-installation-guide-rockfon-system-t24-a-impact-2a-3a-22_d_02_2024.pdf)
  demonstrates separate main runners, cross tees, hangers, wall details and panel edges. Its
  impact classification is not attached to our generic ceiling variants.
- [Gyproc's April 2024 handbook](https://www.gyproc.nl/sites/mac3.gyproc.nl/files/2024-05/Gyproc%20Handboek%20Verwerking%20-%20april%202024.pdf)
  relates stud spacing and system composition to permitted wall configurations. Do not reuse
  a metal-stud table to certify timber framing.
- [Knauf's board range](https://knauf.com/nl-NL/p/producten/platen-30337/gipsplaat-26684?division%5B0%5D=Knauf+Gypsum&front-edge-type%5B0%5D=AK)
  provides examples of board width/thickness and edge types; product-specific processing remains necessary.
- [Wienerberger's glazed-brick advice](https://www.wienerberger.nl/content/dam/wienerberger/netherlands/marketing/documents-magazines/instructions-guidelines/facade/NL_MKT_DOC_TEC_TER_WB_verwerkingsadvies_Glazuurbakstenen-serie.pdf)
  gives approximate waal dimensions and an indicative joint example for that range. Our 50+10
  example uses 60 mm course pitch. The legacy application uses 62.5 mm: do not silently change
  saved models; investigate its intended joint assumptions separately.
- [KVT 11.7.2.2](https://www.kvt-online.nl/het-eindproduct/11-kozijnaansluitingen/11.7-dichtingen--lucht-en-water/11.7.2-waterdichting/11.7.2.2-aanbrengen-en-uitvoering-van-de-waterdichtingen/)
  provides distinct water-sealing conditions at frame interfaces. No proprietary detail
  drawing is reproduced here.
- [VBI PDB05.014](https://vbi.nl/wp-content/uploads/PDB05-014-Kanaalplaatvloer_320.pdf)
  distinguishes the nominal plank width and restricted product infills. Structural capacities,
  maximum spans and fire ratings are intentionally not imported into a generic template.
- [EGGER's OSB brochure](https://www.egger.com/get_download/8f2b4ce1-5e82-49b4-a000-aa8d536f6e13/Brochure_EGGER_OSB3JASTOP_en.pdf)
  illustrates explicit board edge-gap requirements for its product. This is a plywood/OSB
  interface design consideration, not evidence for a Dutch approved wall assembly.

Additional family evidence is scoped in the catalogue: [RHEINZINK seam guidance](https://www.rheinzink.nl/producten/daksystemen/felsdak/),
[Rockpanel installation guidance](https://www.rockpanel.com/nl/syssiteassets/documentation/nl/brochures/rockpanel_instructiegids.pdf),
[Wienerberger working-size guidance](https://www.wienerberger.nl/informatie/dak/omgaan-met-een-maatafwijking.html)
and [Sto system families](https://www.sto.nl/s/c/a0K2p00001NaTWwEAN/products-systems).
These sources support interface/working-size requirements, not approval of the generic recipes.

## Validation and next delivery

Run `python3 tools/validate_building_system_catalogue.py`. It checks identifiers, family/source
references, required fields, finite positive dimensions, known rule/capability names,
layer-zone and substitution-interface references, component port/usage consistency, tiled module arithmetic and brick pitch arithmetic. It does not
validate structural or building-physics design. No network access is required to validate.

Before activating a preset, implement and test every declared capability, resolve every
required input, resolve layer parameter bindings, and validate component/connection interfaces.
Complete manufacturer packs additionally need their processing details and performance
applicability, including what an override invalidates. The present verdict is that the catalogue
is a reusable content foundation, with explicit gaps; it is not yet a construction-ready or
runtime-imported product library.
