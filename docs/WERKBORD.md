# Werkbord — twee computers

Peildatum: 23 oktober 2026. Actuele claims gaan via een issue/draft PR met taak,
eigenaar, branch en bestanden. Werk dit bord bij zodra een taak wordt overgedragen
of afgerond. Een oude claim verdwijnt niet automatisch omdat een sessie uitvalt.

| Taak | Eigenaar | Branch | Bestanden / grens | Status |
|---|---|---|---|---|
| Sketch-ribbon en integratie | PC1 / Codex | `main` | `bim_ui.dl`; integratie na afzonderlijke reviews | Lokaal geïntegreerd; appcontrole open |
| Split face + undo + exacte side-start | PC1 / cursor_fix | `main` | `bim_editor.dl`, `bim_editor_core.dl`, bijbehorende tests | Lokaal geïntegreerd; editorcompile gestopt wegens geheugen |
| 3D-zijvlakselectie, drag en Split-gesture | PC1 / render_diagnosis | `main` | `main.dl`, pick-helper, `bim_scene.dl`, bijbehorende tests | Lokaal geïntegreerd; pick-kern PASS, GUI-controle open |
| Native vensterstijl, section box, properties en viewcube | PC1 / Codex | `main` | App/UI; geen gelijktijdige PC2-edits | Code aanwezig; volledige nieuwe appcontrole open |
| Dak-/vloercontour: hoogtevlak behouden | PC1 / Codex | `main` | `bim_model.dl` + `plate_anchor` | Lokaal geïntegreerd; 17 checks PASS |
| Vloersparingen | PC1 / Codex | `main` | Sparingenkern; GUI nog onvolledig | Kern geïntegreerd; 24 checks PASS, GUI nog onvolledig |
| Compilergeheugen en compileertijd | PC2, na taakacceptatie | `pc2/compiler-memory` | Aparte DynLex-fork; eerst baseline | Voorgesteld / nog niet geclaimd |
| Windows/Linux builds en installers | PC2, na taakacceptatie | `pc2/build-installers` | CI/build/installer; geen modelleringscode | Voorgesteld / nog niet geclaimd |
| Release samenstellen en publiceren | PC1 / coördinator | `main` | Integratie, geteste artefacten, tags | Geblokkeerd op app-/installatietests |

Command `2360` en tool-id `27` zijn gereserveerd voor Sketch Split. Hergebruik
die nummers niet voor een andere functie. Leg nieuwe openbare commandocodes
vooraf vast. Zie [de werkafspraken en startinstructie](TWEE-COMPUTERS.md).

## PC1 claim — 24 October 2026

Codex owns `feature/steel-baseplates`: the single-column base-plate recipe,
connection validation and its ribbon/properties integration. Command **2313** is
reserved for **Base plate**. Complex style **2** denotes a one-column base plate;
addition kind **3** denotes an anchor group. Existing styles remain unchanged.
Files: `connections.dl`, `bim_connections.dl`, `bim_baseplate.dl`,
`bim_editor.dl`, `bim_editor_properties.dl`, `bim_ui.dl`, and related tests.

The same PC1 task fixes selection overlay clipping and adds view-tab dragging in
`main.dl`, `bim_workspace_tabs.dl` and `overlay/lib/vulkan/context.dl`.
The Vulkan change separates overlay scissoring from its full-window projection;
mesh viewports and the batch record layout are unchanged. PC2 should not edit
these files concurrently. Full application/interactive validation is pending.

Additional PC1 scope on this branch: commands **2228** (bending schedule),
**2229** (optional reinforcement diameter display) and **2314** (opening detail).
Opening-detail settings use **2400100–2400105** on the opening; properties use
**12600–12604**. Window recipes are appended after the existing 21 entries so
stored indices remain stable. The application icon module and the two installer
asset lists are included in the user-requested taskbar-icon work.

Validation snapshot: `baseplate`, `workspace_tabs`, `viewport_overlay` PASS;
`connections_model` PASS in the preceding bundle. `opening_detail`,
`bending_schedule` and `reinforcement_schedule` are still running. Full app,
GUI, installer and large-steel-model checks remain pending. This is a development
branch, not a release or fabrication-ready connection library.

### PC1 — fastener thread preview and service-network isolation

`feature/steel-baseplates`: PC1 owns `bim_fastener_detail.dl`, the connection
line-mesh insertion in `bim_scene.dl`, and connector grouping in
`bim_network.dl`. Cosmetic thread is a bounded helix on the exposed start of
the fastener, with approximate pitch; it is not a manufactured thread profile.
It retains the connection's selection ID and uses the existing GPU line path.
Service connectors must share both their linear role and system assignment;
coincident pipes, ducts and cable trays must not form cross-discipline fittings.
Validation: `fastener_detail`, `network_isolation` and `fastener_scene` PASS
in `/tmp/obs-fastener-network-r3`, without compiler diagnostics. The isolated
fastener check also passes with only connection-kernel imports. Full application
visual inspection and the existing broad `network` regression remain pending.
The thread preview covers at most two diameters, with 192 line segments per
fastener; distant-view performance has not yet been measured.

### PC1 — timber and Reynaers window recipes

PC1 extends `bim_system_types.dl` with append-only recipe indices 33–42,
updates `system_types.expected.txt`, and adds the lightweight `window_recipes`
check. Sources and explicit schematic-geometry limits are in
`spikes/dynlex-bim-slice/WINDOW-SYSTEMS.md`. No model schema or new command codes.
Validation: `window_recipes` PASS (seven checks, no compiler diagnostics) in
`/tmp/obs-window-recipes`. Full gallery and GUI validation remain pending;
no new application build has been launched.
