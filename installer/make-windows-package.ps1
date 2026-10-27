# SPDX-License-Identifier: MPL-2.0
# Packages a Windows build of Open BIM Studio: a portable ZIP and, when the
# WiX Toolset 3 is on PATH (heat.exe, candle.exe, light.exe), an MSI
# installer from `open-bim-studio.wxs`.
#
#   make-windows-package.ps1 -Program build\open-bim-studio.exe -Tree <tree> -Output <folder> [-Version 0.1.1]
#
# -Program is the compiled examples/bim-slice/main.dl; the DLLs the DynLex
# compiler copied beside it (GLFW, FreeType, the Vulkan loader, the C++ and
# runtime libraries) go with it. -Tree is the assembled DynLex tree the
# program was compiled in (examples/bim-slice, build/shaders, tests/games/fonts).
# The staged folder holds bin\ (the program and its DLLs), shaders\, fonts\
# with their licences, icons\ and import\; the program finds them from its
# own folder. licenses\ holds the notices of installer\licenses (the
# application, the DynLex runtime, GLFW, the Vulkan loader) and, from the
# build's toolchain, the copyright file of every vcpkg package the DLLs come
# from (-DependencyRoot, by default $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT) and
# llvm-mingw's licence for its runtime DLLs (-ToolchainRoot, by default
# $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT). Nothing is signed.
param(
    [Parameter(Mandatory = $true)] [string] $Program,
    [Parameter(Mandatory = $true)] [string] $Tree,
    [Parameter(Mandatory = $true)] [string] $Output,
    [string] $Version = "0.1.1",
    [switch] $RequireMsi,
    [string] $DependencyRoot = $env:DYNLEX_WINDOWS_DEPENDENCY_ROOT,
    [string] $ToolchainRoot = $env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT
)
$ErrorActionPreference = "Stop"

$programPath = (Resolve-Path $Program).Path
$treePath = (Resolve-Path $Tree).Path
New-Item -ItemType Directory -Force $Output | Out-Null
$outputPath = (Resolve-Path $Output).Path
$slice = Join-Path $treePath "examples\bim-slice"

$stageRoot = Join-Path $outputPath "stage"
if (Test-Path $stageRoot) { Remove-Item -Recurse -Force $stageRoot }
$stage = Join-Path $stageRoot "Open BIM Studio"
foreach ($folder in "bin", "shaders", "fonts", "icons", "import", "licenses") {
    New-Item -ItemType Directory -Force (Join-Path $stage $folder) | Out-Null
}

# The program and every DLL beside it.
Copy-Item $programPath (Join-Path $stage "bin\open-bim-studio.exe")
$libraries = @(Get-ChildItem -Path (Split-Path $programPath) -Filter "*.dll" -File)
if ($libraries.Count -eq 0) {
    throw "No DLLs beside $programPath; the compiler copies the ones it links."
}
foreach ($library in $libraries) { Copy-Item $library.FullName (Join-Path $stage "bin") }

# The SPIR-V shaders.
$shaders = @(Get-ChildItem -Path (Join-Path $treePath "build\shaders") -Filter "*.spv" -File)
if ($shaders.Count -eq 0) { throw "No shaders in $treePath\build\shaders." }
foreach ($shader in $shaders) { Copy-Item $shader.FullName (Join-Path $stage "shaders") }

# The fonts with their licences: osifont (drawings), Inter and JetBrains Mono
# (the interface), Liberation Mono (the fallback).
$fonts = Join-Path $slice "fonts"
foreach ($name in "osifont.ttf", "Inter-Regular.ttf", "Inter-Medium.ttf", "Inter-SemiBold.ttf",
                  "JetBrainsMono-Regular.ttf", "Inter-OFL.txt", "JetBrainsMono-OFL.txt") {
    Copy-Item (Join-Path $fonts $name) (Join-Path $stage "fonts")
}
Copy-Item (Join-Path $fonts "README.md") (Join-Path $stage "fonts\README-osifont.md")
foreach ($name in "LiberationMono-Regular.ttf", "LICENSE-LiberationFonts") {
    Copy-Item (Join-Path $treePath "tests\games\fonts\$name") (Join-Path $stage "fonts")
}

# The notices: the application's and the bundled libraries' from
# installer\licenses, every vcpkg package's copyright, llvm-mingw's licence.
$notices = Join-Path $slice "installer\licenses"
if (-not (Test-Path (Join-Path $notices "README.txt"))) { throw "No notices in $notices." }
Copy-Item -Path (Join-Path $notices "*") -Destination (Join-Path $stage "licenses")
if (-not $DependencyRoot -or -not (Test-Path (Join-Path $DependencyRoot "share"))) {
    throw "No vcpkg packages at '$DependencyRoot' for the DLLs' notices; pass -DependencyRoot."
}
$packageNotices = Join-Path $stage "licenses\vcpkg"
New-Item -ItemType Directory -Force $packageNotices | Out-Null
foreach ($package in Get-ChildItem -Path (Join-Path $DependencyRoot "share") -Directory) {
    $copyright = Join-Path $package.FullName "copyright"
    if (Test-Path $copyright) { Copy-Item $copyright (Join-Path $packageNotices "$($package.Name).txt") }
}
if (-not $ToolchainRoot -or -not (Test-Path (Join-Path $ToolchainRoot "LICENSE.TXT"))) {
    throw "No llvm-mingw LICENSE.TXT at '$ToolchainRoot' for its runtime DLLs; pass -ToolchainRoot."
}
$toolchainLicence = Join-Path $ToolchainRoot "LICENSE.TXT"
Copy-Item $toolchainLicence (Join-Path $stage "licenses\llvm-mingw.txt")

# The interface's icons and the drawing import's script (it needs Python 3).
Copy-Item (Join-Path $slice "icons\ui-icons.txt") (Join-Path $stage "icons")
Copy-Item (Join-Path $slice "icons\README.md") (Join-Path $stage "icons")
foreach ($icon in "open-bim-studio.svg", "open-bim-studio.png", "open-bim-studio.ico", "open-bim-studio.rgba") {
    Copy-Item (Join-Path $slice "icons\$icon") (Join-Path $stage "icons")
}
Copy-Item (Join-Path $slice "import\drawing_to_lines.py") (Join-Path $stage "import")

@"
Open BIM Studio $Version for Windows (x64)

Start bin\open-bim-studio.exe. It needs a graphics driver with Vulkan 1.2 or
later. Importing a drawing (DXF, DWG, PDF) needs Python 3 as `python`.
Settings and recent files are kept in %APPDATA%\Open BIM Studio.
The licences of the program and of the libraries it ships are in
licenses\ (vcpkg\ for the DLLs' packages), the fonts' in fonts\, the
icons' in icons\README.md.
"@ | Set-Content -Encoding UTF8 (Join-Path $stage "README.txt")

# The portable ZIP.
$zip = Join-Path $outputPath "Open-BIM-Studio-$Version-windows-x64-portable.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path $stage -DestinationPath $zip
Write-Host "Wrote $zip"

# The MSI, when WiX 3 is available.
$heat = Get-Command heat.exe -ErrorAction SilentlyContinue
$candle = Get-Command candle.exe -ErrorAction SilentlyContinue
$light = Get-Command light.exe -ErrorAction SilentlyContinue
if (-not ($heat -and $candle -and $light)) {
    if ($RequireMsi) { throw "WiX Toolset 3 is required for this release build." }
    Write-Host "WiX Toolset 3 not on PATH: no MSI."
    exit 0
}
$work = Join-Path $outputPath "wix"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force $work | Out-Null
$files = Join-Path $work "files.wxs"
& $heat.Source dir $stage -nologo -cg AppFiles -dr INSTALLFOLDER -ag -sfrag -srd -sreg -var var.StageDir -out $files
if ($LASTEXITCODE -ne 0) { throw "heat.exe failed." }
$product = Join-Path $PSScriptRoot "open-bim-studio.wxs"
& $candle.Source -nologo -arch x64 "-dStageDir=$stage" "-dVersion=$Version" -out "$work\" $product $files
if ($LASTEXITCODE -ne 0) { throw "candle.exe failed." }
$msi = Join-Path $outputPath "Open-BIM-Studio-$Version-windows-x64.msi"
& $light.Source -nologo -out $msi (Join-Path $work "open-bim-studio.wixobj") (Join-Path $work "files.wixobj")
if ($LASTEXITCODE -ne 0) { throw "light.exe failed." }
Write-Host "Wrote $msi"
