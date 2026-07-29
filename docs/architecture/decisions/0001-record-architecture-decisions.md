# ADR-0001 — Record architecture decisions

**Status:** accepted
**Date:** 2026-07-29

## Context

This repository exists so that the build phase contains no design phase. That only works if
decisions stay decided.

Two forces work against that. Contributors join at different times and arrive at settled
questions with fresh opinions, having not seen the reasoning. And the build itself is intended
to lean on AI assistance, which has no memory of a discussion that is not written down.

A decision recorded as a conclusion — "we use X" — does not survive either. Without the
reasoning and the rejected alternatives, it reads as a preference and gets reopened.

## Decision

We record architecturally significant decisions as Architecture Decision Records in
`docs/architecture/decisions/`, numbered sequentially, using `_template.md`.

An ADR records the context, the decision, **the options rejected and why**, and the
consequences.

ADRs are immutable once accepted. To change a decision, write a new ADR that supersedes it and
update the old one's status. The superseded record stays — the history of why we changed our
mind is itself information.

A decision is architecturally significant if reversing it would require changing more than one
component, or if it constrains what can be built later.

## Options considered

### Architecture Decision Records — chosen
Lightweight, plain markdown, version-controlled alongside what they describe. Well established.
The template's insistence on recording rejected options is the property we actually want.

### Decisions embedded in design documents
Rejected. Design documents get edited, and a decision loses its reasoning as the document is
revised around it. There is no record of what was considered and discarded.

### An issue tracker
Rejected as the primary record. Issues capture discussion well and conclusions badly, and they
are not where someone reading the repository looks.

## Consequences

**Easier:** onboarding — a new contributor can read why, not just what. Settled questions stay
settled. The build brief in `docs/BUILD-BRIEF.md` is largely assembled from ADRs.

**Harder:** decisions take slightly longer to record properly, and there is a real temptation to
skip the rejected-options section, which is the section that does the work.

**Commits us to:** keeping ADRs current. An abandoned ADR directory is worse than none, because
it implies decisions are recorded when they are not.
