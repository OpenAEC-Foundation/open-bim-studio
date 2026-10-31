// Runs a DynLex program compiled with --emit-wasm under Node, on the browser host of the
// DynLex web IDE (memory, printf, the standard library's file and path calls) plus the
// C functions this repository calls that the IDE host lacks.
//
//   node platform/web/run.mjs DYNLEX_ROOT PROGRAM.wasm
//
// Standard output is the program's printed text; a summary line (module size, imports,
// instantiation and run time) goes to standard error. An import neither host provides is
// bound to a stub that fails when called, so a program runs until it reaches one.
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { performance } from "node:perf_hooks";

const [dynlexRoot, wasmPath] = process.argv.slice(2);
if (!dynlexRoot || !wasmPath) {
  console.error("usage: node platform/web/run.mjs DYNLEX_ROOT PROGRAM.wasm");
  process.exit(2);
}
const runtime = await import(
  pathToFileURL(`${dynlexRoot}/src/web/ide/public/compiler/runtimeImports.js`).href
);

// The C library beyond the IDE host: math.h, which the browser has as Math, and exit.
const unary = ["acos", "asin", "asinh", "atan", "ceil", "cos", "floor", "round", "sin", "sqrt", "tan"];
const extraImports = {
  atan2: (y, x) => Math.atan2(y, x),
  copysign: (x, y) => Math.sign(y) * Math.abs(x) * (Object.is(Math.sign(y), -0) ? -1 : 1),
  fmod: (x, y) => x % y,
  hypot: (x, y) => Math.hypot(x, y),
  nan: () => NaN,
  exit: (status) => {
    throw new ProgramExit(Number(status));
  }
};
for (const name of unary) {
  extraImports[name] = (value) => Math[name](value);
}
class ProgramExit extends Error {
  constructor(status) {
    super(`exit ${status}`);
    this.status = status;
  }
}

const bytes = await readFile(wasmPath);
const started = performance.now();
const module = await WebAssembly.compile(bytes);
const imports = WebAssembly.Module.imports(module);
const missing = [];
// The host pushes printed text onto the list it is given; write each piece as it comes.
const output = { push: (text) => process.stdout.write(text) };
const importsObject = runtime.buildRuntimeImports(
  imports,
  output,
  runtime.createRuntimeFilesystem(),
  runtime.inspectRuntimeWasmLayout(bytes)
);
const env = importsObject.env;
for (const spec of imports) {
  if (spec.module !== "env" || spec.name in env) continue;
  if (spec.name in extraImports) {
    env[spec.name] = extraImports[spec.name];
  } else if (spec.kind === "function") {
    missing.push(spec.name);
    env[spec.name] = () => {
      throw new Error(`unsupported import ${spec.name}`);
    };
  }
}
const instance = await WebAssembly.instantiate(module, importsObject);
const instantiated = performance.now();
let status = 0;
try {
  (instance.exports.main ?? instance.exports._start)();
} catch (error) {
  if (error instanceof ProgramExit) status = error.status;
  else {
    console.error(`run failed: ${error.message}`);
    status = 1;
  }
}
const finished = performance.now();
console.error(
  `wasm ${bytes.length} bytes, ${imports.length} imports` +
    (missing.length ? ` (stubbed: ${missing.join(" ")})` : "") +
    `, instantiate ${(instantiated - started).toFixed(1)} ms, run ${(finished - instantiated).toFixed(1)} ms`
);
process.exitCode = status;
