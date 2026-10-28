# SPDX-License-Identifier: MPL-2.0
# The development loop on native Windows: the toolchain from
# .dynlex-windows.local.ps1 (ignored by git; see scripts/dev-windows.example.ps1),
# the compiler from .dynlex-root.local, then one of:
#
#   scripts/dev-windows.ps1 -Tests evaluate,wall_base      compile, run and compare named tests
#   scripts/dev-windows.ps1 -Kernel                         the kernel library and its seam tests
#   scripts/dev-windows.ps1 -App                            the whole application into build\windows-app
#
# Tests are found by name in the modules' tests\ directories and under
# kernel\api\tests; the kernel library is built first and linked as "obskernel".
param(
    [string] $Tests = "",
    [switch] $Kernel,
    [switch] $App,
    [string] $Optimization = "O0"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repo
$local = Join-Path $repo '.dynlex-windows.local.ps1'
if (-not (Test-Path $local)) { throw "Missing .dynlex-windows.local.ps1; copy scripts/dev-windows.example.ps1 to it and fill in the paths." }
. $local
if (-not $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT) { throw '.dynlex-windows.local.ps1 must set DYNLEX_WINDOWS_TOOLCHAIN_ROOT.' }
$rootFile = Join-Path $repo '.dynlex-root.local'
if (-not (Test-Path $rootFile)) { throw 'Missing .dynlex-root.local: the compiler checkout, one line.' }
$compilerTree = (Get-Content $rootFile -TotalCount 1).Trim()
$compiler = Join-Path $compilerTree 'build\dynlex.exe'
if (-not (Test-Path $compiler)) { throw "Missing compiler: $compiler" }
$toolBin = Join-Path $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT 'bin'
$dependencyLib = Join-Path $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT 'lib'
$env:PATH = "$toolBin;" + (Join-Path $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT 'bin') + ";$env:PATH"
$out = Join-Path $repo 'build\windows-dev'
New-Item -ItemType Directory -Force $out, (Join-Path $out 'kernel'), 'generated', 'build\shaders' | Out-Null

# The generated files and the shaders, as build.sh generate writes them.
[IO.File]::WriteAllText((Join-Path $repo 'generated\platform.dl'), "import ui/shell/window_style_windows.dl`n")
if (-not (Test-Path 'generated\self_test.dl')) {
    [IO.File]::WriteAllText((Join-Path $repo 'generated\self_test.dl'), "# Written by scripts/dev-windows.ps1: the self-test entry of ui/shell/main.dl.`nfunction run bim app checks:`n    execute:`n        ignore 0`n")
}
& python -B tools\compose_modules.py --root $repo --out (Join-Path $repo 'generated') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Composing the modules failed.' }
& python -B tools\kernel_client.py --exposed kernel/api/exposed.dl --out kernel/api/client.dl | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Writing the kernel client failed.' }
Copy-Item viewer\shaders\*.spv build\shaders -Force

# The platform shim and the kernel library, linked as obs_platform and obskernel.
$shim = Join-Path $out 'libobs_platform.a'
if (-not (Test-Path $shim) -or (Get-Item 'platform\obs_platform.c').LastWriteTime -gt (Get-Item $shim).LastWriteTime) {
    & "$toolBin\clang-$env:DYNLEX_WINDOWS_TOOLCHAIN_LLVM_VERSION.exe" --target=$env:DYNLEX_WINDOWS_TOOLCHAIN_TARGET -std=c11 -O2 -c platform\obs_platform.c -o (Join-Path $out 'obs_platform.o')
    if ($LASTEXITCODE -ne 0) { throw 'The platform shim does not compile.' }
    & "$toolBin\llvm-ar.exe" rcs $shim (Join-Path $out 'obs_platform.o')
}
$archive = Join-Path $out 'kernel\libobskernel.a'
$kernelNewer = Get-ChildItem kernel -Recurse -Filter '*.dl' | Where-Object { -not (Test-Path $archive) -or $_.LastWriteTime -gt (Get-Item $archive).LastWriteTime } | Select-Object -First 1
if ($Kernel -or $kernelNewer) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $diag = & $compiler kernel/api/exposed.dl --emit-object --no-main "-$Optimization" -o (Join-Path $out 'kernel\obskernel.o') 2>&1
    if ($LASTEXITCODE -ne 0 -or ($diag | Out-String).Trim().Length -gt 0) { $diag | Write-Output; throw 'The kernel library does not compile.' }
    & "$toolBin\llvm-ar.exe" rcs $archive (Join-Path $out 'kernel\obskernel.o')
    Write-Output ("kernel library: " + [int]$sw.Elapsed.TotalSeconds + " s")
}
$env:LIBRARY_PATH = "$out\kernel;$out;$dependencyLib"
$env:LIB = $env:LIBRARY_PATH

function Find-Test([string] $name) {
    $found = Get-ChildItem -Path $repo -Recurse -Filter "$name.dl" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '[\\/]tests[\\/]' -and $_.FullName -notmatch '[\\/](tools|build|generated)[\\/]' -and $_.FullName -notmatch '[\\/]kernel[\\/](tests|reference)[\\/]' } |
        Select-Object -First 1
    if (-not $found) { throw "No */tests/$name.dl in the repository." }
    $found
}

$names = @()
if ($Tests) { $names += ($Tests -split '[ ,]+') }
if ($Kernel) { $names += 'link', 'mesh_round_trip' }
$failed = @()
foreach ($name in $names) {
    $source = Find-Test $name
    $program = Join-Path $out "$name.exe"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $diag = & $compiler $source.FullName "-$Optimization" -o $program 2>&1
    $seconds = [int]$sw.Elapsed.TotalSeconds
    if ($LASTEXITCODE -ne 0 -or ($diag | Out-String).Trim().Length -gt 0) {
        Write-Output "$name DIAG (${seconds}s)"; ($diag | Out-String).Trim() -split "`n" | Select-Object -First 8 | ForEach-Object { Write-Output "  $_" }
        $failed += $name; continue
    }
    $actual = ((& $program | Out-String) -replace "`r`n", "`n").TrimEnd()
    $code = $LASTEXITCODE
    $expectedFile = $source.FullName -replace '\.dl$', '.expected.txt'
    $expected = ((Get-Content -Raw $expectedFile) -replace "`r`n", "`n").TrimEnd()
    if ($code -ne 0 -or $actual -ne $expected) {
        Write-Output "$name FAIL (exit $code, compile ${seconds}s)"; Write-Output '--- actual'; Write-Output $actual; Write-Output '--- expected'; Write-Output $expected
        $failed += $name
    } else {
        Write-Output "$name PASS (compile ${seconds}s)"
    }
}

if ($App) {
    & (Join-Path $PSScriptRoot 'build-windows-app.ps1') -CompilerTree $compilerTree -Repo $repo -Output (Join-Path $repo 'build\windows-app')
}
if ($failed.Count -gt 0) { throw ("Failed: " + ($failed -join ', ')) }
