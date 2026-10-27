#!/usr/bin/env bash
# Sourced by build.sh. Local path data is read as text, never executed.
resolve_bim_toolchain() {
    local project_dir=$1 configured_root
    if [[ -n ${DYNLEX_ROOT:-} ]]; then
        configured_root=$DYNLEX_ROOT
    elif [[ -f "$project_dir/.dynlex-root.local" ]]; then
        IFS= read -r configured_root < "$project_dir/.dynlex-root.local" || [[ -n $configured_root ]]
    else
        echo "Set DYNLEX_ROOT or put the fork checkout path in $project_dir/.dynlex-root.local" >&2
        return 1
    fi
    if [[ -z $configured_root || $configured_root != /* ]]; then
        echo "DynLex checkout must be a nonempty absolute path" >&2
        return 1
    fi
    root=$(cd -- "$configured_root" && pwd -P) || return 1
    if [[ ! -x "$root/build/dynlex" || ! -d "$root/lib" ]]; then
        echo "DynLex checkout requires an executable build/dynlex and a lib directory: $root" >&2
        return 1
    fi
    bim_compiler=${BIM_DYNLEX_COMPILER:-$root/build/dynlex}
    if [[ $bim_compiler != /* || ! -x $bim_compiler ]]; then
        echo "BIM_DYNLEX_COMPILER must name an executable absolute path" >&2
        return 1
    fi
}
show_bim_toolchain() {
    printf 'DynLex checkout: %s\n' "$root"
    printf 'Compiler binary: %s\n' "$(readlink -f -- "$bim_compiler")"
    printf 'Library directory: %s\n' "$root/lib"
    printf 'Compiler SHA-256: '
    sha256sum -- "$bim_compiler"
    if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        printf 'Source HEAD: '
        git -C "$root" rev-parse HEAD
        echo 'Local compiler source changes:'
        git -C "$root" status --short -- src/cpp
    fi
    echo "Source HEAD does not prove which source produced the binary. No build was started."
}
