# GPU paths — how six engines move geometry to the GPU, and what the kernel must emit

**Decision question:** what buffer layout, instancing scheme and camera-relative packing should the
kernel's `gpu` module produce so that geometry uploads without repacking — and exactly what does the
DynLex graphics runtime provide today, what is missing, and which of the missing pieces are `ui/`
work rather than kernel work?

**Serves:** kernel spec §3 ("read and write with Vulkan"), §5 (GPU precision), §6 item 4 (GPU compute
in SPIR-V), §7 (`gpu/` module), §8 (required DynLex extensions); ADR-0004 design rationale
("kernel-owned GPU buffer layouts, compute in SPIR-V"); ADR-0006 row "camera-relative f32 is
sufficient on the GPU"; `../kernels/problems.md` P-05, P-07, P-18, P-27, P-28

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> This is a **source-and-documentation note**. Nothing in it is *measured*: no program was run, no
> frame was timed. The DynLex compiler is not built in this working copy, so no DynLex program could
> be executed to observe the runtime's behaviour; every DynLex claim below is read from the source at
> the pinned commit and labelled *source*, and the two arithmetic results are labelled *inferred*
> with the arithmetic shown. The measured half — frame times, draw-call cost, upload cost — belongs to
> a later spike and is named in §Risks.

---

## Summary

The DynLex graphics runtime is a **single-layout immediate-mode triangle submitter**: one interleaved
36-byte vertex (`float position[3]`, `float texture_coordinates[2]`, `float color[4]`), appended one
vertex at a time through an FFI call into a 32 MiB per-frame host-visible arena that is reset every
frame, drawn with `vkCmdDraw(count, 1, 0, 0)` under a single `mat4` push constant. It has **no index
buffer, no instancing, no storage buffer, no compute pipeline, no GPU→CPU readback, and no f64
anywhere** — and the compiler's SPIR-V backend emits only `Vertex` and `Fragment` entry points, so
spec §6 item 4's "DynLex compute kernels in `gpu/`" cannot be compiled today. Under the current API a
scene of 10⁵ boxes does not merely cost 10⁵ draw calls; it **cannot be drawn at all**, because 10⁵
boxes need 129.6 MB of transient vertex data against a 32 MiB per-frame ceiling.

The five mature engines agree closely on what the kernel should emit — interleaved f32 vertex
attributes, a `u32` index buffer, and a separate instance-rate buffer carrying a 3×`vec4` transposed
affine transform plus an element id — and they disagree only on how far they have taken GPU-driven
submission. On camera-relative rendering the field splits sharply: **OCCT and Filament both implement
it and both do the f64 subtraction on the CPU at object granularity**, while Blender, bevy and
three.js do not implement it at all and say so on their trackers. That split, not a measurement, is
the evidence for ADR-0006's row.

## What was read, and at which commit

| Source | Pin | What was read |
|---|---|---|
| **DynLex graphics runtime** | [`7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd`](https://github.com/OpenAEC-Foundation/dynlex/tree/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd) (`master`) | `src/runtime/graphicsRuntime{,Vulkan,Pipeline,Draw,Texture}.c`, `graphicsRuntime.h`, `graphicsRuntimeInternal.h`, `graphicsBuiltinShaders.h`, `src/runtime/shaders/*.spvasm`, `lib/{graphics,shader,texture,matrix,vector}.dl`, `lib/models/obj.dl`, `src/cpp/main.cpp`, `src/cpp/compiler/parseContext.h`, `src/cpp/compiler/codegen/spirv.cpp`, `src/cpp/compiler/compileTimeValue.cpp`, `tests/games/{three_dimensional,city_flyover}.dl`, `tests/games/model/viewer.dl` |
| **Blender** | [`a37564c4df7a9b604809e5192918400e46a0205f`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f) — the same pin [`../kernels/blender.md`](../kernels/blender.md) uses | `source/blender/draw/intern/draw_command_shared.hh`, `draw_shader_shared.hh`, `source/blender/gpu/intern/gpu_select*.cc` |
| **OCCT** | `V8_0_1` = [`b8f597c677811d1f9f4d8a97f5ae2825c0353a42`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42) — the pin [`../kernels/occt.md`](../kernels/occt.md) uses | `src/Visualization/TKService/Graphic3d/`, `src/Visualization/TKOpenGl/OpenGl/`, `src/Visualization/TKV3d/SelectMgr/` |
| **wgpu** | `wgpu-v29.0.1` = [`923b896955655600c38ac93d6e9ae26845682f80`](https://github.com/gfx-rs/wgpu/tree/923b896955655600c38ac93d6e9ae26845682f80) | `wgpu-types/src/{buffer,vertex,features}.rs` |
| **bevy** | `v0.19.1` = [`b56fc29d3016e641754765244b5ba3f9cc504671`](https://github.com/bevyengine/bevy/tree/b56fc29d3016e641754765244b5ba3f9cc504671) | `crates/bevy_mesh/src/{mesh,index}.rs`, `crates/bevy_render/src/batching/gpu_preprocessing.rs`, `crates/bevy_pbr/src/render/{mesh.rs,mesh_preprocess.wgsl,build_indirect_params.wgsl}`, `crates/bevy_transform/src/components/transform.rs` |
| **Filament** | `v1.76.1` = [`65eaf091d7236b64094c59354c8632a86b911f92`](https://github.com/google/filament/tree/65eaf091d7236b64094c59354c8632a86b911f92) | `filament/include/filament/{TransformManager,RenderableManager,VertexBuffer,View}.h`, `filament/src/details/{Camera,Scene}.{h,cpp}` |
| **three.js** | `r186` = [`148ef33ecb6d2502ff796d4554abd1549c95d519`](https://github.com/mrdoob/three.js/tree/148ef33ecb6d2502ff796d4554abd1549c95d519) | `src/objects/{InstancedMesh,BatchedMesh}.js`, `src/math/Matrix4.js`, `src/renderers/webgl/WebGLUniforms.js` |
| **three-mesh-bvh** | `v0.9.15` = [`6f4964b7ac00c1ae1ec768615dc434b55c0401e2`](https://github.com/gkjohnson/three-mesh-bvh/tree/6f4964b7ac00c1ae1ec768615dc434b55c0401e2) | `src/core/{MeshBVH,Constants}.js`, `README.md` |
| **That Open fragments** | `v3.4.0` = [`daf08b4885d6feee1b1bf9eee5093a42ceffff04`](https://github.com/ThatOpen/engine_fragment/tree/daf08b4885d6feee1b1bf9eee5093a42ceffff04) | `packages/fragments/src/FragmentsModels/src/model/{coordinates-manager,raycast-manager}.ts`, `src/lod/lod-helper.ts` |
| **CesiumJS** | `1.145` = [`7f17be4c05c0cc2f4bc6405f16ce521f620b0112`](https://github.com/CesiumGS/cesium/tree/1.145) | `packages/engine/Source/Core/EncodedCartesian3.js`, `packages/engine/Source/Shaders/Builtin/Functions/translateRelativeToEye.glsl` |

`git status` in the DynLex working copy reports `src/runtime/`, `src/cpp/compiler/codegen/`,
`tests/games/` and every `lib/*.dl` file read here as **unmodified** at that commit; the working
copy's unrelated modifications (`.gitignore`, `lib/config.dl`, four compiler type-inference files)
touch nothing cited below.

---

## The comparison, in three parts

One comparison, split across three tables because thirteen criteria against six paths does not fit
one readable row. **Every cell is *source* — read in the file linked — unless it is marked
*claimed* (the project's own documentation) or *inferred* (reasoning shown in this note).**

### A — Geometry submission

| Path | Vertex layout | Index buffers | Instancing | Dynamic geometry |
|---|---|---|---|---|
| **DynLex runtime** | One interleaved 36-byte f32 vertex: `position[3]`, `texture_coordinates[2]`, `color[4]` ([`graphicsRuntimeInternal.h#L17-L21`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L17-L21)), bound as three attributes at locations 0/1/2 ([`graphicsRuntimePipeline.c#L51-L76`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L51-L76)). A second, 16-byte position-only layout exists for custom pipelines and is reachable only through the fullscreen quad | **None** — grep §The absence list | **None** — `vkCmdDraw(…, 1, 0, 0)`, instance count literal 1 ([`graphicsRuntimeDraw.c#L212`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L212)) | Everything is dynamic: the arena resets every frame ([`graphicsRuntimeDraw.c#L71`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L71)), so static geometry costs the same as changing geometry |
| **Blender** | 29 single-purpose extractors, one per buffer; positions `SFLOAT_32_32_32` **per face corner** — see [`../kernels/blender.md`](../kernels/blender.md) §The GPU module, not repeated here | Yes (`extract_mesh_ibo_*`, 7 extractors — same section) | Yes, and GPU-driven: `DrawPrototype { group_id, res_index, custom_id, instance_len }` is "converted into `DrawCommand` on GPU after visibility and compaction" ([`draw_command_shared.hh#L85-L99`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/draw_command_shared.hh#L85-L99)) | Per-object extractor re-run; usage hints `GPU_USAGE_STREAM/STATIC/DYNAMIC/DEVICE_ONLY` (blender.md §The GPU module) |
| **OCCT** | `Graphic3d_Buffer` of typed attributes; every float type is 32-bit (`Graphic3d_TOD_VEC2/VEC3/VEC4`, [`Graphic3d_Buffer.hxx#L28-L47`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_Buffer.hxx#L28-L47)); `SetVertice(int, const gp_Pnt&)` casts the f64 point to three floats ([`Graphic3d_ArrayOfPrimitives.hxx#L357-L360`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_ArrayOfPrimitives.hxx#L357-L360)) | Yes — `Graphic3d_IndexBuffer` ([`Graphic3d_IndexBuffer.hxx#L20-L25`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_IndexBuffer.hxx#L20-L25)) | **None in the render path.** `OpenGl_PrimitiveArray` calls only `glDrawArrays`/`glDrawElements` ([`OpenGl_PrimitiveArray.cxx#L499-L538`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_PrimitiveArray.cxx#L499-L538)); `glVertexAttribDivisor` appears only in loader tables — grep §The absence list. `OpenGl_Structure::myInstancedStructure` renders its child once with the parent's transform ([`OpenGl_Structure.cxx#L364-L366`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_Structure.cxx#L364-L366)) — structure sharing, not hardware instancing | VBO rebuild per primitive array (`myIsVboInit`, [`OpenGl_PrimitiveArray.cxx#L944-L953`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_PrimitiveArray.cxx#L944-L953)) |
| **wgpu / bevy** | `Mesh::ATTRIBUTE_POSITION` = `Float32x3`, `_NORMAL` = `Float32x3`, `_UV_0` = `Float32x2`, `_TANGENT`/`_COLOR` = `Float32x4` ([`mesh.rs#L267-L318`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_mesh/src/mesh.rs#L267-L318)) | `Indices::U16 \| U32` ([`index.rs#L86-L88`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_mesh/src/index.rs#L86-L88)); `BufferUsages::INDEX` ([`buffer.rs#L83`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/buffer.rs#L83)) | `VertexStepMode::{Vertex, Instance}` ([`vertex.rs#L72-L78`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/vertex.rs#L72-L78)); bevy goes further — a compute shader builds `IndirectParametersIndexed { index_count, instance_count, first_index, base_vertex, first_instance }` ([`gpu_preprocessing.rs#L774-L791`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_render/src/batching/gpu_preprocessing.rs#L774-L791)) consumed by `multi_draw_indexed_indirect_count` ([`mesh.rs#L4532`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh.rs#L4532)) | Slab-allocated vertex/index buffers with `base_vertex`/`first_index` offsets (same struct) |
| **Filament** | `Builder::attribute(VertexAttribute, bufferIndex, AttributeType, byteOffset, byteStride)` — explicit interleaving, multiple buffers ([`VertexBuffer.h#L139-L141`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/VertexBuffer.h#L139-L141)) | Yes (`IndexBuffer`) | Yes — `Builder::instances(size_t)`, clamped 1…32767, all instances sharing one bounding box ([`RenderableManager.h#L577-L590`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/RenderableManager.h#L577-L590)), or an `InstanceBuffer` of per-instance transforms — but that overload is capped at `Engine::getMaxAutomaticInstances()`, documented as "64 on most platforms" ([`#L592-L617`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/RenderableManager.h#L592-L617)) | `setBufferAt` on an existing `VertexBuffer` (*claimed*, API documentation) |
| **three.js / That Open** | `BufferGeometry` attributes, `Float32Array` throughout | Yes (`BufferGeometry.index`) | `InstancedMesh.instanceMatrix = new InstancedBufferAttribute(new Float32Array(count*16), 16)` ([`InstancedMesh.js#L57`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/objects/InstancedMesh.js#L57)); `BatchedMesh` adds a multi-draw list ([`BatchedMesh.js#L33`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/objects/BatchedMesh.js#L33)). That Open hangs an `itemFilter` `InstancedBufferAttribute` of `Uint8Array` per instance for per-element visibility ([`lod-helper.ts#L200-L212`](https://github.com/ThatOpen/engine_fragment/blob/daf08b4885d6feee1b1bf9eee5093a42ceffff04/packages/fragments/src/FragmentsModels/src/lod/lod-helper.ts#L200-L212)) | Per-attribute `needsUpdate` dirty flags (*claimed*, API documentation) |

### B — Compute, readback and picking

| Path | Compute dispatch | Storage buffers | GPU→CPU readback | Picking method |
|---|---|---|---|---|
| **DynLex runtime** | **None** (grep) — and the compiler emits no compute stage: `enum class ShaderStage { Fragment, Vertex }` ([`parseContext.h#L65`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/compiler/parseContext.h#L65)), `executionModel = isVertex ? 0 : 4` ([`spirv.cpp#L642-L644`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/compiler/codegen/spirv.cpp#L642-L644)), CLI `--shader-stage=vertex\|fragment` ([`main.cpp#L42`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/main.cpp#L42), [`#L250-L255`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/main.cpp#L250-L255)) | **None** (grep). Shader inputs are 32 scalar floats in uniform buffers ([`graphicsRuntimeInternal.h#L13`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L13), [`graphicsRuntimeDraw.c#L277-L284`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L277-L284)) plus one `mat4` push constant | **None** (grep). The only transfer in the runtime is CPU→GPU, buffer→image for textures, and it stalls the whole queue: `vkQueueWaitIdle` after every texture upload ([`graphicsRuntimeVulkan.c#L859-L884`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L859-L884)) | **None.** No id attribute, no id buffer, no readback |
| **Blender** | Yes — the GPU module exposes `StorageBuf` and the draw manager declares a `DispatchCommand` ([`draw_shader_shared.hh#L23`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/draw_shader_shared.hh#L23)) | Yes (`StorageBuf`, blender.md §The GPU module) | Only identity: `GPUSelectResult { id; depth }` (blender.md §The GPU module) | Three GPU algorithms — occlusion query, depth-buffer pick, and a dedicated Select-Next draw engine ([`gpu_select.cc#L26-L40`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/intern/gpu_select.cc#L26-L40), [`gpu_select_next.cc#L1-L36`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/gpu/intern/gpu_select_next.cc#L1-L36)) |
| **OCCT** | Not in the GL visualisation path read | Not in the path read | Not in the path read | **CPU BVH.** `SelectMgr_ViewerSelector` builds and traverses BVH trees over sensitive entities, and a dedicated build thread pool ([`SelectMgr_ViewerSelector.hxx#L20-L21`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKV3d/SelectMgr/SelectMgr_ViewerSelector.hxx#L20-L21) includes `SelectMgr_BVHThreadPool.hxx`; the traversal is described at [`#L74-L80`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKV3d/SelectMgr/SelectMgr_ViewerSelector.hxx#L74-L80) and the builder at [`#L174-L180`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKV3d/SelectMgr/SelectMgr_ViewerSelector.hxx#L174-L180)); one tree per transform-persistence subset so a camera change rebuilds only the affected tree ([`SelectMgr_SelectableObjectSet.hxx#L23-L46`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKV3d/SelectMgr/SelectMgr_SelectableObjectSet.hxx#L23-L46)) |
| **wgpu / bevy** | Yes — `@compute @workgroup_size(64)` mesh preprocessing that "expands each `MeshInputUniform` out to a full `MeshUniform` … performs frustum culling and occlusion culling" ([`mesh_preprocess.wgsl#L1-L15`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh_preprocess.wgsl#L1-L15), [`#L157-L158`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh_preprocess.wgsl#L157-L158)) and a second pass building the indirect parameters ([`build_indirect_params.wgsl#L53-L54`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/build_indirect_params.wgsl#L53-L54)) | `BufferUsages::STORAGE`, `INDIRECT` ([`buffer.rs#L89-L91`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/buffer.rs#L89-L91)) | `BufferUsages::MAP_READ` + `COPY_SRC` ([`buffer.rs#L69-L78`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/buffer.rs#L69-L78)) — the standard async `map_async` path | Not fixed by wgpu; bevy's picking crates were outside the directories read here, so **unknown** from this note's sources |
| **Filament** | Not established in the headers read — **unknown** | Not established in the headers read — **unknown** | Yes — `View::pick` is asynchronous with a callback ([`View.h#L890-L897`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/View.h#L890-L897)) | **GPU id buffer.** `PickingQueryResult { Entity renderable; float depth; }`, depth "1 (near plane) to 0 (infinity)", with the documented caveat that "`pick()` has some latency" ([`View.h#L846-L862`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/View.h#L846-L862)) |
| **three.js / That Open** | WebGPU backend only (*claimed*; only `src/renderers/webgl` was read) | WebGPU backend only (*claimed*, same scope) | `WebGLRenderer.readRenderTargetPixelsAsync` ([`WebGLRenderer.js#L3216`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/renderers/WebGLRenderer.js#L3216)) | **CPU.** That Open runs `THREE.Raycaster` ([`raycast-manager.ts#L20`](https://github.com/ThatOpen/engine_fragment/blob/daf08b4885d6feee1b1bf9eee5093a42ceffff04/packages/fragments/src/FragmentsModels/src/model/raycast-manager.ts#L20)) behind its own bounding-box broad phase; the ecosystem's accelerator is `three-mesh-bvh`, a BVH over `BufferGeometry` with CENTER/AVERAGE/SAH splits ([`Constants.js#L9-L29`](https://github.com/gkjohnson/three-mesh-bvh/blob/6f4964b7ac00c1ae1ec768615dc434b55c0401e2/src/core/Constants.js#L9-L29)) that replaces `Mesh.prototype.raycast` ([`README.md#L100-L110`](https://github.com/gkjohnson/three-mesh-bvh/blob/6f4964b7ac00c1ae1ec768615dc434b55c0401e2/README.md#L100-L110)) |

### C — Precision, view and reach

| Path | Camera-relative rendering | Matrix precision reaching the GPU | Depth | Capped clipping | Line rendering | Platform reach / maturity |
|---|---|---|---|---|---|---|
| **DynLex runtime** | **No.** Camera and model translations are taken as `double` and cast to `float` immediately ([`graphicsRuntime.c#L412-L436`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntime.c#L412-L436)) | f32 end to end: `float projection[16]; float camera[16]; float model[16]` ([`graphicsRuntimeInternal.h#L119-L123`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L119-L123)), collapsed to one MVP push constant ([`graphicsRuntimeDraw.c#L198-L205`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L198-L205)); the built-in vertex shader is `OpTypeFloat 32` only ([`color.vert.spvasm#L15-L20`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/shaders/color.vert.spvasm#L15-L20)) | `D32_SFLOAT` preferred, then `D24_UNORM_S8_UINT`, then `D16_UNORM` ([`graphicsRuntimeVulkan.c#L321-L330`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L321-L330)); **forward Z, not reversed** — clear 1.0 ([`graphicsRuntimeDraw.c#L47-L50`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L47-L50)), `VK_COMPARE_OP_LESS` ([`graphicsRuntimePipeline.c#L98-L103`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L98-L103)), projection `[10] = far/(near−far)` ([`graphicsRuntime.c#L399-L405`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntime.c#L399-L405)). Custom pipelines get no depth test at all ([`graphicsRuntimePipeline.c#L424-L426`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L424-L426)) | None | None — topology is `TRIANGLE_LIST` for built-ins and `TRIANGLE_STRIP` for custom pipelines ([`graphicsRuntimePipeline.c#L203-L206`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L203-L206), [`#L424-L426`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L424-L426)); `lineWidth` fixed at 1.0 ([`#L87-L93`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L87-L93)) | Vulkan 1.3 loader required ([`graphicsRuntimeVulkan.c#L96-L102`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L96-L102), [`#L160-L167`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L160-L167)); desktop + MoltenVK via portability; **no device feature is requested at all** — `VkDeviceCreateInfo` has no `pEnabledFeatures` and one extension ([`#L301-L308`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L301-L308)); FIFO present only ([`#L440-L455`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L440-L455)). One maintainer |
| **Blender** | **No.** `ObjectMatrices { float4x4 model; float4x4 model_inverse; }` and `ViewMatrices { float4x4 viewmat; … }` ([`draw_shader_shared.hh#L119-L142`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/draw_shader_shared.hh#L119-L142)); object storage is `float loc[3]` (blender.md §Precision) and positions upload float32 "with no camera-relative rebasing" (blender.md §The GPU module) | f32 | Not established in the files read — **unknown** | Yes — viewport clipping regions (*claimed*, user-facing feature; not traced to source here) | Yes, extensive (*claimed*; the freestyle and overlay engines were not read) | GPL-3.0; `opengl/`, `vulkan/`, `metal/`, `dummy/` backends; very large community — see [`../kernels/blender.md`](../kernels/blender.md) §Evaluation and §The GPU module |
| **OCCT** | **Yes — and it is the fullest implementation read.** A Z-layer carries a `gp_XYZ` origin ([`Graphic3d_ZLayerSettings.hxx#L57-L68`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_ZLayerSettings.hxx#L57-L68)); the world-view matrix is translated by it **in `NCollection_Mat4<double>`** and only then converted to float ([`OpenGl_LayerList.cxx#L642-L663`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_LayerList.cxx#L642-L663)); `SetLocalOrigin` is documented as "Setup local camera transformation for compensating float precision issues" ([`OpenGl_ShaderManager.hxx#L53-L61`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_ShaderManager.hxx#L53-L61)) and clip-plane equations are re-based through it ([`#L63-L70`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_ShaderManager.hxx#L63-L70)) | Camera keeps both: `TransformMatrices<double> myMatricesD` and `<float> myMatricesF` ([`Graphic3d_Camera.hxx#L815-L816`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_Camera.hxx#L815-L816)); the GL context stores `OpenGl_MatrixState<float>` for model-world, world-view and projection ([`OpenGl_Context.hxx#L1097-L1099`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_Context.hxx#L1097-L1099)) | Selectable `[0,1]` or `[-1,1]` range (`IsZeroToOneDepth`, [`Graphic3d_Camera.hxx#L397-L405`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_Camera.hxx#L397-L405), [`#L791`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKService/Graphic3d/Graphic3d_Camera.hxx#L791)) | **Yes — the only candidate with capping built in**: `OpenGl_CappingAlgo`, `OpenGl_CappingPlaneResource`, `Graphic3d_ClipPlane` | Yes — `Graphic3d_ArrayOfSegments`, `Graphic3d_ArrayOfPolylines` in the same directory; hidden-line removal lives outside `Visualization/` (*claimed*) | LGPL-2.1-with-exception; `TKOpenGl`, `TKOpenGles`, `TKD3DHost` toolkits present at the tag — see [`../kernels/occt.md`](../kernels/occt.md) for licence and maintenance evidence |
| **wgpu / bevy** | **No.** `Transform.translation: Vec3` (f32) ([`transform.rs#L86-L92`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_transform/src/components/transform.rs#L86-L92)); `MeshUniform.world_from_local: [Vec4; 3]` ([`mesh.rs#L514-L518`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh.rs#L514-L518)). A maintainer states the constraint on the tracker — §Known problems. Third-party `big_space` supplies an integer grid + floating origin, *claimed* "Enough precision to render proton-sized meshes across the observable universe" ([`README.md#L15-L24`](https://github.com/aevyrie/big_space/blob/06c66a77f00f60bb8ab3792797b14110fe63efde/README.md#L15-L24)) | f32; wgpu offers `Features::SHADER_F64` and `VERTEX_ATTRIBUTE_64BIT` but documents f64 as "frequently between 16 and 64 _times_ slower" ([`features.rs#L1054-L1064`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/features.rs#L1054-L1064)), and even `VertexFormat::Float64x3` is delivered to the shader as `vec3<f32>` ([`vertex.rs#L192-L199`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/vertex.rs#L192-L199)) | Reverse-Z — the mesh pipeline is built with `depth_compare: CompareFunction::GreaterEqual` ([`mesh.rs#L3640`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh.rs#L3640)) | Application-level (*inferred*: nothing in the directories read provides it) | Application-level (*inferred*, same scope) | Vulkan/Metal/DX12/GL/WebGPU; MIT/Apache-2.0 (*claimed*, project documentation) |
| **Filament** | **Yes, opt-in.** `TransformManager::setAccurateTranslationsEnabled` — "the translation component of all transforms is maintained at double precision", disabled by default ([`TransformManager.h#L167-L189`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/TransformManager.h#L167-L189)). Scene preparation composes the f64 world transform with each object's accurate transform and truncates once, under the comment "this is where we go from double to float for our transforms" ([`Scene.cpp#L217-L226`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/src/details/Scene.cpp#L217-L226)) | `CameraInfo` keeps `mat4f projection/model/view` and `mat4 worldTransform` (f64) ([`Camera.h#L232-L257`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/src/details/Camera.h#L232-L257)) | Reversed-Z ([`View.h#L846-L850`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/View.h#L846-L850); [`PostProcessManager.cpp#L1736`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/src/PostProcessManager.cpp#L1736)) | No built-in section capping found in the public API read | Not a technical-drawing renderer (*inferred* from the public API read) | Apache-2.0; Vulkan/Metal/GL/WebGL; Google-maintained (*claimed*, project documentation) |
| **three.js / That Open** | **No.** `Matrix4.elements` is a plain JS array — IEEE-754 double on the CPU ([`Matrix4.js#L86-L91`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/math/Matrix4.js#L86-L91)) — but every matrix uniform is copied into a `Float32Array` before upload ([`WebGLUniforms.js#L68-L70`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/renderers/webgl/WebGLUniforms.js#L68-L70), [`#L329-L352`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/renderers/webgl/WebGLUniforms.js#L329-L352)). That Open's answer is one per-model coordination matrix, a plain `THREE.Matrix4` ([`coordinates-manager.ts#L4-L42`](https://github.com/ThatOpen/engine_fragment/blob/daf08b4885d6feee1b1bf9eee5093a42ceffff04/packages/fragments/src/FragmentsModels/src/model/coordinates-manager.ts#L4-L42)) — a single static origin shift, not a camera-relative one | f32 on the GPU | `logarithmicDepthBuffer` option, *claimed* "necessary if dealing with huge differences in scale in a single scene" ([`WebGLRenderer.js#L3699`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/renderers/WebGLRenderer.js#L3699)) | `ClippingGroup`, no capping | `Line`, `LineSegments`, `LineLoop` in `src/objects/`; wide lines as an add-on (*claimed*) | Browser (WebGL + WebGPU); MIT (*claimed*, project documentation) |

---

## The DynLex graphics runtime in detail

### What it accepts, and how it uploads

There is one vertex type and it is not negotiable from DynLex code. `DynlexGraphicsVertex` is
`float position[3]; float texture_coordinates[2]; float color[4]` — 36 bytes interleaved
([`graphicsRuntimeInternal.h#L17-L21`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L17-L21)).
Each frame owns a 32 MiB `HOST_VISIBLE | HOST_COHERENT` buffer created with
`VK_BUFFER_USAGE_VERTEX_BUFFER_BIT` **only**, permanently mapped at startup
([`graphicsRuntimeVulkan.c#L687-L698`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L687-L698)),
and there are two frames in flight
([`graphicsRuntimeInternal.h#L12-L15`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L12-L15)).

Upload is a bump allocator: `append_vertex_3d` truncates three doubles to float, `memcpy`s 36 bytes
at `upload_offset`, and advances
([`graphicsRuntimeDraw.c#L167-L188`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L167-L188)).
`begin_frame` sets `frame->upload_offset = 0`
([`graphicsRuntimeDraw.c#L71`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L71)),
so **every vertex of every object is re-submitted every frame**. There is no persistent, device-local
geometry buffer of any kind. This is exactly what the shipped viewer does: `lib/models/obj.dl` walks
the triangle list and issues three `add a vertex` FFI calls per triangle, per frame
([`obj.dl#L446-L458`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/lib/models/obj.dl#L446-L458),
[`#L548-L561`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/lib/models/obj.dl#L548-L561)),
and breaks the draw only when the bound texture changes
([`obj.dl#L538-L546`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/lib/models/obj.dl#L538-L546)).

### What it draws

`record_triangles` selects one of four built-in pipelines (textured × depth), binds the arena at the
stream's start offset, pushes `projection × camera × model` as one 64-byte `mat4` push constant, and
calls `vkCmdDraw(vertex_count, 1, 0, 0)`
([`graphicsRuntimeDraw.c#L194-L214`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L194-L214)).
One `start triangles … finish triangles` pair is one draw call. `city_flyover.dl` draws each building
box as its own pair
([`city_flyover.dl#L66-L78`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/tests/games/city_flyover.dl#L66-L78)),
which is the API's intended shape.

### The absence list — the rule, and the output

*Rule:* `grep -rn "<token>" src/runtime/` in the DynLex working copy at `7cacbc9`, counting matching
lines. *Output for all sixteen tokens*, reproduced in full and set in two columns only to fit the
page — no token is omitted and no count is edited:

```
vkCmdDispatch : 0                        VK_BUFFER_USAGE_INDEX_BUFFER_BIT : 0
vkCreateComputePipelines : 0             VK_BUFFER_USAGE_STORAGE_BUFFER_BIT : 0
VK_PIPELINE_BIND_POINT_COMPUTE : 0       VK_DESCRIPTOR_TYPE_STORAGE_BUFFER : 0
VK_SHADER_STAGE_COMPUTE_BIT : 0          VK_VERTEX_INPUT_RATE_INSTANCE : 0
vkCmdBindIndexBuffer : 0                 vkCmdCopyImageToBuffer : 0
vkCmdDrawIndexed : 0                     vkCmdCopyBuffer : 1   (→ vkCmdCopyBufferToImage, line 863)
vkCmdDrawIndirect : 0                    VK_BUFFER_USAGE_TRANSFER_DST_BIT : 0
shaderFloat64 : 0                        VK_FORMAT_R64 : 0
```

The single `vkCmdCopyBuffer` hit is the substring inside `vkCmdCopyBufferToImage` at
[`graphicsRuntimeVulkan.c#L863`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L863) —
CPU→GPU, not readback. Widening the rule to the whole repository
(`grep -rn "vkCmdDispatch\|ComputePipeline" --include=*.c --include=*.h --include=*.cpp --include=*.dl src/ lib/`)
returns zero compute hits; the only line containing the word is an unrelated comment in
`src/cpp/compiler/type.h`.

### The arithmetic for 10⁵ objects — *inferred*

A `city_flyover` box is six quadrilaterals, twelve triangles, 36 vertices
([`city_flyover.dl#L35-L45`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/tests/games/city_flyover.dl#L35-L45),
[`#L66-L78`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/tests/games/city_flyover.dl#L66-L78)).
At 36 bytes per vertex:

- **Per-frame arena ceiling:** 32 MiB = 33 554 432 B ÷ 36 B = **932 067 vertices**, i.e. 310 689
  triangles, i.e. **25 890 boxes**. `append_vertex_3d` refuses the 25 891st box with "the active
  graphics frame exceeds its transient vertex capacity"
  ([`graphicsRuntimeDraw.c#L177-L180`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L177-L180)).
  10⁵ boxes need 129.6 MB. **The scene cannot be drawn at all**, at any frame rate.
- **Command-buffer calls if it could:** four per object — `vkCmdBindPipeline`,
  `vkCmdBindVertexBuffers`, `vkCmdPushConstants`, `vkCmdDraw` — so 4 × 10⁵ = **400 000** per frame.
- **FFI calls:** three `add a vertex` calls per triangle × 12 triangles × 10⁵ = **3.6 million**
  DynLex→C calls per frame, before any geometry work.

This is P-07 (interactivity collapses around 10⁴–10⁵ objects) reproduced from first principles in the
runtime the kernel is supposed to feed. It is not an argument against DynLex; it is the specification
of what `ui/` has to build.

---

## Camera-relative rendering: what it actually requires

### The two implementations that exist, and they agree

OCCT's own source comment is the clearest statement of the design space found anywhere in this
research. It enumerates three ways out of float32-far-from-origin — migrate everything to double
("too expensive for most hardware"), pass a double translation to the shader and emulate ("requires
modified GLSL programs … and extra packing mechanism"), or **move the translation part of the
model-world matrix into the world-view matrix**, because "while moving Camera towards the object,
Camera translation part and Object translation part will compensate each other to fit into single
float precision. But this operation should be performed with double precision" —
and it concludes "for the moment we consider the last one as main scenario"
([`OpenGl_LayerList.cxx#L602-L642`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_LayerList.cxx#L602-L642)).
The implementation matches: the layer origin is added to the f64 orientation matrix, and
`ConvertFrom` truncates to `NCollection_Mat4<float>` **after** the subtraction
([`#L642-L663`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_LayerList.cxx#L642-L663)),
and the origin is reset to zero when the layer is done
([`#L712`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_LayerList.cxx#L712)).

Filament does the same thing one level down, per renderable rather than per layer: with accurate
translations on, the f64 world transform is composed with the object's f64 transform and truncated
once, at a line whose comment says so
([`Scene.cpp#L217-L226`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/src/details/Scene.cpp#L217-L226)).

Cesium takes OCCT's *second* option — the one OCCT rejected as needing packing — and makes it work:
a f64 coordinate is split into two f32 values at a 65 536 quantum
([`EncodedCartesian3.js#L52-L76`](https://github.com/CesiumGS/cesium/blob/1.145/packages/engine/Source/Core/EncodedCartesian3.js#L52-L76)),
uploaded as two vertex attributes, and differenced against the camera's encoded position **in the
vertex shader**: `highDifference + lowDifference`
([`translateRelativeToEye.glsl#L34-L45`](https://github.com/CesiumGS/cesium/blob/1.145/packages/engine/Source/Shaders/Builtin/Functions/translateRelativeToEye.glsl#L34-L45)).
This is the two-float double-emulation family (the DSFUN90 lineage; the Godot article already cited
in [`../../domain/spatial-model.md`](../../domain/spatial-model.md) surveys it — *claimed*). Its cost
is doubled position bandwidth and a shader that cannot be a plain pass-through; its benefit is that
the CPU never touches a matrix per object per frame.

### What this costs the kernel — *inferred*, with the arithmetic

float32 has a 24-bit significand, so the ULP at magnitude *m* is `2^(floor(log2 m) − 23)`:

| Distance from the f32 origin | ULP |
|---|---|
| 1 km | 6.1e-5 m (0.06 mm) |
| 10 km | 9.8e-4 m (0.98 mm) |
| 100 km | 7.8e-3 m (7.8 mm) |
| 500 km | 3.125e-2 m (31 mm) |

The 500 km figure agrees with the measured value in
[`../kernels/blender.md`](../kernels/blender.md) §Precision, which is the check that this arithmetic
is the same arithmetic. **The consequence for ADR-0006:** if the f32 origin is the *camera*, a
building keeps sub-millimetre coordinates out to a 10 km view radius, and 7.8 mm out to 100 km —
beyond which nothing in a building model is resolvable anyway. Camera-relative f32 is sufficient; the
row ADR-0006 needs is answered, and not by a new measurement but by two independent production
implementations plus the ULP table.

### The correction this note makes to spec §5

Spec §5 says positions "are expressed relative to the camera's tile in f64 on the CPU, then truncated
to f32 for upload". Read literally that is a **per-vertex** repack whenever the camera's tile changes,
which means re-uploading every visible vertex buffer at a tile crossing. Neither implementation that
actually ships does that. The cheaper equivalent, and the one to adopt:

1. **Vertex positions are stored and uploaded in their own tile frame, f32, once.** A tile a few
   hundred metres across gives, from the table above, ULP ≤ 6.1e-5 m. These buffers are static
   `DEVICE_LOCAL` and never repacked.
2. **The per-object f64 subtraction is `own_tile_origin − camera_tile_origin`**, a `dvec3`, computed
   on the CPU once per visible tile per frame and folded into the object's instance transform before
   truncation to f32. Cost: one f64 vec3 subtract plus a 4×3 truncate per *tile*, not per vertex —
   for 10⁴ visible tiles, 10⁴ subtractions per frame.
3. **`ui/` must expose a per-draw or per-instance f32 affine transform**, not the collapsed MVP push
   constant the runtime has today, or step 2 has nowhere to put its result.

This keeps spec §5's guarantee ("GPU double precision is never required") intact and removes the
repacking it implies. It is an amendment to the wording, not to the decision.

---

## Known problems — issue-tracker survey

Five threads, each read to its resolution. Roles are GitHub `author_association`.

| Thread | Role of key speaker | What it shows |
|---|---|---|
| [bevy#1680](https://github.com/bevyengine/bevy/issues/1680) "Ability to set Transform fundamental native type to f64 or fixed-point types" — **open since 2021-03-17**, 28 comments, filed by `recatek` (**CONTRIBUTOR**) | `NthTensor` (**CONTRIBUTOR**), `james7132`, `alice-i-cecile` (**MEMBER**) | The engine's own constraint, stated by a maintainer: "Rendering (which is driven by `GlobalTransform`) has to be 32-bit. I don't think we have the same level of flexibility as UE5 here." The proposed direction is pluggable transform types that still map back to a 32-bit `GlobalTransform`. **Unresolved after five years**; the most recent comment (2026-06-28, `ST33LDI9ITAL`, **NONE**) is a request, not a fix |
| [bevy#10443](https://github.com/bevyengine/bevy/issues/10443) "Distortion on high values of transform translate" — **closed completed** 2023-11-09, filed by `numfin` (**NONE**) | `aevyrie` (**MEMBER**) | Diagnosis and the engine's actual answer: "This is caused by limited precision of 32bit floats… Common solutions to this are floating origins and/or double precision coordinates… I've made a bevy plugin that solves this problem using an integer grid and a floating origin: `big_space`". Also `Rigidity` (**CONTRIBUTOR**): visible "at coordinates as low as 20,000", unplayable near 1 000 000. The resolution is a third-party plugin, and the reporter's closing comment asks — unanswered — "feels like there should be tools/api available out of the box" |
| [three.js#16324](https://github.com/mrdoob/three.js/issues/16324) "Moving the camera model will shake if the coordinates are large" — **closed completed** 2019-04-24, filed by `dytmh` (**NONE**) | `Mugen87` (**COLLABORATOR**) | Resolution is explicit refusal: "the issue needs to be handled on application level. `three.js` can't provide a fix for this." Note the reporter's rebuttal — they were already using `InstancedBufferAttribute` for a GIS dataset, i.e. instancing and large coordinates collide |
| [three.js#28148](https://github.com/mrdoob/three.js/issues/28148) "Distortion of the model due to being too far from the origin" — **closed not-planned** 2024-04-16, filed by `vci-core` (**NONE**) | `gkjohnson`, `donmccurdy` (**COLLABORATOR**) | Same answer five years later: "It's not something that three.js can automatically fix, unfortunately." Skinning matrices are named as the specific GPU-side casualty |
| [engine_web-ifc#84](https://github.com/ThatOpen/engine_web-ifc/issues/84) "Define the origin of the model as being the origin of one site" — **open since 2021-09-20**, filed by `favreau84` (**NONE**) | `tomvandig` (**CONTRIBUTOR**), `agviegas` (**COLLABORATOR**) | The BIM-specific version. A maintainer commits — "Sounds good, I'll update the ticket when `first_site_as_origin` (or similar) is in" — and five years later the ticket is still open; what shipped instead is the per-model `coordinationMatrix` a later comment points to, i.e. one static origin shift per model, which is the `coordinates-manager.ts` code cited in table C. Note the honest limit the reporter states up front: `COORDINATE_TO_ORIGIN` does **not** fix every model |

What the survey shows: **no browser or game engine solves this in the engine.** Two of five are
closed with "handle it at application level", one is closed by pointing at a third-party plugin, and
two remain open for five years. The two engines that *do* solve it — OCCT and Filament — are the two
that came from CAD and from a rendering team that had to serve geospatial callers, and both solved it
the same way. That is the strongest available evidence that the kernel must own this and cannot
inherit it.

---

## The answer for the kernel's `gpu` module

### (a) The layout the kernel should emit

Two buffers per *batch* (one mesh shared by many placements) plus one index buffer. All f32, all
interleaved, all tile-local.

**Vertex buffer, `VertexStepMode::Vertex`, 32 bytes, `DEVICE_LOCAL`, written once:**

| Offset | Attribute | Format |
|---|---|---|
| 0 | position (tile-local) | `Float32x3` |
| 12 | normal, octahedral-encoded | `Snorm16x2` |
| 16 | uv | `Float32x2` |
| 24 | material/colour index | `Uint32` |
| 28 | pad / second uv set | `Uint32` |

**Instance buffer, `VertexStepMode::Instance`, 64 bytes, rewritten per frame only for tiles whose
camera-relative offset changed:**

| Offset | Attribute | Format |
|---|---|---|
| 0 | `world_from_local` row 0 (camera-relative) | `Float32x4` |
| 16 | row 1 | `Float32x4` |
| 32 | row 2 | `Float32x4` |
| 48 | element id | `Uint32` |
| 52 | flags: selected / hidden / cut | `Uint32` |
| 56 | per-instance colour | `Unorm8x4` |
| 60 | reserved | `Uint32` |

**Index buffer:** `Uint32`, always — `Uint16` saves nothing once meshes are slab-allocated, and bevy
already promotes `U16` to `U32` on primitive-restart collision
([`index.rs#L127-L133`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_mesh/src/index.rs#L127-L133)).

The 3×`vec4` transposed affine is bevy's `MeshUniform.world_from_local` layout exactly
([`mesh.rs#L514-L518`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh.rs#L514-L518)),
chosen because it is the one form every engine below accepts without repacking.

**What each path would have to adapt:**

| Path | Adaptation needed |
|---|---|
| **wgpu / bevy** | None. Both buffers map directly onto `VertexBufferLayout` with `VertexStepMode::Vertex`/`Instance` |
| **Filament** | None for the vertex buffer (`attribute(…, byteOffset, byteStride)` takes interleaving directly); the instance buffer becomes an `InstanceBuffer` of `mat4f`, so the 4×3 rows are expanded to 4×4 — a widening copy, not a repack |
| **three.js** | None. `InterleavedBufferAttribute` for the vertex side; the instance side is `InstancedMesh.instanceMatrix` (4×4 f32) or a `BatchedMesh` |
| **Blender** | Would need splitting into one buffer per attribute — its extractor model is deliberately de-interleaved and per face corner. Not a target; listed to show the layout is *not* universal |
| **OCCT** | Vertex buffer maps onto `Graphic3d_Buffer` attributes; **the instance buffer has nowhere to go** — no instance-rate attribute is used anywhere in its render path, so instancing would have to be added or every placement drawn separately |
| **DynLex runtime** | Everything. It has one fixed 36-byte layout, no index buffer, no instance rate — §(c) |

### (b) What camera-relative rendering requires of the kernel

The kernel's `gpu` module owns exactly one numeric step. In pseudocode — this is a description of the
step, not DynLex and not copied from any source:

```text
offset_f64  = tile_origin_f64 − camera_tile_origin_f64      # exact: both are on a coarse grid (spec §5)
affine_f64  = translate(offset_f64) ∘ object_placement_f64
instance    = truncate_to_f32(affine_f64)                   # the only f64 → f32 conversion in the kernel
```

- **Where the subtraction happens:** on the CPU, in the kernel, in f64, at *tile* granularity —
  never per vertex, never on the GPU. This is OCCT's choice
  ([`OpenGl_LayerList.cxx#L626-L642`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_LayerList.cxx#L626-L642))
  and Filament's
  ([`Scene.cpp#L217-L226`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/src/details/Scene.cpp#L217-L226)).
- **Per-frame cost:** one `dvec3` subtract and one 4×3 truncation per visible tile — negligible, and
  in any case *inferred* here, not measured; see §Risks.
- **When it is skipped entirely:** if the camera has not crossed a tile boundary and no object moved,
  the instance buffer is unchanged and nothing is uploaded. This is the reason to put the offset in
  the *instance* record rather than in a push constant.
- **What `ui/` must expose for it to work:** a bindable per-instance buffer; a draw that takes an
  instance range; and the ability to leave a vertex buffer resident across frames. None of the three
  exists today.
- **What is explicitly *not* required:** GPU f64. wgpu's own feature documentation is the citation
  ([`features.rs#L1054-L1064`](https://github.com/gfx-rs/wgpu/blob/923b896955655600c38ac93d6e9ae26845682f80/wgpu-types/src/features.rs#L1054-L1064)),
  and the DynLex device requests no features at all
  ([`graphicsRuntimeVulkan.c#L301-L308`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L301-L308)),
  so requiring it would mean changing device creation as well as every shader.

### (c) The gap list

Each gap carries the source line that shows its absence. "`ui/`" means the work belongs to the UI
library (spec §2); "dynlex" means it is a language or runtime extension and belongs in spec §8's
table, which currently lists threading, aligned/mapped allocation and SIMD — and **not** any of these.

| Gap | Evidence of absence | Owner | Blocks |
|---|---|---|---|
| Persistent device-local vertex/index buffers | Arena is `VERTEX_BUFFER_BIT`-only, host-visible, reset each frame ([`graphicsRuntimeVulkan.c#L687-L698`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeVulkan.c#L687-L698); [`graphicsRuntimeDraw.c#L71`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L71)) | `ui/` | spec §9 M2 |
| Index buffers | grep `vkCmdBindIndexBuffer` = 0, `vkCmdDrawIndexed` = 0, `VK_BUFFER_USAGE_INDEX_BUFFER_BIT` = 0 | `ui/` | M2 |
| Instance-rate attributes and instanced draws | grep `VK_VERTEX_INPUT_RATE_INSTANCE` = 0; instance count is the literal `1` in the only draw ([`graphicsRuntimeDraw.c#L212`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L212)) | `ui/` | M2, and P-07 |
| A caller-supplied vertex layout | `builtin ? 3u : 1u` attributes, both hard-coded ([`graphicsRuntimePipeline.c#L51-L76`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L51-L76)) | `ui/` | M2 |
| Storage buffers / SSBOs | grep `VK_BUFFER_USAGE_STORAGE_BUFFER_BIT` = 0, `VK_DESCRIPTOR_TYPE_STORAGE_BUFFER` = 0; shader inputs are 32 scalar floats ([`graphicsRuntimeInternal.h#L13`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L13)) | `ui/` | spec §6 item 4 |
| **Compute pipelines and dispatch** | grep `vkCmdDispatch` = 0, `vkCreateComputePipelines` = 0, `VK_PIPELINE_BIND_POINT_COMPUTE` = 0, `VK_SHADER_STAGE_COMPUTE_BIT` = 0 | `ui/` | spec §6 item 4 |
| **A compute shader stage in the compiler** | `enum class ShaderStage { Fragment, Vertex }` ([`parseContext.h#L65`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/compiler/parseContext.h#L65)); `executionModel = isVertex ? 0 : 4` with I/O hard-wired to `in_Position`/`gl_Position` or `gl_FragCoord`/`gl_FragColor` ([`spirv.cpp#L642-L671`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/compiler/codegen/spirv.cpp#L642-L671)); CLI accepts only `vertex\|fragment` ([`main.cpp#L250-L255`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/main.cpp#L250-L255)) | **dynlex — missing from spec §8** | spec §6 item 4, §7 `gpu/`, §9 M7 |
| GPU→CPU readback | grep `vkCmdCopyImageToBuffer` = 0, `VK_BUFFER_USAGE_TRANSFER_DST_BIT` = 0; no fence-and-map path exists | `ui/` | picking, spec §3 "consumes buffers produced on the GPU" |
| Reverse-Z depth | Clear 1.0 + `COMPARE_OP_LESS` + standard projection ([`graphicsRuntimeDraw.c#L47-L50`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L47-L50); [`graphicsRuntimePipeline.c#L98-L103`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L98-L103); [`graphicsRuntime.c#L399-L405`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntime.c#L399-L405)) | `ui/` | depth precision criterion |
| Clip planes and capping | No `VkPipelineRasterizationStateCreateInfo` clip distance, no stencil use ([`graphicsRuntimePipeline.c#L87-L103`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L87-L103)) | `ui/` (algorithm borrowed from OCCT) | section views |
| A depth test for custom shader pipelines | `create_pipeline(…, TRIANGLE_STRIP, false, false, …)` — `depth` is literal `false` ([`graphicsRuntimePipeline.c#L424-L426`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimePipeline.c#L424-L426)) | `ui/` | any custom material |

**The one that changes spec §8.** Every row above except one is `ui/` work that the spec already
implies. The compute-stage row is different: spec §6 item 4 says "DynLex compiles to SPIR-V.
Embarrassingly parallel work … is written as DynLex compute kernels in `gpu/` and dispatched by
`ui/`" — and the compiler cannot emit a `GLCompute` entry point. That is a **language extension**,
and spec §8's table does not list it. It is added to `problems.md` as P-28 and named in §Risks.

---

## Verdict

### Build on — the DynLex runtime, because it is the given, and here is the bill

ADR-0004 makes this a decision about *what to add*, not *what to pick*. The runtime is a competent,
small, correct immediate-mode 2D/3D submitter — Vulkan 1.3, two frames in flight, correct
swapchain-recreation handling, honest error strings. It is not a BIM viewport and was never meant to
be. The twelve-row gap list above is the bill, and eleven of the twelve rows are `ui/` work that can
be done incrementally without touching the language. Spec §9 M2's exit criterion ("rotating extruded
polygon on screen, driven only by kernel buffers") is reachable *today* through
`begin_triangles`/`append_vertex`; it just does not exercise anything the kernel's real layout needs.
**Recommendation: keep M2's criterion but add a second one** — the same mesh drawn through an index
buffer and an instance buffer — so M2 forces the first three gap rows closed rather than deferring
them to M7.

### Borrow from

1. **bevy's GPU preprocessing, as the target architecture for `ui/`.** A compute pass expands
   per-object input records into per-view instance records, culls, and writes
   `IndirectParametersIndexed`, which a single `multi_draw_indexed_indirect_count` consumes
   ([`mesh_preprocess.wgsl#L1-L15`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh_preprocess.wgsl#L1-L15),
   [`gpu_preprocessing.rs#L774-L791`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_render/src/batching/gpu_preprocessing.rs#L774-L791),
   [`mesh.rs#L4532`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_pbr/src/render/mesh.rs#L4532)).
   Blender independently arrived at the same shape — `DrawPrototype` compacted into `DrawCommand` on
   the GPU ([`draw_command_shared.hh#L85-L99`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/draw_command_shared.hh#L85-L99)).
   Two independent arrivals at one design is the reason to adopt it. **This is the single largest
   argument for the compute-stage extension**: without it, the kernel's `gpu/` module can emit the
   buffers but nothing can preprocess them on the device.
2. **Filament's accurate translations**, as the object-granular form of the f64→f32 step, and its
   default-off ergonomics: the expensive mode is opt-in
   ([`TransformManager.h#L167-L189`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/TransformManager.h#L167-L189)).
   For us it is default-on, because our default project is georeferenced.
3. **OCCT's layer origin**, as the coarser tile-granular form, and its capping algorithm
   (`OpenGl_CappingAlgo`, `OpenGl_CappingPlaneResource`) — the only section-capping implementation
   among the six, and one whose clip-plane equations are correctly re-based through the local origin
   ([`OpenGl_ShaderManager.hxx#L63-L70`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/Visualization/TKOpenGl/OpenGl/OpenGl_ShaderManager.hxx#L63-L70)) —
   a trap we would otherwise fall into.
4. **Budget-driven LOD**, from Potree's `pointBudget` traversal (see
   [`../kernels/pointclouds.md`](../kernels/pointclouds.md) §Out-of-core) and bevy's visibility
   ranges. Adopt the budget; **do not adopt it without an eviction policy** — that is P-18, and it is
   still open against spec §4/§8.
5. **CPU-BVH picking as the primary path, GPU id-buffer picking as the secondary.** Three of the six
   pick on the CPU through a BVH (OCCT, That Open via `THREE.Raycaster`, the `three-mesh-bvh`
   ecosystem), and the kernel already owns a BVH (spec §7 `spatial/`), so the primary path costs
   nothing new and has no latency. Filament's async `View::pick` documents the cost of the other
   one — "`pick()` has some latency"
   ([`View.h#L858-L862`](https://github.com/google/filament/blob/65eaf091d7236b64094c59354c8632a86b911f92/filament/include/filament/View.h#L858-L862)) —
   and Blender's returns only `{id, depth}`, nothing the kernel could consume (blender.md §The GPU
   module). Keep the id in the instance record anyway: rubber-band selection over 10⁵ elements is the
   case where an id buffer wins, and it costs 4 bytes.

### Avoid

| Avoid | Seen in | `problems.md` |
|---|---|---|
| **float32 world matrices** — a `float4x4` object transform in world coordinates, or an f32 camera translation | DynLex runtime ([`graphicsRuntime.c#L412-L436`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntime.c#L412-L436)); Blender ([`draw_shader_shared.hh#L119-L142`](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/source/blender/draw/intern/draw_shader_shared.hh#L119-L142)); bevy ([`transform.rs#L86-L92`](https://github.com/bevyengine/bevy/blob/b56fc29d3016e641754765244b5ba3f9cc504671/crates/bevy_transform/src/components/transform.rs#L86-L92)); three.js on upload ([`WebGLUniforms.js#L329-L352`](https://github.com/mrdoob/three.js/blob/148ef33ecb6d2502ff796d4554abd1549c95d519/src/renderers/webgl/WebGLUniforms.js#L329-L352)) | **P-05** |
| **One draw call per element** — and its stricter cousin, one transient vertex stream per element | DynLex runtime ([`graphicsRuntimeDraw.c#L194-L214`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L194-L214), [`city_flyover.dl#L66-L78`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/tests/games/city_flyover.dl#L66-L78)); OCCT, which has no instancing at all | **P-07** |
| **A drawing budget without a residency policy** | Potree | **P-18** |
| **A fixed per-frame transient upload arena as the only path to the GPU** — a hard ceiling that converts a performance problem into a hard failure, at 25 890 boxes | DynLex runtime ([`graphicsRuntimeInternal.h#L15`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeInternal.h#L15), [`graphicsRuntimeDraw.c#L177-L180`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/runtime/graphicsRuntimeDraw.c#L177-L180)) | **P-27 (new)** |
| **Planning GPU compute against a toolchain that cannot emit a compute stage** | DynLex compiler ([`parseContext.h#L65`](https://github.com/OpenAEC-Foundation/dynlex/blob/7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd/src/cpp/compiler/parseContext.h#L65)) | **P-28 (new)** |

---

## Risks

- **Nothing here is measured.** The draw-call and arena arithmetic is sound but untested; the claim
  that the per-tile f64 subtraction is negligible is arithmetic, not a profile. The experiment that
  settles both: a spike that builds the DynLex compiler, adds index and instance buffers to the
  runtime, and draws 10⁵ instanced boxes at a tile offset of 500 km — reporting frame time, upload
  bytes and the observed coordinate error. It is named in `docs/risks.md` and it is the natural
  content of spec §9 M2's second exit criterion.
- **The compute-stage extension is unscoped.** Adding `GLCompute` to the SPIR-V backend means storage
  buffers, workgroup builtins, barriers and a memory model — a much larger change than adding a CLI
  flag, and none of it is in spec §8's table. If it proves too large, spec §6 item 4 must be
  rewritten to run that work on CPU threads (spec §8's first row), and §10's targets rechecked
  against that.
- **OCCT's local origin is per Z-layer, not per tile.** Borrowing the design is safe; borrowing the
  *granularity* is not, since a Z-layer is a display concern and a tile is a coordinate frame. The
  two must not be conflated, exactly as `../../domain/spatial-model.md` warns against conflating
  tiles with the spatial hierarchy.
- **This note evaluated OCCT's OpenGL visualiser, not its Vulkan one.** If a Vulkan backend exists at
  a later tag its instancing story may differ; the absence claim above is scoped to
  `src/Visualization/TKOpenGl/` at `V8_0_1`.

## Corrections and additions this note makes to `problems.md`

- **P-05** — adds the GPU half. The kernel's answer is not only "f64 in tile frames" but "the f64
  subtraction happens on the CPU at tile granularity, and the instance transform is the only thing
  truncated". Adds OCCT and Filament as the two candidates that *do* solve it, which the row
  previously did not record.
- **P-07** — adds a second, independent mechanism at the GPU end: Blender's ceiling is the evaluation
  graph, but the DynLex runtime's ceiling is the draw-call and transient-arena model, and the two are
  separate failures with the same symptom.
- **P-18** — unchanged in substance; this note confirms that none of the six engines pairs its budget
  with an eviction policy, so the open question stands.
- **P-27 (new)** — a fixed transient per-frame upload arena as the only path to the GPU.
- **P-28 (new)** — planning GPU compute against a toolchain with no compute stage.

## Sources

Every link above is pinned to the commit or tag in §What was read. Additional references:

- Cesium GPU RTE — [`EncodedCartesian3.js`](https://github.com/CesiumGS/cesium/blob/1.145/packages/engine/Source/Core/EncodedCartesian3.js) and [`translateRelativeToEye.glsl`](https://github.com/CesiumGS/cesium/blob/1.145/packages/engine/Source/Shaders/Builtin/Functions/translateRelativeToEye.glsl) at `1.145`
- `big_space` — [README at `06c66a7`](https://github.com/aevyrie/big_space/blob/06c66a77f00f60bb8ab3792797b14110fe63efde/README.md) (*claimed*)
- [Emulating double precision on the GPU to render large worlds — Godot](https://godotengine.org/article/emulating-double-precision-gpu-render-large-worlds/) (*claimed*; already cited by [`../../domain/spatial-model.md`](../../domain/spatial-model.md))
- Issue threads: [bevy#1680](https://github.com/bevyengine/bevy/issues/1680), [bevy#10443](https://github.com/bevyengine/bevy/issues/10443), [three.js#16324](https://github.com/mrdoob/three.js/issues/16324), [three.js#28148](https://github.com/mrdoob/three.js/issues/28148), [engine_web-ifc#84](https://github.com/ThatOpen/engine_web-ifc/issues/84)
- Within this repository: [`../kernels/blender.md`](../kernels/blender.md) §The GPU module and §Precision, [`../kernels/occt.md`](../kernels/occt.md), [`../kernels/pointclouds.md`](../kernels/pointclouds.md) §Out-of-core, [`../kernels/problems.md`](../kernels/problems.md), [`../../domain/spatial-model.md`](../../domain/spatial-model.md), [`README.md`](README.md)
