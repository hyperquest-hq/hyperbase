from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, cast

from hyperbase.hyperedge import Atom, Hyperedge, UniqueAtom

if TYPE_CHECKING:
    from hyperbase.parsers.parse_result import ParseResult


def str_to_atom(s: str) -> str:
    """Converts a string into a valid atom."""
    atom = s.lower()

    atom = atom.replace("%", "%25")
    atom = atom.replace("/", "%2f")
    atom = atom.replace(" ", "%20")
    atom = atom.replace("(", "%28")
    atom = atom.replace(")", "%29")
    atom = atom.replace(".", "%2e")
    atom = atom.replace("*", "%2a")
    atom = atom.replace("&", "%26")
    atom = atom.replace("@", "%40")
    atom = atom.replace("\n", "%0a")
    atom = atom.replace("\r", "%0d")

    return atom


def _edge_str_has_outer_parens(edge_str: str) -> bool:
    """Check if string representation of edge is delimited by outer
    parenthesis.
    """
    if len(edge_str) < 2:
        return False
    return edge_str[0] == "("


def split_edge_str(edge_str: str) -> tuple[str, ...]:
    """Shallow split into tokens of a string representation of an edge,
    without outer parenthesis.
    """
    start = 0
    depth = 0
    str_length = len(edge_str)
    active = 0
    tokens: list[str] = []
    for i in range(str_length):
        c = edge_str[i]
        if c == " ":
            if active and depth == 0:
                tokens.append(edge_str[start:i])
                active = 0
        elif c == "(":
            if depth == 0:
                active = 1
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                tokens.append(edge_str[start : i + 1])
                active = 0
            elif depth < 0:
                raise ValueError(f"Unbalanced parenthesis in edge string: '{edge_str}'")
        else:
            if not active:
                active = 1
                start = i

    if active:
        if depth > 0:
            raise ValueError(f"Unbalanced parenthesis in edge string: '{edge_str}'")
        else:
            tokens.append(edge_str[start:])

    return tuple(tokens)


def _parsed_token(token: str) -> Hyperedge:
    if _edge_str_has_outer_parens(token):
        return hedge(token)
    else:
        return Atom(token)


def _collect_positions(tok_pos: Hyperedge) -> list[int]:
    """Collect all valid (>= 0) token positions from a tok_pos tree."""
    if tok_pos.atom:
        pos = int(str(tok_pos))
        return [pos] if pos >= 0 else []
    else:
        positions: list[int] = []
        for sub in tok_pos:
            positions.extend(_collect_positions(sub))
        return positions


def _rebuild_with_text(
    edge: Hyperedge,
    tok_pos: Hyperedge,
    tokens: list[str],
) -> Hyperedge:
    """Recursively rebuild an edge, assigning text from tokens and tok_pos."""
    if edge.atom:
        atom = cast(Atom, edge)
        pos = int(str(tok_pos))
        text = tokens[pos] if pos >= 0 else None
        return Atom(str(atom), atom.parens, text=text)
    else:
        new_children = tuple(
            _rebuild_with_text(sub_edge, sub_tok_pos, tokens)
            for sub_edge, sub_tok_pos in zip(edge, tok_pos, strict=False)
        )
        positions = _collect_positions(tok_pos)
        if positions:
            min_pos = min(positions)
            max_pos = max(positions)
            text = " ".join(tokens[min_pos : max_pos + 1])
        else:
            text = None
        return Hyperedge(new_children, text=text)


def hedge(
    source: str | Hyperedge | list | tuple | ParseResult,
) -> Hyperedge:
    """Create a hyperedge."""
    # Check for ParseResult via duck typing to avoid circular import
    if (
        hasattr(source, "tok_pos")
        and hasattr(source, "tokens")
        and hasattr(source, "edge")
    ):
        from hyperbase.parsers import ParseResult

        _source = cast(ParseResult, source)
        edge = _rebuild_with_text(_source.edge, _source.tok_pos, _source.tokens)
        object.__setattr__(edge, "text", _source.text)
        return edge
    if type(source) in {tuple, list}:
        _source = cast(Iterable, source)
        return Hyperedge(tuple(hedge(item) for item in _source))
    elif type(source) is str:
        edge_str = source.strip().replace("\n", " ")
        edge_inner_str = edge_str

        parens = _edge_str_has_outer_parens(edge_str)
        if parens:
            edge_inner_str = edge_str[1:-1]

        tokens = split_edge_str(edge_inner_str)
        if not tokens:
            raise ValueError(f"Edge string is empty: '{source}'")
        edges = tuple(_parsed_token(token) for token in tokens)
        if len(edges) == 1 and isinstance(edges[0], Atom):
            return Atom(str(edges[0]), parens)
        elif len(edges) > 0:
            return Hyperedge(edges)
        else:
            raise ValueError(f"Edge string is empty: '{source}'")
    elif type(source) in {Hyperedge, Atom, UniqueAtom}:
        return source  # type: ignore
    else:
        raise TypeError(
            f"Cannot create hyperedge from {type(source).__name__}: {source!r}"
        )


def build_atom(text: str, *parts: str) -> Atom:
    """Build an atom from text and other parts."""
    atom = str_to_atom(text)
    parts_str = "/".join([part for part in parts if part])
    if len(parts_str) > 0:
        atom_str = "".join((atom, "/", parts_str))
    return Atom(atom_str)
