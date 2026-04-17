from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

from trafilatura import bare_extraction, fetch_url

from hyperbase.readers.reader import Reader, register_reader, split_blocks


class UrlReader(Reader):
    def __init__(self) -> None:
        self._blocks: list[str] | None = None
        self._title: str | None = None

    @staticmethod
    def accepts(source: str) -> bool:
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https")

    def _fetch(self, source: str) -> list[str]:
        if self._blocks is None:
            document = fetch_url(source)
            if not document:
                raise RuntimeError(f"Could not read data from URL: {source}")

            result = bare_extraction(document, url=source)
            text = result.get("text") if result else None
            self._title = result.get("title") if result else None
            if not text:
                text = document

            self._blocks = split_blocks(text)
        return self._blocks

    def block_count(self, source: str) -> int | None:
        return len(self._fetch(source))

    def source_info(self, source: str) -> dict[str, Any]:
        self._fetch(source)
        info: dict[str, Any] = {"source_type": "url", "source": source}
        if self._title:
            info["title"] = self._title
        return info

    def read(self, source: str) -> Iterator[str]:
        yield from self._fetch(source)


register_reader("url", UrlReader)
