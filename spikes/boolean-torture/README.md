# `boolean-torture`

**Question (R-16):** does a candidate kernel's boolean survive coplanar faces, shared edges,
touching vertices, identical operands, containment, a near-zero-thickness slab, a near-degenerate
triangle and a wall cut by twelve openings — producing a valid closed result each time, with
`V(A∪B) + V(A∩B) = V(A) + V(B)`?

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-16, written before any
driver ran: pass is every case valid and the volume identity within 1e-9 relative; fail is any
invalid result or a volume error above 1e-6 relative.

The cases are fixed in [`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py)
and are the same ten pairs for every candidate. A driver may not add, drop or adjust a case.

## Layout

```
occt_common.py        shared OCCT helpers (mesh -> solid, boolean, volume, tolerance)
occt_driver.py        the OCCT driver
results/<candidate>.md raw results, one file per candidate, written by that candidate's driver
FINDINGS.md           assembled across candidates once they have all run
```

`FINDINGS.md` is written from the `results/` files, not from a single run.

## Running the OCCT driver

```bash
pip install cadquery-ocp==8.0.1.0.0      # bundles OCCT 8.0.1
python spikes/boolean-torture/occt_driver.py
```

from the repository root. It writes [`results/occt.md`](results/occt.md) and prints a one-line
summary. `--repeats N` changes how many times each boolean is timed (the fastest is reported).

The construction method — triangle soup to `TopoDS_Solid` — is documented in `occt_common.py` and
is part of the measurement: a case whose operands OCCT cannot build is a finding about OCCT.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Standard library plus the candidate's
own bindings only; nothing here is a design proposal for `kernel/`.
