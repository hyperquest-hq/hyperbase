from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator
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


def _compute_token_offsets(
    tokens: list[str], text: str
) -> list[tuple[int, int] | None]:
    """Cursor-scan ``text`` for each token in order, returning per-token
    (start, end) byte offsets. Tokens that can't be located after the running
    cursor get ``None`` and the cursor is left unchanged so a single failed
    token does not poison the rest of the sentence.
    """
    spans: list[tuple[int, int] | None] = []
    cursor = 0
    for tok in tokens:
        idx = text.find(tok, cursor)
        if idx < 0:
            spans.append(None)
        else:
            spans.append((idx, idx + len(tok)))
            cursor = idx + len(tok)
    return spans


def _rebuild_with_metadata(
    edge: Hyperedge,
    tok_pos: Hyperedge,
    tokens: list[str],
    text: str,
    offsets: list[tuple[int, int] | None],
    claimed: frozenset[int],
) -> Hyperedge:
    """Recursively rebuild an edge, populating per-atom tok_pos/text_span and
    per-non-atom continuity-aware ``text``. ``claimed`` is the global set of
    token positions actually mapped to atoms anywhere in the loaded root.
    """
    if edge.atom:
        atom = cast(Atom, edge)
        pos = int(str(tok_pos))
        if pos < 0:
            return Atom(str(atom), atom.parens)
        span = offsets[pos] if 0 <= pos < len(offsets) else None
        atom_text = (
            text[span[0] : span[1]]
            if span is not None
            else (tokens[pos] if 0 <= pos < len(tokens) else None)
        )
        return Atom(str(atom), atom.parens, text=atom_text, tok_pos=pos, text_span=span)
    else:
        new_children = tuple(
            _rebuild_with_metadata(
                sub_edge, sub_tok_pos, tokens, text, offsets, claimed
            )
            for sub_edge, sub_tok_pos in zip(edge, tok_pos, strict=False)
        )
        sub_text = _derive_subedge_text(new_children, text, tokens, offsets, claimed)
        return Hyperedge(new_children, text=sub_text)


def _derive_subedge_text(
    children: tuple[Hyperedge, ...],
    root_text: str,
    root_tokens: list[str],
    offsets: list[tuple[int, int] | None],
    claimed: frozenset[int],
) -> str | None:
    """Continuity-aware text derivation for a non-atomic edge.

    Walks the descendant atoms, uses their ``tok_pos`` to identify which
    source positions the sub-edge references (``used``), and slices the
    root's ``text`` per contiguous run. A run is broken only by a position
    in ``claimed`` (a real atom anywhere in the root) that is not in
    ``used`` -- synthetic atoms and unclaimed tokens (e.g. punctuation that
    no atom maps to) keep the run continuous.
    """
    used_positions: set[int] = set()
    for a in _walk_atoms(children):
        pos = cast(Atom, a).tok_pos
        if pos is not None:
            used_positions.add(pos)
    used: list[int] = sorted(used_positions)
    if not used:
        return None

    span_by_pos: dict[int, tuple[int, int] | None] = {}
    for a in _walk_atoms(children):
        atom = cast(Atom, a)
        if atom.tok_pos is not None and atom.tok_pos not in span_by_pos:
            span_by_pos[atom.tok_pos] = atom.text_span

    # Group used positions into runs, splitting whenever a claimed-but-unused
    # position falls between two consecutive used positions.
    used_set = set(used)
    runs: list[list[int]] = [[used[0]]]
    for prev, curr in itertools.pairwise(used):
        broken = any(prev < p < curr and p not in used_set for p in claimed)
        if broken:
            runs.append([curr])
        else:
            runs[-1].append(curr)

    slices: list[str] = []
    for run in runs:
        first_span = span_by_pos.get(run[0])
        last_span = span_by_pos.get(run[-1])
        if first_span is not None and last_span is not None:
            slices.append(root_text[first_span[0] : last_span[1]])
        else:
            # Local fallback: token-join for this run.
            slices.append(
                " ".join(root_tokens[p] for p in run if 0 <= p < len(root_tokens))
            )
    return " ".join(slices)


def _walk_atoms(edges: tuple[Hyperedge, ...]) -> Iterator[Hyperedge]:
    for e in edges:
        if e.atom:
            yield e
        else:
            yield from _walk_atoms(tuple(e))


def hedge(
    source: str | Hyperedge | list | tuple | ParseResult,
) -> Hyperedge:
    """Create a hyperedge."""
    if isinstance(source, ParseResult):
        _source = source
        offsets = _compute_token_offsets(_source.tokens, _source.text)
        # Compute claimed = all token positions referenced by atoms in the
        # original edge tree. Used to detect real (non-synthetic, non-padding)
        # discontinuities in sub-edge text derivation.
        claimed = frozenset(_collect_positions(_source.tok_pos))
        edge = _rebuild_with_metadata(
            _source.edge,
            _source.tok_pos,
            _source.tokens,
            _source.text,
            offsets,
            claimed,
        )
        # Override the root's text with the verbatim original sentence and
        # store tokens on the root for any later derivation.
        object.__setattr__(edge, "_text", _source.text)
        object.__setattr__(edge, "tokens", tuple(_source.tokens))
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
