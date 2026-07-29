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

## Status

Phase 0. Category READMEs define the criteria; individual candidate notes are not yet written.
See [`../roadmap.md`](../roadmap.md).
