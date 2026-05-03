import unittest

from hyperbase.builders import hedge
from hyperbase.parsers.parse_result import ParseResult


class TestHyperedgeText(unittest.TestCase):
    def test_text_none_by_default(self):
        edge = hedge("(is/P.so (the/M sky/C) blue/C)")
        assert edge.text is None

    def test_atom_text_none_by_default(self):
        atom = hedge("sky/C")
        assert atom.text is None

    def test_hedge_parse_result_top_level_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        assert result.text == "The sky is blue."

    def test_hedge_parse_result_atom_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        # is/P.so -> token at position 2 -> "is"
        assert result[0].text == "is"
        # blue/C -> token at position 3 -> "blue"
        assert result[2].text == "blue"

    def test_hedge_parse_result_subedge_text(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        # (the/M sky/C) -> positions 0,1 -> "The sky"
        assert result[1].text == "The sky"
        # the/M -> position 0 -> "The"
        assert result[1][0].text == "The"
        # sky/C -> position 1 -> "sky"
        assert result[1][1].text == "sky"

    def test_hedge_parse_result_preserves_edge_structure(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        assert str(result) == "(is/P.so (the/M sky/C) blue/C)"

    def test_hedge_parse_result_neg_pos(self):
        pr = ParseResult(
            edge=hedge("(+/B a/C b/C)"),
            text="a and b",
            tokens=["a", "and", "b"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        assert result.text == "a and b"
        # +/B -> position -1 -> None
        assert result[0].text is None
        # a/C -> position 0 -> "a"
        assert result[1].text == "a"
        # b/C -> position 2 -> "b"
        assert result[2].text == "b"

    def test_hedge_parse_result_gap_tokens(self):
        pr = ParseResult(
            edge=hedge("(+/B a/C b/C)"),
            text="a and b",
            tokens=["a", "and", "b"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        # top-level overridden with full text
        assert result.text == "a and b"

    def test_hedge_parse_result_single_atom(self):
        pr = ParseResult(
            edge=hedge("hello/C"),
            text="Hello",
            tokens=["Hello"],
            tok_pos=hedge("0"),
        )
        result = hedge(pr)
        assert result.text == "Hello"
        assert result.atom
        assert str(result) == "hello/C"

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
        assert result.text == "The man says that the sky is blue."
        # say/P.so -> "says"
        assert result[0].text == "says"
        # (the/M man/C) -> "The man"
        assert result[1].text == "The man"
        # (that/T (is/P.sc (the/M sky/C) blue/C)) -> positions 3,6,4,5,7
        # min=3, max=7 -> "that the sky is blue"
        assert result[2].text == "that the sky is blue"
        # (is/P.sc (the/M sky/C) blue/C) -> positions 6,4,5,7
        # min=4, max=7 -> "the sky is blue"
        assert result[2][1].text == "the sky is blue"

    def test_hedge_parse_result_metadata_on_atoms(self):
        pr = ParseResult(
            edge=hedge("(is/P.so (the/M sky/C) blue/C)"),
            text="The sky is blue.",
            tokens=["The", "sky", "is", "blue", "."],
            tok_pos=hedge("(2 (0 1) 3)"),
        )
        result = hedge(pr)
        # is/P.so at token 2
        assert result[0].tok_pos == 2
        assert result[0].text_span == (8, 10)
        # the/M at token 0
        assert result[1][0].tok_pos == 0
        assert result[1][0].text_span == (0, 3)
        # blue/C at token 3
        assert result[2].tok_pos == 3
        assert result[2].text_span == (11, 15)
        # synthetic atom (none here, but sanity-check root tokens)
        assert result.tokens == ("The", "sky", "is", "blue", ".")

    def test_hedge_parse_result_punctuation_fidelity(self):
        # Sub-edge text should preserve the comma glued to "Hello", not
        # produce "Hello , world".
        pr = ParseResult(
            edge=hedge("(+/B hello/Cn world/Cn)"),
            text="Hello, world",
            tokens=["Hello", ",", "world"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        # Synthetic +/B has no source token; sub-edge spans hello..world.
        # No atom claims position 1 (the comma), so the run is contiguous.
        assert result.text == "Hello, world"

    def test_hedge_parse_result_real_unused_atom_splits_runs(self):
        # An edge where two of the tokens that ARE claimed by the parse fall
        # in the middle of our sub-edge's range. Not realistic to handcraft a
        # full parse, but we can simulate by giving a tok_pos tree that
        # claims positions our outer edge doesn't reference.
        pr = ParseResult(
            edge=hedge("(+/B john/Cp apples/Cn)"),
            # The wider parse claims positions 0, 4, 5, 6 -- but our edge
            # only references 0 and 6. Positions 4, 5 are claimed-but-unused
            # by THIS sub-edge, so the run must split.
            text="John, who I met yesterday, eats apples",
            tokens=[
                "John",
                ",",
                "who",
                "I",
                "met",
                "yesterday",
                ",",
                "eats",
                "apples",
            ],
            tok_pos=hedge("(-1 0 8)"),
        )
        result = hedge(pr)
        # Top-level text override is the full sentence (verbatim from pr.text).
        assert result.text == "John, who I met yesterday, eats apples"
        # john/Cp atom: position 0
        assert result[1].tok_pos == 0
        assert result[1].text == "John"
        # apples/Cn atom: position 8
        assert result[2].tok_pos == 8
        assert result[2].text == "apples"

    def test_hedge_parse_result_offset_failure_local_fallback(self):
        # A token that doesn't appear in the source text. The cursor-scan
        # returns None for that span; the affected atom falls back to the
        # tokens list, no crash.
        pr = ParseResult(
            edge=hedge("(+/B foo/Cn bar/Cn)"),
            text="something else entirely",
            tokens=["something", "missing", "entirely"],
            tok_pos=hedge("(-1 0 2)"),
        )
        result = hedge(pr)
        # Atom at position 0 located normally.
        assert result[1].tok_pos == 0
        assert result[1].text_span == (0, 9)
        # Atom at position 2 located after a missing token in between.
        assert result[2].tok_pos == 2
        assert result[2].text_span is not None


if __name__ == "__main__":
    unittest.main()
