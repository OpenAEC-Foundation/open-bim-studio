#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Build the isolated native CSG probe, serially, from repository sources."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'build/fastener-components/analytic'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    compiler_root = Path(os.environ.get('DYNLEX_ROOT') or (ROOT / '.dynlex-root.local').read_text().strip())
    compiler = compiler_root / 'build/dynlex'
    if subprocess.run(['pgrep', '-x', 'dynlex'], stdout=subprocess.DEVNULL).returncode == 0:
        raise SystemExit('A DynLex compiler is running. Wait for it before building this probe.')
    env = os.environ.copy()
    libraries = compiler_root / '.cache/bootstrap/root/usr/lib/x86_64-linux-gnu'
    if libraries.is_dir():
        for name in ('LIBRARY_PATH', 'LD_LIBRARY_PATH'):
            env[name] = str(libraries) + (':' + env[name] if env.get(name) else '')
    (OUT / 'shaders').mkdir(parents=True, exist_ok=True)

    def compile_file(source, target, *flags):
        with target.with_suffix('.build.log').open('w') as log:
            result = subprocess.run([str(compiler), str(source), *flags, '-o', str(target)],
                                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(f'Build failed; see {target.with_suffix(".build.log")}')

    shader_names = ('screen_vertex', 'canvas_vertex', 'mesh_vertex', 'mesh_instance_vertex',
                    'text_fragment', 'image_fragment', 'edge_fragment', 'edge_cut_fragment',
                    'mesh_fragment', 'mesh_cut_fragment', 'flat_fragment')
    validator = os.environ.get('SPIRV_VAL') or shutil.which('spirv-val')
    for name in shader_names:
        source = SOURCE / 'solid_fragment.dl' if name == 'flat_fragment' else ROOT / 'viewer/shaders' / (name + '.dl')
        target = OUT / 'shaders' / (name + '.spv')
        compile_file(source, target, '--emit-spirv', '--shader-stage=' + name.split('_')[-1])
        if validator:
            subprocess.run([validator, str(target)], check=True)
    if not validator:
        print('SPIR-V validation skipped: set SPIRV_VAL or install spirv-val.', flush=True)
    compile_file(SOURCE / 'field_check.dl', OUT / 'field-check', '-O0')
    subprocess.run([str(OUT / 'field-check')], cwd=ROOT, env=env, check=True)
    compile_file(SOURCE / 'main.dl', OUT / 'solid-viewer', '-O0')
    print(f'Built {OUT / "solid-viewer"}', flush=True)
    if args.run:
        os.chdir(ROOT)
        os.execve(str(OUT / 'solid-viewer'), [str(OUT / 'solid-viewer')], env)


if __name__ == '__main__':
    main()
