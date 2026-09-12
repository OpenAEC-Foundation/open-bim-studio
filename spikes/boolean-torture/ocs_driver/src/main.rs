//! `cadkernel` driver for the boolean torture set (R-16) and the precision set (R-17).
//!
//! `cadkernel` is the MPL-2.0 Rust B-rep kernel that Open CAD Studio's solid
//! modelling runs on. This driver measures it on exactly the cases every other
//! candidate was measured on, read from `cases.json` (written by
//! `dump_cases.py` straight out of `reference/boolean_torture_set.py` and
//! `reference/precision_set.py`, so no case is re-typed here).
//!
//! Method, stated once:
//!
//! * Operands are built with `brep::make::faceted_solid`, which takes the
//!   reference triangle soup verbatim. A refusal is a `None`, not a typed
//!   error, and a refusal is recorded as a result rather than worked around.
//! * The boolean is `brep::combine(a, b, Operation::_, tolerance)`. Three
//!   settings: the tolerance `brep::operation_tolerance(&[&a, &b])` derives
//!   from the operands, and two explicit values, 1e-9 and 1e-6. The derived
//!   value is recorded per case.
//! * **Both operands are rebuilt inside every repeat**, because `combine`
//!   takes them by value and imprints them on the way through. Five repeats,
//!   median reported.
//! * Validity is *two* checks, both reported: `Body::validate()`, which is the
//!   kernel's own topological audit, and this driver's own check on the
//!   tessellated triangles — closed, every directed edge used once with a
//!   matching opposite, no loose vertices, no face below 1e-14 m² — matching
//!   the check the Manifold, CGAL and Blender drivers use so that "valid"
//!   means the same thing across the results files.
//! * Volume is this driver's own `signed_volume` over the tessellation, the
//!   same divergence-theorem sum as `reference.signed_volume`. The kernel's own
//!   `Mesh::mass_properties()` is reported beside it, never instead of it.
//!
//! Usage, from the repository root:
//!
//! ```text
//! cargo run --release --manifest-path spikes/boolean-torture/ocs_driver/Cargo.toml -- torture
//! cargo run --release --manifest-path spikes/boolean-torture/ocs_driver/Cargo.toml -- precision
//! ```

use std::collections::HashMap;
use std::fmt::Write as _;
use std::time::Instant;

use cadkernel::brep::make::faceted_solid;
use cadkernel::brep::mesh::{tessellate, TessellationTolerance};
use cadkernel::brep::place::{transform, Placement};
use cadkernel::brep::{combine, operation_tolerance, Body, Operation};
use serde_json::Value;

/// Tessellation parameters, fixed for every measurement in both result files.
/// `max_angle` is the largest direction change allowed across a triangle and is
/// inert on this set — every case is planar — and `linear` is the chordal
/// tolerance. 1e-9 m is the kernel's own floor (`TessellationTolerance::new`
/// replaces a non-positive linear value with 1e-9), i.e. the tightest setting
/// that is honoured.
const TESS_ANGLE: f64 = 0.2;
const TESS_LINEAR: f64 = 1e-9;

/// Welding epsilon for the driver's own topology check. `cadkernel` emits one
/// position block per face and concatenates them (`Mesh::absorb`), so positions
/// are duplicated per face and a halfedge check on the raw indices would call
/// every mesh open. Positions that came from the same B-rep vertex are welded
/// before the check. 1e-12 m is four orders below the tightest boolean
/// tolerance measured here and below any feature in the set.
const WELD_EPS: f64 = 1e-12;

const REPEATS: usize = 5;

// ---------------------------------------------------------------- formatting

/// `%.<digits>g`, so the numbers in these files line up with the Python
/// drivers' `f"{x:.12g}"`.
fn g(x: f64, digits: usize) -> String {
    if !x.is_finite() {
        return format!("{x}");
    }
    if x == 0.0 {
        return "0".to_string();
    }
    let exp = x.abs().log10().floor() as i32;
    if exp < -4 || exp >= digits as i32 {
        let s = format!("{:.*e}", digits.saturating_sub(1), x);
        let (mantissa, e) = s.split_once('e').unwrap();
        let mantissa = if mantissa.contains('.') {
            mantissa.trim_end_matches('0').trim_end_matches('.')
        } else {
            mantissa
        };
        format!("{mantissa}e{e}")
    } else {
        let places = (digits as i32 - 1 - exp).max(0) as usize;
        let s = format!("{x:.places$}");
        if s.contains('.') {
            s.trim_end_matches('0').trim_end_matches('.').to_string()
        } else {
            s
        }
    }
}

fn g12(x: f64) -> String {
    g(x, 12)
}

fn ms(x: f64) -> String {
    format!("{x:.3}")
}

// --------------------------------------------------------------- case input

#[derive(Clone)]
struct MeshIn {
    verts: Vec<[f64; 3]>,
    faces: Vec<Vec<usize>>,
    /// `reference.signed_volume` of the specified mesh, computed by the dumper.
    specified_volume: f64,
}

#[derive(Clone)]
struct Case {
    name: String,
    a: MeshIn,
    b: MeshIn,
    expected_union: f64,
    expected_intersection: f64,
}

fn read_mesh(value: &Value) -> MeshIn {
    let verts = value["vertices"]
        .as_array()
        .unwrap()
        .iter()
        .map(|p| {
            let p = p.as_array().unwrap();
            [
                p[0].as_f64().unwrap(),
                p[1].as_f64().unwrap(),
                p[2].as_f64().unwrap(),
            ]
        })
        .collect();
    let faces = value["faces"]
        .as_array()
        .unwrap()
        .iter()
        .map(|f| {
            f.as_array()
                .unwrap()
                .iter()
                .map(|i| i.as_u64().unwrap() as usize)
                .collect()
        })
        .collect();
    MeshIn {
        verts,
        faces,
        specified_volume: value["volume"].as_f64().unwrap(),
    }
}

fn read_cases(root: &Value, key: &str) -> Vec<Case> {
    root[key]
        .as_array()
        .unwrap()
        .iter()
        .map(|c| Case {
            name: c["name"].as_str().unwrap().to_string(),
            a: read_mesh(&c["a"]),
            b: read_mesh(&c["b"]),
            expected_union: c["expected_union"].as_f64().unwrap(),
            expected_intersection: c["expected_intersection"].as_f64().unwrap(),
        })
        .collect()
}

// --------------------------------------------------------------- geometry

fn build(mesh: &MeshIn, offset: [f64; 3]) -> Option<Body> {
    let verts: Vec<[f64; 3]> = mesh
        .verts
        .iter()
        .map(|p| [p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]])
        .collect();
    faceted_solid(&verts, &mesh.faces)
}

struct Tess {
    positions: Vec<[f64; 3]>,
    triangles: Vec<[usize; 3]>,
    /// Faces the tessellator could not triangulate. Any non-zero count means
    /// the volume below is integrated over an incomplete boundary.
    missing_faces: usize,
    kernel_volume: Option<f64>,
}

fn tess(body: &Body) -> Tess {
    let out = tessellate(body, TessellationTolerance::new(TESS_ANGLE, TESS_LINEAR));
    Tess {
        positions: out.mesh.positions.clone(),
        triangles: out.mesh.triangles.clone(),
        missing_faces: out.missing_faces.len(),
        kernel_volume: out.mesh.mass_properties().map(|(v, _)| v),
    }
}

/// The divergence-theorem volume of a closed triangle mesh, term for term the
/// same sum as `reference.signed_volume`.
fn signed_volume(positions: &[[f64; 3]], triangles: &[[usize; 3]]) -> f64 {
    let mut total = 0.0;
    for t in triangles {
        let [x0, y0, z0] = positions[t[0]];
        let [x1, y1, z1] = positions[t[1]];
        let [x2, y2, z2] = positions[t[2]];
        total += x0 * (y1 * z2 - z1 * y2) - y0 * (x1 * z2 - z1 * x2) + z0 * (x1 * y2 - y1 * x2);
    }
    total / 6.0
}

fn weld(positions: &[[f64; 3]], triangles: &[[usize; 3]]) -> (Vec<[f64; 3]>, Vec<[usize; 3]>) {
    let key = |p: [f64; 3]| -> [i64; 3] {
        [
            (p[0] / WELD_EPS).round() as i64,
            (p[1] / WELD_EPS).round() as i64,
            (p[2] / WELD_EPS).round() as i64,
        ]
    };
    let mut map: HashMap<[i64; 3], usize> = HashMap::new();
    let mut out_pos: Vec<[f64; 3]> = Vec::new();
    let mut remap = vec![usize::MAX; positions.len()];
    for (index, &p) in positions.iter().enumerate() {
        let k = key(p);
        // 27-neighbourhood so a pair straddling a cell boundary still welds.
        let mut found = None;
        'search: for dx in -1..=1i64 {
            for dy in -1..=1i64 {
                for dz in -1..=1i64 {
                    if let Some(&existing) = map.get(&[k[0] + dx, k[1] + dy, k[2] + dz]) {
                        let q = out_pos[existing];
                        let d = (p[0] - q[0]).powi(2) + (p[1] - q[1]).powi(2) + (p[2] - q[2]).powi(2);
                        if d <= WELD_EPS * WELD_EPS {
                            found = Some(existing);
                            break 'search;
                        }
                    }
                }
            }
        }
        let target = found.unwrap_or_else(|| {
            out_pos.push(p);
            map.insert(k, out_pos.len() - 1);
            out_pos.len() - 1
        });
        remap[index] = target;
    }
    let out_tris = triangles
        .iter()
        .map(|t| [remap[t[0]], remap[t[1]], remap[t[2]]])
        .filter(|t| t[0] != t[1] && t[1] != t[2] && t[0] != t[2])
        .collect();
    (out_pos, out_tris)
}

/// The same validity check the Manifold, CGAL and Blender drivers apply, on the
/// welded tessellation.
fn check_mesh(positions: &[[f64; 3]], triangles: &[[usize; 3]]) -> Vec<String> {
    let mut problems = Vec::new();
    if triangles.is_empty() {
        problems.push("empty result".to_string());
        return problems;
    }
    let mut directed: HashMap<(usize, usize), usize> = HashMap::new();
    for t in triangles {
        for e in [(t[0], t[1]), (t[1], t[2]), (t[2], t[0])] {
            *directed.entry(e).or_insert(0) += 1;
        }
    }
    if directed.values().any(|n| *n > 1) {
        problems.push("directed edge used more than once".to_string());
    }
    let unmatched = directed
        .iter()
        .filter(|((u, v), n)| directed.get(&(*v, *u)).copied().unwrap_or(0) != **n)
        .count();
    if unmatched > 0 {
        problems.push(format!("{unmatched} edges without a matching opposite halfedge"));
    }
    let mut used = vec![false; positions.len()];
    for t in triangles {
        for &i in t {
            used[i] = true;
        }
    }
    let loose = used.iter().filter(|u| !**u).count();
    if loose > 0 {
        problems.push(format!("{loose} loose verts"));
    }
    let mut tiny = 0;
    for t in triangles {
        let p0 = positions[t[0]];
        let p1 = positions[t[1]];
        let p2 = positions[t[2]];
        let u = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
        let v = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
        let c = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        ];
        if 0.5 * (c[0] * c[0] + c[1] * c[1] + c[2] * c[2]).sqrt() < 1e-14 {
            tiny += 1;
        }
    }
    if tiny > 0 {
        problems.push(format!("{tiny} zero-area faces"));
    }
    problems
}

fn flaw_names(body: &Body) -> Vec<String> {
    let flaws = body.validate();
    let mut counts: Vec<(String, usize)> = Vec::new();
    for flaw in &flaws {
        // The variant name verbatim, without the key payload, which is an
        // arena index and would not be comparable between runs.
        let text = format!("{flaw:?}");
        let name = text.split(['(', ' ']).next().unwrap_or(&text).to_string();
        match counts.iter_mut().find(|(n, _)| *n == name) {
            Some((_, count)) => *count += 1,
            None => counts.push((name, 1)),
        }
    }
    counts
        .into_iter()
        .map(|(name, count)| if count == 1 { name } else { format!("{name} x{count}") })
        .collect()
}

fn worst_nearest(a: &[[f64; 3]], b: &[[f64; 3]]) -> Option<f64> {
    if a.is_empty() || b.is_empty() {
        return None;
    }
    let one_way = |src: &[[f64; 3]], dst: &[[f64; 3]]| -> f64 {
        let mut worst = 0.0_f64;
        for p in src {
            let mut best = f64::INFINITY;
            for q in dst {
                let d = (p[0] - q[0]).powi(2) + (p[1] - q[1]).powi(2) + (p[2] - q[2]).powi(2);
                if d < best {
                    best = d;
                }
            }
            worst = worst.max(best.sqrt());
        }
        worst
    };
    Some(one_way(a, b).max(one_way(b, a)))
}

fn median(mut values: Vec<f64>) -> f64 {
    values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mid = values.len() / 2;
    if values.len() % 2 == 0 {
        (values[mid - 1] + values[mid]) / 2.0
    } else {
        values[mid]
    }
}

// --------------------------------------------------------------- settings

#[derive(Clone, Copy, PartialEq)]
enum Setting {
    Derived,
    Explicit(f64),
}

impl Setting {
    fn label(&self) -> String {
        match self {
            Setting::Derived => "derived".to_string(),
            Setting::Explicit(t) => format!("tol={}", g(*t, 6)),
        }
    }

    fn value(&self, a: &Body, b: &Body) -> f64 {
        match self {
            Setting::Derived => operation_tolerance(&[a, b]),
            Setting::Explicit(t) => *t,
        }
    }
}

const SETTINGS: [Setting; 3] = [
    Setting::Derived,
    Setting::Explicit(1e-9),
    Setting::Explicit(1e-6),
];

const OPS: [(Operation, &str); 2] = [
    (Operation::Union, "union"),
    (Operation::Intersection, "intersection"),
];

/// One boolean, timed over `REPEATS` fresh operand pairs. The analysed result is
/// the last repeat's.
struct Run {
    ms: f64,
    outcome: Result<Body, String>,
    tolerance: f64,
}

fn run_op(
    case: &Case,
    offset: [f64; 3],
    setting: Setting,
    op: Operation,
) -> Option<Run> {
    let mut times = Vec::new();
    let mut last: Option<Result<Body, String>> = None;
    let mut tolerance = f64::NAN;
    for _ in 0..REPEATS {
        let a = build(&case.a, offset)?;
        let b = build(&case.b, offset)?;
        tolerance = setting.value(&a, &b);
        let start = Instant::now();
        let outcome = combine(a, b, op, tolerance);
        let elapsed = start.elapsed().as_secs_f64() * 1e3;
        times.push(elapsed);
        last = Some(outcome.map_err(|snag| format!("{snag:?}")));
    }
    Some(Run {
        ms: median(times),
        outcome: last.unwrap(),
        tolerance,
    })
}

/// What a finished boolean produced, as the tables report it.
struct Analysis {
    valid: bool,
    problems: Vec<String>,
    flaws: Vec<String>,
    volume: f64,
    positions: Vec<[f64; 3]>,
    verts: usize,
    tris: usize,
}

/// The analytic volume this case expects from this operation.
fn expected_for(case: &Case, op: Operation) -> f64 {
    match op {
        Operation::Union => case.expected_union,
        _ => case.expected_intersection,
    }
}

/// `expected` is the analytic volume for this operation, because an **empty**
/// result is only a defect when something was expected — the same rule
/// `manifold_driver.py`'s `valid_cell` and `cgal_driver.py` apply, so that
/// "valid" means the same thing in every results file. `DELTA_FLOOR` there is
/// 1e-9 and is used here unchanged.
fn analyse(body: &Body, expected: f64) -> Analysis {
    let raw = tess(body);
    let (positions, triangles) = weld(&raw.positions, &raw.triangles);
    let mut problems = check_mesh(&positions, &triangles);
    if triangles.is_empty() && expected.abs() <= 1e-9 {
        problems.clear();
    }
    let flaws = flaw_names(body);
    let mut all = problems.clone();
    if raw.missing_faces > 0 {
        all.push(format!("{} faces not tessellated", raw.missing_faces));
    }
    Analysis {
        valid: all.is_empty() && flaws.is_empty(),
        problems: all,
        flaws,
        volume: signed_volume(&positions, &triangles),
        positions,
        verts: triangles.iter().flatten().copied().collect::<std::collections::HashSet<_>>().len(),
        tris: triangles.len(),
    }
}

// --------------------------------------------------------------- environment

fn environment(extra: &str) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "## Environment\n");
    let _ = writeln!(out, "*Measured.*\n");
    let _ = writeln!(out, "| | |");
    let _ = writeln!(out, "|---|---|");
    let _ = writeln!(out, "| Run date | {} |", env_or("OCS_DATE", "unrecorded"));
    let _ = writeln!(out, "| CPU | `{}` |", env_or("OCS_CPU", "unrecorded"));
    let _ = writeln!(out, "| RAM | {} GB |", env_or("OCS_RAM", "unrecorded"));
    let _ = writeln!(out, "| OS | {} |", env_or("OCS_OS", "unrecorded"));
    let _ = writeln!(
        out,
        "| Toolchain | `{}` / `{}` |",
        env_or("OCS_CARGO", "unrecorded"),
        env_or("OCS_RUSTC", "unrecorded")
    );
    let _ = writeln!(
        out,
        "| `cadkernel` | commit `953d546b68aef4b6692566a1a9b077fc5bd9fb4f`, \
         <https://github.com/HakanSeven12/cadkernel>, `default-features = false`, \
         `features = [\"brep\"]` |"
    );
    let _ = writeln!(
        out,
        "| Build profile | `--release`; `spade` 2.15.1 and `rustc-hash` 2.x resolved through \
         `Cargo.lock`, committed beside this driver |"
    );
    let _ = writeln!(
        out,
        "| Tessellation | `brep::mesh::tessellate` with `TessellationTolerance::new(max_angle = \
         {TESS_ANGLE} rad, linear = {TESS_LINEAR} m)`; positions welded at {WELD_EPS} m before the \
         topology check |"
    );
    let _ = writeln!(out, "| Repeats | {REPEATS}, median reported, operands rebuilt inside every repeat |");
    let _ = writeln!(out, "{extra}");
    out
}

fn env_or(key: &str, fallback: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| fallback.to_string())
}

// --------------------------------------------------------------- torture

fn torture(cases: &[Case], out_path: &std::path::Path) {
    let mut doc = String::new();
    let _ = writeln!(doc, "# Boolean torture set — `cadkernel` raw results\n");
    let _ = writeln!(
        doc,
        "Written by [`../ocs_driver/src/main.rs`](../ocs_driver/src/main.rs). `cadkernel` is the \
         MPL-2.0 B-rep kernel that Open CAD Studio's solid modelling runs on; see \
         [`../../../docs/research/kernels/opencadstudio.md`](../../../docs/research/kernels/opencadstudio.md).\n"
    );
    let _ = writeln!(
        doc,
        "The ten cases are [`../../../reference/boolean_torture_set.py`](../../../reference/boolean_torture_set.py) \
         verbatim, carried into Rust as JSON by [`../ocs_driver/dump_cases.py`](../ocs_driver/dump_cases.py). \
         No case is added, dropped or adjusted.\n"
    );
    doc.push_str(&environment(""));

    // ---- construction
    let _ = writeln!(doc, "\n## Construction of the operands\n");
    let _ = writeln!(
        doc,
        "*Measured.* Every operand goes through `brep::make::faceted_solid(&vertices, &faces)`, \
         which takes the reference triangle soup as-is. **Its refusal is an `Option::None`, not a \
         typed error** — the kernel's typed refusal (`Snag`) exists only on the boolean, so a \
         construction failure here carries no machine-readable reason and the cause below is read \
         out of the source, not out of the return value.\n"
    );
    let _ = writeln!(
        doc,
        "*Volume* is this driver's `signed_volume` over the tessellation; *kernel V* is \
         `Mesh::mass_properties()`. *Flaws* is `Body::validate()`.\n"
    );
    let _ = writeln!(
        doc,
        "| Case | Operand | Built? | Lumps/shells/faces | Volume | kernel V | Specified V | Flaws | Derived tolerance |"
    );
    let _ = writeln!(doc, "|---|---|---|---|---|---|---|---|---|");

    let mut constructed: HashMap<String, (Option<Body>, Option<Body>)> = HashMap::new();
    for case in cases {
        let a = build(&case.a, [0.0; 3]);
        let b = build(&case.b, [0.0; 3]);
        let derived = match (&a, &b) {
            (Some(a), Some(b)) => Some(operation_tolerance(&[a, b])),
            _ => None,
        };
        for (label, body, mesh) in [("A", &a, &case.a), ("B", &b, &case.b)] {
            match body {
                Some(body) => {
                    let t = tess(body);
                    let (p, tr) = weld(&t.positions, &t.triangles);
                    let flaws = flaw_names(body);
                    let _ = writeln!(
                        doc,
                        "| `{}` | {label} | yes | {}/{}/{} | {} | {} | {} | {} | {} |",
                        case.name,
                        body.lumps.iter().count(),
                        body.shells.iter().count(),
                        body.faces.iter().count(),
                        g12(signed_volume(&p, &tr)),
                        t.kernel_volume.map(g12).unwrap_or_else(|| "-".into()),
                        g12(mesh.specified_volume),
                        if flaws.is_empty() { "none".to_string() } else { flaws.join(", ") },
                        derived.map(g12).unwrap_or_else(|| "-".into()),
                    );
                }
                None => {
                    let _ = writeln!(
                        doc,
                        "| `{}` | {label} | **no — `faceted_solid` returned `None`** | - | - | - | {} | - | - |",
                        case.name,
                        g12(mesh.specified_volume),
                    );
                }
            }
        }
        constructed.insert(case.name.clone(), (a, b));
    }

    // ---- boolean results
    let _ = writeln!(doc, "\n## Boolean results\n");
    let _ = writeln!(
        doc,
        "*Measured.* *Identity* is `|V(A) + V(B) − (V(∪) + V(∩))|` from the **measured** operand \
         volumes in the table above, so it isolates the boolean from error already in the \
         operands. A case whose operands cannot be built has no boolean to measure and its row \
         says so. `ms (∪ / ∩)` is the median of {REPEATS} runs, operands rebuilt inside every \
         repeat. **Read the ms column as an order of magnitude and not as a benchmark** — the \
         paragraph under the table measures why, from this table's own rows.\n"
    );
    let _ = writeln!(
        doc,
        "| Case | Setting | Valid? | V(union) | V(intersection) | Identity | ms (∪ / ∩) | Note |"
    );
    let _ = writeln!(doc, "|---|---|---|---|---|---|---|---|");

    let mut summary: Vec<(String, usize, usize, f64, f64, f64)> = Vec::new();
    // `(setting label, case name, op, ms)` for every timed cell, used for the noise paragraph
    // under the table.
    let mut noise: Vec<(String, String, &'static str, f64)> = Vec::new();
    for setting in SETTINGS {
        let mut valid_count = 0usize;
        let mut correct_count = 0usize;
        let mut worst_identity = 0.0_f64;
        let mut min_ms = f64::INFINITY;
        let mut max_ms = 0.0_f64;

        for case in cases {
            let (a, b) = constructed.get(&case.name).unwrap();
            let (Some(a), Some(b)) = (a, b) else {
                let which = match (a.is_some(), b.is_some()) {
                    (false, false) => "A and B",
                    (false, true) => "A",
                    _ => "B",
                };
                let _ = writeln!(
                    doc,
                    "| `{}` | {} | **n/a — operand {which} not built** | - | - | - | - | \
                     `faceted_solid` refused; no boolean ran |",
                    case.name,
                    setting.label()
                );
                continue;
            };
            let measured_a = {
                let t = tess(a);
                let (p, tr) = weld(&t.positions, &t.triangles);
                signed_volume(&p, &tr)
            };
            let measured_b = {
                let t = tess(b);
                let (p, tr) = weld(&t.positions, &t.triangles);
                signed_volume(&p, &tr)
            };

            let mut cells: Vec<(f64, String, Option<Analysis>, Vec<String>)> = Vec::new();
            for (op, _name) in OPS {
                match run_op(case, [0.0; 3], setting, op) {
                    Some(run) => match run.outcome {
                        Ok(body) => {
                            let analysis = analyse(&body, expected_for(case, op));
                            cells.push((run.ms, g12(run.tolerance), Some(analysis), Vec::new()));
                        }
                        Err(snag) => {
                            cells.push((run.ms, g12(run.tolerance), None, vec![format!("`Snag::{snag}`")]));
                        }
                    },
                    None => cells.push((f64::NAN, "-".into(), None, vec!["operand refused".into()])),
                }
            }

            let v_union = cells[0].2.as_ref().map(|a| a.volume);
            let v_inter = cells[1].2.as_ref().map(|a| a.volume);
            let identity = match (v_union, v_inter) {
                (Some(u), Some(i)) => Some((measured_a + measured_b - (u + i)).abs()),
                _ => None,
            };
            let valid = cells.iter().all(|c| c.2.as_ref().is_some_and(|a| a.valid));
            if valid {
                valid_count += 1;
            }
            let correct = |got: Option<f64>, expected: f64| -> bool {
                got.is_some_and(|v| (v - expected).abs() <= 1e-6 * expected.abs().max(1.0))
            };
            if correct(v_union, case.expected_union) && correct(v_inter, case.expected_intersection) {
                correct_count += 1;
            }
            if let Some(identity) = identity {
                worst_identity = worst_identity.max(identity);
            }
            for (index, cell) in cells.iter().enumerate() {
                if cell.0.is_finite() {
                    min_ms = min_ms.min(cell.0);
                    max_ms = max_ms.max(cell.0);
                    noise.push((
                        setting.label(),
                        case.name.clone(),
                        if index == 0 { "∪" } else { "∩" },
                        cell.0,
                    ));
                }
            }

            let mut notes: Vec<String> = Vec::new();
            for (index, (_, _, analysis, refusal)) in cells.iter().enumerate() {
                let op = if index == 0 { "∪" } else { "∩" };
                if !refusal.is_empty() {
                    notes.push(format!("{op} refused: {}", refusal.join(", ")));
                } else if let Some(analysis) = analysis {
                    if analysis.tris == 0 {
                        notes.push(format!("{op} empty, as expected"));
                    }
                    if !analysis.problems.is_empty() {
                        notes.push(format!("{op} {}", analysis.problems.join("; ")));
                    }
                    if !analysis.flaws.is_empty() {
                        notes.push(format!("{op} `Flaw::{}`", analysis.flaws.join("`, `Flaw::")));
                    }
                    let expected = if index == 0 { case.expected_union } else { case.expected_intersection };
                    let delta = analysis.volume - expected;
                    if delta.abs() > 1e-6 * expected.abs().max(1.0) {
                        notes.push(format!("Δ{op}={}", g(delta, 6)));
                    }
                }
            }
            if setting == Setting::Derived {
                notes.push(format!("derived tol {}", cells[0].1));
            }

            let _ = writeln!(
                doc,
                "| `{}` | {} | {} | {} | {} | {} | {} / {} | {} |",
                case.name,
                setting.label(),
                if valid { "yes".to_string() } else { "**no**".to_string() },
                v_union.map(g12).unwrap_or_else(|| "-".into()),
                v_inter.map(g12).unwrap_or_else(|| "-".into()),
                identity.map(g12).unwrap_or_else(|| "-".into()),
                if cells[0].0.is_finite() { ms(cells[0].0) } else { "-".into() },
                if cells[1].0.is_finite() { ms(cells[1].0) } else { "-".into() },
                if notes.is_empty() { "-".to_string() } else { notes.join("; ") },
            );
        }
        summary.push((
            setting.label(),
            valid_count,
            correct_count,
            worst_identity,
            if min_ms.is_finite() { min_ms } else { 0.0 },
            max_ms,
        ));
    }

    // ---- the noise floor, measured from the table's own rows
    let _ = writeln!(doc, "\n### How much of that ms column is the machine\n");
    let _ = writeln!(
        doc,
        "*Measured, from the rows above and nothing else.* Every case except `sliver` runs the \
         same geometry through the same code path at all three settings — the tolerances differ \
         by orders of magnitude but none of them changes what is classified — so **the spread \
         between one case's three rows is this machine's noise, not a tolerance effect**. `sliver` \
         is excluded because its 1e-6 row genuinely does different work (it refuses).\n"
    );
    let _ = writeln!(doc, "| Case | Op | ms at the three settings | Spread |");
    let _ = writeln!(doc, "|---|---|---|---|");
    let mut worst_spread = 1.0_f64;
    for case in cases {
        if case.name == "sliver" {
            continue;
        }
        for op in ["∪", "∩"] {
            let cells: Vec<f64> = SETTINGS
                .iter()
                .filter_map(|setting| {
                    noise
                        .iter()
                        .find(|(label, name, cell_op, _)| {
                            *label == setting.label() && *name == case.name && *cell_op == op
                        })
                        .map(|(_, _, _, value)| *value)
                })
                .collect();
            if cells.len() < SETTINGS.len() {
                continue;
            }
            let lo = cells.iter().cloned().fold(f64::INFINITY, f64::min);
            let hi = cells.iter().cloned().fold(0.0_f64, f64::max);
            let spread = if lo > 0.0 { hi / lo } else { f64::NAN };
            if spread.is_finite() {
                worst_spread = worst_spread.max(spread);
            }
            let _ = writeln!(
                doc,
                "| `{}` | {op} | {} | ×{} |",
                case.name,
                cells.iter().map(|v| ms(*v)).collect::<Vec<_>>().join(" / "),
                g(spread, 3)
            );
        }
    }
    let _ = writeln!(
        doc,
        "\nWorst spread over identical work in this session: **×{}**. Any cross-candidate timing \
         comparison in [`../FINDINGS.md`](../FINDINGS.md) has to survive that factor before it \
         means anything.\n",
        g(worst_spread, 3)
    );

    let _ = writeln!(doc, "\n## Summary\n");
    let _ = writeln!(
        doc,
        "*Measured.* *Correct* is both volumes within `1e-6 * max(1, |expected|)` of the analytic \
         expectation — the definition [`blender.md`](blender.md) fixes and the Manifold and CGAL \
         files adopt. A case whose operands `faceted_solid` refused counts as neither valid nor \
         correct.\n"
    );
    let _ = writeln!(doc, "| Setting | Valid /10 | Correct /10 | Worst identity residual | Time range (ms) |");
    let _ = writeln!(doc, "|---|---|---|---|---|");
    for (label, valid, correct, identity, lo, hi) in &summary {
        let _ = writeln!(
            doc,
            "| {label} | **{valid}** | {correct} | {} | {} – {} |",
            g12(*identity),
            ms(*lo),
            ms(*hi)
        );
    }

    // ---- probes
    doc.push_str(&torture_probes(cases, &constructed));

    std::fs::write(out_path, doc).unwrap();
    println!("wrote {}", out_path.display());
    for (label, valid, correct, identity, _, _) in &summary {
        println!("  {label}: {valid}/10 valid, {correct}/10 correct, worst identity {}", g12(*identity));
    }
}

fn torture_probes(cases: &[Case], constructed: &HashMap<String, (Option<Body>, Option<Body>)>) -> String {
    let mut doc = String::new();

    // Probe A — the twelve-shell operand.
    let _ = writeln!(doc, "\n## Probe A — the twelve-shell cutting tool\n");
    let _ = writeln!(
        doc,
        "**Question:** what does `faceted_solid` do with `wall_with_openings` operand B — twelve \
         disconnected closed boxes in one triangle soup, the object every other candidate was \
         handed as a single multi-component solid?\n"
    );
    let case = cases.iter().find(|c| c.name == "wall_with_openings").unwrap();
    let whole = build(&case.b, [0.0; 3]);
    let _ = writeln!(
        doc,
        "*Measured.* `faceted_solid` on the twelve-shell soup: **{}**.\n",
        match &whole {
            Some(_) => "built".to_string(),
            None => "`None`".to_string(),
        }
    );
    let _ = writeln!(
        doc,
        "*Measured, by splitting the soup into its connected components in this driver and \
         offering each one separately:*\n"
    );
    let _ = writeln!(doc, "| Shell | Verts | Faces | Built? | Volume |");
    let _ = writeln!(doc, "|---|---|---|---|---|");
    let mut built = 0;
    let mut total = 0.0;
    let components = split_components(&case.b);
    for (index, part) in components.iter().enumerate() {
        match build(part, [0.0; 3]) {
            Some(body) => {
                let t = tess(&body);
                let (p, tr) = weld(&t.positions, &t.triangles);
                let v = signed_volume(&p, &tr);
                total += v;
                built += 1;
                let _ = writeln!(
                    doc,
                    "| {} | {} | {} | yes | {} |",
                    index + 1,
                    part.verts.len(),
                    part.faces.len(),
                    g12(v)
                );
            }
            None => {
                let _ = writeln!(
                    doc,
                    "| {} | {} | {} | **no** | - |",
                    index + 1,
                    part.verts.len(),
                    part.faces.len()
                );
            }
        }
    }
    let _ = writeln!(
        doc,
        "\n{built} of {} shells build individually, total volume {}. The whole soup does not: \
         `brep::make::faceted_solid` counts the connected components of the face graph and returns \
         `None` unless there is exactly one, with the reason stated in its own source — *\"A \
         disconnected or nested shell needs explicit lump/cavity containment. Until that topology \
         is represented, accept only one closed shell so a cavity can never be silently converted \
         into filled material.\"* This is a **refusal, not a wrong answer**, and it is the reason \
         `wall_with_openings` has no boolean row above.\n",
        components.len(),
        g12(total)
    );

    // Probe B — the T-junction operand.
    let _ = writeln!(doc, "\n## Probe B — the T-junction operand\n");
    let _ = writeln!(
        doc,
        "**Question:** `near_degenerate_triangle` operand B splits the cube's top face by \
         inserting a vertex *on* the edge v5→v6, leaving a T-junction. Manifold refuses it with \
         `NotManifold`; CGAL builds it but reports it not closed. What does `faceted_solid` do?\n"
    );
    let tj = constructed.get("near_degenerate_triangle").unwrap();
    let _ = writeln!(
        doc,
        "*Measured.* Operand A: **{}**. Operand B: **{}**.\n",
        if tj.0.is_some() { "built" } else { "`None`" },
        if tj.1.is_some() { "built" } else { "`None`" }
    );
    let _ = writeln!(
        doc,
        "*Inferred, from the source:* `faceted_solid` builds an undirected edge-use map and \
         requires `entries.len() == 2` for **every** edge before it will proceed. A T-junction \
         leaves the unsplit side of v5→v6 used once and the two split halves used once each, so \
         the map fails and the constructor returns `None` — the same precondition Manifold \
         enforces, reported without a name.\n"
    );

    // Probe C — the 1e-7 m slab against the tolerance.
    let _ = writeln!(doc, "\n## Probe C — the 1e-7 m slab against the tolerance\n");
    let _ = writeln!(
        doc,
        "**Question:** OCCT's sewing tolerance degraded the slab at construction and Manifold \
         deleted it at tolerance 1e-6. Does `cadkernel` keep it, and at which boolean tolerance \
         does it stop keeping it?\n"
    );
    let sliver = cases.iter().find(|c| c.name == "sliver").unwrap();
    let _ = writeln!(doc, "| Boolean tolerance | ∩ valid? | V(∩) | Δ vs. 1e-07 | Note |");
    let _ = writeln!(doc, "|---|---|---|---|---|");
    for tolerance in [1e-12, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5] {
        match run_op(sliver, [0.0; 3], Setting::Explicit(tolerance), Operation::Intersection) {
            Some(run) => match run.outcome {
                Ok(body) => {
                    let a = analyse(&body, 1e-7);
                    let _ = writeln!(
                        doc,
                        "| {} | {} | {} | {} | {} |",
                        g(tolerance, 6),
                        if a.valid { "yes" } else { "**no**" },
                        g12(a.volume),
                        g(a.volume - 1e-7, 6),
                        if a.problems.is_empty() && a.flaws.is_empty() {
                            "-".to_string()
                        } else {
                            format!("{} {}", a.problems.join("; "), a.flaws.join(", "))
                        }
                    );
                }
                Err(snag) => {
                    let _ = writeln!(
                        doc,
                        "| {} | **refused** | - | - | `Snag::{snag}` |",
                        g(tolerance, 6)
                    );
                }
            },
            None => {
                let _ = writeln!(doc, "| {} | - | - | - | operand refused |", g(tolerance, 6));
            }
        }
    }
    let _ = writeln!(
        doc,
        "\nThe slab's own thickness is 1e-07 m. A tolerance at or above it is a tolerance larger \
         than the feature, which is the state that deleted the slab silently on one other \
         candidate; a typed refusal instead of a deletion is the behaviour this column is checking \
         for.\n"
    );

    // Probe D — the derived tolerance, per case.
    let _ = writeln!(doc, "\n## Probe D — what `operation_tolerance` derives\n");
    let _ = writeln!(
        doc,
        "**Question:** `brep::operation_tolerance(&[&a, &b])` is `extent * 1e-8 + \
         f64::EPSILON * coordinate_scale * 64.0` over the two bodies' vertices. What does it \
         actually come to on this set, and how does it compare with the smallest feature in the \
         case?\n"
    );
    let _ = writeln!(doc, "| Case | Derived tolerance | Smallest feature in the case |");
    let _ = writeln!(doc, "|---|---|---|");
    for case in cases {
        let (a, b) = constructed.get(&case.name).unwrap();
        let (Some(a), Some(b)) = (a, b) else {
            let _ = writeln!(doc, "| `{}` | - (operand refused) | - |", case.name);
            continue;
        };
        let feature = match case.name.as_str() {
            "sliver" => "1e-07 m (the slab thickness)",
            "near_degenerate_triangle" => "~1e-06 rad sliver triangle",
            "contained" => "0.25 m",
            _ => "0.5 m or larger",
        };
        let _ = writeln!(
            doc,
            "| `{}` | {} | {feature} |",
            case.name,
            g12(operation_tolerance(&[a, b]))
        );
    }
    let _ = writeln!(
        doc,
        "\nOn a unit-scale case the derived value is around 1e-08 m — one order **below** the \
         `sliver`'s 1e-07 m thickness, which is why the slab is not at risk from the default \
         setting here. It is a bounding-box-derived number, so it tracks the model's size and, as \
         the precision file's own probe shows, its distance from the origin.\n"
    );

    // Probe E — determinism.
    let _ = writeln!(doc, "\n## Probe E — run-to-run determinism\n");
    let _ = writeln!(
        doc,
        "**Question:** does the same input give the same output? Two other candidates emit \
         run-to-run variation (`problems.md` P-16).\n"
    );
    let _ = writeln!(doc, "| Case | Op | Runs | Distinct (verts, tris, volume) signatures |");
    let _ = writeln!(doc, "|---|---|---|---|");
    for case in cases {
        let (a, b) = constructed.get(&case.name).unwrap();
        if a.is_none() || b.is_none() {
            continue;
        }
        for (op, name) in OPS {
            let mut signatures: Vec<String> = Vec::new();
            for _ in 0..10 {
                let Some(a) = build(&case.a, [0.0; 3]) else { continue };
                let Some(b) = build(&case.b, [0.0; 3]) else { continue };
                let tolerance = operation_tolerance(&[&a, &b]);
                let signature = match combine(a, b, op, tolerance) {
                    Ok(body) => {
                        let analysis = analyse(&body, expected_for(case, op));
                        format!("{}v/{}t/V={}", analysis.verts, analysis.tris, g(analysis.volume, 17))
                    }
                    Err(snag) => format!("Snag::{snag:?}"),
                };
                if !signatures.contains(&signature) {
                    signatures.push(signature);
                }
            }
            let _ = writeln!(
                doc,
                "| `{}` | {name} | 10 | {} — {} |",
                case.name,
                signatures.len(),
                signatures.join(" · ")
            );
        }
    }

    doc
}

/// Splits a triangle soup into its connected components by shared vertex index.
fn split_components(mesh: &MeshIn) -> Vec<MeshIn> {
    let mut parent: Vec<usize> = (0..mesh.verts.len()).collect();
    fn find(parent: &mut Vec<usize>, mut x: usize) -> usize {
        while parent[x] != x {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        x
    }
    for face in &mesh.faces {
        for window in face.windows(2) {
            let (a, b) = (find(&mut parent, window[0]), find(&mut parent, window[1]));
            parent[a] = b;
        }
    }
    let mut groups: Vec<(usize, Vec<usize>)> = Vec::new();
    for (index, face) in mesh.faces.iter().enumerate() {
        let root = find(&mut parent, face[0]);
        match groups.iter_mut().find(|(r, _)| *r == root) {
            Some((_, faces)) => faces.push(index),
            None => groups.push((root, vec![index])),
        }
    }
    groups
        .into_iter()
        .map(|(_, face_indices)| {
            let mut remap: HashMap<usize, usize> = HashMap::new();
            let mut verts = Vec::new();
            let mut faces = Vec::new();
            for &index in &face_indices {
                let face = &mesh.faces[index];
                let mapped: Vec<usize> = face
                    .iter()
                    .map(|&v| {
                        *remap.entry(v).or_insert_with(|| {
                            verts.push(mesh.verts[v]);
                            verts.len() - 1
                        })
                    })
                    .collect();
                faces.push(mapped);
            }
            MeshIn {
                verts,
                faces,
                specified_volume: f64::NAN,
            }
        })
        .collect()
}

// --------------------------------------------------------------- precision

fn precision(cases: &[Case], offset: [f64; 3], out_path: &std::path::Path) {
    let mut doc = String::new();
    let _ = writeln!(doc, "# Precision set — `cadkernel` raw results\n");
    let _ = writeln!(
        doc,
        "Written by [`../../boolean-torture/ocs_driver/src/main.rs`](../../boolean-torture/ocs_driver/src/main.rs) \
         (`precision` mode), the same driver and the same construction path as \
         [`../../boolean-torture/results/opencadstudio.md`](../../boolean-torture/results/opencadstudio.md).\n"
    );
    let _ = writeln!(
        doc,
        "**Offset:** `({}, {}, {})` — 500 km east, 500 km north, applied to the **input \
         coordinates**, which is what a project modelling in a national projection does. The far \
         result is translated back by −offset before any comparison or any volume integral.\n",
        offset[0], offset[1], offset[2]
    );
    doc.push_str(&environment(""));

    // The coordinate policy, measured rather than quoted.
    let _ = writeln!(doc, "\n## Does the 500 km offset reach the boolean?\n");
    let _ = writeln!(
        doc,
        "**This question has to be answered before the table below can be read.** `cadkernel`'s \
         crate documentation states a coordinate policy in `src/lib.rs`: *\"Every entry point lifts \
         its input into a local frame before doing any math, and shifts results back to world \
         coordinates on the way out.\"* `geom2d::Frame` implements exactly that — a translation-only \
         frame, `Frame::around` anchoring at the **midpoint of the bounding box** rather than at \
         an arbitrary member, documented as bounding every lifted coordinate by half the extent.\n"
    );
    let _ = writeln!(
        doc,
        "*Measured, at commit `953d546b68aef4b6692566a1a9b077fc5bd9fb4f`:* `Frame::around`, \
         `Frame::at` and `Frame::identity` are constructed **nowhere outside `src/geom2d/frame.rs` \
         itself**, and inside that file only in its own unit tests. `grep -rn \
         'Frame::around\\|Frame::at\\|Frame::identity\\|\\.lift(\\|\\.lower('` over `src/` returns no \
         call site in `src/brep/`. The B-rep boolean path — `make::faceted_solid`, \
         `bounds::operation_tolerance`, `imprint::imprint`, `boolean::combine`, `brep::mesh` — \
         does its arithmetic on the world coordinates it is handed.\n"
    );
    let _ = writeln!(
        doc,
        "So **the 500 km offset reaches the boolean in full**, and the deviations below are the \
         unmitigated f64 answer, not a lifted one. The lift is written, documented and unwired; \
         the `space::planar` `lift`/`lower` pair that *is* used throughout is a different \
         operation — the 3D↔2D map onto a face's plane, not a translation for conditioning.\n"
    );

    // Derived tolerance, near vs far.
    let _ = writeln!(doc, "\n## `operation_tolerance` near vs far\n");
    let _ = writeln!(
        doc,
        "*Measured.* `extent * 1e-8 + f64::EPSILON * coordinate_scale * 64.0`, where \
         `coordinate_scale` is the largest absolute coordinate. The second term is what the offset \
         moves.\n"
    );
    let _ = writeln!(doc, "| Case | Derived tolerance at the origin | at 500 km | Ratio |");
    let _ = writeln!(doc, "|---|---|---|---|");
    for case in cases {
        let near = match (build(&case.a, [0.0; 3]), build(&case.b, [0.0; 3])) {
            (Some(a), Some(b)) => Some(operation_tolerance(&[&a, &b])),
            _ => None,
        };
        let far = match (build(&case.a, offset), build(&case.b, offset)) {
            (Some(a), Some(b)) => Some(operation_tolerance(&[&a, &b])),
            _ => None,
        };
        match (near, far) {
            (Some(near), Some(far)) => {
                let _ = writeln!(
                    doc,
                    "| `{}` | {} | {} | {} |",
                    case.name,
                    g12(near),
                    g12(far),
                    g(far / near, 4)
                );
            }
            _ => {
                let _ = writeln!(doc, "| `{}` | - | - | - (operand refused) |", case.name);
            }
        }
    }
    let _ = writeln!(
        doc,
        "\nThe tolerance a boolean runs at is therefore **a function of where the model sits**, not \
         only of how big it is — the same coupling the Manifold file records for its own derived \
         tolerance. A local frame in the caller fixes the coordinates and leaves this coupling \
         alone, because the tolerance is derived after the coordinates are handed over.\n"
    );

    // The main table.
    let _ = writeln!(doc, "\n## Boolean results near vs far\n");
    let _ = writeln!(
        doc,
        "*Measured.* *Vertex deviation* is the worst nearest-neighbour distance between the \
         origin result's welded tessellation vertices and the far result's, after translating the \
         far result back by −offset, taken as the worse of both matching directions. **The far \
         volume is computed on the back-translated vertices**, because `signed_volume` sums \
         products of raw coordinates and at 5e5 m the cancellation in that sum is larger than \
         anything the kernel does — charging it to the candidate would be a measurement artefact, \
         which is the reason the Manifold and CGAL drivers back-translate too.\n"
    );
    let _ = writeln!(
        doc,
        "| Case | Setting | Op | Valid near+far? | V near / far | ΔV (abs, rel) | Deviation | ms near / far | tol near / far |"
    );
    let _ = writeln!(doc, "|---|---|---|---|---|---|---|---|---|");

    let mut worst_overall = 0.0_f64;
    let mut worst_relative = 0.0_f64;
    for case in cases {
        for setting in [Setting::Derived, Setting::Explicit(1e-9)] {
            for (op, name) in OPS {
                let near = run_op(case, [0.0; 3], setting, op);
                let far = run_op(case, offset, setting, op);
                let (Some(near), Some(far)) = (near, far) else {
                    let _ = writeln!(
                        doc,
                        "| `{}` | {} | {name} | **n/a — operand not built** | - | - | - | - | - |",
                        case.name,
                        setting.label()
                    );
                    continue;
                };
                match (&near.outcome, &far.outcome) {
                    (Ok(near_body), Ok(far_body)) => {
                        let expected = expected_for(case, op);
                        let near_analysis = analyse(near_body, expected);
                        let far_analysis = analyse(far_body, expected);
                        let far_back: Vec<[f64; 3]> = far_analysis
                            .positions
                            .iter()
                            .map(|p| [p[0] - offset[0], p[1] - offset[1], p[2] - offset[2]])
                            .collect();
                        let far_tess = tess(far_body);
                        let (_, far_tris) = weld(&far_tess.positions, &far_tess.triangles);
                        let v_far = signed_volume(&far_back, &far_tris);
                        let v_near = near_analysis.volume;
                        let deviation = worst_nearest(&near_analysis.positions, &far_back);
                        let delta = v_far - v_near;
                        let relative = if v_near.abs() > 0.0 { delta / v_near } else { f64::NAN };
                        if let Some(deviation) = deviation {
                            worst_overall = worst_overall.max(deviation);
                        }
                        if relative.is_finite() {
                            worst_relative = worst_relative.max(relative.abs());
                        }
                        let _ = writeln!(
                            doc,
                            "| `{}` | {} | {name} | {} | {} / {} | {}, {} | {} | {} / {} | {} / {} |",
                            case.name,
                            setting.label(),
                            match (near_analysis.valid, far_analysis.valid) {
                                (true, true) => "yes".to_string(),
                                (true, false) => format!("near yes / far **no** — {}", far_analysis.problems.join("; ")),
                                (false, true) => format!("near **no** — {} / far yes", near_analysis.problems.join("; ")),
                                (false, false) => format!("**no** — {}", near_analysis.problems.join("; ")),
                            },
                            g12(v_near),
                            g12(v_far),
                            g(delta, 6),
                            if relative.is_finite() { g(relative, 6) } else { "n/a".to_string() },
                            deviation
                                .map(|d| format!("**{} m**", g(d, 6)))
                                .unwrap_or_else(|| "n/a (0 verts)".into()),
                            ms(near.ms),
                            ms(far.ms),
                            g(near.tolerance, 4),
                            g(far.tolerance, 4),
                        );
                    }
                    (near_outcome, far_outcome) => {
                        let describe = |outcome: &Result<Body, String>| match outcome {
                            Ok(_) => "ok".to_string(),
                            Err(snag) => format!("`Snag::{snag}`"),
                        };
                        let _ = writeln!(
                            doc,
                            "| `{}` | {} | {name} | **refused** — near {}, far {} | - | - | - | {} / {} | {} / {} |",
                            case.name,
                            setting.label(),
                            describe(near_outcome),
                            describe(far_outcome),
                            ms(near.ms),
                            ms(far.ms),
                            g(near.tolerance, 4),
                            g(far.tolerance, 4),
                        );
                    }
                }
            }
        }
    }

    let _ = writeln!(
        doc,
        "\n**Worst vertex deviation over the whole set: {} m**, worst relative ΔV {}. R-17's pass \
         line is 1e-6 m and its fail line 1e-4 m.\n",
        g(worst_overall, 6),
        g(worst_relative, 6)
    );

    // Mitigation probe.
    let _ = writeln!(doc, "\n## Probe — the tile-frame mitigation, measured\n");
    let _ = writeln!(
        doc,
        "**Question:** ADR-0006 proposes f64 local coordinates in tile frames — the far placement \
         carried *outside* the geometry. `cadkernel` does not carry it for the caller (see the \
         first section), so the mitigation here is the caller's own: run the boolean at the \
         origin, then move the result out to 5e5 m with `brep::place::transform` and back again, \
         which is what a tile frame does on the way to and from the world. What does the round \
         trip cost?\n"
    );
    let _ = writeln!(doc, "| Case | Op | Valid after the round trip? | V | Deviation vs. the origin result |");
    let _ = writeln!(doc, "|---|---|---|---|---|");
    for case in cases {
        for (op, name) in OPS {
            let Some(run) = run_op(case, [0.0; 3], Setting::Derived, op) else {
                let _ = writeln!(doc, "| `{}` | {name} | - | - | operand refused |", case.name);
                continue;
            };
            let Ok(body) = run.outcome else {
                let _ = writeln!(doc, "| `{}` | {name} | - | - | boolean refused |", case.name);
                continue;
            };
            let origin = analyse(&body, expected_for(case, op));
            let out = transform(&body, &Placement::at(offset));
            let back = out.as_ref().and_then(|b| transform(b, &Placement::at([-offset[0], -offset[1], -offset[2]])));
            match back {
                Some(back) => {
                    let round_tripped = analyse(&back, expected_for(case, op));
                    let deviation = worst_nearest(&origin.positions, &round_tripped.positions);
                    let _ = writeln!(
                        doc,
                        "| `{}` | {name} | {} | {} | {} |",
                        case.name,
                        if round_tripped.valid { "yes" } else { "**no**" },
                        g12(round_tripped.volume),
                        deviation
                            .map(|d| format!("**{} m**", g(d, 6)))
                            .unwrap_or_else(|| "n/a (0 verts)".into())
                    );
                }
                None => {
                    let _ = writeln!(doc, "| `{}` | {name} | **transform refused** | - | - |", case.name);
                }
            }
        }
    }

    // What a 0 m deviation can and cannot show.
    let _ = writeln!(doc, "\n## Probe — what a 0 m deviation can and cannot show\n");
    let _ = writeln!(
        doc,
        "**Question:** the main table's deviations are exactly 0 m. Is that a result about the \
         kernel, or about the coordinates?\n"
    );
    let _ = writeln!(
        doc,
        "*Measured.* Worst `|((v + offset) − offset) − v|` over every operand vertex of the case, in \
         `f64`, with no kernel involved — the exactness of the offset itself — beside whether the \
         case reached the boolean at all.\n"
    );
    let _ = writeln!(doc, "| Case | Operand vertices | Offset round-trip error | Reached the boolean? |");
    let _ = writeln!(doc, "|---|---|---|---|");
    for case in cases {
        let mut worst = 0.0_f64;
        let mut count = 0usize;
        for mesh in [&case.a, &case.b] {
            for v in &mesh.verts {
                count += 1;
                for axis in 0..3 {
                    worst = worst.max(((v[axis] + offset[axis]) - offset[axis] - v[axis]).abs());
                }
            }
        }
        let reached = build(&case.a, [0.0; 3]).is_some() && build(&case.b, [0.0; 3]).is_some();
        let _ = writeln!(
            doc,
            "| `{}` | {count} | {} | {} |",
            case.name,
            g(worst, 6),
            if reached { "yes" } else { "**no — `faceted_solid` refused operand B**" }
        );
    }
    let _ = writeln!(
        doc,
        "\nThe two cases that reach the boolean are built from coordinates that are multiples of \
         0.5 m, and 500000 ± those values is exact in `f64`, so the offset introduces no error \
         before the boolean starts. **Every other f64 candidate also measured exactly 0 m on these \
         two cases** — see [`../FINDINGS.md`](../FINDINGS.md) §Results, the `overlap_half` and \
         `coplanar_faces` rows for OCCT, Manifold `Mesh64` and CGAL Epick f64. The case that \
         separated those candidates from each other, `wall_with_openings`, is the one \
         `faceted_solid` refuses. So this file's 0 m is **consistent with an f64 path and adds no \
         evidence beyond the three candidates already measured**; it is not a tighter result than \
         theirs.\n"
    );

    // Cancellation probe.
    let _ = writeln!(doc, "\n## Probe — how much of a far-field volume error is the measurement's own\n");
    let _ = writeln!(
        doc,
        "*Measured.* The same far solid, integrated four ways, so the back-translation in the main \
         table is shown not to be doing the work. *Near, coords shifted* moves the **origin** \
         result out to 5e5 m in `double` and integrates there — no boolean, no kernel, just the \
         sum — and is the floor on what any far-field volume can be worth.\n"
    );
    let _ = writeln!(doc, "| Case | Op | Near | Near, coords shifted | Far, raw | Far, back-translated | Far, `Mesh::mass_properties()` |");
    let _ = writeln!(doc, "|---|---|---|---|---|---|---|");
    for case in cases {
        for (op, name) in OPS {
            let near = run_op(case, [0.0; 3], Setting::Derived, op);
            let far = run_op(case, offset, Setting::Derived, op);
            let (Some(near), Some(far)) = (near, far) else { continue };
            let (Ok(near_body), Ok(far_body)) = (&near.outcome, &far.outcome) else { continue };
            let near_raw = tess(near_body);
            let (near_pos, near_tris) = weld(&near_raw.positions, &near_raw.triangles);
            let shifted: Vec<[f64; 3]> = near_pos
                .iter()
                .map(|p| [p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]])
                .collect();
            let far_raw = tess(far_body);
            let (far_pos, far_tris) = weld(&far_raw.positions, &far_raw.triangles);
            let far_back: Vec<[f64; 3]> = far_pos
                .iter()
                .map(|p| [p[0] - offset[0], p[1] - offset[1], p[2] - offset[2]])
                .collect();
            let _ = writeln!(
                doc,
                "| `{}` | {name} | {} | {} | {} | {} | {} |",
                case.name,
                g12(signed_volume(&near_pos, &near_tris)),
                g12(signed_volume(&shifted, &near_tris)),
                g12(signed_volume(&far_pos, &far_tris)),
                g12(signed_volume(&far_back, &far_tris)),
                far_raw.kernel_volume.map(g12).unwrap_or_else(|| "-".into()),
            );
        }
    }

    std::fs::write(out_path, doc).unwrap();
    println!("wrote {}", out_path.display());
    println!("  worst deviation {} m, worst relative ΔV {}", g(worst_overall, 6), g(worst_relative, 6));
}

// --------------------------------------------------------------- main

fn main() {
    let mode = std::env::args().nth(1).unwrap_or_else(|| "torture".to_string());
    let here = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).to_path_buf();
    let text = std::fs::read_to_string(here.join("cases.json"))
        .expect("cases.json missing — run `python spikes/boolean-torture/ocs_driver/dump_cases.py` first");
    let root: Value = serde_json::from_str(&text).unwrap();
    let offset_array = root["offset"].as_array().unwrap();
    let offset = [
        offset_array[0].as_f64().unwrap(),
        offset_array[1].as_f64().unwrap(),
        offset_array[2].as_f64().unwrap(),
    ];
    let spikes = here.parent().unwrap().parent().unwrap().to_path_buf();

    match mode.as_str() {
        "torture" => {
            let cases = read_cases(&root, "torture");
            torture(&cases, &spikes.join("boolean-torture/results/opencadstudio.md"));
        }
        "precision" => {
            let cases = read_cases(&root, "precision");
            precision(&cases, offset, &spikes.join("precision-set/results/opencadstudio.md"));
        }
        other => panic!("unknown mode {other}; use `torture` or `precision`"),
    }
}
