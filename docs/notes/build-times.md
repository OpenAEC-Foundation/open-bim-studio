# Build times

Wall time and peak memory of the builds that matter, measured with
`/usr/bin/time -v` on the same machine before and after each restructuring
stage (design §11). Extrapolations are never written here; only runs.

| target | stage | wall time | peak RSS | compiler | machine | date |
|---|---|---|---|---|---|---|
| `build.sh app` (`-O2`) | before stage 1 | pending (computer 1) | | `c2d32bea` + patches | | |
| `build.sh dev` (`-O0 -g`) | before stage 1 | pending (computer 1) | | | | |
| `build.sh test ifc_read` | before stage 1 | pending (computer 1) | | | | |
| `build.sh test editor` | before stage 1 | pending (computer 1) | | | | |
| `build.sh test sketch` | before stage 1 | pending (computer 1) | | | | |
| `build.sh test` (all) | before stage 1 | pending (computer 1) | | | | |

Earlier observations, recorded in `findings.md` rather than measured for this
table: the application 40 to 51 minutes at `-O2`; `tests/ifc_read.dl` 13 to 18
minutes at `-O0`; one editor test peaking at 9.6 GB (dynlex issue 13, before the
fix of 2026-10-16).
