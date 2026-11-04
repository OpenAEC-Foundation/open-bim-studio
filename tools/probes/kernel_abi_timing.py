#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Measure the built CAD kernel through its existing native C seam.

Vec3, Plane and the scalar/pointer slice result follow the shared kernel types.
The native x86-64 slice and mesh stores were checked against the archive as well.
Bodies stay opaque; every owned handle is released. No compiler is changed.
Mesh/list ownership follows the shared types and the compiler's plain list
release. Checks include topology, finite tessellation and analytic signed volumes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess


def box_component_fixture(model, component_id):
    """Exact analytic union volume from an independent coordinate cell sweep."""
    boxes=[];active=False
    for line in model.read_text().splitlines():
        fields=line.split()
        if not fields:continue
        if fields[0]=='component':active=int(fields[1])==component_id
        if active and fields[0]=='solid':
            if fields[1:3]!=['0','0'] or float(fields[9])!=0:
                raise ValueError('component probe requires unrotated additive boxes')
            box=tuple(float(value) for value in fields[3:9])
            if any(size<=0 for size in box[3:]):raise ValueError('box dimensions must be positive')
            boxes.append(box)
    if not boxes:raise ValueError('component has no supported box solids')
    axes=[sorted({value for box in boxes for value in (box[axis],box[axis]+box[axis+3])}) for axis in range(3)]
    cells=(len(axes[0])-1)*(len(axes[1])-1)*(len(axes[2])-1)
    if cells>1000000:raise ValueError('analytic cell sweep is too large')
    volume=0.0
    for x0,x1 in zip(axes[0],axes[0][1:]):
        for y0,y1 in zip(axes[1],axes[1][1:]):
            for z0,z1 in zip(axes[2],axes[2][1:]):
                centre=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
                if any(all(box[axis]<=centre[axis]<=box[axis]+box[axis+3] for axis in range(3)) for box in boxes):
                    volume+=(x1-x0)*(y1-y0)*(z1-z0)
    return boxes,volume


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--box-component-model',type=Path,help='Instead of walls, fold one native component made of additive axis-aligned boxes.')
    parser.add_argument('--component-id',type=int)
    parser.add_argument('--component-rounds',type=int,default=3)
    args=parser.parse_args()
    if bool(args.box_component_model)!=(args.component_id is not None):
        raise ValueError('provide both --box-component-model and --component-id')
    if not 1<=args.component_rounds<=15:raise ValueError('--component-rounds must be between 1 and 15')
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
        'slice':symbol('initialize_obskernel_plane_slice_'),
        'mesh':symbol('initialize_obskernel_mesh_of_'),
    }
    types=(root/'kernel/api/types.dl').read_text()
    operation=re.search(r'function cad difference operation:\s+replacement:\s+(\d+)',types)
    if not operation:raise RuntimeError('kernel difference operation not found')
    aliases='\n'.join([
        f'extern void *make(const Vec3 *,int32_t,const int32_t *,int32_t,double) __asm__("{symbols["make"]}");',
        f'extern void *combine(void *,void *,int32_t,double) __asm__("{symbols["combine"]}");',
        f'extern int32_t flaws(void *) __asm__("{symbols["flaws"]}");',
        f'extern void release(void *) __asm__("{symbols["release"]}");',
        f'extern void slice(void *,const Plane *,Slice *) __asm__("{symbols["slice"]}");',
        f'extern void mesh(void *,double,double,Mesh *) __asm__("{symbols["mesh"]}");',
    ])
    source=out/'kernel-timing.c'
    driver=r'''#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef struct { double x,y,z; } Vec3;
typedef struct { Vec3 origin,xAxis,yAxis; } Plane;
typedef struct { _Bool valid,divided; int32_t snag; void *negative,*positive; } Slice;
typedef struct { void *data; int32_t length,capacity; } List;
typedef struct { List *positions,*normals,*triangles; int32_t *owner; } Mesh;
typedef struct { int32_t first,second,third; } Triangle;
_Static_assert(sizeof(Vec3)==24,"Vec3 ABI");
_Static_assert(sizeof(Plane)==72,"Plane ABI");
_Static_assert(sizeof(Slice)==24 && offsetof(Slice,snag)==4 && offsetof(Slice,negative)==8 && offsetof(Slice,positive)==16,"native slice ABI");
_Static_assert(sizeof(List)==16 && offsetof(List,length)==8 && sizeof(Mesh)==32 && offsetof(Mesh,owner)==24 && sizeof(Triangle)==12,"native mesh/list ABI");
ALIASES
static uint64_t now(void) { struct timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t))abort(); return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec; }
static void *box(double x,double y,double z,double a,double b,double c) {
    Vec3 p[]={{x,y,z},{x+a,y,z},{x+a,y+b,z},{x,y+b,z},{x,y,z+c},{x+a,y,z+c},{x+a,y+b,z+c},{x,y+b,z+c}};
    const int32_t f[]={4,0,3,2,1,4,4,5,6,7,4,0,1,5,4,4,1,2,6,5,4,2,3,7,6,4,3,0,4,7};
    return make(p,8,f,30,1e-7);
}
static void require_body(void *b) { if(!b){fputs("kernel returned no body\n",stderr);exit(1);} }
static void free_mesh(Mesh *m) {
    /* The sole-owner release in kernel/api/types.dl and lib/list.dl. */
    if(!m->owner || *m->owner!=1){fputs("unexpected mesh ownership\n",stderr);exit(1);}
    free(m->positions->data);free(m->positions);
    free(m->normals->data);free(m->normals);
    free(m->triangles->data);free(m->triangles);free(m->owner);
}
static void check_volume(void *body,double expected) {
    Mesh m={0};uint64_t start=now();mesh(body,.15,1e-7,&m);uint64_t elapsed=now()-start;
    if(!m.positions || !m.normals || !m.triangles || m.positions->length<4 || m.triangles->length<4) {
        fputs("missing tessellation\n",stderr);exit(1);
    }
    Vec3 *p=m.positions->data;Triangle *tri=m.triangles->data;Vec3 ref=p[0];
    long double total=0;
    for(int i=0;i<m.positions->length;++i)
        if(!isfinite(p[i].x) || !isfinite(p[i].y) || !isfinite(p[i].z)) {
            fputs("nonfinite tessellation\n",stderr);exit(1);
        }
    for(int i=0;i<m.triangles->length;++i) {
        Triangle t=tri[i];
        if(t.first<0 || t.second<0 || t.third<0 || t.first>=m.positions->length || t.second>=m.positions->length || t.third>=m.positions->length) {
            fputs("invalid triangle index\n",stderr);exit(1);
        }
        Vec3 a={p[t.first].x-ref.x,p[t.first].y-ref.y,p[t.first].z-ref.z};
        Vec3 b={p[t.second].x-ref.x,p[t.second].y-ref.y,p[t.second].z-ref.z};
        Vec3 c={p[t.third].x-ref.x,p[t.third].y-ref.y,p[t.third].z-ref.z};
        total+=(long double)a.x*(b.y*c.z-b.z*c.y)+(long double)a.y*(b.z*c.x-b.x*c.z)+(long double)a.z*(b.x*c.y-b.y*c.x);
    }
    double volume=(double)(total/6),error=fabs(volume-expected);
    fprintf(stderr,"OBS_KERNEL_VOLUME expected=%.12g actual=%.12g error=%.12g mesh_us=%.3f\n",expected,volume,error,elapsed/1000.0);
    free_mesh(&m);
    if(error>fmax(1e-6,fabs(expected)*1e-6)){fputs("tessellated volume differs from analytic volume\n",stderr);exit(1);}
}
static double timed_slice(void *wall,const Plane *plane,double negative_volume,double positive_volume) {
    Slice cut={0}; uint64_t start=now(); slice(wall,plane,&cut); uint64_t elapsed=now()-start;
    if(!cut.valid || !cut.divided || !cut.negative || !cut.positive) {
        fprintf(stderr,"slice refused: valid=%d divided=%d snag=%d\n",cut.valid,cut.divided,cut.snag);
        exit(1);
    }
    int bad=flaws(cut.negative)+flaws(cut.positive);
    check_volume(cut.negative,negative_volume);check_volume(cut.positive,positive_volume);
    release(cut.negative);release(cut.positive);
    if(bad){fputs("slice produced topology flaws\n",stderr);exit(1);}
    return elapsed/1000.0;
}
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
            check_volume(wall,6.48-.54*holes);
            Plane plan={{x,y,1.2},{1,0,0},{0,1,0}};
            Plane section={{x+3,y,0},{0,1,0},{0,0,1}};
            double plan_us=timed_slice(wall,&plan,2.592-.108*holes,3.888-.432*holes);
            int left_holes=holes>2?2:holes,right_holes=holes-left_holes;
            double section_us=timed_slice(wall,&section,3.24-.54*left_holes,3.24-.54*right_holes);
            fprintf(stderr,"OBS_KERNEL_SLICE survey=%d openings=%d plane=plan us=%.3f\n",far,holes,plan_us);
            fprintf(stderr,"OBS_KERNEL_SLICE survey=%d openings=%d plane=vertical us=%.3f\n",far,holes,section_us);
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
    fixture=None
    if args.box_component_model:
        boxes,volume=box_component_fixture(args.box_component_model,args.component_id)
        fixture={'model':str(args.box_component_model.resolve()),'model_sha256':hashlib.sha256(args.box_component_model.read_bytes()).hexdigest(),
                 'component_id':args.component_id,'additive_boxes':len(boxes),'analytic_union_volume_m3':volume,'boolean_tolerance_m':1e-9}
        union=re.search(r'function cad union operation:\s+replacement:\s+(\d+)',types)
        if not union:raise RuntimeError('kernel union operation not found')
        rows=',\n'.join('{'+','.join(format(value,'.17g') for value in box)+'}' for box in boxes)
        body=r'''int main(void) {
    const double boxes[][6]={BOXES};
    puts("[");
    for(int round=0;round<ROUNDS;++round) {
        void *folding=NULL;uint64_t start=now();
        for(size_t i=0;i<sizeof(boxes)/sizeof(boxes[0]);++i) {
            const double *b=boxes[i];uint64_t step=now();
            void *built=box(b[0],b[1],b[2],b[3],b[4],b[5]);require_body(built);
            if(folding) {
                void *joined=combine(folding,built,UNION,1e-9);
                release(folding);release(built);require_body(joined);folding=joined;
            } else folding=built;
            fprintf(stderr,"OBS_KERNEL_COMPONENT_STEP round=%d part=%zu us=%.3f\n",round,i,(now()-step)/1000.0);
        }
        double elapsed=(now()-start)/1000.0;
        if(flaws(folding)){fputs("component has topology flaws\n",stderr);return 1;}
        check_volume(folding,VOLUME);release(folding);
        printf("{\"component_id\":ID,\"round\":%d,\"microseconds\":%.3f,\"topology_flaws\":0}%s\n",round,elapsed,round+1==ROUNDS?"":",");
    }
    puts("]");
}
'''
        body=body.replace('BOXES',rows).replace('ROUNDS',str(args.component_rounds)).replace('UNION',union.group(1)).replace('VOLUME',format(volume,'.17g')).replace('ID',str(args.component_id))
        prefix=driver[:driver.index('static double timed_slice')]
        prefix=prefix.replace('return make(p,8,f,30,1e-7);','return make(p,8,f,30,1e-9);')
        driver=prefix+body
    source.write_text(driver)
    binary=out/'kernel-timing'
    command=['cc','-std=c11','-O2','-Wall','-Wextra',str(source),str(archive),'-lm','-o',str(binary)]
    compiled=subprocess.run(command,capture_output=True,text=True)
    (out/'compile.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise RuntimeError('C seam driver compilation failed; see compile.log')
    run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=240,
                       preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
    (out/'kernel-timing.out').write_text(run.stdout)
    (out/'kernel-timing.err').write_text(run.stderr)
    if run.returncode:raise RuntimeError('kernel timing/correctness check failed; see kernel-timing.err')
    slice_samples=[dict(field.split('=',1) for field in line.split()[1:])
                   for line in run.stderr.splitlines() if line.startswith('OBS_KERNEL_SLICE ')]
    volume_samples=[dict(field.split('=',1) for field in line.split()[1:])
                    for line in run.stderr.splitlines() if line.startswith('OBS_KERNEL_VOLUME ')]
    result={'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'shared_types_sha256':hashlib.sha256((root/'kernel/api/types.dl').read_bytes()).hexdigest(),
            'compiler_command':command,'samples':json.loads(run.stdout),
            'slice_samples':slice_samples,
            'volume_samples':volume_samples,
            'component_fixture':fixture,
            'correctness_scope':'valid bodies'+('/slices' if fixture is None else '')+', zero topology flaws, finite tessellation with bounded indices and analytic signed volumes within max(1e-6 m3, 1 ppm)'}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    if fixture:
        print(json.dumps({'fixture':fixture,'samples':result['samples']}),flush=True)
        return
    for item in result['samples']:
        values=sorted(item['microseconds'])
        print(json.dumps({'survey':item['survey'],'openings':item['openings'],
                          'p50_us':values[7],'p95_us':values[13],'max_us':values[-1]}),flush=True)
    for survey in [0,1]:
        for openings in [0,1,4]:
            for plane in ['plan','vertical']:
                values=sorted(float(row['us']) for row in slice_samples
                              if row['survey']==str(survey) and row['openings']==str(openings) and row['plane']==plane)
                if len(values)!=15:raise RuntimeError('missing kernel slice samples')
                print(json.dumps({'survey':bool(survey),'openings':openings,'plane':plane,
                                  'p50_us':values[7],'p95_us':values[13],'max_us':values[-1]}),flush=True)


if __name__=='__main__':main()
