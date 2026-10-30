# Direct CSG fastener rendering probe

This isolated experiment tests a display path without tessellating a fastener
boundary. Pixel rays evaluate a signed implicit CSG field on the GPU. A screen
rectangle starts the fragment shader; its vertices describe the screen, not the
model. Bolt heads and nuts intersect hexagonal stock with an analytically rounded
cylinder. Nut and washer bores are subtracted volumes. Union combines the pieces.
`field.dl` supplies the same geometry to the GPU and the CPU geometry checks.

This is **not integrated into the Open BIM Studio model viewport**. It is not a
replacement CAD kernel, a validated rounded B-rep export or a fabrication model.
The existing rounded-rim B-rep Boolean operation is still unsupported. The probe
does not contain anchors, footplates, welds or HEA profiles.

Build from the repository root, with no other DynLex compiler running:

```sh
python3 tools/probes/analytic_fasteners/build.py --run
```

The script uses `DYNLEX_ROOT` or `.dynlex-root.local`, builds all required shaders
and the native viewer serially, and runs ten geometry checks. `spirv-val`, if
available through `PATH` or `SPIRV_VAL`, validates each compiled shader. Build
outputs and logs go under `build/fastener-components/analytic/`. The native viewer
must run with that repository as its working directory. The build script supplies
the compiler bootstrap library path where present.

Controls (the window must have keyboard focus):

| Input | Parameter |
| --- | --- |
| `[` / `]` | Catalogue diameter, M8–M40 |
| `+` / `-` | Pitch in 0.25 mm steps, from 0.5 to 6 mm |
| `W` | Assembly washers |
| `R` | Rounded head and nut rims |
| `V` | Helical thread lines |
| `A` | Material label: steel, stainless A2, stainless A4 |
| `F` | Finish label: uncoated, hot-dip zinc, electrolytic zinc |
| Right drag | Orbit |
| Mouse wheel | Zoom |

Each parameter change saves `current-fastener.csg` in the output directory. This
is an experimental parameter record, not a native BIM file; automatic loading is
not implemented. Seven positional command-line arguments can reproduce a state:
metric catalogue index, pitch in millimetres, material index, finish index,
washers flag, rounded rims flag, thread lines flag. The title reports the values.

Shaft length is five diameters. Rim radius is derived from head flats and height,
not an independent user setting. Material and finish labels are independent;
the simple shading is illustrative and does not model coating thickness,
material chemistry, strength, manufacturing tolerances or finish compatibility.
Thread marks follow the pitch analytically; they are lines, not cut helical teeth.

Ray marching uses at most 160 steps and a hit threshold of 0.001 shaft diameters.
Normals use finite differences. Thus there is no model tessellation, but display
accuracy still has numerical and pixel limits. Ten signed-volume sample checks
cover bores, retained material, rounded nut/head corners and shaft extent. These
are not a proof of B-rep validity or exhaustive visual regression coverage.

Validation on the pinned local compiler: ten checks pass; the fragment shader
passes SPIR-V validation; the native Vulkan process starts and remains alive.
A CPU render of the same field and shading was inspected. Native-window visual
inspection was unavailable in this session. The shader avoids `atan2`: this
compiler emits an unresolved function declaration for that GPU intrinsic; the
helix is evaluated with sine/cosine instead.

Reproduce the CPU preview without building a model mesh:

```sh
python3 tools/probes/analytic_fasteners/render_preview.py
```

This compiles the actual shared field and fragment shading for CPU evaluation at
660 by 480 pixels. It writes `render.ppm` (and `render.png` if Pillow is present).
This is a reference render, not a screenshot of the native application.
