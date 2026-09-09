# Research

The bulk of the preparation work. Every note answers one decision question, cites its evidence,
and ends with a verdict.

Use [`_template.md`](_template.md). Rules are in [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).

## Categories

| Directory | Question it serves |
|---|---|
| [`kernels/`](kernels/) | Which semantic and geometry kernels do we build on? **The decisive one.** |
| [`hosts-and-engines/`](hosts-and-engines/) | Standalone application, or built inside an existing host? |
| [`renderers/`](renderers/) | How do we draw 10⁵–10⁶ elements interactively? |
| [`prior-art/`](prior-art/) | What do existing tools get right, get wrong, and what do we take? |

## Method

The order matters: **the measuring stick before the candidates.** Otherwise evaluation becomes
an exchange of preferences, and whoever writes the last note wins.

1. Fix the criteria and their weights (done per category, in that category's README).
2. Fix the benchmark set once, in [`../../reference/`](../../reference/). All candidates are
   measured on the same models.
3. Evaluate every candidate on every axis. An unknown is recorded as unknown, not skipped.
4. Shortlist to two.
5. Falsify the shortlist with spikes in [`../../spikes/`](../../spikes/). Documentation claims
   do not survive contact with measurement often enough to be trusted.

## Evidence discipline

Label every claim:

- **Claimed** — stated by documentation, a maintainer, or a third party. Cite the URL.
- **Measured** — we ran it. State hardware, model, version, and method.
- **Inferred** — our reasoning from other facts. Show the reasoning.

Most published performance numbers are *claimed*. Treat them as hypotheses to test, not as
findings.

## Traceability

Decisions must be traceable to evidence years later, by someone who was not there.

- Every note records the **version or commit hash** of what it read or measured. Links point at
  that commit, not at a moving branch.
- Every note names the **decision it serves** — an ADR number or a spec section — in its header.
- Every ADR carries an **evidence table**: claim → note and section → evidence type. An ADR with
  an empty cell stays `proposed`.
- [`kernels/problems.md`](kernels/problems.md) indexes problem → root cause → candidates →
  evidence → our design's answer. It is the cross-reference between what existing kernels get
  wrong and why our design looks the way it does.
- Measurements live in [`../../spikes/`](../../spikes/) with hardware, versions, model and
  method, so the number can be reproduced.

## Status

Phase 2 (kernel research) in progress since 2026-09-09, under a revised question: not only
*which kernel do we build on* but *what does each kernel teach a kernel we build ourselves*. The
method is in [`kernels/README.md`](kernels/README.md); the order of work in
[`../superpowers/plans/2026-09-09-kernel-research-programme.md`](../superpowers/plans/2026-09-09-kernel-research-programme.md).
Phase 1 (prior art, domain) is complete; see [`../roadmap.md`](../roadmap.md).
