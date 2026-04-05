from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from os import PathLike
from pathlib import Path

from hyperbase.hyperedge import Hyperedge, hedge
from hyperbase.parsers.parse_result import ParseResult


def load_edges(
    source: str | PathLike | Iterable,
    lazy: bool = False,
) -> Iterator[Hyperedge] | list[Hyperedge]:
    """Load a sequence of hyperedges from various sources.

    *source* can be:
    - A path to a ``.jsonl`` file (one JSON object per line, each treated as
      a ``ParseResult``).
    - A path to a ``.json`` file (must contain a JSON array, items handled as
      the sequence case below).
    - A path to any other text file (one edge string per line, fed to
      ``hedge``).
    - Any iterable of items accepted by ``hedge``.  ``dict`` items are first
      converted to ``ParseResult`` via ``ParseResult.from_dict``.

    If *lazy* is ``True``, return a generator (lazy evaluation).
    If *lazy* is ``False`` (default), return a list.
    """
    gen = _generate_edges(source)
    if lazy:
        return gen
    return list(gen)


def _generate_edges(
    source: str | PathLike | Iterable,
) -> Iterator[Hyperedge]:
    path = _as_path(source)
    if path is not None:
        yield from _load_from_file(path)
    else:
        yield from _load_from_sequence(source)


def _as_path(source: str | PathLike | Iterable) -> Path | None:
    if isinstance(source, PathLike):
        return Path(source)
    if isinstance(source, str):
        p = Path(source)
        if p.is_file():
            return p
    return None


def _load_from_file(path: Path) -> Iterator[Hyperedge]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        yield from _load_jsonl(path)
    elif suffix == ".json":
        yield from _load_json(path)
    else:
        yield from _load_text(path)


def _load_jsonl(path: Path) -> Iterator[Hyperedge]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            pr = ParseResult.from_dict(d)
            yield hedge(pr)


def _load_json(path: Path) -> Iterator[Hyperedge]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    yield from _load_from_sequence(data)


def _load_text(path: Path) -> Iterator[Hyperedge]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield hedge(line)


def _load_from_sequence(items: Iterable) -> Iterator[Hyperedge]:
    for item in items:
        if isinstance(item, dict):
            pr = ParseResult.from_dict(item)
            yield hedge(pr)
        else:
            yield hedge(item)
