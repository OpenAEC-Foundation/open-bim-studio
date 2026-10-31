# `dynlex-jit`

**Question:** can a DynLex script be compiled while the editor runs, loaded
into the editor's process and run directly against the live BIM model, fast
enough to be used interactively? Answering yes would make it possible to talk
to the model in DynLex, from a console or through the MCP server.

**Pass / fail:** none was registered in `docs/risks.md` before this ran, and
`FINDINGS.md` says so. The working bar was that a script touching the model
should compile, load and run in seconds, with no change to the compiler.

## How it works

```text
editor (DynLex)  --obs_jit_run_script(path, entry, model*)-->  libobsjit.so (C++, LLVM ORC)
                                                                  | dynlex script.dl --emit-object --no-main
                                                                  | LLJIT: load object, resolve libc
                 <----------- entry(model*) runs in-process ------+
```

- `obsjit.cpp` is the shim. It runs the `dynlex` compiler on the script,
  loads the object with ORC `LLJIT` into its own JITDylib and calls the
  script's exposed entry with the model's address.
- `editor_host.dl` stands in for the editor. It builds a real
  `bim model record` (level, wall type), then runs two scripts against it.
- `scripts/bim_add.dl` imports `bim/bim_model.dl` and adds five walls
  through the model's own `add bim wall typed …`.
- `scripts/bim_raise.dl` imports only `generated/model.dl` and edits walls
  in place.

## Run

```bash
spikes/dynlex-jit/run.sh
```

It needs the compiler checkout named by `.dynlex-root.local` (or
`DYNLEX_ROOT`) with its LLVM toolchain cache, plus clang-20, CMake and
Ninja. It changes to the repository root itself, where the script imports
resolve.
