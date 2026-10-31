# Running DynLex applications in the browser through WebAssembly

**Decision question:** What has to exist before Open BIM Studio, a DynLex program that today
links libc, Vulkan, GLFW, FreeType and two C libraries of its own, can run in a browser tab as
WebAssembly — and which part of that is already there?

**Status:** draft
**Author:** Elize
**Last updated:** 2026-10-31

---

## Summary

The DynLex compiler already emits WebAssembly (`--emit-wasm`, LLVM target `wasm32-unknown-unknown`)
and its own web IDE already runs such programs against a JavaScript host. What Open BIM Studio
lacks is not a compiler feature but a *browser host*: a JavaScript (and WebGPU) implementation of
the C functions the program calls, plus a main loop that returns to the browser between frames.
The proposal is a `web/` host in four stages, starting with the kernel, which needs nothing but libc.

## How a DynLex program becomes WebAssembly (as read from the compiler source)

WebAssembly is a portable instruction format: a `.wasm` file holds functions, one linear memory (a
flat byte array that the program sees as its address space) and a list of **imports** — functions
the module expects its host to supply. The module cannot open a file, draw a pixel or read the
clock by itself; every contact with the outside world is an imported function that the page's
JavaScript provides when it instantiates the module.

DynLex maps onto that as follows (all **inferred** from reading the DynLex checkout at `c2d32bea`):

1. The compiler front end is target independent. Parsing, pattern resolution and type inference
   produce LLVM IR, exactly as for a native build.
2. With `--emit-wasm`, `src/cpp/compiler/codegen/wasm.cpp` gives that IR to LLVM's WebAssembly
   back end (`wasm32-unknown-unknown`, position-independent code) and writes one relocatable object.
   It then patches the export of `main` so a host can call it. There is no separate linker step:
   the whole program is one module.
3. Every `@intrinsic("call", library, function, ...)` becomes a WebAssembly import from module
   `env` with the function's name. The library name (`libc`, `vulkan`, `glfw`) is dropped; what
   remains is a C-shaped signature with 32-bit pointers (offsets into linear memory) and 64-bit
   integers.
4. The host instantiates the module with an object that supplies those imports. The web IDE's host
   is `src/web/ide/public/compiler/runtimeImports.js` (memory, stack pointer, `malloc`/`free`,
   `memcpy`, `printf`, `snprintf`, a few maths functions) plus `runtimeFilesystem.js` and
   `runtimePathHost.js` (the standard library's `dynlex_filesystem_*` calls on an in-memory file
   tree). `isSupportedRuntimeImport` rejects any import outside that list.
5. Shaders take a parallel route: DynLex compiles them to SPIR-V, and the web IDE translates SPIR-V
   to WGSL (WebGPU) or GLSL (WebGL) with `dynlex_wgsl_translator.wasm`.

The compiler itself also exists as WebAssembly (`dynlex_web.wasm`, an Emscripten build), which is
how the web IDE compiles in the browser. For Open BIM Studio that is irrelevant: a full build takes
several gigabytes of compiler memory, so the application is compiled natively with `--emit-wasm`
and only the resulting `.wasm` is shipped.

### Does an application need a particular format to be built for WebAssembly?

No source format: the same `.dl` files compile to native code or to WebAssembly. What decides
whether a program *runs* in the browser is its set of external calls, because each one becomes an
import that the browser host has to supply. A program that only calls libc functions the host
implements runs unchanged. A program that calls Vulkan, GLFW or `fopen` does not, until those
calls are either implemented in the host or moved behind an abstraction with a browser
implementation. The practical "format" is therefore an **import contract**: the list of C
functions, with signatures, that a browser host promises to provide.

Four properties of the browser constrain the program's structure, not just its imports:

- **No blocking main loop.** The page freezes while WebAssembly runs; a `while window is open`
  loop that polls events never yields. Either the loop body becomes a per-frame callback driven by
  `requestAnimationFrame`, or the build uses JavaScript Promise Integration (JSPI), which lets an
  import suspend the WebAssembly stack and resume it later.
- **32-bit addresses.** `wasm32` gives at most 4 GiB of linear memory. Large models must fit, or
  the build moves to `memory64` (supported by LLVM; browser support is newer).
- **Threads only with cross-origin isolation.** WebAssembly threads need `SharedArrayBuffer`, which
  browsers only enable when the page is served with COOP/COEP headers; the DynLex documentation
  states atomics are CPU-only today.
- **No native pointer calls.** `@intrinsic("call pointer", ...)` is CPU-only by design
  (`docs/stages.md` in the DynLex checkout), so runtime-loaded native code (the `obsjit` spike) has
  no browser equivalent.

## What Open BIM Studio calls today

Counted over all `.dl` files in this repository (**measured**, `grep` over `@intrinsic("call"`):

| Library | Call sites | Browser status |
|---|---|---|
| `libc` (plus 145 variadic) | 1024 | ~45 distinct functions; the IDE host covers memory, `printf`/`snprintf` and some maths. Missing: `fopen`/`fread`/`fwrite`/`fseek`/`ftell`/`fclose`, `clock_gettime`, `getenv`, `setenv`, `system`, `mkdir`, `rename`, `remove`, `getrusage`, most of `math.h` |
| `vulkan` | 195 | None. Confined to `viewer/vulkan/` (context, graphics, images, renderer) plus probes |
| `glfw` | 64 | None. In `viewer/vulkan/` and `ui/shell/window_style_*.dl` |
| `obs_platform` | 37 | None. The shim in `platform/obs_platform.c`; threads in `ui/shell/bim_loading.dl` |
| `obskernel` | 24 | Linked as a static archive natively; a single-module WebAssembly build has to compile `kernel/api/exposed.dl` into the same module instead |
| `freetype` | 4 | None. Either FreeType compiled to WebAssembly and linked in, or text measurement through Canvas |
| `dwmapi`, `user32` | 3 | Windows only, already behind `generated/platform.dl` |

The kernel (`kernel/`) calls none of `vulkan`, `glfw`, `obs_platform` or `freetype` (**measured**,
same grep). It is the natural first target.

## Proposal: a `web` platform in four stages

The repository already selects platform code at build time (`BIM_PLATFORM` writes
`generated/platform.dl`). A third value, `web`, plus a host directory with the JavaScript side, fits
that pattern.

1. **Kernel in the browser (headless).** `./build.sh wasm-test NAME` compiles a module test or a
   kernel test directory with `--emit-wasm` and runs it under Node on `platform/web/run.mjs`: the
   DynLex IDE's runtime files, loaded from the compiler checkout, plus the missing `math.h`
   functions and `exit`. Imports neither provides are bound to stubs that fail when called and are
   listed in the run summary. A page that runs the same module is the next step. This answers the questions this note cannot: does the full kernel compile for `wasm32`,
   how large is the module, and how fast is it relative to native.
2. **Files through the standard library, not libc.** Replace the direct `fopen`/`fread` calls with
   the DynLex standard library's file API, which already has a browser implementation. Opening a
   model becomes a file picker or drag-and-drop into the in-memory tree; saving becomes a download
   or the Origin Private File System. This change also helps native builds (one file API instead of
   two).
3. **A WebGPU viewer next to the Vulkan one.** The Vulkan code already sits in one directory. A
   `viewer/webgpu/` with the same surface, implemented as imports onto `navigator.gpu`, reuses the
   shaders through the SPIR-V-to-WGSL translator the DynLex web IDE already ships. GLFW's role
   (window, input events) goes to a `<canvas>` and DOM events.
4. **The main loop.** Restructure the editor's loop into a "run one frame" function called from
   `requestAnimationFrame`, or adopt JSPI for the waits (`glfwWaitEventsTimeout`, loading threads).
   The background loader in `bim_loading.dl` runs synchronously in the first version.

Stages 1 and 2 are useful on their own: a kernel that runs in a browser tab or a Node service is a
demonstration and a test vehicle long before the editor is.

## Risks

- **Unmeasured compile:** nobody has compiled any Open BIM Studio program with `--emit-wasm`. The
  WebAssembly back end may hit DynLex code generation paths that only the native target has
  exercised. Stage 1 settles this.
- **Memory ceiling:** 4 GiB of `wasm32` memory, with the IDE host's simple JavaScript allocator, may
  not hold large models. Unknown until stage 1 runs a large fixture.
- **Two viewers to maintain:** a WebGPU viewer next to the Vulkan one doubles rendering work unless
  both sit behind one interface.
- **Host drift:** the IDE host lives in the compiler checkout; copying it here forks it. Prefer
  contributing the missing imports upstream, as with `lib/` overrides.

## Verdict

Provisional: **feasible, and cheaper than it looks for the kernel; expensive for the editor.** The
compiler side exists; what is missing is a browser host. Start with stage 1 (kernel tests as
WebAssembly under Node) — it needs no change to product code and turns every open question above
into a measurement. Decide on the WebGPU viewer only after stage 1 shows the module size and speed.

No measurement was taken for this note: two compiler runs were already active on this machine, and
the repository runs one compiler per computer.

## Sources

- DynLex checkout `c2d32bea`: `src/cpp/compiler/codegen/wasm.cpp`, `src/cpp/main.cpp`
  (`--emit-wasm`), `src/web/ide/public/compiler/runtimeImports.js`, `runtimeFilesystem.js`,
  `compiler-worker.js`, `docs/stages.md` (code generation), `docs/host.md` (browser builds)
- [WebAssembly core specification](https://webassembly.github.io/spec/core/)
- [JavaScript Promise Integration proposal](https://github.com/WebAssembly/js-promise-integration)
- [Memory64 proposal](https://github.com/WebAssembly/memory64)
- [WebGPU specification](https://www.w3.org/TR/webgpu/)
- [Cross-origin isolation for SharedArrayBuffer](https://web.dev/articles/coop-coep)
