#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Reject application locals that DynLex may capture as implicit pattern arguments.

This narrow preflight is not a DynLex parser/type checker. Application function
parameters use explicit typed braces; an assignment to an otherwise unbound
word in the function's literal pattern is ambiguous. Check product modules,
not standard-library functions intentionally using implicit parameters.
"""
import re
import sys
from pathlib import Path


def collisions(text):
    words = set()
    active = False
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"(?:local )?function ", line):
            signature = re.sub(r"^(?:local )?function ", "", line)
            parameters = set(re.findall(r":([A-Za-z_][A-Za-z_0-9]*)}", signature))
            literals = re.sub(r"\{[^}]*\}", " ", signature)
            # [word]/[choices] and {literal:word} are explicit literals in
            # DynLex; the compiler never promotes them into parameters.
            while re.search(r"\[[^\[\]]*\]", literals):
                literals = re.sub(r"\[[^\[\]]*\]", " ", literals)
            words = set(re.findall(r"\b[A-Za-z_][A-Za-z_0-9]*\b", literals)) - parameters
            if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", signature.rstrip(":").strip()):
                words = set()  # A whole single-word spelling is always literal.
            active, seen = True, set()
        elif line and not line[0].isspace() and not line.startswith("#"):
            active = False
        if active:
            declaration = re.match(r"\s+(?:set (\w+) to|loop (\w+) from)", line)
            if declaration:
                name = next(value for value in declaration.groups() if value)
                if name in words and name not in seen:
                    seen.add(name)
                    yield number, name


def main(paths):
    failed = False
    for supplied in paths:
        path = Path(supplied)
        sources = sorted(path.glob("*.dl")) if path.is_dir() else [path]
        for source in sources:
            for number, name in collisions(source.read_text(encoding="utf-8")):
                print(f"{source}:{number}: local '{name}' also occurs in the function pattern; "
                      "rename the local or declare an intended parameter in typed braces", file=sys.stderr)
                failed = True
    return int(failed)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: check_dynlex_locals.py APPLICATION_DIRECTORY_OR_FILE [...]")
    sys.exit(main(sys.argv[1:]))
