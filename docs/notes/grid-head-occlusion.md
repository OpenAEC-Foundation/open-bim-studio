# Grid-head occlusion candidates

Each visible grid endpoint keeps the existing exact mesh/opening/space picker
to determine whether geometry lies before its label. Camera motion previously
sent the entire shown scene to that picker for every endpoint.

`viewer/bim_ray_bounds.dl` builds world-space axis-aligned mesh bounds once.
The shell keys them by `shownMeshesKey`, so geometry regeneration, filtering,
isolation and clipping follow the same invalidation as the picking scene.
Camera motion queries those bounds without rebuilding them. Scenes without
grids do not allocate the bounds array.

An inclusive slab intersection, padded by 0.1 micrometres, retains candidate
meshes that the ray can reach before the label's existing 50 mm margin. The
unchanged exact picker receives those candidates and the complete model and
space list; opening precedence and room-floor semantics remain its concern.
Bounds never determine a final hit. A count mismatch or missing bounds falls
back to the full mesh list. Callers must rebuild after geometry changes even
when the number of meshes stays constant.

`ray_bounds` checks parallel, grazing, inside, behind, flat and finite rays,
then compares 208 exact picks near the origin and 500 km away, including rays
through windows, beneath sills and over rooms. It also compares finite-distance
occlusion decisions and verifies the missing-index fallback. `pick` and
`plan_inset` retain their existing editor checks.

```sh
./build.sh bundle ray_bounds pick plan_inset
```

This is a linear scan of cheap bounds followed by exact tests on candidates,
not a BVH. It does not yet accelerate the editor's general selection queries.
`OBS_PROFILE_FRAMES=1` adds `grid_heads_us` for the label stage, including a
bounds rebuild when one is needed. The measured mixed showcase rises from
2.26 to 43.05 FPS during the same
15-second input trajectory, with the initial fitted 3D pane pixel-identical.
The grid-head stage has p95 4.636 ms. See
[build provenance and limits](../research/native-component-rendering.md).
