# Lokale branchconsolidatie — 23 oktober 2026

Op verzoek van Maarten zijn alle 40 bestaande lokale branches verenigd.
De basis is work/project1357-integration op b90cc2f. De merges zijn voorbereid
in integration/consolidate-main; main heeft deze geschiedenis met fast-forward overgenomen.
Dit is consolidatie van ontwikkeling, geen nieuwe release of installer.

## Inhoudelijk samengevoegd

- De huidige Windows-port, native vensterstijl, platformbrug, packaging,
  licentiemeldingen en controle van Windows-programma's en DLL's.
- Sketch Split en zijwaarts Push/Pull samen, inclusief exact geselecteerd vlak.
- Wandreferentielijnen, individuele laaghoogtes en property-setbewerking.
- HH/Hide in view en HR/Restore hidden elements, met de huidige editorvelden.
- Dak-/vloerankerbehoud gecombineerd met de kern voor meerdere vloersparingen.
  Bij contourwijziging blijven zowel het hoogtevlak als de sparingvalidatie behouden.
- De eerder geïntegreerde wapening, Spaces, DXF, selectie, section box en UI-fixes.

Bij oude cherry-picks is eerst patch-equivalentie gecontroleerd. Alleen branches
zonder unieke patches zijn met een history-only merge gemarkeerd. Bij gewijzigde
cherry-picks zijn conflicten beoordeeld; latere parsing-, test- en UI-fixes blijven
behouden. Er zijn geen complete oude modules over de nieuwe versies gekopieerd.

## Bewaring en afbakening

Vooraf is buiten de repository een volledige git bundle gemaakt en geverifieerd.
Ook de status, tracked diffs en untracked bestanden van iedere bestaande worktree
zijn veiliggesteld. De enige losse wijzigingen stonden in de oude hoofdwerkmap:
overlay/bim-slice/, overlay/gpu/ en patches/overlay-realistic-view.patch.
Die zijn niet als actieve modules geïntegreerd. Inmiddels zijn alle 166 bestanden
vastgelegd in het manifest onder docs/recovery/2026-10-23-rendering: 159 bestaan
al in de Git-geschiedenis, de zeven overige varianten zijn daar apart gearchiveerd
in bef64ab. De lokale originelen en alle bestaande worktrees blijven behouden.

Twee uitsluitend remote experimentele takken vallen buiten deze lokale opdracht:
origin/codex/dynedra-dwg-viewer en origin/spike/bim-slice-linear-members. Zij
blijven beschikbaar voor een aparte inhoudelijke beoordeling. Privéprojectdata
is niet aan de repository toegevoegd. Op aanvullend verzoek van Maarten zijn
de consolidatie, het herstelarchief en de daaropvolgende fixes naar origin/main
gepusht. De oorspronkelijke lokale branchnamen zijn niet afzonderlijk gepusht;
hun vastgelegde commits zijn bereikbaar via main.

## Validatie

- Alle oorspronkelijke lokale branch-tips zijn ancestors van de consolidatie.
- Geen dubbele functies binnen DynLex-modules; editorvelden en constructor
  hebben beide 129 argumenten/velden.
- DynLex-preflight: 320 gewijzigde/nieuwe functies gecontroleerd, geen meldingen.
- Bash-syntax en Linux C-platformbrug met -Wall -Wextra -Werror gecontroleerd.
- Kernbundel op broncommit 722a740: plate_anchor, plate_openings en push_pick
  PASS (54 checks), zonder compilerdiagnoses; 7m28s, piek 4.42 GiB.
  De eerste poging ontdekte een double-free bij het weigeren van een contour.
  Deze is hersteld; de extra regressies testen helling en sparingen samen.
  De gecompileerde bundel is nogmaals afzonderlijk uitgevoerd en vergeleken,
  exit 0. De oorspronkelijke wrapper eindigde na de drie PASS-regels met een
  Bash-parsefout doordat build.sh tijdens die run was aangepast. Het huidige
  script slaagt voor bash -n; wijzig een lopend buildscript voortaan niet.
- Editorbundel op 9912496: sketch_split, hide_element, layer_heights NIET
  UITGEVOERD. De compile is na circa 10m34s gestopt wegens te weinig beschikbaar
  geheugen (compiler circa 9.3 GiB RSS). De guard meldde 582484 kB beschikbaar;
  de compilerchild is daarna expliciet gestopt omdat timeout een eigen groep had.
  Geen nieuwe automatische poging gestart; de gebruikersapp bleef open.
  Deze editortests blijven open; de latere appbuild staat hieronder. Main is de
  geconsolideerde ontwikkelbasis, niet een gevalideerde release.
- Compilerbinary SHA-256: 2dbd12c50b009233682a76a923cb961eb8974d25d1eac71aa15e040bd7bfb4ed.
  Dit is de vastgelegde lokale binary, geen claim over een reproduceerbare
  upstream-compilerbuild.
- Windows-app/MSI en volledige GUI-regressies zijn nog niet bevestigd.
  Vloersparingen hebben nog geen volledige gebruikersinterface.

## Vervolgvalidatie na de consolidatie

De oude gebruikersapp is op verzoek opgeslagen en gesloten om geheugen vrij te
maken voor een volledige appbuild. De eerste poging ontdekte fouten in de
section-boxdispatch en de groepering van negatieve property-contextcodes;
f111f2f herstelt die. De tweede poging ontdekte een record/pointerverschil in
de wandpreview; 42992c6 herstelt dat. Deze builds zijn niet geslaagd en leveren
geen gevalideerde nieuwe app op.

De volledige Linux-developmentbuild op 42992c6 is vervolgens geslaagd zonder
compilerdiagnoses: 14m47s, piek 8.54 GiB, exit 0, -O0 zonder debug-symbolen.
De nieuwe binary heeft het vooraf opgeslagen IFCXB-model geopend. De lokale
API bevestigt de geladen objecten; plattegrond en 3D-weergave zijn visueel
gecontroleerd, inclusief modelboom, view-properties, frames en section box.
Dit is een opstartcontrole met een klein QA-model, geen volledige regressietest
of installercontrole. De geneste X11-preview meldt ontbrekende DRI3-ondersteuning;
weergave werkt, maar deze controle valideert geen GPU-prestaties.

## Vastgelegde oorspronkelijke tips

| Branch | Commit |
|---|---|
| codex/windows-release-0.1.1 | 1e4dedab093c |
| codex/windows-v0.1 | f25d0da9968d |
| feature/reinforcement-module | f2c72452ea7f |
| main | 1b77f1eee2c8 |
| spike/dynlex-bim-slice | 184d6ec5e10c |
| work/boundary-numeric | 14b82b0913f8 |
| work/context-properties | e44a920e0b7a |
| work/coord | dfb85bfa60f2 |
| work/cursor-shadows | f8398571a25a |
| work/duplicate-wall-type | 9e5342a6791c |
| work/dxf-diagnostics | dbfed0f38fde |
| work/dxf-native | 2696a5901b58 |
| work/grid-coordinates | d628b4e1339a |
| work/gui-levels | 0023dd925c79 |
| work/gui-preflight | 007dc76ea595 |
| work/hide-element | 960ca8e5375a |
| work/int | cf5327b1bee8 |
| work/linear-type-copy | b0c1149d9b23 |
| work/linear-xyz | dbc4ce43a0e0 |
| work/masonry-module | 2bbed9f9094e |
| work/masonry-review | 0e8b0e593eef |
| work/panel-icons | debb48bddd47 |
| work/plate-anchor | c86a1038cc81 |
| work/plate-openings | a6c217b30b55 |
| work/project1357-integration | b90cc2f070e8 |
| work/render-idle | ce25374cb061 |
| work/roof-routing | 6fe8ad39bccf |
| work/section-box-fix | c5ac50d840fb |
| work/side-push | 7cb9bfa92de5 |
| work/sketch-split | 5a226fe64e88 |
| work/space-explorer | 87891b31103d |
| work/space-object | 36a221a12da5 |
| work/space-test-split | ba8a5be623fc |
| work/system-profiles-fix | 4c168c2722d5 |
| work/ui | 20b0645d6d07 |
| work/wall-location-line | 122aec4d1ced |
| work/wall-masonry | 68102675e391 |
| work/window-host | 68102675e391 |
| work/window-style | 5bfc365068fb |
| work/windows-release | b4aed5f6946f |
