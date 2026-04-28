"""Plugin-facing API for parser extensions to the Hyperbase REPL.

Parser plugins use this module to integrate with the interactive REPL
without the REPL having to know anything parser-specific. The actual
:class:`ReplSession` is implemented in :mod:`hyperbase.cli.repl`; this
module only declares the dataclass and signatures that plugins should
import for type hints.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hyperbase.hyperedge import Hyperedge
    from hyperbase.parsers.parse_result import ParseResult


@dataclass
class ReplContext:
    """Context passed to REPL hooks during ``parse_text``.

    Hooks may inspect the parse output and use ``session`` to access
    the console, formatter, settings, and the parser itself.
    """

    session: Any
    """The :class:`ReplSession` (duck-typed). Exposes ``parser``,
    ``console``, ``settings``, ``formatter``, plus the ``register_*``
    methods documented below."""

    text: str
    """The raw input text the user typed."""

    parse_result: list[ParseResult]
    """The full list returned by ``parser.parse(text)``."""

    result: ParseResult | None
    """The single :class:`ParseResult` currently being rendered. ``None``
    only when ``parse_result`` is empty (the FAILED case)."""

    edge: Hyperedge | None
    """The current result's edge (``result.edge``), or ``None`` if
    parsing produced no result."""

    tokens: list[str] | None
    """The current result's tokens, or ``None`` if absent."""

    elapsed_time: float
    """Wall-clock parse time in seconds."""


# Type aliases for hook signatures.
PreResultHook = Callable[[ReplContext], None]
"""Hook called after parsing but before the result panel is rendered."""

PostResultHook = Callable[[ReplContext], None]
"""Hook called after the result panel is rendered."""

StatsProvider = Callable[[ReplContext], list[tuple[str, str]]]
"""Provider returning extra ``(label, value)`` rows for the stats table."""

CommandHandler = Callable[[list[str]], bool]
"""REPL command handler. Receives the command arguments and returns
``True`` if the REPL should exit."""
