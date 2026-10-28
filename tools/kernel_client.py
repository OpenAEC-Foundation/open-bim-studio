"""Writes the client of the kernel library: for every `exposed function` in the
library's entry file, a function with the same pattern and parameter types
whose body calls the function's C symbol in the library "obskernel". The
symbol is the compiler's (codegen/codegenTypes.cpp getPatternFunctionName and
codegen/callableCodegen.inl buildCallableFunctionName):

  pattern text, every character that is not alphanumeric or '_' replaced by
  '_' for a space and by (code % 10) as a digit otherwise ('{' 3, ':' 8,
  '}' 5, '-' 5), then "_callable", then for each parameter "_" and the type's
  compiler spelling with every non-alphanumeric character as "_XX_" (hex):
  integer i32, a 64 bit integer i64, a 32 bit unsigned integer u32, boolean
  bool, a 64 bit floating-point number f64, pointer i8*, a pointer to X: X's
  spelling plus '*' (a class by its first pattern name: cad mesh*).

A comment line `# returns: <type>` directly above an exposed function gives
the wrapper's return type; without it the function returns nothing. A
mismatch between this file and the compiler fails at link time, never at run
time. Usage: kernel_client.py [--exposed kernel/api/exposed.dl] [--out kernel/api/client.dl]
"""
import argparse
import pathlib
import re
import sys

HEADER = [
    "# Written by tools/kernel_client.py from the library's exposed functions; do not edit.",
    "# Each function has the exposed function's pattern and types and calls its C",
    "# symbol in the library \"obskernel\"; a mangling mismatch fails at link time.",
    "import lib/std.dl",
    "import kernel/api/types.dl",
]
SCALARS = {
    "integer": "i32", "an integer": "i32", "a 32 bit integer": "i32",
    "a 64 bit integer": "i64", "a 16 bit integer": "i16", "an 8 bit integer": "i8",
    "a 32 bit unsigned integer": "u32", "a 64 bit unsigned integer": "u64",
    "a 16 bit unsigned integer": "u16", "an 8 bit unsigned integer": "u8",
    "boolean": "bool", "a boolean": "bool",
    "a 64 bit floating-point number": "f64", "a 32 bit floating-point number": "f32",
    "pointer": "i8*", "a pointer": "i8*",
}
PARAMETER = re.compile(r"\{([^{}:]+):([^{}]+)\}")


class ClientError(Exception):
    pass


def compiler_spelling(type_text):
    """DataType::toString for the types an exposed parameter may have."""
    text = " ".join(type_text.split())
    if text in SCALARS:
        return SCALARS[text]
    for prefix in ("a pointer to ", "pointer to "):
        if text.startswith(prefix):
            return compiler_spelling(text[len(prefix):]) + "*"
    # A class, named by its first pattern without the article.
    for article in ("an ", "a ", "the "):
        if text.startswith(article):
            return text[len(article):]
    return text


def pattern_name(pattern):
    out = []
    for character in pattern:
        if character.isalnum() or character == "_":
            out.append(character)
        elif character == " ":
            out.append("_")
        else:
            out.append(str(ord(character) % 10))
    return "".join(out)


def encode_component(value):
    out = []
    for character in value:
        if character.isalnum():
            out.append(character)
        else:
            out.append("_%02x_" % ord(character))
    return "".join(out)


def symbol_of(pattern):
    name = pattern_name(pattern) + "_callable"
    for type_text, _ in PARAMETER.findall(pattern):
        name += "_" + encode_component(compiler_spelling(type_text))
    return name


def exposed_functions(text):
    """Yields (pattern, return type or None) for every exposed function."""
    returns = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# returns:"):
            returns = stripped[len("# returns:"):].strip()
            continue
        if line.startswith("exposed function "):
            pattern = line[len("exposed function "):].rstrip()
            if not pattern.endswith(":"):
                raise ClientError(f"exposed function without a colon: {line!r}")
            yield pattern[:-1], returns
            returns = None
            continue
        if stripped and not stripped.startswith("#"):
            returns = None


def client_text(exposed):
    lines = list(HEADER)
    for pattern, returns in exposed_functions(exposed):
        names = [name.strip() for _, name in PARAMETER.findall(pattern)]
        call = ", ".join(['@intrinsic("call"', '"obskernel"', f'"{symbol_of(pattern)}"', returns or "nothing"] + names) + ")"
        lines += ["", f"function {pattern}:", "    execute:"]
        lines.append(f"        return {call}" if returns else f"        {call}")
    return "\n".join(lines) + "\n"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--exposed", default="kernel/api/exposed.dl")
    parser.add_argument("--out", default="kernel/api/client.dl")
    parser.add_argument("--check", action="store_true", help="exit 1 when the client on disk differs from what would be written")
    args = parser.parse_args(argv)
    exposed = pathlib.Path(args.exposed).read_text(encoding="utf-8")
    try:
        text = client_text(exposed)
    except ClientError as error:
        print(f"kernel_client: {error}", file=sys.stderr)
        return 1
    out = pathlib.Path(args.out)
    if args.check:
        current = out.read_text(encoding="utf-8").replace("\r\n", "\n") if out.exists() else ""
        if current != text:
            print(f"kernel_client: {out} is not current; run tools/kernel_client.py", file=sys.stderr)
            return 1
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
