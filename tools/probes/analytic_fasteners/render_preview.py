#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Render the actual DynLex field/shading on the CPU; not a window screenshot."""
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'build/fastener-components/analytic'
OUT.mkdir(parents=True, exist_ok=True)
compiler_root = Path(os.environ.get('DYNLEX_ROOT') or (ROOT / '.dynlex-root.local').read_text().strip())
if subprocess.run(['pgrep', '-x', 'dynlex'], stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Wait for the current DynLex compiler before rendering.')
shader = (SOURCE / 'solid_fragment.dl').read_text()
body = 'set yaw to' + shader.split('set yaw to', 1)[1]
body = body[:body.index('set the fragment color')]
body = re.sub(r'@intrinsic\("shader buffer read", 0, (\d+)\)', r'(the analytic parameter at \1)', body)
body = body.replace('the fragment x coordinate', '(pixelX as a 64 bit floating-point number)')
body = body.replace('the fragment y coordinate', '(pixelY as a 64 bit floating-point number)')
# M16 defaults, matching the native catalogue and initial camera.
parameters = {0: 1.5, 1: .625, 2: .925, 3: .9375, 4: .53125, 5: .1875,
              6: .125, 7: 5., 8: 1., 9: 0., 10: 0., 11: .4, 12: .45,
              13: 660., 14: 480., 15: 8., 16: 1., 17: 1.}
function = 'function the analytic parameter at {integer:index}:\n    execute:\n'
for key, value in parameters.items():
    function += f'        if index = {key}:\n            return {value}\n'
function += '        return 0.0\n'
channels = ['(the string form of (((' + c + ' * 255.0) clamped between 0.0 and 255.0) as an integer))' for c in ('red', 'green', 'blue')]
body += f'print (({channels[0]} + (the string form of " ")) + (({channels[1]} + (the string form of " ")) + {channels[2]})) as a line\n'
generated = 'import tools/probes/analytic_fasteners/field.dl\n\n' + function
generated += 'print "P3" as a line\nprint "660 480" as a line\nprint "255" as a line\nloop pixelY from 0 to 480:\n    loop pixelX from 0 to 660:\n'
generated += ''.join('        ' + line + '\n' for line in body.splitlines())
(OUT / 'render-check.dl').write_text(generated)
with (OUT / 'render-build.log').open('w') as log:
    subprocess.run([str(compiler_root / 'build/dynlex'), str(OUT / 'render-check.dl'), '-O0', '-o', str(OUT / 'render-check')], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
with (OUT / 'render.ppm').open('w') as image:
    subprocess.run([str(OUT / 'render-check')], cwd=ROOT, stdout=image, check=True)
print(OUT / 'render.ppm')
try:
    from PIL import Image
except ImportError:
    pass
else:
    Image.open(OUT / 'render.ppm').save(OUT / 'render.png')
    print(OUT / 'render.png')
