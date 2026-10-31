# Development

Read first, in the repository: [CLAUDE.md](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/CLAUDE.md), the [DynLex guide](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/docs/notes/dynlex-guide.md), [layering](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/docs/notes/layering.md) and the [module owners](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/docs/OWNERS.md).

## Building

The compiler is a separate DynLex checkout, named in `.dynlex-root.local` or by `DYNLEX_ROOT`.

```sh
bash build.sh dev                 # the application: build/open-bim-studio-dev (about 8–10 min, about 3 GB of memory)
bash build.sh test NAME ...       # the named tests (all tests without names)
BIM_JOBS=3 bash build.sh test     # tests in parallel
bash build.sh generate            # the generated imports only
bash scripts/check-layers.sh      # the import direction between layers
```

`build.sh generate` (run by every command) writes `generated/`: the window style per platform, the self-test entry, the composed model record and dispatchers (`tools/compose_modules.py`), and `generated/version.dl` (`tools/write_version.py`: `BIM_VERSION` or `YYYY.W dev`, plus the short commit). The Windows build scripts and the Windows CI call the same tools.

## Layout

The application lives in module directories, one per domain, in layers. A module holds its tests in `tests/` and a `MODULE` manifest.

| Layer | Directories |
|---|---|
| 0 kernel | `kernel/` (core, fast, planar, nurbs, space, brep, acis, api) |
| 1 model | `bim/` |
| 2 services | `viewer/`, `exchange/`, `ifc/`, `views/`, `materials/`, `localisation/`, `automation/`, `ui/editor/` |
| 3 shape classes | `elements/` (linear, planar, object, connection), `pattern/` |
| 4 disciplines | `structural/`, `architectural/`, `mep/` |
| 5–6 UI | `ui/properties/`, `ui/panels/` |
| 7 shell | `ui/shell/` (`main.dl`, the window and its event loop) |

Also: `tools/`, `installer/`, `platform/` (the C shim), `patches/`, `lib/`, `spikes/` (throwaway experiments only).

## Tests

A test is a `.dl` program in a module's `tests/` with an `.expected.txt` beside it; `build.sh test` compiles it, runs it and compares the output. A handful of tests are known to fail on `main` and are tracked as such; a change must not add to them.

## Getting changes into main

- Since 31 October 2026 work for computer 1 goes to `main` directly: a short task branch is merged locally after its tests pass and the app builds, then `main` is pushed. Branches of other contributors still go through pull requests.
- Commit messages describe the change, in English. Repository content is English (except `README.nl.md`).
- Settled decisions are ADRs in `docs/architecture/decisions/`; research notes follow `docs/research/_template.md`.

## Conventions worth knowing

- DynLex has no `continue`; `and`/`or` evaluate both sides.
- A local variable whose name is also a word in a function's pattern breaks overload resolution.
- The editor record (`bim editor record`) is constructed in one place, `a new bim editor`; new members go at its end.
- Command codes and setting codes are reserved in `docs/WERKBORD.md`.
