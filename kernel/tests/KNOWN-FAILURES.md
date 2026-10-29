# Known fixture failures

The fixtures under `kernel/tests` are the kernel's test set; `verify.py` runs
them against the compiler named by `.dynlex-root.local` or `DYNLEX_ROOT`. The
authoritative result is a Linux run with the pinned compiler (the fork's
`codex/cadkernel-port` at `c2d32bea` with the seven patches of `patches/`); a
Windows run with another compiler differs in diagnostics and timing.

## Authoritative run, 2026-10-27

`python3 -B kernel/tests/verify.py --optimization O0` on computer 1 (Linux,
pinned compiler, issue 11): 173 passed, 41 failed, 0 not run, in 7:50 wall
time with a 1.1 GB peak.

Two of the 41 were the restructuring's: `lab_model` and `lab_state` imported
`kernel/reference/lab/…`, the fork's lab programs, which the move left out
because they are not kernel reference programs. The two fixtures tested those
programs, not the kernel, and were removed with them. The set is therefore
212 fixtures, of which 173 pass and 39 fail.

The 39 failures predate the restructuring: the fixtures came from the fork's
port of the kernel, while the kernel compiled here is the application's
overlay of it (21 files rewritten, 6 added; ADR-0007), under a compiler with
the pattern patches applied. They are findings for the kernel owner, not
regressions of the move, and their expectations were left alone so that the
divergence stays visible. By cause:

| Count | Failure | Reason seen |
|---|---|---|
| 6 | compile error in `lib/std.dl`: "Logical operator 'if condition' requires a boolean operand, got 'a pointer to a cad coedge'" (the ACIS append, lift and history fixtures) | the overlay's coedge record differs from the port's that the ACIS files were written against |
| about 10 | "No overload matches call '…'s pcurve's value' for argument types [a cad pcurve result]" (`brep_pcurve*`, `brep_place*`, `brep_sweep_path_body`, `brep_topology_ownership`, loft and split variants) | the overlay's pcurve result record |
| 2 | `brep_debug`: no `cad debug text` overload for `a cad coedge adjacency`; `brep_split` expects a `cad topology list` and gets `a cad coedge adjacency` | the overlay replaced topology lists by adjacency values |
| several | diagnostics mismatches: `brep_geometry_extra` ("assignment target … is not writable"), `managed_surface_incomplete`, `arena_*`, `arclength3*`, `lengthen3*` | overlay files that differ from the port's, or notes the patched compiler adds |
| 2 | runtime exit 1: `brep_mesh_missing_faces` ("wireframe reports missing surface"), `brep_mesh_nurbs` ("outward winding") | the overlay's `brep_mesh.dl` (5,378 lines) replaced the port's (2,557) |

The per-fixture list with one-line causes from that run replaces this table
when the final Linux report on issue 11 is in.

An indicative Windows run with an older compiler (167 passed of 214, before
the two lab fixtures were removed) differs mainly in path spellings inside
diagnostics and in the 30-second compile budgets; it is not authoritative.

To reproduce one: `python3 -B kernel/tests/verify.py --filter NAME --optimization O0`.
