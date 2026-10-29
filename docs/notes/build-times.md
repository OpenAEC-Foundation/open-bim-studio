# Build times

Wall time and peak memory of the builds that matter, measured with
`/usr/bin/time -v` on the same machine before and after each restructuring
stage (design §11). Extrapolations are never written here; only runs.

Machine for every row below: AMD Ryzen 7 9700X (8 cores, 16 threads), 29 GB
RAM, Ubuntu 26.04.1, clang-20. Compiler: the fork at `c2d32bea` with the six
patches of `patches/`, SHA-256 `1b233f8c2439847d56c180618f79699042c69ec214c80ab72887ccc5e3cf5eeb`.
Trees: `main` at `f647f38` (before), `restructure/one-tree` at `75ba24b`
(after; the later commits on the branch touch no compiled source); the
later rows name their `main` commit. Peak RSS
is the largest process of the run. One compiler at a time, except the two
`build.sh test` (all) rows, whose parallelism is stated; those two are not
comparable with each other or with a sequential run. Full results and the
test-by-test comparison are in issue 11.

| target | stage | wall time | peak RSS | compiler | machine | date |
|---|---|---|---|---|---|---|
| `build.sh app` (`-O2`) | before stage 1 | 12:06.87 | 3.94 GB | `c2d32bea` + patches | Ryzen 7 9700X, 29 GB | 2026-10-27 |
| `build.sh dev` (`-O0 -g`) | before stage 1 | 10:59.23 | 3.33 GB | same | same | 2026-10-27 |
| `build.sh test ifc_read` | before stage 1 | 1:17.05 | 1.49 GB | same | same | 2026-10-27 |
| `build.sh test editor` | before stage 1 | 4:20.30 | 2.52 GB | same | same | 2026-10-27 |
| `build.sh test sketch` | before stage 1 | 4:21.15 | 2.53 GB | same | same | 2026-10-27 |
| `build.sh test api` | before stage 1 | 6:58.07 | 2.99 GB | same | same | 2026-10-27 |
| `build.sh test` (all 224, four streams with separate `BIM_BUILD_DIR`) | before stage 1 | 2:41:31 | 3.20 GB per stream | same | same | 2026-10-28 |
| `build.sh app` (`-O2`) | after stage 1 | 11:57.97 | 3.95 GB | same | same | 2026-10-28 |
| `build.sh dev` (`-O0`, `BIM_DEBUG=0`) | after stage 1 | 10:55.18 | 3.28 GB | same | same | 2026-10-27 |
| `build.sh dev-test sheet_cache import_metadata_cache` | after stage 1 | 11:00.61 | 3.34 GB | same | same | 2026-10-27 |
| `build.sh test ifc_read` | after stage 1 | 1:16.61 | 1.50 GB | same | same | 2026-10-28 |
| `build.sh test editor` | after stage 1 | 4:27.16 | 2.53 GB | same | same | 2026-10-27 |
| `build.sh test sketch` | after stage 1 | 4:19.26 | 2.52 GB | same | same | 2026-10-28 |
| `build.sh test api` | after stage 1 | 6:58.41 | 2.99 GB | same | same | 2026-10-28 |
| `build.sh test` (all 224, `BIM_JOBS=8`) | after stage 1 | 1:24:06 | 3.20 GB per process | same | same | 2026-10-27 |
| `kernel/tests/verify.py --optimization O0` (214 fixtures) | after stage 1 | 7:50.25 | 1.05 GB | same | same | 2026-10-27 |
| `build.sh dev` (`-O0`, `BIM_DEBUG=0`) | after the module move (`0c04769`) | 11:30.88 | 3.34 GB | same | same | 2026-10-28 |
| `build.sh test editor` | after the module move | 4:42.14 | 2.61 GB | same | same | 2026-10-28 |
| `build.sh test` (all 235, `BIM_JOBS=8`) | after the module move | 1:34:49 | 3.28 GB per process | same | same | 2026-10-28 |
| `kernel/tests/verify.py --optimization O0` (212 fixtures) | after the module move | 7:50.25 | 1.05 GB | same | same | 2026-10-28 |
| `build.sh test` (all 236, `BIM_JOBS=8`) | after C2 records, scene by id, scene point (`563b0ae`) | 1:31:31 | 3.28 GB per process | same | same | 2026-10-28 |
| `build.sh app` (`-O2`) | after C2 records, scene by id, scene point (`d1ae7d9`) | 12:41.20 | 3.95 GB | same | same | 2026-10-28 |
| `build.sh test evaluate` (one planar test against the generated files) | before C2 (`0c04769`) / after (`4c5509c`) | 82.58 / 76.52 | 1.37 / 1.36 GB | same | same | 2026-10-28 |
| `build.sh kernel` (`kernel/api/exposed.dl`, `--emit-object --no-main -O2`, seam step 2) | after the module move (`c5fdfc8`) | 7.37 s | 0.58 GB | same | same | 2026-10-28 |

Earlier observations, recorded in `findings.md` rather than measured for this
table: the application 40 to 51 minutes at `-O2`; `tests/ifc_read.dl` 13 to 18
minutes at `-O0`; one editor test peaking at 9.6 GB (dynlex issue 13, before the
fix of 2026-10-16). Those came from a slower machine; the rows above are the
baseline for every later stage on this one.
