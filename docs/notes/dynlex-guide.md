# DynLex in this repository: a working guide

DynLex is this project's own language, compiled by the fork named in
`.dynlex-root.local` or `DYNLEX_ROOT`. No assistant and few people know it from
elsewhere; what anyone can do with it comes from the compiler's documentation,
the standard library and the code in this tree. This note collects the parts
that matter for writing and reading code here. Read it at the start of a
session, then open the sources it points at when a detail matters.

Deeper sources, in the compiler checkout: `docs/stages.md` (how a program is
imported, matched, typed and generated), `docs/subject_and_chaining.md`,
`docs/named_compile_time_values.md`, `lib/std.dl`, `lib/string.dl`,
`lib/list.dl`. In this tree: `kernel/docs/` for the kernel's own conventions.

## 1. Programs, files, imports

- A program is one `.dl` file with top-level statements (`app/main.dl`, every
  `tests/*.dl`). Definitions live in imported files; a definition file has no
  top-level statements.
- `import model/bim_model.dl` at the top of a file. A path resolves against the
  importing file's directory, then its root, then the current directory, then
  the compiler's own source tree (where its `lib/` is). Compile from the
  repository root, as `build.sh` does, so `model/…` and `kernel/…` resolve. A
  `lib/x.dl` in this repository shadows the compiler's copy.
- The whole import closure is one compile unit. Patterns are resolved per
  program, not per file: a file may call a pattern that a file it does not
  import defines, as long as some file in the program imports the definition
  (measured 2026-10-28). Import cycles compile. Still import what you use, for
  readers and for `scripts/check-layers.sh`.
- `return`, `set`, `ignore`, `print … as a line` and the list patterns come from
  `lib/std.dl`; a file that uses them imports it (a definition-only library
  file compiled on its own found this out: without the import, `return 1` is
  "This pattern couldn't be resolved"). `the string form of "text"` and the
  other string patterns need `import lib/string.dl`; JSON needs `lib/json.dl`. When the compiler says
  "This pattern couldn't be resolved", check the imports and the closure before
  the spelling: the message is the same for a missing import, a typo and a
  type that matches no overload.
- One program compiles on one thread. Compile time grows faster than the
  closure's size, so a test imports only the files it needs. Use `-O0` while
  developing and `-O2` for releases.

## 2. Functions and patterns

A function is a sentence pattern with a body:

```dynlex
function the bim wall thickness of {bim wall record:wallValue} in {bim model record:modelValue}:
    execute:
        set found to the bim wall type index of wallValue's typeId in modelValue
        if found's valid = false:
            return 0.0
        return (the item at found's position in (modelValue's wallTypes's values))'s thickness
```

- `execute:` holds statements; `return value` leaves with a value, `return
  nothing` without one. `replacement:` holds one expression that replaces the
  call. A zero-argument `replacement` of a constant is the language's enum:
  `function bim wall tool:` with `replacement: 1`. Name such values; never
  repeat the number at call sites.
- Parameters are `{type:name}` or `{name}`. The type is a constraint:
  `integer` accepts every integer width, `a 64 bit integer` exactly one,
  `a 64 bit floating-point number`, `a number`, `boolean`, `a string`,
  `a pointer to a list`, `a pointer to a bim model record`, `cad vector2`,
  `the type of (an expression)`.
- The same words with different parameter types are overloads; the compiler
  picks by the arguments' types. Pattern words are literal. `[a|]` makes an
  article optional, `[word]` forces a word literal. Do not name a parameter
  like a literal word of the same pattern.
- A plain word in a pattern that the body uses becomes a parameter without a
  brace (implicit promotion). It surprises readers; write `{name}`.
- Functions are instantiated per use with the caller's types. A definition
  that nothing calls costs almost nothing; the instantiations are what compile
  time is made of. A library that exposes little generates little.
- `local function` is visible only in its own file: a module's helpers are
  `local`, its API is its public patterns. `exposed function` gets a C symbol
  for a separately compiled library (`--emit-object`); only scalars and
  pointers cross that seam. `flex function` expands in the caller's context;
  it belongs to the standard library, not to this tree.
- Actions produce nothing; values are nouns or predicates. A value may never
  be left unused: `set x to …` or `ignore …` a value you do not need. Two
  actions chain with `and`; an action may `set the subject to` a value that
  the next action reads as `it`.
- The compiler tries operand groupings until one types. When two do, it
  reports ambiguity; when its first guess fails deep inside, the message can
  name the wrong spot. Parentheses settle it:
  `the bim api elements of (editor's documentValue's current)`.

## 3. Values, records, lists

- Literals: `1` is an integer, `1 as a 64 bit integer` a sized one, `0.0` a
  floating-point number. An integer literal where a floating-point number is
  required is an error: write `.0`. `true`, `false`. Strings come from
  `the string form of "text"` and join with `+`; parenthesise the operands.
- Casts read `value as a pointer`, `count as a 32 bit unsigned integer`,
  `0 as a pointer to a cad pcurve allocation`.
- A record is a class:

```dynlex
class:
    patterns:
        [a|] bim level record
    members:
        id as a 64 bit integer
        name as a string
        height as a 64 bit floating-point number
```

  Construct it positionally, in member order, inside a constructor function:
  `@intrinsic("construct", a bim level record, id, name, 0.0)`. Read members
  with `value's name`, assign with `set value's name to x`. A parameter
  `{a pointer to a bim model record:target}` reads and writes through the
  pointer the same way; `the address of x` makes the pointer. A class may
  carry `retain:` and `release:` sections for its own lifecycle (reference
  counts in the kernel), using `@intrinsic("lifecycle value")`.
- Lists: `an empty list of a 64 bit integer`, `append x to values`,
  `the item at i in values`, `the length of values`,
  `insert x into values at index i`, `replace item at index i in values with x`,
  `remove item i from values`, `the last item of values`, `clear values`,
  `free values`. Lists are freed by hand; `free` the ones you own when done.
  Pass a list as `{a pointer to a list:values}`. The kernel's
  `cad topology list of X` (`kernel/core/topology_list.dl`) wraps a list with
  a reference count: `modelValue's walls's values` is the list,
  `the cad clone of modelValue's walls` copies it.
- Failure travels in result records, not exceptions: a `… result` class with
  `valid` and `value` (`cad body result`, `bim index result record`), or a
  status code. Check `valid` before `value`.

## 4. Control flow

```dynlex
if found's valid:
    …
else if slabFound's valid:
    …
else:
    …
loop cursor from 0 to the length of values:
    …
loop while (the length of ids) > kept:
    …
```

`loop … from a to b` stops before `b`. Comparisons are `=`, `!=`, `<`, `<=`,
`>`, `>=`; booleans combine with `and` and `or`, with parentheses around each
operand: `set continuing to (a = b) and (c >= d)`. The code writes
`x = false` more often than `not x`.

## 5. Native calls

`@intrinsic("call", "libc", "exit", nothing, 1)`: the library, the symbol, the
return type, then the arguments. Libraries used here: `libc`, `vulkan`,
`glfw`, `obs_platform` (the C shim in `platform/obs_platform.c`, the one place
for calls whose names differ per OS). `@intrinsic("variadic call", …)` for
`printf`-like symbols. `the function named "bim id ordering $ and $"` gives a
function's native address for a C callback such as a sort comparator. Wrap
every intrinsic in a plain-English function that says what it does, and never
let a native result fall on the floor.

## 6. Output and tests

- `print value as a line`; `print` alone adds no newline.
- A test is `tests/NAME.dl` with `tests/NAME.expected.txt`; `build.sh test NAME`
  compiles it at `-O0`, runs it and compares the output. The result lines are
  `PASS`, `FAIL` (output differs), `DIAG` (compile diagnostics) and
  `RUNTIME FAIL`. Output must be deterministic: no times, no addresses.
- Kernel fixtures are `kernel/tests/<name>/main.dl` with `expected.txt`, run by
  `kernel/tests/verify.py`; some expect diagnostics rather than output.
- The compiler emits warnings as diagnostics; a build with any diagnostic is
  a `DIAG`. "Repeated pattern word 'x' stays literal" means a word appears
  twice in one pattern definition; rename one.

## 7. Pitfalls met in this tree

| Symptom | Cause | Remedy |
|---|---|---|
| "This pattern couldn't be resolved" on a line that looks right | the definition is not in the program's closure, or it is `local` to another file, or no overload matches the argument types | add the import, make the helper public, or check the types |
| the same message on a string expression | `lib/string.dl` not imported | import it |
| "No overload matches call" on a nested `'s` chain | the grouping the compiler tried first | parentheses |
| a constructor compiles but values land in the wrong members | positional `construct` and the member order changed | regenerate or reorder; prefer one constructor function per record |
| an integer literal rejected | a floating-point number was required | write `.0` |
| a value left unused | an action-shaped call returned a value | `ignore` it or consume it |
| `stop_because_a_list_index_is_out_of_bounds` from `loop while (i < n) and ((the item at i in xs) < v)` | `and` and `or` evaluate both operands; nothing short-circuits (measured 2026-10-31) | guard the read with an `if`, or stop the loop by a flag |
| a test takes minutes to compile | its closure is most of the application | import less; model-level tests stay under 20k lines |
| diagnostics differ between Linux and Windows | path spellings in messages | compare on Linux; the fixture runner strips the checkout path |

## 8. Module rules

From `docs/superpowers/specs/2026-10-28-module-split-design.md`: a module's
records live in its `records.dl`, its stores are declared in its `MODULE`
manifest, and it implements an extension point by defining the point's pattern
with its own name as a literal word (`collect bim candidates of modelValue with
planar elements into candidates`). A module imports the layers below it and
never a sibling; it calls the generated dispatchers without importing
`generated/`. Helpers stay `local`.
