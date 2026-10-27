#!/usr/bin/env bash
# Finds references to the layouts before the restructuring of 2026-10-27 and
# before the module split of 2026-10-28 in
# sources, scripts, workflows, expectations and the current documents. The
# historical notes (docs/notes, docs/superpowers, docs/recovery, the decision
# record of the move, kernel/docs) and the kernel's reference material from the
# fork keep their old paths on purpose and are not scanned. Prints every hit
# and exits non-zero when there is one.
set -euo pipefail
cd "$(dirname "$0")/.."
pattern='spikes/dynlex-bim-slice|examples/bim-slice|lib/cadkernel|lib/fastkernel|lib/vulkan|tests/games/fonts|examples/gpu|tests/cadkernel|tests/required|import (model|formats|graphics|editor|app)/|app/(fonts|icons|main\.dl)|graphics/(shaders|vulkan|window_style)|formats/import|import tests/|"tests/(support|fixtures)/'
# tools/check_compiler_patterns.py reads the compiler checkout's own tests/required
# and belongs to the fork (design §7); this script names the pattern itself.
hits=$(grep -rnE "$pattern" \
    --include='*.dl' --include='*.py' --include='*.sh' --include='*.ps1' --include='*.yml' --include='*.md' --include='*.txt' --include='*.wxs' \
    --exclude-dir=reference --exclude-dir=docs --exclude-dir=notes \
    --exclude=check_compiler_patterns.py --exclude=check-old-paths.sh \
    kernel bim viewer exchange ifc views materials localisation automation ui elements pattern structural architectural mep platform tests tools installer scripts lib patches .github \
    README.md CLAUDE.md CONTRIBUTING.md docs/TWEE-COMPUTERS.md docs/risks.md docs/roadmap.md 2>/dev/null || true)
if [ -n "$hits" ]; then
    echo "$hits"
    exit 1
fi
