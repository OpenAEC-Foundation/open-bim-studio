# Interaction model

**Decision question: what concretely makes modelling feel immediate, and how much of it survives
contact with a semantic building model?**

This document carries the half of the vision that is easiest to lose. Technology decisions have
obvious consequences and get argued about; interaction decisions get deferred until the
architecture has quietly made them.

## The thesis

The immediacy of real-time 3D tools does not come from their kernels. It comes from their
interaction model. That model can be built on top of a semantic core.

If this thesis is wrong, the project reduces to "another BIM tool, but open source" — which may
be worth building, but is not what was asked for.

## What immediacy actually consists of

To be verified against real tools during phase 1 prior-art work, not accepted from intuition:

**Direct manipulation.** You act on the object, not on a dialog describing it. Drag the wall;
do not open a properties panel and type a coordinate.

**Continuous feedback.** The result is visible *during* the gesture, not after confirming it.
This has a hard architectural consequence: geometry must re-evaluate at frame rate. See R-01.

**Modal tools, keyboard-driven.** One key enters a mode; the hands stay on the keyboard and
mouse. No hunting through ribbons.

**No dialogs in the common path.** Dialogs are acceptable for rare configuration, never for
routine operations.

**The viewport is the interface.** Not a preview of the model — the place where work happens.

**Forgiving.** Undo is instant and unlimited. Experimentation costs nothing, so users
experiment.

## Where this collides with BIM

Honest tension, not a solved problem:

| Immediacy wants | Semantic modelling wants |
|---|---|
| Drag freely | Snap to grids, levels, and constraints |
| Geometry now, meaning later | Meaning first — you must say it is a wall |
| Cheap experimentation | Consistent, valid, exportable state |
| Instant feedback | Evaluation that may be expensive |
| Direct geometry editing | Parameters as the source of truth |

The productive question is not which side wins, but **where the seam goes**. Candidate answers,
to be developed:

- Meaning is assigned on creation but the tool is chosen by gesture, not by dialog.
- Free manipulation is allowed inside a constrained solution space — you drag, but the wall
  stays vertical and stays connected.
- Validity is continuous rather than gated: the model is always exportable, and invalid states
  are prevented rather than reported.

## Gamification — what is meant, and what is not

The word appeared in the originating brief and needs pinning down before it becomes decoration.

**Almost certainly meant:** the responsiveness, learnability, and low friction of a good game's
control scheme. Tools that teach themselves through use. Immediate consequence for every action.

**Almost certainly not meant:** points, badges, achievements, progress bars. Professional tools
that add these are worse for it.

*This needs confirming with the maintainers rather than assuming.*

## Open questions

1. Which specific interactions are the ones users perform hundreds of times a day? Those are the
   only ones whose friction matters. Requires observation, not speculation.
2. What is the minimum viable snapping and constraint system — enough to be accurate, not so much
   that it fights the user?
3. Can re-evaluation be made cheap enough for continuous feedback, or must we fall back to
   preview-then-commit? **This is the question that decides whether the thesis holds.** See R-01.
4. How do 2D drawing views participate? Are they editable surfaces or generated output?

## Method

Do not design this in the abstract. During phase 1 prior-art work, record specific interactions —
what the user does, what happens, how many actions it takes — in the tools being examined. The
comparison between how a low-friction tool and a professional BIM tool handle the *same* task is
where the real content of this document comes from.
