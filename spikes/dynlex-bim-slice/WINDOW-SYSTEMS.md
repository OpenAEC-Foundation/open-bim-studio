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

Profile cavities, supplier-specific rebates, hardware, drainage, opening/sliding motion and thermal
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

`type_menu` passed six range/navigation checks. The manual
`tools/type_menu_probe.dl` passed four checks against the production properties
renderer, including actual first/last row hit targets, and was inspected
visually. Build/run it with `build.sh probe type_menu_probe` and
`build.sh run-probe type_menu_probe` on a Vulkan display. Its compile used
about 3.84 GiB locally; it is smaller in memory but still takes about ten minutes
with the current compiler.

The full app on `73f9552` passed hosted creation/selection, placement property
edits and undo/redo, and includes the type-menu scroll fix. Its local dev build
completed in 15m04s with a peak RSS of 9,415,700 KiB after safely saving and
closing the previous app.

## Hosted placement editing

The full-system properties now expose **Host opening (click)**,
**Installation gap** and **Depth in wall**. The host action selects the
associated opening so its width, height and sill can be edited there.
Distances follow the project length unit and are stored in whole millimetres.
Positive depth follows the right side of the wall direction; negative depth
moves to the opposite side, including on rotated walls.

Changing the installation gap preserves bay/row counts. Explicitly moved grid
lines retain their offsets. An edit is refused if a cell can no longer contain
its frame and operable sash. Gap changes on sketched/contoured frames are not
supported; their existing outline is preserved. Depth changes translate the
whole hosted system. Unhosted systems reject these opening placement edits.

Placement edits use one transaction. Re-entering the same value creates no undo
step; invalid input leaves both the revision and redo history intact.
`window_placement` tests the model operations and native persistence;
`window_placement_editor` exercises the exact action helpers used by Props/MCP.

A custom outer-frame profile must agree with **Frame width** before its gap can
be edited. Inconsistent widths are refused so the displayed gap cannot silently
place a wider profile through the wall. Profile cavities and supplier-specific
rebates remain outside this schematic modelling layer.

Validation for the added placement controls: 16 model checks and 12 editor-action
checks passed, including history preservation, project units and refusals.
The 43-type gallery, construction and profile regressions passed as well.
The full `73f9552` app also passed the placement property dispatcher, no-op and
invalid-input handling, opening/system selection, frame-width refit and refusal,
and undo/redo. The saved 1357 project was reopened in that build.

## Glazing detail

Window presets 3–5 and 21–42 derive glazing beads and dark rubber seals on
both sides of each glass pane. Four butt-jointed members form each ring;
the bead leaves a 4 mm seal reveal. Their depth follows the actual available
frame/sash depth and stays inside its nominal envelope. Profiles too thin
for this detail retain plain glass, as do tiny cells and opaque panel types.
Operable windows retain the same sash and glazing dimensions and sliding
track offsets. All detail keeps the editable system identity and is grouped
by material in the existing scene. No extra persistent objects are added.

Existing window grids receive this detail without retyping, moving grid
lines or changing their opening linkage. These generic sections are not
manufacturer fabrication profiles. `window_glazing` checks rotated placement,
glass clearance, frame envelope, ownership, persistence and safe fallbacks.

In a plan, the schematic three-line window symbol is omitted when its hosted
system is visible. The view uses the actual frame and glazing geometry.
Unfilled openings retain the placeholder; door swing symbols are retained.

Plan overviews skip generating the tiny glazing rings, as well as omitting
them from the all-pairs end-join calculation. Their 4 mm seal reveal must occupy at least one screen pixel;
zooming in resolves the detail automatically. Main frame/sash members and
glass remain visible at every scale. This drawing LOD does not alter the
stored system, its complete 3D geometry or the exported model.
