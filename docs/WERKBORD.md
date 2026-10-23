# Werkbord — twee computers

Peildatum: 23 oktober 2026. Actuele claims gaan via een issue/draft PR met taak,
eigenaar, branch en bestanden. Werk dit bord bij zodra een taak wordt overgedragen
of afgerond. Een oude claim verdwijnt niet automatisch omdat een sessie uitvalt.

| Taak | Eigenaar | Branch | Bestanden / grens | Status |
|---|---|---|---|---|
| Sketch-ribbon en integratie | PC1 / Codex | `main` | `bim_ui.dl`; integratie na afzonderlijke reviews | Lokaal geïntegreerd; appcontrole open |
| Split face + undo + exacte side-start | PC1 / cursor_fix | `main` | `bim_editor.dl`, `bim_editor_core.dl`, bijbehorende tests | Lokaal geïntegreerd; test open |
| 3D-zijvlakselectie, drag en Split-gesture | PC1 / render_diagnosis | `main` | `main.dl`, pick-helper, `bim_scene.dl`, bijbehorende tests | Lokaal samen met Split/core geïntegreerd; test open |
| Native vensterstijl, section box, properties en viewcube | PC1 / Codex | `main` | App/UI; geen gelijktijdige PC2-edits | Code aanwezig; volledige nieuwe appcontrole open |
| Dak-/vloercontour: hoogtevlak behouden | PC1 / Codex | `main` | `bim_model.dl` + `plate_anchor` | Lokaal geïntegreerd; tests lopen |
| Vloersparingen | PC1 / Codex | `main` | Sparingenkern; GUI nog onvolledig | Kern lokaal geïntegreerd; GUI nog onvolledig |
| Compilergeheugen en compileertijd | PC2, na taakacceptatie | `pc2/compiler-memory` | Aparte DynLex-fork; eerst baseline | Voorgesteld / nog niet geclaimd |
| Windows/Linux builds en installers | PC2, na taakacceptatie | `pc2/build-installers` | CI/build/installer; geen modelleringscode | Voorgesteld / nog niet geclaimd |
| Release samenstellen en publiceren | PC1 / coördinator | `main` | Integratie, geteste artefacten, tags | Geblokkeerd op app-/installatietests |

Command `2360` en tool-id `27` zijn gereserveerd voor Sketch Split. Hergebruik
die nummers niet voor een andere functie. Leg nieuwe openbare commandocodes
vooraf vast. Zie [de werkafspraken en startinstructie](TWEE-COMPUTERS.md).
