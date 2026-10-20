# Interface icons

`ui-icons.txt` holds the editor's interface icons as coverage images at 16
and 22 pixels: one line per icon, size and part (glyph, size, part, then one
hex byte per pixel). The editor puts them in its glyph atlas at start and
colours them by its theme: part 0 in the text colour, part 1 in the accent.
Glyph numbers are the `bim icon ...` constants in `bim_ui.dl`.

The file is made by `tools/make_ui_icons.py` from the OpenAEC Style Repo
(commit bd8b453):

- General commands come from the B2 icon set (`design/icon-set-b2/svg`,
  filled outlines with a primary and an accent part, 16 and 24 pixel
  masters). B2 is the family the maintainer chose for the 0.4 style.
- Building elements (wall, floor, door, stair, ...) come from the BIM drafts
  (`design/icon-drafts/bim`, 1.75 pixel strokes on a 24 grid), because B2
  has no building icons yet. They are drafts, not approved designs; when B2
  gets building icons, the generator's table switches to them.

Licence: the Style Repo's designs are CC BY-SA 4.0 (the repository's
`LICENSE`); these rasterized icons are an adaptation under the same licence.
The Style Repo itself is a private repository of OpenAEC.

To regenerate after the Style Repo changes:

    python3 tools/make_ui_icons.py ~/Documenten/GitHub/OpenAEC-Style-Repo overlay/examples/bim-slice/icons/ui-icons.txt
