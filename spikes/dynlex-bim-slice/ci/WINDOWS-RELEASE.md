# Windows release candidate workflow

`windows-release.yml` prepares a native x64 Windows compiler, builds the app
from the selected checkout, runs three headless checks, then produces a ZIP
and MSI. It uploads artifacts only; it does not publish a release.

## Run prerequisites

1. Merge the Windows port from `codex/windows-v0.1` with the current Linux UI.
   The default `required_ancestor` is `5bff3a3`; the workflow refuses a source
   ref without that commit. This prevents shipping the old app bundled in the
   compiler-source snapshot. Resolve port changes in loading, file dialogs,
   runtime paths, theme setup and the platform C shim, not just installer files.
2. Include these CI files and the updated packaging script in that merged ref.
3. Copy `ci/windows-release.yml` to `.github/workflows/windows-release.yml`
   on a branch permitted to host workflows. Repository credentials need
   permission to write workflows. `source_ref` identifies the merged commit.
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

The existing compiler-only workflow remains unchanged. The release candidate
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

- Merge the current UI with the Windows platform port and run this workflow.
- Confirm the three headless checks and application compile emit no diagnostics.
- Inspect dependency DLLs and try ZIP startup on a clean Windows machine with a
  Vulkan driver (CI headless checks cannot prove interactive rendering).
- Install the MSI, use its Start menu entry, open/save/reopen a model, verify
  file dialogs, fonts, shaders, selection and the recent UI. Test uninstall and
  upgrade. A successful compiler-only artifact is not an application release.
- Keep the Linux artifact separate and identify its source commit independently;
  this Windows workflow does not build Linux.

The new workflow is configuration awaiting Windows execution, not evidence of a
successful Windows build. The through-opening branch is excluded from this
release preparation.
