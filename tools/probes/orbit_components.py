#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Orbit a disposable native 3D window and retain frame samples/screenshots."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from PIL import ImageGrab


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=20)
    parser.add_argument('--build-note',default='Compiler flags not recorded; supply --build-note for performance comparisons.')
    parser.add_argument('--startup-timeout',type=float,default=300)
    parser.add_argument('--save-copy',action='store_true',help='Save a new IFCXB next to the generated BIM after measuring; refuse an existing destination.')
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    assert not (out/'handed-to-user').exists()
    model=args.model.resolve();binary=args.binary.resolve()
    native_copy=model.with_suffix('.ifcxb')
    if args.save_copy and (model.suffix!='.bim' or native_copy.exists()):
        raise ValueError('--save-copy requires a BIM source and a new IFCXB destination')
    if not 0 < args.seconds <= 300:
        raise ValueError('--seconds must be between 0 and 300')
    checksum=hashlib.sha256(model.read_bytes()).hexdigest()
    sys.path.insert(0,str(root/'automation/mcp'));import open_bim_studio_mcp as mcp
    spec=importlib.util.spec_from_file_location('obs_pointer',root/'tools/build_readme_images.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1440x900x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    app=None;pointer=None;log=out/'editor.log';started=time.monotonic()
    try:
        display=':'+server.stdout.readline().strip();env=os.environ.copy();env.pop('WAYLAND_DISPLAY',None)
        home=out/'home';home.mkdir(exist_ok=True)
        env.update(DISPLAY=display,HOME=str(home),XDG_SESSION_TYPE='x11',OBS_PROFILE_FRAMES='1',OBS_MODEL_VIEW='1',OBS_UI_SCALE='1')
        with log.open('w') as stream:
            app=subprocess.Popen(['stdbuf','-oL',str(binary),str(model),'--api',str(out/'api')],cwd=root,env=env,stdout=stream,stderr=stream)
        api=mcp.Modeller();deadline=started+args.startup_timeout
        while time.monotonic()<deadline:
            if app.poll() is not None:raise RuntimeError(f'editor exited {app.returncode}; see {log}')
            try:
                api.connect(str(out/'api'));before=api.request('state',timeout=2);break
            except Exception:time.sleep(.5)
        else:raise TimeoutError('startup/API timeout')
        startup=time.monotonic()-started;print(f'API ready after {startup:.3f}s',flush=True)
        # Let the first 3D scene complete before measuring motion.
        api.request('fit',timeout=120)
        time.sleep(3);offset=log.stat().st_size
        pointer=helper.Pointer(display)
        ImageGrab.grab(xdisplay=display).save(out/'before.png')
        pointer.xtst.XTestFakeMotionEvent(pointer.display,-1,850,450,0)
        pointer.xtst.XTestFakeButtonEvent(pointer.display,3,1,0);pointer.x11.XFlush(pointer.display)
        orbitStarted=time.monotonic();memory=[]
        while time.monotonic()-orbitStarted<args.seconds:
            elapsed=time.monotonic()-orbitStarted
            x=850+int(230*math.sin(elapsed*.9));y=450+int(125*math.sin(elapsed*.6))
            pointer.xtst.XTestFakeMotionEvent(pointer.display,-1,x,y,0);pointer.x11.XFlush(pointer.display)
            if app.poll() is not None:raise RuntimeError('editor exited while orbiting')
            status=Path(f'/proc/{app.pid}/status').read_text()
            memory.append({line.split(':')[0]:line.split(':')[1].strip() for line in status.splitlines() if line.startswith(('VmRSS:','VmHWM:'))})
            time.sleep(.025)
        orbitElapsed=time.monotonic()-orbitStarted
        end_offset=log.stat().st_size
        pointer.xtst.XTestFakeButtonEvent(pointer.display,3,0,0);pointer.x11.XFlush(pointer.display)
        time.sleep(2);after=api.request('state',timeout=60)
        ImageGrab.grab(xdisplay=display).save(out/'after.png')
        data=log.read_bytes()[offset:end_offset].decode(errors='replace')
        frames=[]
        for line in data.splitlines():
            if line.startswith('OBS_FRAME '):frames.append(dict(field.split('=',1) for field in line.split()[1:] if '=' in field))
        active_kinds={frame['active_kind'] for frame in frames if 'active_kind' in frame}
        if active_kinds and active_kinds!={'1'}:
            raise RuntimeError(f'orbit left the 3D tab: {active_kinds}')
        def quantiles(field):
            values=sorted(float(frame[field])/1000 for frame in frames if field in frame)
            if not values:return None
            return {'samples':len(values),'p50_ms':statistics.median(values),'p95_ms':values[int((len(values)-1)*.95)],'p99_ms':values[int((len(values)-1)*.99)]}
        if args.save_copy:
            # This X server and its only application belong to this invocation.
            # Ctrl+S uses the native editor writer and its derived IFCXB path.
            pointer.x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
            pointer.x11.XKeysymToKeycode.restype=ctypes.c_uint
            pointer.xtst.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
            control=pointer.x11.XKeysymToKeycode(pointer.display,0xffe3)
            letter=pointer.x11.XKeysymToKeycode(pointer.display,ord('s'))
            for key,pressed in ((control,1),(letter,1),(letter,0),(control,0)):
                pointer.xtst.XTestFakeKeyEvent(pointer.display,key,pressed,0)
                pointer.x11.XFlush(pointer.display)
                time.sleep(.1)
            deadline=time.monotonic()+120
            while not native_copy.exists() and time.monotonic()<deadline:
                if app.poll() is not None:
                    raise RuntimeError('editor exited while saving')
                time.sleep(.5)
            if not native_copy.exists():
                raise TimeoutError('native IFCXB save did not complete')
            # Wait for the writer to finish before returning the artifact.
            after=api.request('state',timeout=120)
        assert before['undoSteps']==after['undoSteps']==0
        assert hashlib.sha256(model.read_bytes()).hexdigest()==checksum
        result={'model':str(model),'sha256':checksum,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'startup_seconds':startup,'orbit_seconds':orbitElapsed,'observed_fps':len(frames)/orbitElapsed,'renderer':[line for line in log.read_text(errors='replace').splitlines() if line.startswith('OBS_RENDERER ')],'viewport':[1440,900],'build_note':args.build_note,'active_kinds':sorted(active_kinds),'cpu':quantiles('cpu_us'),'presented':quantiles('presented_us'),'gpu':quantiles('gpu_us'),'frames':frames,'memory_samples':memory,'state_before':before,'state_after':after,'model_unchanged':True,'saved_copy':str(native_copy) if args.save_copy else None,'environment':{k:env.get(k) for k in ['VK_ICD_FILENAMES','MESA_VK_DEVICE_SELECT','DISPLAY','OBS_MODEL_VIEW','OBS_UNCAPPED']}}
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['startup_seconds','cpu','presented','gpu','model_unchanged']}),flush=True)
    finally:
        if pointer:pointer.close()
        if app is not None:
            app.terminate()
            try:app.wait(10)
            except subprocess.TimeoutExpired:app.kill();app.wait()
        server.terminate();server.wait(10)


if __name__=='__main__':main()
