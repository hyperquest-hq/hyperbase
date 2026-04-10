from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hyperbase.parsers.parse_result import ParseResult


DEFAULT_MAX_DEPTH = 50


class Parser:
    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params: dict[str, Any] = params or {}
        self.max_depth: int = int(self.params.get("max_depth", DEFAULT_MAX_DEPTH))

    @classmethod
    def accepted_params(cls) -> dict[str, dict[str, Any]]:
        """Return the set of parameters this parser accepts.

        Each key is a parameter name. The value is a dict with:
        - ``"type"``: the expected Python type (e.g. ``str``, ``int``).
        - ``"default"``: the default value (or ``None`` if required).
        - ``"description"``: a short human-readable description.
        - ``"required"``: whether the parameter must be provided.

        Subclasses should merge their own parameters with the result of
        ``super().accepted_params()`` so that common parameters like
        ``max_depth`` remain discoverable.
        """
        return {
            "max_depth": {
                "type": int,
                "default": DEFAULT_MAX_DEPTH,
                "description": (
                    "Maximum allowed nesting depth for produced edges. "
                    "Sentences whose parse exceeds this depth are rejected "
                    "rather than processed, to avoid pathological inputs "
                    "blowing the Python stack."
                ),
                "required": False,
            },
        }

    def get_sentences(self, text: str) -> list[str]:
        raise NotImplementedError

    def parse_sentence(self, sentence: str) -> list[ParseResult]:
        raise NotImplementedError

    def parse_batch(self, sentences: list[str]) -> list[list[ParseResult]]:
        """Parse multiple sentences. Subclasses may override with a
        true batched implementation (e.g. a single CT2 call)."""
        return [self.parse_sentence(sentence) for sentence in sentences]

    def parse(
        self, text: str, batch_size: int = 8, progress: bool = False
    ) -> list[ParseResult]:
        """Sentensize text, then parse all sentences in batches.

        Returns a flat list of parse results across all sentences.
        """
        sentences = [s for s in self.get_sentences(text) if len(s.split()) > 1]
        batch_range = range(0, len(sentences), batch_size)
        if progress:
            from tqdm import tqdm  # type: ignore[import-untyped]

            batch_range = tqdm(batch_range, desc="Parsing batches", leave=False)
        results: list[ParseResult] = []
        for i in batch_range:
            batch = sentences[i : i + batch_size]
            for sentence_results in self.parse_batch(batch):
                results.extend(sentence_results)
        return results

    def parse_to_jsonl(
        self,
        text: str,
        output: str,
        batch_size: int = 8,
        progress: bool = False,
    ) -> None:
        """Parse *text* and write results to a JSONL file.

        Each ParseResult is serialized as one JSON line.
        """
        with open(output, "w") as f:
            for result in self.parse(text, batch_size=batch_size, progress=progress):
                f.write(result.to_json() + "\n")

    def parse_source(
        self,
        source: str,
        reader: str = "auto",
        batch_size: int = 8,
        progress: bool = False,
    ) -> Iterator[list[ParseResult]]:
        """Read text blocks from *source* and parse each one.

        Automatically selects (or explicitly uses) a reader, then
        yields one list of parse results per text block.
        """
        from hyperbase.readers.reader import get_reader

        rdr = get_reader(source, reader=reader)
        yield from rdr.read_and_parse(
            source,
            self,
            batch_size=batch_size,
            progress=progress,
        )

    def parse_source_to_jsonl(
        self,
        source: str,
        output: str,
        reader: str = "auto",
        batch_size: int = 8,
        progress: bool = False,
    ) -> None:
        """Read *source*, parse every block, and write results to a JSONL file.

        Each ParseResult is serialized as one JSON line.
        """
        with open(output, "w") as f:
            for results in self.parse_source(
                source,
                reader=reader,
                batch_size=batch_size,
                progress=progress,
            ):
                for result in results:
                    f.write(result.to_json() + "\n")
