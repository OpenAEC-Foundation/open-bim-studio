# Indexed native settings

Native settings remain the same `(elementId, code, value)` records and file
fields. The in-memory list is ordered by element ID, then integer code.
`the bim setting …` performs a binary lower-bound lookup. Range serialisation
starts at the same bound and stops at the end of that owner's range; enumerating
owners scans the ordered list once.

Use `set bim setting …` for document edits. It preserves the order and journals
one change as before. `restore bim setting …` preserves the order without
journaling, for file loading and isolated preview construction. Direct list
mutation must preserve the ordering invariant. Removing records preserves it.
Native file loading accepts old unsorted rows and normalises them; duplicate
keys retain their former first-readable-value semantics. Canonical output may
therefore reorder legacy setting rows without changing the effective values.

This matters for masonry: thousands of per-placement heights made repeated
missing-setting queries scan thousands of unrelated records during a frame.
The component-count-only benchmark did not expose that workload.

A headless `-O0` probe with 8,192 records performs 32,768 hit/miss lookups and
checks the same checksum. Across three process runs the median elapsed time,
including startup and construction, was 1.6387 seconds with linear lookup and
0.00713 seconds with the index, about 230 times faster. This is a lookup
measurement, not a renderer FPS result.

On the mixed native showcase, sequential desktop runs with the same RTX 5070
reduce API readiness from 78.927 to 31.000 seconds. Orbit remains about 2 FPS;
the lookup speedup must not be presented as an equivalent frame-rate gain.
See [the measured workload and build provenance](../research/native-component-rendering.md).

```sh
./build.sh probe setting_lookup
build/tools/setting_lookup
./build.sh bundle setting_index component_rise systems_showcase
./build.sh bundle system_types system_inspection
```

The regression covers unordered edits, missing keys, explicit zero, replacement,
removal, 64-bit owners, range reads, isolated cloned arrays, non-journaling
restoration, legacy duplicates and stable canonical file round trips. Preview
construction uses the same ordered restoration path on its own cloned list.
