#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Checks the DXF and DWG that tests/cad_export.dl writes.

1. The DWG's structure, independently of any CAD library: the file header
   and its CRC, each section between its sentinels with its size and CRC,
   the object map (every chunk's CRC; every handle once, ascending) and
   every object it points at (its byte count, its CRC, its type, and the
   handle in its own bits equal to the map's).
2. Both files read back with cadcodec (tests/reference, built here with
   cargo when it is installed): the same layers and entities from the DXF
   and the DWG, equal to tests/cad_export.reference.txt.

Run from the repository root after `./build.sh test cad_export`:

    python3 -B exchange/dxf_dwg/tests/verify_dxf_dwg.py [DXF DWG]
"""
import pathlib
import re
import shutil
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]

SENTINELS = {
    "header": ("CF7B1F23FDDE38A95F7C68B84E6D335F", "3084E0DC0221C756A0839747B192CCA0"),
    "classes": ("8DA1C4B8C4A9F8C5C0DCF45FE7CFB68A", "725E3B473B56073A3F230BA018304975"),
}
FILE_SENTINEL = "95A04E2899821AE55E41E05F9D3A4D00"


def crc16(data, seed=0xC0C1):
    crc = seed
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


class Bits:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def bit(self):
        value = (self.data[self.pos >> 3] >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return value

    def bits(self, count):
        value = 0
        for _ in range(count):
            value = (value << 1) | self.bit()
        return value

    def byte(self):
        return self.bits(8)

    def raw_short(self):
        return struct.unpack("<h", bytes([self.byte(), self.byte()]))[0]

    def raw_long(self):
        return struct.unpack("<i", bytes(self.byte() for _ in range(4)))[0]

    def short(self):
        code = self.bits(2)
        return [lambda: self.raw_short(), lambda: self.byte(), lambda: 0, lambda: 256][code]()

    def handle(self):
        head = self.byte()
        value = 0
        for _ in range(head & 15):
            value = (value << 8) | self.byte()
        return head >> 4, value


def check_dwg(path):
    data = path.read_bytes()
    problems = []
    if data[:6] != b"AC1015":
        return ["not an AC1015 file"]
    count = struct.unpack_from("<i", data, 21)[0]
    locators = {}
    for index in range(count):
        number, seeker, size = struct.unpack_from("<Bii", data, 25 + 9 * index)
        locators[number] = (seeker, size)
    end = 25 + 9 * count
    if struct.unpack_from("<H", data, end)[0] != crc16(data[:end]):
        problems.append("file header CRC")
    if data[end + 2:end + 18].hex().upper() != FILE_SENTINEL:
        problems.append("file header sentinel")
    for name, number in (("header", 0), ("classes", 1)):
        seeker, size = locators[number]
        section = data[seeker:seeker + size]
        opening, closing = SENTINELS[name]
        if section[:16].hex().upper() != opening or section[-16:].hex().upper() != closing:
            problems.append(name + " sentinels")
        length = struct.unpack_from("<i", section, 16)[0]
        if 16 + 4 + length + 2 + 16 != size:
            problems.append(name + " size")
        if struct.unpack_from("<H", section, 20 + length)[0] != crc16(section[16:20 + length]):
            problems.append(name + " CRC")
    # The object map.
    seeker, size = locators[2]
    cursor, last_handle, entries = seeker, 0, []
    while cursor < seeker + size:
        length = (data[cursor] << 8) | data[cursor + 1]
        chunk = data[cursor:cursor + length]
        if ((data[cursor + length] << 8) | data[cursor + length + 1]) != crc16(chunk):
            problems.append("object map chunk CRC at %d" % cursor)
        place, handle, offset = cursor + 2, 0, 0
        while place < cursor + length:
            value, shift = 0, 0
            while True:
                byte = data[place]; place += 1
                value |= (byte & 0x7F) << shift; shift += 7
                if not byte & 0x80:
                    break
            handle += value
            value, shift = 0, 0
            while True:
                byte = data[place]; place += 1
                if byte & 0x80:
                    value |= (byte & 0x7F) << shift; shift += 7
                else:
                    value |= (byte & 0x3F) << shift
                    if byte & 0x40:
                        value = -value
                    break
            offset += value
            if handle <= last_handle:
                problems.append("object map handle %X not ascending" % handle)
            last_handle = handle
            entries.append((handle, offset))
        cursor += length + 2
        if length == 2:
            break
    types = {}
    for handle, offset in entries:
        size, place, shift = 0, offset, 0
        while True:
            word = struct.unpack_from("<H", data, place)[0]; place += 2
            size |= (word & 0x7FFF) << shift; shift += 15
            if not word & 0x8000:
                break
        body = data[place:place + size]
        if struct.unpack_from("<H", data, place + size)[0] != crc16(data[offset:place + size]):
            problems.append("object %X CRC" % handle)
        bits = Bits(body)
        kind = bits.short()
        data_bits = bits.raw_long()
        code, own = bits.handle()
        if code != 0 or own != handle:
            problems.append("object at map handle %X holds handle %X" % (handle, own))
        if not 0 < data_bits <= 8 * size:
            problems.append("object %X size in bits %d of %d bytes" % (handle, data_bits, size))
        types[kind] = types.get(kind, 0) + 1
    return problems, len(entries), types


def reference_reader():
    binary = HERE / "reference" / "target" / "release" / "dxf-dwg-reference"
    if not binary.exists():
        if shutil.which("cargo") is None:
            return None
        subprocess.run(["cargo", "build", "--release", "--quiet"], cwd=HERE / "reference", check=True)
    return binary


def main():
    dxf = pathlib.Path(sys.argv[1]) if len(sys.argv) > 2 else ROOT / "build" / "tests" / "cad_export.dxf"
    dwg = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "build" / "tests" / "cad_export.dwg"
    failed = False
    problems, objects, types = check_dwg(dwg)
    print("dwg structure: %d objects, %d types, %s" % (objects, len(types), "ok" if not problems else "FAIL"))
    for problem in problems:
        print("  " + problem)
    failed |= bool(problems)
    reader = reference_reader()
    if reader is None:
        print("cadcodec reference: SKIPPED (no cargo)")
        return 1 if failed else 0
    # cadcodec decodes \U+XXXX in DWG text, not in DXF text.
    def read(path):
        text = subprocess.run([str(reader), str(path)], check=True, capture_output=True, text=True).stdout
        return re.sub(r"\\\\U\+([0-9A-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    from_dxf, from_dwg = read(dxf), read(dwg)
    expected = (HERE / "cad_export.reference.txt").read_text()
    for name, got in (("dxf", from_dxf), ("dwg", from_dwg)):
        same = got == expected
        print("cadcodec reads the %s: %s" % (name, "ok" if same else "FAIL"))
        if not same:
            failed = True
            for line in sorted(set(got.splitlines()) ^ set(expected.splitlines())):
                print("  " + line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
