from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import urlparse

from trafilatura import fetch_url, extract

from hyperbase.readers.reader import Reader, register_reader, split_blocks


class UrlReader(Reader):
    def __init__(self):
        self._blocks: list[str] | None = None

    @staticmethod
    def accepts(source: str) -> bool:
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https")

    def _fetch(self, source: str) -> list[str]:
        if self._blocks is None:
            document = fetch_url(source)
            if not document:
                raise RuntimeError(f"Could not read data from URL: {source}")

            text = extract(document)
            if not text:
                text = document

            self._blocks = split_blocks(text)
        return self._blocks

    def block_count(self, source: str) -> int | None:
        return len(self._fetch(source))

    def read(self, source: str) -> Iterator[str]:
        yield from self._fetch(source)


register_reader("url", UrlReader)
