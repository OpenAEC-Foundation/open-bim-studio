#!/usr/bin/env bash
# Checks the import direction between the modules (module split design §4):
# a file may import its own module, the kernel, lib/, and modules of a lower
# layer; programs (ui/shell, tests) may import anything. The layers:
#   0 kernel   1 bim   2 services (viewer, exchange/*, ifc, views/*, materials,
#   localisation, automation, ui/editor)   3 elements/*, pattern/*
#   4 structural/*, architectural/*, mep/*   5 ui/properties   6 ui/panels
#   7 ui/shell
# The tree still carries edges from before the split (the editor framework
# importing element modules, services importing each other). Those are listed
# in scripts/layer-baseline.txt; this script fails only on an edge that is not
# in the baseline, so the count can go down but never up. Run with
# `--write-baseline` to record the current edges after removing some.
set -euo pipefail
cd "$(dirname "$0")/.."
layer_of() {
    case "$1" in
        kernel/*|lib/*) echo 0 ;;
        bim/*) echo 1 ;;
        viewer/*|exchange/*|ifc/*|views/*|materials/*|localisation/*|automation/*|ui/editor/*) echo 2 ;;
        elements/*|pattern/*) echo 3 ;;
        structural/*|architectural/*|mep/*) echo 4 ;;
        ui/properties/*) echo 5 ;;
        ui/panels/*) echo 6 ;;
        ui/shell/*|generated/*) echo 7 ;;
        *) echo 9 ;;
    esac
}
module_of() {
    case "$1" in
        kernel/*|lib/*) echo kernel ;;
        exchange/*|views/*|elements/*|pattern/*|structural/*|architectural/*|mep/*|ui/*) echo "${1%/*}" | cut -d/ -f1-2 ;;
        *) echo "${1%%/*}" ;;
    esac
}
edges=$(grep -rnoE '^import [^[:space:]]+' --include='*.dl' \
    --exclude-dir=tests --exclude-dir=reference --exclude-dir=docs --exclude-dir=build --exclude-dir=generated --exclude-dir=tools \
    bim viewer exchange ifc views materials localisation automation ui elements pattern structural architectural mep 2>/dev/null \
    | while IFS=: read -r file _ line; do
        target=${line#import }
        from_layer=$(layer_of "$file"); to_layer=$(layer_of "$target")
        from_module=$(module_of "$file"); to_module=$(module_of "$target")
        if [ "$from_layer" = 7 ]; then continue; fi
        if [ "$to_layer" -lt "$from_layer" ] || [ "$to_module" = "$from_module" ]; then continue; fi
        echo "$from_module -> $target"
    done | sort -u)
if [ "${1:-}" = "--write-baseline" ]; then
    printf '%s\n' "$edges" > scripts/layer-baseline.txt
    echo "baseline: $(printf '%s\n' "$edges" | grep -c .) edges"
    exit 0
fi
new=$(comm -23 <(printf '%s\n' "$edges") <(sort -u scripts/layer-baseline.txt 2>/dev/null))
if [ -n "$new" ]; then
    echo "import edges against the layer order that are not in scripts/layer-baseline.txt:"
    echo "$new"
    exit 1
fi
