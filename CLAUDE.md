# CLAUDE.md — instructions for AI agents working in this repository

## What this repository is

A preparation and research repository for a future BIM modeller. There is no product code here
and none should be added during the research phases. The output is documentation: research
notes, benchmarks, architecture decisions, and ultimately `docs/BUILD-BRIEF.md`.

Read `README.md` and `docs/roadmap.md` before acting. Read `docs/risks.md` to see what is
actually open.

## Language

**All repository content is in English** — documents, file names, commit messages, and any
future code. Conversations with maintainers are typically in Dutch; that does not change what
gets written to disk.

Dutch domain terms that have no accurate English equivalent (for example names of national
standards) are kept in Dutch and explained in `docs/vision/glossary.md`.

## Naming rules — read carefully, this repository has an explicit exception

The maintainer's global instructions prohibit naming commercial software products in repository
content. **That rule is scoped to competing calculation software** (geotechnical and structural
analysis packages) and remains fully in force everywhere else.

**In this repository, BIM and 3D software may be named explicitly.** Revit, Archicad, Blender,
Bonsai, Rhino, Grasshopper, FreeCAD, Unreal Engine, Godot, SketchUp, Onshape, Speckle and
similar tools are the subject of legitimate prior-art research. Comparative analysis is
worthless if it is written as "package A" and "package B".

The exception does **not** extend to:
- Geotechnical or structural calculation packages — these stay generic ("external reference
  calculation", "external geotechnical software package") even here.
- Client names, project names, or any customer data.

## Conversation history

`PROMPTS.md` is a log of **originating prompts from maintainers only**. It records intent and
the decision trail.

Do not add assistant responses, transcripts, paraphrased conversations, or session dumps to
this repository — not in `PROMPTS.md`, not in commit messages, not anywhere. Commit messages
describe changes, never the conversation that produced them.

## How to write research notes

Use `docs/research/_template.md`. The rules that matter:

1. **Every note opens with the decision question it answers.** A note without a question becomes
   a wiki page nobody reads.
2. **Every note ends with a verdict**, even a provisional one. "More research needed" is only
   acceptable if it names the specific missing evidence.
3. **Cite sources with URLs.** Claims about performance, licensing, or capability need a source
   or a measurement.
4. **Distinguish measured from claimed.** "The documentation states X" and "we measured X" are
   different kinds of evidence and must be labelled as such.

## Decisions

Settled decisions become ADRs in `docs/architecture/decisions/`. Once an ADR is `Accepted`, do
not silently contradict it in other documents. To change it, write a new ADR that supersedes it.

## What not to do

- Do not add product code, scaffolding, or build tooling during phases 0–3. Experiments belong
  in `spikes/`, clearly marked as throwaway.
- Do not commit large binaries. Benchmark models go in `reference/` with acquisition
  instructions; see `reference/README.md` and `.gitignore`.
- Do not present the working hypothesis in `docs/architecture/layers.md` as settled. It is
  explicitly there to be falsified.
- Do not fill stubs with plausible-sounding prose to make them look complete. An honest empty
  stub with a sharp question is more useful than a page of generic content.
