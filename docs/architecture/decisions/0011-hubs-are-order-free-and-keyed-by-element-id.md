# ADR-0011 — Hubs are order-free and keyed by element id

**Status:** accepted
**Date:** 2026-10-31 (decided in #13 on 2026-10-28, recorded here)
**Deciders:** the maintainer

## Context

The module split (#13, `docs/superpowers/specs/2026-10-28-module-split-design.md`) replaces
hand-written hubs by dispatchers composed from the `MODULE` manifests. The scene hub
(`viewer/bim_scene.dl`) built one list in a fixed kind order and reused kept meshes **by
position**. A dispatcher calls modules in layer order and a program may carry only some modules,
so positions stop lining up; the whole-remake fallback only fired when the count differed, so a
wrong mesh could be reused without any error.

## Decision

Hubs are order-free. Anything a hub keeps between runs (meshes, plan lines, read and write
records) is found by element id and part, never by position in a list. A module's contribution
is tagged with its element id; the order in which the dispatcher calls modules is not part of any
contract.

## Options considered

### Reuse by element id (chosen)
A program is a *set* of modules, and the set differs per program. Only identity survives that.

### Keep positions, one segment per module
Still positional: the hub would have to know which modules are present and in what order, which
is the coupling the split removes.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| Positional reuse breaks silently under a dispatcher | #13, the scene-point finding and decision | inferred (reasoning shown there) |
| Scene by id keeps every test outcome | #13: PRs #19 and #20; full set 210 PASS of 235, the same 25 non-PASS as before | measured |

## Consequences

**What this makes easier:** a module can be switched off or tested alone (`scene_alone`).

**What this makes harder:** every kept item needs a stable id and part key, and an index built per
run.

**What this commits us to:** no new positional bookkeeping in any hub.

**What we would have to change to reverse it:** a new ADR, and fixing the module order into the
composer.
