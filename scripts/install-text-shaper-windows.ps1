# SPDX-License-Identifier: MPL-2.0
# App-owned dependency: keep the compiler checkout unchanged.
param(
    [Parameter(Mandatory = $true)] [string] $CompilerTree,
    [Parameter(Mandatory = $true)] [string] $Output
)
$ErrorActionPreference = 'Stop'
$tree = (Resolve-Path $CompilerTree).Path
$repo = Split-Path $PSScriptRoot
$releaseLine = Get-Content (Join-Path $tree 'metadata\VCPKG_TOOLCHAIN') | Where-Object { $_ -match '^release ' } | Select-Object -First 1
if (-not $releaseLine) { throw 'The compiler does not declare a pinned vcpkg release.' }
$release = ($releaseLine -split '\s+')[1]
$vcpkgRoot = Join-Path $tree ".cache\vcpkg\$release"
$vcpkg = Join-Path $vcpkgRoot 'vcpkg.exe'
if (-not (Test-Path $vcpkg)) { throw 'Install the compiler dependencies first.' }
$manifest = Join-Path $repo 'platform\windows'
$expected = (Get-Content -Raw (Join-Path $manifest 'vcpkg.json') | ConvertFrom-Json).'builtin-baseline'
$actual = (& git -C $vcpkgRoot rev-parse HEAD).Trim()
if ($actual -ne $expected) { throw "Expected pinned vcpkg $expected, found $actual." }
$install = Join-Path $repo '.cache\text-shaper-windows'
$triplet = 'x64-windows-static-crt'
& $vcpkg install "--x-manifest-root=$manifest" "--x-install-root=$install" `
    "--overlay-triplets=$tree\cmake\vcpkg-triplets" --triplet $triplet --disable-metrics
if ($LASTEXITCODE -ne 0) { throw 'HarfBuzz dependency installation failed.' }
$packages = Join-Path $install $triplet
New-Item -ItemType Directory -Force $Output | Out-Null
# Reuse the compiler's exact runtime bytes for shared dependencies. Both
# manifests use the same baseline; copying rebuilt FreeType/Brotli DLLs
# over them triggers the compiler's runtime collision protection.
$compilerBin = Join-Path $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT 'bin'
foreach ($library in Get-ChildItem (Join-Path $packages 'bin') -Filter '*.dll' -File) {
    $existing = Join-Path $compilerBin $library.Name
    if (Test-Path $existing) {
        Copy-Item $existing $Output -Force
    } else {
        Copy-Item $library.FullName $Output -Force
    }
}
# Package notices alongside the compiler dependency notices.
$share = Join-Path $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT 'share'
foreach ($package in Get-ChildItem (Join-Path $packages 'share') -Directory) {
    $notice = Join-Path $package.FullName 'copyright'
    if (Test-Path $notice) {
        $destination = Join-Path $share $package.Name
        New-Item -ItemType Directory -Force $destination | Out-Null
        Copy-Item $notice $destination -Force
    }
}
if (-not ((Test-Path (Join-Path $Output 'harfbuzz.dll')) -or (Test-Path (Join-Path $Output 'harfbuzz-0.dll')) -or (Test-Path (Join-Path $Output 'libharfbuzz-0.dll')))) { throw 'The HarfBuzz runtime DLL is missing.' }
