/* Throwaway spike driver — R-01 (incremental evaluation) and P-10 (implementation disagreement).
 *
 * Measures, for web-ifc in Node.js, on one benchmark model from ../../reference/models/:
 *
 *   1. OpenModel time            parse into the loader's token tape
 *   2. LoadAllGeometry time      the whole-model batch path
 *   3. StreamAllMeshes time      the streaming path
 *   4. process peak RSS          a PROCESS peak, not a data size. One model per process
 *                                (--model is required) so the number is not inflated by a
 *                                previous model in the same process.
 *   5. per-element GetFlatMesh   timed separately for EVERY element with geometry, on a
 *                                model where nothing has been evaluated yet, so each number
 *                                is a first evaluation: median, p95, max, and how many fall
 *                                under the 16 ms and 100 ms thresholds R-01 is stated in.
 *   6. the R-01 edit test        translate one IfcWall's placement by 1 m through WriteLine,
 *                                then time GetFlatMesh(expressID) for that element alone,
 *                                and a full LoadAllGeometry re-run.
 *   7. the cache probes          whether an in-memory edit is visible in the geometry the
 *                                loader returns, before and after ResetCache(modelID) --
 *                                the only cache-invalidation call the API exposes -- and
 *                                what ResetCache costs.
 *   8. a per-GUID element table  GUID, IfcClass, triangles, vertices, signed volume, bbox -- consumed
 *                                by compare.py for the P-10 disagreement analysis
 *
 * Every timed operation opens a fresh model (OpenModel on a freshly read buffer) and closes
 * it afterwards, so no model or geometry object is reused across repeats. The element table
 * is built in a separate, untimed pass.
 *
 * Usage:  node webifc_driver.mjs --model NAME [--repeats N] [--collect-only]
 * Writes: results/webifc_<model>.json
 *         results/webifc_<model>_elements.csv
 *
 * --collect-only runs nothing but the untimed element-table pass (8) and rewrites the CSV,
 * leaving the JSON untouched. It exists so the element table can be regenerated without
 * re-measuring -- every timing in results/webifc_<model>.json would otherwise change, and
 * those numbers are quoted across the research notes. Nothing in the element table depends
 * on a timing, and nothing in the JSON depends on the CSV except the row counts, which this
 * pass does not change.
 */

import * as WebIFC from "web-ifc";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const RESULTS = path.join(HERE, "results");
const MODELS = {
  "AC20-FZK-Haus": path.join(REPO, "reference", "models", "AC20-FZK-Haus.ifc"),
  IFC_Schependomlaan: path.join(REPO, "reference", "models", "IFC_Schependomlaan.ifc"),
};

/* web-ifc's own defaults, ALL TWELVE of them, restated verbatim from CreateSettings() in
 * src/ts/web-ifc-api.ts at tag 0.77 (commit f26c4beef0a668ebdb180d2b95a94097a1e21cef,
 * lines 442-459). Passing them explicitly means the results file states the tolerances the
 * booleans actually ran with instead of leaving them implicit. Note that USE_FAST_BOOLS,
 * which older documentation mentions, does not exist in this version -- these named
 * TOLERANCE_* settings replaced it; `grep -rn USE_FAST_BOOLS src/` at that tag returns
 * nothing. */
const SETTINGS = {
  COORDINATE_TO_ORIGIN: false,
  CIRCLE_SEGMENTS: 12,
  TAPE_SIZE: 67108864,
  MEMORY_LIMIT: 2147483648,
  LINEWRITER_BUFFER: 10000,
  TOLERANCE_PLANE_INTERSECTION: 1.0e-4,
  TOLERANCE_PLANE_DEVIATION: 1.0e-4,
  TOLERANCE_BACK_DEVIATION_DISTANCE: 1.0e-4,
  TOLERANCE_INSIDE_OUTSIDE_PERIMETER: 1.0e-10,
  TOLERANCE_SCALAR_EQUALITY: 1.0e-4,
  PLANE_REFIT_ITERATIONS: 1,
  BOOLEAN_UNION_THRESHOLD: 150,
};

// The R-01 thresholds, quoted from docs/risks.md R-01 so the driver reports against them.
const R01_PASS_MS = 16.0;
const R01_FAIL_MS = 100.0;

const args = process.argv.slice(2);
const repeats = Number(argOf("--repeats") ?? 5);
const collectOnly = args.includes("--collect-only");
const modelName = argOf("--model");
if (!modelName || !MODELS[modelName]) {
  console.error(`--model is required, one of: ${Object.keys(MODELS).join(", ")}`);
  process.exit(2);
}

function argOf(flag) {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : undefined;
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function quantiles(ms) {
  const s = [...ms].sort((a, b) => a - b);
  if (!s.length) return {};
  const q = (p) => s[Math.min(s.length - 1, Math.max(0, Math.round(p * (s.length - 1))))];
  return {
    n: s.length,
    min_ms: s[0],
    median_ms: median(s),
    p90_ms: q(0.9),
    p95_ms: q(0.95),
    p99_ms: q(0.99),
    max_ms: s[s.length - 1],
    mean_ms: s.reduce((a, b) => a + b, 0) / s.length,
    total_ms: s.reduce((a, b) => a + b, 0),
  };
}

let peakRss = 0;
function sampleRss() {
  const r = process.memoryUsage().rss;
  if (r > peakRss) peakRss = r;
}
function peakRssMb() {
  return peakRss / (1024 * 1024);
}

function hardware() {
  let cpu = "";
  try {
    cpu = execFileSync(
      "powershell",
      ["-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
      { encoding: "utf8" }
    ).trim();
  } catch (e) {
    cpu = `<unavailable: ${e.message}>`;
  }
  return {
    cpu,
    ram_gb: Math.round(os.totalmem() / 1024 ** 3),
    logical_processors: os.cpus().length,
    os: `${os.type()} ${os.release()}`,
    node: process.version,
  };
}

/* Signed volume via the divergence theorem, identical formula to the Python driver's
 * so the two numbers are comparable: v = 1/6 * sum over triangles of dot(a, cross(b,c)).
 * The vertex buffer web-ifc hands back is a Float32Array interleaved as [x,y,z,nx,ny,nz]
 * (GetVertexArray reads HEAPF32; see the note in the results file about float32 output). */
function meshStats(verts, indices, m) {
  let vol = 0;
  let xmin = Infinity, ymin = Infinity, zmin = Infinity;
  let xmax = -Infinity, ymax = -Infinity, zmax = -Infinity;
  const px = (i) => m[0] * verts[i * 6] + m[4] * verts[i * 6 + 1] + m[8] * verts[i * 6 + 2] + m[12];
  const py = (i) => m[1] * verts[i * 6] + m[5] * verts[i * 6 + 1] + m[9] * verts[i * 6 + 2] + m[13];
  const pz = (i) => m[2] * verts[i * 6] + m[6] * verts[i * 6 + 1] + m[10] * verts[i * 6 + 2] + m[14];
  for (let i = 0; i < indices.length; i += 3) {
    const a = indices[i], b = indices[i + 1], c = indices[i + 2];
    const ax = px(a), ay = py(a), az = pz(a);
    const bx = px(b), by = py(b), bz = pz(b);
    const cx = px(c), cy = py(c), cz = pz(c);
    vol += ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx);
    for (const [x, y, z] of [[ax, ay, az], [bx, by, bz], [cx, cy, cz]]) {
      if (x < xmin) xmin = x; if (y < ymin) ymin = y; if (z < zmin) zmin = z;
      if (x > xmax) xmax = x; if (y > ymax) ymax = y; if (z > zmax) zmax = z;
    }
  }
  return { volume: vol / 6, triangles: indices.length / 3, vertices: verts.length / 6,
           bbox: [xmin, ymin, zmin, xmax, ymax, zmax] };
}

/* The vertex count is the sum over the placed geometries of a mesh, where each geometry's count
 * is its interleaved [x,y,z,nx,ny,nz] float array length divided by six. web-ifc does NOT weld
 * across the geometries of one flat mesh, so this counts a shared corner once per geometry --
 * the number is "vertices as delivered", not "distinct positions", and is therefore not
 * comparable with IfcOpenShell's welded vertex count element for element. */
function flatMeshStats(api, id, mesh) {
  let tris = 0;
  let verts = 0;
  let vol = 0;
  let bb = [Infinity, Infinity, Infinity, -Infinity, -Infinity, -Infinity];
  for (let gi = 0; gi < mesh.geometries.size(); gi++) {
    const placed = mesh.geometries.get(gi);
    const geom = api.GetGeometry(id, placed.geometryExpressID);
    const v = api.GetVertexArray(geom.GetVertexData(), geom.GetVertexDataSize());
    const ix = api.GetIndexArray(geom.GetIndexData(), geom.GetIndexDataSize());
    const st = meshStats(v, ix, placed.flatTransformation);
    tris += st.triangles;
    verts += st.vertices;
    vol += st.volume;
    bb = [Math.min(bb[0], st.bbox[0]), Math.min(bb[1], st.bbox[1]), Math.min(bb[2], st.bbox[2]),
          Math.max(bb[3], st.bbox[3]), Math.max(bb[4], st.bbox[4]), Math.max(bb[5], st.bbox[5])];
    geom.delete();
  }
  return { triangles: tris, vertices: verts, volume: vol,
           bbox: bb.map((x) => (Number.isFinite(x) ? x : 0)) };
}

async function newApi() {
  const api = new WebIFC.IfcAPI();
  await api.Init();
  return api;
}

function openFresh(api, file) {
  const buf = new Uint8Array(fs.readFileSync(file));
  return api.OpenModel(buf, { ...SETTINGS });
}

function lengthUnitsPerMetre(api, id) {
  // IfcUnitAssignment -> IfcSIUnit with UnitType LENGTHUNIT; prefix MILLI => 1000.
  const units = api.GetLineIDsWithType(id, WebIFC.IFCSIUNIT);
  for (let i = 0; i < units.size(); i++) {
    const u = api.GetLine(id, units.get(i), false, false);
    if (u.UnitType?.value === "LENGTHUNIT") {
      const p = u.Prefix?.value;
      if (p === "MILLI") return 1000;
      if (p === "CENTI") return 100;
      return 1;
    }
  }
  return 1;
}

/* Find an IfcWall (or IfcWallStandardCase) whose ObjectPlacement is an IfcLocalPlacement
 * with an IfcAxis2Placement3D, and return both its express id and the express id of the
 * IfcCartesianPoint that placement's Location points at. */
function findWall(api, id) {
  for (const typeName of ["IFCWALL", "IFCWALLSTANDARDCASE"]) {
    const t = WebIFC[typeName];
    if (t === undefined) continue;
    const ids = api.GetLineIDsWithType(id, t);
    for (let i = 0; i < ids.size(); i++) {
      const w = api.GetLine(id, ids.get(i), false, false);
      if (!w.Representation || !w.ObjectPlacement) continue;
      const lp = api.GetLine(id, w.ObjectPlacement.value, false, false);
      if (!lp.RelativePlacement) continue;
      const ax = api.GetLine(id, lp.RelativePlacement.value, false, false);
      if (!ax.Location) continue;
      return { wallID: ids.get(i), pointID: ax.Location.value, guid: w.GlobalId.value };
    }
  }
  return null;
}

/* The edit. web-ifc keeps REAL values as strings up to the JS boundary, exposed through
 * _internalValue / _representationValue (see the note in the results file), so the value is
 * parsed, incremented and written back through the typed GetLine/WriteLine path.
 * The GetRawLineData/WriteRawLineData path is NOT usable for this: on this version it turns
 * every REAL on the line into "nan" even on an unmodified round trip -- rawWriteProbe()
 * below measures exactly that, so the claim is not taken on trust. */
function editPointX(api, id, pointID, deltaRawUnits) {
  const line = api.GetLine(id, pointID, false, false);
  const oldX = Number(line.Coordinates[0]._internalValue);
  const newX = oldX + deltaRawUnits;
  line.Coordinates[0]._internalValue = String(newX);
  line.Coordinates[0]._representationValue = newX;
  api.WriteLine(id, line);
  return { oldX, newX };
}

/* ------------------------------------------------------------------ phases */

async function timeOpen(file, out) {
  const openTimes = [];
  for (let r = 0; r < repeats; r++) {
    const api = await newApi();
    const buf = new Uint8Array(fs.readFileSync(file));
    const t0 = performance.now();
    const id = api.OpenModel(buf, { ...SETTINGS });
    openTimes.push(performance.now() - t0);
    if (r === 0) {
      out.schema = api.GetModelSchema(id);
      out.total_lines = api.GetAllLines(id).size();
    }
    api.CloseModel(id);
    api.Dispose();
    sampleRss();
  }
  out.open_ms = openTimes;
  out.open_median_ms = median(openTimes);
  console.log(`   OpenModel median ${out.open_median_ms.toFixed(1)} ms`);
}

async function timeLoadAllGeometry(file, out) {
  const loadTimes = [];
  let n = 0;
  for (let r = 0; r < repeats; r++) {
    const api = await newApi();
    const id = openFresh(api, file);
    const t0 = performance.now();
    const meshes = api.LoadAllGeometry(id);
    n = meshes.size();
    loadTimes.push(performance.now() - t0);
    api.CloseModel(id);
    api.Dispose();
    sampleRss();
    console.log(`   LoadAllGeometry run ${r + 1}: ${loadTimes[r].toFixed(1)} ms (${n} meshes)`);
  }
  out.load_all_geometry_ms = loadTimes;
  out.load_all_geometry_median_ms = median(loadTimes);
  out.load_all_geometry_meshes = n;
}

async function timeStreamAllMeshes(file, out) {
  const streamTimes = [];
  let streamed = 0;
  for (let r = 0; r < repeats; r++) {
    const api = await newApi();
    const id = openFresh(api, file);
    let n = 0;
    const t0 = performance.now();
    api.StreamAllMeshes(id, () => { n++; });
    streamTimes.push(performance.now() - t0);
    streamed = n;
    api.CloseModel(id);
    api.Dispose();
    sampleRss();
  }
  out.stream_all_meshes_ms = streamTimes;
  out.stream_all_meshes_median_ms = median(streamTimes);
  out.stream_all_meshes_count = streamed;
  console.log(`   StreamAllMeshes median ${out.stream_all_meshes_median_ms.toFixed(1)} ms (${streamed} meshes)`);
}

/* The element table. A separate, UNTIMED pass: the volume function is plain JS and must
 * never sit inside a timed region. */
async function collectElements(file, name, out) {
  const api = await newApi();
  const id = openFresh(api, file);
  const meshes = api.LoadAllGeometry(id);
  const rows = [];
  const ids = [];
  for (let i = 0; i < meshes.size(); i++) {
    const mesh = meshes.get(i);
    const st = flatMeshStats(api, id, mesh);
    const line = api.GetLine(id, mesh.expressID, false, false);
    rows.push({
      guid: line?.GlobalId?.value ?? "",
      ifc_class: api.GetNameFromTypeCode(api.GetLineType(id, mesh.expressID)),
      express_id: mesh.expressID,
      triangles: st.triangles,
      vertices: st.vertices,
      volume: st.volume,
      bbox: st.bbox,
    });
    ids.push(mesh.expressID);
  }
  api.CloseModel(id);
  api.Dispose();

  const csv = ["guid,ifc_class,express_id,triangles,vertices,volume,xmin,ymin,zmin,xmax,ymax,zmax"];
  for (const r of rows) {
    csv.push([r.guid, r.ifc_class, r.express_id, r.triangles, r.vertices,
              fmt(r.volume), ...r.bbox.map(fmt)].join(","));
  }
  const p = path.join(RESULTS, `webifc_${name}_elements.csv`);
  fs.writeFileSync(p, csv.join("\n") + "\n");
  out.element_table = path.relative(HERE, p).replace(/\\/g, "/");
  out.element_table_rows = rows.length;
  out.element_table_rows_with_zero_triangles = rows.filter((r) => r.triangles === 0).length;
  console.log(`   collected ${rows.length} rows`);
  return ids;
}

function fmt(x) {
  if (!Number.isFinite(x)) return "0";
  return Number(x.toPrecision(9)).toString();
}

/* Per-element first evaluation: one freshly opened model on which nothing has been
 * evaluated, then GetFlatMesh() timed for every element in turn. Each call is therefore the
 * FIRST evaluation of that element. Note that web-ifc caches per geometry express id, not
 * per product, so an element whose representation was already built for an earlier element
 * (mapped items, repeated window types) is served from that cache and measures as cheap --
 * this is a property of the library, and it is why the distribution has a long tail rather
 * than being uniform. */
async function perElement(file, ids, out) {
  const api = await newApi();
  const id = openFresh(api, file);
  const times = [];
  const rows = [];
  for (const eid of ids) {
    const t0 = performance.now();
    const mesh = api.GetFlatMesh(id, eid);
    const dt = performance.now() - t0;
    times.push(dt);
    rows.push({ express_id: eid, ms: dt,
                ifc_class: api.GetNameFromTypeCode(api.GetLineType(id, eid)) });
  }
  api.CloseModel(id);
  api.Dispose();
  sampleRss();
  rows.sort((a, b) => b.ms - a.ms);
  const under16 = times.filter((t) => t < R01_PASS_MS).length;
  const under100 = times.filter((t) => t < R01_FAIL_MS).length;
  out.per_element = {
    method: "one fresh model, GetFlatMesh() timed once per element, in express-id order",
    elements_timed: times.length,
    distribution: quantiles(times),
    under_16ms: under16,
    under_16ms_fraction: times.length ? under16 / times.length : 0,
    under_100ms: under100,
    under_100ms_fraction: times.length ? under100 / times.length : 0,
    slowest_10: rows.slice(0, 10),
  };
  const d = out.per_element.distribution;
  console.log(`   per-element median ${d.median_ms.toFixed(3)} ms, p95 ${d.p95_ms.toFixed(2)} ms, ` +
              `max ${d.max_ms.toFixed(2)} ms; ${under16}/${times.length} under 16 ms`);
}

/* R-01 edit test. Each repeat opens its own model, so nothing is reused across repeats.
 *
 *  warm   GetFlatMesh(wall) -> edit -> GetFlatMesh(wall)           (what a naive caller does)
 *  reset  GetFlatMesh(wall) -> edit -> ResetCache -> GetFlatMesh(wall)
 *  cold   edit -> GetFlatMesh(wall) on a model where nothing was evaluated
 *  full   edit -> ResetCache -> LoadAllGeometry
 *
 * The bbox x of the wall is recorded for each, so a 1 m translation is visible as a 1.0
 * shift, and whether a measured time is a regeneration or a cache hit is decided by that
 * number rather than assumed. */
async function r01(file, out) {
  const warm = [], reset = [], cold = [], full = [], resetCall = [], reopen = [];
  let info = {};
  for (let r = 0; r < repeats; r++) {
    const api = await newApi();
    const id = openFresh(api, file);
    const w = findWall(api, id);
    if (!w) { api.CloseModel(id); api.Dispose(); out.r01 = { error: "no suitable IfcWall found" }; return null; }
    const scale = lengthUnitsPerMetre(api, id);

    const refStats = flatMeshStats(api, id, api.GetFlatMesh(id, w.wallID));
    const { oldX, newX } = editPointX(api, id, w.pointID, 1.0 * scale);
    const readBack = Number(api.GetLine(id, w.pointID, false, false).Coordinates[0]._internalValue);

    // (warm) re-request the element with the cache still populated
    let t0 = performance.now();
    const warmMesh = api.GetFlatMesh(id, w.wallID);
    warm.push(performance.now() - t0);
    const warmStats = flatMeshStats(api, id, warmMesh);

    // (reset) drop the cache, then re-request the same element.
    // ResetCache is the only cache-invalidation call the API exposes, but in the published
    // 0.0.77 build it throws, so the failure is recorded rather than assumed away.
    let resetStats = null;
    let resetError = null;
    try {
      t0 = performance.now();
      api.ResetCache(id);
      resetCall.push(performance.now() - t0);
      t0 = performance.now();
      const resetMesh = api.GetFlatMesh(id, w.wallID);
      reset.push(performance.now() - t0);
      resetStats = flatMeshStats(api, id, resetMesh);
    } catch (e) {
      resetError = `${e.constructor.name}: ${e.message}`;
    }

    // (full) a whole-model re-run on the edited model
    t0 = performance.now();
    const meshes = api.LoadAllGeometry(id);
    const n = meshes.size();
    full.push(performance.now() - t0);
    api.CloseModel(id);

    // (cold) the same edit on a model where nothing has been evaluated yet
    const id2 = openFresh(api, file);
    editPointX(api, id2, w.pointID, 1.0 * scale);
    t0 = performance.now();
    const coldMesh = api.GetFlatMesh(id2, w.wallID);
    cold.push(performance.now() - t0);
    const coldStats = flatMeshStats(api, id2, coldMesh);
    api.CloseModel(id2);

    // (reopen) with ResetCache unusable, the only route from an edit to updated geometry
    // is to discard the model and open it again. Timed end to end: OpenModel on the same
    // bytes, apply the edit, then GetFlatMesh for the one element.
    const buf = new Uint8Array(fs.readFileSync(file));
    t0 = performance.now();
    const id3 = api.OpenModel(buf, { ...SETTINGS });
    editPointX(api, id3, w.pointID, 1.0 * scale);
    const reopenMesh = api.GetFlatMesh(id3, w.wallID);
    reopen.push(performance.now() - t0);
    const reopenStats = flatMeshStats(api, id3, reopenMesh);
    api.CloseModel(id3);
    api.Dispose();
    sampleRss();

    info = {
      reset_cache_error: resetError,
      reset_shift: resetStats ? resetStats.bbox[0] - refStats.bbox[0] : null,
      reopen_shift: reopenStats.bbox[0] - refStats.bbox[0],
      global_id: w.guid,
      express_id: w.wallID,
      placement_point_express_id: w.pointID,
      length_units_per_metre: scale,
      old_x: oldX,
      new_x: newX,
      read_back_x: readBack,
      write_took_effect_in_the_model: readBack === newX,
      expected_shift_m: 1.0,
      ref_xmin: refStats.bbox[0],
      warm_shift: warmStats.bbox[0] - refStats.bbox[0],
      cold_shift: coldStats.bbox[0] - refStats.bbox[0],
      triangles_ref: refStats.triangles,
      full_reiteration_meshes: n,
    };
  }
  out.r01 = {
    element: info,
    single_element_warm_ms: warm,
    single_element_warm_median_ms: median(warm),
    reset_cache_call_ms: resetCall,
    reset_cache_call_median_ms: resetCall.length ? median(resetCall) : null,
    single_element_after_reset_ms: reset,
    single_element_after_reset_median_ms: reset.length ? median(reset) : null,
    single_element_cold_ms: cold,
    single_element_cold_median_ms: median(cold),
    reopen_and_single_element_ms: reopen,
    reopen_and_single_element_median_ms: median(reopen),
    full_reiteration_ms: full,
    full_reiteration_median_ms: median(full),
    ratio_full_over_cold_single: median(full) / median(cold),
    note: "warm is a cache hit -- its shift is 0, so it is not a re-evaluation. With " +
          "ResetCache unusable in this build, the only route from an edit to updated " +
          "geometry is reopen_and_single_element, which re-parses the whole file.",
  };
  console.log(`   R-01 warm ${median(warm).toFixed(3)} ms (shift ${info.warm_shift}), ` +
              `cold ${median(cold).toFixed(3)} ms (shift ${info.cold_shift}), ` +
              `reopen ${median(reopen).toFixed(1)} ms (shift ${info.reopen_shift}), ` +
              `full ${median(full).toFixed(1)} ms; ResetCache: ${info.reset_cache_error ?? "ok"}`);
  return info;
}

/* A separate, self-contained probe: does the raw read/write pair round-trip a REAL?
 * Three cases on a freshly opened model, each on its own model instance:
 *   A  GetRawLineData -> WriteRawLineData with NOTHING changed
 *   B  the same, with one coordinate replaced by a JS number
 *   C  the typed GetLine -> WriteLine path with one coordinate changed
 * Returns what GetRawLineData / GetLine reports afterwards in each case. */
async function rawWriteProbe(file, expressID) {
  const buf = new Uint8Array(fs.readFileSync(file));
  const out = {};
  const api = await newApi();

  let id = api.OpenModel(buf.slice(), { ...SETTINGS });
  out.before = api.GetRawLineData(id, expressID).arguments[0].map((a) => a.value);
  const raw = api.GetRawLineData(id, expressID);
  api.WriteRawLineData(id, raw);
  out.A_unmodified_raw_roundtrip = api.GetRawLineData(id, expressID).arguments[0].map((a) => a.value);
  api.CloseModel(id);

  id = api.OpenModel(buf.slice(), { ...SETTINGS });
  const raw2 = api.GetRawLineData(id, expressID);
  raw2.arguments[0][0] = { type: 4, value: 8.41 };
  api.WriteRawLineData(id, raw2);
  out.B_numeric_raw_write = api.GetRawLineData(id, expressID).arguments[0].map((a) => a.value);
  api.CloseModel(id);

  id = api.OpenModel(buf.slice(), { ...SETTINGS });
  const line = api.GetLine(id, expressID, false, false);
  line.Coordinates[0]._internalValue = "8.41";
  line.Coordinates[0]._representationValue = 8.41;
  api.WriteLine(id, line);
  out.C_typed_writeline = api
    .GetLine(id, expressID, false, false)
    .Coordinates.map((c) => c._internalValue);
  api.CloseModel(id);

  api.Dispose();
  out.rule = "each case on its own freshly opened model; values as GetRawLineData/GetLine " +
             "report them afterwards";
  return out;
}

/* Is the only cache-invalidation call in the API reachable at all in this build?
 *
 * IfcAPI.ResetCache(modelID) is declared in src/ts/web-ifc-api.ts and forwards to
 * this.wasmModule.ResetCache. The C++ function exists (src/cpp/wasm/web-ifc-wasm.cpp,
 * `void ResetCache(uint32_t modelID)`), but this probe checks whether the compiled module
 * actually exports it, and what happens when it is called. Also records the model-wide
 * scope of the call as declared in the source, and -- if the call does work -- whether an
 * unrelated, unedited element is invalidated along with the edited one. */
async function resetCacheProbe(file, wallID, pointID, scale, otherID) {
  const api = await newApi();
  const id = openFresh(api, file);
  const out = {
    ifcapi_has_ResetCache: typeof api.ResetCache === "function",
    wasm_module_exports_ResetCache: typeof api.wasmModule?.ResetCache === "function",
    wall_express_id: wallID,
    other_express_id: otherID,
  };

  let t0 = performance.now();
  api.GetFlatMesh(id, wallID);
  out.wall_first_ms = performance.now() - t0;
  t0 = performance.now();
  api.GetFlatMesh(id, otherID);
  out.other_first_ms = performance.now() - t0;
  t0 = performance.now();
  api.GetFlatMesh(id, otherID);
  out.other_second_cached_ms = performance.now() - t0;

  editPointX(api, id, pointID, 1.0 * scale);
  try {
    api.ResetCache(id);
    out.reset_cache_call = "returned without throwing";
    t0 = performance.now();
    api.GetFlatMesh(id, otherID);
    out.other_after_reset_ms = performance.now() - t0;
  } catch (e) {
    out.reset_cache_call = `threw ${e.constructor.name}: ${e.message}`;
    out.other_after_reset_ms = null;
  }
  api.CloseModel(id);
  api.Dispose();
  out.rule = "the unrelated element was never edited; if other_after_reset_ms is close to " +
             "other_first_ms rather than other_second_cached_ms, ResetCache dropped it too";
  return out;
}

/* ------------------------------------------------------------------ main */

async function main() {
  fs.mkdirSync(RESULTS, { recursive: true });

  if (collectOnly) {
    const only = {};
    await collectElements(MODELS[modelName], modelName, only);
    console.log(`collect-only: rewrote results/webifc_${modelName}_elements.csv ` +
                `(${only.element_table_rows} rows); JSON left untouched`);
    return;
  }

  const probe = await newApi();
  const file = MODELS[modelName];
  const out = {
    driver: "webifc_driver.mjs",
    model: modelName,
    hardware: hardware(),
    versions: {
      web_ifc_npm: JSON.parse(fs.readFileSync(path.join(HERE, "node_modules", "web-ifc", "package.json"), "utf8")).version,
      node: process.version,
      web_ifc_reported: probe.GetVersion ? probe.GetVersion() : "<no GetVersion>",
    },
    settings: SETTINGS,
    repeats,
    r01_thresholds_ms: { pass_under: R01_PASS_MS, fail_over: R01_FAIL_MS },
    api_has_reset_cache: typeof probe.ResetCache === "function",
  };
  probe.Dispose();

  console.log(`== ${modelName}`);
  const m = {
    path: path.relative(REPO, file).replace(/\\/g, "/"),
    size_bytes: fs.statSync(file).size,
  };

  await timeOpen(file, m);
  await timeLoadAllGeometry(file, m);
  await timeStreamAllMeshes(file, m);
  const ids = await collectElements(file, modelName, m);
  await perElement(file, ids, m);
  const wall = await r01(file, m);
  if (wall) {
    m.raw_write_probe = await rawWriteProbe(file, wall.placement_point_express_id);
    const other = ids.find((x) => x !== wall.express_id);
    m.reset_cache_probe = await resetCacheProbe(
      file, wall.express_id, wall.placement_point_express_id,
      wall.length_units_per_metre, other);
    console.log(`   ResetCache probe: IfcAPI has it ${m.reset_cache_probe.ifcapi_has_ResetCache}, ` +
                `wasm exports it ${m.reset_cache_probe.wasm_module_exports_ResetCache}; ` +
                `call ${m.reset_cache_probe.reset_cache_call}`);
  }

  m.process_peak_rss_mb = peakRssMb();
  out.result = m;
  fs.writeFileSync(path.join(RESULTS, `webifc_${modelName}.json`),
                   JSON.stringify(out, null, 2) + "\n");
  console.log(`wrote results/webifc_${modelName}.json`);
}

await main();
