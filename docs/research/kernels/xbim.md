# xBIM — the third IFC implementation, read but not run

**Decision question:** xBIM is the third independent IFC toolkit, and the disagreement analysis
(P-10) wanted three implementations, not two. Can it supply a third geometry opinion — and does
its architecture offer anything for the `ifc/` sub-project that IfcOpenShell and web-ifc do not?

**Serves:** ADR-0004; the `ifc/` sub-project spec; [`problems.md`](problems.md) P-06, P-10, P-14,
P-24; R-01

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-11

> **Nothing in this note is labelled *measured*.** No .NET SDK is installed on the measurement
> machine — `dotnet --list-sdks` prints nothing and exits 0, while `dotnet --version` reports
> "The command could not be loaded"; only the shared runtimes are present (Microsoft.NETCore.App
> 6.0.36, 8.0.31, 9.0.20, 10.0.12, plus the matching ASP.NET and WindowsDesktop runtimes). The
> geometry engine additionally needs a C++/CLI build with Visual Studio 2022 and the Windows SDK
> (§Platform), which is well beyond the brief's "if it installs within an hour". Every claim below
> is **claimed** (stated by a file in the repository or by a named person on the tracker) or
> **inferred** (our reading of source or build configuration). The three-way disagreement analysis
> the brief wanted is therefore a **two-way** one; see
> [`compare.md`](../../../spikes/incremental-evaluation/results/compare.md).

---

## Summary

xBIM is a genuine third opinion on IFC *parsing* — `Xbim.Essentials` is cross-platform, supports
IFC2x3, IFC4 and IFC4x3 Add2, and is actively released — but its geometry is a C++/CLI managed
wrapper around **OCCT 7.8.1**, the same kernel version IfcOpenShell's wheel bundles, so it is not
an independent geometry opinion in the way web-ifc is. It is Windows-only by construction, not by
packaging: the engine is compiled as C++/CLI, and its own runtime-path helper throws
`NotImplementedException` for anything that is not `win-x86` or `win-x64`. For incremental
evaluation it is the clearest negative of the three: whole-model regeneration is enforced at the
*storage contract*, because `IGeometryStore.BeginInit()` is documented as clearing the store, so
there is no API-level place to put a per-element update even if one wanted to.

## What it is

The xBIM Toolkit is a .NET IFC library maintained by xBimTeam, split across two repositories.
`XbimEssentials` is the schema, parsing and model layer — pure managed C#, multi-targeting
`netstandard2.0`, `netstandard2.1`, `net8.0` and `net10.0`
([README](https://github.com/xBimTeam/XbimEssentials/blob/e3c877712aeff39813219b9dd13383c266d07055/README.md), *claimed*).
`XbimGeometry` is the geometry engine plus the scene/tessellation layer that drives it.

Releases do not happen through GitHub Releases. Tags are CI-generated per build — 714 of them on
`XbimGeometry` — and shipping is on NuGet (*inferred* from the tag pattern and the NuGet feed). The
newest `Xbim.Essentials` NuGet package is **6.1.605** (published 2026-07-15). The newest
`Xbim.Geometry` package is **6.3.891-netcore** (2026-04-01); the newest **non-prerelease** is
**5.1.820**. The 6.x geometry line has shipped only as a `-netcore` prerelease off the
`feature/netcore` branch for years, while `master` still carries 5.1.x (*inferred* from the branch
each 6.x tag sits on; independently stated by the reporter of
[XbimGeometry#578](https://github.com/xBimTeam/XbimGeometry/issues/578), *claimed*).

## What was read, and at which commit

| Repository | Pin | Commit |
|---|---|---|
| `xBimTeam/XbimGeometry` | tag `XbimGeometry_netcore_6.3.897` (newest, on `feature/netcore`) | `be4a6b95eec0b73140cbfd4a51300152c9e33781` |
| `xBimTeam/XbimGeometry` | tag `XbimGeometry_master_5.1.820` (newest on `master`) | `0271bb030ce6789e0cbbf32e2663da798af00764` |
| `xBimTeam/XbimEssentials` | tag `XbimEssentials_master_6.1.605` | `e3c877712aeff39813219b9dd13383c266d07055` |

Read: `Xbim.Geometry.Engine/Xbim.Geometry.Engine.vcxproj`, `Xbim.Geometry.Engine.Interop/`
(`XbimArchitectureConventions.cs`, `Configuration/GeometryEngineOptions.cs`,
`Xbim.Geometry.Engine.Interop.csproj`), `Xbim.Geometry.Abstractions/` (`IXGeometryConverterFactory.cs`,
`IXShapeFactory.cs`, `Enums/XGeometryEngineVersion.cs`), `Xbim.ModelGeometry.Scene/Xbim3DModelContext.cs`,
`Licences/`, both `LICENCE.md` files in full, `Xbim.Common/Geometry/IGeometryStore.cs`,
`Xbim.Common/Step21/XbimSchemaVersion.cs`, the `Schemas/` directory, and the schema `.csproj` files.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | Both repositories ship **CDDL-1.0**, byte-identical except two extra lines in the geometry one. No dual-licence or commercial-option clause in either file. `XbimGeometry` additionally ships `Licences/` containing the **OPEN CASCADE Public Licence** (v6.5, 2011, "LGPL-like with certain differences") *and* `Xbim.Geometry.Engine/OCC/LICENSE_LGPL_21.txt` + `OCCT_LGPL_EXCEPTION.txt`. The two READMEs assert the OCCT terms permit closed-source commercial use; the licence files themselves contain no such analysis | **claimed** (files read in full) | [`XbimEssentials/LICENCE.md`](https://github.com/xBimTeam/XbimEssentials/blob/e3c877712aeff39813219b9dd13383c266d07055/LICENCE.md), [`XbimGeometry/LICENCE.md`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/LICENCE.md), [`Licences/`](https://github.com/xBimTeam/XbimGeometry/tree/be4a6b95eec0b73140cbfd4a51300152c9e33781/Licences) |
| **Representations held natively** | B-rep (OCCT `TopoDS_Shape`) plus a triangulated mesh from `Xbim.Tessellator`. No point cloud, no implicit. V6 is BREP-first: it converts to BREP and tessellates with OCCT's tessellator, which is why BREP generation was made opt-in | **claimed** | `andyward` (**MEMBER**) on [XbimGeometry#473](https://github.com/xBimTeam/XbimGeometry/issues/473) |
| **Boolean robustness** | OCCT's booleans, so OCCT's failure modes — inherited, not independent. `Factories/BooleanFactory` is the wrapper | **inferred** from the dependency; see [`occt.md`](occt.md) for the kernel's own record |
| **Tolerance and precision model** | Doubles throughout (managed + OCCT). Tolerance comes from `ModelFactor.Precision`, whose **default differs between `MemoryModel` and `EsentModel`** — the same file processed with different storage back-ends can succeed or fail | **claimed** | `andyward` (**MEMBER**) on [XbimGeometry#570](https://github.com/xBimTeam/XbimGeometry/issues/570) |
| **Incremental evaluation** | **None.** One whole-model entry point, `Xbim3DModelContext.CreateContext`, and the store contract clears itself on `BeginInit()` | **claimed** (documented) + **inferred** (searched, §Incremental evaluation) | [`Xbim3DModelContext.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.ModelGeometry.Scene/Xbim3DModelContext.cs), [`IGeometryStore.cs`](https://github.com/xBimTeam/XbimEssentials/blob/e3c877712aeff39813219b9dd13383c266d07055/Xbim.Common/Geometry/IGeometryStore.cs) |
| **Threading model** | Boolean union was multithreaded in response to a performance issue; the whole-model context is the parallel unit. Not characterised further without a build | **claimed**, partial | `SteveLockley` (**MEMBER**) on [XbimGeometry#147](https://github.com/xBimTeam/XbimGeometry/issues/147) |
| **GPU path** | None in-library. Output is `wexBIM`, a tessellated stream format for the xBIM viewers; `martin1cerny` (**MEMBER**) states it "is only documented by the code" | **claimed** | [XbimGeometry#575](https://github.com/xBimTeam/XbimGeometry/issues/575) |
| **IFC coverage** | IFC2x3 TC1, IFC4 (Add2), IFC4x3 **Add2**. Projects `Xbim.Ifc2x3/`, `Xbim.Ifc4/`, `Xbim.Ifc4x3/`; the 4x3 factory is `EntityFactoryIfc4x3Add2.cs`. `XbimSchemaVersion` also has an `Ifc4x1` member with no top-level project. **The README is stale** — it advertises only 2x3 and 4/Add2 | **claimed** (csproj, CHANGELOG) + **inferred** (factory name, enum) | [`Xbim.Ifc4x3.csproj`](https://github.com/xBimTeam/XbimEssentials/blob/e3c877712aeff39813219b9dd13383c266d07055/Xbim.Ifc4x3/Xbim.Ifc4x3.csproj), [`Schemas/`](https://github.com/xBimTeam/XbimEssentials/tree/e3c877712aeff39813219b9dd13383c266d07055/Schemas) |
| **Performance** | **Unknown, and unpublished.** Asked directly, `andyward` (**MEMBER**) answered there are "too many variables to given an answer other than 'It depends'", and proposed counting `IfcShapeRepresentation`s weighted by representation type rather than file size, because `IfcBooleanResult` dominates | **claimed** | [XbimGeometry#511](https://github.com/xBimTeam/XbimGeometry/issues/511) |
| **Embeddability** | Not embeddable from DynLex on any reasonable path: managed .NET for the model layer, and C++/CLI for the geometry engine. In-process use means hosting the CLR | **inferred** from the build configuration |
| **2D derivation** | Not examined | **unknown** |
| **Maturity** | Actively maintained — commits and MEMBER responses through September 2026 — but the stable geometry package is 5.1.820 and 6.x has been prerelease off a feature branch for years, with a live V6-only regression open at the newest commit ([#578](https://github.com/xBimTeam/XbimGeometry/issues/578)) | **claimed** (NuGet dates, issue dates) + **inferred** (branch layout) |
| **AI familiarity** | Not scored. One column, never a tiebreaker (R-09), and nothing here turns on it | **unknown** |

## Geometry engine: OCCT 7.8.1 behind a C++/CLI wrapper

`Xbim.Geometry.Engine` is a C++/CLI project — `<CLRSupport>NetCore</CLRSupport>`,
`<PlatformToolset>v143</PlatformToolset>`, `<TargetFramework>net8.0</TargetFramework>`, platforms
`Win32` and `x64` only. It contains **zero `.cs` files**; the engine internals are `Factories/`
(BooleanFactory, CurveFactory, SolidFactory, ProfileFactory, ShapeFactory) and `Services/`, each
with an `Unmanaged/` subfolder of pure-native `N*` classes (*inferred* from the project tree).

OCCT arrives as a NuGet package: `Xbim.Geometry.Engine.Interop.csproj` pins
`Xbim.Geometry.Occt` **7.8.1** (*claimed*, the version string in the package reference). At the 6.x
pin there are no git submodules, no CMake and no vendored OCC source. On `master` (5.1.820) the
arrangement is different: OCCT is vendored as source under `Xbim.Geometry.Engine/OCC/src/`, and
[`Standard_Version.hxx`](https://github.com/xBimTeam/XbimGeometry/blob/0271bb030ce6789e0cbbf32e2663da798af00764/Xbim.Geometry.Engine/OCC/src/Standard/Standard_Version.hxx)
there declares `OCC_VERSION_COMPLETE "7.6.3"` (*claimed*).

**This matters for P-10.** IfcOpenShell's Python wheel bundles OCCT **7.8.1** as well (see
[`ifcopenshell.md`](ifcopenshell.md) §Which OCCT). Two of the three implementations the brief named
would have been running the same kernel version, so a three-way comparison would have measured
*two* independent geometry opinions and one near-duplicate. The two-way comparison we did run
(IfcOpenShell/OCCT against web-ifc's own boolean) is the more informative pair, and the
IfcOpenShell-internal `opencascade` vs `cgal-simple` pairing in
[`compare.md`](../../../spikes/incremental-evaluation/results/compare.md) supplies a third kernel
opinion that xBIM would not have.

There is **no newer managed engine** alongside the native one. The V5/V6 split is real but both are
native: `GeometryEngineOptions` documents the property as "The default version of the **native**
Geometry Engine to use", and `IXGeometryConverterFactory` calls V5 "now deprecated" and V6 "for
backward compatibility, test and develop purposes only" (*claimed*,
[`IXGeometryConverterFactory.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.Geometry.Abstractions/Factories/IXGeometryConverterFactory.cs)).
The V5→V6 difference is architecture — DI-registered factories and services, BREP-first pipeline —
not managed versus native (*inferred*).

## Platform: Windows-only by construction

Four independent grounds, all *claimed* or *inferred* from files at the pin:

1. The engine is C++/CLI (`CLRSupport=NetCore`), MSVC toolset v143, `Win32`/`x64` only. C++/CLI has
   no non-Windows target.
2. [`XbimArchitectureConventions.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.Geometry.Engine.Interop/Internal/XbimArchitectureConventions.cs)
   maps the runtime folder to exactly `win-x86` or `win-x64` and **throws
   `NotImplementedException`** for every other architecture.
3. The README's build prerequisites are Visual Studio 2022, "Visual C++ Core desktop features",
   "VC++ 2022 v143 tools" and the Windows 10 SDK.
4. CI (`azure-pipelines.yml`) demands `msbuild` and `visualstudio`; Essentials pins
   `vmImage: 'windows-2022'`.

The user-facing confirmation is [XbimGeometry#575](https://github.com/xBimTeam/XbimGeometry/issues/575)
(CLOSED 2026-06-19): the reporter `szlq` (**NONE**) opens with "xBIM (.NET) doesn't work well on
Linux"; `martin1cerny` (**MEMBER**) does not dispute it and redirects to a contributor's personal
fork. `Ibrahim5aad` — **CONTRIBUTOR**, not a team member — offers a `native-engine` branch as "a
native port I'm working on". The reporter then reopened a correctness gap four days later: walls
with doors and windows are missing under the native port but render correctly under official xBIM.
The Linux path is one contributor's unreleased fork with known opening/boolean regressions.

`XbimEssentials` alone is cross-platform. The caveat is `Xbim.IO.Esent`, which multi-targets the
same frameworks but wraps ManagedEsent, a Windows-only storage engine at runtime — off Windows you
use `MemoryModel` (*inferred*), which is also the back-end whose `ModelFactor.Precision` default
differs (see #570 above).

## Incremental evaluation — none, and the store contract is why

This is the sharpest finding in the note, and it is a **searched negative**, not an absence of
looking.

The only build entry point is `Xbim3DModelContext.CreateContext(...)`, four overloads, all
whole-model. The richest signature is
`CreateContext(ReportProgressDelegate, bool adjustWcs, bool generateBREPs,
Func<XbimTriangulatedMesh,int,XbimTriangulatedMesh> postTessellationCallback,
DynamicDeflectionSettings)`. Everything else public on the class is a reader — `ShapeInstances()`,
`ShapeGeometries()`, `ShapeGeometry(int)`, `ShapeInstancesOf(IIfcProduct)`, `GetRegions()`
(*claimed*).

`CreateContext` opens with `using (var geometryTransaction = geometryStore.BeginInit())`, and
`BeginInit` is documented in `IGeometryStore` as clearing the store of any existing geometries and
preparing for an update (*claimed*,
[`IGeometryStore.cs`](https://github.com/xBimTeam/XbimEssentials/blob/e3c877712aeff39813219b9dd13383c266d07055/Xbim.Common/Geometry/IGeometryStore.cs)).
`IGeometryStoreInitialiser` offers only `AddShapeGeometry`, `AddShapeInstance`, `AddRegions` and
`Commit` — additive into an emptied store, with no update-one and no delete-one (*inferred*).
Changing one wall therefore means reprocessing the model.

What does exist is **stateless per-item construction**, usable as a building block but not wired to
the store: `IXShapeFactory.Build(IIfcGeometricRepresentationItem)` plus `Cut`, `Union`, `Transform`,
`Moved`, and `IXbimGeometryEngine.Create(IIfcGeometricRepresentationItem, …)`. An incremental layer
could be built on those, but the dependency tracking, the opening/feature resolution and the store
diffing would all be new code (*inferred*).

Searched across every `.cs`, `.cpp`, `.h` and `.md` in `XbimGeometry` for
`incremental|invalidate|dirty|recompute|regenerat|partial context|CreateContextForProduct|UpdateContext`.
Every hit is OCCT's `BRepMesh_IncrementalMesh` (an unrelated meshing class) or `Xbim.Tessellator`'s
internal sweep-line `Dirty` flag.

One further datapoint that bears on *any* plan to build on this API: `andyward` (**MEMBER**) states
the team "don't directly use the Scene/Xbim3DModelContext code - we drive the GeometryEngine and
Tessellator directly" ([#473](https://github.com/xBimTeam/XbimGeometry/issues/473)). The public
whole-model entry point is not the maintainers' own hot path.

## Known problems

Seven issues, with each speaker's login and their verbatim `authorAssociation`. `andyward`,
`SteveLockley`, `CBenghi` and `martin1cerny` are **MEMBER**; `bekraft` and `Ibrahim5aad` are
**CONTRIBUTOR**; reporters are marked individually.

| Issue | State / dates | What goes wrong | Root cause, and who says so |
|---|---|---|---|
| [#578](https://github.com/xBimTeam/XbimGeometry/issues/578) — short parameter-trimmed conics treated as full circles | OPEN, created 2026-09-07 | A ~351 mm profile segment becomes a ~320 m halo in a hospital export. Reproduces on 6.3.873, 6.3.891 and **6.3.897 — the exact commit pinned above** — and does not take the faulty branch in V5 | A dimensional-analysis error: the code "compares an angular parameter difference, in radians, with the IFC model precision" — reporter `tskarman` (**NONE**). `andyward` (**MEMBER**) replies "I'd be happy to take a PR with a covering test". Open and unfixed. **A V6-only regression relative to V5** |
| [#254](https://github.com/xBimTeam/XbimGeometry/issues/254) — incorrect geometry, missing booleans | OPEN since 2020-03-14, 33 comments | A file renders correctly in xBIM 4.0 and in a third-party checker but loses boolean operations in 5.1 | `SteveLockley` (**MEMBER**) first diagnoses "it is just a problem inside the OCC multi boolean code", then finds the booleans were fine and the artefact came from tessellation instead. `CBenghi` (**MEMBER**) concedes "there is no single approach that works in every scenario". See §On agreeing with other implementations |
| [#473](https://github.com/xBimTeam/XbimGeometry/issues/473) — V6 much slower than V5 | CLOSED 2024-04-26 | "it's taking 20-30 secs to process a single moderately complex representation item" — `andyward` (**MEMBER**) | V6 converts to BREP and uses "OCC's Tessellator - which seems to be orders of magnitude slower" (`andyward`, **MEMBER**). Fixed by making BREPs opt-in. BREP-first existed for accurate quantity take-off versus mesh-derived quantities |
| [#147](https://github.com/xBimTeam/XbimGeometry/issues/147) — very slow `IfcBooleanResult` cutting | CLOSED 2018-12-14 | Hundreds of chained booleans: "2-3+ minutes per operation" — `andyward` (**MEMBER**), ten minutes total | `SteveLockley` (**MEMBER**) optimised and multithreaded boolean union to 45 s, and notes such unions are "rarely found so we haven't had good test cases to work with" |
| [#570](https://github.com/xBimTeam/XbimGeometry/issues/570) — `CreateContext` fails inconsistently across machines | OPEN, created 2026-01-10 | Identical input, identical version, different machines: `General Error Creating IfcExtrudedAreaSolid` on sub-millimetre profiles. Some models then hang over a day without crashing | `andyward` (**MEMBER**) attributes it to `ModelFactor.Precision` differing between `MemoryModel` and `EsentModel` defaults. The reporter (`A-Shawqi`, **NONE**) adds a live API trap: "the Xbim3DModelContext constructor default engineVersion is still v5" |
| [#511](https://github.com/xBimTeam/XbimGeometry/issues/511) — are there performance metrics? | CLOSED 2024-12-07 | There are none published | `andyward` (**MEMBER**): "too many variables to given an answer other than 'It depends'". He proposes counting `IfcShapeRepresentation`s weighted by representation type, because `IfcBooleanResult` dominates cost, not file size |
| [#575](https://github.com/xBimTeam/XbimGeometry/issues/575) — IFC to wexBIM on Linux | CLOSED 2026-06-19 | No supported Linux path; the offered one is a contributor's fork with missing door and window openings | `martin1cerny` (**MEMBER**) redirects to `Ibrahim5aad` (**CONTRIBUTOR**), whose `native-engine` branch the reporter finds incomplete |

### On agreeing with other implementations

[#254](https://github.com/xBimTeam/XbimGeometry/issues/254) contains a design statement that bears
directly on P-10 and on how we read our own disagreement numbers. `bekraft` (**CONTRIBUTOR**, not a
team member) argues the principle: "the main goal is not to show geometry like platform X does" —
schema fidelity over visual agreement with other viewers. `CBenghi` (**MEMBER**) acknowledges the
compatibility tension in the same thread without endorsing a rule.

If that is xBIM's position, then "the implementations disagree" is partly a statement about
*objectives*, not only about bugs, and a benchmark whose criterion is "agrees with the other
implementations" is measuring something xBIM has not agreed to optimise. Our own criterion should
therefore be stated as agreement with the *schema's intent* where that is determinable, with
cross-implementation agreement as evidence rather than as the definition. Nothing in our measured
data depends on this; it changes how the numbers are read.

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** **No**, and the
   obstruction is the storage contract, not just the API surface — see §Incremental evaluation.
   *claimed + inferred.*
2. **What happens to geometry on an IFC round trip?** Not examined; no measurement was possible.
   *unknown.*
3. **Driven in-process from DynLex?** No reasonable path: managed .NET plus C++/CLI means hosting
   the CLR, on Windows only. *inferred.*
4. **Threading model?** Boolean union is multithreaded; the whole-model context is the parallel
   unit. Not characterised further. *claimed, partial.*
5. **What breaks first at scale?** Unknown — and there are no published metrics
   ([#511](https://github.com/xBimTeam/XbimGeometry/issues/511)). The failure modes on the tracker
   are time (#147, #473, #570's day-long hangs), not memory. *claimed.*
6. **Numeric precision?** Doubles. Tolerance from `ModelFactor.Precision`, whose default depends on
   the storage back-end (#570). *claimed.*
7. **Operate on a subset of the model?** The read side can (`ShapeInstancesOf(IIfcProduct)`); the
   *build* side cannot, because `BeginInit()` clears the store. *claimed + inferred.*
8. **Who maintains it?** xBimTeam; MEMBER responses through September 2026. The bus factor question
   is sharpened by the 6.x line living on a feature branch as a prerelease. *inferred.*
9. **Documented failure modes?** §Known problems, seven issues. *claimed.*
10. **Representations held natively?** OCCT B-rep and a triangulated mesh. *claimed.*
11. **How does geometry reach the GPU?** Via `wexBIM`, a tessellated stream format for the xBIM
    viewers, "only documented by the code" — `martin1cerny` (**MEMBER**), #575. *claimed.*
12. **What would we take, and what would we avoid?** §Verdict.

## Measurements

**None.** See the note at the top. The specific blocker, recorded so the decision is reproducible:

```
$ dotnet --list-sdks
                                   (no output, exit 0)
$ dotnet --version
The command could not be loaded, possibly because:
  * You intended to execute a .NET application: ...
$ dotnet --list-runtimes
Microsoft.NETCore.App 6.0.36 / 8.0.31 / 9.0.20 / 10.0.12  (+ ASP.NET, WindowsDesktop)
```

Runtimes without an SDK cannot build, and `Xbim.Geometry.Engine` needs more than an SDK — it needs
the MSVC v143 toolset and the Windows SDK for its C++/CLI project. This is not a "we ran out of
time" gap; it is a different toolchain.

## Strengths

- **Broadest schema coverage of the three**: IFC2x3 TC1, IFC4 Add2 and IFC4x3 Add2, with the
  EXPRESS sources in the tree. Where the geometry engine is Windows-only, `Xbim.Essentials` alone is
  cross-platform and is a legitimate parsing reference.
- **An explicit geometry-engine version switch** (`XGeometryEngineVersion.V5/V6`) with a
  DI-registered factory, so two engine generations coexist and a caller can pick. Compare
  IfcOpenShell's `geometry_library` parameter, which does the same thing for kernels rather than
  engine versions.
- **A stateless per-item shape factory** (`IXShapeFactory.Build/Cut/Union/Transform/Moved`) that is
  separate from the whole-model context. The separation is the right shape even though the store
  above it does not use it that way.
- **Honest maintainers on the record** about what is untested (#147's "rarely found so we haven't
  had good test cases"), what is unmeasured (#511) and what they themselves do not use (#473).

## Weaknesses

- Windows-only geometry, by compilation model rather than by packaging (§Platform).
- No incremental evaluation, and the store contract forecloses adding one without replacing
  `Xbim3DModelContext` and `IGeometryStore` (§Incremental evaluation).
- The stable geometry release is 5.1.820 on OCCT 7.6.3; the 6.x line that carries the current
  architecture is a prerelease with an open tolerance regression at its newest commit (#578).
- No published performance data at all (#511), so nothing here can be compared with our numbers.
- Licence needs a legal read rather than a README read: CDDL-1.0 in the licence files, an OCC
  Public Licence 6.5 shipped alongside an LGPL-2.1-with-exception claim in the Essentials README.
  The two repositories describe the same dependency differently.

## Risks

If we ever needed a third geometry opinion for a specific disputed element, standing this up is not
a small task: a Windows machine with Visual Studio 2022 and the v143 toolset, a prerelease package
off a feature branch, and a known tolerance regression in the version that would be used. The risk
of *not* doing it is that P-10's disagreement counts rest on two implementations. The mitigation we
took instead — comparing two kernels *inside* IfcOpenShell, which shares one parser and one schema
mapping between them — isolates the kernel better than a third full implementation would have, and
is in [`compare.md`](../../../spikes/incremental-evaluation/results/compare.md).

## Verdict

### Build on — **no**, for the `ifc/` sub-project and for ADR-0004

The disqualifying assumption is not geometric, it is architectural and it is **two** assumptions,
either of which is sufficient:

1. **The geometry engine is C++/CLI and therefore Windows-only.** This is a compilation model, not
   a build flag. Using it from DynLex would mean hosting the CLR on Windows and shipping nothing
   else.
2. **Whole-model regeneration is enforced at the storage contract.** `IGeometryStore.BeginInit()`
   clears the store; `IGeometryStoreInitialiser` has no update-one. There is no seam at which
   per-element re-evaluation could be added without replacing both `Xbim3DModelContext` and
   `IGeometryStore` — that is, without replacing the part of xBIM that would have been the reason
   to adopt it.

Neither depends on a measurement, which is fortunate, because none was possible.

### Borrow from — three things, pinned

| What | Why | Where |
|---|---|---|
| **A versioned geometry-engine selector as a first-class option** (`XGeometryEngineVersion.V5/V6`, DI-registered, defaulted, documented as "the default version of the native Geometry Engine to use") | Two engine generations coexist in one product, and a caller can pin one per model. We will need exactly this when our own kernel's algorithms change under existing files. Note the trap #570 records: the *constructor* default lagged the documented default, and users hit the old engine without knowing | [`Enums/XGeometryEngineVersion.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.Geometry.Abstractions/Enums/XGeometryEngineVersion.cs), [`Configuration/GeometryEngineOptions.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.Geometry.Engine.Interop/Configuration/GeometryEngineOptions.cs) |
| **The stateless shape factory, separated from the model-level context** — `Build`, `Cut`, `Union`, `Transform`, `Moved` on a representation item, with no store and no model state | This is the right decomposition, and xBIM demonstrates it while *not* exploiting it: the layer above throws the separation away by clearing the store. Our evaluation layer should sit on a factory like this and keep the per-element identity the factory already has | [`IXShapeFactory.cs`](https://github.com/xBimTeam/XbimGeometry/blob/be4a6b95eec0b73140cbfd4a51300152c9e33781/Xbim.Geometry.Abstractions/Factories/IXShapeFactory.cs) |
| **`andyward`'s cost model for IFC geometry** (**MEMBER**, #511): the independent variable is the count of `IfcShapeRepresentation`s **weighted by representation type**, because `IfcBooleanResult` dominates — not file size, not element count | Our own benchmark set is described by element count and file size. This says both are the wrong axis. Our per-element distribution supports him: on IFC_Schependomlaan the median element costs 2.2 ms and the slowest 556 ms, and the expensive ones are a *type*, not a size | [XbimGeometry#511](https://github.com/xBimTeam/XbimGeometry/issues/511); our numbers in [`ifcopenshell.md`](ifcopenshell.md) §Per-element evaluation |

### Avoid — each mapped to a design choice, each with a P-row

Only rows that map to a `problems.md` row appear here. Two further observations from the tracker
— that the public whole-model entry point is not the maintainers' own path (#473), and that no
performance figures are published at all (#511) — are maturity findings rather than design
problems, and are in §Weaknesses instead.

| Failure | Design choice it traces to | Our design's answer |
|---|---|---|
| **One changed element forces the whole model's geometry to be rebuilt.** `CreateContext` is the only build entry point and `BeginInit()` clears the store | The geometry store is modelled as a build *artefact* regenerated wholesale, not as state with identity per element | Geometry is addressed per handle and the evaluation graph decides what is stale (spec §3). **P-06** |
| **A tolerance derived from a storage back-end's default, so the same file succeeds on one machine and fails on another** (#570) | Precision is a property of the *model container*, inherited implicitly, rather than of the geometry or the operation | Tolerances are explicit and per-entity, never inherited from a storage choice (spec §5). **P-05**, and see the new row P-24 |
| **An angular quantity compared against a length tolerance** (#578): radians tested against the model's length precision, turning a 351 mm arc into a 320 m circle | One scalar `precision` used for every comparison regardless of the quantity's dimension | Tolerances carry the dimension of the quantity they bound; an angular comparison cannot be fed a length (spec §5). **P-05**, new row P-24 |

## Sources

- [xBimTeam/XbimGeometry](https://github.com/xBimTeam/XbimGeometry) at
  `be4a6b95eec0b73140cbfd4a51300152c9e33781` (tag `XbimGeometry_netcore_6.3.897`) and
  `0271bb030ce6789e0cbbf32e2663da798af00764` (tag `XbimGeometry_master_5.1.820`)
- [xBimTeam/XbimEssentials](https://github.com/xBimTeam/XbimEssentials) at
  `e3c877712aeff39813219b9dd13383c266d07055` (tag `XbimEssentials_master_6.1.605`)
- Issues [#147](https://github.com/xBimTeam/XbimGeometry/issues/147),
  [#254](https://github.com/xBimTeam/XbimGeometry/issues/254),
  [#473](https://github.com/xBimTeam/XbimGeometry/issues/473),
  [#511](https://github.com/xBimTeam/XbimGeometry/issues/511),
  [#570](https://github.com/xBimTeam/XbimGeometry/issues/570),
  [#575](https://github.com/xBimTeam/XbimGeometry/issues/575),
  [#578](https://github.com/xBimTeam/XbimGeometry/issues/578)
- NuGet package listings for `Xbim.Geometry` and `Xbim.Essentials` (version and publication dates)
- [`compare.md`](../../../spikes/incremental-evaluation/results/compare.md) — the two-way
  disagreement analysis this note explains the absence of a third side of
