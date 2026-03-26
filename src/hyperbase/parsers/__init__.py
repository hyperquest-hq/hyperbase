from importlib.metadata import entry_points, EntryPoint
from typing import Any

from hyperbase.parsers.parser import Parser


def list_parsers() -> dict[str, EntryPoint]:
    """Return all installed parser plugins.

    Each plugin registers via the ``hyperbase.parsers`` entry-point group
    in its ``pyproject.toml``::

        [project.entry-points."hyperbase.parsers"]
        alphabeta = "hyperparser_alphabeta:ParserAlphaBeta"
    """
    eps = entry_points(group="hyperbase.parsers")
    return {ep.name: ep for ep in eps}


def get_parser(name: str, **kwargs: Any) -> Parser:
    """Instantiate a parser plugin by name.

    Looks up *name* in the ``hyperbase.parsers`` entry-point group and
    returns an instance of the registered :class:`Parser` subclass.

    Raises :class:`ValueError` if the parser is not installed.
    """
    parsers = list_parsers()
    if name not in parsers:
        available = ", ".join(sorted(parsers)) or "(none)"
        raise ValueError(
            f"Parser {name!r} is not installed. "
            f"Available parsers: {available}"
        )
    cls = parsers[name].load()
    return cls(**kwargs)  # type: ignore[no-any-return]


__all__ = ["Parser", "get_parser", "list_parsers"]
