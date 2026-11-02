#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Orbit a disposable native 3D window and retain frame samples/screenshots."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import mmap
import struct
import shutil
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from PIL import ImageGrab



class OwnedDesktopWindow:
    """Only control the new GLFW client whose process this invocation owns."""
    def __init__(self, display_name):
        from Xlib import display
        self.connection=display.Display(display_name)
        self.root=self.connection.screen().root
        self.window=None
        self.width=1440;self.height=900
        self.x=0;self.y=0

    def claim(self, pid, activate=True):
        from Xlib import X
        atom=self.connection.intern_atom('_NET_WM_PID')
        matches=[]
        def visit(window, depth):
            try:
                value=window.get_full_property(atom,X.AnyPropertyType)
                if value is not None and int(value.value[0])==pid:
                    matches.append(window)
                    return
                if depth:
                    for child in window.query_tree().children:visit(child,depth-1)
            except Exception:
                pass
        visit(self.root,3)
        if len(matches)!=1:
            raise RuntimeError(f'expected one owned GLFW client, got {len(matches)}')
        self.window=matches[0]
        self.window.configure(x=100,y=100,width=1440,height=900,stack_mode=X.Above)
        self.connection.sync()
        time.sleep(1)
        size=self.window.get_geometry()
        self.width=size.width;self.height=size.height
        origin=self.root.translate_coords(self.window,0,0)
        self.x=origin.x;self.y=origin.y
        if (self.width,self.height)!=(1440,900):
            raise RuntimeError(f'client viewport changed: {self.width}x{self.height}')
        if activate and not self.focused():raise RuntimeError('owned client did not receive focus')

    def focused(self):
        focus=self.connection.get_input_focus().focus
        return getattr(focus,'id',None)==getattr(self.window,'id',-1)

    def capture(self, path):
        from Xlib import X
        from PIL import Image
        pixels=self.window.get_image(0,0,self.width,self.height,X.ZPixmap,0xffffffff)
        Image.frombytes('RGB',(self.width,self.height),pixels.data,'raw','BGRX').save(path)

    def restore(self):
        self.connection.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--internal-orbit-lib',type=Path,help='Process-local diagnostic GLFW input shim; no global mouse input.')
    parser.add_argument('--desktop',action='store_true',help='Use a new, PID-verified window on the current X display instead of Xvfb.')
    parser.add_argument('--keep-open',action='store_true',help='Hand the measured desktop model to the user; never valid with Xvfb.')
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
    if args.desktop and args.save_copy:raise ValueError('native copy saving uses the isolated Xvfb window')
    if args.desktop and not args.internal_orbit_lib:raise ValueError('--desktop requires --internal-orbit-lib; global input is limited to the owned Xvfb display')
    if args.keep_open and not args.desktop:raise ValueError('--keep-open requires --desktop')
    desktop=OwnedDesktopWindow(os.environ['DISPLAY']) if args.desktop else None
    server=None if args.desktop else subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1440x900x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    handed_over=False
    orbit_control=None;control_stream=None
    app=None;pointer=None;log=out/'editor.log';started=time.monotonic()
    try:
        display=os.environ['DISPLAY'] if args.desktop else ':'+server.stdout.readline().strip()
        env=os.environ.copy();env.pop('WAYLAND_DISPLAY',None)
        home=out/'home';home.mkdir(exist_ok=True)
        env.update(DISPLAY=display,HOME=str(home),XDG_SESSION_TYPE='x11',OBS_PROFILE_FRAMES='1',OBS_MODEL_VIEW='1',OBS_UI_SCALE='1')
        if args.internal_orbit_lib:
            control_stream=(out/'orbit-control').open('w+b')
            control_stream.write(struct.pack('QQQQ',0,0,os.getpid(),0));control_stream.flush()
            orbit_control=mmap.mmap(control_stream.fileno(),32)
            env['OBS_ORBIT_CONTROL']=str(out/'orbit-control')
            shim_copy=out/'orbit-input.so'
            shutil.copy2(args.internal_orbit_lib.resolve(),shim_copy)
            env['LD_PRELOAD']=str(shim_copy)+(':'+env['LD_PRELOAD'] if env.get('LD_PRELOAD') else '')
        with log.open('w') as stream:
            launch=[str(binary),str(model),'--api',str(out/'api')]
            if not args.internal_orbit_lib:launch=['stdbuf','-oL']+launch
            app=subprocess.Popen(launch,cwd=root,env=env,stdout=stream,stderr=stream)
        api=mcp.Modeller();deadline=started+args.startup_timeout
        while time.monotonic()<deadline:
            if app.poll() is not None:raise RuntimeError(f'editor exited {app.returncode}; see {log}')
            try:
                api.connect(str(out/'api'));before=api.request('state',timeout=2);break
            except Exception:time.sleep(.5)
        else:raise TimeoutError('startup/API timeout')
        startup=time.monotonic()-started;print(f'API ready after {startup:.3f}s',flush=True)
        if desktop:desktop.claim(app.pid,activate=not args.internal_orbit_lib)
        # Let the first 3D scene complete before measuring motion.
        api.request('fit',timeout=120)
        # Fit is deferred to the next event-loop iteration. A subsequent API
        # response is the barrier; a fixed delay alone can include a slow fit
        # in the first measured frame of a mixed construction scene.
        api.request('state',timeout=120)
        ready_to_orbit=time.monotonic()-started
        time.sleep(3);offset=log.stat().st_size
        pointer=None if orbit_control else helper.Pointer(display)
        desktop.capture(out/'before.png') if desktop else ImageGrab.grab(xdisplay=display).save(out/'before.png')
        if orbit_control:
            struct.pack_into('Q',orbit_control,8,int(args.seconds*1e9))
            struct.pack_into('Q',orbit_control,0,time.monotonic_ns())
        else:
            pointer.xtst.XTestFakeMotionEvent(pointer.display,-1,850+(desktop.x if desktop else 0),450+(desktop.y if desktop else 0),0)
            pointer.xtst.XTestFakeButtonEvent(pointer.display,3,1,0);pointer.x11.XFlush(pointer.display)
        orbitStarted=time.monotonic();memory=[]
        while time.monotonic()-orbitStarted<args.seconds:
            elapsed=time.monotonic()-orbitStarted
            if desktop and not orbit_control and not desktop.focused():raise RuntimeError('focus left owned client; orbit stopped')
            x=850+int(230*math.sin(elapsed*.9));y=450+int(125*math.sin(elapsed*.6))
            if not orbit_control:
                pointer.xtst.XTestFakeMotionEvent(pointer.display,-1,x+(desktop.x if desktop else 0),y+(desktop.y if desktop else 0),0);pointer.x11.XFlush(pointer.display)
            if app.poll() is not None:raise RuntimeError('editor exited while orbiting')
            status=Path(f'/proc/{app.pid}/status').read_text()
            memory.append({line.split(':')[0]:line.split(':')[1].strip() for line in status.splitlines() if line.startswith(('VmRSS:','VmHWM:'))})
            time.sleep(.025)
        orbitElapsed=time.monotonic()-orbitStarted
        end_offset=log.stat().st_size
        if orbit_control:struct.pack_into('Q',orbit_control,0,0)
        else:
            pointer.xtst.XTestFakeButtonEvent(pointer.display,3,0,0);pointer.x11.XFlush(pointer.display)
        time.sleep(2);after=api.request('state',timeout=60)
        desktop.capture(out/'after.png') if desktop else ImageGrab.grab(xdisplay=display).save(out/'after.png')
        data=log.read_bytes()[offset:end_offset].decode(errors='replace')
        frames=[]
        for line in data.splitlines():
            if line.startswith('OBS_FRAME '):frames.append(dict(field.split('=',1) for field in line.split()[1:] if '=' in field))
        if not frames:raise RuntimeError('no moving-camera frames; measurement rejected')
        active_kinds={frame['active_kind'] for frame in frames if 'active_kind' in frame}
        if active_kinds and active_kinds!={'1'}:
            raise RuntimeError(f'orbit left the 3D tab: {active_kinds}')
        host_samples=[dict(field.split('=',1) for field in line.split()[1:] if '=' in field) for line in data.splitlines() if line.startswith('OBS_HOST ')]
        def quantiles(field,samples=frames):
            values=sorted(float(frame[field])/1000 for frame in samples if field in frame and (field!='gpu_us' or float(frame[field])>0))
            if not values:return None
            return {'samples':len(values),'p50_ms':statistics.median(values),'p95_ms':values[int((len(values)-1)*.95)],'p99_ms':values[int((len(values)-1)*.99)]}
        if args.save_copy:
            # This X server and its only application belong to this invocation.
            # Ctrl+S uses the native editor writer and its derived IFCXB path.
            pointer.x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
            pointer.x11.XKeysymToKeycode.restype=ctypes.c_uint
            pointer.xtst.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
            control_key=pointer.x11.XKeysymToKeycode(pointer.display,0xffe3)
            letter=pointer.x11.XKeysymToKeycode(pointer.display,ord('s'))
            for key,pressed in ((control_key,1),(letter,1),(letter,0),(control_key,0)):
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
        if desktop and after['undoSteps']!=0:
            (out/'handed-to-user').write_text(str(app.pid)+'\n')
            handed_over=True
            raise RuntimeError('model contains edits; keeping the owned desktop window open and rejecting this run')
        assert before['undoSteps']==after['undoSteps']==0
        assert hashlib.sha256(model.read_bytes()).hexdigest()==checksum
        result={'model':str(model),'sha256':checksum,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'startup_seconds':startup,'fit_ready_seconds':ready_to_orbit,'fit_barrier':True,'orbit_seconds':orbitElapsed,'observed_fps':len(frames)/orbitElapsed,'renderer':[line for line in log.read_text(errors='replace').splitlines() if line.startswith('OBS_RENDERER ')],'viewport':[1440,900],'surface':'desktop' if desktop else 'Xvfb','motion_source':'process-local GLFW shim' if orbit_control else 'XTEST','input_shim_sha256':hashlib.sha256(shim_copy.read_bytes()).hexdigest() if args.internal_orbit_lib else None,'owned_pid':app.pid,'server_pid':server.pid if server else None,'build_note':args.build_note,'active_kinds':sorted(active_kinds),'cpu':quantiles('cpu_us'),'presented':quantiles('presented_us'),'gpu':quantiles('gpu_us'),'host_record':quantiles('record_us',host_samples),'host_present':quantiles('present_us',host_samples),'frames':frames,'memory_samples':memory,'state_before':before,'state_after':after,'model_unchanged':True,'saved_copy':str(native_copy) if args.save_copy else None,'environment':{k:env.get(k) for k in ['VK_ICD_FILENAMES','MESA_VK_DEVICE_SELECT','DISPLAY','OBS_MODEL_VIEW','OBS_UNCAPPED','VK_DRIVER_FILES','__NV_PRIME_RENDER_OFFLOAD','__VK_LAYER_NV_optimus']}}
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        if args.keep_open:
            (out/'handed-to-user').write_text(str(app.pid)+'\n')
            handed_over=True
        print(json.dumps({k:result[k] for k in ['startup_seconds','cpu','presented','gpu','model_unchanged']}),flush=True)
    finally:
        if orbit_control:struct.pack_into('Q',orbit_control,0,0)
        if pointer and not orbit_control:
            pointer.xtst.XTestFakeButtonEvent(pointer.display,3,0,0)
            pointer.x11.XFlush(pointer.display)
        if pointer:pointer.close()
        if orbit_control:orbit_control.close()
        if control_stream:control_stream.close()
        if desktop:desktop.restore()
        if app is not None and not handed_over:
            app.terminate()
            try:app.wait(10)
            except subprocess.TimeoutExpired:app.kill();app.wait()
        if server:
            server.terminate();server.wait(10)


if __name__=='__main__':main()
