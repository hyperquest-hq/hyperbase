from __future__ import annotations

from hyperbase.hyperedge import Hyperedge, hedge
from hyperbase.patterns.matcher import Matcher
from hyperbase.patterns.utils import _normalize_fun_patterns


def match_pattern(
        edge: Hyperedge | str | list[object] | tuple[object, ...],
        pattern: Hyperedge | str | list[object] | tuple[object, ...],
        curvars: dict[str, Hyperedge] | None = None
) -> list[dict[str, Hyperedge]]:
    """Matches an edge to a pattern. This means that, if the edge fits the
    pattern, then a list of dictionaries will be returned. If the pattern
    specifies variables, then the returned dictionaries will be populated
    with the values for each pattern variable. There can be more than one
    dictionary in the list if there are multiple ways of matching the
    variables. If the pattern specifies no variables but the edge matches
    it, then a list with a single empty dictionary is returned. If the
    edge does not match the pattern, an empty list is returned.

    Patterns are themselves edges. They can match families of edges
    by employing special atoms:

    - `\\*` represents a general wildcard (matches any entity)
    - `.` represents an atomic wildcard (matches any atom)
    - `(\\*)` represents an edge wildcard (matches any non-atom)
    - `...` at the end indicates an open-ended pattern.

    The wildcards (`\\*`, `.` and `(\\*)`) can be used to specify variables,
    for example `\\*x`, `(CLAIM)` or `.ACTOR`. In case of a match, these
    variables are assigned the hyperedge they correspond to. For example, consider
    the edge:

    `(is/P.so (my/Mp name/Cn) mary/Cp)`

    - matching to the pattern: `(is/P.so (my/Mp name/Cn) \\*)`
    produces the result: `[{}]`
    - matching to the pattern: `(is/P.so (my/Mp name/Cn) \\*NAME)`
    produces the result: `[{'NAME', mary/Cp}]`
    - matching to the pattern: `(is/P.so . \\*NAME)`
    produces the result: `[]`
    """
    _edge = hedge(edge)
    _pattern = hedge(pattern)
    if _edge is None or _pattern is None:
        return []
    _pattern = _normalize_fun_patterns(_pattern)

    matcher: Matcher = Matcher(
        edge=_edge,
        pattern=_pattern,
        curvars=curvars,
    )

    return matcher.results


def edge_matches_pattern(
        edge: Hyperedge | str | list[object] | tuple[object, ...],
        pattern: Hyperedge | str | list[object] | tuple[object, ...],
        **kwargs: object
) -> bool:
    """Check if an edge matches a pattern.

    Patterns are themselves edges. They can match families of edges
    by employing special atoms:

    -> '\\*' represents a general wildcard (matches any entity)

    -> '.' represents an atomic wildcard (matches any atom)

    -> '(\\*)' represents an edge wildcard (matches any edge)

    -> '...' at the end indicates an open-ended pattern.

    The pattern can be any valid hyperedge, including the above special atoms.
    Examples: (is/Pd hyperbase/C .)
    (says/Pd * ...)
    """
    result = match_pattern(edge, pattern)
    return len(result) > 0
