# Windows release candidate workflow

`windows-release.yml` prepares a native x64 Windows compiler, builds the app
from the selected checkout, runs three headless checks, then produces a ZIP
and MSI. It uploads artifacts only; it does not publish a release.

The release candidate package version is **0.1.1**; the existing v0.1 source
asset is only the compiler bootstrap input and is never overwritten.

## Run prerequisites

1. Use the consolidated `main` source, which includes the Windows port and current Linux UI.
   The default `required_ancestor` is `fb36c86`; the workflow refuses a source
   ref without that commit. This prevents shipping the old app bundled in the
   compiler-source snapshot. Resolve port changes in loading, file dialogs,
   runtime paths, theme setup and the platform C shim, not just installer files.
2. Include these CI files and the updated packaging script in that merged ref.
3. Copy `ci/windows-release.yml` to `.github/workflows/windows-release.yml`
   on a branch permitted to host workflows. Repository credentials need
   permission to write workflows. `source_ref` identifies the merged commit.
   Pushes trigger only on `main`; without dispatch
   inputs the source is `github.sha` and the required ancestor is `fb36c86`.
4. The v0.1 release asset `Open-BIM-Studio-0.1-source.tar.gz` must be accessible
   to the workflow token. Its SHA-256 must equal
   `086aa0704607372473f0604a6f9bdd7143589cea9b18f3d3a65e1705b3efbf5a`
   before extraction. It supplies compiler/CAD sources and fallback fonts;
   the selected checkout replaces the application and library overlay before
   app compilation. Compiler patches are applied only after `git apply --check`;
   an exact reverse-check accepts patches already in the snapshot. A missing
   asset, hash mismatch or patch that passes neither check fails the job.
5. Dispatch on GitHub's native Windows runner. The initial LLVM build has a
   six-hour ceiling; its duration and memory requirement have not been measured.

The old compiler-only workflow is manual-only; main uses the application workflow. The release candidate
workflow caches dependency toolchains, stages the compiler, builds the platform
bridge using the same llvm-mingw target, and requires WiX packaging to succeed.
It records the actual application commit and package SHA-256 hashes. Diagnostic
files are uploaded after an app/test failure. The package remains unsigned.

WiX 3.14.1 is fetched from its [official fixed release](https://github.com/wixtoolset/wix3/releases/tag/wix3141rtm).
The existing authoring uses the [Heat/Candle/Light tools](https://docs.firegiant.com/wix3/overview/alltools/).
No WSL launcher, Linux executable or placeholder executable is packaged.

## Verification performed and still required

Performed locally: YAML parsing, patch whitespace checks, official GitHub API
confirmation of `actions/checkout@v7`, `actions/cache@v6` and
`actions/upload-artifact@v7` tags, read-only review of
compiler installation environment and native packaging paths. `install.ps1`
writes target/root/dependency root/architecture/LLVM version to `GITHUB_ENV`;
a separate workflow step verifies persistence and the x64 target before the
compiler build. No local compiler
or app build was started. PowerShell was unavailable for syntax/runtime checks.

Still required before public release:

- Run this workflow on the consolidated commit.
- Confirm the three headless checks and application compile emit no diagnostics.
- Inspect dependency DLLs and try ZIP startup on a clean Windows machine with a
  Vulkan driver (CI headless checks cannot prove interactive rendering).
- Install the MSI, use its Start menu entry, open/save/reopen a model, verify
  file dialogs, fonts, shaders, selection and the recent UI. Test uninstall and
  upgrade. A successful compiler-only artifact is not an application release.
- Keep the Linux artifact separate and identify its source commit independently;
  this Windows workflow does not build Linux.

The new workflow is configuration awaiting Windows execution, not evidence of a
successful Windows build. The plate-opening core is integrated; its GUI remains incomplete.

The first native run stopped before dependency installation because Windows
checkout converted patch files to CRLF, while the verified tarball contains LF
sources. `.gitattributes` now keeps the compiler patches at LF. Reproduced
locally without compiling: the exact verified snapshot passes the LF local
patch reverse-check, and the shader/library patches pass forward-checks; a
CRLF copy of the local patch fails its reverse-check.

The second native run completed dependency installation, then exposed that the
slim llvm-mingw tree contains `clang-22.exe` (version from the persisted LLVM
metadata), not `clang.exe`. Preflight and bridge compilation now use that
versioned executable. Dependency and LLVM caches are restored separately and
saved immediately after successful installation/compiler build respectively;
a later application or MSI failure does not discard completed toolchains.
The staged compiler artifact is also uploaded before the application build.

The third native run (42992c6) built and staged the compiler and passed the
three headless checks; the application compile then failed without a
diagnostic. Reproduced locally on Windows 11 with that run's compiler
artifact and the app at 52093c5: the compiler ended with
STATUS_STACK_OVERFLOW (0xC00000FD) after about five minutes. Its PE header
reserves the Windows default of 1 MiB of stack. In a copy with 512 MiB
reserved, compilation reached the link, which failed on `-l:libz.so.1`
(the zlib calls of the binary IfcX file). `dynlex-windows-compiler-stack.patch`
now sets that reserve when the compiler is linked; the library-name patch
maps zlib to the vcpkg package's `z`, whose import library
`build-windows-app.ps1` puts on the link path. With both changes made by hand
locally, the `-O2` application compile took 596 s without diagnostics and the
program opened the example building. Measured peak working set of the
compiler on the overflowing run: 5.0 GB. No CI run has confirmed these
changes yet.
