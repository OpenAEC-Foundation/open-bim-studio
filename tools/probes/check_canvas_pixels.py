#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check actual GPU stroke widths on an owned, isolated X11 display."""
import argparse,json,os,subprocess,time
from pathlib import Path
from PIL import Image
from Xlib import X,display


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--shaders',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    app=None;connection=None;log=args.out/'native.log'
    try:
        display_name=':'+server.stdout.readline().strip();env=os.environ.copy();env['DISPLAY']=display_name;env['XDG_SESSION_TYPE']='x11';env['OBS_UI_SCALE']='1';env.pop('WAYLAND_DISPLAY',None)
        with log.open('w') as stream:
            app=subprocess.Popen([str(args.binary.resolve()),str(args.shaders.resolve())],env=env,stdout=stream,stderr=stream)
            deadline=time.monotonic()+30
            while 'READY: first native stroke frame submitted' not in log.read_text():
                if app.poll() is not None:raise RuntimeError('probe exited before its first frame')
                if time.monotonic()>deadline:raise TimeoutError('first native frame was not submitted')
                time.sleep(.05)
            connection=display.Display(display_name);pid_atom=connection.intern_atom('_NET_WM_PID')
            clients=[]
            for child in connection.screen().root.query_tree().children:
                value=child.get_full_property(pid_atom,X.AnyPropertyType)
                named=child.get_wm_name()=='Open BIM Studio - pixel stroke probe'
                owned=(value is not None and int(value.value[0])==app.pid) or named
                if owned and child.get_geometry().width==640:clients.append(child)
            if len(clients)!=1:
                inventory=[{'name':c.get_wm_name(),'width':c.get_geometry().width,'height':c.get_geometry().height,'mapped':c.get_attributes().map_state} for c in connection.screen().root.query_tree().children]
                raise RuntimeError(f'expected one owned 640px client, got {len(clients)}: {inventory}')
            time.sleep(.1);pixels=clients[0].get_image(0,0,640,480,X.ZPixmap,0xffffffff)
            image=Image.frombytes('RGB',(640,480),pixels.data,'raw','BGRX');image.save(args.out/'pixels.png')
            counts={name:[sum(max(image.getpixel((x,y)))<64 for y in range(centre-20,centre+20)) for centre in [80,140,200]] for name,x in [('retained',85),('ordinary',345)]}
            expected={'retained':[2,2,2],'ordinary':[2,6,20]}
            (args.out/'results.json').write_text(json.dumps({'widths_px':counts,'expected':expected,'passed':counts==expected},indent=2)+'\n')
            print(json.dumps(counts),flush=True)
            if counts!=expected:raise RuntimeError('native GPU stroke widths differ; inspect pixels.png')
            if app.wait(20)!=0:raise RuntimeError('native stroke probe failed')
    finally:
        if app is not None and app.poll() is None:app.terminate();app.wait(10)
        if connection:connection.close()
        server.terminate();server.wait(10)


if __name__=='__main__':main()
