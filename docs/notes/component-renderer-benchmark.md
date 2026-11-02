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

An owned Xvfb window can be measured without touching an active project:

```sh
python3 tools/probes/orbit_components.py --binary build/open-bim-studio \
  --model build/components-100000.bim --out build/orbit-100000 --seconds 20
```

The helper fits the model, orbits with actual right-button input, retains before
and after screenshots and raw samples, and checks the source file hash and undo
count. Inspect the screenshots before accepting a run: builds predating the
component fit correction leave component-only models close to the origin.
Samples cover the moving-camera interval, excluding the final settling period.

For an explicit rendering-throughput measurement use `OBS_UNCAPPED=1`. The
native context selects IMMEDIATE when the surface advertises it, otherwise
MAILBOX, otherwise FIFO. The normal editor keeps FIFO. `OBS_RENDERER` reports
the actual GPU, device kind and selected Vulkan present mode (0 immediate,
1 mailbox, 2 FIFO); `OBS_FRAME` also records the active tab kind. Xvfb results
must not be treated as a refresh-rate measurement on the maintainer's desktop.

Collect multiple retained runs into a compact table without losing their raw
samples:

```sh
python3 tools/probes/report_component_orbits.py \
  build/orbit-100000/results.json build/orbit-250000/results.json \
  --output build/component-orbit-report.md
```

The report retains model/binary hashes and peak process RSS, and explicitly
labels legacy runs with missing device or FPS metadata. Review fitted before
and after images; a table alone does not establish which geometry was visible.

## Desktop presentation and process-local motion

Xvfb can select a different physical device and presentation path from the real
X11/XWayland desktop. Always compare the reported device, not just the model
count. The product context now prefers a discrete GPU when it has a graphics
queue capable of presenting to the window; integrated and software devices
remain fallbacks, and standard Vulkan loader filters can restrict the choice.

For an owned desktop window, install the diagnostic `python-xlib` and Pillow
dependencies in a development environment, then build the optional Linux shim:

```sh
cc -std=c11 -O2 -Wall -Wextra -shared -fPIC tools/probes/orbit_input_shim.c \
  -ldl -lm -o build/orbit-input.so
OBS_UNCAPPED=1 python3 tools/probes/orbit_components.py --desktop \
  --internal-orbit-lib build/orbit-input.so --binary build/open-bim-studio \
  --model build/components-100000.bim --out build/desktop-100000 --seconds 20 \
  --build-note 'record the source commit and actual compiler flags here'
```

The shim changes returned cursor coordinates/right-button state only inside the
new test process for a finite interval. It still performs the real GLFW queries.
It never moves the desktop pointer or sends global mouse/keyboard events.
The owned client is identified by its PID; screenshots contain that client.
The shim is copied into each evidence directory and its hash is retained.
It is a diagnostic tool and is not linked into the application. `stdbuf` is
not used for this mode because it replaces the diagnostic preload; the shim
sets line buffering itself.

The recorded 1440 by 900 size is the client framebuffer, including the ribbon
and properties. Raw `OBS_HOST` samples additionally distinguish command-buffer
recording from the host call to queue presentation. Frame preparation includes
waiting for the preceding GPU frame and acquiring an image, so `cpu_us` is not
a pure active-CPU measurement. GPU timestamps exclude presentation/compositor
work; submitted FPS is not monitor refresh rate.

`--save-copy` is limited to the isolated Xvfb surface. It saves through the
native editor to a new IFCXB destination and refuses an existing destination.
`--keep-open` is available for desktop handoff and leaves a marker preventing
that evidence directory from being reused against a user's working window.
