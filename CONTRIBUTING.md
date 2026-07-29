# Contributing

This is a research repository. Contributions are documents, measurements, and decisions — not
code. The goal is that when the build starts, nobody has to think about architecture again.

## Where things go

| You have… | Put it in |
|---|---|
| An evaluation of a library, kernel, or engine | `docs/research/<category>/<name>.md` |
| An observation about an existing BIM/3D tool | `docs/research/prior-art/<tool>.md` |
| Domain knowledge (IFC, drawings, standards) | `docs/domain/` |
| A decision that is now settled | `docs/architecture/decisions/` as an ADR |
| An open question or unknown | `docs/risks.md` |
| Code that proves or disproves something | `spikes/<name>/` with a `FINDINGS.md` |
| A specification, schema, or benchmark model | `reference/` (see its README about binaries) |

If you cannot tell where something belongs, it is usually a sign the item mixes two things.
Split it.

## Writing a research note

Copy `docs/research/_template.md`. Three rules do most of the work:

**Start with the decision question.** Not "IfcOpenShell" but "Can IfcOpenShell serve as our
semantic kernel without forcing OCCT on the real-time path?" A note that does not answer a
question does not need to exist.

**Separate claimed from measured.** Documentation claims and benchmark results are different
kinds of evidence. Label which one you have. A vendor's performance claim is a hypothesis; your
measurement is a finding.

**End with a verdict.** Even a provisional one. If the verdict is "insufficient evidence", name
the specific experiment that would settle it and add it to `docs/risks.md`.

## Writing an ADR

When a decision is settled, record it in `docs/architecture/decisions/` using `_template.md`.
Number sequentially. Include the options rejected and why — the rejected options are the most
valuable part, because they are what stops the decision being reopened every time somebody new
joins.

ADRs are immutable once accepted. To change a decision, write a new ADR that supersedes the old
one and update the old one's status.

## Running a spike

Spikes are throwaway code that answers one question. They are exempt from quality standards and
must never grow into the product.

Each spike gets a directory in `spikes/` containing:
- Whatever code is needed
- A `README.md` — the question and how to run it
- A `FINDINGS.md` — what was measured, on what hardware, against which model from `reference/`,
  and what it means for the decision

**No conclusions without measurements.** A spike that ends in an impression rather than numbers
has not finished.

## Language and naming

English for everything written to disk. See `CLAUDE.md` for the full rules, including this
repository's explicit exception allowing BIM and 3D software to be named in prior-art research.

Do not commit conversation transcripts. `PROMPTS.md` holds originating prompts only.

## Commits

Describe the change, in English, in the imperative. Keep research and structural changes in
separate commits. Never describe the conversation that led to a change.

## Working in parallel

Claim work by opening an issue or by adding your name next to an item in `docs/risks.md`. The
risk register is the shared backlog — if it is not there, it is not tracked.
