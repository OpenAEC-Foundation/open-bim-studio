#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check the diagnostic GLFW event audit with an owned hidden native window."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shim',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source=out/'event-audit.c'
    source.write_text(r'''#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
extern int glfwInit(void);
extern void glfwTerminate(void);
extern void glfwPollEvents(void);
extern void glfwWaitEventsTimeout(double);
extern void glfwWindowHint(int,int);
extern void *glfwCreateWindow(int,int,const char *,void *,void *);
extern void glfwDestroyWindow(void *);
static uint64_t now(void) {
    struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;
}
int main(void) {
    if(!glfwInit())return 1;
    glfwWindowHint(0x00020004,0); /* GLFW_VISIBLE = false. */
    glfwWindowHint(0x00022001,0); /* GLFW_CLIENT_API = GLFW_NO_API. */
    void *window=glfwCreateWindow(32,32,"Owned event audit",0,0);
    if(!window)return 2;
    glfwPollEvents();
    struct timespec pause={0,200000000};
    while(nanosleep(&pause,&pause) && errno==EINTR){}
    glfwPollEvents();
    uint64_t start=now();
    for(;;) {
        uint64_t elapsed=now()-start;
        if(elapsed>=200000000ULL)break;
        glfwWaitEventsTimeout((200000000ULL-elapsed)/1e9);
    }
    printf("wait_us=%llu\n",(unsigned long long)((now()-start)/1000));
    glfwPollEvents();glfwDestroyWindow(window);glfwTerminate();return 0;
}
''')
    binary=out/'event-audit'
    subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra',str(source),'-lglfw','-o',str(binary)],check=True)
    shim=args.shim.resolve()
    env=os.environ.copy();env.pop('WAYLAND_DISPLAY',None)
    env.update(XDG_SESSION_TYPE='x11',OBS_ORBIT_CONTROL=str(out/'unused-control'),LD_PRELOAD=str(shim))
    run=subprocess.run([str(binary)],env=env,capture_output=True,text=True,timeout=5,check=True)
    (out/'probe.log').write_text(run.stdout+run.stderr)
    gaps=[dict(field.split('=',1) for field in line.split()[1:])
          for line in run.stderr.splitlines() if line.startswith('OBS_EVENT_PUMP ')]
    waits=[int(line.split('=',1)[1]) for line in run.stdout.splitlines() if line.startswith('wait_us=')]
    if (len(gaps)!=1 or not 190000<=int(gaps[0]['gap_us'])<2000000
            or gaps[0]['stage']!='between_calls' or len(waits)!=1 or waits[0]<190000):
        raise RuntimeError('application blocking or intentional event waiting was classified incorrectly; see probe.log')
    result={'passed':True,'gaps':gaps,'actual_event_wait_us':waits[0],
            'assertion':'200 ms application blocking is logged once; measured GLFW event waiting is excluded',
            'shim_sha256':hashlib.sha256(shim.read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
