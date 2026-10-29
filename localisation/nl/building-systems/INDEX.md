# Building-system family and preset index

Version 0.2.0. **183 concept presets in 43 families; 83 component interfaces.**
All entries are authoring specifications. Native geometry/UI activation and complete product-system validation are separate capabilities.
These finite families can be composed recursively; they do not claim to enumerate every possible building or certify their combinations.

## Family coverage

| Family | Presets | Layer functions | Boundary roles | Required project/product inputs |
|---|---:|---|---|---|
| hsb | 7 | weather, frame, insulation, sheathing, air-control, service, lining | base, head, jamb, corner, prefab-joint | structural-member-sizes, board-stock-formats, membrane-product-and-order, roll-width-length-laps, fasteners, support-and-loads, prefab-transport-limits |
| partition | 4 | lining-a, frame, insulation, lining-b | base, head, jamb, corner | wall-height-system-selection, profile-product, head-deflection, fixing-schedule, insulation-product |
| ceiling | 4 | hangers, grid, infill | wall-angle, free-edge, column, movement-joint | ceiling-product, panel-edge-and-thickness, support-grid-and-capacity, hanger-spacing, fixture-support, plenum-height |
| window | 15 | frame, infill, seals | head, jamb, sill, glazing-rebate | profile-and-rebate-definition, glazing-specification, hardware, installation-gap, exposure-and-drainage, connection-details |
| masonry | 3 | units, mortar | bonded-corner, jamb, sill, head, movement-joint | brick-product-and-tolerances, joint-widths, ties-and-support, movement-joint-design, lintel-selection |
| sandlime | 1 | units, adhesive | base, head, jamb, corner | supplier-unit-format, adhesive-joint, load-bearing-design, lifting-plan |
| tile | 7 | adhesive, tiles, joints | straight-border, curved-border, movement-joint, threshold, column | actual-calibre, thickness, adhesive-system, movement-joints, minimum-edge-size, kerf-and-cutting-capability, box-quantity |
| cladding | 9 | subframe, cladding | ventilated-base, head, jamb, corner | cladding-product, subframe-design, cavity-depth, fixing-schedule, joint-and-expansion |
| cassette | 2 | deck, frame, insulation, lining | bearing, free-edge, cassette-joint, perimeter | structural-design, member-sizes-and-spacing, deck-product, connections, membrane-strategy, transport-limits |
| hollowcore | 1 | planks, joints | bearing, side-edge, trimmed-edge, joint | supplier-product, span-load-bearing-design, approved-openings, infill-widths, handling-and-lifting |
| cavity-wall | 3 | outer-leaf, cavity, insulation, inner-leaf, ties | base, head, jamb, corner, movement-joint, cavity-barrier | leaf-products, cavity-depth, insulation-strategy, tie-design, cavity-barriers, moisture-design, lintels |
| mass-timber | 4 | structural-panel, optional-insulation, optional-lining | bearing, panel-joint, corner, free-edge | lamination-and-strength-design, panel-stock, machining-limits, fire-design, acoustic-build-up, connections, lifting-plan |
| precast-wall | 3 | outer-face, concrete, optional-insulation | base, head, corner, panel-joint, movement-joint | reinforcement-design, panel-dimensions, bearings, lifting-anchors, connection-design, joint-seals, transport |
| block-wall | 4 | units, joints, optional-finish | base, head, jamb, corner, movement-joint | unit-product, bond, joint-thickness, structural-design, moisture-exposure, ties-and-anchors |
| insulated-formwork | 2 | outer-form, core, inner-form, ties | base, head, corner, pour-stop | system-product, core-design, reinforcement, pour-sequence, bracing, openings, fire-protection |
| sandwich-panel | 4 | outer-skin, core, inner-skin | base, head, corner, panel-joint, ridge, eaves | supplier-panel, core-type, working-width, span-and-loads, fasteners, joint-and-seal, system-fire-evidence |
| light-steel-frame | 4 | frame, insulation, sheathing, weather, lining | base, head, corner, module-joint, bearing | structural-section-design, centre-spacing, sheathing-products, moisture-and-thermal-strategy, connections, corrosion, transport |
| curtain-facade | 5 | frame, infill, seals, anchors | sill, head, jamb, corner, stack-joint | profile-system, drainage, glazing-specification, brackets, building-movement, fire-stopping, pressure-equalisation |
| demountable-partition | 4 | tracks, panels, seals | floor-track, head-track, jamb, corner | system-product, height-adjustment, acoustic-and-fire-evidence, fixings, panel-edge, doors |
| external-insulation | 4 | bond, insulation, fixings, reinforcement, finish | plinth, head, jamb, corner, movement-joint | complete-system-selection, substrate, fixings, reinforcement-laps, opening-reinforcement, plinth-and-fire-details, weather-window |
| roof-covering | 5 | covering, battens, counter-battens, underlay | eaves, ridge, verge, hip, valley, abutment | product, working-length-and-width, measured-batch, roof-slope, exposure, fastening, battens, valley-and-ridge-details |
| standing-seam-roof | 4 | trays, clips, separation, deck | ridge, eaves, verge, valley, expansion-joint | metal-product, developed-and-working-width, slope-and-seam-type, clip-layout, tray-length, substrate, separation-layer |
| flat-roof | 5 | surface, waterproofing, insulation, vapour-control, deck | parapet, eaves, movement-joint, upstand | roof-system, layer-order, slope-drainage, vapour-analysis, wind-design, fire-design, attachment, upstand-and-drain-details |
| vegetated-roof | 5 | vegetation, substrate, filter, retention, protection | vegetation-free-edge, fire-break, parapet | saturated-weight, drainage, waterproofing-compatibility, fire-breaks, vegetation, irrigation, maintenance-access |
| raised-floor | 3 | finish, panels, stringers, pedestals | perimeter, ramp, step, movement-joint | system-panel-size, loading, floor-height, pedestal-and-stringer-layout, fire-zones, cut-edge-support |
| beam-block-floor | 2 | topping, fillers, beams | bearing, perimeter, closure | supplier-system, span-load-design, bearing, lengths, beam-spacing, topping-and-reinforcement, ventilation-openings |
| precast-slab | 4 | finish, structural-panel, joints | bearing, perimeter, joint | supplier-panel, structural-design, bearings, lifting, transportation, joint-design, opening-approval |
| composite-deck | 2 | concrete, deck, supports | bearing, side-edge, pour-stop | deck-profile, span-propping, studs, reinforcement, fire-design, pour-sequence, opening-reinforcement |
| screed | 5 | screed, separation, insulation, edge-strip | edge-isolation, movement-joint, threshold | substrate, screed-system, thickness, moisture-and-curing, movement-joints, insulation-compression, loads, heating-design |
| timber-floor-finish | 5 | boards, underlay, support | perimeter, threshold, movement-joint, stair-nosing | product-width-and-length, stock-assortment, end-joint-rules, moisture-and-expansion, adhesion-or-fasteners, minimum-end-piece |
| resilient-floor | 4 | finish, adhesive, levelling | coved-skirting, threshold, seam, movement-joint | product, roll-width-and-length, direction-and-batch, seam-process, substrate-moisture, adhesives, residual-quality |
| modular-floor-finish | 4 | finish, fixing | border, threshold, movement-joint | product, tile-format, direction-policy, substrate, fixing-system, batch, minimum-reusable-size |
| pavement | 5 | units, bedding, foundation, edge-restraint | kerb, border, threshold, movement-joint | paver-product, bond, load-bearing-foundation, falls, drainage, joints, edge-restraints, frost-and-exposure |
| decking | 4 | deck, joists, pedestals | edge, nosing, curved-border, movement-joint | deck-product, stock-lengths, joist-spacing, fastening, gaps, drainage, supports, corrosion-and-exposure |
| drylining-ceiling | 4 | finish, boards, secondary, primary, hangers | perimeter, shadow-gap, movement-joint | complete-system-selection, board-layers, framing-spacing, hangers, fixings, spans, fire-and-acoustic-evidence |
| special-ceiling | 6 | elements, carriers, hangers | perimeter, free-edge, curved-edge | element-product, carrier-grid, suspension, loads, element-spacing, acoustic-evidence, access-and-cleaning |
| stretched-membrane | 3 | membrane, tracks, optional-backing | track, corner, curve, splice | system-membrane, tension, mounting-tracks, dimensional-limits, temperature, fire-and-acoustic-evidence, service-reinforcement |
| solar-overlay | 4 | modules, rails, supports | fire-access-edge, wind-zone, drainage-zone | mounting-product, module-size, wind-and-snow, roof-capacity, waterproofing, interfaces, fire-access, electrical-design |
| shading | 4 | slats, carriers, brackets | head, jamb, sill, edge | product, wind-design, supports, slat-angle, movement-envelope, corrosion, controls, maintenance |
| green-facade | 4 | vegetation, carrier, irrigation, protection | base, head, corner, fire-break | saturated-load, support-design, plant-species, irrigation, drainage, root-protection, fire-breaks, maintenance |
| guarding | 4 | posts, rails, infill, anchors | base, end, corner, handrail | required-guard-height, loading, opening-dimensions, anchorage, substrate, waterproofing, impact-evidence |
| modular-interior | 3 | carcass, fronts, hardware, worktop | plinth, top, side, wall-junction | module-dimensions, board-products, edge-banding, hardware, load-and-fixings, appliance-clearance, worktop-cutouts |
| service-carrier | 4 | supports, rails, service-modules | end, support, crossing, fire-compartment | service-discipline-design, load-and-support, spacing, movement, electrical-and-fluid-interfaces, fire-stopping, access |

## Presets

| Stable ID | Dutch label | Family | Status |
|---|---|---|---|
| `nl.generic.hsb-140-600` | HSB buitenwand 140 / h.o.h. 600 | hsb | concept |
| `nl.generic.hsb-140-610` | HSB buitenwand 140 / h.o.h. 610 | hsb | concept |
| `nl.generic.hsb-184-600` | HSB buitenwand 184 / h.o.h. 600 | hsb | concept |
| `nl.generic.hsb-184-610` | HSB buitenwand 184 / h.o.h. 610 | hsb | concept |
| `nl.generic.hsb-235-600` | HSB buitenwand 235 / h.o.h. 600 | hsb | concept |
| `nl.generic.hsb-235-610` | HSB buitenwand 235 / h.o.h. 610 | hsb | concept |
| `nl.generic.hsb-internal` | HSB binnenwand met tweezijdige beplating | hsb | concept |
| `nl.generic.metal-stud-75-1` | Metalen systeemwand 75, 1 plaatlaag per zijde | partition | concept |
| `nl.generic.metal-stud-75-2` | Metalen systeemwand 75, 2 plaatlaag per zijde | partition | concept |
| `nl.generic.metal-stud-100-1` | Metalen systeemwand 100, 1 plaatlaag per zijde | partition | concept |
| `nl.generic.metal-stud-100-2` | Metalen systeemwand 100, 2 plaatlaag per zijde | partition | concept |
| `nl.generic.ceiling-t24-600` | Systeemplafond t24-600 | ceiling | concept |
| `nl.generic.ceiling-t24-1200` | Systeemplafond t24-1200 | ceiling | concept |
| `nl.generic.ceiling-t15-600` | Systeemplafond t15-600 | ceiling | concept |
| `nl.generic.ceiling-concealed-600` | Systeemplafond concealed-600 | ceiling | concept |
| `nl.generic.window-timber-fixed` | Houten kozijn — fixed | window | concept |
| `nl.generic.window-timber-single-casement` | Houten kozijn — single-casement | window | concept |
| `nl.generic.window-timber-double-casement` | Houten kozijn — double-casement | window | concept |
| `nl.generic.window-timber-transom` | Houten kozijn — transom | window | concept |
| `nl.generic.window-timber-sidelight-door` | Houten kozijn — sidelight-door | window | concept |
| `nl.generic.window-aluminium-fixed` | Aluminium kozijn — fixed | window | concept |
| `nl.generic.window-aluminium-single-casement` | Aluminium kozijn — single-casement | window | concept |
| `nl.generic.window-aluminium-double-casement` | Aluminium kozijn — double-casement | window | concept |
| `nl.generic.window-aluminium-transom` | Aluminium kozijn — transom | window | concept |
| `nl.generic.window-aluminium-sidelight-door` | Aluminium kozijn — sidelight-door | window | concept |
| `nl.generic.window-pvc-fixed` | Kunststof kozijn — fixed | window | concept |
| `nl.generic.window-pvc-single-casement` | Kunststof kozijn — single-casement | window | concept |
| `nl.generic.window-pvc-double-casement` | Kunststof kozijn — double-casement | window | concept |
| `nl.generic.window-pvc-transom` | Kunststof kozijn — transom | window | concept |
| `nl.generic.window-pvc-sidelight-door` | Kunststof kozijn — sidelight-door | window | concept |
| `nl.generic.brick-waal-half` | Metselwerk waalformaat — half | masonry | concept |
| `nl.generic.brick-waal-stack` | Metselwerk waalformaat — stack | masonry | concept |
| `nl.generic.brick-waal-quarter` | Metselwerk waalformaat — quarter | masonry | concept |
| `nl.generic.sandlime-elements` | Kalkzandsteen lijmelementen — productmaat kiezen | sandlime | concept |
| `nl.generic.tile-300-none` | Tegelvloer module 300 — rand none | tile | concept |
| `nl.generic.tile-300-straight` | Tegelvloer module 300 — rand straight | tile | concept |
| `nl.generic.tile-300-curved` | Tegelvloer module 300 — rand curved | tile | concept |
| `nl.generic.tile-600-none` | Tegelvloer module 600 — rand none | tile | concept |
| `nl.generic.tile-600-straight` | Tegelvloer module 600 — rand straight | tile | concept |
| `nl.generic.tile-600-curved` | Tegelvloer module 600 — rand curved | tile | concept |
| `nl.generic.tile-running` | Tegelvloer rechthoekig — verspringend verband | tile | concept |
| `nl.generic.cladding-timber-horizontal` | Gevelbekleding — timber-horizontal | cladding | concept |
| `nl.generic.cladding-timber-vertical` | Gevelbekleding — timber-vertical | cladding | concept |
| `nl.generic.cladding-hpl` | Gevelbekleding — hpl | cladding | concept |
| `nl.generic.cladding-standing-seam-zinc` | Gevelbekleding — standing-seam-zinc | cladding | concept |
| `nl.generic.timber-cassette-floor` | Houten cassette — floor | cassette | concept |
| `nl.generic.timber-cassette-roof` | Houten cassette — roof | cassette | concept |
| `nl.generic.hollowcore-320` | Kanaalplaatvloer 320 — productselectie vereist | hollowcore | concept |
| `nl.generic.cavity-wall-brick-sandlime` | Spouwmuur baksteen / kalkzandsteen | cavity-wall | concept |
| `nl.generic.cavity-wall-brick-hsb` | Spouwmuur baksteen / HSB | cavity-wall | concept |
| `nl.generic.cavity-wall-brick-concrete` | Spouwmuur baksteen / beton | cavity-wall | concept |
| `nl.generic.mass-timber-clt-wall` | CLT wandplaat | mass-timber | concept |
| `nl.generic.mass-timber-clt-floor` | CLT vloerplaat | mass-timber | concept |
| `nl.generic.mass-timber-clt-roof` | CLT dakplaat | mass-timber | concept |
| `nl.generic.mass-timber-dowel-panel` | Massief houten deuvelpaneel | mass-timber | concept |
| `nl.generic.precast-wall-solid` | Prefab massieve betonwand | precast-wall | concept |
| `nl.generic.precast-wall-sandwich` | Prefab betonnen sandwichwand | precast-wall | concept |
| `nl.generic.precast-wall-double-wall` | Prefab dubbele breedwand | precast-wall | concept |
| `nl.generic.block-wall-aac` | Cellenbeton blokkenwand | block-wall | concept |
| `nl.generic.block-wall-concrete-block` | Betonblokkenwand | block-wall | concept |
| `nl.generic.block-wall-clay-block` | Keramische binnenmuurblokken | block-wall | concept |
| `nl.generic.block-wall-sandlime-block` | Kalkzandsteen blokkenwand | block-wall | concept |
| `nl.generic.insulated-formwork-icf` | ICF wand met isolatiebekisting | insulated-formwork | concept |
| `nl.generic.insulated-formwork-mineral-form` | Minerale verloren wandbekisting | insulated-formwork | concept |
| `nl.generic.sandwich-panel-mineral-core` | Sandwichpaneel minerale-wolkern | sandwich-panel | concept |
| `nl.generic.sandwich-panel-foam-core` | Sandwichpaneel schuimkern | sandwich-panel | concept |
| `nl.generic.sandwich-panel-sip-timber` | Houten SIP sandwichpaneel | sandwich-panel | concept |
| `nl.generic.sandwich-panel-cold-store` | Sandwichpaneel koelcel | sandwich-panel | concept |
| `nl.generic.light-steel-frame-sfs-infill` | Licht stalen gevelinvulwand | light-steel-frame | concept |
| `nl.generic.light-steel-frame-loadbearing` | Dragend licht staalframe | light-steel-frame | concept |
| `nl.generic.light-steel-frame-floor-cassette` | Licht stalen vloercassette | light-steel-frame | concept |
| `nl.generic.light-steel-frame-roof-cassette` | Licht stalen dakcassette | light-steel-frame | concept |
| `nl.generic.curtain-facade-stick` | Vliesgevel stijl-regel | curtain-facade | concept |
| `nl.generic.curtain-facade-unitised` | Elementenvliesgevel | curtain-facade | concept |
| `nl.generic.curtain-facade-structural-glazing` | Vliesgevel structurele beglazing | curtain-facade | concept |
| `nl.generic.curtain-facade-double-skin` | Dubbele-huidgevel | curtain-facade | concept |
| `nl.generic.curtain-facade-timber-hybrid` | Hout-aluminium vliesgevel | curtain-facade | concept |
| `nl.generic.demountable-partition-single-glass` | Enkelglazen systeemwand | demountable-partition | concept |
| `nl.generic.demountable-partition-double-glass` | Dubbelglazen systeemwand | demountable-partition | concept |
| `nl.generic.demountable-partition-opaque` | Dichte demontabele systeemwand | demountable-partition | concept |
| `nl.generic.demountable-partition-operable` | Verplaatsbare paneelwand | demountable-partition | concept |
| `nl.generic.external-insulation-mineral-wool` | Gevelisolatie minerale wol / pleister | external-insulation | concept |
| `nl.generic.external-insulation-eps` | Gevelisolatie EPS / pleister | external-insulation | concept |
| `nl.generic.external-insulation-wood-fibre` | Gevelisolatie houtvezel / pleister | external-insulation | concept |
| `nl.generic.external-insulation-brick-slip` | Gevelisolatie met steenstrips | external-insulation | concept |
| `nl.generic.roof-covering-clay-tile` | Keramisch pannendak | roof-covering | concept |
| `nl.generic.roof-covering-concrete-tile` | Betonnen pannendak | roof-covering | concept |
| `nl.generic.roof-covering-natural-slate` | Natuurleien dak | roof-covering | concept |
| `nl.generic.roof-covering-fibre-cement-slate` | Vezelcement leien dak | roof-covering | concept |
| `nl.generic.roof-covering-shingle` | Shingle dak | roof-covering | concept |
| `nl.generic.standing-seam-roof-zinc-double` | Zinken dubbele staande fels | standing-seam-roof | concept |
| `nl.generic.standing-seam-roof-zinc-single` | Zinken enkele staande fels | standing-seam-roof | concept |
| `nl.generic.standing-seam-roof-aluminium` | Aluminium felsdak | standing-seam-roof | concept |
| `nl.generic.standing-seam-roof-steel` | Stalen felsdak | standing-seam-roof | concept |
| `nl.generic.flat-roof-warm-bitumen` | Warm dak met bitumineuze bedekking | flat-roof | concept |
| `nl.generic.flat-roof-warm-epdm` | Warm dak met EPDM | flat-roof | concept |
| `nl.generic.flat-roof-warm-thermoplastic` | Warm dak met kunststof membraan | flat-roof | concept |
| `nl.generic.flat-roof-inverted` | Omgekeerd dak | flat-roof | concept |
| `nl.generic.flat-roof-renovation-overlay` | Renovatiedak met overlaag | flat-roof | concept |
| `nl.generic.vegetated-roof-sedum` | Extensief sedumdak | vegetated-roof | concept |
| `nl.generic.vegetated-roof-biodiverse` | Biodivers groendak | vegetated-roof | concept |
| `nl.generic.vegetated-roof-intensive` | Intensieve daktuin | vegetated-roof | concept |
| `nl.generic.vegetated-roof-blue` | Waterretentiedak | vegetated-roof | concept |
| `nl.generic.vegetated-roof-biosolar` | Groendak met PV-zones | vegetated-roof | concept |
| `nl.generic.raised-floor-pedestal-stringer` | Verhoogde vloer met stringers | raised-floor | concept |
| `nl.generic.raised-floor-pedestal-only` | Verhoogde vloer op losse vijzels | raised-floor | concept |
| `nl.generic.raised-floor-ventilated` | Geperforeerde installatievloer | raised-floor | concept |
| `nl.generic.beam-block-floor-concrete-filler` | Balken-broodjesvloer met betonvulling | beam-block-floor | concept |
| `nl.generic.beam-block-floor-insulated-filler` | Balken-broodjesvloer met isolatievulling | beam-block-floor | concept |
| `nl.generic.precast-slab-solid` | Massieve prefab betonvloer | precast-slab | concept |
| `nl.generic.precast-slab-double-tee` | TT-plaatvloer | precast-slab | concept |
| `nl.generic.precast-slab-ribbed` | Geribde prefab betonvloer | precast-slab | concept |
| `nl.generic.precast-slab-filigree` | Breedplaatvloer met opstort | precast-slab | concept |
| `nl.generic.composite-deck-composite` | Samenwerkende staalplaat-betonvloer | composite-deck | concept |
| `nl.generic.composite-deck-permanent-formwork` | Staalplaat als verloren bekisting | composite-deck | concept |
| `nl.generic.screed-cement-bonded` | Hechtende cementdekvloer | screed | concept |
| `nl.generic.screed-floating-cement` | Zwevende cementdekvloer | screed | concept |
| `nl.generic.screed-calcium-sulphate` | Calciumsulfaat gietdekvloer | screed | concept |
| `nl.generic.screed-dry-board` | Droge plaatdekvloer | screed | concept |
| `nl.generic.screed-heated` | Dekvloer met vloerverwarming | screed | concept |
| `nl.generic.timber-floor-finish-solid` | Massieve houten plankenvloer | timber-floor-finish | concept |
| `nl.generic.timber-floor-finish-engineered` | Samengestelde houten vloer | timber-floor-finish | concept |
| `nl.generic.timber-floor-finish-herringbone` | Houten visgraatvloer | timber-floor-finish | concept |
| `nl.generic.timber-floor-finish-chevron` | Houten Hongaarse punt | timber-floor-finish | concept |
| `nl.generic.timber-floor-finish-laminate` | Laminaatvloer | timber-floor-finish | concept |
| `nl.generic.resilient-floor-linoleum` | Linoleum banen | resilient-floor | concept |
| `nl.generic.resilient-floor-vinyl` | Vinyl banen | resilient-floor | concept |
| `nl.generic.resilient-floor-rubber` | Rubber banen | resilient-floor | concept |
| `nl.generic.resilient-floor-carpet` | Tapijt banen | resilient-floor | concept |
| `nl.generic.modular-floor-finish-carpet-monolithic` | Tapijttegels monolithisch | modular-floor-finish | concept |
| `nl.generic.modular-floor-finish-carpet-quarter` | Tapijttegels kwartslag | modular-floor-finish | concept |
| `nl.generic.modular-floor-finish-vinyl-plank` | PVC-strokenvloer | modular-floor-finish | concept |
| `nl.generic.modular-floor-finish-rubber-tile` | Rubber tegelvloer | modular-floor-finish | concept |
| `nl.generic.pavement-clay` | Gebakken klinkerbestrating | pavement | concept |
| `nl.generic.pavement-concrete` | Betonklinkerbestrating | pavement | concept |
| `nl.generic.pavement-stone` | Natuursteenbestrating | pavement | concept |
| `nl.generic.pavement-permeable` | Waterpasserende bestrating | pavement | concept |
| `nl.generic.pavement-slabs` | Terrastegels met opsluitranden | pavement | concept |
| `nl.generic.decking-timber` | Houten vlonder | decking | concept |
| `nl.generic.decking-composite` | Composiet vlonder | decking | concept |
| `nl.generic.decking-aluminium` | Aluminium terrasdelen | decking | concept |
| `nl.generic.decking-pedestal-slabs` | Tegeldragerterras | decking | concept |
| `nl.generic.drylining-ceiling-single-board` | Enkel beplaat gipsplafond | drylining-ceiling | concept |
| `nl.generic.drylining-ceiling-double-board` | Dubbel beplaat gipsplafond | drylining-ceiling | concept |
| `nl.generic.drylining-ceiling-acoustic` | Geperforeerd akoestisch plaatplafond | drylining-ceiling | concept |
| `nl.generic.drylining-ceiling-moisture` | Vochtbestendige plafondbeplating | drylining-ceiling | concept |
| `nl.generic.special-ceiling-baffles` | Verticaal baffleplafond | special-ceiling | concept |
| `nl.generic.special-ceiling-rafts` | Akoestische plafondeilanden | special-ceiling | concept |
| `nl.generic.special-ceiling-metal-planks` | Metalen strokenplafond | special-ceiling | concept |
| `nl.generic.special-ceiling-timber-slats` | Houten lattenplafond | special-ceiling | concept |
| `nl.generic.special-ceiling-open-cell` | Open rasterplafond | special-ceiling | concept |
| `nl.generic.special-ceiling-mesh` | Strekmetaalplafond | special-ceiling | concept |
| `nl.generic.stretched-membrane-ceiling` | Spanplafond | stretched-membrane | concept |
| `nl.generic.stretched-membrane-backlit` | Verlicht spanplafond | stretched-membrane | concept |
| `nl.generic.stretched-membrane-acoustic-wall` | Gespannen akoestisch wanddoek | stretched-membrane | concept |
| `nl.generic.solar-overlay-pitched-rail` | PV op schuindakrails | solar-overlay | concept |
| `nl.generic.solar-overlay-flat-ballast` | PV op geballast platdaksysteem | solar-overlay | concept |
| `nl.generic.solar-overlay-seam-clamp` | PV op felsdak-klemmen | solar-overlay | concept |
| `nl.generic.solar-overlay-facade` | PV-gevelmontage | solar-overlay | concept |
| `nl.generic.shading-horizontal` | Horizontale gevel-lamellen | shading | concept |
| `nl.generic.shading-vertical` | Verticale gevel-lamellen | shading | concept |
| `nl.generic.shading-screen` | Gevelscreens | shading | concept |
| `nl.generic.shading-shutter` | Schuifluikpanelen | shading | concept |
| `nl.generic.green-facade-trellis` | Klimplanten op raster | green-facade | concept |
| `nl.generic.green-facade-cable` | Klimplanten op kabelsysteem | green-facade | concept |
| `nl.generic.green-facade-modular` | Modulaire groene gevel | green-facade | concept |
| `nl.generic.green-facade-planters` | Gevel met plantenbakken | green-facade | concept |
| `nl.generic.guarding-posts-bars` | Spijlenbalustrade | guarding | concept |
| `nl.generic.guarding-posts-glass` | Glasbalustrade met stijlen | guarding | concept |
| `nl.generic.guarding-channel-glass` | Glasbalustrade in vloerprofiel | guarding | concept |
| `nl.generic.guarding-mesh` | Gaas- of plaatbalustrade | guarding | concept |
| `nl.generic.modular-interior-storage` | Modulaire kastenwand | modular-interior | concept |
| `nl.generic.modular-interior-kitchen` | Modulaire keukenwand | modular-interior | concept |
| `nl.generic.modular-interior-workbench` | Werkbankmodules | modular-interior | concept |
| `nl.generic.service-carrier-rack` | Installatierack | service-carrier | concept |
| `nl.generic.service-carrier-cable-tray` | Kabelgootsysteem | service-carrier | concept |
| `nl.generic.service-carrier-wall-service` | Installatievoorzetwand | service-carrier | concept |
| `nl.generic.service-carrier-floor-heating-carrier` | Drager voor vloerverwarming | service-carrier | concept |
| `nl.generic.cladding-fibre-cement` | Vezelcement gevelbekleding | cladding | concept |
| `nl.generic.cladding-stone` | Natuursteen gevelbekleding | cladding | concept |
| `nl.generic.cladding-ceramic` | Keramische gevelbekleding | cladding | concept |
| `nl.generic.cladding-metal-cassettes` | Metalen gevelcassettes | cladding | concept |
| `nl.generic.cladding-terracotta` | Terracotta baguettegevel | cladding | concept |

## Component interfaces

| Interface role | Ports | Required definition inputs |
|---|---|---|
| accent-board | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| accent-panel | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| accent-strip | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| accent-tile | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| accent-unit | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| access-door | opening-edge, support, access | product-definition, clear-opening, swing-envelope, locking, edge-compatibility, assembly-evidence |
| access-hatch | opening-edge, support, access | product-definition, clear-opening, swing-envelope, locking, edge-compatibility, assembly-evidence |
| access-panel | cell-edge, support, access | clear-opening, swing-envelope, edge-compatibility |
| access-walkway | substrate, support, drainage, access | system-product, layer-order, saturated-load, drainage, fire-access, waterproofing-compatibility |
| acoustic-board | cell-edge, support, finish | board-product, edge-support, thickness, assembly-evidence, fixing-schedule |
| acoustic-membrane | perimeter-track, tension, support, access | membrane-product, tension, edge-fixing, service-clearance, electrical-or-acoustic-design |
| acoustic-panel | cell-edge, support, finish | board-product, edge-support, thickness, assembly-evidence, fixing-schedule |
| appliance | opening-edge, support, services, access | product-definition, envelope, mounting, discipline-connection, maintenance-clearance, fire-stopping |
| backlit-panel | perimeter-track, tension, support, access | membrane-product, tension, edge-fixing, service-clearance, electrical-or-acoustic-design |
| blue-roof | substrate, support, drainage, access | system-product, layer-order, saturated-load, drainage, fire-access, waterproofing-compatibility |
| border-product | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| border-strip | pattern-edge, support, finish | product-definition, actual-dimensions, batch, direction, factory-edge-requirements, cut-policy |
| brick-slip | substrate, finish, joint | complete-system-selection, substrate-compatibility, coverage, thickness, reinforcement |
| cable-tray | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| casement | frame-edge, hinge, latch, air, water, access | leaf-definition, handing, opening-sweep, hardware, glazing-or-panel, weight |
| climbing-wire | anchor, support, drainage, irrigation, access | product-definition, wet-load, plant-and-irrigation-design, anchorage, fire-breaks, maintenance |
| closure-block | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| closure-unit | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| cut-unit | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| diffuser | cell-edge, support, air, access | manufacturer-envelope, weight, support-method, duct-envelope |
| door | head, jamb-left, jamb-right, threshold, access | rough-opening, leaf-definition, hardware, swing-envelope |
| door-leaf | frame-edge, hinge, latch, air, water, access | leaf-definition, handing, opening-sweep, hardware, glazing-or-panel, weight |
| drawer | carcass-edge, support, access | product-definition, dimensions, loads, hardware, opening-envelope, finish-direction |
| dry-board-zone | cell-edge, support, finish | board-product, edge-support, thickness, assembly-evidence, fixing-schedule |
| duct-zone | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| dummy-module | mounting-edge, support, electrical, water, access | product-definition, envelope, electrical-design, wind-restraint, roof-compatibility, maintenance-access |
| entrance-mat | floor-edge, support, drainage, finish | product-definition, actual-dimensions, load-and-slip-requirements, drainage, edge-restraint |
| fire-board | cell-edge, support, finish | board-product, edge-support, thickness, assembly-evidence, fixing-schedule |
| fixed-glazing | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| fixed-louvre | bracket, support, movement, access | product-definition, loads, support, movement-envelope, control-interface, exposure |
| floor-box | opening-edge, support, services, access | product-definition, envelope, mounting, discipline-connection, maintenance-clearance, fire-stopping |
| glass-panel | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| glazing | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| green-roof | substrate, support, drainage, access | system-product, layer-order, saturated-load, drainage, fire-access, waterproofing-compatibility |
| insulated-filler | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| louvre | bracket, support, movement, access | product-definition, loads, support, movement-envelope, control-interface, exposure |
| luminaire | cell-edge, support, electrical, access | manufacturer-envelope, weight, support-method, clearance, edge-finish |
| mesh-panel | frame-edge, support, guard-boundary | product-definition, opening-size, loads, fixing-system, impact-requirements |
| mineral-render | substrate, finish, joint | complete-system-selection, substrate-compatibility, coverage, thickness, reinforcement |
| modular-panel | anchor, support, drainage, irrigation, access | product-definition, wet-load, plant-and-irrigation-design, anchorage, fire-breaks, maintenance |
| moisture-board | cell-edge, support, finish | board-product, edge-support, thickness, assembly-evidence, fixing-schedule |
| opaque-panel | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| opaque-spandrel | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| open-shelf | carcass-edge, support, access | product-definition, dimensions, loads, hardware, opening-envelope, finish-direction |
| operable-louvre | bracket, support, movement, access | product-definition, loads, support, movement-envelope, control-interface, exposure |
| organic-render | substrate, finish, joint | complete-system-selection, substrate-compatibility, coverage, thickness, reinforcement |
| permeable-unit | floor-edge, support, drainage, finish | product-definition, actual-dimensions, load-and-slip-requirements, drainage, edge-restraint |
| photovoltaic-panel | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| pipe-rack | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| planter | anchor, support, drainage, irrigation, access | product-definition, wet-load, plant-and-irrigation-design, anchorage, fire-breaks, maintenance |
| reinforced-unit | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| rod-infill | frame-edge, support, guard-boundary | product-definition, opening-size, loads, fixing-system, impact-requirements |
| rooflight | curb, head, jamb, sill, water, air, support, access | product-definition, roof-slope, flashing-set, rough-opening, insulation, mounting |
| screen | bracket, support, movement, access | product-definition, loads, support, movement-envelope, control-interface, exposure |
| service-opening | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| service-penetration | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| service-zone | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| snow-guard | covering-interface, support, water | supplier-product, roof-compatibility, fasteners, snow-or-air-design |
| solar-module | mounting-edge, support, electrical, water, access | product-definition, envelope, electrical-design, wind-restraint, roof-compatibility, maintenance-access |
| solar-overlay | mounting-edge, support, electrical, water, access | product-definition, envelope, electrical-design, wind-restraint, roof-compatibility, maintenance-access |
| solar-tile | mounting-edge, support, electrical, water, access | product-definition, envelope, electrical-design, wind-restraint, roof-compatibility, maintenance-access |
| speaker | opening-edge, support, services, access | product-definition, envelope, mounting, discipline-connection, maintenance-clearance, fire-stopping |
| special-closer | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| sprinkler-clearance | opening-edge, support, services, access | product-definition, envelope, mounting, discipline-connection, maintenance-clearance, fire-stopping |
| supplier-infill | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| supplier-infill-plank | unit-edge, bearing, joint | supplier-product, exact-shape, bearing, cut-approval, handling, joint-detail |
| tactile-paving | floor-edge, support, drainage, finish | product-definition, actual-dimensions, load-and-slip-requirements, drainage, edge-restraint |
| tilt-turn | frame-edge, hinge, latch, air, water, access | leaf-definition, handing, opening-sweep, hardware, glazing-or-panel, weight |
| translucent-panel | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| translucent-unit | cell-edge, support, air, water, access | product-definition, envelope, edge-finish, support-method, exposure, batch |
| underfloor-heating | carrier, support, services, access, fire-boundary | discipline-design, envelope, loads, supports, connections, insulation, fire-stopping |
| vent | cell-edge, support, air, access | product-definition, airflow-interface, envelope, weather-or-fire-requirements, support-method |
| vent-panel | cell-edge, support, air, access | product-definition, airflow-interface, envelope, weather-or-fire-requirements, support-method |
| vent-tile | covering-interface, support, water | supplier-product, roof-compatibility, fasteners, snow-or-air-design |
| vent-unit | cell-edge, support, air, access | product-definition, airflow-interface, envelope, weather-or-fire-requirements, support-method |
| ventilation-opening | cell-edge, support, air, access | product-definition, airflow-interface, envelope, weather-or-fire-requirements, support-method |
| walkway | substrate, support, drainage, access | system-product, layer-order, saturated-load, drainage, fire-access, waterproofing-compatibility |
| window | head, jamb-left, jamb-right, sill, air, water | rough-opening, frame-definition, installation-joint, exposure |

## Composition boundaries

A parent supplies a bounded domain and typed ports; a child supplies its envelope and interface requests.
Only compatible component roles may substitute. A matching bounding rectangle is insufficient.
Product-specific dimensions, assembly evidence, structural/MEP design and connection rules remain required inputs.
Layer suppression is an occurrence operation, not a substitute product. Unknown geometry capabilities refuse activation.
See [the generator contract](../../../docs/domain/building-system-generator.md) and [catalogue policy](README.md).
