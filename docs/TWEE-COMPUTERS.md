# Open BIM Studio — samenwerken op twee computers

Peildatum: 23 oktober 2026. Eigenaar van de werkverdeling: Maarten; integratie
wordt in de bestaande Codex-sessie op computer 1 gecoördineerd.

## Startpunt en status

De native BIM-modeller staat in de unitmappen in de root (`kernel/`, `model/`,
`formats/`, `graphics/`, `editor/`, `app/`, `automation/`). De productlogica en
geometrie worden in **DynLex** ontwikkeld. `build.sh` compileert vanuit de
repositoryroot met een afzonderlijke DynLex-checkout als compiler; er wordt
niets meer over die checkout heen gelegd. De bestaande platformbrug en
buildscripts zijn infrastructuur; voeg geen Python-implementatie van BIM-tools toe.

Gebruik **main** als gezamenlijke ontwikkelbasis, zodra de lokale consolidatie
naar GitHub is gepusht. Controleer altijd de commit-hash; de remote kan nog achterlopen.
De voormalige integratie-, Windows-, Sketch- en modulebranches zijn lokaal
samengevoegd. Begin nieuw werk vanaf main in één korte taakbranch en lever een
PR naar main. Na integratie en controle kan die taakbranch worden verwijderd.

Main is een ontwikkelbasis, geen releasecertificaat. Vloersparingen hebben nu een
geïntegreerde kern; de GUI is nog onvolledig. Volledige app- en Windows-validatie
blijven expliciete releasevoorwaarden. Zie [het consolidatieverslag](CONSOLIDATIE.md).

## Demarcatie

Dit is de voorlopige standaardverdeling. Maarten kan computer 2 een andere
afgebakende module geven; leg die wijziging eerst hier en in het taakbord vast.

| Werkgebied | Eigenaar | Afbakening |
|---|---|---|
| Sketch, zijwaarts Push/Pull, Split face, undo en selectie | Computer 1 | Editor, geometrie en interactie |
| Ribbon, properties, viewcube, section box en vensterstijl | Computer 1 | Applicatie-UI en rendering |
| BIM-objecten, gegevensmodel, bestandsschema en privéproject | Computer 1 | Geen parallelle schemawijzigingen |
| DynLex-compiler, compileertijd, geheugengebruik en incrementeel bouwen | Computer 2 | Eigen compilercheckout/fork; eerst reproduceerbare metingen |
| Windows-/Linux-builds, CI, installer en distributie | Computer 2 | Bouw een expliciet gekozen commit; verander hiervoor geen modelleerfuncties |
| Integreren van branches, tags en publiceren van releases | Coördinator op computer 1 | Na testresultaten en afstemming; één publicerende sessie |

Computer 1 laat nieuwe toolchain-/installerwijzigingen aan computer 2 zodra die
sessie de taak heeft aangenomen. Een review of foutmelding over de grens mag;
dezelfde bestanden tegelijk aanpassen niet.

## Bestanden en eigenaarschap

Paden hieronder zijn relatief aan de repositoryroot.

**Per module een eigenaar** sinds de modulesplitsing van 2026-10-28: de tabel
staat in [OWNERS.md](OWNERS.md) en `.github/CODEOWNERS`; een computer claimt daar
de modules waaraan hij werkt. Het taakbord [WERKBORD.md](WERKBORD.md) houdt de
lopende claims.

**Computer 2:** `build.sh`, `toolchain.sh`, `scripts/`, `.github/workflows/`,
`installer/`, `platform/`, `patches/` en `lib/`; daarnaast de compilerbron
in een **afzonderlijke DynLex-repository**. Native platformcode blijft beperkt
tot platformintegratie. De app blijft DynLex.

**Eerst afstemmen, dan één eigenaar aanwijzen:**

- `kernel/` en `viewer/` (Vulkan en shaders);
- `.github/workflows/` in de repositoryroot is de enige plek van de workflows;
- compiler-ABI, openbare module-API's, nieuwe commandocodes, bestandsschema,
  exportsemantiek en migraties;
- een wijziging die bestanden van beide computers nodig heeft.

Voor zo'n wijziging volstaat een concrete claim in issue/PR: taak, eigenaar,
bestanden, branch en verwachte API. De coördinator bevestigt de verdeling. Daarna
hoeft niet voor iedere commit opnieuw toestemming te worden gevraagd.

## Werkwijze op computer 2

Maak een eigen clone op de eigen schijf. Deel geen `.git`-map, worktree of
builddirectory via een netwerkschijf/OneDrive. GitHub is de uitwissellaag.

```sh
git clone --branch main https://github.com/OpenAEC-Foundation/open-bim-studio.git
cd open-bim-studio
git switch -c pc2/build-installers
git rev-parse HEAD
```

1. Lees dit document en `docs/WERKBORD.md`. Meld in een issue/PR dat computer 2
   de toolchain-/buildtaak heeft aangenomen, met de exacte startcommit.
2. Gebruik één taak per branch, bijvoorbeeld `pc2/compiler-memory` of
   `pc2/windows-installer`. Maak een draft PR naar
   `main`; de coördinator controleert en integreert.
3. Begin met een reproduceerbare build, niet met een grote compilerverbouwing.
   Noteer OS, compilercommit, compilerbinary-hash, appcommit, opdracht, duur,
   piekgeheugen, diagnostics en testuitslagen.
4. Push de eigen branch regelmatig. Gebruik geen force-push op gedeelde
   branches en push niet rechtstreeks naar de integratiebranch, releasebranch
   of `main`. Geen automatische merges, tags of public releases.
5. Lever bij afronding commit-hash, geraakte bestanden, tests, artefacten en
   resterende beperkingen aan. De coördinator integreert en werkt het taakbord bij.

Een compilerpatch hoort als commit/PR in de DynLex-fork thuis. De BIM-repo krijgt
de vastgelegde compilerreferentie en zo nodig een reproduceerbare patch; geen
afhankelijkheid van een ongedocumenteerde lokale compilerbinary.

## Builds en bekende blokkades

- **Eén DynLex-compile per fysieke computer.** Computer 2 mag dus onafhankelijk
  bouwen terwijl computer 1 bouwt, als beide afzonderlijk genoeg geheugen hebben.
- Iedere taak krijgt een eigen `BIM_BUILD_DIR`. Deel geen uitvoermappen tussen
  branches of computers. Sluit nooit een applicatie die Maarten gebruikt.
- Computer 1 heeft 16 GB RAM. De laatste volledige `dev-test` stopte met
  `std::bad_alloc`; de geheugenbewaking registreerde ook te weinig beschikbaar
  geheugen. Vergroot niet blind de limiet en start geen tweede compiler.
- Testbundels hebben hoogstens drie tests. `properties_context` en tests die
  `bim_view_panel.dl` importeren zijn zwaar; noem die niet licht. Begin bijvoorbeeld
  met `ui_layout`, `text_glyphs` en `plan_pan`, daarna appbouw zonder ingebedde tests.
- De Windows-compilerbouw is gelukt in [run 39560063519](https://github.com/OpenAEC-Foundation/open-bim-studio/actions/runs/39560063519).
  Compilerartifact en caches zijn opgeslagen. De appfase stopte bij de eerste
  `ui_layout`-test wegens een ontbrekende standaardimport; die fix staat in de
  startbranch (`34b9fde`, gevolgd door `78e55ab`). App/MSI zijn daarmee nog niet bewezen.
- Hergebruik beschikbare Actions-artifacts/caches. Lees
  `docs/notes/windows-release.md`. Controleer altijd de actuele
  workflow en artifactbeschikbaarheid voordat je een nieuwe run start.
- Laat buildrapporten de **werkelijk gebouwde commit** noemen. Een groene
  compilerbuild of een nieuwere branch-HEAD bewijst niets over een oudere appbinary.

## Privédata en oplevering

De repository is openbaar. Privé-DWG/PDF-bronnen, projectmodellen, absolute
privébronpaden, tokens en lokale configuratie worden niet gepusht. Gebruik voor
tests generieke fixtures. Draag privéprojectdata alleen via een afzonderlijk,
door Maarten gekozen kanaal over.

Een taak is klaar wanneer de code gecommit is, de passende tests slagen, de
beperkingen beschreven zijn en de coördinator de wijziging heeft geïntegreerd.
Een installer vereist bovendien een installatie-/starttest op het doelplatform;
een geslaagde headless test vervangt geen Windows-GUI-controle.

## Starttekst voor de sessie op computer 2

> Werk aan Open BIM Studio in je eigen clone, vanaf
> `origin/main`. Lees eerst `docs/TWEE-COMPUTERS.md` en
> `docs/WERKBORD.md`. Jij beheert voorlopig compiler, buildprestaties, CI en
> installers. Computer 1 beheert Sketch/Push-Pull/Split, UI, BIM-model en
> integratie. Maak een `pc2/...`-branch en meld je startcommit en bestandsclaim.
> Hergebruik de bestaande Windows-compilerartifact/cache waar mogelijk.
> Doe eerst een reproduceerbare build en rapporteer testuitslagen en geheugen.
> Geen appfunctionaliteit, gedeelde kernel-API of schema wijzigen zonder
> afstemming; geen gebruikersapp sluiten. Productcode blijft DynLex. Push je
> eigen branch en lever een draft PR aan; de coördinator merget en publiceert.

## Connection module development — 2026-10-26

The explicit module assignment extends this session to issue #6 on
`feature/connection-module`, based on `1768c2d`. Scope: connection kernel,
BIM adapter, native connection persistence, connection commands/properties,
headless tests and a synthetic steel hall example. Command range 2320–2330
is reserved for steel recipes, welds and reusable connection types. Existing
base-plate style 2 and anchor kind 3 remain compatible. No compiler changes.

The required full-build repair also renames local identifiers in sheet paper
recording and plan/mesh helpers to avoid DynLex pattern-word capture. These are
identifier-only changes; sheet/layout behaviour is unchanged.

The build repair includes `build.sh` and `tools/check_dynlex_locals.py`: a fast
application-source preflight for these proven local/pattern-name collisions,
with focused Python regression tests. It does not modify the compiler or the
active source snapshots/build scripts.

GUI validation exposed a connection-hole meshing hotspot in the overlay's
`kernel/brep/brep_append.dl`. The connection task also owns its bounded
face-component traversal repair and geometric regression checks: direct
arena-slot membership and adjacency, preserving seed and breadth-first order.
The compiler checkout is unchanged. Application readiness still requires the
full steel-hall scene and GUI checks.

## Compiler and drilled display geometry — 2026-10-27

The explicit performance assignment extends this session to an isolated DynLex
compiler worktree. The connection task also covers `bim_plate_mesh.dl`,
`bim_swept_perforations.dl`, `kernel/fast/perforation.dl`, their scene
integration and geometry tests. `bim_profiles.dl` is included for the missing
rounded-box tangent points exposed by the hollow-brace drilling checks. Product geometry remains DynLex. The fast display
path accepts closed planar stock and separate through-bores; unsupported
cuts retain the existing general BREP path. Validation must establish volumes,
closed meshes, complete hall rendering and actual editor interaction.

`build.sh` and `toolchain.sh` accept an explicit `BIM_DYNLEX_COMPILER` for isolated
candidate benchmarking. Compiler-binary hashes must be recorded separately from
the library checkout commit. Compiler regression checks and application GUI
checks remain separate acceptance conditions. One compiler runs per machine.
