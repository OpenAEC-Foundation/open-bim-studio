"""Rebuild the KIT FZK-Haus (AC20-FZK-Haus.ifc) in Open BIM Studio through its MCP server,
using the UI's own tools: ribbon buttons, clicks in the plan and the properties panel, then
draw it: rooms, exterior dimensions, technical floor plans on A3 sheets exported as PDF.

    OBS_API=api-folder OBS_OUT=fzk-out python3 rebuild.py [all | STEP ...]

Steps run in the order of ALL (see STEPS). Prints each MCP call and the state after it.
See README.md.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcp_client as mcp  # noqa: E402

# Where plan.json is read and the drawings are written.
OUT = os.path.abspath(os.environ.get("OBS_OUT", "fzk-out"))
ESCAPE = 256
EXT, INT = 0.30, 0.24
CLIENT = None


def call(name, arguments=None, quiet=False):
    text, _ = CLIENT.call(name, arguments or {})
    try:
        data = json.loads(text)
    except ValueError:
        data = {"text": text}
    if not quiet:
        brief = {k: data.get(k) for k in ("ok", "id", "message", "selection", "walls", "slabs", "openings",
                                          "levels", "storey", "tool", "error") if k in data}
        print("  %s %s -> %s" % (name, json.dumps(arguments or {}), json.dumps(brief)))
    return data


def press(label):
    """A ribbon button, run by the window on its next frame: the state is read after it."""
    import time
    call("press_button", {"label": label}, quiet=True)
    time.sleep(0.2)
    data = call("state", quiet=True)
    print("  press %s -> %s" % (label, data.get("message")))
    return data


def click(x, y):
    return call("click", {"x": x, "y": y})


def escape():
    return call("key", {"code": ESCAPE})


def prop(code, value):
    return call("set_property", {"code": code, "value": str(value)})


def row(label):
    for entry in call("properties", quiet=True)["rows"]:
        if entry["label"] == label:
            return entry
    return None


def use_type(tab, type_id):
    """Type `type_id` as the drawing default. Escape first: apply_type also gives the type to a
    compatible selection, so a floor still selected after it was drawn would become a roof."""
    escape()
    return call("apply_type", {"tab": tab, "id": type_id})


def type_named(tab, name):
    for entry in call("list_types", {"tab": tab}, quiet=True)["types"]:
        if entry["name"] == name:
            return entry
    return None


def made_type(tab, base_id, name, thickness=None):
    """A copy of type `base_id` named `name` (its one layer `thickness` thick), made once."""
    found = type_named(tab, name)
    if found:
        return found["id"]
    new_id = call("duplicate_type", {"tab": tab, "id": base_id})["id"]
    call("set_type_field", {"tab": tab, "id": int(new_id), "field": 0, "value": name})
    if thickness is not None:  # project units: millimetres
        call("set_type_field", {"tab": tab, "id": int(new_id), "field": 2, "value": str(thickness), "layer": 0})
    return int(new_id)


def step_types():
    ext = type_named(0, "Metselwerk-spouw-isolatie-kalkzandsteen 300")["id"]
    made_type(0, ext, "FZK Aussenwand 300")
    made_type(0, type_named(0, "Kalkzandsteen 214")["id"], "FZK Innenwand 240", 240)
    made_type(1, type_named(1, "Beton 200")["id"], "FZK Decke 200")
    # 200 mm across the slope is 231 mm upright at 30 degrees, as the IFC's 0.2309 extrusion.
    made_type(2, type_named(2, "Isolatie-hout 200")["id"], "FZK Dach 230", 181)
    for tab in range(4, 9):
        print("tab", tab, [(t["id"], t["name"], t["width"], t["depth"], t["sill"]) for t in
                           call("list_types", {"tab": tab}, quiet=True)["types"]][:12])


def level_ids():
    levels = call("elements", quiet=True).get("levels", [])
    return levels


def step_levels():
    # Erdgeschoss at 0.00 with a 2.70 m storey, Dachgeschoss at +2.70 up to the ridge.
    levels = level_ids()
    if len(levels) < 2:
        press("Level")
        levels = level_ids()
    ground, roof = sorted(levels, key=lambda entry: entry["elevation"])[:2]
    call("select", {"id": ground["id"]})
    prop(283, "Erdgeschoss")
    prop(10, "2700")
    call("select", {"id": roof["id"]})
    prop(283, "Dachgeschoss")
    prop(9, "2700")
    prop(10, "3400")
    print(json.dumps(level_ids()))
    call("select", {"id": ground["id"]})


def go_to_storey(name):
    """Page Down or Page Up, as typed, until the active storey is `name` (never past the top,
    where Page Up adds a level)."""
    order = [entry["name"] for entry in sorted(level_ids(), key=lambda entry: entry["elevation"])]
    for _ in range(len(order)):
        current = call("state", quiet=True)["storey"]
        if current == name:
            return
        call("key", {"code": 267 if order.index(name) < order.index(current) else 266})
    if call("state", quiet=True)["storey"] != name:
        raise RuntimeError("storey %s not reached" % name)


def wall_chain(points):
    press("Wall")
    for x, y in points:
        click(x, y)
    escape()


def use_wall_type(name):
    use_type(0, type_named(0, name)["id"])


def step_walls_eg():
    go_to_storey("Erdgeschoss")
    use_wall_type("FZK Aussenwand 300")
    wall_chain([(0.15, 0.15), (11.85, 0.15), (11.85, 9.85), (0.15, 9.85), (0.15, 0.15)])
    use_wall_type("FZK Innenwand 240")
    wall_chain([(7.53, 9.85), (7.53, 4.13), (11.85, 4.13)])
    wall_chain([(3.92, 9.85), (3.92, 5.87)])
    wall_chain([(0.15, 5.87), (7.53, 5.87)])
    wall_chain([(0.15, 4.13), (3.80, 4.13)])
    call("state")


def step_fix_interior():
    innen = type_named(0, "FZK Innenwand 240")["id"]
    call("set_type_field", {"tab": 0, "id": innen, "field": 2, "value": "240", "layer": 0})
    for wall in call("elements", quiet=True)["walls"]:
        if wall["type"] == "FZK Innenwand 240" and wall["storeyId"] == 1:
            call("select", {"id": wall["id"]})
            prop(1, "2500")
    escape()


def sketch_rectangle_floor(type_name, x1, y1, x2, y2):
    use_type(1, type_named(1, type_name)["id"])
    escape()
    press("Floor")
    call("key", {"code": 82})  # R: rectangle
    click(x1, y1)
    click(x2, y2)
    return call("key", {"code": 258})  # Tab: finish the sketch


def step_floor_eg():
    go_to_storey("Erdgeschoss")
    sketch_rectangle_floor("FZK Decke 200", 0.0, 0.0, 12.0, 10.0)


def step_floor_dg():
    go_to_storey("Dachgeschoss")
    sketch_rectangle_floor("FZK Decke 200", 0.1, 0.1, 11.9, 9.9)


def roof_plane(x1, y1, x2, y2, pitch, toward, top_mm):
    use_type(2, type_named(2, "FZK Dach 230")["id"])
    escape()
    press("Roof")
    call("key", {"code": 82})
    click(x1, y1)
    click(x2, y2)
    call("key", {"code": 258})
    prop(18, pitch)
    prop(19, toward)
    prop(17, top_mm)


def step_roof():
    go_to_storey("Dachgeschoss")
    # Dach-2 south of the ridge (y = 5), Dach-1 north of it; 30 degrees, eaves 0.5 m out.
    # Top is the top face at the outline's first corner (the first click), above the
    # storey, and the plane rises toward "Slope toward": the south plane from its eave
    # (2.911 + 0.231 - 2.700 = 0.442), the north plane from the ridge (6.087 + 0.231 - 2.700).
    roof_plane(-0.5, -0.5, 12.5, 5.0, 30, 90, 442)
    roof_plane(-0.5, 5.0, 12.5, 10.5, 30, 270, 3618)
    escape()


def attach_to_roof(wall_id, wanted_roof):
    """Clicks Top constraint until it reads Attached to roof `wanted_roof` (at most 6 clicks)."""
    call("select", {"id": wall_id})
    for _ in range(6):
        if row("Top constraint (click)")["value"] == "Attached to roof %d" % wanted_roof:
            return True
        call("set_property", {"code": 12670, "value": ""})
    return False


def step_walls_dg():
    # The knee walls along the eaves and the gables split at the ridge (y = 5): a wall
    # follows one roof plane, so each half of a gable is attached to its own plane.
    go_to_storey("Dachgeschoss")
    use_wall_type("FZK Aussenwand 300")
    existing = [w for w in call("elements", quiet=True)["walls"] if w["storeyId"] == level_ids()[1]["id"]]
    if not any(w["start"] == [0.15, 0.15] for w in existing):
        wall_chain([(0.15, 5.0), (0.15, 0.15), (11.85, 0.15), (11.85, 5.0)])
    if not any(w["start"] == [11.85, 9.85] for w in existing):
        wall_chain([(11.85, 5.0), (11.85, 9.85), (0.15, 9.85), (0.15, 5.0)])
    elif not any(w["start"] == [0.15, 9.85] for w in existing):
        wall_chain([(0.15, 9.85), (0.15, 5.0)])
    if not any(w["start"] == [0.15, 5.0] for w in existing) and any(w["start"] == [0.15, 0.15] for w in existing):
        wall_chain([(0.15, 5.0), (0.15, 0.15)])
    roofs = [slab for slab in call("elements", quiet=True)["slabs"] if slab["outline"][0][0] == -0.5]
    south = [r for r in roofs if r["outline"][0][1] == -0.5][0]["id"]
    north = [r for r in roofs if r["outline"][0][1] == 5][0]["id"]
    for wall in call("elements", quiet=True)["walls"]:
        if wall["storeyId"] != level_ids()[1]["id"]:
            continue
        middle = (wall["start"][1] + wall["end"][1]) / 2
        print("   wall", wall["id"], wall["start"], wall["end"], "->",
              attach_to_roof(wall["id"], south if middle < 5 else north))
    escape()


OPENING_TYPES = {  # name: (base, width, height, sill) in millimetres
    "FZK Fenster 2000x1200": ("Raam 1200x1500", 2000, 1200, 800),
    "FZK Fenster 2000x1200 B950": ("Raam 1200x1500", 2000, 1200, 950),
    "FZK Fenster 1000x1000": ("Raam 1200x1500", 1000, 1000, 800),
    "FZK Innentuer 885x2010": ("Deur 900x2100", 885, 2010, 0),
    "FZK Haustuer 1010x2010": ("Deur 900x2100", 1010, 2010, 0),
    "FZK Terrassentuer 2010x2375": ("Deur 900x2100", 2010, 2375, 0),
}


def step_opening_types():
    for name, (base, width, height, sill) in OPENING_TYPES.items():
        if type_named(7, name):
            continue
        new_id = int(call("duplicate_type", {"tab": 7, "id": type_named(7, base)["id"]})["id"])
        for field, value in ((0, name), (2, width), (3, height), (4, sill)):
            call("set_type_field", {"tab": 7, "id": new_id, "field": field, "value": str(value)})


def place_opening(type_name, x, y):
    use_type(7, type_named(7, type_name)["id"])
    escape()
    press("Door" if "tuer" in type_name else "Window")
    result = click(x, y)
    escape()
    return result


def step_windows_dg():
    go_to_storey("Dachgeschoss")
    # OG-Fenster-1/2 sit across the ridge line (y 4.5-5.5) in the IFC; the gables are split
    # there, so they go in the south halves, y 3.9-4.9, clear of the halves' joint (0.6 m off).
    place_opening("FZK Fenster 1000x1000", 0.15, 4.4)
    place_opening("FZK Fenster 1000x1000", 11.85, 4.4)


# The IFC's wall axes (outer faces, or one face of an interior wall) moved to the centre
# lines drawn here, as the clicks snapped them.
AXIS_TO_CENTRE = {0.0: 0.15, 12.0: 11.85, 10.0: 9.85, 7.41: 7.55, 5.75: 5.85, 4.25: 4.15}


def on_centre(value):
    for axis, centre in AXIS_TO_CENTRE.items():
        if abs(value - axis) < 0.01:
            return centre
    return round(value, 3)


def opening_type_for(opening):
    if opening["kind"] == "door":
        return {0.885: "FZK Innentuer 885x2010", 1.01: "FZK Haustuer 1010x2010",
                2.01: "FZK Terrassentuer 2010x2375"}[round(opening["width"], 3)]
    if opening["width"] < 1.5:
        return "FZK Fenster 1000x1000"
    return "FZK Fenster 2000x1200 B950" if opening["origin"][2] > 0.9 else "FZK Fenster 2000x1200"


def step_openings_eg():
    go_to_storey("Erdgeschoss")
    plan = json.load(open(os.environ.get("OBS_PLAN", os.path.join(OUT, "plan.json"))))
    for opening in plan["openings"]:
        if opening["storey"] != "Erdgeschoss":
            continue
        ox, oy, _ = opening["origin"]
        dx, dy, _ = opening["xdir"]
        cx, cy = ox + dx * opening["width"] / 2, oy + dy * opening["width"] / 2
        # The coordinate across the wall goes onto its centre line; along it stays.
        if abs(dx) > 0.5:
            cy = on_centre(cy)
        else:
            cx = on_centre(cx)
        made = place_opening(opening_type_for(opening), round(cx, 3), round(cy, 3))
        print("   %-14s %-28s at %.3f, %.3f -> %s" % (opening["name"], opening_type_for(opening), cx, cy,
                                                    made.get("message")))


def cycle_to(code, label, wanted, limit=40):
    """Clicks a (click) row until it reads `wanted`."""
    for _ in range(limit):
        current = row(label)
        if current and current["value"].strip() == wanted:
            return True
        call("set_property", {"code": code, "value": ""}, quiet=True)
    return False


def step_drawings():
    import shutil
    import time
    out = os.path.join(OUT, "drawings")
    os.makedirs(out, exist_ok=True)
    # The project's data for the title blocks (Model > Project settings).
    escape()
    press("Model/Settings")
    for code, value in ((12820, "FZK-Haus"), (12821, "AC20"), (12822, "KIT Karlsruhe"),
                        (12823, "Rebuilt from AC20-FZK-Haus.ifc"), (12824, "DO")):
        prop(code, value)
    escape()
    for storey, sheet_name in (("Erdgeschoss", "Grundriss Erdgeschoss"), ("Dachgeschoss", "Grundriss Dachgeschoss")):
        CLIENT.call("open_view", {"name": storey})
        time.sleep(0.5)
        escape()
        # Drawn by the design phase DO of a floor plan: dimensions, level marks and tags.
        print("   type", cycle_to(66, "Drawing type (click)", "Floor plan DO (Automatic)"),
              "palette", cycle_to(12610, "Palette (click)", "Technical drawing"))
        print("  ", press("Exterior dimensions").get("message"))
        escape()
        press("New sheet")
        prop(12621, sheet_name)
        print("   paper", cycle_to(12622, "Paper", "A3"))
        prop(12825, "06-11-2026")
        prop(12826, "Open BIM Studio via MCP")
        number = row("Number")["value"]
        call("key", {"code": 2096})  # Place view: the editor's own, in the sheet's middle
        press("Collaborate/Export: Open sheet/PDF")
        time.sleep(1.5)
        print("  ", storey, number, call("state", quiet=True)["message"])
        produced = os.path.join(os.environ.get("OBS_CWD", os.getcwd()), "%s.pdf" % number)
        if os.path.exists(produced):
            shutil.move(produced, os.path.join(out, "%s.pdf" % number))
    CLIENT.call("save")


def step_section():
    """Section A-A across the house at x = 6 m, through the gable window and the ridge, with
    its height chains, on an A3 sheet of its own."""
    import shutil
    import time
    out = os.path.join(OUT, "drawings")
    os.makedirs(out, exist_ok=True)
    go_to_storey("Erdgeschoss")
    press("View/Section")
    click(6.0, -1.5)
    print("  ", click(6.0, 11.5).get("message"))
    escape()
    CLIENT.call("open_view", {"name": "Section 1"})  # the first section of a fresh rebuild
    time.sleep(0.5)
    escape()
    prop(12841, "A-A")
    print("  ", press("Height dimensions").get("message"))
    escape()
    press("New sheet")
    prop(12621, "Schnitt A-A")
    print("   paper", cycle_to(12622, "Paper", "A3"))
    prop(12825, "06-11-2026")
    prop(12826, "Open BIM Studio via MCP")
    number = row("Number")["value"]
    call("key", {"code": 2096})  # Place view: the section, whose tab was active last
    press("Collaborate/Export: Open sheet/PDF")
    time.sleep(1.5)
    print("   section", number, call("state", quiet=True)["message"])
    produced = os.path.join(os.environ.get("OBS_CWD", os.getcwd()), "%s.pdf" % number)
    if os.path.exists(produced):
        shutil.move(produced, os.path.join(out, "%s.pdf" % number))
    CLIENT.call("save")


# The IFC's spaces (IfcSpace LongName) by a point inside each; Küche, Wohnen and Flur are
# parted by virtual boundaries, drawn here as room separation lines.
SPACES_EG = (("Küche", 2.0, 2.0), ("Wohnen", 8.0, 2.0), ("Flur", 3.0, 5.0), ("Buero", 2.0, 8.0),
             ("Bad", 5.7, 8.0), ("Schlafzimmer", 9.6, 7.0))
SEPARATORS_EG = (((4.7, 0.3), (4.7, 4.15)), ((3.8, 4.15), (7.55, 4.15)))


def name_space_at(x, y, name):
    escape()
    click(x, y)
    made = press("Space")
    space_row = row("Name")
    if space_row and space_row["code"] > 0:
        prop(space_row["code"], name)
    print("   space", name, "->", made.get("message"), "|", call("state", quiet=True)["selection"])


def step_spaces():
    go_to_storey("Erdgeschoss")
    for first, second in SEPARATORS_EG:
        press("Room separator")
        click(*first)
        click(*second)
        escape()
    for name, x, y in SPACES_EG:
        name_space_at(x, y, name)
    go_to_storey("Dachgeschoss")
    name_space_at(6.0, 5.0, "Galerie")
    escape()


STEPS = {"section": step_section, "spaces": step_spaces, "drawings": step_drawings, "openings_eg": step_openings_eg, "opening_types": step_opening_types, "windows_dg": step_windows_dg, "walls_dg": step_walls_dg, "roof": step_roof, "floor_dg": step_floor_dg, "floor_eg": step_floor_eg, "fix_interior": step_fix_interior, "types": step_types, "levels": step_levels, "walls_eg": step_walls_eg}

ALL = ("types", "opening_types", "levels", "walls_eg", "fix_interior", "floor_eg", "floor_dg", "roof",
       "walls_dg", "windows_dg", "openings_eg", "spaces", "drawings", "section")

if __name__ == "__main__":
    CLIENT = mcp.connected()
    try:
        for name in (ALL if sys.argv[1:] in ([], ["all"]) else sys.argv[1:]):
            print("== step", name)
            STEPS[name]()
    finally:
        CLIENT.close()
