import unittest

from hyperbase.hyperedge import hedge
from hyperbase.parsers.parse_result import ParseResult


class TestHyperedgeText(unittest.TestCase):
    def test_text_none_by_default(self):
        edge = hedge("(is/P.so (the/M sky/C) blue/C)")
        self.assertIsNone(edge.text)

    def test_atom_text_none_by_default(self):
        atom = hedge("sky/C")
        self.assertIsNone(atom.text)

    def test_hedge_parse_result_top_level_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        self.assertEqual(result.text, "The sky is blue.")

    def test_hedge_parse_result_atom_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        # is/P.so -> token at position 2 -> "is"
        self.assertEqual(result[0].text, "is")
        # blue/C -> token at position 3 -> "blue"
        self.assertEqual(result[2].text, "blue")

    def test_hedge_parse_result_subedge_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        # (the/M sky/C) -> positions 0,1 -> "The sky"
        self.assertEqual(result[1].text, "The sky")
        # the/M -> position 0 -> "The"
        self.assertEqual(result[1][0].text, "The")
        # sky/C -> position 1 -> "sky"
        self.assertEqual(result[1][1].text, "sky")

    def test_hedge_parse_result_preserves_edge_structure(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        self.assertEqual(str(result), "(is/P.so (the/M sky/C) blue/C)")

    def test_hedge_parse_result_neg_pos(self):
        pr = ParseResult(
            edge=hedge("(+/B a/C b/C)"),
            text="a and b",
            tokens=["a", "and", "b"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        self.assertEqual(result.text, "a and b")
        # +/B -> position -1 -> None
        self.assertIsNone(result[0].text)
        # a/C -> position 0 -> "a"
        self.assertEqual(result[1].text, "a")
        # b/C -> position 2 -> "b"
        self.assertEqual(result[2].text, "b")

    def test_hedge_parse_result_gap_tokens(self):
        pr = ParseResult(
            edge=hedge("(+/B a/C b/C)"),
            text="a and b",
            tokens=["a", "and", "b"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        # top-level overridden with full text
        self.assertEqual(result.text, "a and b")

    def test_hedge_parse_result_single_atom(self):
        pr = ParseResult(
            edge=hedge("hello/C"),
            text="Hello",
            tokens=["Hello"],
            tok_pos=hedge("0"),
        )
        result = hedge(pr)
        self.assertEqual(result.text, "Hello")
        self.assertTrue(result.atom)
        self.assertEqual(str(result), "hello/C")

    def test_hedge_parse_result_nested(self):
        pr = ParseResult(
            edge=hedge(
                "(say/P.so (the/M man/C) (that/T (is/P.sc (the/M sky/C) blue/C)))"
            ),
            text="The man says that the sky is blue.",
            tokens=["The", "man", "says", "that", "the", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) (3 (6 (4 5) 7)))"),
        )
        result = hedge(pr)
        self.assertEqual(result.text, "The man says that the sky is blue.")
        # say/P.so -> "says"
        self.assertEqual(result[0].text, "says")
        # (the/M man/C) -> "The man"
        self.assertEqual(result[1].text, "The man")
        # (that/T (is/P.sc (the/M sky/C) blue/C)) -> positions 3,6,4,5,7
        # min=3, max=7 -> "that the sky is blue"
        self.assertEqual(result[2].text, "that the sky is blue")
        # (is/P.sc (the/M sky/C) blue/C) -> positions 6,4,5,7
        # min=4, max=7 -> "the sky is blue"
        self.assertEqual(result[2][1].text, "the sky is blue")

    def test_hedge_parse_result_parens_atom(self):
        pr = ParseResult(
            edge=hedge("(is/P.sc (X/C) good/C)"),
            text="X is good.",
            tokens=["X", "is", "good", "."],
            tok_pos=hedge("(1 (0) 2)"),
        )
        result = hedge(pr)
        self.assertEqual(str(result), "(is/P.sc (X/C) good/C)")
        self.assertTrue(result[1].atom)
        self.assertTrue(result[1].parens)
        self.assertEqual(result[1].text, "X")


if __name__ == "__main__":
    unittest.main()
