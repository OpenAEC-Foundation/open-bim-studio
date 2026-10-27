# Overrides of the DynLex checkout's library

A file here shadows the checkout's file of the same path, because the compiler
resolves `lib/...` imports from the working directory before its own tree.
Every file here is tied to an open upstream pull request and is deleted when
the pinned checkout contains the change. Empty is the goal.

| File | Change | Upstream |
|---|---|---|
| `lib/json.dl` | `patches/lib-json-public-parse.patch` and `patches/lib-json-bounded-string.patch` applied to the checkout's file at `c2d32bea` | to be opened in stage 3 |
