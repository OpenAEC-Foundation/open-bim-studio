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

These are schematic rectangular frame envelopes and coplanar glazed bays,
not manufacturer CAD profiles. In particular, a rail count selects the bay
layout and nominal system depth; it does not yet generate offset tracks or
moving sashes. The 50 mm width is a schematic common frame width, not a claim
that every jamb, head and interlock uses that dimension. Timber sizes are
generic modelling presets, not a supplier specification.

Profile cavities, rebates, seals, hardware, drainage, sliding motion and thermal
performance are not modelled. The existing `DetailStatus` property records the
simplification. No manufacturer approval or fabrication suitability is implied.

Validation: `window_recipes` checks recipe application, dimensions, layout
counts and retyping. Full GUI and profile-detail verification remain separate.
