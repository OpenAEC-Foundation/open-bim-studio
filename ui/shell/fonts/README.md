# Drawing font

`osifont.ttf` is osifont (version 0.1.20221020), the ISO 3098 technical
lettering font that Open 2D Studio draws its CAD text with; copied from Open 2D
Studio's `public/fonts`. Upstream: https://github.com/hikikomori82/osifont/

Licence, as stated in the font's own name table: distributed under the GNU
LGPL version 3 with the GPL font exception (a document that embeds the font is
not thereby covered by the GPL). The editor uses it for text in the drawing:
grid names, area labels, sketch text and level labels.

# Interface fonts

The OpenAEC style (Style Repo 0.4) sets the interface in Inter and its
labels and figures in JetBrains Mono. `Inter-Regular.ttf`, `Inter-Medium.ttf`,
`Inter-SemiBold.ttf` and `JetBrainsMono-Regular.ttf` are copied from the
OpenAEC Style Repo (`crates/openaec-ui/assets/fonts`), with their licences
`Inter-OFL.txt` and `JetBrainsMono-OFL.txt` (from `crates/openaec-ui/licenses`):
both under the SIL Open Font License 1.1. Upstream:
https://github.com/rsms/inter and https://github.com/JetBrains/JetBrainsMono.
The installer ships them; when they are missing the editor falls back to
Noto Sans and Liberation Mono.

## Lao fallback

`NotoSansLao.ttf` (variable font, default weight 400) is from
https://github.com/google/fonts/tree/main/ofl/notosanslao, git blob
`c9e20f733b5b0c8edebc5eb9a8783dc2caa67f5a`. SHA-256:
`9608b94603a82d09a8038946f9775242f99e3b3459b7f1e4d5b335b578cd7ab3`.
Its SIL OFL 1.1 licence is `NotoSansLao-OFL.txt`. HarfBuzz shapes Lao marks
and contextual glyphs before atlas drawing; see https://harfbuzz.github.io/harfbuzz-hb-ft.html.
