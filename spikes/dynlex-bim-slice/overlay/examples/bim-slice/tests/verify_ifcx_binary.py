#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Checks a binary IfcX file (.ifcxb) against the JSON IfcX of the same model.

The file is uncompressed when it is gzip; then an independent CBOR (RFC 8949)
reader, with the string reference extension
(tags 256 and 25) and decimal fractions (tag 4), turns the binary file into
JSON values; they must equal the JSON file's, the header (which names the
file and the time) left out.

    verify_ifcx_binary.py MODEL.ifcxb MODEL.ifcx
"""
import gzip
import json
import struct
import sys
from decimal import Decimal


class Reader:
    def __init__(self, data):
        self.data, self.at, self.tables = data, 0, [None]

    def take(self, count):
        if self.at + count > len(self.data):
            raise ValueError(f"cut short at byte {self.at}")
        piece = self.data[self.at:self.at + count]
        self.at += count
        return piece

    def argument(self, info):
        if info < 24:
            return info
        if info in (24, 25, 26, 27):
            return int.from_bytes(self.take(1 << (info - 24)), "big")
        raise ValueError(f"bad argument at byte {self.at}")

    def note(self, text):
        table = self.tables[-1]
        if table is None:
            return
        size, count = len(text.encode()), len(table)
        least = 3 if count < 24 else 4 if count < 256 else 5 if count < 65536 else 7 if count < 2**32 else 11
        if size >= least:
            table.append(text)

    def value(self):
        initial = self.take(1)[0]
        major, info = initial >> 5, initial & 31
        if major == 7:
            simple = {20: False, 21: True, 22: None, 23: None}
            if info in simple:
                return simple[info]
            if info == 25:
                return struct.unpack(">e", self.take(2))[0]
            if info == 26:
                return struct.unpack(">f", self.take(4))[0]
            if info == 27:
                return struct.unpack(">d", self.take(8))[0]
            raise ValueError(f"unknown simple value at byte {self.at}")
        if info == 31:
            raise ValueError("indefinite lengths are not written by the slice")
        amount = self.argument(info)
        if major == 0:
            return amount
        if major == 1:
            return -1 - amount
        if major == 3:
            text = self.take(amount).decode()
            self.note(text)
            return text
        if major == 4:
            return [self.value() for _ in range(amount)]
        if major == 5:
            result = {}
            for _ in range(amount):
                key = self.value()
                result[key] = self.value()
            return result
        if major == 6:
            if amount == 256:
                self.tables.append([])
                inner = self.value()
                self.tables.pop()
                return inner
            if amount == 25:
                return self.tables[-1][self.value()]
            if amount == 4:
                exponent, mantissa = self.value()
                return float(Decimal(mantissa).scaleb(exponent))
            if amount == 55799:
                return self.value()
        raise ValueError(f"unexpected major type {major} at byte {self.at}")


def same(left, right, where):
    if isinstance(left, bool) or isinstance(right, bool) or left is None or right is None:
        return left is right or (left == right and type(left) is type(right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if left != right:
            print(f"{where}: {left!r} != {right!r}")
            return False
        return True
    if isinstance(left, str) or isinstance(right, str):
        if left != right:
            print(f"{where}: {left!r} != {right!r}")
        return left == right
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            print(f"{where}: {len(left)} items != {len(right)}")
            return False
        return all(same(a, b, f"{where}[{i}]") for i, (a, b) in enumerate(zip(left, right)))
    if isinstance(left, dict) and isinstance(right, dict):
        if list(left) != list(right):
            print(f"{where}: keys {list(left)[:5]} != {list(right)[:5]}")
            return False
        return all(same(left[k], right[k], f"{where}.{k}") for k in left)
    print(f"{where}: {type(left).__name__} != {type(right).__name__}")
    return False


def main():
    stored = open(sys.argv[1], "rb").read()
    binary = gzip.decompress(stored) if stored[:2] == b"\x1f\x8b" else stored
    reader = Reader(binary)
    decoded = reader.value()
    if reader.at != len(binary):
        sys.exit(f"{len(binary) - reader.at} bytes after the document")
    text = json.load(open(sys.argv[2]))
    for document in (decoded, text):
        document.pop("header", None)
    if not same(decoded, text, "document"):
        sys.exit("the binary file differs from the JSON")
    size = len(open(sys.argv[2], "rb").read())
    print(f"same document: {len(text.get('data', []))} nodes; {len(stored)} bytes stored ({len(binary)} uncompressed), {size} bytes JSON ({100 * len(stored) // size}%)")


if __name__ == "__main__":
    main()
