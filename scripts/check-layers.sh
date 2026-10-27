#!/usr/bin/env bash
# Checks the import direction between the unit directories (design §5):
# kernel → kernel, lib; model → model, kernel, lib; formats and graphics →
# themselves, each other, model, kernel, lib; editor → editor, graphics,
# formats, model, kernel, lib and app (the editor-to-app edges the design
# leaves). app, automation, tests and tools may import anything. Prints every
# forbidden edge as `FILE: import PATH` and exits non-zero when there is one.
set -euo pipefail
cd "$(dirname "$0")/.."
allowed() {
    case "$1" in
        kernel) echo "kernel lib" ;;
        model) echo "model kernel lib" ;;
        formats) echo "formats graphics model kernel lib" ;;
        graphics) echo "graphics formats model kernel lib" ;;
        editor) echo "editor graphics formats model kernel lib app" ;;
    esac
}
status=0
for unit in kernel model formats graphics editor; do
    ok=$(allowed "$unit")
    while IFS=: read -r file _ line; do
        target=${line#import }
        top=${target%%/*}
        case " $ok " in
            *" $top "*) ;;
            *) echo "$file: $line"; status=1 ;;
        esac
    done < <(grep -rnoE '^import [^[:space:]]+' --include='*.dl' --exclude-dir=tests --exclude-dir=reference --exclude-dir=docs "$unit")
done
exit $status
