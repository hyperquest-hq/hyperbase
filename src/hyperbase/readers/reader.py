from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from hyperbase.parsers.parser import Parser


_REGISTRY: dict[str, type[Reader]] = {}


def split_blocks(text: str) -> list[str]:
    """Split text into paragraph-sized blocks, detecting the separation style.

    If the text contains blank lines (one or more empty lines between
    content), they are used as paragraph separators — this handles the
    common "typewriter" convention where lines wrap at a fixed width
    and paragraphs are separated by an empty line.

    Otherwise, each non-empty line is treated as its own paragraph.
    """
    # Normalize line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if re.search(r'\n[ \t]*\n', text):
        blocks = re.split(r'\n[ \t]*\n', text)
        # In typewriter-style text, single newlines within a block are
        # just line wrapping — collapse them into spaces.
        blocks = [re.sub(r'\s*\n\s*', ' ', b) for b in blocks]
    else:
        blocks = text.split('\n')
    return [b for block in blocks if (b := block.strip())]


def register_reader(name: str, reader_cls: type[Reader]) -> None:
    """Register a reader class by name.

    Built-in readers call this at import time. Users may call it to
    register their own readers, which take priority over built-ins
    with the same name.
    """
    _REGISTRY[name] = reader_cls


def list_readers() -> dict[str, type[Reader]]:
    """Return a copy of all registered readers."""
    return dict(_REGISTRY)


def get_reader(
    source: str | None = None,
    reader: str = 'auto',
) -> Reader:
    """Return an appropriate reader instance.

    Either *source* or a named *reader* (other than ``'auto'``) must
    be provided.

    When *reader* is a specific name, looks it up directly in the
    registry (*source* is not required).

    When *reader* is ``'auto'``, *source* must be given.  The registry
    is iterated in insertion order and the first reader whose
    ``accepts(source)`` returns ``True`` is selected.

    Raises :class:`ValueError` if no reader is found or if neither
    *source* nor *reader* is provided.
    """
    if reader != 'auto':
        if reader not in _REGISTRY:
            available = ', '.join(sorted(_REGISTRY)) or '(none)'
            raise ValueError(
                f"Reader {reader!r} is not registered. "
                f"Available readers: {available}"
            )
        return _REGISTRY[reader]()

    if source is None:
        raise ValueError(
            "Either 'source' or a named 'reader' must be provided."
        )

    # Collect all readers that accept this source.
    candidates: dict[str, type[Reader]] = {
        name: cls for name, cls in _REGISTRY.items() if cls.accepts(source)
    }

    if not candidates:
        raise ValueError(
            f"No reader found that accepts source: {source!r}"
        )

    # Remove readers that a more-specific candidate declares as more general.
    general_names: set[str] = set()
    for cls in candidates.values():
        general_names.update(cls.more_general)

    specific = {
        name: cls for name, cls in candidates.items()
        if name not in general_names
    }

    # Pick the first surviving candidate (or first overall as fallback).
    chosen = specific or candidates
    return next(iter(chosen.values()))()


class Reader:
    """Base class for all readers.

    Subclasses must implement :meth:`accepts` and :meth:`read`.

    Subclasses may set ``more_general`` to a list of reader names
    that accept a superset of the sources this reader handles.
    When multiple readers accept a source, the most specific one
    (i.e. the one not listed as *more_general* by another
    accepting reader) is chosen.
    """

    more_general: list[str] = []

    @staticmethod
    def accepts(source: str) -> bool:
        """Return ``True`` if this reader can handle *source*."""
        raise NotImplementedError

    def block_count(self, source: str) -> int | None:
        """Return the number of text blocks, or ``None`` if unknown ahead of time."""
        return None

    def read(self, source: str) -> Iterator[str]:
        """Yield text blocks from *source*.

        Each block is a paragraph- or section-sized chunk of text
        appropriate for the source type.
        """
        raise NotImplementedError

    def read_to_text(
        self,
        source: str,
        output: str,
        progress: bool = False,
    ) -> None:
        """Read *source* and write raw text blocks to a plain text file.

        Each block is separated by a blank line.
        """
        if progress:
            from tqdm import tqdm
            total = self.block_count(source)
            pbar = tqdm(total=total, desc='Reading', unit='block')
        first = True
        with open(output, 'w') as f:
            for block in self.read(source):
                if not first:
                    f.write('\n\n')
                f.write(block)
                first = False
                if progress:
                    pbar.update(1)
            f.write('\n')
        if progress:
            pbar.close()

    def read_and_parse(
        self,
        source: str,
        parser: Parser,
        batch_size: int = 8,
        progress: bool = False,
    ) -> Iterator[list[dict[str, Any]]]:
        """Read text blocks and parse each one with *parser*.

        Yields one list of parse results per text block, leveraging
        the parser's built-in batch processing.
        """
        if progress:
            from tqdm import tqdm
            total = self.block_count(source)
            pbar = tqdm(total=total, desc='Parsing', unit='block')
        for block in self.read(source):
            results = parser.parse_text(block, batch_size=batch_size)
            if progress:
                pbar.update(1)
            if results:
                yield results
        if progress:
            pbar.close()

    def parse_to_jsonl(
        self,
        source: str,
        output: str,
        parser: Parser,
        batch_size: int = 8,
        progress: bool = False,
    ) -> None:
        """Read *source*, parse every block, and write results to a JSONL file.

        Each ParseResult is serialized as one JSON line.
        """
        with open(output, 'w') as f:
            for results in self.read_and_parse(
                source, parser, batch_size=batch_size, progress=progress,
            ):
                for result in results:
                    f.write(result.to_json() + '\n')
