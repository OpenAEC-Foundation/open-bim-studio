#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Measure the built CAD kernel through its scalar/opaque-pointer C seam.

Only Vec3 (three binary64 members) crosses as a concrete input record. Bodies
stay opaque and every owned handle is released. No compiler checkout is changed.
The check is non-null results and closed topology; it does not assert volumes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    archive=args.archive.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    client=(root/'kernel/api/client.dl').read_text()
    def symbol(prefix):
        found=re.findall(r'"('+re.escape(prefix)+r'[^" ]*)"',client)
        if len(found)!=1:raise RuntimeError(f'expected one kernel seam symbol: {prefix}')
        return found[0]
    symbols={
        'make':symbol('the_obskernel_faceted_solid_with_vertices_'),
        'combine':symbol('the_obskernel_combination_of_'),
        'flaws':symbol('the_obskernel_flaw_count_of_'),
        'release':symbol('release_obskernel_body_'),
    }
    types=(root/'kernel/api/types.dl').read_text()
    operation=re.search(r'function cad difference operation:\s+replacement:\s+(\d+)',types)
    if not operation:raise RuntimeError('kernel difference operation not found')
    aliases='\n'.join([
        f'extern void *make(const Vec3 *,int32_t,const int32_t *,int32_t,double) __asm__("{symbols["make"]}");',
        f'extern void *combine(void *,void *,int32_t,double) __asm__("{symbols["combine"]}");',
        f'extern int32_t flaws(void *) __asm__("{symbols["flaws"]}");',
        f'extern void release(void *) __asm__("{symbols["release"]}");',
    ])
    source=out/'kernel-timing.c'
    driver=r'''#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef struct { double x,y,z; } Vec3;
_Static_assert(sizeof(Vec3)==24,"Vec3 ABI");
ALIASES
static uint64_t now(void) { struct timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t))abort(); return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec; }
static void *box(double x,double y,double z,double a,double b,double c) {
    Vec3 p[]={{x,y,z},{x+a,y,z},{x+a,y+b,z},{x,y+b,z},{x,y,z+c},{x+a,y,z+c},{x+a,y+b,z+c},{x,y+b,z+c}};
    const int32_t f[]={4,0,3,2,1,4,4,5,6,7,4,0,1,5,4,4,1,2,6,5,4,2,3,7,6,4,3,0,4,7};
    return make(p,8,f,30,1e-7);
}
static void require_body(void *b) { if(!b){fputs("kernel returned no body\n",stderr);exit(1);} }
int main(void) {
    puts("[");
    for(int far=0;far<2;++far) for(int holes=0;holes<=4;++holes) {
        if(holes!=0 && holes!=1 && holes!=4)continue;
        double x=far?500000.0:0,y=far?450000.0:0;
        printf("{\"survey\":%s,\"openings\":%d,\"microseconds\":[",far?"true":"false",holes);
        for(int round=0;round<15;++round) {
            uint64_t start=now();
            void *wall=box(x,y,0,6,.36,3); require_body(wall);
            for(int h=0;h<holes;++h) {
                void *void_body=box(x+.3+h*1.4,y-.1,.9,1.0,.56,1.5);require_body(void_body);
                void *cut=combine(wall,void_body,DIFFERENCE,1e-7);
                release(void_body);release(wall);require_body(cut);wall=cut;
            }
            uint64_t elapsed=now()-start;
            if(flaws(wall)!=0){fputs("kernel produced topology flaws\n",stderr);release(wall);return 1;}
            release(wall);
            printf("%s%.3f",round?",":"",elapsed/1000.0);
        }
        printf("],\"topology_flaws\":0}%s\n",far==1 && holes==4?"":",");
    }
    puts("]");
}
'''
    # The driver string is ordinary C; its JSON/diagnostic escapes are literal.
    driver=driver.replace('ALIASES',aliases).replace('DIFFERENCE',operation.group(1))
    source.write_text(driver)
    binary=out/'kernel-timing'
    command=['cc','-std=c11','-O2','-Wall','-Wextra',str(source),str(archive),'-lm','-o',str(binary)]
    compiled=subprocess.run(command,capture_output=True,text=True)
    (out/'compile.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise RuntimeError('C seam driver compilation failed; see compile.log')
    run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=240)
    (out/'kernel-timing.out').write_text(run.stdout)
    (out/'kernel-timing.err').write_text(run.stderr)
    if run.returncode:raise RuntimeError('kernel timing/correctness check failed; see kernel-timing.err')
    result={'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'compiler_command':command,'samples':json.loads(run.stdout),
            'correctness_scope':'non-null bodies and zero topology flaws; volumes not checked'}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for item in result['samples']:
        values=sorted(item['microseconds'])
        print(json.dumps({'survey':item['survey'],'openings':item['openings'],
                          'p50_us':values[7],'p95_us':values[13],'max_us':values[-1]}),flush=True)


if __name__=='__main__':main()
