# Copy to .dynlex-windows.local.ps1 at the repository root (ignored by git) and
# fill in the staged toolchain of the compiler checkout: the llvm-mingw root,
# its clang version, and the vcpkg root holding GLFW, Vulkan, FreeType, zlib
# and PNG for the x64 static-CRT triplet. scripts/dev-windows.ps1 dot-sources
# it; the compiler itself comes from .dynlex-root.local.
$fork = 'C:\path\to\dynlex'
$env:DYNLEX_WINDOWS_TOOLCHAIN_ROOT = "$fork\.cache\llvm-mingw\20260616-ucrt-x86_64"
$env:DYNLEX_WINDOWS_TOOLCHAIN_TARGET = 'x86_64-w64-mingw32'
$env:DYNLEX_WINDOWS_TOOLCHAIN_LLVM_VERSION = '22'
$env:DYNLEX_WINDOWS_DEPENDENCY_ROOT = "$fork\.cache\vcpkg-installed\<hash>\x64-windows-static-crt"
