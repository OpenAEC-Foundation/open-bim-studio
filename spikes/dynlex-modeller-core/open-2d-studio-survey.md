# Open 2D Studio — what the modeller core takes from it

**Question.** What content and way of working does Open 2D Studio define, so that the
modeller core (parts C, D and G of this spike's README) can adopt it exactly?

Open 2D Studio is a deprecated TypeScript project of the maintainer. It is used here as
the reference for content and workflow, not as code. Paths are relative to its core
repository, `open-2d-studio-main`, or to `open-2D-studio-AEC-extension` where marked
(AEC). All lengths are in millimetres, as in the source. Everything below was read
from the source; nothing was measured.

## Wall types

`src/state/slices/parametricSlice.ts:699-721` and
`src/services/wallSystem/groupedWallDefaults.ts`.

**Single-material types** (id, name, thickness, material):

| Material | Types |
|---|---|
| Concrete | beton-150, beton-200, beton-250, beton-300 (`Beton`) |
| Calcium silicate | kzst-100, kzst-150, kzst-214 (`Kalkzandsteen`) |
| Masonry | metselwerk-100, metselwerk-210 (`Metselwerk`) |
| Timber | hsb-120, hsb-170 (`Hout`) |
| Steel | staal-10 (`Staal`) |
| Insulation | isolatie-184 (`Isolatie`) |
| Grouped-wall components | gevelbekleding-20 (timber), osb-12 (timber), hsb-stijl-140 (timber), gipsplaat-12 (12.5, generic), metalstud-75 (steel) |

**Grouped (layered) types.** Layers are listed exterior first as
`name thickness + gap after it`. A layer marked "not drawn" only takes space.

- **Spouwmuur 360mm** (360, aligned on the exterior):
  - metselwerk 100 + 40 gap;
  - isolatie PIR 100, not drawn;
  - kalkzandsteen 120.
- **Spouwmuur 300mm** (300, aligned on the exterior):
  - metselwerk 100 + 30 gap;
  - isolatie 50, not drawn;
  - kalkzandsteen 120.
- **HSB Buitenwand** (204.5, aligned on the exterior):
  - gevelbekleding 20 + 20 gap;
  - OSB 12;
  - HSB stijl+isolatie 140;
  - dampremmer 0, not drawn;
  - gipsplaat 12.5.
- **Metal Stud Binnenwand** (100, centred): gipsplaat 12.5, metal stud CW75+isolatie 75,
  gipsplaat 12.5.
- **Massieve Binnenwand** (100, centred): kalkzandsteen 100.

**Wall systems.** Wall systems with studs (`src/services/wallSystem/wallSystemDefaults.ts`)
add layer functions: structure, insulation, finish, membrane, air-gap, substrate.

## Floor types

`parametricSlice.ts:726-738`. All are single material:
- concrete (`Beton`): vloer-beton-150, -200, -250, -300;
- hollow core (`Kanaalplaat`): vloer-kanaalplaat-200, -260, -320;
- timber (`Hout`): vloer-hout-200.

Structural floor kinds: kanaalplaatvloer, breedplaatvloer, ribcassettevloer,
staalplaatbetonvloer, massieve vloer, houten vloer, predallen. There are no roof or
ceiling types.

## Material hatching

`src/types/hatch.ts:1080-1088`. The pattern scale is the spacing divided by 10, and
hatch lines turn with the wall's direction.

| Material | Pattern | Background | Lines |
|---|---|---|---|
| concrete | nen47-gewapend-beton: solid fill | — | `#C0C0C0` |
| masonry | nen47-metselwerk-baksteen: 45° double lines | `#D4908F` | black, spacing 800 |
| calcium-silicate | nen47-metselwerk-kunststeen: 45° | `#C8C0B0` | `#A8A090`, 800 |
| timber | nen47-naaldhout: 45° | `#F0DCB9` | black, 750 |
| steel | nen47-staal: solid | — | black |
| insulation | nen47-isolatie | `#FFFDE0` | black |
| generic | 45° | — | `#808080`, 60 |

**Insulation.** In a wall it is one continuous zigzag between the two faces, at 60° to
the wall axis, with a leg of thickness / tan 60°.

**Line families** of the NEN 47 patterns (angle, x origin, y origin, x offset, y
spacing, at scale 1):

| Pattern | Line families |
|---|---|
| baksteen | 45/0/0/0/3 and 45/0/0.5/0/3 |
| kunststeen | 45/0/0/0/3 |
| beton prefab | 45/0/0/0/3 |
| ongewapend beton | ±45/0/0/0/3 |
| naaldhout | 45/0/0/0/3 |
| loofhout | ±45/0/0/0/4 |
| isolatie | ±60/0/0/0/5 |

## Snapping and tracking

`src/state/slices/snapSlice.ts`, `src/engine/geometry/SnapUtils.ts`,
`src/engine/geometry/Tracking.ts`.

**Snap kinds by priority:** endpoint, midpoint, centre, intersection, perpendicular,
parallel, tangent, nearest, alignment, origin, grid.

**Which snap wins.** The nearest candidate within 10 pixels wins. Priority only breaks
near-ties.

**Walls** offer:
- ends: the centreline ends and the four corners;
- middles: the centreline and the four edges;
- nearest: on each edge and the centreline;
- perpendicular: to the centreline and both faces.

Grid lines offer endpoint, midpoint, perpendicular and nearest.

**Tracking:**
- polar rays every 45° (or every 90° in ortho);
- rays parallel and perpendicular to the edge the first click snapped to;
- extension rays from nearby endpoints;
- where two rays meet, the point snaps to their crossing.

**Toggles.** F3 turns snapping on and off, F8 toggles ortho, F10 polar, F11 object
tracking and F12 dynamic input. Shift alone toggles sticky ortho, and X or Y constrains
a move.

**Snap glyphs:**

| Snap | Glyph | Colour |
|---|---|---|
| end | □ | green |
| middle | △ | cyan |
| centre | ○ | magenta |
| intersection | × | yellow |
| perpendicular | ⊥ | orange |
| nearest | ◇ | pink |
| grid | + | blue |

## Navigation and keys

`src/hooks/keyboard/useKeyboardShortcuts.ts`, `src/hooks/navigation/usePanZoom.ts`.

**Mouse:**
- middle-drag pans, and a double middle click zooms to the extents;
- the wheel zooms ×1.1 toward the pointer;
- right-drag places a 2D cursor; a right click opens a context menu.

**Single keys, Blender-like:**
- G moves the selection, from a grip, the 2D cursor or the selection's centre;
- H hides, Shift+H shows everything;
- I isolates;
- L locks, Shift+L unlocks;
- Tab selects a connected chain or enters sketch editing;
- Enter or Space repeats the last tool.

**Two-letter commands.** Commands are also two letters typed within 750 ms, for
example:

| Keys | Command | Keys | Command |
|---|---|---|---|
| wa | wall | wo | wall opening |
| sl | slab | gl | grid line |
| lv | level | rm | space |
| di | dimension | mv | move |
| co | copy | ro | rotate |
| mm | mirror | tr | trim |
| ex | extend | of | offset |

## Views, grids, levels, dimensions

**Drawings and scale.** Drawings are plans (pile, structural, floor or area plan) or
sections, each with a scale (1:100 by default), linked to a storey.

**Visibility** is set per IFC category.

**Line types** are given at 1:100, in mm:
- dashed: 500 on, 250 off;
- dash-dot: 500, 150, 100, 150.

**Grids:**
- A grid line has a label and a bubble at one or both ends.
- It is extended by a scale-dependent length: 1000 mm at 1:100 and 2000 mm at 1:20.
- North-south axes are numbered and east-west axes lettered. Angled axes are named A1,
  B1 and so on.
- A spacing such as `4000 3000 5x5400` creates a series.
- Grid dimensions are generated: spans plus a total.

**Levels.** Levels draw a dashed line with a filled triangle and their datum level
("peil", for example `± 0`, `+ 500`), with the NAP height when a datum is set.

**Dimension styles** (paper mm, 2.5 mm text):
- NEN: filled circle ticks, text above;
- DimAssociate: dots, text centred.

**Temporary dimensions** are previews in screen units, with two decimals.

## IFC

- **Exporter.** The export is hand-written IFC4 in mm.
- **Walls** are exported as extrusions with a fixed 3000 mm height, a single-layer
  material layer set, and `Pset_WallCommon`.
- **Slabs** are extruded up from their elevation. Each type becomes an `IfcWallType`
  or `IfcSlabType` named `<name> <thickness>mm`.
- **Grids:** axes with |dx| ≥ |dy| become U axes, the others V axes.
- There is no IFC import.

## Verdict

The modeller core adopts:
- the wall and floor type library above, including grouped layers with gaps and
  drawn or undrawn layers;
- the material hatch table and NEN 47 line families, with the 60° insulation zigzag;
- the snap kinds, priorities and tracking rules;
- the Blender-like single keys and middle-mouse navigation.

Two-letter commands and plan subtypes are deferred until the basic UI (part G) exists.
