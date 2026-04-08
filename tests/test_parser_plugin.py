"""Tests for the parser plugin system.

Covers plugin discovery, instantiation errors, and mock plugin
registration via entry points.
"""

from unittest.mock import MagicMock, patch

import pytest

from hyperbase.parsers import ParseResult, get_parser, list_parsers
from hyperbase.parsers.parser import Parser as ParserBase


class TestListParsers:
    """Tests for list_parsers()."""

    def test_returns_dict(self):
        result = list_parsers()
        assert isinstance(result, dict)

    def test_keys_are_strings(self):
        result = list_parsers()
        for key in result:
            assert isinstance(key, str)

    @patch("hyperbase.parsers.entry_points")
    def test_with_mock_entry_points(self, mock_eps):
        """Simulate installed parser plugins."""
        ep1 = MagicMock()
        ep1.name = "mock_parser"
        ep2 = MagicMock()
        ep2.name = "another_parser"
        mock_eps.return_value = [ep1, ep2]

        result = list_parsers()
        assert "mock_parser" in result
        assert "another_parser" in result
        mock_eps.assert_called_once_with(group="hyperbase.parsers")

    @patch("hyperbase.parsers.entry_points")
    def test_empty_plugins(self, mock_eps):
        """No installed plugins should return empty dict."""
        mock_eps.return_value = []
        result = list_parsers()
        assert result == {}


class TestGetParser:
    """Tests for get_parser()."""

    def test_unknown_parser_raises(self):
        with pytest.raises(ValueError, match="not installed"):
            get_parser("nonexistent_parser_xyz")

    def test_error_message_lists_available(self):
        """Error message should list available parsers."""
        try:
            get_parser("nonexistent_parser_xyz")
        except ValueError as e:
            msg = str(e)
            assert "Available parsers:" in msg

    @patch("hyperbase.parsers.entry_points")
    def test_mock_plugin_instantiation(self, mock_eps):
        """A mock plugin should be loadable and instantiable."""

        class MockParser(ParserBase):
            def __init__(self, params=None):
                super().__init__(params)

            def get_sentences(self, text):
                return [text]

            def parse_sentence(self, sentence):
                return []

        ep = MagicMock()
        ep.name = "mock"
        ep.load.return_value = MockParser
        mock_eps.return_value = [ep]

        parser = get_parser("mock", params={"lang": "en"})
        assert isinstance(parser, MockParser)
        assert parser.params == {"lang": "en"}

    @patch("hyperbase.parsers.entry_points")
    def test_plugin_load_failure(self, mock_eps):
        """If plugin load() raises, it should propagate."""
        ep = MagicMock()
        ep.name = "broken"
        ep.load.side_effect = ImportError("missing dependency")
        mock_eps.return_value = [ep]

        with pytest.raises(ImportError, match="missing dependency"):
            get_parser("broken")


class TestParserBaseClass:
    """Tests for the Parser base class methods."""

    def test_get_sentences_not_implemented(self):
        parser = ParserBase()
        with pytest.raises(NotImplementedError):
            parser.get_sentences("hello world")

    def test_parse_sentence_not_implemented(self):
        parser = ParserBase()
        with pytest.raises(NotImplementedError):
            parser.parse_sentence("hello world")

    def test_parse_uses_get_sentences(self):
        """parse() should call get_sentences then parse_sentence."""

        class TestParser(ParserBase):
            def get_sentences(self, text):
                return ["hello world", "foo bar"]

            def parse_sentence(self, sentence):
                return [MagicMock(spec=ParseResult)]

        parser = TestParser()
        results = parser.parse("any text")
        assert len(results) == 2

    def test_parse_batch_default(self):
        """Default parse_batch calls parse_sentence for each."""

        class TestParser(ParserBase):
            def get_sentences(self, text):
                return [text]

            def parse_sentence(self, sentence):
                return [MagicMock(spec=ParseResult)]

        parser = TestParser()
        results = parser.parse_batch(["s1", "s2", "s3"])
        assert len(results) == 3

    def test_parse_filters_short_sentences(self):
        """parse should skip sentences with 1 or fewer words."""

        class TestParser(ParserBase):
            def get_sentences(self, text):
                return ["hello", "hello world", "a"]

            def parse_sentence(self, sentence):
                return [MagicMock(spec=ParseResult)]

        parser = TestParser()
        results = parser.parse("ignored", batch_size=10)
        # Only "hello world" has more than 1 word
        assert len(results) == 1


class TestParseResult:
    """Tests for ParseResult serialization."""

    def test_roundtrip_json(self):
        from hyperbase.builders import hedge

        edge = hedge("(is/P.sc bob/C happy/C)")
        tok_pos = hedge("(0 1 2)")
        pr = ParseResult(
            edge=edge,
            text="bob is happy",
            tokens=["bob", "is", "happy"],
            tok_pos=tok_pos,
        )
        json_str = pr.to_json()
        pr2 = ParseResult.from_json(json_str)
        assert str(pr2.edge) == str(pr.edge)
        assert pr2.text == pr.text
        assert pr2.tokens == pr.tokens

    def test_from_dict_invalid_edge_type(self):
        with pytest.raises(TypeError, match="str or Hyperedge"):
            ParseResult.from_dict(
                {
                    "edge": 42,
                    "text": "t",
                    "tokens": [],
                    "tok_pos": "0",
                }
            )

    def test_from_dict_invalid_tok_pos_type(self):
        with pytest.raises(TypeError, match="str or Hyperedge"):
            ParseResult.from_dict(
                {
                    "edge": "a/C",
                    "text": "t",
                    "tokens": [],
                    "tok_pos": 42,
                }
            )
