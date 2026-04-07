from __future__ import annotations

from typing import TYPE_CHECKING

import hyperbase.constants as const

if TYPE_CHECKING:
    from hyperbase.hyperedge import Hyperedge


def is_wildcard(edge: Hyperedge) -> bool:
    """Check if edge is a wildcard pattern matcher."""
    if edge.atom:
        root = edge.root()  # type: ignore[union-attr]
        return root[0] in {"*", "."} or root[0].isupper()
    return False


def is_pattern(edge: Hyperedge) -> bool:
    """Check if edge defines a pattern (contains at least one matcher)."""
    if edge.atom:
        return is_wildcard(edge) or "{" in edge.argroles() or "[" in edge.argroles()
    if is_fun_pattern(edge):
        return True
    return any(is_pattern(item) for item in edge)


def is_fun_pattern(edge: Hyperedge) -> bool:
    """Check if edge is a functional pattern (var, atoms, lemma, any)."""
    if edge.atom:
        return False
    return str(edge[0]) in const.PATTERN_FUNCTIONS


def is_variable(edge: Hyperedge) -> bool:
    """Check if edge is a pattern variable."""
    if edge.atom:
        root = edge.root()  # type: ignore[union-attr]
        return root[0].isupper() or (
            root[0] in {"*", "."} and len(root) > 1 and root[1].isupper()
        )
    return (
        str(edge[0]) == "var"
        and len(edge) == 3
        and edge[2].atom
        and "/" not in str(edge[2])
    )


def contains_variable(edge: Hyperedge) -> bool:
    """Check if edge contains any pattern variable."""
    if edge.atom:
        return is_variable(edge)
    if is_variable(edge):
        return True
    return any(contains_variable(sub) for sub in edge)


def variable_name(edge: Hyperedge) -> str:
    """Return the variable name of a pattern variable edge."""
    if edge.atom:
        root = edge.root()  # type: ignore[union-attr]
        if root[0].isupper():
            return root
        elif root[0] in {"*", "."} and len(root) > 1 and root[1].isupper():
            return root[1:]
        else:
            raise ValueError(f"'{root}' is not a variable")
    if is_variable(edge):
        return str(edge[2])
    raise ValueError(f"'{edge!s}' is not a variable")
