# NVIDIA USD BRep

**Decision question:** Can USD BRep supply an exchange representation or GPU
tessellation path for Open BIM Studio, or does it only serialize a separate
modelling kernel?

**Status:** under review — source assessment, no runtime benchmark
**Author:** Codex
**Last updated:** 2026-10-31
**Pinned source:** [`3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5`](https://github.com/NVIDIA-Omniverse/usd-brep/tree/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5), committed 2026-10-22

## Summary

The pinned repository includes the SMLib modelling kernel, boolean APIs and
CPU tessellation, alongside an OpenUSD B-rep schema and adapters. Its audited
tessellation path does not provide an OBS-ready GPU mesher. Track the schema
as exchange prior art; no dependency or kernel decision changes follow from
this source review ([#156](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/156)).

## What it is

The project has separable layers: SMLib geometry and topology, C++ modelling
APIs, USD import/export and the codeless `omniSolid` schema, Python bindings,
and a Hydra imaging plugin. SMLib is built as a shared library; the public
API contains boolean operations, projection and tessellation. Therefore the
issue's initial hypothesis that this is only a serialization layer is
incorrect for this pin. These are source observations, not results from
running its modelling operations. [API][api] · [build definition][build]

The schema stores topology as arrays and retains analytic and NURBS
geometry, including double-precision points and control vertices. It could
inform a future optional USD exchange adapter. This is distinct from IFC
semantics and the native IFCX project format. [Schema][schema] · [schema definitions][definitions]

## Evaluation

The thirteen criteria are those of the [kernel evaluation method](../kernels/README.md).
“Inferred” means a conclusion from the cited source, not a benchmark.

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| License | Root license and inspected SMLib files use Apache-2.0. Dependencies have separate notices; this is not a completed distribution licence review. | Inferred | [License][license], [notices][notices], [build][build] |
| Native representations | B-rep topology, analytic/NURBS geometry and polygonal tessellation are present. USD is one serialization route. | Inferred | [API][api], [definitions][definitions] |
| Boolean robustness | Union, difference, intersection and options exist. Documentation's exact-NURBS description does not establish exact predicates or robust results on our torture set. Thin features and healing failures are documented. | Claimed / inferred | [Boolean guide][booleans], [known issues][issues] |
| Tolerance and precision | USD attributes include per-B-rep intersection tolerances and double-precision geometry. Kernel APIs use doubles and local tolerance machinery; accumulation through chained operations is unmeasured. | Inferred | [Definitions][definitions], [edge tolerance declarations][edge] |
| Incremental evaluation | Callers can operate on individual B-reps. That is not a measured model dependency graph or an answer to R-01. Hydra documents unsupported edits to B-rep geometry after initial loading. | Inferred / claimed | [API][api], [Hydra][hydra] |
| Threading | Tessellation contains TBB parallel loops; Hydra documents parallel loading and a thread-count/memory tradeoff. This does not prove all modelling operations are thread-safe. | Inferred / claimed | [Tessellation implementation][tess], [Hydra][hydra] |
| GPU path | Audited tessellation runs C++/TBB code and returns an owned `SmPolyBrep`. The USD tool creates meshes for Hydra rendering. No direct Vulkan-buffer or GPU-tessellation interface was established. | Inferred | [API][api], [tessellation implementation][tess], [Hydra][hydra] |
| IFC coverage | The reviewed layers expose USD geometry, not native IFC authoring semantics. No IFC certification or lossless IFC round-trip claim is established. | Inferred; coverage unknown | [Schema][schema], [API][api] |
| Performance | Load, booleans, tessellation, picking and 10k/100k/1M model behaviour were not measured here. | Unknown | No execution or benchmark |
| Embeddability | Native shared-library/API design permits an in-process integration in principle. C++ classes, references, ownership and output conversion require an explicit DynLex bridge. The USD layer requires OpenUSD; an Omniverse application process is not an inherent API requirement. No OBS binding or WASM build was tested. | Inferred / claimed | [Build][build], [API][api], [build instructions][building] |
| 2D derivation | The API exposes projection onto a plane and boundary tessellation. This does not establish an issuable drawing pipeline or annotation support. | Inferred | [API][api] |
| Maturity | Published source, platform build instructions and known defects exist. No production qualification or maintenance-capacity assessment was performed. | Inferred; maturity unknown | [Build instructions][building], [known issues][issues] |
| AI familiarity | Source and API documentation are publicly inspectable. No agent-productivity measurement or comparison was made; this is not a selection tiebreaker. | Inferred; productivity unknown | Inspected source and guides |

## Measurements

None. No USD BRep package was installed, compiled or executed for this note.
No boolean success rate, runtime, frame rate or memory-performance claim is
made. The pin identifies the reviewed code, not a validated toolchain.

## Strengths

- The schema separates geometry/topology interchange from a particular UI.
- The included native kernel and modelling API make the project materially
  broader than a USD serializer. [API][api] · [schema][schema]
- The default tessellator rejects failed faces unless partial output is
  explicitly requested, and reports ownership/failure handling. [API][api]

## Weaknesses

Upstream documents wrong triangle winding on some filleted solids and
chord-height violations near sphere poles and on skinned surfaces. These
are upstream reports, not reproduced failures in OBS. They prevent treating
tessellation quality controls as proven geometric bounds. [Known issues][issues]

The Hydra adapter tessellates on initial mesh access and documents limits
on subsequent B-rep geometry edits. It cannot simply replace OBS's editing
and invalidation path. [Hydra][hydra]

## Risks

Do not add a duplicate candidate-specific risk merely for documenting an
optional technology. Any proposed adoption must answer existing
[R-16 (boolean robustness), R-17 (precision) and R-20 (GPU path)](../../risks.md).
None is mitigated by this source review. Dependency notices also remain part
of the dependency review required by R-11. No dependency is added here.

## Verdict

**Track as exchange prior art; do not integrate it into OBS on this evidence.**
For the requested exchange role it belongs beside category D; the repository
also contains category-A kernel material. This is a post-evaluation note,
not a reopening of the historical candidate matrix or an amendment to an
accepted ADR. Keep IFC/IFCX and OBS's renderer as the current product paths.

**Borrow from:** inspect its flattened topology schema, double-precision
geometry and explicit tessellation-failure/ownership reporting when designing
an optional USD adapter. **Avoid:** assuming GPU acceleration from the project
name, conflating exact NURBS geometry with robust predicates, or assuming
Hydra's initial-loading model supplies interactive dependency evaluation.

Before any adoption proposal, a separate spike must (1) round-trip our planar
and trimmed-NURBS fixtures through `BrepArray`, checking topology, orientations
and volume; (2) run the extended boolean torture set and 500 km precision set;
and (3) tessellate those fixtures into the existing Vulkan path, measuring
geometric error, CPU time and uploaded bytes. A source/build pin, hardware,
failures and the complete dependency manifest must accompany those results.
These are the specific missing measurements; this note makes no speed or
robustness recommendation.

## Sources

All implementation and documentation links below point to the reviewed pin.

[license]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/LICENSE
[notices]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/THIRD_PARTY_NOTICES.md
[build]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/SMLib/premake5.lua
[building]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/BUILDING.md
[api]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/SM_API/inc/SmApiBrep.h
[schema]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/schema/README.md
[definitions]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/schema/omniSolid/resources/schema.usda
[booleans]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/.agents/operations/booleans.md
[edge]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/SMLib/inc/SmEdge.h
[tess]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/SMLib/src/SmTess.cpp
[hydra]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/source/HYDRA_USD_BREP/README.md
[issues]: https://github.com/NVIDIA-Omniverse/usd-brep/blob/3fd5b9548d19aa8c12c29bc9637a96d42a06f8a5/KNOWN_ISSUES.md
