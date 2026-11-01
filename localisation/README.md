# Interface translations

Open BIM Studio is a native DynLex application. Issue [#157](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/157)
is implemented with UTF-8 JSON message catalogues, without a Rust or browser runtime.

Choose **File → Settings → General → Language**. English, Dutch and Lao are the
initial choices. Changes apply immediately and survive restarting. The setting
belongs to the application, not the project; changing it does not rename model
objects, types, materials, properties, IFC entities or saved files.

## Translate

Copy `messages/en.json`, change `locale` and the language's own `name`, then
translate the values in `messages`. Keep the stable keys unchanged. Literal UTF-8
and JSON Unicode escapes are both accepted. The initial 36 keys cover selected
interface controls and ribbon actions, not the whole application. Dutch and Lao
catalogues are starter translations; Lao terminology needs native-speaker review.
Further interface strings should receive explicit keys as they are migrated.
Complete Dutch interface and domain terminology remain tracked in #104.

Missing or empty messages fall back to the English text supplied at the call site.
Malformed catalogues (including duplicate keys, non-string values and invalid
UTF-8) are rejected as a whole. JSON is loaded once at startup or language change;
lookups use a hash table. Limits: 1 MiB per catalogue, 4096 entries, 128 bytes per
key and 65536 bytes per message. There are no interpolation placeholders yet;
keep model/user values outside translated text.

For a new locale, add its choice in `bim_app_files.dl` and `bim_ui_files.dl`,
add renderer font/shaping coverage for its script, and run the checks below.
Installers copy all `messages/*.json`; translators can edit these files without
recompiling the application. Application-owned chrome uses `the bim message KEY
defaulting to ENGLISH in CATALOGUE`; never pass model names through chrome lookup.

## Lao rendering

Noto Sans Lao is bundled under SIL OFL 1.1 (font and provenance in
`ui/shell/fonts/README.md`). HarfBuzz supplies contextual glyph IDs and combining
mark offsets; FreeType rasterizes those glyphs into the atlas at each fixed UI
size. Width calculation and drawing consume the same shaped advances. Lao caps
labels preserve the script and do not insert letter spacing. Text fitting keeps
UTF-8 scalar boundaries. General bidirectional layout and arbitrary-script
fallback are not implemented by this initial locale support.

HarfBuzz is loaded as a native service by the platform shim. Linux development
needs `libharfbuzz.so.0` (normally installed with the desktop); the installer
bundles it. Windows uses the app-owned pinned `platform/windows/vcpkg.json` and
`scripts/install-text-shaper-windows.ps1`; packages require `harfbuzz.dll` and
include dependency notices. See the [HarfBuzz FreeType contract](https://harfbuzz.github.io/harfbuzz-hb-ft.html)
and the [pinned vcpkg port](https://github.com/microsoft/vcpkg/blob/56bb2411609227288b70117ead2c47585ba07713/ports/harfbuzz/vcpkg.json).
The native cache compares the full text, face and length, and is capped at 8 MiB.
Each shaping run is limited to 4096 UTF-8 bytes. Faces keep their pixel sizes
and remain alive for the application lifetime. If the shaping service or Lao
font is unavailable in a development environment, the interface uses English
instead of showing unreadable Lao labels.

## Check

```sh
./build.sh bundle text_glyphs lao_shaping text_atlas_paths
./build.sh bundle catalogues interface_language app_files
python3 tools/check_lao_shaping.py
./build.sh dev-test catalogues lao_shaping app_files
```

The first bundle checks decoding, fallback, catalogue rejection, glyph mapping
and application settings. The native shaping check uses the real font and tests
combining marks, offsets, glyph coverage and cache consistency. A GUI check must
also exercise language switching, restarting and installing outside the source tree.
