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
