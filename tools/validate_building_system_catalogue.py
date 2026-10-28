#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Validate authoring data, not building design. No application rules run in Python."""
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "localisation/nl/building-systems/catalogue.json"
CAPABILITIES = set("layers opening-regions prefab-partition roll-courses semantic-overrides "
                   "planar-domain independent-grid-members connection-intents cell-substitution "
                   "point-support nested-systems explicit-axes ordinary-linear-elements "
                   "staggered-grid bonded-corners unit-cutting supplier-cut-constraints "
                   "polygon-clipping stock-ledger edge-aware-reuse curved-offsets "
                   "polygon-cutting parallel-grid".split())
RULES = set("supported-board-edges rectangular-opening-regions prefab-max-length "
            "sealed-membrane-laps insulation-excludes-frame layer-suppression-dependencies "
            "offset-lining-seams head-movement-clearance main-runner-continuity "
            "cross-tee-termination hanger-support compatible-panel-edge fixture-load-and-access "
            "minimum-border-width profile-role-orientation head-jamb-sill-water-path "
            "glazing-support opening-sweep handedness compatible-leaf-ports brick-plus-joint-pitch "
            "bonded-returns movement-joints supported-head batch-consistency "
            "supplier-bond-and-bearings lifting-and-installation cut-restrictions "
            "manufacturing-size-vs-module edge-aware-remnant-reuse batch-calibre-direction "
            "minimum-cut-width border-offset-validity movement-joint-continuity "
            "support-and-fixings ventilation-continuity panel-expansion grain-and-face-direction "
            "bearing-and-span opening-trimming supplier-widths-only span-and-bearing "
            "strand-and-web-exclusions engineered-cuts-only".split())
COVERAGE = set("roll-courses linear-repetition cavity-fill rectangular-stock point-support "
               "linear-network cell-fill nested-cells perimeter-network joint-fill "
               "continuous-coating linear-stock".split())


def validate(data):
    errors = []

    def require(condition, location, message):
        if not condition:
            errors.append(f"{location}: {message}")

    def keys(value, required, location):
        if not isinstance(value, dict):
            errors.append(f"{location}: expected object")
            return False
        require(required <= value.keys(), location, f"missing fields {sorted(required - value.keys())}")
        return required <= value.keys()

    def unique(records, location):
        ids = [r.get("id") for r in records if isinstance(r, dict)]
        require(len(ids) == len(records), location, "all entries must be objects")
        require(all(isinstance(i, str) and re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", i) for i in ids), location, "invalid ID")
        require(len(set(ids)) == len(ids), location, "duplicate IDs")
        return set(ids)

    def dimensions(value, location):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("_mm") and child is not None:
                    values = child if isinstance(child, list) else [child]
                    require(bool(values) and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in values), f"{location}.{key}", "dimensions must be finite and positive, or null")
                dimensions(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                dimensions(child, f"{location}[{index}]")

    required = {"schema_version", "catalogue_id", "version", "units", "language", "status", "sources", "families", "components", "recipes"}
    if not keys(data, required, "catalogue"):
        return errors
    require(data["schema_version"] == 1 and data["units"] == "mm", "catalogue", "unsupported schema/units")
    require(data["status"] == "authoring-data-not-runtime-imported", "catalogue", "runtime activation requires a separate importer contract")
    for field in ("sources", "recipes", "components"):
        if not isinstance(data[field], list):
            errors.append(f"{field}: expected array")
            return errors
    if not isinstance(data["families"], dict):
        return errors + ["families: expected object"]
    source_ids = unique(data["sources"], "sources")
    unique(data["recipes"], "recipes")
    unique(data["components"], "components")
    for source in data["sources"]:
        if not keys(source, {"id", "url", "title", "locator", "retrieved", "scope"}, "source"):
            continue
        require(source["url"].startswith("https://"), source["id"], "source must have HTTPS URL")
        require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["retrieved"])), source["id"], "retrieval date required")
    for name, family in data["families"].items():
        if not keys(family, {"layers", "pattern", "boundaries", "openings", "substitutions", "stock", "rules", "inputs", "sources"}, name):
            continue
        require(set(family["sources"]) <= source_ids, name, "unknown evidence reference")
        require(set(family["rules"]) <= RULES, name, "unknown rule")
        require(bool(family["inputs"]), name, "unresolved project inputs must be explicit")
        layers = family["layers"]
        layer_keys = [item.get("key") for item in layers]
        require(len(set(layer_keys)) == len(layer_keys), name, "duplicate layer keys")
        for item in layers:
            if not keys(item, {"key", "coverage", "material", "thickness_mm"}, name):
                continue
            require(item["coverage"] in COVERAGE, name, "unknown layer coverage")
            if "shares_zone_with" in item:
                require(item["shares_zone_with"] in layer_keys and item["shares_zone_with"] != item["key"], name, "invalid shared-zone reference")
    for component in data["components"]:
        keys(component, {"id", "kind", "ports", "requires"}, "component")
    for item in data["recipes"]:
        required = {"id", "version", "label_nl", "family", "validation_status", "host_roles", "parameters", "requires_capabilities", "performance_claims", "default_basis", "manufacturer_system"}
        if not keys(item, required, "recipe"):
            continue
        label = item["id"]
        require(item["family"] in data["families"], label, "unknown family")
        require(item["validation_status"] == "concept" and item["manufacturer_system"] is False and item["performance_claims"] == [], label, "concept recipes cannot carry manufacturer/performance approval")
        require(bool(item["host_roles"]) and set(item["host_roles"]) <= {"wall", "floor", "roof", "ceiling", "opening"}, label, "invalid host role")
        require(set(item["requires_capabilities"]) <= CAPABILITIES, label, "unknown capability")
        p = item["parameters"]
        if item["family"] == "tile" and p.get("actual_tile_mm") is not None and p.get("joint_mm") is not None:
            require(all(math.isclose(a + p["joint_mm"], b, abs_tol=1e-8) for a, b in zip(p["actual_tile_mm"], p["module_mm"], strict=True)), label, "actual tile + joint must equal module")
        if item["family"] == "masonry":
            require(math.isclose(p["unit_mm"][0] + p["head_joint_mm"], p["horizontal_pitch_mm"]), label, "horizontal brick pitch mismatch")
            require(math.isclose(p["unit_mm"][2] + p["bed_joint_mm"], p["vertical_pitch_mm"]), label, "vertical brick pitch mismatch")
        if "insulation_depth_mm" in p:
            require(p["insulation_depth_mm"] == p["stud_depth_mm"], label, "example insulation and framing zone depths differ")
    dimensions(data, "catalogue")
    return errors


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    try:
        data = json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite {value}")))
        errors = validate(data)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Invalid catalogue: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(data['recipes'])} concepts, {len(data['families'])} families, {len(data['sources'])} evidence references; authoring data only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
