from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from hyperbase.readers.reader import Reader, register_reader, split_blocks


class TxtReader(Reader):
    def __init__(self) -> None:
        self._blocks: list[str] | None = None

    @staticmethod
    def accepts(source: str) -> bool:
        return os.path.isfile(source)

    def _load(self, source: str) -> list[str]:
        if self._blocks is None:
            with open(source) as f:
                self._blocks = split_blocks(f.read())
        return self._blocks

    def block_count(self, source: str) -> int | None:
        return len(self._load(source))

    def source_info(self, source: str) -> dict[str, Any]:
        return {"source_type": "txt", "source": os.path.basename(source)}

    def read(self, source: str) -> Iterator[str]:
        yield from self._load(source)


register_reader("plain_text", TxtReader)
