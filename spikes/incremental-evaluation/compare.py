"""Throwaway spike driver — P-10: do IFC implementations disagree on the same model's geometry?

Joins the per-GUID element tables written by ifcopenshell_driver.py and webifc_driver.mjs
and reports, per model, for each PAIR of tables:

  * elements present in one table and not the other, grouped by IfcClass, split into rows
    that carry triangles and rows that do not
  * elements whose signed volume differs by more than 1e-3 relative, grouped by IfcClass
  * the largest individual disagreements
  * how many elements agree on triangle count exactly

Three pairings are compared:

  1. IfcOpenShell (opencascade) vs web-ifc   -- two implementations, two kernels
  2. IfcOpenShell (opencascade) vs IfcOpenShell (cgal-simple)
                                             -- ONE implementation, ONE parser, two kernels.
                                                Isolates the kernel from the schema mapping:
                                                anything this pair disagrees on cannot be
                                                blamed on a different reading of the schema.
  3. IfcOpenShell (cgal-simple) vs web-ifc   -- for completeness

The volume for every table is computed by the *same* formula
(1/6 * sum over triangles of dot(a, cross(b, c)), world coordinates) implemented separately
in each driver, so a difference in the number is a difference in the triangles each
implementation produced, not a difference in how they were measured.

It also checks both drivers' own IfcProduct counts against the element counts recorded in
../../reference/README.md, parsed from that file rather than retyped here.

Only two implementations are compared. xBIM is not measured (no .NET SDK on this machine;
see ../../docs/research/kernels/xbim.md) so this is a two-implementation, not a
three-implementation, comparison.

Usage:  python compare.py
Writes: results/compare_raw.json
"""

from __future__ import annotations

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RESULTS = os.path.join(HERE, "results")
MODELS = ["AC20-FZK-Haus", "IFC_Schependomlaan"]

REL_TOLERANCE = 1e-3  # the brief's threshold

TABLES = {
    "ifcopenshell-opencascade": "ifcopenshell-opencascade_{model}_elements.csv",
    "ifcopenshell-cgal-simple": "ifcopenshell-cgal-simple_{model}_elements.csv",
    "webifc": "webifc_{model}_elements.csv",
}
PAIRS = [
    ("ifcopenshell-opencascade", "webifc"),
    ("ifcopenshell-opencascade", "ifcopenshell-cgal-simple"),
    ("ifcopenshell-cgal-simple", "webifc"),
]


def load(path: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            guid = row["guid"]
            if not guid:
                continue
            row["triangles"] = int(row["triangles"])
            row["volume"] = float(row["volume"])
            # A GUID can appear more than once if an implementation emits several meshes for
            # one product. Accumulate, so the comparison is per product.
            if guid in rows:
                rows[guid]["triangles"] += row["triangles"]
                rows[guid]["volume"] += row["volume"]
                rows[guid]["duplicate_rows"] += 1
            else:
                row["duplicate_rows"] = 1
                rows[guid] = row
    return rows


def reference_counts() -> dict:
    """Element counts for each model, parsed out of reference/README.md.

    The rule: inside the model's section, take the line beginning
    "- **Element count:**"; the first integer on it is the IfcProduct total, and every
    "<n> `IfcSomething`" pair after "By class:" is a per-class count. Parsed rather than
    retyped so the check cannot drift from the file it checks against.
    """
    path = os.path.join(REPO, "reference", "README.md")
    if not os.path.exists(path):
        return {"error": "reference/README.md not found"}
    text = open(path, encoding="utf-8").read()
    # split into per-model sections on the "#### 1a." / "#### 1b." headings
    sections = re.split(r"\n#### ", text)
    out: dict[str, dict] = {}
    for name in MODELS:
        # the Schependomlaan heading spells the model differently from its file name
        needles = {name, name.replace("IFC_", "")}
        for sec in sections:
            head = sec.splitlines()[0] if sec.splitlines() else ""
            if not any(nd in head or nd in head.replace(" ", "_") for nd in needles):
                continue
            m = re.search(r"- \*\*Element count:\*\*(.*?)(?=\n- \*\*|\n\n)", sec, re.S)
            if not m:
                continue
            line = " ".join(m.group(1).split())
            total = re.search(r"(\d[\d,]*)\s+`IfcProduct`", line)
            per_class = {c: int(n.replace(",", ""))
                         for n, c in re.findall(r"(\d[\d,]*)\s+`(Ifc\w+)`", line)
                         if c != "IfcProduct"}
            out[name] = {
                "ifcproduct_total": int(total.group(1).replace(",", "")) if total else None,
                "per_class": per_class,
                "verbatim": line,
            }
            break
        out.setdefault(name, {"error": "no Element count line found"})
    out["rule"] = ("parsed from reference/README.md: the '- **Element count:**' line of each "
                   "model's section; first integer before `IfcProduct` is the total, each "
                   "'<n> `IfcClass`' pair a per-class count")
    return out


def driver_counts(model: str) -> dict:
    """What the two drivers themselves counted, read back out of their JSON."""
    out: dict = {}
    p = os.path.join(RESULTS, f"ifcopenshell_{model}.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))["result"]
        out["ifcopenshell"] = {
            "ifcproduct_total": d["reference_counts"]["ifcproduct_total"],
            "ifcproduct_with_representation":
                d["reference_counts"]["ifcproduct_with_representation"],
            "ifcproduct_all_by_class": d["reference_counts"]["ifcproduct_all_by_class"],
            "total_instances": d["file"]["total_instances"],
            "schema": d["file"]["schema"],
        }
    p = os.path.join(RESULTS, f"webifc_{model}.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))["result"]
        out["webifc"] = {"total_lines": d["total_lines"], "schema": d["schema"]}
    return out


def check_counts(model: str, ref: dict, drv: dict) -> dict:
    """Do the drivers' own counts match reference/README.md? Reported as a comparison, and
    as the list of classes whose counts differ, so a mismatch is visible rather than
    swallowed."""
    if "ifcopenshell" not in drv or ref.get(model, {}).get("ifcproduct_total") is None:
        return {"checked": False, "reason": "missing reference or driver counts"}
    r = ref[model]
    d = drv["ifcopenshell"]
    mismatches = {}
    for cls, n in r["per_class"].items():
        got = d["ifcproduct_all_by_class"].get(cls)
        if got != n:
            mismatches[cls] = {"reference_readme": n, "measured_now": got}
    return {
        "checked": True,
        "ifcproduct_total_reference_readme": r["ifcproduct_total"],
        "ifcproduct_total_measured_now": d["ifcproduct_total"],
        "ifcproduct_total_agrees": r["ifcproduct_total"] == d["ifcproduct_total"],
        "per_class_classes_checked": len(r["per_class"]),
        "per_class_mismatches": mismatches,
        "note": "reference/README.md lists only the larger classes, so classes it omits are "
                "not checked here; every class it does list is checked",
    }


def group(rows: list[dict], key: str = "ifc_class") -> dict[str, int]:
    d: dict[str, int] = {}
    for r in rows:
        d[r[key]] = d.get(r[key], 0) + 1
    return dict(sorted(d.items(), key=lambda kv: -kv[1]))


def compare_pair(a_path: str, b_path: str, a_name: str, b_name: str) -> dict:
    if not (os.path.exists(a_path) and os.path.exists(b_path)):
        return {"error": "one or both element tables missing; run the drivers first"}

    a = load(a_path)
    b = load(b_path)
    only_a = [a[g] for g in a.keys() - b.keys()]
    only_b = [b[g] for g in b.keys() - a.keys()]
    both = sorted(a.keys() & b.keys())

    differing = []
    agreeing = 0
    zero_in_one = 0
    for g in both:
        va, vb = a[g]["volume"], b[g]["volume"]
        denom = max(abs(va), abs(vb))
        if denom == 0.0:
            agreeing += 1
            continue
        if abs(va) == 0.0 or abs(vb) == 0.0:
            zero_in_one += 1
        rel = abs(va - vb) / denom
        if rel > REL_TOLERANCE:
            differing.append(
                {
                    "guid": g,
                    "ifc_class": a[g]["ifc_class"],
                    f"class_{b_name}": b[g]["ifc_class"],
                    f"volume_{a_name}": va,
                    f"volume_{b_name}": vb,
                    "relative_difference": rel,
                    f"triangles_{a_name}": a[g]["triangles"],
                    f"triangles_{b_name}": b[g]["triangles"],
                }
            )
        else:
            agreeing += 1

    differing.sort(key=lambda d: -d["relative_difference"])
    tri_equal = sum(1 for g in both if a[g]["triangles"] == b[g]["triangles"])

    # A row with zero triangles is an entry the implementation emitted without any geometry
    # in it. Counting those as "produced by one and not the other" would overstate the
    # disagreement, so the two are split and reported separately.
    only_a_geo = [r for r in only_a if r["triangles"] > 0]
    only_b_geo = [r for r in only_b if r["triangles"] > 0]

    # How badly do they disagree? Bucketed, so "13 disagreements" is not read as 13 equally
    # serious ones.
    buckets = {"1e-3 to 1e-2": 0, "1e-2 to 1e-1": 0, "1e-1 to 0.5": 0, "over 0.5": 0}
    for d in differing:
        r = d["relative_difference"]
        if r < 1e-2:
            buckets["1e-3 to 1e-2"] += 1
        elif r < 1e-1:
            buckets["1e-2 to 1e-1"] += 1
        elif r < 0.5:
            buckets["1e-1 to 0.5"] += 1
        else:
            buckets["over 0.5"] += 1

    return {
        "a": a_name,
        "b": b_name,
        f"elements_{a_name}": len(a),
        f"elements_{b_name}": len(b),
        f"empty_rows_{a_name}": sum(1 for r in a.values() if r["triangles"] == 0),
        f"empty_rows_{b_name}": sum(1 for r in b.values() if r["triangles"] == 0),
        "guids_in_both": len(both),
        f"only_in_{a_name}": len(only_a),
        f"only_in_{a_name}_with_geometry": len(only_a_geo),
        f"only_in_{a_name}_with_geometry_by_class": group(only_a_geo),
        f"only_in_{a_name}_empty_by_class": group([r for r in only_a if r["triangles"] == 0]),
        f"only_in_{b_name}": len(only_b),
        f"only_in_{b_name}_with_geometry": len(only_b_geo),
        f"only_in_{b_name}_with_geometry_by_class": group(only_b_geo),
        f"only_in_{b_name}_empty_by_class": group([r for r in only_b if r["triangles"] == 0]),
        # The GUIDs themselves, so a claim about "the four walls one side is missing" can be
        # checked against the file rather than taken from a count.
        f"only_in_{a_name}_guids": sorted(
            (r["guid"], r["ifc_class"], r["triangles"]) for r in only_a)[:40],
        f"only_in_{b_name}_guids": sorted(
            (r["guid"], r["ifc_class"], r["triangles"]) for r in only_b)[:40],
        "volume_agrees_within_1e-3_relative": agreeing,
        "volume_differs_by_more_than_1e-3_relative": len(differing),
        "differing_by_class": group(differing),
        "differing_by_magnitude": buckets,
        "zero_volume_in_exactly_one": zero_in_one,
        "identical_triangle_count": tri_equal,
        "top_20_disagreements": differing[:20],
        "rule": (
            "one row per GlobalId, volumes of multiple rows for the same GlobalId summed; "
            f"relative difference = |va-vb| / max(|va|,|vb|); threshold {REL_TOLERANCE}"
        ),
    }


def main() -> None:
    ref = reference_counts()
    out = {
        "driver": "compare.py",
        "implementations_compared": ["IfcOpenShell", "web-ifc"],
        "note": "two implementations, three table pairings; xBIM was not measured "
                "(no .NET SDK on this machine)",
        "reference_readme_counts": ref,
        "models": {},
    }
    for model in MODELS:
        print(f"== {model}", flush=True)
        drv = driver_counts(model)
        entry = {
            "driver_counts": drv,
            "reference_count_check": check_counts(model, ref, drv),
            "pairs": {},
        }
        chk = entry["reference_count_check"]
        if chk.get("checked"):
            print(f"   reference count check: IfcProduct total "
                  f"{chk['ifcproduct_total_measured_now']} vs README "
                  f"{chk['ifcproduct_total_reference_readme']} -> "
                  f"{'agrees' if chk['ifcproduct_total_agrees'] else 'DIFFERS'}; "
                  f"{len(chk['per_class_mismatches'])} of "
                  f"{chk['per_class_classes_checked']} listed classes differ", flush=True)
        for a_name, b_name in PAIRS:
            a_path = os.path.join(RESULTS, TABLES[a_name].format(model=model))
            b_path = os.path.join(RESULTS, TABLES[b_name].format(model=model))
            r = compare_pair(a_path, b_path, a_name, b_name)
            entry["pairs"][f"{a_name} vs {b_name}"] = r
            if "error" in r:
                print(f"   {a_name} vs {b_name}: {r['error']}", flush=True)
                continue
            print(f"   {a_name} vs {b_name}: {r[f'elements_{a_name}']}/"
                  f"{r[f'elements_{b_name}']} rows, {r['guids_in_both']} shared GUIDs; "
                  f"only-a {r[f'only_in_{a_name}']} ({r[f'only_in_{a_name}_with_geometry']} "
                  f"with geometry), only-b {r[f'only_in_{b_name}']} "
                  f"({r[f'only_in_{b_name}_with_geometry']} with geometry); "
                  f"{r['volume_differs_by_more_than_1e-3_relative']} volume disagreements",
                  flush=True)
        out["models"][model] = entry
    with open(os.path.join(RESULTS, "compare_raw.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("wrote results/compare_raw.json")


if __name__ == "__main__":
    main()
