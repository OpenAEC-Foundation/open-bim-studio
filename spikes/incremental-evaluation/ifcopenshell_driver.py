"""Throwaway spike driver — R-01 (incremental evaluation) and P-10 (implementation disagreement).

Measures, for IfcOpenShell, on one benchmark model from ../../reference/models/:

  1. parse time                ifcopenshell.open
  2. full geometry iteration   ifcopenshell.geom.iterator, for every geometry library the
                               wheel exposes (opencascade, cgal, cgal-simple,
                               hybrid-cgal-simple-opencascade) at num_threads=32, and
                               opencascade also at num_threads=1
  3. process peak working set  psutil peak_wset -- a PROCESS peak, not a data size. Each model
                               is run in its own process (see --model) so the number is not
                               inflated by a previous model in the same process.
  4. per-element re-evaluation create_shape() timed separately for EVERY element the iterator
                               produced: median, p95, max, and how many fall under the 16 ms
                               and 100 ms thresholds R-01 is stated in. This is the R-01
                               measurement; the single-wall test below is one point in it.
  5. failures by entity type   create_shape() run on every IfcProduct with a Representation
                               that the iterator did NOT produce, and the exception recorded
                               per IfcClass.
  6. the R-01 edit test        translate one IfcWall's ObjectPlacement by 1 m, then time
                               (a) create_shape() for that element alone and
                               (b) a full re-iteration of the model.
                               Repeated for the single most expensive element in the model
                               (the one with the largest create_shape time in step 4), so the
                               worst case is measured and not only a convenient one.
  7. a per-GUID element table  GUID, IfcClass, triangles, signed volume, bbox -- one table per
                               geometry library in ELEMENT_TABLE_LIBRARIES, consumed by
                               compare.py for the P-10 disagreement analysis

Every timed operation opens a fresh ifcopenshell.file and builds a fresh iterator, so no
operand or object is reused across repeats. The pass that collects the element table is a
separate, untimed pass: the pure-Python volume computation is never inside a timed region.

Usage:  python ifcopenshell_driver.py --model NAME [--repeats N] [--out FILE]
Writes: results/<out>                       (default results/ifcopenshell_<model>.json)
        results/ifcopenshell-<library>_<model>_elements.csv

Requires: ifcopenshell (wheel), psutil.  numpy is NOT used; the volume function is below.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import subprocess
import sys
import time

import psutil

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.ifcopenshell_wrapper as ios_wrapper

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODELS = {
    "AC20-FZK-Haus": os.path.join(REPO, "reference", "models", "AC20-FZK-Haus.ifc"),
    "IFC_Schependomlaan": os.path.join(REPO, "reference", "models", "IFC_Schependomlaan.ifc"),
}
RESULTS = os.path.join(HERE, "results")

# Every geometry library the installed wheel exposes. Verified at runtime against
# typing.get_args(ifcopenshell.geom.GEOMETRY_LIBRARY).
LIBRARIES = ["opencascade", "cgal", "cgal-simple", "hybrid-cgal-simple-opencascade"]
# Which of them also get a per-GUID element table written, for the disagreement analysis.
ELEMENT_TABLE_LIBRARIES = ["opencascade", "cgal-simple"]
# The R-01 thresholds, quoted from docs/risks.md R-01 so the driver reports against them.
R01_PASS_MS = 16.0
R01_FAIL_MS = 100.0


# ---------------------------------------------------------------- helpers


def hardware() -> dict:
    cpu = ""
    try:
        cpu = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name",
            ],
            text=True,
        ).strip()
    except Exception as exc:  # pragma: no cover - spike
        cpu = f"<unavailable: {exc}>"
    return {
        "cpu": cpu,
        "ram_gb": round(psutil.virtual_memory().total / (1024**3)),
        "logical_processors": os.cpu_count(),
        "os": f"{platform.system()} {platform.release()} {platform.version()}",
        "python": sys.version.split()[0],
    }


def peak_wset_mb() -> float:
    """Process peak working set in MB. This is a PROCESS peak, not a data size."""
    return psutil.Process().memory_info().peak_wset / (1024**2)


def signed_volume(verts: list[float], faces: list[int]) -> float:
    """Signed volume via the divergence theorem, summed over triangles.

    v = 1/6 * sum over triangles of dot(a, cross(b, c)).
    Correct only for a closed surface; for an open one it is still a deterministic
    function of the same triangles, which is what the disagreement comparison needs.
    Plain Python so the number depends on nothing but the triangles.
    """
    total = 0.0
    for i in range(0, len(faces), 3):
        i0, i1, i2 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
        ax, ay, az = verts[i0], verts[i0 + 1], verts[i0 + 2]
        bx, by, bz = verts[i1], verts[i1 + 1], verts[i1 + 2]
        cx, cy, cz = verts[i2], verts[i2 + 1], verts[i2 + 2]
        total += (
            ax * (by * cz - bz * cy)
            - ay * (bx * cz - bz * cx)
            + az * (bx * cy - by * cx)
        )
    return total / 6.0


def bbox(verts: list[float]) -> tuple[float, float, float, float, float, float]:
    xs = verts[0::3]
    ys = verts[1::3]
    zs = verts[2::3]
    if not xs:
        return (0.0,) * 6
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def make_settings() -> ifcopenshell.geom.settings:
    """Defaults, made explicit so the results file can state them."""
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)  # so vertices are comparable with web-ifc's
    s.set("weld-vertices", True)  # default; stated for the record
    s.set("apply-default-materials", True)  # default
    return s


def settings_dump(s: ifcopenshell.geom.settings) -> dict:
    """Every setting name the wheel exposes and its value; "<not set>" where the
    library raises RuntimeError("Setting not set") for a name with no default."""
    out = {}
    for name in sorted(s.setting_names()):
        try:
            out[name] = repr(s.get(name))
        except Exception:
            out[name] = "<not set>"
    return out


def summarise_log(log: str) -> dict:
    """Group log lines by severity and by the text of the message.

    IfcOpenShell writes "[Severity] [timestamp] message", and where a message concerns an
    instance it writes that instance on the FOLLOWING line, with no severity tag. This
    function does not join the two, so an instance line is counted on its own under the
    "<none>" severity; entity-type attribution is therefore NOT done here. Failures by
    entity type come from per_element_create_shape instead, which catches the exception on
    a known element.

    The rule: severity is the first bracketed word; the message is everything after the
    timestamp, with any run of digits replaced by "<n>" so that lines differing only in a
    number or an id collapse into one group; each line counted exactly once.
    """
    import re as _re

    severity: dict[str, int] = {}
    per_message: dict[str, int] = {}
    lines = [ln for ln in log.splitlines() if ln.strip()]
    for ln in lines:
        s = ln.strip()
        m = _re.match(r"\[(\w+)\]\s*(?:\[[^\]]*\]\s*)?(.*)$", s)
        sev = m.group(1) if m else "<none>"
        msg = (m.group(2) if m else s).strip()
        severity[sev] = severity.get(sev, 0) + 1
        key = f"[{sev}] " + _re.sub(r"\d+", "<n>", msg)[:160]
        per_message[key] = per_message.get(key, 0) + 1
    return {
        "total_lines": len(lines),
        "by_severity": dict(sorted(severity.items(), key=lambda kv: -kv[1])),
        "top_messages": dict(sorted(per_message.items(), key=lambda kv: -kv[1])[:25]),
        "rule": "severity from the leading [tag]; message text after the timestamp with "
                "digit runs replaced by <n>; each line counted once. The log does not name "
                "the instance, so it is not attributed to an entity type here",
    }


def quantiles(xs: list[float]) -> dict:
    s = sorted(xs)
    if not s:
        return {}

    def q(p: float) -> float:
        if len(s) == 1:
            return s[0]
        i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
        return s[i]

    return {
        "n": len(s),
        "min_ms": s[0] * 1000.0,
        "median_ms": statistics.median(s) * 1000.0,
        "p90_ms": q(0.90) * 1000.0,
        "p95_ms": q(0.95) * 1000.0,
        "p99_ms": q(0.99) * 1000.0,
        "max_ms": s[-1] * 1000.0,
        "mean_ms": statistics.fmean(s) * 1000.0,
        "total_s": sum(s),
    }


# ---------------------------------------------------------------- measurements


def time_parse(path: str, repeats: int) -> tuple[list[float], dict]:
    times = []
    info = {}
    for _ in range(repeats):
        t0 = time.perf_counter()
        f = ifcopenshell.open(path)  # fresh file object every repeat
        times.append(time.perf_counter() - t0)
        info = {
            "schema": f.schema,
            "schema_identifier": f.schema_identifier,
            "total_instances": len(list(f)),
        }
        del f
    return times, info


def iterate_timed(path: str, num_threads: int, library: str) -> tuple[float, dict]:
    """One full iteration over a freshly opened file. Nothing but iteration is timed."""
    f = ifcopenshell.open(path)
    settings = make_settings()
    t0 = time.perf_counter()
    it = ifcopenshell.geom.iterator(settings, f, num_threads=num_threads,
                                    geometry_library=library)
    produced = 0
    ok = it.initialize()
    if ok:
        while True:
            it.get()
            produced += 1
            if not it.next():
                break
    elapsed = time.perf_counter() - t0
    log = it.getLog()
    had_error = it.had_error_processing_elements()
    del it, f
    return elapsed, {"produced": produced, "initialized": ok,
                     "had_error_processing_elements": bool(had_error), "log": log}


def iterate_collect(path: str, num_threads: int, library: str) -> tuple[list[dict], dict]:
    """A separate, UNTIMED pass that builds the per-GUID element table.

    Kept out of every timed region on purpose: the volume function is plain Python and
    would otherwise be counted as iteration time.
    """
    f = ifcopenshell.open(path)
    settings = make_settings()
    it = ifcopenshell.geom.iterator(settings, f, num_threads=num_threads,
                                    geometry_library=library)
    rows = []
    if it.initialize():
        while True:
            shape = it.get()
            geo = shape.geometry
            verts = list(geo.verts)
            faces = list(geo.faces)
            rows.append(
                {
                    "guid": shape.guid,
                    "ifc_class": shape.type,
                    "express_id": shape.id,
                    "triangles": len(faces) // 3,
                    "vertices": len(verts) // 3,
                    "volume": signed_volume(verts, faces),
                    "bbox": bbox(verts),
                }
            )
            if not it.next():
                break
    log = it.getLog()
    del it, f
    return rows, {"produced": len(rows), "log": log}


def count_geometric_products(path: str) -> dict:
    """How many IfcProduct instances carry a Representation at all.

    The rule: an instance is counted if it is an IfcProduct, its Representation
    attribute is set, and it is not an IfcOpeningElement (openings are subtracted,
    never emitted as elements) and not an IfcSpace or IfcGrid or IfcAnnotation
    (which the default 'Body' context filter drops). Counted per class as well.
    """
    f = ifcopenshell.open(path)
    excluded = {"IfcOpeningElement", "IfcSpace", "IfcGrid", "IfcAnnotation",
                "IfcOpeningStandardCase"}
    per_class: dict[str, int] = {}
    per_class_all: dict[str, int] = {}
    guid_seen: dict[str, int] = {}
    total = 0
    with_repr = 0
    for prod in f.by_type("IfcProduct"):
        total += 1
        cls = prod.is_a()
        per_class_all[cls] = per_class_all.get(cls, 0) + 1
        g = getattr(prod, "GlobalId", None)
        if g:
            guid_seen[g] = guid_seen.get(g, 0) + 1
        if getattr(prod, "Representation", None) is None:
            continue
        with_repr += 1
        if cls in excluded:
            continue
        per_class[cls] = per_class.get(cls, 0) + 1
    dup = {g: n for g, n in guid_seen.items() if n > 1}
    del f
    return {
        # The comparison in compare.py joins on GlobalId, so a file with non-unique
        # GlobalIds would silently merge two products into one row. Counted here so the
        # join is known to be sound (or known not to be).
        "ifcproduct_distinct_globalids": len(guid_seen),
        "ifcproduct_globalids_used_more_than_once": len(dup),
        "ifcproduct_duplicate_globalid_examples": dict(list(dup.items())[:5]),
        "ifcproduct_total": total,
        "ifcproduct_with_representation": with_repr,
        "counted_by_rule": sum(per_class.values()),
        "rule": "IfcProduct with Representation set, excluding " + ", ".join(sorted(excluded)),
        "per_class": dict(sorted(per_class.items(), key=lambda kv: -kv[1])),
        "ifcproduct_all_by_class": dict(sorted(per_class_all.items(), key=lambda kv: -kv[1])),
    }


def per_element_create_shape(path: str, produced_ids: list[int], library: str) -> dict:
    """Time create_shape() separately for every element the iterator produced.

    This is the R-01 measurement: create_shape(settings, element) is the only public way
    IfcOpenShell offers to produce the geometry of ONE element, so it is the cost of
    re-evaluating one element after a change. It is a conservative (pessimistic) proxy:
    every call constructs its own kernel and mapping, so any setup an incremental
    implementation would hold across edits is charged to every measurement here.

    'cache-shapes' is off (see the settings dump), so no call returns a cached result.

    Also runs create_shape() on the IfcProducts with a Representation that the iterator did
    NOT produce, and records the exception per IfcClass -- the failures-by-entity-type table.
    """
    f = ifcopenshell.open(path)
    settings = make_settings()
    produced = set(produced_ids)

    times: list[float] = []
    per_row: list[tuple[int, str, float]] = []
    errors: dict[str, int] = {}
    for eid in produced_ids:
        el = f.by_id(eid)
        t0 = time.perf_counter()
        try:
            shape = ifcopenshell.geom.create_shape(settings, el, geometry_library=library)
            dt = time.perf_counter() - t0
            del shape
        except Exception as exc:
            dt = time.perf_counter() - t0
            key = f"{el.is_a()}: {type(exc).__name__}"
            errors[key] = errors.get(key, 0) + 1
            continue
        times.append(dt)
        per_row.append((eid, el.is_a(), dt))

    # elements the iterator did not produce, but which carry a Representation.
    # Detailed logging is turned on for this pass only -- it writes parser progress to
    # stdout and adds logging I/O, so it must never be on inside a timed region.
    ios_wrapper.turn_on_detailed_logging()
    not_produced: dict[str, int] = {}
    not_produced_reason: dict[str, int] = {}
    excluded = {"IfcOpeningElement", "IfcSpace", "IfcGrid", "IfcAnnotation",
                "IfcOpeningStandardCase"}
    for prod in f.by_type("IfcProduct"):
        if prod.id() in produced or getattr(prod, "Representation", None) is None:
            continue
        cls = prod.is_a()
        not_produced[cls] = not_produced.get(cls, 0) + 1
        if cls in excluded:
            reason = f"{cls}: filtered by the default context/type filter (not attempted)"
            not_produced_reason[reason] = not_produced_reason.get(reason, 0) + 1
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, prod, geometry_library=library)
            n = len(shape.geometry.faces) // 3
            reason = f"{cls}: create_shape succeeded standalone, {('empty' if n == 0 else 'non-empty')}"
            del shape
        except Exception as exc:
            reason = f"{cls}: {type(exc).__name__}"
        not_produced_reason[reason] = not_produced_reason.get(reason, 0) + 1
    # NOTE ON SCOPE: get_log() returns what the library has accumulated in this process,
    # not only what was produced after turn_on_detailed_logging(). The summary below
    # therefore covers the per-element pass above as well as this one. That is why a model
    # on which no element raised can still show logged errors: "Failed to convert" is
    # written for a sub-item and swallowed, while the element itself still produces
    # geometry. The counts are read that way in the results file.
    standalone_log = ios_wrapper.get_log()
    ios_wrapper.turn_off_detailed_logging()

    per_row.sort(key=lambda r: -r[2])
    dist = quantiles(times)
    under16 = sum(1 for t in times if t * 1000.0 < R01_PASS_MS)
    under100 = sum(1 for t in times if t * 1000.0 < R01_FAIL_MS)
    by_class: dict[str, list[float]] = {}
    for _eid, cls, dt in per_row:
        by_class.setdefault(cls, []).append(dt)
    del f
    return {
        "geometry_library": library,
        "elements_timed": len(times),
        "create_shape_raised": errors,
        "distribution": dist,
        "under_16ms": under16,
        "under_16ms_fraction": (under16 / len(times)) if times else 0.0,
        "under_100ms": under100,
        "under_100ms_fraction": (under100 / len(times)) if times else 0.0,
        "slowest_10": [{"express_id": e, "ifc_class": c, "ms": t * 1000.0}
                       for e, c, t in per_row[:10]],
        "median_ms_by_class": {
            c: {"n": len(v), "median_ms": statistics.median(v) * 1000.0,
                "max_ms": max(v) * 1000.0}
            for c, v in sorted(by_class.items(), key=lambda kv: -len(kv[1]))
        },
        "iterator_did_not_produce_by_class": dict(sorted(not_produced.items(),
                                                         key=lambda kv: -kv[1])),
        "iterator_did_not_produce_reason": dict(sorted(not_produced_reason.items(),
                                                       key=lambda kv: -kv[1])),
        "standalone_log_summary": summarise_log(standalone_log or ""),
        "note": "create_shape constructs a fresh kernel per call; the numbers therefore "
                "include per-call setup and overstate steady-state re-evaluation cost. "
                "Detailed logging is on only for the not-produced pass, never during a "
                "timed region, so the iteration log files in this directory are empty.",
    }


def find_wall(f: ifcopenshell.file):
    """The first IfcWall (or IfcWallStandardCase) with a Representation and a placement."""
    for cls in ("IfcWall", "IfcWallStandardCase"):
        for w in f.by_type(cls, include_subtypes=False):
            if w.Representation is not None and w.ObjectPlacement is not None:
                rp = w.ObjectPlacement
                if rp.is_a("IfcLocalPlacement") and rp.RelativePlacement.is_a("IfcAxis2Placement3D"):
                    return w
    return None


def translate_placement(f: ifcopenshell.file, element, dx: float) -> tuple[float, float, float]:
    """Translate the element's own IfcAxis2Placement3D location by dx along X.

    Rewrites the IfcCartesianPoint in place. `dx` is already in the file's length units.
    Returns the new coordinates.
    """
    placement = element.ObjectPlacement.RelativePlacement
    loc = placement.Location
    old = tuple(loc.Coordinates)
    new = (old[0] + dx, old[1], old[2] if len(old) > 2 else 0.0)
    loc.Coordinates = new
    return new


def length_unit_scale(f: ifcopenshell.file) -> float:
    """Return how many file length units make one metre."""
    import ifcopenshell.util.unit

    return 1.0 / ifcopenshell.util.unit.calculate_unit_scale(f)


def r01_edit_test(path: str, repeats: int, library: str, express_id: int | None,
                  label: str) -> dict:
    """The R-01 edit test.

    (a) single-element regeneration after an edit, via geom.create_shape(settings, element)
    (b) a full re-iteration of the same edited model, num_threads=32

    Each repeat re-opens the file, so the edit is applied to a fresh model every time
    and no shape or file object is reused across repeats.

    `express_id` None selects the first suitable IfcWall; otherwise the named element is
    used (so the worst case found in step 4 can be measured too).
    """
    single = []
    full = []
    info = {}
    for _ in range(repeats):
        f = ifcopenshell.open(path)
        settings = make_settings()
        if express_id is None:
            element = find_wall(f)
        else:
            element = f.by_id(express_id)
        if element is None or element.ObjectPlacement is None:
            return {"error": f"no suitable element for {label}"}
        rp = element.ObjectPlacement
        if not (rp.is_a("IfcLocalPlacement")
                and rp.RelativePlacement.is_a("IfcAxis2Placement3D")):
            return {"error": f"{label}: element {element.id()} has no IfcAxis2Placement3D"}
        scale = length_unit_scale(f)
        # warm: produce the shape once before the edit, so the measured call is the
        # regeneration and not a first touch of lazily built schema machinery.
        warm = ifcopenshell.geom.create_shape(settings, element, geometry_library=library)
        del warm
        new_coords = translate_placement(f, element, 1.0 * scale)
        t0 = time.perf_counter()
        shape = ifcopenshell.geom.create_shape(settings, element, geometry_library=library)
        single.append(time.perf_counter() - t0)
        verts = list(shape.geometry.verts)
        info = {
            "label": label,
            "global_id": element.GlobalId,
            "ifc_class": element.is_a(),
            "express_id": element.id(),
            "length_units_per_metre": scale,
            "new_placement_coordinates": list(new_coords),
            "triangles_after_edit": len(shape.geometry.faces) // 3,
            "bbox_after_edit": list(bbox(verts)),
        }
        del shape
        # (b) full re-iteration of the edited model, in the same process, same file object
        t0 = time.perf_counter()
        it = ifcopenshell.geom.iterator(settings, f, num_threads=32,
                                        geometry_library=library)
        n = 0
        if it.initialize():
            while True:
                it.get()
                n += 1
                if not it.next():
                    break
        full.append(time.perf_counter() - t0)
        info["full_reiteration_elements"] = n
        del it, f
    return {
        "element": info,
        "geometry_library": library,
        "single_element_seconds": single,
        "single_element_median_ms": statistics.median(single) * 1000.0,
        "full_reiteration_seconds": full,
        "full_reiteration_median_s": statistics.median(full),
        "ratio_full_over_single": statistics.median(full) / statistics.median(single),
    }


def edit_visibility(path: str, library: str) -> dict:
    """Does an in-memory placement edit actually reach the geometry create_shape returns?

    Three cases, each on its own freshly opened file:
      ref    no edit; create_shape(wall)
      cold   edit first, then the FIRST create_shape(wall) on that file
      warm   create_shape(wall), then edit, then create_shape(wall) again
    Reported as the x of the element's bounding box, so a 1 m translation shows as 1.0.
    The same probe is run against web-ifc by webifc_driver.mjs, so the two are comparable.
    """
    out = {}
    settings = make_settings()

    f = ifcopenshell.open(path)
    wall = find_wall(f)
    wid = wall.id()
    out["express_id"] = wid
    out["global_id"] = wall.GlobalId
    ref = ifcopenshell.geom.create_shape(settings, wall, geometry_library=library)
    out["ref_xmin"] = bbox(list(ref.geometry.verts))[0]
    del ref, wall, f

    f = ifcopenshell.open(path)
    wall = f.by_id(wid)
    scale = length_unit_scale(f)
    translate_placement(f, wall, 1.0 * scale)
    cold = ifcopenshell.geom.create_shape(settings, wall, geometry_library=library)
    out["cold_xmin"] = bbox(list(cold.geometry.verts))[0]
    del cold, wall, f

    f = ifcopenshell.open(path)
    wall = f.by_id(wid)
    first = ifcopenshell.geom.create_shape(settings, wall, geometry_library=library)
    del first
    translate_placement(f, wall, 1.0 * length_unit_scale(f))
    warm = ifcopenshell.geom.create_shape(settings, wall, geometry_library=library)
    out["warm_xmin"] = bbox(list(warm.geometry.verts))[0]
    del warm, wall, f

    out["expected_shift_m"] = 1.0
    out["cold_shift"] = out["cold_xmin"] - out["ref_xmin"]
    out["warm_shift"] = out["warm_xmin"] - out["ref_xmin"]
    return out


# ---------------------------------------------------------------- main


def write_table(rows: list[dict], name: str, library: str) -> str:
    csv_path = os.path.join(RESULTS, f"ifcopenshell-{library}_{name}_elements.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["guid", "ifc_class", "express_id", "triangles",
                    "vertices", "volume", "xmin", "ymin", "zmin",
                    "xmax", "ymax", "zmax"])
        for row in rows:
            w.writerow([row["guid"], row["ifc_class"], row["express_id"],
                        row["triangles"], row["vertices"],
                        f"{row['volume']:.9g}",
                        *[f"{v:.9g}" for v in row["bbox"]]])
    return os.path.relpath(csv_path, HERE).replace("\\", "/")


def subprocess_phase(model: str, phase: str, library: str, threads: int,
                     repeats: int) -> dict:
    """Run one measurement phase in a fresh child process of this same script.

    Needed because building iterators for more than one geometry library inside a single
    process crashes the process (observed: opencascade runs, then the first cgal iterator
    in the same process dies without a Python traceback). Running each library in its own
    process also keeps each configuration's peak working set its own number.
    """
    cmd = [sys.executable, os.path.abspath(__file__), "--model", model,
           "--phase", phase, "--library", library, "--threads", str(threads),
           "--repeats", str(repeats)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    return {
        "crashed": True,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-1500:],
        "command": " ".join(cmd[1:]),
    }


def run_phase(args) -> None:
    """The child-process entry point: one phase, one geometry library, JSON on stdout."""
    path = MODELS[args.model]
    if args.phase == "iterate":
        times = []
        stats: dict = {}
        for _ in range(args.repeats):
            secs, st = iterate_timed(path, args.threads, args.library)
            times.append(secs)
            stats = st
        log = stats["log"] or ""
        # Detailed logging is off during timed runs (see main), so this log is normally
        # empty. An empty log file is not written -- there is nothing in it to commit.
        log_rel = None
        if log.strip():
            log_path = os.path.join(
                RESULTS, f"ifcopenshell_{args.model}_{args.library}_t{args.threads}.log")
            with open(log_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(log)
            log_rel = os.path.relpath(log_path, HERE).replace("\\", "/")
        out = {
            "geometry_library": args.library,
            "num_threads": args.threads,
            "seconds": times,
            "median_s": statistics.median(times),
            "elements_produced": stats["produced"],
            "initialized": stats["initialized"],
            "had_error_processing_elements": stats["had_error_processing_elements"],
            "log_file": log_rel,
            "log_empty_because": None if log_rel else
                "detailed logging is off during timed runs; see per_element."
                "standalone_log_summary for the attributed log",
            "log_summary": summarise_log(log),
            "process_peak_wset_mb": peak_wset_mb(),
        }
    elif args.phase == "collect":
        rows, _st = iterate_collect(path, args.threads, args.library)
        out = {
            "geometry_library": args.library,
            "file": write_table(rows, args.model, args.library),
            "rows": len(rows),
            "rows_with_zero_triangles": sum(1 for r in rows if r["triangles"] == 0),
            "express_ids": [r["express_id"] for r in rows],
        }
    else:
        raise SystemExit(f"unknown phase {args.phase}")
    print("JSON:" + json.dumps(out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--phase", default=None, choices=["iterate", "collect"],
                    help="child-process entry point; not used when running by hand")
    ap.add_argument("--library", default="opencascade")
    ap.add_argument("--threads", type=int, default=32)
    args = ap.parse_args()

    if args.phase:
        os.makedirs(RESULTS, exist_ok=True)
        run_phase(args)
        return

    # Detailed logging is deliberately NOT turned on globally: it makes the parser write
    # progress to stdout and adds logging I/O inside every region we time. It is turned on
    # only inside the untimed failure-attribution pass (see per_element_create_shape).
    os.makedirs(RESULTS, exist_ok=True)
    name = args.model
    path = MODELS[name]
    import typing
    out = {
        "driver": "ifcopenshell_driver.py",
        "model": name,
        "hardware": hardware(),
        "versions": {
            "ifcopenshell_python": ifcopenshell.version,
            "ifcopenshell_native": ios_wrapper.version(),
            "psutil": psutil.__version__,
        },
        "geometry_libraries_available": list(
            typing.get_args(ifcopenshell.geom.GEOMETRY_LIBRARY)),
        "settings": settings_dump(make_settings()),
        "repeats": args.repeats,
        "r01_thresholds_ms": {"pass_under": R01_PASS_MS, "fail_over": R01_FAIL_MS},
    }

    print(f"== {name}", flush=True)
    m: dict = {"path": os.path.relpath(path, REPO).replace("\\", "/"),
               "size_bytes": os.path.getsize(path)}

    parse_times, info = time_parse(path, args.repeats)
    m["file"] = info
    m["parse_seconds"] = parse_times
    m["parse_median_s"] = statistics.median(parse_times)
    print(f"   parse median {m['parse_median_s']:.3f} s", flush=True)

    m["reference_counts"] = count_geometric_products(path)

    runs = [("opencascade", 1), ("opencascade", 32)] + [(lib, 32) for lib in LIBRARIES
                                                        if lib != "opencascade"]
    m["iteration"] = {}
    for library, threads in runs:
        r = subprocess_phase(name, "iterate", library, threads, args.repeats)
        m["iteration"][f"{library}_t{threads}"] = r
        if r.get("crashed"):
            print(f"   iterate {library} t={threads}: CRASHED "
                  f"(returncode {r['returncode']})", flush=True)
        else:
            print(f"   iterate {library} t={threads}: median {r['median_s']:.3f} s "
                  f"({r['elements_produced']} elements)", flush=True)

    # untimed collection passes, each in its own process
    m["element_tables"] = {}
    produced_ids: list[int] = []
    for library in ELEMENT_TABLE_LIBRARIES:
        r = subprocess_phase(name, "collect", library, 32, 1)
        if library == "opencascade":
            produced_ids = r.get("express_ids", [])
        r.pop("express_ids", None)
        m["element_tables"][library] = r
        print(f"   collected {r.get('rows')} rows for {library}", flush=True)

    print("   per-element create_shape ...", flush=True)
    m["per_element"] = per_element_create_shape(path, produced_ids, "opencascade")
    d = m["per_element"]["distribution"]
    print(f"   per-element median {d['median_ms']:.2f} ms, p95 {d['p95_ms']:.2f} ms, "
          f"max {d['max_ms']:.2f} ms; {m['per_element']['under_16ms']}/"
          f"{m['per_element']['elements_timed']} under 16 ms", flush=True)

    print("   R-01 edit test ...", flush=True)
    m["r01_first_wall"] = r01_edit_test(path, args.repeats, "opencascade", None,
                                        "first IfcWall with an IfcAxis2Placement3D")
    slowest = m["per_element"]["slowest_10"]
    worst_id = slowest[0]["express_id"] if slowest else None
    m["r01_slowest_element"] = r01_edit_test(
        path, args.repeats, "opencascade", worst_id,
        "the element with the largest create_shape time in the per-element pass")
    print(f"   R-01 first wall {m['r01_first_wall']['single_element_median_ms']:.2f} ms, "
          f"full {m['r01_first_wall']['full_reiteration_median_s']:.3f} s", flush=True)
    if "error" not in m["r01_slowest_element"]:
        print(f"   R-01 slowest element "
              f"{m['r01_slowest_element']['single_element_median_ms']:.2f} ms", flush=True)

    m["edit_visibility_probe"] = edit_visibility(path, "opencascade")
    print(f"   edit visibility: cold {m['edit_visibility_probe']['cold_shift']}, "
          f"warm {m['edit_visibility_probe']['warm_shift']}", flush=True)

    m["process_peak_wset_mb"] = peak_wset_mb()
    out["result"] = m

    dest = args.out or f"ifcopenshell_{name}.json"
    with open(os.path.join(RESULTS, dest), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(f"wrote results/{dest}")


if __name__ == "__main__":
    main()
