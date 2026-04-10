"""Tests for malformed input resilience.

Covers deeply nested edges, recursion limits, broken edge strings,
and edge cases in builders/hyperedge construction.
"""

import pytest

from hyperbase.builders import hedge, split_edge_str
from hyperbase.hyperedge import Atom, Hyperedge


class TestDeeplyNestedEdges:
    """Ensure deeply nested edges don't blow the stack on recursive operations."""

    @staticmethod
    def _build_nested(depth: int) -> Hyperedge:
        """Build a left-nested modifier chain: (m0/M (m1/M (m2/M ... thing/C)))."""
        edge = Atom("thing/C")
        for i in range(depth):
            edge = Hyperedge((Atom(f"m{i}/M"), edge))
        return edge

    def test_depth_100(self):
        edge = self._build_nested(100)
        assert edge.depth() == 100
        assert edge.size() == 101  # 100 modifier atoms + 1 thing/C

    def test_depth_beyond_recursion_limit_raises(self):
        """Extremely deep nesting hits Python's recursion limit."""
        edge = self._build_nested(500)
        with pytest.raises(RecursionError):
            edge.size()

    def test_depth_cached_properties(self):
        """Cached properties should survive repeated access on deep edges."""
        edge = self._build_nested(200)
        d1 = edge.depth()
        s1 = edge.size()
        assert edge.depth() == d1
        assert edge.size() == s1

    def test_deep_contains(self):
        """contains() on deeply nested structure."""
        edge = self._build_nested(100)
        assert edge.contains(Atom("thing/C"))

    def test_deep_subedges(self):
        """subedges() on deeply nested structure."""
        edge = self._build_nested(50)
        subs = edge.subedges()
        # 50 nested edges + 51 atoms
        assert len(subs) > 50

    def test_deep_atoms(self):
        """atoms() on deeply nested structure."""
        edge = self._build_nested(50)
        all_atoms = edge.all_atoms()
        # 50 modifier atoms + 1 thing/C
        assert len(all_atoms) == 51

    def test_deep_simplify(self):
        """simplify() on a deeply nested edge should not crash."""
        edge = self._build_nested(100)
        simplified = edge.simplify()
        assert simplified is not None

    def test_deep_normalise(self):
        """normalise() on a deeply nested modifier chain."""
        edge = self._build_nested(50)
        normalised = edge.normalise()
        assert normalised is not None


class TestBrokenEdgeStrings:
    """Tests for malformed string inputs to hedge() and split_edge_str()."""

    def test_unbalanced_open_paren(self):
        with pytest.raises(ValueError, match="Unbalanced parenthesis"):
            split_edge_str("(a b")

    def test_unbalanced_close_paren(self):
        with pytest.raises(ValueError, match="Unbalanced parenthesis"):
            split_edge_str("a b)")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            hedge("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="empty"):
            hedge("   ")

    def test_empty_parens(self):
        with pytest.raises(ValueError, match="empty"):
            hedge("()")

    def test_nested_empty_parens(self):
        # Inner "()" is actually a valid parenthesized empty — should error
        with pytest.raises(ValueError):
            hedge("(a ())")

    def test_deeply_nested_parens_string(self):
        """Parsing a string with 200 levels of nesting."""
        s = "(" * 200 + "a/C b/C" + ")" * 200
        edge = hedge(s)
        assert edge is not None
        assert edge.depth() > 0

    def test_extremely_deeply_nested_parens_string(self):
        """hedge() must not blow Python's stack on pathological nesting.

        Regression test: previously hedge() recursed once per nesting
        level (~2 Python frames per level), so anything beyond ~450
        levels raised RecursionError mid-parse — and the error leaked
        out through except handlers because they themselves needed
        stack frames they didn't have. The string parser is now
        iterative and bounded only by available memory.
        """
        depth = 5000
        s = "(" * depth + "a/C b/C" + ")" * depth
        edge = hedge(s)
        assert edge is not None

    def test_invalid_type_input(self):
        with pytest.raises(TypeError):
            hedge(42)

    def test_none_input(self):
        with pytest.raises(TypeError):
            hedge(None)

    def test_single_atom_in_parens(self):
        """(atom) should produce an Atom with parens=True."""
        edge = hedge("(hello/C)")
        assert edge.atom
        assert isinstance(edge, Atom)
        assert edge.parens

    def test_newlines_in_edge_string(self):
        """Newlines in edge strings should be treated as spaces."""
        edge = hedge("(is/P.sc\nbob/C\nhappy/C)")
        assert len(edge) == 3

    def test_extra_spaces(self):
        """Multiple spaces between tokens should be handled."""
        edge = hedge("(is/P.sc   bob/C   happy/C)")
        assert len(edge) == 3


class TestMalformedAtoms:
    """Tests for atoms with unusual or broken structure."""

    def test_atom_no_type(self):
        """Atom with no type part (just root)."""
        atom = Atom("hello")
        assert atom.root() == "hello"
        # Default type for bare root is J (conjunction)
        assert atom.mtype() == "J"

    def test_atom_empty_root(self):
        """Atom with empty root but has type."""
        atom = Atom("/C")
        assert atom.root() == ""
        assert atom.type() == "C"

    def test_atom_many_parts(self):
        """Atom with many slash-separated parts."""
        atom = Atom("hello/Cp.so/en/1/extra")
        parts = atom.parts()
        assert len(parts) == 5
        assert parts[0] == "hello"

    def test_atom_special_chars_in_root(self):
        """Atom with percent-encoded characters."""
        atom = Atom("new%20york/C")
        assert atom.root() == "new%20york"
        assert atom.label() == "new york"
