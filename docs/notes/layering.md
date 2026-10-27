# Layering: the import direction between units

`scripts/check-layers.sh` enforces the direction of the design
(`docs/superpowers/specs/2026-10-27-restructuring-design.md` §5): kernel →
kernel, lib; model → model, kernel, lib; formats and graphics → themselves,
each other, model, kernel, lib; editor → editor, graphics, formats, model,
kernel, lib and app. The application, automation, tests and tools import
anything. The script prints every forbidden edge and exits non-zero.

## Repaired in stage 1 (2026-10-27)

- `bim_section_gpu` imported the view panel: moved to `app/`.
- `bim_drawing_rules` and `bim_images` imported the editor: moved to `editor/`.
- `bim_clash` imported the scene, and `bim_schedule` imports clash: both moved
  to `graphics/`.
- The GPU example imported the editor: moved to `tools/gpu_example/`.
- The scene mesh record, the category colouring, the id base of imported
  elements and the triangulation of a free mesh moved from the scene to
  `model/bim_mesh.dl`, so the importers and the IFC writers no longer depend on
  the scene for those. `bim_import` keeps importing the scene all the same:
  the readers built on it (`bim_ifc_read`, `bim_ifcx_read`, `bim_ifc_promote`,
  `bim_ifc_native`) and their tests use scene helpers such as `the bim metres
  text of` through that import, and a smaller closure silently removes
  definitions a pattern call needs (found by the final review). Cutting the
  edge needs every such call listed first; the compiler is the only tool that
  finds them.
- `bim_steel_profiles` imported the `.bim` reader for the real and whole
  number readers: those moved to `model/bim_readings.dl`.

## Left, by design

- `formats/bim_ifcx.dl` and `formats/bim_ifc.dl` import `graphics/bim_scene.dl`:
  the IFCX writer tessellates the evaluation through the scene builder (`the
  bim scene meshes of … layered true`), and the IFC writer shapes linear
  members through the scene's `the bim linear shape of … cut by …`. The
  direction formats → graphics is allowed today; cutting formats as its own
  unit (design §10, stage 6) first needs that tessellation and shaping below
  the scene, in the model or the kernel seam.
- The nine editor → app imports the design leaves (`bim_api`, `bim_grid_controls`,
  `bim_model_explorer`, `bim_modify_options`, `bim_modify_preview`,
  `bim_type_manager`, `bim_ui_files` import `app/bim_ui.dl`, `bim_plan_panel.dl`
  or `bim_view_panel.dl`): editor and app are one unit.
