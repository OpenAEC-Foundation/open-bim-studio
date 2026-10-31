#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Exercise the native shaping ABI with real Lao combining marks (Linux)."""
import argparse
import ctypes as c
from ctypes.util import find_library
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, default=Path('ui/shell/fonts/NotoSansLao.ttf'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='obs-shaping-') as tmp:
        bridge = Path(tmp) / 'platform.so'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        'platform/obs_platform.c', '-o', str(bridge), '-pthread', '-ldl'], check=True)
        native = c.CDLL(str(bridge))
        ft = c.CDLL(find_library('freetype'))
        ft.FT_Init_FreeType.argtypes = [c.POINTER(c.c_void_p)]
        ft.FT_New_Face.argtypes = [c.c_void_p, c.c_char_p, c.c_long, c.POINTER(c.c_void_p)]
        ft.FT_Set_Pixel_Sizes.argtypes = [c.c_void_p, c.c_uint, c.c_uint]
        ft.FT_Done_Face.argtypes = [c.c_void_p]
        ft.FT_Done_FreeType.argtypes = [c.c_void_p]

        class Glyph(c.Structure):
            _fields_ = [(name, c.c_int64) for name in
                        ('glyph', 'cluster', 'advance_x', 'advance_y', 'offset_x', 'offset_y')]

        shape = native.obs_platform_shape_utf8
        shape.argtypes = [c.c_void_p, c.c_char_p, c.c_int64, c.POINTER(Glyph), c.c_int64]
        shape.restype = c.c_int64
        assert native.obs_platform_has_text_shaper() == 1, 'HarfBuzz unavailable'
        library, face = c.c_void_p(), c.c_void_p()
        assert ft.FT_Init_FreeType(c.byref(library)) == 0
        assert ft.FT_New_Face(library, bytes(args.font), 0, c.byref(face)) == 0
        assert ft.FT_Set_Pixel_Sizes(face, 0, 15) == 0
        try:
            for text, marks in [('ລາວ', False), ('ຕັ້ງຄ່າ', True), ('ບັນທຶກ', True),
                                ('ຄຸນສົມບັດ', True), ('Model ລາວ 2026', False)]:
                encoded = text.encode()
                count = shape(face, encoded, len(encoded), None, 0)
                assert 0 < count <= len(encoded)
                glyphs = (Glyph * count)()
                assert shape(face, encoded, len(encoded), glyphs, count - 1) == -count
                assert shape(face, encoded, len(encoded), glyphs, count) == count
                assert all(g.glyph > 0 for g in glyphs), 'missing font glyph'
                assert sum(g.advance_x for g in glyphs) > 0
                assert all(0 <= g.cluster < len(encoded) for g in glyphs)
                if marks:
                    assert any(g.advance_x == 0 for g in glyphs), 'combining marks must not advance'
                    assert any(g.offset_x or g.offset_y for g in glyphs), 'marks need shaped offsets'
                expected = bytes(glyphs)
                assert shape(face, encoded, len(encoded), glyphs, count) == count
                assert bytes(glyphs) == expected, 'cached positions differ'
                print(f'PASS {text}: {count} shaped glyphs')
            assert shape(face, b'', 0, None, 0) == 0
            assert shape(None, b'text', 4, None, 0) == -1
            assert shape(face, b'x', 4097, None, 0) == -1
            print('PASS empty text, invalid arguments, bounds and cached ABI')
        finally:
            ft.FT_Done_Face(face)
            ft.FT_Done_FreeType(library)


if __name__ == '__main__':
    main()
