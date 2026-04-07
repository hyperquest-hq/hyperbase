"""Performance regression tests for pattern matching.

These tests ensure that pattern matching operations complete within
reasonable time bounds, catching algorithmic regressions (e.g.
exponential blowup in argrole matching).
"""

import time

import pytest

from hyperbase.builders import hedge
from hyperbase.patterns.matcher import _MAX_ARGROLE_ITEMS, match_pattern


class TestPatternMatchingPerformance:
    """Guard against algorithmic regressions in the Matcher."""

    def test_simple_match_is_fast(self):
        """A simple exact match should complete in well under 100ms."""
        edge = hedge("(is/P.sc bob/C happy/C)")
        pattern = hedge("(is/P.sc bob/C happy/C)")
        start = time.perf_counter()
        for _ in range(1000):
            match_pattern(edge, pattern)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"1000 simple matches took {elapsed:.2f}s"

    def test_wildcard_match_is_fast(self):
        """Wildcard matching should not degrade badly."""
        edge = hedge("(is/P.sc bob/C happy/C)")
        pattern = hedge("(is/P.sc * *)")
        start = time.perf_counter()
        for _ in range(1000):
            match_pattern(edge, pattern)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"1000 wildcard matches took {elapsed:.2f}s"

    def test_variable_match_is_fast(self):
        """Variable binding shouldn't be significantly slower."""
        edge = hedge("(is/P.sc bob/C happy/C)")
        pattern = hedge("(is/P.sc *X *Y)")
        start = time.perf_counter()
        for _ in range(1000):
            result = match_pattern(edge, pattern)
            assert len(result) > 0
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"1000 variable matches took {elapsed:.2f}s"

    def test_open_ended_pattern_is_fast(self):
        """Open-ended patterns (...) on edges with many args."""
        edge = hedge("(is/P.scox bob/C happy/C thing/C (to/T place/C))")
        pattern = hedge("(is/P.sc * * ...)")
        start = time.perf_counter()
        for _ in range(500):
            match_pattern(edge, pattern)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"500 open-ended matches took {elapsed:.2f}s"

    def test_argrole_matching_bounded(self):
        """Argrole-based matching with max allowed items shouldn't explode."""
        # Build an edge with _MAX_ARGROLE_ITEMS arguments
        n = _MAX_ARGROLE_ITEMS
        roles = "s" + "x" * (n - 1)
        args = " ".join(f"a{i}/C" for i in range(n))
        edge_str = f"(do/P.{roles} {args})"
        edge = hedge(edge_str)

        pattern = hedge(f"(do/P.{roles} {args})")
        start = time.perf_counter()
        result = match_pattern(edge, pattern)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"Max argrole match took {elapsed:.2f}s"
        assert len(result) > 0

    def test_argrole_limit_exceeded(self):
        """Exceeding _MAX_ARGROLE_ITEMS for a single role should raise ValueError."""
        # Build edge with 11 arguments all having the same role 'x',
        # so arguments_with_role('x') returns 11 items (> limit of 10).
        n = _MAX_ARGROLE_ITEMS + 1
        roles = "x" * n
        args = " ".join(f"a{i}/C" for i in range(n))
        edge_str = f"(do/P.{{{roles}}} {args})"
        edge = hedge(edge_str)

        # Pattern: same structure but with wildcards to force argrole path
        pat_args = " ".join("*" for _ in range(n))
        pattern_str = f"(do/P.{{{roles}}} {pat_args})"
        pattern = hedge(pattern_str)

        with pytest.raises(ValueError, match="exceeding limit"):
            match_pattern(edge, pattern)

    def test_no_match_exits_quickly(self):
        """Non-matching patterns should fail fast."""
        edge = hedge("(is/P.sc bob/C happy/C)")
        pattern = hedge("(runs/P.s *X)")
        start = time.perf_counter()
        for _ in range(1000):
            result = match_pattern(edge, pattern)
            assert len(result) == 0
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"1000 non-matches took {elapsed:.2f}s"

    def test_deep_edge_matching(self):
        """Matching on a moderately deep edge shouldn't be slow."""
        edge = hedge(
            "(is/P.sc (the/M (big/M (very/M (old/M house/C)))) (in/T (the/M city/C)))"
        )
        pattern = hedge("(is/P.sc (the/M *X) *Y)")
        start = time.perf_counter()
        for _ in range(500):
            result = match_pattern(edge, pattern)
            assert len(result) > 0
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"500 deep matches took {elapsed:.2f}s"


class TestRecursivePropertyPerformance:
    """Ensure cached property access is fast on large edges."""

    def test_size_depth_cached_fast(self):
        """Repeated size()/depth() calls should be near-instant due to caching."""
        # Build a wide edge
        args = " ".join(f"a{i}/C" for i in range(50))
        edge = hedge(f"(and/J {args})")

        # First call computes
        _ = edge.size()
        _ = edge.depth()

        # Repeated calls should be cached
        start = time.perf_counter()
        for _ in range(10000):
            edge.size()
            edge.depth()
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"20000 cached property accesses took {elapsed:.2f}s"

    def test_type_inference_cached(self):
        """type() inference should be cached after first call."""
        edge = hedge("(is/P.sc (the/M bob/C) happy/C)")
        _ = edge.type()

        start = time.perf_counter()
        for _ in range(10000):
            edge.type()
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"10000 type() calls took {elapsed:.2f}s"
