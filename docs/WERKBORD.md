# Werkbord — twee computers

Peildatum: 23 oktober 2026. Actuele claims gaan via een issue/draft PR met taak,
eigenaar, branch en bestanden. Werk dit bord bij zodra een taak wordt overgedragen
of afgerond. Een oude claim verdwijnt niet automatisch omdat een sessie uitvalt.

| Taak | Eigenaar | Branch | Bestanden / grens | Status |
|---|---|---|---|---|
| Sketch-ribbon en integratie | PC1 / Codex | `work/project1357-integration` | `bim_ui.dl`; integratie na afzonderlijke reviews | In uitvoering |
| Split face + undo + exacte side-start | PC1 / cursor_fix | `work/sketch-split` | `bim_editor.dl`, `bim_editor_core.dl`, bijbehorende tests | WIP; nog niet gebouwd |
| 3D-zijvlakselectie, drag en Split-gesture | PC1 / render_diagnosis | `work/side-push` | `main.dl`, pick-helper, `bim_scene.dl`, bijbehorende tests | WIP; afhankelijk van Split/core |
| Native vensterstijl, section box, properties en viewcube | PC1 / Codex | integratie + releasecandidate | App/UI; geen gelijktijdige PC2-edits | Code aanwezig; volledige nieuwe appcontrole open |
| Dak-/vloercontour: hoogtevlak behouden | PC1 / Codex | `work/plate-anchor` | `bim_model.dl` + `plate_anchor` | Apart gehouden; testen open |
| Vloersparingen | PC1 / Codex | `work/plate-openings` | Sparingenkern; GUI nog onvolledig | Geparkeerd |
| Compilergeheugen en compileertijd | PC2, na taakacceptatie | `pc2/compiler-memory` | Aparte DynLex-fork; eerst baseline | Voorgesteld / nog niet geclaimd |
| Windows/Linux builds en installers | PC2, na taakacceptatie | `pc2/build-installers` | CI/build/installer; geen modelleringscode | Voorgesteld / nog niet geclaimd |
| Release samenstellen en publiceren | PC1 / coördinator | `codex/windows-release-0.1.1` | Integratie, geteste artefacten, tags | Geblokkeerd op app-/installatietests |

Command `2360` en tool-id `27` zijn gereserveerd voor Sketch Split. Hergebruik
die nummers niet voor een andere functie. Leg nieuwe openbare commandocodes
vooraf vast. Zie [de werkafspraken en startinstructie](TWEE-COMPUTERS.md).
