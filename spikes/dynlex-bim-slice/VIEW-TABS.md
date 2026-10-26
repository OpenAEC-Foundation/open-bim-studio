# View tabs

Tabs show the view name without redundant `Plan:`/`Schedule:` prefixes. Sheet
tabs use the sheet number; named 3D views retain their actual name. Labels fit
within 88–180 pixels, leaving a separate close target.

Use the arrows or the mouse wheel over the strip to reach overflow tabs.
Activating a tab reveals it. Hit testing and drag reordering use the same scrolled
positions as drawing. Pane captions are distinct from the clickable tab row.

Each plan tab keeps its view identity. Changing the storey focuses or opens the
corresponding plan instead of changing another tab's meaning. Opening a new
project clears the previous project's tabs. A tiled sheet remains a sheet when
the plan pane receives focus, so the pane caption matches its rendered content.

`workspace_tabs` passes 15 headless checks for identity-preserving reordering,
compact widths, overflow visibility, resizing/closing, and new-document reset.
Full app/visual verification of this checkpoint is pending; the current running
window has not been replaced.
