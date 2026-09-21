from importlib.metadata import EntryPoint, entry_points
from typing import TYPE_CHECKING, Any

from hyperbase.parsers.parser import Parser
from hyperbase.parsers.repl import ReplContext
from hyperbase.parsers.result import ParseResult
from hyperbase.parsers.vocabulary import (
    ARGROLE_LETTERS,
    ATOM_TYPES,
    SINGLETON_ARGROLES,
    SPECIAL_ATOMS,
    VALID_B_ARGROLES,
    VALID_P_ARGROLES,
    is_admissible_atom_type,
    is_admissible_special_atom,
)


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

    Any parameter the caller does not supply is seeded with the
    ``"default"`` declared in the parser's :meth:`Parser.accepted_params`,
    so a programmatic caller gets the same effective configuration as the
    REPL/CLI front-ends (which pre-fill those defaults before constructing
    the parser). A declared default of ``None`` means "no default" — it is
    left unset so the parser's own ``__init__`` fallback or validation
    applies.

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
    for pname, info in cls.accepted_params().items():
        if pname not in merged and info.get("default") is not None:
            merged[pname] = info["default"]
    return cls(merged)


# Served lazily by ``__getattr__``: importing ``hyperbase.parsers.correctness``
# at module scope would close a cycle (it imports ``hyperbase.builders``, which
# comes back around to this package), so every entry into ``hyperbase.parsers``
# would fail. Declared here for type checkers, which do not run the import.
if TYPE_CHECKING:
    from hyperbase.parsers.correctness import (
        CheckContext,
        CorrectnessCheck,
        ErrorMap,
        check_parse_correctness,
        run_checks,
        run_parser_checks,
    )

_CORRECTNESS_EXPORTS = frozenset(
    {
        "CheckContext",
        "CorrectnessCheck",
        "ErrorMap",
        "check_parse_correctness",
        "run_checks",
        "run_parser_checks",
    }
)


def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Resolve the correctness re-exports on first access.

    Deferred rather than imported above for the cycle described there; by the
    time anything asks for one of these, the package is fully initialised.
    """
    if name in _CORRECTNESS_EXPORTS:
        import hyperbase.parsers.correctness as _correctness

        value = getattr(_correctness, name)
        globals()[name] = value  # cache it; __getattr__ runs once per name
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ARGROLE_LETTERS",
    "ATOM_TYPES",
    "SINGLETON_ARGROLES",
    "SPECIAL_ATOMS",
    "VALID_B_ARGROLES",
    "VALID_P_ARGROLES",
    "CheckContext",
    "CorrectnessCheck",
    "ErrorMap",
    "ParseResult",
    "Parser",
    "ReplContext",
    "check_parse_correctness",
    "get_parser",
    "is_admissible_atom_type",
    "is_admissible_special_atom",
    "list_parsers",
    "run_checks",
    "run_parser_checks",
]
