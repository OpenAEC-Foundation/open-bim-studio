# Dynedra DWG-viewer

Deze repository bevat de read-only testapp als afzonderlijke spike. De app is
geschreven in DynLex; voor het decoderen van het binaire DWG-bestand gebruikt
ze een kleine, apart gebouwde reader op basis van de gepinde MPL-2.0-codec.
Dat deel telt niet mee als native DynLex-kernelport.

De bronbestanden onder `overlay/` worden voor bouwen en testen tijdelijk in een
lokale DynLex-checkout geplaatst. De bronbestanden worden in deze repository
beheerd. De standaardcheckout is
`build/dynlex-port/.worktrees/cadkernel-port`. Kies een andere checkout met
`--dynlex PATH` of de omgevingsvariabele `DYNLEX_CHECKOUT`.

```powershell
python -B spikes/dynlex-dwg-viewer/verify.py
```

De verificatie bouwt een kleine DWG met zes entiteittypen, leest deze terug,
controleert de segmenten en tekent ze vanuit DynLex in een verborgen
GPU-venster bij O0 en O2. Het testbestand komt onder de `build/`-map van de
DynLex-checkout. Na de test verwijdert het script alleen bronbestanden die het
zelf in de checkout heeft geplaatst.

Voor interactief gebruik kun je de bestanden laten staan:

```powershell
python -B spikes/dynlex-dwg-viewer/verify.py --keep
Push-Location build/dynlex-port/.worktrees/cadkernel-port
./build/dynedra-dwg-viewer-O2.exe "C:\path\to\drawing.dwg"
Pop-Location
```

Start de viewer met de DynLex-checkout als werkmap, omdat die de font-assets en
de DWG-reader bevat. Bediening: slepen om te verschuiven, Q/E om te zoomen,
pijlen om te roteren, 1 voor bovenaanzicht, 2 voor 3D-aanzicht, 0 voor
reset en Escape om af te sluiten.

De eerste viewer toont model-space-lijnen, cirkels, bogen, 2D/3D-polylijnen en
3D-vlakranden. Andere entiteittypen worden geteld als overgeslagen. Met name
blokreferenties, tekst, maatvoering, arceringen, meshes en ACIS-solids zijn
nog niet zichtbaar. Het is dus een bruikbare technische test, geen volledige
DWG-renderer.
