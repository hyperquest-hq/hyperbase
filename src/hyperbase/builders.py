from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

from hyperbase.constants import ATOM_ENCODE_TABLE
from hyperbase.hyperedge import Atom, Hyperedge, UniqueAtom
from hyperbase.parsers.parse_result import ParseResult


def str_to_atom(s: str) -> str:
    """Converts a string into a valid atom."""
    return s.lower().translate(ATOM_ENCODE_TABLE)


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


def _hedge_from_str(source: str) -> Hyperedge:
    """Iteratively parse an edge string into a Hyperedge.

    Uses an explicit stack rather than recursion so that pathologically
    nested edge strings cannot exhaust Python's call stack. Each frame in
    the stack represents one open ``(...)`` group being assembled and
    holds: ``[parens_flag, tokens, next_token_index, children_built]``.
    """
    edge_str = source.strip().replace("\n", " ")
    parens = _edge_str_has_outer_parens(edge_str)
    inner = edge_str[1:-1] if parens else edge_str

    tokens = split_edge_str(inner)
    if not tokens:
        raise ValueError(f"Edge string is empty: '{source}'")

    stack: list[list[Any]] = [[parens, tokens, 0, []]]
    final: Hyperedge | None = None

    while stack:
        frame = stack[-1]
        if frame[2] >= len(frame[1]):
            # All tokens for this frame consumed; build the edge.
            children: list[Hyperedge] = frame[3]
            frame_parens: bool = frame[0]
            if len(children) == 1 and isinstance(children[0], Atom):
                built: Hyperedge = Atom(str(children[0]), frame_parens)
            elif children:
                built = Hyperedge(tuple(children))
            else:
                # Unreachable: empty token lists are rejected before push,
                # but keep the guard for defensiveness.
                raise ValueError(f"Edge string is empty: '{source}'")
            stack.pop()
            if stack:
                stack[-1][3].append(built)
            else:
                final = built
            continue

        token = frame[1][frame[2]]
        frame[2] += 1
        if _edge_str_has_outer_parens(token):
            inner_tok = token[1:-1]
            sub_tokens = split_edge_str(inner_tok)
            if not sub_tokens:
                raise ValueError(f"Edge string is empty: '{token}'")
            stack.append([True, sub_tokens, 0, []])
        else:
            frame[3].append(Atom(token))

    assert final is not None  # loop guarantees this
    return final


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
    if isinstance(source, ParseResult):
        _source = source
        edge = _rebuild_with_text(_source.edge, _source.tok_pos, _source.tokens)
        object.__setattr__(edge, "text", _source.text)
        return edge
    if type(source) in {tuple, list}:
        _source = cast(Iterable, source)
        return Hyperedge(tuple(hedge(item) for item in _source))
    elif type(source) is str:
        return _hedge_from_str(source)
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
