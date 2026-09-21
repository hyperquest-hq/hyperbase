from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hyperbase.parsers.correctness import CorrectnessCheck
    from hyperbase.parsers.result import ParseResult


DEFAULT_MAX_DEPTH = 25


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
        - ``"reload"`` (optional, default ``True``): whether changing
          this setting via ``/set`` requires re-instantiating the
          parser. When ``False`` the REPL calls
          :meth:`apply_live_setting` on the live instance instead, and
          the value is excluded from :meth:`cache_key_from_settings`.

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
                "reload": False,
            },
        }

    @classmethod
    def cache_key_from_settings(cls, settings: dict[str, Any]) -> tuple:
        """Build a cache key tuple from a settings dict.

        The default implementation produces one ``(name, value)`` pair
        per init-time entry in :meth:`accepted_params` (i.e. params
        whose ``"reload"`` is not ``False``), sorted by name. Two
        settings dicts that yield the same key are guaranteed to
        produce equivalent parser instances; live-applicable settings
        are excluded because they're mutated on the existing instance.
        """
        params = cls.accepted_params()
        names = sorted(
            name for name, info in params.items() if info.get("reload", True)
        )
        return tuple((name, settings.get(name)) for name in names)

    def apply_live_setting(self, name: str, value: Any) -> None:  # noqa: ANN401
        """Apply a live-changeable setting (``"reload": False``) to this
        running parser instance, without rebuilding it.

        The default implementation updates ``self.params[name]`` and
        ``setattr(self, name, value)``. Subclasses should override when
        the attribute name differs from the param name, when the value
        needs clamping/coercion beyond the REPL's type cast, or when a
        side effect is required (e.g. updating a library's RNG seed).
        Overrides may delegate to ``super().apply_live_setting(...)``
        after performing their custom step.
        """
        self.params[name] = value
        setattr(self, name, value)

    @classmethod
    def format_cache_key(cls, cache_key: tuple) -> str:
        """Render a cache key produced by :meth:`cache_key_from_settings`
        as a human-readable string for the REPL ``/parsers`` command."""
        return ", ".join(f"{name}={value}" for name, value in cache_key)

    def install_repl(self, session: Any) -> None:  # noqa: ANN401
        """Hook for parser plugins to extend the Hyperbase REPL.

        Override this to register parser-specific REPL behavior on
        *session* (a :class:`hyperbase.cli.repl.ReplSession`). The
        session exposes the following registration methods:

        - ``register_command(name, help, handler)`` -- add a slash
          command callable as ``/name``.
        - ``register_setting(name, default, type_, description="")``
          -- expose an extra REPL-only setting (e.g. a display
          toggle) that can be changed via ``/set``.
        - ``register_pre_result_hook(hook)`` -- run *hook* after
          parsing but before the parse result panel is rendered.
        - ``register_post_result_hook(hook)`` -- run *hook* after the
          parse result panel is rendered.
        - ``register_stats_provider(provider)`` -- supply extra
          ``(label, value)`` rows for the statistics table.
        - ``register_diagnostics_provider(provider)`` -- render
          detailed parse diagnostics (atoms, attempts, traces, ...)
          to ``ctx.session.console``. Invoked after the result panel
          only when the built-in ``diagnostics`` setting is enabled
          (``/set diagnostics on``). Use this to expose information for
          debugging and improving the parser.

        Hooks receive a :class:`~hyperbase.parsers.repl.ReplContext`
        object. The default implementation is a no-op.
        """

    def correctness_checks(self) -> list[CorrectnessCheck]:
        """Extra correctness checks this parser contributes to the parse gate.

        :func:`hyperbase.parsers.correctness.check_parse_correctness` runs the
        checks returned here after its own, whenever it is called with
        ``parser=``, and merges what they report into the same error map. Use
        this for what *this parser* cannot represent but hyperbase has no reason
        to forbid in general: a model's vocabulary, a tokenizer invariant, a
        structure the architecture can never emit. A rule that holds for every
        Semantic Hypergraph belongs in hyperbase instead.

        A check takes a :class:`~hyperbase.parsers.correctness.CheckContext`
        (the edge, its tokens, and the optional ``tok_pos``/``text``/``strict``)
        and returns an
        :data:`~hyperbase.parsers.correctness.ErrorMap`: subedges -- or a string
        naming the class of problem, as the built-in ``"token-matching"`` does --
        mapped to lists of ``(code, message, severity)``, where severity ``0`` is
        worst. Return an empty dict when there is nothing to report.

        Checks are **additive only**. What a check returns is merged in; it is
        never used to remove or relax what the built-in checks found, so a parser
        can make the gate stricter for its own output but never more lenient.
        Each check is isolated -- one that raises, or returns a malformed map, is
        reported under ``"parser-checks"`` and the others still run.

        The default implementation returns no checks.

        Note that ``check_parse_correctness`` only reaches these when the caller
        has the parser on hand. A parser whose own pipeline assembles parses
        somewhere it does not (a worker subprocess, say -- a ``Parser`` should
        never be pickled into one) calls
        :func:`~hyperbase.parsers.correctness.run_parser_checks` there with
        module-level check functions instead.
        """
        return []

    def close(self) -> None:
        """Release any resources held by this parser (subprocess pools, open
        files, GPU contexts, ...).

        The default is a no-op. Drivers that run to completion and then exit
        hard (e.g. via ``os._exit``, which skips atexit and ``__del__``) should
        call this first, so a parser's worker subprocesses are shut down rather
        than orphaned. Implementations must be idempotent.
        """

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
