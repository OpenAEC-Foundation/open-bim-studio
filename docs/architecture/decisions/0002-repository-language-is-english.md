# ADR-0002 — Repository language is English

**Status:** accepted
**Date:** 2026-07-29

## Context

The maintainers work in Dutch. The repository is private now but intended to be open source
later — the GitHub description already states this. Domain vocabulary in BIM is predominantly
English, and IFC itself is an English-language specification.

The build is also intended to lean on AI assistance, which performs measurably better on English
technical specifications than on other languages.

## Decision

All repository content is written in English: documents, file names, commit messages, and any
future code.

Conversations between maintainers continue in Dutch. That is a separate thing from what gets
written to disk.

Dutch terms are kept where the Dutch term is the accurate one — national standards, regulatory
concepts — and explained in `docs/vision/glossary.md`.

## Options considered

### English throughout — chosen
Matches the domain vocabulary, the intended openness, and the build strategy. Costs the
maintainers some fluency when writing.

### Dutch throughout
Rejected. More comfortable for the current contributors, but it conflicts with English domain
terminology, closes off later openness, and weakens the AI assistance the build strategy depends
on.

### Mixed — Dutch for vision and domain, English for technical content
Rejected, though it was tempting. The boundary would need policing on every document, and
documents that start on one side migrate to the other. `docs/domain/nl-standards.md` shows the
mixed case is handled adequately by keeping specific terms in Dutch inside an English document.

## Consequences

**Easier:** open-sourcing later requires no translation pass. Contributors outside the
Netherlands can participate. AI assistance is more effective.

**Harder:** maintainers write in their second language, which costs some precision and speed.

**Commits us to:** keeping the glossary current, since it is what makes Dutch domain terms
legible to an English-reading contributor.
