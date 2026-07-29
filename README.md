# open-bim-studio

Preparation repository for a BIM modeller that combines the capabilities of a professional
BIM authoring tool (3D modelling, parametric components, 2D drawings) with the immediacy of a
real-time 3D application (direct manipulation, fast iteration, low friction).

## What this repository is — and is not

**This repository contains no product code.** Not yet, and not by accident.

The application is intended to be built later this year, in a short and concentrated effort,
with heavy AI assistance. That is only realistic if the build phase contains *no design phase*.
Every open question — which kernel, which host, which scope, which interaction model — must be
answered and recorded before the build starts.

So the deliverable here is knowledge: research, benchmarks, decisions, and their reasoning.

The endpoint is [`docs/BUILD-BRIEF.md`](docs/BUILD-BRIEF.md) — a single handover document
complete enough that an AI agent with no other context can produce a coherent implementation
plan from it. That is the acceptance test for this entire repository.

## Where to start

| If you want to… | Read |
|---|---|
| Understand the goal | [`docs/vision/vision.md`](docs/vision/vision.md) |
| Understand the boundaries | [`docs/vision/non-goals.md`](docs/vision/non-goals.md) |
| Know what needs doing | [`docs/risks.md`](docs/risks.md) — open uncertainties are the backlog |
| Contribute research | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| See the technical thesis | [`docs/architecture/layers.md`](docs/architecture/layers.md) |
| See where we are | [`docs/roadmap.md`](docs/roadmap.md) |

## Layout

```
docs/vision/          Goal, boundaries, shared vocabulary
docs/domain/          BIM domain knowledge: IFC, parametrics, drawings, standards
docs/research/        Technology evaluation — the bulk of the work
docs/architecture/    System design and frozen decisions (ADRs)
docs/ux/              The interaction model: why this should feel different
docs/roadmap.md       Phases and their artefacts
docs/risks.md         Open uncertainties, each linked to a spike
docs/BUILD-BRIEF.md   The handover document (grows throughout)
spikes/               Throwaway experiments, each with measured findings
reference/            External specs and benchmark models
PROMPTS.md            Log of originating prompts — the intent trail
```

## Status

**Phase 0 — skeleton in place.** Most documents are stubs. Each stub states the decision
question it exists to answer; none contain filler. Answering them is the work.

See [`docs/roadmap.md`](docs/roadmap.md) for the phase plan.

## A note on the working hypothesis

[`docs/architecture/layers.md`](docs/architecture/layers.md) contains an early technical
hypothesis. It is written to be **falsified, not assumed**. It exists so that research has a
target to attack, not so that the conclusion is settled in advance. If the spikes in phase 3
contradict it, the hypothesis loses.
