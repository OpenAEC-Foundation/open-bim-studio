# Component renderer benchmark

Generate actual native object instances with six shared component definitions:

```sh
./build.sh probe component_benchmark
build/tools/component_benchmark 100000 build/components-100000.bim
OBS_MODEL_VIEW=1 OBS_PROFILE_FRAMES=1 build/open-bim-studio build/components-100000.bim
```

Counts from 0 to 1,000,000 are supported. Each 10,000 placements occupy one
storey; prototypes include a cube, brick, joist, precast panel, steel post and
four-part window frame. IDs remain independent and the file stores instances,
not copies of each definition. This benchmark deliberately has no systems,
openings, drawing annotations or reinforcement; the mixed systems showcase is
a separate workload.

Measure generation, opening, meshing, first presentation and moving-camera
frames separately. `OBS_FRAME` logs CPU and GPU times; report build flags,
GPU/driver, viewport size and presentation mode with results. Use an isolated
window for orbit automation. Never repurpose a maintainer's active model.
The generator's speed is not a renderer FPS result. 120 FPS requires a frame
budget of about 8.33 ms; report median and tail frame times rather than only
an average.
