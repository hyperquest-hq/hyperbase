from __future__ import annotations

import os
from collections.abc import Iterator

from hyperbase.readers.reader import Reader, register_reader, split_blocks


class TxtReader(Reader):
    def __init__(self):
        self._blocks: list[str] | None = None

    @staticmethod
    def accepts(source: str) -> bool:
        return os.path.isfile(source)

    def _load(self, source: str) -> list[str]:
        if self._blocks is None:
            with open(source, 'rt') as f:
                self._blocks = split_blocks(f.read())
        return self._blocks

    def block_count(self, source: str) -> int | None:
        return len(self._load(source))

    def read(self, source: str) -> Iterator[str]:
        yield from self._load(source)


register_reader('plain_text', TxtReader)
