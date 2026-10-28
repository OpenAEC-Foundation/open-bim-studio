# Module owners

One owner per module, from the module split design
(`superpowers/specs/2026-10-28-module-split-design.md`). The owner merges the
pull requests that touch only their module, keeps its tests green and decides
its public patterns. A change to `bim/`, to a service's API or to the
composition rules is its own pull request, merged before the modules that need
it. `.github/CODEOWNERS` mirrors this table; "unassigned" modules fall to the
maintainer until someone claims them here, in one commit that names the
computer and the person.

| Layer | Module | Directory | Owner |
|---|---|---|---|
| 0 | kernel-core | `kernel/core`, `kernel/fast` | unassigned |
| 0 | kernel-planar | `kernel/planar` | unassigned |
| 0 | kernel-nurbs | `kernel/nurbs`, `kernel/space` | unassigned |
| 0 | kernel-brep | `kernel/brep`, `kernel/acis` | unassigned |
| 1 | bim | `bim/` | maintainer |
| 2 | viewer | `viewer/` | Elize, computer 1 (Linux) |
| 2 | native format (IFCX) | `exchange/ifcx` | Elize, computer 1 (Linux) |
| 2 | ifc | `ifc/` | Elize, computer 1 (Linux) |
| 2 | dxf and dwg | `exchange/dxf_dwg` | Elize, computer 1 (Linux) |
| 2 | step | `exchange/step` | Elize, computer 1 (Linux) |
| 2 | import | `exchange/import` | Elize, computer 1 (Linux) |
| 2 | views | `views/common` | Elize, computer 1 (Linux) |
| 2 | drawings | `views/drawings` | Elize, computer 1 (Linux) |
| 2 | sheets | `views/sheets` | Elize, computer 1 (Linux) |
| 2 | schedules | `views/schedules` | Elize, computer 1 (Linux) |
| 2 | export | `views/export` | Elize, computer 1 (Linux) |
| 2 | materials | `materials/` | Elize, computer 1 (Linux) |
| 2 | localisation | `localisation/` | Elize, computer 1 (Linux) |
| 2 | automation | `automation/` | Elize, computer 1 (Linux) |
| 2 | editor framework | `ui/editor` | Elize, computer 1 (Linux) |
| 3 | linear | `elements/linear` | Elize, computer 1 (Linux) |
| 3 | connection | `elements/connection` | Elize, computer 1 (Linux) |
| 3 | planar | `elements/planar` | Elize, computer 1 (Linux) |
| 3 | object | `elements/object` | Elize, computer 1 (Linux) |
| 3 | pattern | `pattern/common`, `pattern/grids`, `pattern/facade` | Elize, computer 1 (Linux) |
| 4 | structural | `structural/rebar`, `structural/steel`, `structural/results` | Elize, computer 1 (Linux) |
| 4 | architectural | `architectural/openings`, `architectural/stairs`, `architectural/spaces` | Elize, computer 1 (Linux) |
| 4 | mep | `mep/common` | Elize, computer 1 (Linux) |
| 5 | properties | `ui/properties` | Elize, computer 1 (Linux) |
| 6 | panels | `ui/panels` | Elize, computer 1 (Linux) |
| 7 | shell | `ui/shell` | maintainer |
| – | build, CI, installers, platform shim, tools | `build.sh`, `scripts/`, `.github/`, `installer/`, `platform/`, `tools/` | maintainer |

Modules that exist only as a name in the design (`pattern/levels`,
`structural/common`, `structural/concrete`, `structural/prefab`,
`structural/timber`, `architectural/common`, `mep/hvac`, `mep/piping`,
`mep/electrical`, `extensions/`, `collaborate/`, `site/`, `infra/`,
`quantities/`, `planning/`, `analysis/`) get their directory, manifest and
owner when work on them starts.

## How to claim

1. Put your name and computer in the Owner column, in one commit on `main`.
2. Work on branches `mod/<module>/<topic>`; open a pull request per change.
3. Keep `scripts/check-layers.sh` silent: new imports against the layer order
   are refused; removing an edge from `scripts/layer-baseline.txt` is welcome.
4. Run your module's tests before every pull request: `bash build.sh test
   <name>…` with the names of the tests in `<module>/tests/`.
