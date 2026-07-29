# Spikes

Throwaway experiments that answer one question with a measurement.

## Rules

**Spikes are throwaway.** They are exempt from quality standards and must never grow into the
product. A spike that starts looking like a foundation has stopped being a spike, and the
temptation to keep it is how research code becomes production architecture nobody chose.

**No conclusions without measurements.** A spike ending in an impression has not finished.

**The pass/fail criterion is written before the spike runs.** Criteria written afterwards get
rationalised into agreement with whatever happened. The criteria live in
[`../docs/risks.md`](../docs/risks.md).

## Structure

```
spikes/<name>/
├── README.md      the question, and how to run this
├── FINDINGS.md    what was measured and what it means
└── <code>
```

`FINDINGS.md` must record:
- The question, restated
- Hardware, OS, library versions
- Which model from [`../reference/`](../reference/) was used
- Method, reproducible enough that someone else gets the same number
- Results as numbers
- Verdict against the pass/fail criterion
- What this means for the decision — including "this does not settle it, because…"

## Planned spikes

From the critical risks in [`../docs/risks.md`](../docs/risks.md):

| Spike | Question | Risk |
|---|---|---|
| `incremental-evaluation/` | Can a candidate kernel re-evaluate one changed element cheaply? | R-01 |
| `geometry-seam/` | Does converting between fast-mesh and exact geometry lose what 2D and IFC export need? | R-02 |
| `blender-ceiling/` | Is Blender's scale limit architectural, or Bonsai's implementation? | R-03 |
| `renderer-scale/` | What does 100k selectable elements at interactive frame rates actually cost? | R-04 |

R-03 is worth running early despite Blender not being the current hypothesis: it is cheap, and
its result either eliminates a whole branch of the host decision or reopens it.

## Note on phase discipline

Spikes are the only code permitted during phases 0–3. If you find yourself writing something
that is not answering a question from the risk register, stop — it belongs to a later phase, or
to a risk that has not been written down yet.
