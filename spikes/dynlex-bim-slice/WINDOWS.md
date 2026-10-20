# Windows build and installer for the BIM slice

**Decision question:** can release v0.1 of the BIM slice ship a Windows
installer next to the Linux one, and if not, what stands in the way?

Everything below was found by reading the code and the DynLex fork
(`codex/cadkernel-port`, compiler version 0.0.3) on 2026-10-21. Nothing was
built or run on Windows; no Windows machine was available.

## What exists

- **DynLex itself builds on Windows.** The fork's `CMakeLists.txt` has a
  Windows path (MSVC runtime, `src/runtime/*Windows.c`), and
  `scripts/install.ps1` installs the toolchain: llvm-mingw 20260616 (UCRT,
  target `x86_64-w64-windows-gnu`), and through a pinned vcpkg manifest
  GLFW, FreeType, the Vulkan loader and nlohmann_json.
- **The fork's release workflow** (`.github/workflows/release.yml`) builds
  `dynlex.exe` on `windows-latest` and `windows-11-arm`, stages it with
  `scripts/stage-windows-toolchain.ps1`, and packages an MSI with WiX, signed
  through Azure artifact signing.
- **Published upstream release** (read with `gh release list`):
  OpenAEC-Foundation/dynlex 0.0.1 (2026-03-08) has `dynlex.msi`. It predates
  the fork's compiler changes and the cadkernel library, so it cannot build
  the slice.
- **The compiler cannot cross-compile.** Its link step is chosen when the
  compiler itself is built (`#ifdef _WIN32` in `codegen/native.cpp`); there
  is no target option. A Windows build of the slice needs a Windows build of
  the fork's compiler, run on Windows.
- **The pinned LLVM fork is built from source** on the first run
  (`scripts/build.sh`, `metadata/LLVM_TOOLCHAIN`, LLVM 23). The release
  workflow caches it per runner; how long a first build takes on a GitHub
  Windows runner was not measured.

## Blockers in the slice (link time)

On Windows the program links against the UCRT through llvm-mingw. Calls the
slice makes with the library name `"libc"` add nothing to the link line, so
every symbol must exist in the CRT or the link fails.

| Call | Where | On Windows | Proposed change |
|---|---|---|---|
| `"glfw"`, `"vulkan"` libraries | `overlay/lib/vulkan/*.dl` | linked as `-lglfw`, `-lvulkan`; vcpkg installs `glfw3dll`, `vulkan-1` | `patches/dynlex-windows-library-names.patch` (compiler) maps them on Windows only |
| `setenv` | `bim_ui.dl` (`use bim ui theme …`) | not in the UCRT | `putenv` with the literal `NAME=value` strings (both C libraries have it; the literals live as long as the program) |
| `pthread_create`, `pthread_join`, `pthread_attr_init`, `pthread_attr_setstacksize`, `pthread_attr_destroy` | `bim_loading.dl` | in winpthreads, not the UCRT | call them with the library `"pthread"`: `-lpthread` links winpthreads there and is harmless on Linux; ship `libwinpthread-1.dll` |
| `clock_gettime` | `bim_editor_core.dl` | in winpthreads | the same library change; `tv_nsec` is 32 bits on Windows, so zero the record before the call |
| `localtime_r`, `gmtime_r` | `bim_app_files.dl`, `bim_ifcx.dl` | inline in the mingw headers, no symbol | `localtime` and `gmtime` (copying the result; the first nine `tm` fields match) |
| `realpath` | `bim_app_files.dl` | not in the UCRT | joining a relative path to the working directory with `lib/path.dl` (`whether input is an absolute path`, `left joined with right`); a symbol of one platform only would break the other's link |
| `mkdir(path, mode)` | `bim_app_files.dl`, `main.dl` | `mkdir(path)` through the old names; the extra argument is ignored by the x64 calling convention | none needed; check once |

`getrusage` appears only in tests.

## Blockers in the slice (run time)

- **File dialogs** run `zenity` through `system` and read the answer from
  `/tmp/open-bim-studio-pick.txt` (`bim_editor.dl`). On Windows: a
  PowerShell `System.Windows.Forms.OpenFileDialog` command, its answer in
  `%TEMP%`.
- **Drawing import** runs `python3` on `import/drawing_to_lines.py`. Python
  is not on a Windows machine by default: leave the import out of the
  Windows build or ship an embedded Python.
- **Settings and recent files** live under `HOME`, which Windows does not
  set: use `APPDATA` (or `the user cache directory` of `lib/host.dl`).
- **Fonts**: the Linux installer copies Noto Sans from
  `/usr/share/fonts/truetype/noto`; the Windows installer must carry them
  itself (SIL OFL, licence beside them).
- **Shaders**: the prebuilt SPIR-V in `shaders/` is portable.
- **Vulkan**: the loader `vulkan-1.dll` comes with current GPU drivers; GitHub
  Windows runners have no GPU, so CI can build and run headless tests but not
  open the editor.

## Route

1. In the fork's Windows build, apply the slice's compiler patches
   (`dynlex-compiler-local.patch`, `dynlex-shader-extensions.patch`,
   `dynlex-windows-library-names.patch`) and build `dynlex.exe` with
   `scripts/install.ps1` and `scripts/build.sh` on `windows-latest`,
   caching `.cache/llvm-toolchain`, `.cache/llvm-mingw`, `.cache/vcpkg` and
   `.cache/vcpkg-installed` as the fork's release workflow does.
2. Make the link-time changes of the table in the overlay, each harmless on
   Linux, and run the Linux tests once more.
3. Replace the run-time Linux assumptions (dialogs, `/tmp`, `HOME`, Python).
4. Assemble the tree as `build.sh` does (lib, overlay, JSON patch, shaders,
   fonts) and compile `examples/bim-slice/main.dl -O2`; the compiler copies
   the runtime DLLs it links (`copyRuntimeDependencies`) beside the program.
5. Stage `open-bim-studio.exe`, the DLLs (GLFW, FreeType, winpthreads), the
   shaders, fonts with licences, and icons, and package them: a ZIP first,
   an MSI through WiX after, unsigned (signing needs the foundation's Azure
   account).
6. Test on a Windows machine with a Vulkan driver: start, open the
   demonstration pavilion, save, reopen.

## Verdict

Not for v0.1. Read from the code, the slice would not link on Windows as
it stands (ten symbols: `setenv`, five `pthread_` functions,
`clock_gettime`, `localtime_r`, `gmtime_r` and `realpath`; two library
names), its file dialogs and drawing import assume Linux, and no Windows
build of the fork's compiler from this branch is known. Ship v0.1 for
Linux; the Windows build follows once steps 1 to 3 are done and step 6 has
been seen on a real Windows machine. Missing evidence before a date can be
given: how long the first LLVM build takes on a Windows runner, and
whether the fork's compiler changes build there.
