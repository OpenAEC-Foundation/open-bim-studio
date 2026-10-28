# SPDX-License-Identifier: MPL-2.0
# Builds and packages Open BIM Studio on native Windows, after the fork's
# scripts/install.ps1 and a compiler build in the fork checkout.
#
#   scripts/build-windows-app.ps1 -CompilerTree <fork checkout> -Repo <this repository> -Output <folder> [-Version 0.1.1]
#
# Programs compile from this repository's root, as build.sh does on Linux:
# the compiler finds lib/ in its own checkout, imports such as model/x.dl
# here, and lib/json.dl here shadows the checkout's. The two generated import
# files select the Windows window style and the no-op self-test entry.
param(
    [Parameter(Mandatory = $true)] [string] $CompilerTree,
    [Parameter(Mandatory = $true)] [string] $Repo,
    [Parameter(Mandatory = $true)] [string] $Output,
    [string] $Version = '0.1.1'
)
$ErrorActionPreference = 'Stop'
# $IsWindows exists from PowerShell 6 on; Windows PowerShell 5.1 only runs on Windows.
if ($PSVersionTable.PSVersion.Major -ge 6 -and -not $IsWindows) { throw 'This script requires native Windows, not WSL.' }
$treePath = (Resolve-Path $CompilerTree).Path
$repoPath = (Resolve-Path $Repo).Path
New-Item -ItemType Directory -Force $Output | Out-Null
$outPath = (Resolve-Path $Output).Path
$compiler = Join-Path $treePath 'build\dynlex.exe'
if (-not (Test-Path $compiler)) { throw "Missing compiler: $compiler" }
if (-not $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT) { throw 'Run scripts/install.ps1 first.' }
if ($env:DYNLEX_WINDOWS_TOOLCHAIN_TARGET -ne 'x86_64-w64-mingw32') { throw 'A native x64 llvm-mingw target is required.' }

Push-Location $repoPath
try {
    # The generated imports of ui/shell/main.dl (build.sh generate on Linux).
    New-Item -ItemType Directory -Force generated, build\shaders | Out-Null
    [IO.File]::WriteAllText((Join-Path $repoPath 'generated\platform.dl'), "import ui/shell/window_style_windows.dl`n")
    $stub = "# Written by scripts/build-windows-app.ps1: the self-test entry of ui/shell/main.dl.`n" +
        "function run bim app checks:`n    execute:`n        ignore 0`n"
    [IO.File]::WriteAllText((Join-Path $repoPath 'generated\self_test.dl'), $stub)
    & python -B (Join-Path $repoPath 'tools\compose_modules.py') --root $repoPath --out (Join-Path $repoPath 'generated') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Composing the modules failed.' }
    & python -B tools\kernel_client.py --exposed kernel/api/exposed.dl --out kernel/api/client.dl | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Writing the kernel client failed.' }
    # The prebuilt SPIR-V shaders, where the program reads them (build/shaders).
    Copy-Item viewer\shaders\*.spv build\shaders -Force

    # The C ABI bridge is required by the Windows port. Never link a Linux
    # object or a host-MSVC library into the llvm-mingw program.
    $platformSource = Join-Path $repoPath 'platform\obs_platform.c'
    if (-not (Test-Path $platformSource)) { throw 'Missing platform/obs_platform.c.' }
    $toolBin = Join-Path $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT 'bin'
    $object = Join-Path $outPath 'obs_platform.o'
    & "$toolBin\clang-$env:DYNLEX_WINDOWS_TOOLCHAIN_LLVM_VERSION.exe" --target=$env:DYNLEX_WINDOWS_TOOLCHAIN_TARGET -std=c11 -O2 -c $platformSource -o $object
    if ($LASTEXITCODE -ne 0) { throw 'Platform bridge compilation failed.' }
    & "$toolBin\llvm-ar.exe" rcs "$outPath\libobs_platform.a" $object
    if ($LASTEXITCODE -ne 0) { throw 'Platform bridge archive failed.' }
    # The staged toolchain carries only the GLFW, Vulkan and FreeType import
    # libraries; zlib and PNG import libraries are in the vcpkg root.
    $dependencyLib = Join-Path $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT 'lib'
    if (-not (Test-Path "$dependencyLib\z.lib")) { throw "Missing zlib import library: $dependencyLib\z.lib" }
    if (-not (Test-Path "$dependencyLib\libpng16.lib")) { throw "Missing PNG import library: $dependencyLib\libpng16.lib" }
    # The kernel library (phase E of the module split): kernel/api/exposed.dl
    # as a definition-only object, archived as libobskernel.a beside the shim.
    $kernelObject = Join-Path $outPath 'obskernel.o'
    $diagnostics = & $compiler kernel/api/exposed.dl --emit-object --no-main -O2 -o $kernelObject 2>&1
    if ($LASTEXITCODE -ne 0 -or ($diagnostics | Out-String).Trim().Length -gt 0) { $diagnostics | Write-Output; throw 'Kernel library compilation failed or emitted diagnostics.' }
    & "$toolBin\llvm-ar.exe" rcs "$outPath\libobskernel.a" $kernelObject
    if ($LASTEXITCODE -ne 0) { throw 'Kernel library archive failed.' }
    $env:LIBRARY_PATH = "$outPath;$dependencyLib;$env:LIBRARY_PATH"
    $env:LIB = "$outPath;$dependencyLib;$env:LIB"

    foreach ($name in 'link', 'mesh_round_trip', 'body_round_trip', 'ui_layout', 'plan_pan', 'text_glyphs', 'png_library') {
        $program = "$outPath\check-$name.exe"
        $source = Get-ChildItem -Path $repoPath -Recurse -Filter "$name.dl" -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '[\\/]tests[\\/]' -and $_.FullName -notmatch '[\\/](tools|build|generated)[\\/]' -and $_.FullName -notmatch '[\\/]kernel[\\/](tests|reference)[\\/]' } | Select-Object -First 1
        if (-not $source) { throw "No */tests/$name.dl in the repository." }
        $diagnostics = & $compiler $source.FullName -O0 -o $program 2>&1
        $compileCode = $LASTEXITCODE
        $diagnostics | Set-Content "$outPath\$name.diag"
        if ($compileCode -ne 0 -or ($diagnostics | Out-String).Trim().Length -gt 0) { throw "Compile diagnostics: $name" }
        $actual = (& $program | Out-String) -replace "`r`n", "`n"
        $runCode = $LASTEXITCODE
        $actual | Set-Content "$outPath\$name.out"
        $expected = (Get-Content -Raw ($source.FullName -replace '\.dl$', '.expected.txt')) -replace "`r`n", "`n"
        if ($runCode -ne 0 -or $actual.TrimEnd() -ne $expected.TrimEnd()) { throw "Headless check failed: $name" }
    }
    $app = "$outPath\open-bim-studio.exe"
    $diagnostics = & $compiler ui/shell/main.dl -O2 -o $app 2>&1
    $compileCode = $LASTEXITCODE
    $diagnostics | Set-Content "$outPath\app.diag"
    if ($compileCode -ne 0 -or ($diagnostics | Out-String).Trim().Length -gt 0) { throw 'Application compilation failed or emitted diagnostics.' }
    # Verify architecture and DLL closure before packaging the current app.
    $peFiles = @(Get-ChildItem -Path $outPath -File | Where-Object { $_.Extension -in '.exe', '.dll' }).FullName
    & "$treePath\scripts\verify-windows-pe-files.ps1" -Files $peFiles -Architecture x64
    if ($LASTEXITCODE -ne 0) { throw 'Windows PE verification failed.' }
    & "$repoPath\installer\make-windows-package.ps1" -Program $app -Repo $repoPath -Shaders "$repoPath\build\shaders" -Output "$outPath\packages" -Version $Version -RequireMsi
    if (-not (Test-Path "$outPath\packages\Open-BIM-Studio-$Version-windows-x64.msi")) { throw 'MSI missing.' }
} finally {
    Pop-Location
}
