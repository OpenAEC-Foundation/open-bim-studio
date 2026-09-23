# Dynedra DWG Viewer

A read-only native DynLex test application. It opens a DWG file from the command
line, shows its model-space wireframe, and supports pan, zoom and orbit. The
window and rendering are DynLex. DWG decoding is a separate Rust reader built
from the same pinned MPL-2.0 `acadrust` revision used by the upstream kernel's
optional codec dependency; it does not count as native DynLex kernel coverage.

The first viewer supports lines, circles, circular arcs, 2D/3D polylines and
3D face outlines. Curves are sampled for display. Other entity types are
counted as skipped in the sidebar, not silently claimed as rendered. The app
does not edit or save DWG. Model-space block inserts, text, dimensions, hatches,
meshes and ACIS solids still need rendering paths.

From the repository root on Windows:

```powershell
cargo build --offline --manifest-path examples/dynedra-dwg/bridge/Cargo.toml --target-dir build/dynedra-dwg-cargo
build/dynlex.exe examples/dynedra-dwg/main.dl -O2 -o build/dynedra-dwg-viewer.exe
build/dynedra-dwg-viewer.exe "C:\path\to\drawing.dwg"
```

The optional second viewer argument selects another reader executable. The
reader emits a bounded, versioned line-segment stream. The DynLex side checks
its header, counts, finite coordinates and bounds before drawing.

Generate and check a small real DWG file, including hidden-window GPU drawing:

```powershell
python -B tests/cadkernel/dwg_viewer/verify.py
```

The check runs the Rust reader and the DynLex test app at O0 and O2. It creates
`build/dynedra-dwg-sample.dwg` as a local test file. The font asset comes from
`tests/games/fonts/LiberationMono-Regular.ttf`; launch from the repository root.
