#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# Diagnostic only: inspect generated native boxes, never author model geometry.
from pathlib import Path
import math
import sys
path=Path(sys.argv[1] if len(sys.argv)>1 else 'build/systems-showcase.bim')
components={};instances=[];rises={};level_z={};current=None
for line in path.read_text().splitlines():
    fields=line.split()
    if not fields:continue
    if fields[0]=='component':
        current=int(fields[1]);components[current]={'name':' '.join(fields[2:]),'solids':[]}
    elif fields[0]=='solid' and current is not None:
        components[current]['solids'].append(tuple(map(float,fields[3:9])))
    elif fields[0]=='instance':instances.append(fields)
    elif fields[0]=='level':level_z[int(fields[1])]=float(fields[2])
    elif fields[0]=='settings':
        for i in range(int(fields[2])):
            if int(fields[3+2*i])==2401900:rises[int(fields[1])]=int(fields[4+2*i])/1e6
boxes=[];corner_count=0
for fields in instances:
    iid,cid,lid=map(int,fields[1:4]);component=components[cid];name=component['name']
    if not (name.startswith('Facing brick ') or name.endswith(' corner')):continue
    corner_count+=int(name.endswith(' corner'))
    ox,oy,angle=map(float,fields[4:7]);c=math.cos(angle);s=math.sin(angle)
    for x,y,z,dx,dy,dz in component['solids']:
        corners=[(ox+a*c-b*s,oy+a*s+b*c) for a,b in ((x,y),(x+dx,y),(x,y+dy),(x+dx,y+dy))]
        low=(min(p[0] for p in corners),min(p[1] for p in corners),z+rises.get(iid,0)+level_z[lid])
        high=(max(p[0] for p in corners),max(p[1] for p in corners),low[2]+dz)
        boxes.append((iid,low,high))
assert corner_count==14,corner_count
courses={}
for box in boxes:courses.setdefault(round(box[1][2]/.0625),[]).append(box)
for course,items in courses.items():
    items.sort(key=lambda b:b[1][0])
    for i,a in enumerate(items):
        for b in items[i+1:]:
            if b[1][0]>=a[2][0]-1e-7:break
            assert not all(min(a[2][axis],b[2][axis])-max(a[1][axis],b[1][axis])>1e-7 for axis in range(3)),(course,a,b)
previous=None
for course,items in sorted(courses.items()):
    joints={round(b[2][0],6) for b in items if abs(b[1][1]-17)<1e-7 and 4<=b[1][0]<6.2 and b[2][0]<6.189}
    assert joints,(course,'no half-running front joints')
    if previous is not None:assert not (joints&previous),(course,joints&previous)
    previous=joints
previous=None
for course,items in sorted(courses.items()):
    joints={round(b[2][1],6) for b in items if abs(b[1][0]-4)<1e-7 and 17<=b[1][1]<19.2 and b[2][1]<19.189}
    assert joints,(course,'no half-running return joints')
    if previous is not None:assert not (joints&previous),(course,joints&previous)
    previous=joints
print(f'PASS: {len(boxes)} brick boxes across {len(courses)} courses, 14 corner objects, no overlaps')
print('PASS: half-running joints on both arms stagger on every neighbouring course')
