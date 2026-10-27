# Known fixture failures

The fixtures under `kernel/tests` are the kernel's test set; `verify.py` runs
them against the compiler named by `.dynlex-root.local` or `DYNLEX_ROOT`. The
authoritative result is a Linux run with the pinned compiler (the fork's
`codex/cadkernel-port` at `c2d32bea` with the six patches of `patches/`); a
Windows run with another compiler differs in diagnostics and timing.

## State on 2026-10-27

Until the final review of the restructuring, 130 of the 214 fixtures still
imported `tests/cadkernel/…`, a path that exists only in the fork checkout, and
so compiled the fork's stale kernel copy instead of `kernel/`. Those imports
now point at `kernel/reference/…`. The first authoritative run of the whole
set against `kernel/` is pending on the Linux machine (issue 11); its counts
and failure names replace this section when they are in.

The nine fixtures below failed in the earlier run among the 84 that already
compiled `kernel/`. Their causes predate the restructuring: the fixtures came
from the fork's port of the kernel, while the kernel compiled here is the
application's overlay of it (21 files rewritten, 6 added; ADR-0007), under a
compiler with the pattern patches applied. They are findings for the kernel
owner, not regressions of the move, and their expectations were left alone so
that the divergence stays visible.

| Fixture | Failure | Reason seen |
|---|---|---|
| `acis_append_analytic` | compile error in `kernel/acis/acis_append_faceted.dl` (`if coedge` on a pointer) | the overlay's coedge and pcurve records differ from the port's that the ACIS files were written against |
| `brep_sweep_path_body` | no overload for `usage's pcurve's value` on `a cad pcurve result` | the same pcurve record change |
| `managed_surface_incomplete` | diagnostics name `kernel/core/topology_list.dl` where the expectation names `kernel/brep/brep_topology.dl` | the overlay keeps the topology list in its own file |
| `arena_missing_clone`, `arena_wrong_clone` | extra inference notes in the diagnostics | the overlay's `arena.dl` (407 lines) differs from the port's (345) |
| `brep_geometry_extra` | "assignment target is not writable" where the port expected success | the overlay's geometry records, or the compiler patches |
| `brep_loft_general_body_open` | an extra warning, "Repeated pattern word 'previous' stays literal" | emitted by the patched compiler |
| `brep_mesh_missing_faces` | runtime exit 1: "wireframe reports missing surface" | the overlay's `brep_mesh.dl` (5,378 lines) replaced the port's (2,557) |
| `brep_mesh_nurbs` | runtime exit 1: "outward winding" | the same |

To reproduce one: `python3 -B kernel/tests/verify.py --filter NAME --optimization O0`.
