#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
# Builds a self-extracting Linux installer for Open BIM Studio.
#
#   installer/make-installer.sh BINARY OUTPUT [release|dev]
#
# BINARY is a built ui/shell/main.dl; OUTPUT is the installer file
# to write. `release` (the default) installs as `open-bim-studio`; `dev` installs
# a development build (for instance -O0 -g) side by side as
# `open-bim-studio-dev`,
# with its own directory, launcher and menu entry. Run from the repository root with .cache/bootstrap/env.sh sourced,
# so the libraries the binary links against resolve. Every library that does
# not come from the system (/lib, /usr/lib) is copied into the installer,
# together with the font and its licence and the SPIR-V shaders compiled from
# viewer/shaders into build/shaders, so an installed copy does not depend
# on this repository, its caches or the build machine's temporary files.
set -euo pipefail

binary=$(realpath "$1")
output=$2
variant=${3:-release}
version=${BIM_VERSION:-development}
source_commit=${BIM_SOURCE_COMMIT:-unknown}
case "$variant" in
    release) name=open-bim-studio; title="Open BIM Studio" ;;
    dev) name=open-bim-studio-dev; title="Open BIM Studio (dev)" ;;
    *) echo "unknown variant $variant" >&2; exit 1 ;;
esac
root=$(pwd)
font="$root/ui/shell/fonts/LiberationMono-Regular.ttf"
licence="$root/ui/shell/fonts/LICENSE-LiberationFonts"
[ -x "$binary" ] || { echo "not an executable: $binary" >&2; exit 1; }
[ -f "$font" ] && [ -f "$licence" ] || { echo "run from the repository root" >&2; exit 1; }
shaders="$root/build/shaders"
# The interface font, Noto Sans (SIL Open Font License), from the system.
noto=/usr/share/fonts/truetype/noto
[ -f "$noto/NotoSans-Regular.ttf" ] || { echo "Noto Sans not found in $noto (package fonts-noto-core)" >&2; exit 1; }
[ -f "$shaders/screen_vertex.spv" ] || { echo "run build.sh generate first (viewer/shaders into build/shaders)" >&2; exit 1; }

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/payload/bin" "$stage/payload/lib" "$stage/payload/fonts" "$stage/payload/shaders"
cp -R "$root/installer/licenses" "$stage/payload/licenses"
cp "$shaders"/*.spv "$stage/payload/shaders/"
cp "$binary" "$stage/payload/bin/open-bim-studio"
cp "$font" "$licence" "$stage/payload/fonts/"
cp "$noto/NotoSans-Regular.ttf" "$noto/NotoSans-Bold.ttf" "$stage/payload/fonts/"
cp /usr/share/doc/fonts-noto-core/copyright "$stage/payload/fonts/LICENSE-NotoSans"
# The drawing font, osifont (LGPL-3.0 with the GPL font exception).
cp "$root/ui/shell/fonts/osifont.ttf" "$stage/payload/fonts/"
cp "$root/ui/shell/fonts/README.md" "$stage/payload/fonts/README-osifont.md"
# The interface fonts of the OpenAEC style, Inter and JetBrains Mono, with
# their licences (SIL OFL 1.1).
for style_font in Inter-Regular.ttf Inter-Medium.ttf Inter-SemiBold.ttf JetBrainsMono-Regular.ttf Inter-OFL.txt JetBrainsMono-OFL.txt; do
    cp "$root/ui/shell/fonts/$style_font" "$stage/payload/fonts/"
done
# The interface's icons (CC BY-SA 4.0, see icons/README.md).
mkdir -p "$stage/payload/icons"
cp "$root/ui/shell/icons/ui-icons.txt" "$root/ui/shell/icons/README.md" "$stage/payload/icons/"
cp "$root/ui/shell/icons/open-bim-studio.svg" "$root/ui/shell/icons/open-bim-studio.png" "$root/ui/shell/icons/open-bim-studio.rgba" "$stage/payload/icons/"
# The script that reads 2D drawings (DXF, DWG, PDF) for Collaborate > Import.
mkdir -p "$stage/payload/import"
cp "$root/exchange/import/drawing_to_lines.py" "$stage/payload/import/"

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

cat > "$stage/payload/open-bim-studio" <<'LAUNCHER'
#!/usr/bin/env bash
# Starts the installed Open BIM Studio. Exports are written to the current
# directory.
home=$(dirname "$(realpath "$0")")
export OPEN_BIM_STUDIO_HOME="$home"
export LD_LIBRARY_PATH="$home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$home/bin/open-bim-studio" "$@"
LAUNCHER
chmod +x "$stage/payload/open-bim-studio"

cat > "$stage/payload/uninstall" <<'UNINSTALL'
#!/usr/bin/env bash
# Removes the installed Open BIM Studio, its launcher and its menu entry.
set -euo pipefail
home=$(dirname "$(realpath "$0")")
name=$(basename "$home")
rm -f "$HOME/.local/bin/$name" "$HOME/.local/share/applications/$name.desktop"
rm -rf "$home"
echo "Open BIM Studio removed"
UNINSTALL
chmod +x "$stage/payload/uninstall"

built=$(date -u +%Y-%m-%dT%H:%M:%SZ)
digest=$(sha256sum "$binary" | cut -c1-16)
printf '%s\nversion %s\nsource %s\nbuilt %s\nbinary sha256 %s\n' "$title" "$version" "$source_commit" "$built" "$digest" > "$stage/payload/VERSION"

tar -C "$stage/payload" -czf "$stage/payload.tar.gz" .

cat > "$output" <<'HEADER'
#!/usr/bin/env bash
# Self-extracting installer of Open BIM Studio. Installs into
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
ln -sf "$target/open-bim-studio" "$HOME/.local/bin/@NAME@"
cat > "$HOME/.local/share/applications/@NAME@.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=@TITLE@
Icon=$target/icons/open-bim-studio.svg
Comment=Plan, section and 3D BIM editor on the native DynLex CAD kernel
Exec=$target/open-bim-studio
Path=$documents
Terminal=false
Categories=Graphics;Engineering;
StartupWMClass=open-bim-studio
Actions=example;

[Desktop Action example]
Name=Open with the example building
Exec=$target/open-bim-studio --example
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
