# SPDX-License-Identifier: MPL-2.0
# Run on native Windows after scripts/install.ps1 and the compiler build.
param(
    [Parameter(Mandatory = $true)] [string] $CompilerTree,
    [Parameter(Mandatory = $true)] [string] $Slice,
    [Parameter(Mandatory = $true)] [string] $Output,
    [string] $Version = '0.1.1'
)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'This script requires native Windows, not WSL.' }
$treePath = (Resolve-Path $CompilerTree).Path
$slicePath = (Resolve-Path $Slice).Path
New-Item -ItemType Directory -Force $Output | Out-Null
$outPath = (Resolve-Path $Output).Path
$compiler = Join-Path $treePath 'build\dynlex.exe'
if (-not (Test-Path $compiler)) { throw "Missing compiler: $compiler" }
if (-not $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT) { throw 'Run scripts/install.ps1 first.' }
if ($env:DYNLEX_WINDOWS_TOOLCHAIN_TARGET -ne 'x86_64-w64-mingw32') { throw 'A native x64 llvm-mingw target is required.' }

# Use this checkout's app and library overlay, never the app in the snapshot.
# Keep the snapshot's CAD library, runtime and fallback font.
Copy-Item (Join-Path $slicePath 'overlay\*') $treePath -Recurse -Force
# The canonical overlay uses Linux window decoration APIs. Replace it with
# the native DWM implementation before parsing/linking anything on Windows.
$windowStyle = Join-Path $slicePath 'platform\windows\bim_window_style.dl'
if (-not (Test-Path -PathType Leaf $windowStyle)) { throw 'Missing Windows window-style implementation; refusing Linux X11 fallback.' }
Copy-Item $windowStyle "$treePath\examples\bim-slice\bim_window_style.dl" -Force
New-Item -ItemType Directory -Force "$treePath\build\shaders" | Out-Null
Copy-Item "$slicePath\shaders\*.spv" "$treePath\build\shaders" -Force
New-Item -ItemType Directory -Force "$treePath\examples\bim-slice\models" | Out-Null
Copy-Item "$slicePath\examples\*" "$treePath\examples\bim-slice\models" -Recurse -Force
Push-Location $treePath
try {
    if (-not (Select-String -Quiet -SimpleMatch 'the JSON document parsed from' lib/json.dl)) {
        git apply -p1 --whitespace=nowarn "$slicePath/patches/lib-json-public-parse.patch"
        if ($LASTEXITCODE -ne 0) { throw 'Public JSON parser patch failed.' }
    }
    # The C ABI bridge is required by the Windows port. Never link a Linux
    # object or a host-MSVC library into the llvm-mingw program.
    $platformSource = "$treePath\examples\bim-slice\platform\obs_platform.c"
    if (-not (Test-Path $platformSource)) { throw 'Source ref does not contain the Windows platform port.' }
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
    $env:LIBRARY_PATH = "$outPath;$dependencyLib;$env:LIBRARY_PATH"
    $env:LIB = "$outPath;$dependencyLib;$env:LIB"

    foreach ($name in 'ui_layout', 'plan_pan', 'text_glyphs', 'png_library') {
        $program = "$outPath\check-$name.exe"
        $diagnostics = & $compiler "examples/bim-slice/tests/$name.dl" -O0 -o $program 2>&1
        $compileCode = $LASTEXITCODE
        $diagnostics | Set-Content "$outPath\$name.diag"
        if ($compileCode -ne 0 -or ($diagnostics | Out-String).Trim().Length -gt 0) { throw "Compile diagnostics: $name" }
        $actual = (& $program | Out-String) -replace "`r`n", "`n"
        $runCode = $LASTEXITCODE
        $actual | Set-Content "$outPath\$name.out"
        $expected = (Get-Content -Raw "examples/bim-slice/tests/$name.expected.txt") -replace "`r`n", "`n"
        if ($runCode -ne 0 -or $actual.TrimEnd() -ne $expected.TrimEnd()) { throw "Headless check failed: $name" }
    }
    $app = "$outPath\open-bim-studio.exe"
    $diagnostics = & $compiler examples/bim-slice/main.dl -O2 -o $app 2>&1
    $compileCode = $LASTEXITCODE
    $diagnostics | Set-Content "$outPath\app.diag"
    if ($compileCode -ne 0 -or ($diagnostics | Out-String).Trim().Length -gt 0) { throw 'Application compilation failed or emitted diagnostics.' }
    # Verify architecture and DLL closure before packaging the current app.
    $peFiles = @(Get-ChildItem -Path $outPath -File | Where-Object { $_.Extension -in '.exe', '.dll' }).FullName
    & "$treePath\scripts\verify-windows-pe-files.ps1" -Files $peFiles -Architecture x64
    if ($LASTEXITCODE -ne 0) { throw 'Windows PE verification failed.' }
    & "$slicePath\overlay\examples\bim-slice\installer\make-windows-package.ps1" -Program $app -Tree $treePath -Output "$outPath\packages" -Version $Version -RequireMsi
    if (-not (Test-Path "$outPath\packages\Open-BIM-Studio-$Version-windows-x64.msi")) { throw 'MSI missing.' }
} finally {
    Pop-Location
}
