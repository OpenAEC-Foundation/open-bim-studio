#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Generate an editable native wall/opening fixture for navigation measurements."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rooms',type=int,default=100)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--survey-offset',type=float,default=0)
    args=parser.parse_args()
    if not 1<=args.rooms<=100000:raise ValueError('room count must be between 1 and 100000')
    if not math.isfinite(args.survey_offset):raise ValueError('survey offset must be finite')
    columns=math.ceil(math.sqrt(args.rooms))
    opening_start=10+4*args.rooms
    lines=['BIM-SLICE 1',f'next {opening_start+2*args.rooms}',
           'level 1 0 3 Synthetic ground floor','walltype 2 Cavity wall 420',
           'layer 0.1 brick','layer 0.05 air','layer 0.12 insulation','layer 0.15 concrete',
           'openingtype 3 1.2 1.5 0.9 0.05 0 Synthetic window',
           'openingtype 4 0.9 2.1 0 0.05 1 Synthetic door']
    openings=[]
    for room in range(args.rooms):
        x=args.survey_offset+(room%columns)*10
        y=args.survey_offset+(room//columns)*8
        points=[(x,y),(x+6,y),(x+6,y+4),(x,y+4)]
        for edge in range(4):
            a,b=points[edge],points[(edge+1)%4]
            wall=10+room*4+edge
            lines.append(f'wall {wall} 2 1 {a[0]:.17g} {a[1]:.17g} {b[0]:.17g} {b[1]:.17g} 3')
            if edge in (0,2):
                openings.append(f'opening {opening_start+len(openings)} 3 {wall} 3')
    lines.extend(openings);lines.append('units m')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    data=('\n'.join(lines)+'\n').encode()
    args.out.write_bytes(data)
    print(json.dumps({'path':str(args.out.resolve()),'walls':4*args.rooms,
                      'openings':len(openings),'sha256':hashlib.sha256(data).hexdigest()}))


if __name__=='__main__':main()
