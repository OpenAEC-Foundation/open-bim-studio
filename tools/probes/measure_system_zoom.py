#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Linux/X11 zoom audit of an explicitly identified disposable native window.

Select and visually verify the plan or 3D tab before running this tool. The API
has no active-tab observation: --view labels a run, it does not verify its view.
Requires python-xlib, Pillow and wmctrl. Never attach it to a user work session.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

from PIL import Image
from Xlib import X, display
from Xlib.ext import xtest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--api', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--view', required=True, choices=['plan', '3d'])
    args = parser.parse_args()
    out = args.out.resolve()
    model = args.model.resolve()
    folder = args.api.resolve()
    assert model.parent == out and folder.parent == out
    assert args.log.resolve().parent == out
    assert not list(out.glob('*handed-to-user*')), 'user handoff guard present'
    assert args.label.replace('-', '').replace('_', '').isalnum()
    command = Path(f'/proc/{args.pid}/cmdline').read_bytes().split(b'\0')
    assert command[0].decode() == str(args.binary.resolve())
    assert command[1].decode() == str(model)
    assert command[command.index(b'--api') + 1].decode() == str(folder)
    environment = Path(f'/proc/{args.pid}/environ').read_bytes().split(b'\0')
    assert b'OBS_UI_SCALE=1' in environment
    assert b'OBS_PROFILE_FRAMES=1' in environment
    windows = subprocess.check_output(['wmctrl', '-lp'], text=True).splitlines()
    matches = [line for line in windows if int(line.split()[2]) == args.pid]
    assert len(matches) == 1
    window_id = matches[0].split()[0]
    connection = display.Display()
    window = connection.create_resource_object('window', int(window_id, 16))
    owner = window.get_full_property(connection.intern_atom('_NET_WM_PID'), X.AnyPropertyType)
    assert int(owner.value[0]) == args.pid
    size = window.get_geometry()
    assert (size.width, size.height) == (1280, 900)
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('obs_zoom_api', root / 'automation/mcp/open_bim_studio_mcp.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    api = module.Modeller()
    api.connect(str(folder))
    before = api.request('elements', timeout=240)
    initial = api.request('state', timeout=240)
    assert initial['systems'] == 58 and initial['undoSteps'] == 0 and initial['tool'] == 0
    checksum = hashlib.sha256(model.read_bytes()).hexdigest()

    def capture(name):
        pixels = window.get_image(0, 0, size.width, size.height, X.ZPixmap, 0xffffffff)
        Image.frombytes('RGB', (size.width, size.height), pixels.data, 'raw', 'BGRX').save(out / name)

    capture(args.label + '-before.png')
    phases = []
    for index, button in enumerate([4, 5, 4, 5, 4, 5]):
        offset = args.log.stat().st_size
        started = time.monotonic()
        subprocess.run(['wmctrl', '-ia', window_id], check=True)
        time.sleep(0.5)
        origin = connection.screen().root.translate_coords(window, 0, 0)
        xtest.fake_input(connection, X.MotionNotify, x=origin.x + 700, y=origin.y + 450)
        connection.sync()
        for _ in range(4):
            xtest.fake_input(connection, X.ButtonPress, button)
            connection.sync()
            time.sleep(0.05)
            xtest.fake_input(connection, X.ButtonRelease, button)
            connection.sync()
            time.sleep(0.2)
        barriers = []
        for _ in range(3):
            tick = time.monotonic()
            api.request('state', timeout=240)
            barriers.append(time.monotonic() - tick)
        elapsed = time.monotonic() - started
        with args.log.open() as stream:
            stream.seek(offset)
            frames = [dict(pair.split('=', 1) for pair in line.split()[1:])
                      for line in stream if line.startswith('OBS_FRAME ')]
        phases.append({'index': index, 'button': button,
                       'burst_and_three_barriers_seconds': elapsed,
                       'api_barriers_seconds': barriers, 'frames': frames})
        (out / (args.label + '-measure.json')).write_text(json.dumps({'phases': phases}, indent=2) + '\n')
        print(json.dumps({'phase': index, 'seconds': elapsed, 'frames': len(frames)}), flush=True)
    after = api.request('elements', timeout=240)
    final = api.request('state', timeout=240)
    assert after == before and final['undoSteps'] == 0
    assert hashlib.sha256(model.read_bytes()).hexdigest() == checksum
    capture(args.label + '-after.png')
    result = {'view_label': args.view, 'active_view_verification': 'manual, separate',
              'model_sha256': checksum, 'systems': 58, 'model_elements_equal': True,
              'undo_steps': 0, 'phases': phases}
    (out / (args.label + '-measure.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('Zoom sequence completed; model data/file/Undo unchanged.', flush=True)


if __name__ == '__main__':
    main()
