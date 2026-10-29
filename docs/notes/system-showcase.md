# Native system showcase

Generate with the existing compatible DynLex toolchain:

```sh
bash build.sh probe system_showcase
build/tools/system_showcase > build/system-showcase.out
cmp tools/probes/system_showcase.expected.txt build/system-showcase.out
```

Output: `build/system-showcase.bim`. The model uses 43 existing recipe definitions,
plus nine larger feature stations, giving 58 system records including native
layer systems. It is a sample exhibition, not a complete building.

The model was generated, serialized and independently opened in the native app.
All 20 expected output lines matched, both compiler diagnostics were empty, and
native inspection showed 58 systems with Undo 0. File SHA256:
`73e06706bc823fc61e38eed679e5c7aa058d43740d01c1ece94c0b102e33033a`.

Visual review covered the plan, a 3D overview and enlarged feature stations:
curved glass and masonry carriers, sloping upper contours, concave circular
upper contours, diamond and running/stack bond samples, floors and ceiling.
Sloping contours remain in vertical wall planes; tilted workplanes are not
shown. Curved carriers are faceted. Window/door recipes are schematic examples.
This does not establish generic regeneration or product certification.

The app used the independently tested Fit review binary at a3086e5, not merged
main. Its first frame reported 93,863 ms for this large model. The model remains
open in its own process. No previously handed-off user window was operated.

## Station map

```text
System showcase station map
Native modeller examples; no certification or generic regeneration claim.
Catalogue stations: 8 columns; x=column*9 m, y=row*10 m. Each sample 6 m wide.

01  (0, 0) m: Vliesgevel aluminium 1500
02  (9, 0) m: Vliesgevel structural glazing
03  (18, 0) m: Vliesgevel hout-aluminium 1200
04  (27, 0) m: Kozijn hout 67x114
05  (36, 0) m: Kozijn aluminium 75
06  (45, 0) m: Kozijn kunststof 70
07  (54, 0) m: HSB wand 38x140 h.o.h. 600
08  (63, 0) m: HSB wand 38x184 h.o.h. 600
09  (0, 10) m: Metselwerk waalformaat halfsteens
10  (9, 10) m: Metselwerk dikformaat halfsteens
11  (18, 10) m: Metselwerk waalformaat stapelverband
12  (27, 10) m: Kalkzandsteen elementen 100
13  (36, 10) m: Zinken felsgevel 430
14  (45, 10) m: Houten rabatdelen 140
15  (54, 10) m: Gevelplaten HPL 1200x3000
16  (63, 10) m: Kanaalplaatvloer 150
17  (0, 20) m: Kanaalplaatvloer 200
18  (9, 20) m: Kanaalplaatvloer 260
19  (18, 20) m: Kanaalplaatvloer 320
20  (27, 20) m: Kanaalplaatvloer 400
21  (36, 20) m: Systeemplafond 600x600
22  (45, 20) m: Fixed timber 67x114
23  (54, 20) m: Fixed aluminium 50x75
24  (63, 20) m: Fixed PVC 64x70
25  (0, 30) m: Casement timber layout
26  (9, 30) m: Tilt-turn PVC layout
27  (18, 30) m: Double casement timber layout
28  (27, 30) m: Timber window with transom
29  (36, 30) m: Timber door leaf
30  (45, 30) m: Timber door with sidelight
31  (54, 30) m: Double glazed timber doors
32  (63, 30) m: Two-panel sliding aluminium layout
33  (0, 40) m: Three-panel sliding aluminium layout
34  (9, 40) m: Fixed timber 90x139
35  (18, 40) m: Double casement timber 90x139 layout
36  (27, 40) m: Timber 90x139 with transom
37  (36, 40) m: Timber sliding door 67x174 layout
38  (45, 40) m: Reynaers ConceptPatio 130 - 2 rail layout
39  (54, 40) m: Reynaers ConceptPatio 130 - 3 rail layout
40  (63, 40) m: Reynaers MasterPatio - 2 rail layout
41  (0, 50) m: Reynaers MasterPatio - 3 rail layout
42  (9, 50) m: Reynaers SlimPatio 68 - 2 rail layout
43  (18, 50) m: Reynaers SlimPatio 68 - 3 rail layout

Feature row y=64 m (8 m wide):
01 x=0 curved glass facade; 02 x=12 curved running-bond masonry
03 x=24 sloped-top timber frame; 04 x=36 sloped-top masonry
05 x=48 rounded-top stack-bond masonry; 06 x=60 rounded-top glass
Feature row y=78 m:
07 x=0 diamond-pattern masonry; 08 x=12 diamond-pattern infill; 09 x=24 ceiling

Sloped tops are vertical face contours, not tilted wall planes.
Curved carriers are faceted between generated stations.
Window/door recipes demonstrate schematic layouts, not full product certification.
```
