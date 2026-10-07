#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
# Builds a self-extracting Linux installer for the BIM slice editor.
#
#   examples/bim-slice/installer/make-installer.sh BINARY OUTPUT [release|dev]
#
# BINARY is a built examples/bim-slice/main.dl; OUTPUT is the installer file
# to write. `release` (the default) installs as `bim-slice`; `dev` installs a
# development build (for instance -O0 -g) side by side as `bim-slice-dev`,
# with its own directory, launcher and menu entry. Run from the repository root with .cache/bootstrap/env.sh sourced,
# so the libraries the binary links against resolve. Every library that does
# not come from the system (/lib, /usr/lib) is copied into the installer,
# together with the font and its licence and the SPIR-V shaders compiled from
# lib/vulkan/shaders into build/shaders, so an installed copy does not depend
# on this repository, its caches or the build machine's temporary files.
set -euo pipefail

binary=$(realpath "$1")
output=$2
variant=${3:-release}
case "$variant" in
    release) name=bim-slice; title="BIM slice" ;;
    dev) name=bim-slice-dev; title="BIM slice (dev)" ;;
    *) echo "unknown variant $variant" >&2; exit 1 ;;
esac
root=$(pwd)
font="$root/tests/games/fonts/LiberationMono-Regular.ttf"
licence="$root/tests/games/fonts/LICENSE-LiberationFonts"
[ -x "$binary" ] || { echo "not an executable: $binary" >&2; exit 1; }
[ -f "$font" ] && [ -f "$licence" ] || { echo "run from the DynLex repository root" >&2; exit 1; }
shaders="$root/build/shaders"
# The interface font, Noto Sans (SIL Open Font License), from the system.
noto=/usr/share/fonts/truetype/noto
[ -f "$noto/NotoSans-Regular.ttf" ] || { echo "Noto Sans not found in $noto (package fonts-noto-core)" >&2; exit 1; }
[ -f "$shaders/screen_vertex.spv" ] || { echo "compile lib/vulkan/shaders into build/shaders first" >&2; exit 1; }

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/payload/bin" "$stage/payload/lib" "$stage/payload/fonts" "$stage/payload/shaders"
cp "$shaders"/*.spv "$stage/payload/shaders/"
cp "$binary" "$stage/payload/bin/bim-slice"
cp "$font" "$licence" "$stage/payload/fonts/"
cp "$noto/NotoSans-Regular.ttf" "$noto/NotoSans-Bold.ttf" "$stage/payload/fonts/"
cp /usr/share/doc/fonts-noto-core/copyright "$stage/payload/fonts/LICENSE-NotoSans"

# Bundle every resolved library outside the system directories; refuse when
# one does not resolve at all.
if ldd "$binary" | grep -q "not found"; then
    ldd "$binary" | grep "not found" >&2
    echo "unresolved libraries; source .cache/bootstrap/env.sh first" >&2
    exit 1
fi
ldd "$binary" | sed -n 's/^.*=> \(\/.*\) (0x[0-9a-f]*)$/\1/p' | while IFS= read -r library; do
    case "$library" in
        /lib/*|/usr/lib/*|/lib64/*|/usr/lib64/*) ;;
        *) cp -L "$library" "$stage/payload/lib/" ;;
    esac
done

cat > "$stage/payload/bim-slice" <<'LAUNCHER'
#!/usr/bin/env bash
# Starts the installed BIM slice editor. Exports are written to the current
# directory.
home=$(dirname "$(realpath "$0")")
export BIM_SLICE_HOME="$home"
export LD_LIBRARY_PATH="$home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$home/bin/bim-slice" "$@"
LAUNCHER
chmod +x "$stage/payload/bim-slice"

cat > "$stage/payload/uninstall" <<'UNINSTALL'
#!/usr/bin/env bash
# Removes the installed BIM slice editor, its launcher and its menu entry.
set -euo pipefail
home=$(dirname "$(realpath "$0")")
name=$(basename "$home")
rm -f "$HOME/.local/bin/$name" "$HOME/.local/share/applications/$name.desktop"
rm -rf "$home"
echo "BIM slice removed"
UNINSTALL
chmod +x "$stage/payload/uninstall"

built=$(date -u +%Y-%m-%dT%H:%M:%SZ)
digest=$(sha256sum "$binary" | cut -c1-16)
printf '%s\nbuilt %s\nbinary sha256 %s\n' "$title" "$built" "$digest" > "$stage/payload/VERSION"

tar -C "$stage/payload" -czf "$stage/payload.tar.gz" .

cat > "$output" <<'HEADER'
#!/usr/bin/env bash
# Self-extracting installer of the BIM slice editor. Installs into
# ~/.local/share/@NAME@, adds ~/.local/bin/@NAME@ and a menu entry.
# Running it again replaces the installed copy. Remove with
# ~/.local/share/@NAME@/uninstall.
set -euo pipefail
target="$HOME/.local/share/@NAME@"
documents=$(xdg-user-dir DOCUMENTS 2>/dev/null || echo "$HOME")
mkdir -p "$HOME/.local/share"
fresh=$(mktemp -d "$HOME/.local/share/.@NAME@-XXXXXX")
line=$(awk '/^__PAYLOAD__$/ { print NR + 1; exit }' "$0")
tail -n +"$line" "$0" | tar -xz -C "$fresh"
rm -rf "$target"
mv "$fresh" "$target"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
ln -sf "$target/bim-slice" "$HOME/.local/bin/@NAME@"
cat > "$HOME/.local/share/applications/@NAME@.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=@TITLE@
Comment=Plan, section and 3D BIM editor on the native DynLex CAD kernel
Exec=$target/bim-slice
Path=$documents
Terminal=false
Categories=Graphics;Engineering;
Actions=example;

[Desktop Action example]
Name=Open with the example building
Exec=$target/bim-slice --example
DESKTOP
echo "@TITLE@ installed in $target"
echo "Start it from the applications menu or with: @NAME@   (@NAME@ --example opens an example building)"
exit 0
__PAYLOAD__
HEADER
sed -i "s/@NAME@/$name/g; s/@TITLE@/$title/g" "$output"
cat "$stage/payload.tar.gz" >> "$output"
chmod +x "$output"
echo "wrote $output"
