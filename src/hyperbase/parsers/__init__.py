from importlib.metadata import EntryPoint, entry_points
from typing import Any

from hyperbase.parsers.parse_result import ParseResult
from hyperbase.parsers.parser import Parser
from hyperbase.parsers.repl_api import ReplContext


def list_parsers() -> dict[str, EntryPoint]:
    """Return all installed parser plugins.

    Each plugin registers via the ``hyperbase.parsers`` entry-point group
    in its ``pyproject.toml``::

        [project.entry-points."hyperbase.parsers"]
        myparser = "my_package:MyParser"
    """
    eps = entry_points(group="hyperbase.parsers")
    return {ep.name: ep for ep in eps}


def get_parser(
    name: str, params: dict[str, Any] | None = None, **kwargs: object
) -> Parser:
    """Instantiate a parser plugin by name.

    Looks up *name* in the ``hyperbase.parsers`` entry-point group and
    returns an instance of the registered :class:`Parser` subclass.

    *params* is a dictionary of parser parameters.  For backwards
    compatibility, keyword arguments are merged into *params* (explicit
    *params* entries take precedence).

    Raises :class:`ValueError` if the parser is not installed.
    """
    parsers = list_parsers()
    if name not in parsers:
        available = ", ".join(sorted(parsers)) or "(none)"
        raise ValueError(
            f"Parser {name!r} is not installed. Available parsers: {available}"
        )
    merged: dict[str, Any] = {**kwargs, **(params or {})}
    cls = parsers[name].load()
    return cls(merged)


__all__ = ["ParseResult", "Parser", "ReplContext", "get_parser", "list_parsers"]
