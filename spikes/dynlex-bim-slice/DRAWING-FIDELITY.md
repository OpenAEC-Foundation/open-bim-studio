# Sheet drawing units and source-frame templates

Sheet symbols use paper dimensions independently of model scale and export
resolution. `bim canvas record.paperScale` holds canvas units per millimetre:
zero retains screen recording behaviour; a sheet sets it to its export density.
Existing screen stroke widths and dimension-symbol coordinates use four units
per millimetre. The conversion happens once at recording time.

On sheets, grid heads have a 6 mm circle diameter, with the stroke outside that
radius. Grid dash-dot strokes use a 4.5 mm dash, 0.5 mm dot and 4 mm gaps.
Dimension text offsets are 1.25 mm; the existing 0.7-unit dimension line becomes
0.175 mm. Screen recordings retain their existing readable symbol sizes.

## Grid heads

Setting **2400410** on a grid controls the plan heads: 0 none, 1 start,
2 finish, 3 both. An absent or invalid setting means both. The grid's
**Heads (click)** property (**12611**) cycles these options transactionally.
The line reaches its endpoint when that endpoint has no head; it is shortened
by the head radius at a visible head. Grid coordinates and measurements remain
independent of this presentation setting.

## Custom sheet frames

A sheet may set `OpenBIM_Drawing.CustomFrame=true`. This suppresses the default
border, legend, title block and viewport captions. Place a separate view with
a frame/legend as an ordinary viewport on that sheet. The template view can
carry `OpenBIM_VectorTriangles` artwork; its layer is recorded independently
of model geometry. Views with every category hidden record only that reference
artwork, so model dimensions and elevation marks do not leak into templates.

A source-derived frame is static 2D artwork, not editable building geometry or
a model-derived legend. It must be described as such. Keep project-specific
artwork and source drawings in the private project directory.

## Verification

`paper_units` checks physical line widths, dimension offsets, tick geometry and
export density conversion. Existing `dimension_text` checks cover SVG/PDF
rotation and unchanged screen/member-tag behaviour. `grid_sheet` checks the
6 mm grid heads, endpoint property, single-head drawing, paper dash pattern and
custom-frame flag. Full application and project-level comparison remain
separate checks. A colour change or matching area alone does not establish
visual or geometric equivalence with a reference drawing.
