# ADR-0017 — Scripting bridges run as a separate process over JSON-RPC

**Status:** accepted
**Date:** 2026-11-05
**Deciders:** the maintainer

## Context

[R-06](../../risks.md): parametric components may need a scripting escape hatch, and if so it must be
designed in from the start. On 31 October the maintainer chose DynLex as the default scripting
language, plus bridges to Python, Java and other languages; on 5 November they chose how the bridges
work ([`open-questions.md`](../../open-questions.md), round 2, question 5).

## Decision

- Components and connection recipes are written in DynLex, as a parameter schema plus a recipe.
- Other languages reach the application through a **separate process** that talks to it over a
  language-independent protocol: **JSON-RPC 2.0 over standard input and output**.
- Python gets the first client library. Any language that can read and write JSON on a pipe can be
  a client.
- The protocol offers batch calls for bulk work, so a script does not need thousands of round trips.
- A script runs with the rights the protocol grants it; it never runs inside the application's
  process.

## Options considered

### A separate process with JSON-RPC (chosen)
Works for every language, a crashing script cannot take the application down, and a process is the
natural unit to sandbox.

### In-process through a C API on the seams of ADR-0008
Fastest, but a script error can crash the application and the C API would have to stay stable.

### An embedded Python interpreter only
Quickest for Python users; ties the application to one interpreter and its version.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| JSON-RPC 2.0 is language-independent and transport-agnostic | [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification) | claimed |
| The same shape works for editor tooling across languages | [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) | claimed |

## Consequences

**What this makes easier:** new languages need only a client library; scripts are isolated.

**What this makes harder:** many small calls are slow; the API has to be designed for batches.

**What this commits us to:** a versioned protocol description in the repository, and a Python client
kept in step with it.

**What we would have to change to reverse it:** a new ADR; client libraries written against the
protocol would be replaced.
