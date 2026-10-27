#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
import unittest
from check_dynlex_locals import collisions


class PatternLocalTests(unittest.TestCase):
    def test_paper_capture(self):
        source = "function record sheet paper {integer:size}:\n    execute:\n        set paper to an empty list of an integer\n"
        self.assertEqual(list(collisions(source)), [(3, "paper")])

    def test_explicit_parameter(self):
        source = "function revise paper {integer:paper}:\n    execute:\n        set paper to paper + 1\n"
        self.assertEqual(list(collisions(source)), [])

    def test_member_assignment_is_not_a_local(self):
        source = "function revise paper {a value:canvas}:\n    execute:\n        set canvas's paper to 3\n"
        self.assertEqual(list(collisions(source)), [])

    def test_loop_capture(self):
        source = "function draw sheet:\n    execute:\n        loop sheet from 0 to 3:\n            print sheet as a line\n"
        self.assertEqual(list(collisions(source)), [(3, "sheet")])

    def test_scope_and_comments(self):
        source = "function draw paper:\n    execute:\n        # set paper to 3\nfunction draw border:\n    execute:\n        set paper to 3\n"
        self.assertEqual(list(collisions(source)), [])

    def test_bracketed_literal_is_not_captured(self):
        source = "function create [image] {integer:width}:\n    execute:\n        set image to width\n"
        self.assertEqual(list(collisions(source)), [])

    def test_curly_literal_is_not_captured(self):
        source = "function create {literal:image} {integer:width}:\n    execute:\n        set image to width\n"
        self.assertEqual(list(collisions(source)), [])

    def test_single_word_spelling_is_always_literal(self):
        source = "function sample:\n    execute:\n        set sample to 1\n"
        self.assertEqual(list(collisions(source)), [])

    def test_renamed_local(self):
        source = "function record sheet paper {integer:size}:\n    execute:\n        set paperTriangles to an empty list of an integer\n"
        self.assertEqual(list(collisions(source)), [])


if __name__ == "__main__":
    unittest.main()
