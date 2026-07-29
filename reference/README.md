# Reference material

External specifications and the benchmark models every candidate is measured against.

## The benchmark set

**Fixed once, used by every evaluation.** Candidates measured on different models cannot be
compared, and the temptation to benchmark each one on whatever is convenient is strong.

Defined in [`../docs/research/kernels/README.md`](../docs/research/kernels/README.md):

### 1. A realistic IFC model
Representative complexity from an open test set — a real building, not a demo cube. It should
contain the things that break implementations: curved walls, complex roofs, nested components,
non-trivial property sets.

- **Source:** *to be chosen*
- **Element count:** *to be recorded*
- **Why this one:** *to be justified*

### 2. Synthetic scale tests
Generated models at 10k / 100k / 1M elements. Simple geometry — these measure scaling behaviour,
not geometric complexity.

The generator script belongs here, not the generated files. Reproducible beats committed.

### 3. A parametric change scenario
Move a wall; its openings, its junctions with adjoining walls, and every 2D view showing it must
follow.

This is the sharpest test in the set. It measures precisely what separates a viewer from a
modeller, and it is the one most likely to eliminate candidates.

- **Definition:** *to be written* — must be precise enough that every candidate is asked to do
  the same thing.

## Binaries

**Do not commit large model files.** See [`../.gitignore`](../.gitignore).

For each benchmark model record instead:
- Where to obtain it, with a URL
- Its licence
- A checksum, so everyone verifies they measured the same file
- Its characteristics: element count, schema version, notable features

A `models/` subdirectory is gitignored for local copies.

## Specifications

Reference documents worth keeping links to — IFC schema documentation, national standards, file
format specifications.

Prefer stable links over copies. Where a copy is necessary, check the licence first.
