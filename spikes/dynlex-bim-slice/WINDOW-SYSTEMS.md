# Window and sliding-door recipes

The Building System type library includes generic timber windows and doors,
plus schematic layouts named for Reynaers sliding systems. Existing recipe
indices are retained; new recipes occupy indices 33–42. They appear through
both the existing type selector and the `systemtypes` automation API.

| Recipe | Nominal frame envelope, mm | Layout |
|---|---:|---|
| Fixed timber | 90 × 139 | One glazed bay |
| Double casement timber | 90 × 139 | Two glazed bays |
| Timber with transom | 90 × 139 | Two glazed rows |
| Timber sliding door | 67 × 174 | Two glazed bays |
| Reynaers ConceptPatio 130 | 50 × 130 / 50 × 210 | Two / three bays |
| Reynaers MasterPatio | 50 × 180 / 50 × 283 | Two / three bays |
| Reynaers SlimPatio 68 | 34 × 120 / 34 × 176 | Two / three bays |

The recipes fit their bay and row counts to the placed system's dimensions.
Manufacturer and source URL are stored as `OpenBIM_Window` properties and reset
when another recipe is applied.

## Source and modelling limits

Frame depths for ConceptPatio 130 and MasterPatio are taken from the official
[Reynaers contemporary collection, January 2026](https://www.reynaersathome.co.uk/wp-content/uploads/2026/01/REY20243-Contemporary-Brochure_Print_AW-Edited-JAN-26.pdf).
SlimPatio 68 frame depths and the 34 mm visible vent dimension are taken from
the official [Reynaers product overview](https://www.reynaers.com.au/sites/default/files/public/2023-01/reynaers-aluminium-product-overview-en.pdf).

The generator now derives rectangular sash stiles, sash rails and inset glazing
for casement, tilt-turn and door recipes. Sliding recipes derive a sash per
bay at a separate track depth, with a guide at sill and head for each track.
All parts belong to the editable Building System; they follow its hosted
opening, remain derived after saving/loading, and disappear with an unpinned
cell. Plan edges and 3D meshes use those same derived parts.

These are schematic rectangular profiles, not manufacturer CAD sections.
Track spacing and sash dimensions are generic modelling choices within the
nominal frame envelope. The 50 mm frame width is a schematic common width,
not a claim that every jamb, head and interlock uses that dimension. Timber
sizes are generic presets. Curved, contoured and horizontal systems retain
their existing infill; cells too small for a sash retain their plain infill.

Profile cavities, rebates, seals, hardware, drainage, opening/sliding motion and thermal
performance are not modelled. The existing `DetailStatus` property records the
simplification. No manufacturer approval or fabrication suitability is implied.

Validation: `window_recipes` checks recipe application, dimensions, layout
counts and retyping; `window_construction` checks derived sash/glass dimensions,
track separation, ownership, persistence and unpinning. `system_profiles`
checks that unrelated building systems retain their original member geometry.
Full GUI and manufacturer profile-detail verification remain separate.

## Create from a wall opening

Select a window/door opening and click **Building System (click)** in Props.
**Create window system** adds a hosted timber system with a 10 mm installation
joint and selects it. Choose its recipe in the existing type selector.
Selecting that opening again shows **Select window system**; clicking it selects
the same system without adding a duplicate or changing its recipe.

Creation is one undoable action. Curved-wall or unsupported openings are refused
and rolled back. Automation uses the same action: `select` the opening, inspect
`properties`, then invoke `set_property` for **12612**, without a text value.

For this new action, the installation joint is measured to the **outer frame
faces**. Setting 1700002 remembers that clear gap in millimetres; assigning a
new window recipe recalculates the centre-line hosting inset using its frame
width. Previously authored models without this setting retain their explicit
hosting inset. Older models can therefore keep their established placement.

The type menu has its own bounded scroll position. It opens around the current
type and scrolls through the complete library independently of property rows.
