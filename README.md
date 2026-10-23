# Open BIM Studio

Open BIM Studio is a native BIM modeller developed in **DynLex**. The current
application lives in [spikes/dynlex-bim-slice](spikes/dynlex-bim-slice/README.md):
parametric building elements, reinforcement, direct geometry editing, IFCX
persistence, views, drawings and sheets.

**main is the shared development baseline.** Use a short task branch from main
and submit a PR back to main. A merged commit is not automatically a tested release.
The local October 2026 consolidation is recorded in
[docs/CONSOLIDATIE.md](docs/CONSOLIDATIE.md).

## Start here

| Purpose | Location |
|---|---|
| Build and run the modeller | [Application README](spikes/dynlex-bim-slice/README.md) |
| Coordinate work on two computers | [Working agreement](docs/TWEE-COMPUTERS.md) |
| See ownership and unfinished work | [Task board](docs/WERKBORD.md) |
| Prepare Windows packages | [Windows build instructions](spikes/dynlex-bim-slice/ci/WINDOWS-RELEASE.md) |
| Review the branch consolidation | [Consolidation report](docs/CONSOLIDATIE.md) |

The application overlay is staged over a separate DynLex compiler checkout.
Set DYNLEX_ROOT to that checkout and give each build its own BIM_BUILD_DIR.
Run at most one DynLex compiler per physical computer; compilation can require
several GB of memory. Do not close another person's running app to make room.
BIM product logic remains DynLex; the C platform bridge and build helpers are
infrastructure. Private project drawings and models stay outside this public repo.

## Status

This is active development. The consolidated code includes the Linux application,
Windows port, Sketch tools, wall-layer editing and plate-opening geometry. The
plate-opening GUI is incomplete. Full application/GUI validation and native
Windows installer validation are still required before a new release.

## Research and architecture

The repository began as a research programme. Its original findings and decisions
remain available; older research documents may describe plans predating the app.

- [Vision](docs/vision/vision.md) and [scope](docs/vision/non-goals.md)
- [Architecture](docs/architecture/layers.md) and [build brief](docs/BUILD-BRIEF.md)
- [Research roadmap](docs/roadmap.md) and [risks](docs/risks.md)
- [Research contribution guide](CONTRIBUTING.md)

Other directories under spikes contain experiments; they are not alternative
production branches of the modeller. Compiler development belongs in the separate
DynLex repository, with its exact revision recorded for reproducible builds.
