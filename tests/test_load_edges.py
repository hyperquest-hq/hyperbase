import json
import types
import unittest
from collections.abc import Iterator
from pathlib import Path
from tempfile import NamedTemporaryFile

from hyperbase.hyperedge import hedge
from hyperbase.load_edges import load_edges
from hyperbase.parsers.parse_result import ParseResult


def _make_parse_result() -> ParseResult:
    edge = hedge("(is a/1 b/1)")
    tok_pos = hedge("(1 0 2)")
    return ParseResult(
        edge=edge,
        text="a is b",
        tokens=["a", "is", "b"],
        tok_pos=tok_pos,
    )


class TestLoadEdgesFromSequence(unittest.TestCase):
    def test_list_of_strings(self):
        edges = load_edges(["(is a/1 b/1)", "(src x/1 y/1)"])
        assert isinstance(edges, list)
        assert len(edges) == 2
        assert str(edges[0]) == "(is a/1 b/1)"
        assert str(edges[1]) == "(src x/1 y/1)"

    def test_list_of_hyperedges(self):
        h1 = hedge("(is a/1 b/1)")
        h2 = hedge("(src x/1 y/1)")
        edges = load_edges([h1, h2])
        assert edges[0] == h1
        assert edges[1] == h2

    def test_list_of_dicts(self):
        pr = _make_parse_result()
        edges = load_edges([pr.to_dict()])
        assert len(edges) == 1
        assert str(edges[0][0]) == "is"

    def test_mixed_types(self):
        pr = _make_parse_result()
        edges = load_edges(["(src x/1 y/1)", pr.to_dict(), hedge("hello/1")])
        assert len(edges) == 3

    def test_generator_input(self):
        def gen() -> Iterator[str]:
            yield "(is a/1 b/1)"
            yield "(src x/1 y/1)"

        edges = load_edges(gen())
        assert len(edges) == 2

    def test_parse_result_items(self):
        pr = _make_parse_result()
        edges = load_edges([pr])
        assert len(edges) == 1


class TestLoadEdgesLazy(unittest.TestCase):
    def test_lazy_returns_generator(self):
        result = load_edges(["(is a/1 b/1)"], lazy=True)
        assert isinstance(result, types.GeneratorType)
        edges = list(result)
        assert len(edges) == 1
        assert str(edges[0]) == "(is a/1 b/1)"

    def test_eager_returns_list(self):
        result = load_edges(["(is a/1 b/1)"], lazy=False)
        assert isinstance(result, list)


class TestLoadEdgesFromTextFile(unittest.TestCase):
    def test_text_file(self):
        with NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("(is a/1 b/1)\n")
            f.write("\n")
            f.write("(src x/1 y/1)\n")
            path = f.name

        edges = load_edges(path)
        assert len(edges) == 2
        assert str(edges[0]) == "(is a/1 b/1)"
        assert str(edges[1]) == "(src x/1 y/1)"
        Path(path).unlink()

    def test_text_file_with_path_object(self):
        with NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("hello/1\n")
            path = Path(f.name)

        edges = load_edges(path)
        assert len(edges) == 1
        assert str(edges[0]) == "hello/1"
        path.unlink()


class TestLoadEdgesFromJsonlFile(unittest.TestCase):
    def test_jsonl_file(self):
        pr1 = _make_parse_result()
        pr2 = _make_parse_result()

        with NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write(pr1.to_json() + "\n")
            f.write("\n")
            f.write(pr2.to_json() + "\n")
            path = f.name

        edges = load_edges(path)
        assert len(edges) == 2
        Path(path).unlink()


class TestLoadEdgesFromJsonFile(unittest.TestCase):
    def test_json_file_with_strings(self):
        data = ["(is a/1 b/1)", "(src x/1 y/1)"]
        with NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            path = f.name

        edges = load_edges(path)
        assert len(edges) == 2
        assert str(edges[0]) == "(is a/1 b/1)"
        Path(path).unlink()

    def test_json_file_with_dicts(self):
        pr = _make_parse_result()
        data = [pr.to_dict()]
        with NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            path = f.name

        edges = load_edges(path)
        assert len(edges) == 1
        Path(path).unlink()


class TestLoadEdgesStringNotFile(unittest.TestCase):
    def test_string_not_existing_file_iterates_chars(self):
        """A string that is not an existing file path is treated as an
        iterable of characters, each fed to hedge as an atom."""
        edges = load_edges("ab")
        assert len(edges) == 2
        assert str(edges[0]) == "a"
        assert str(edges[1]) == "b"
