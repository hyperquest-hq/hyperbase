"""Tests for the reader plugin system.

Covers reader registration, auto-detection, specificity ranking,
split_blocks edge cases, and error paths.
"""

import os
import tempfile

import pytest

from hyperbase.readers.reader import (
    _REGISTRY,
    Reader,
    get_reader,
    list_readers,
    register_reader,
    split_blocks,
)


class TestSplitBlocks:
    """Edge cases for split_blocks()."""

    def test_empty_string(self):
        assert split_blocks("") == []

    def test_whitespace_only(self):
        assert split_blocks("   \n\n   ") == []

    def test_single_line(self):
        assert split_blocks("hello world") == ["hello world"]

    def test_blank_line_separation(self):
        text = "First paragraph.\n\nSecond paragraph."
        blocks = split_blocks(text)
        assert len(blocks) == 2
        assert blocks[0] == "First paragraph."
        assert blocks[1] == "Second paragraph."

    def test_typewriter_line_wrapping(self):
        """Lines within a paragraph (no blank lines) should be joined."""
        text = "This is a long\nline that wraps\nat 40 columns.\n\nNew paragraph here."
        blocks = split_blocks(text)
        assert len(blocks) == 2
        assert blocks[0] == "This is a long line that wraps at 40 columns."
        assert blocks[1] == "New paragraph here."

    def test_no_blank_lines_each_line_is_block(self):
        """Without blank lines, each line becomes its own block."""
        text = "line one\nline two\nline three"
        blocks = split_blocks(text)
        assert len(blocks) == 3

    def test_crlf_normalized(self):
        text = "first\r\n\r\nsecond"
        blocks = split_blocks(text)
        assert len(blocks) == 2

    def test_cr_only_normalized(self):
        text = "first\r\rsecond"
        blocks = split_blocks(text)
        assert len(blocks) == 2

    def test_multiple_blank_lines(self):
        text = "first\n\n\n\nsecond"
        blocks = split_blocks(text)
        assert len(blocks) == 2

    def test_tabs_in_blank_lines(self):
        """Blank lines with only tabs should still be separators."""
        text = "first\n\t\nsecond"
        blocks = split_blocks(text)
        assert len(blocks) == 2

    def test_leading_trailing_whitespace_stripped(self):
        text = "  hello  \n\n  world  "
        blocks = split_blocks(text)
        assert blocks == ["hello", "world"]


class TestReaderRegistry:
    """Tests for register_reader, list_readers, get_reader."""

    def setup_method(self):
        """Save registry state to restore after each test."""
        self._saved_registry = dict(_REGISTRY)

    def teardown_method(self):
        """Restore registry state."""
        _REGISTRY.clear()
        _REGISTRY.update(self._saved_registry)

    def test_register_and_list(self):
        class DummyReader(Reader):
            @staticmethod
            def accepts(source):
                return False

            def read(self, source):
                yield "dummy"

        register_reader("dummy", DummyReader)
        readers = list_readers()
        assert "dummy" in readers
        assert readers["dummy"] is DummyReader

    def test_register_overwrites(self):
        class R1(Reader):
            @staticmethod
            def accepts(source):
                return False

            def read(self, source):
                yield "r1"

        class R2(Reader):
            @staticmethod
            def accepts(source):
                return False

            def read(self, source):
                yield "r2"

        register_reader("test", R1)
        register_reader("test", R2)
        assert list_readers()["test"] is R2

    def test_get_reader_by_name(self):
        class Named(Reader):
            @staticmethod
            def accepts(source):
                return True

            def read(self, source):
                yield "named"

        register_reader("named_reader", Named)
        reader = get_reader(reader="named_reader")
        assert isinstance(reader, Named)

    def test_get_reader_unknown_name(self):
        with pytest.raises(ValueError, match="not registered"):
            get_reader(reader="nonexistent_reader_xyz")

    def test_get_reader_auto_no_source(self):
        with pytest.raises(ValueError, match="Either 'source' or"):
            get_reader(reader="auto")

    def test_get_reader_auto_no_match(self):
        """Auto-detection with a source no reader accepts."""
        # Clear all readers so nothing matches
        _REGISTRY.clear()
        with pytest.raises(ValueError, match="No reader found"):
            get_reader(source="/nonexistent/path/to/nothing.xyz")

    def test_get_reader_auto_selects_accepting(self):
        class AlwaysAccepts(Reader):
            @staticmethod
            def accepts(source):
                return True

            def read(self, source):
                yield source

        register_reader("always", AlwaysAccepts)
        reader = get_reader(source="anything")
        assert isinstance(reader, AlwaysAccepts)

    def test_specificity_ranking(self):
        """More-specific reader should be preferred over more-general one."""

        class GeneralReader(Reader):
            @staticmethod
            def accepts(source):
                return True

            def read(self, source):
                yield "general"

        class SpecificReader(Reader):
            more_general = ("general_r",)

            @staticmethod
            def accepts(source):
                return True

            def read(self, source):
                yield "specific"

        register_reader("general_r", GeneralReader)
        register_reader("specific_r", SpecificReader)

        reader = get_reader(source="test")
        # specific_r declares general_r as more_general, so specific_r wins
        assert isinstance(reader, SpecificReader)


class TestTxtReader:
    """Integration tests for the built-in TxtReader."""

    def test_reads_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world.\n\nSecond paragraph.")
            f.flush()
            path = f.name

        try:
            reader = get_reader(source=path)
            blocks = list(reader.read(path))
            assert len(blocks) == 2
            assert blocks[0] == "Hello world."
        finally:
            os.unlink(path)

    def test_block_count(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("One.\n\nTwo.\n\nThree.")
            f.flush()
            path = f.name

        try:
            reader = get_reader(source=path)
            assert reader.block_count(path) == 3
        finally:
            os.unlink(path)

    def test_read_to_text(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Alpha.\n\nBeta.")
            f.flush()
            src = f.name

        out = src + ".out"
        try:
            reader = get_reader(source=src)
            reader.read_to_text(src, out)
            with open(out) as f:
                content = f.read()
            assert "Alpha." in content
            assert "Beta." in content
        finally:
            os.unlink(src)
            if os.path.exists(out):
                os.unlink(out)


class TestReaderBaseClass:
    """Tests for the Reader base class defaults."""

    def test_accepts_not_implemented(self):
        with pytest.raises(NotImplementedError):
            Reader.accepts("anything")

    def test_read_not_implemented(self):
        reader = Reader()
        with pytest.raises(NotImplementedError):
            list(reader.read("anything"))

    def test_block_count_default_none(self):
        reader = Reader()
        assert reader.block_count("anything") is None

    def test_more_general_default_empty(self):
        reader = Reader()
        assert reader.more_general == ()
