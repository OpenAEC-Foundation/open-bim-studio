# Mixed construction showcase

Generate and open the native model:

```sh
./build.sh probe systems_showcase
build/tools/systems_showcase build/systems-showcase.bim
OBS_MODEL_VIEW=1 build/open-bim-studio build/systems-showcase.bim
```

The building is 18 by 12 metres with levels at 0, 3.2, 6.4 and 9.6 metres.
It contains 36 piles, twelve pile caps, a concrete frame, shared 600 mm PS
beam/EPS floor units, precast floor/deck units, timber joists and OSB, three
straight stairs in a 6 by 6 metre reservation, native hollow-core roof systems,
curtain walls, timber frames, masonry, zinc, timber and panel cladding and a
suspended ceiling. Four plans, two sections, four elevations and a plan sheet
are stored with the model. The exposed precast specimen beside the building
shows nominal reinforcement positions; it is not a fabrication cage.

There are 8,057 native component placements sharing 23 definitions and 22
parametric building systems. Floor units and masonry specimens are explicit
component assemblies. They do not masquerade as regenerating system recipes.
The model is illustrative: sizes, bearings, reinforcement, thermal layers and
stair details have not been engineered or checked against building regulations.

## Masonry gallery

Four columns of specimens start at y=17 m, spaced 4 m in both directions.
Read left to right, then toward increasing y:

1. Stack
2. Half running
3. Quarter standing
4. Quarter right
5. Quarter left
6. English
7. English cross
8. Flemish
9. Monk
10. Header
11. Block
12. Mixed deterministic
13. English garden
14. Flemish garden

Each L-shaped specimen has 24 courses, 2.2 m arms and a separate selectable
corner object, identified by `OpenAEC_Masonry.ObjectRole=MasonryCorner` and its
bond label. Four shared brick lengths (45, 100, 155 and 210 mm), 100 mm deep
and 52.5 mm high, use 10 mm joints. Bricks above the first course use the
instance rise setting rather than duplicated definitions. In half running bond,
alternating quoins and opposite phases on the two arms carry the half-brick
stagger around the corner without overlapping the corner component.

These are 100 mm facing-leaf layout studies, including cut header bats. They
are not full-thickness structural bonds, certified wild bond, every possible
regional bond, or a replacement for the current system tool's regeneration.
The corner object contains the quoin stack; straight-arm bricks retain their
own identities.

Pattern references: [Wienerberger Netherlands](https://www.wienerberger.nl/informatie/gevel/verbanden-in-metselwerk.html),
[Wienerberger UK](https://www.wienerberger.co.uk/tips-and-advice/brickwork/how-do-i-choose-the-correct-brick-bonding-pattern.html),
and the [Brick Development Association bond guide](https://www.brick.org.uk/uploads/downloads/brick-bonds.pdf).
These describe the bond families; they do not validate this generated detail.

The `systems_showcase` native test also retains `build/systems-showcase.bim`.
Verify the generated facing-brick boxes independently of the pattern rules:

```sh
python3 pattern/common/tests/verify_masonry_gallery.py build/systems-showcase.bim
```

The diagnostic checks all 24 courses for intersecting brick volumes and checks
that adjacent half-running courses have different perp-joint positions on both
arms. It measures this explicit box fixture, not arbitrary curved masonry.
