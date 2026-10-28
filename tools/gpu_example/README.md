# GPU-resident 3D view

A 3D view written in DynLex against libvulkan and GLFW directly. The model's
meshes are written once into GPU buffers. Each frame then only sets the camera's
parameters and issues one draw, so the frame's CPU time does not depend on the
model's size. No C runtime is in the rendering path; only libvulkan, GLFW and
the driver are.

| File | Contents |
| --- | --- |
| `viewer/vulkan/structs.dl` | The Vulkan structures in use, as DynLex classes with C layout |
| `viewer/vulkan/renderer.dl` | Window, swapchain, depth buffer, one pipeline, persistent vertex and index buffers, and the shaders' parameters in one storage buffer |
| `gpu_view.dl` | Loads the example house, a BIM-MESH import or the generated tower, and orbits it while reporting the frame time |
| `solid_vertex.dl`, `solid_fragment.dl` | Shaders for per-face vertices that carry a normal |
| `shared_vertex.dl`, `shared_fragment.dl` | Shaders for shared corners: the face's normal comes from screen-space derivatives of the position |

## The shader language extensions it needs

The shaders use four additions to DynLex's shader language. They are in the
compiler patch `dynlex-shader-extensions.patch`, kept beside this repository in
the workspace:
- `@intrinsic("shader input", "AttributeN")`: vertex inputs at locations 1 to 7;
- `@intrinsic("shader buffer read", binding, index)`: a float of a read-only
  storage buffer;
- `@intrinsic("shader sample", binding, u, v)`: a 2D texture, with the image at
  `binding` and its sampler at `binding + 1`;
- `@intrinsic("shader derivative x" / "y", value)`: how a value changes from
  pixel to pixel.

## Building and running

Build a compiler with the patch, then:

```sh
for stage in vertex fragment; do
  dynlex tools/gpu_example/shared_$stage.dl --emit-spirv --shader-stage=$stage -o build/gpu/shared_$stage.spv
  dynlex tools/gpu_example/solid_$stage.dl --emit-spirv --shader-stage=$stage -o build/gpu/solid_$stage.spv
done
build/dynlex tools/gpu_example/gpu_view.dl -O2 -o build/gpu/gpu_view
build/gpu/gpu_view --generate 390000 --shared --uncapped --frames 480
```

The options:
- `--import FILE.bimmesh` opens a model converted by
  `exchange/import/ifc_to_mesh.py`;
- `--generate N` builds the editor's imaginary tower;
- `--shared` stores shared corners;
- `--uncapped` presents without waiting for the display;
- `--frames N` stops after N frames.

## Measured

On an Intel UHD Graphics (CML GT2), in a 1280 × 820 window, uncapped:

| Model | Triangles | Vertices | Frames per second |
|---|---:|---:|---:|
| HITOS, per-face vertices | 371,598 | 1,114,794 | 184 |
| HITOS, shared corners | 371,598 | 181,795 | 305 |
| Generated tower, 392,700 walls, shared | 5,082,924 | 3,296,216 | 61 |
| Generated tower, 504,900 walls, shared | 6,535,188 | 4,237,992 | 54 |

The towers are drawn top storey first, so that seen from above the depth test
rejects the hidden faces before they are shaded. Drawn bottom first, the
392,700-wall tower ran at 52 fps.
