from __future__ import annotations

import itertools
from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING

from hyperbase.hyperedge import Hyperedge, hedge
from hyperbase.patterns.utils import _defun_pattern_argroles

if TYPE_CHECKING:
    from hyperbase.patterns.matcher import Matcher


def _match_by_argroles(
    matcher: Matcher,
    edge: Hyperedge,
    pattern: Hyperedge,
    role_counts: list[tuple[str, int]],
    min_vars: int,
    matched: tuple[Hyperedge, ...] = (),
    curvars: dict[str, Hyperedge] | None = None,
    tok_pos: list[int] | None = None,
) -> list[dict[str, Hyperedge]]:
    if curvars is None:
        curvars = {}

    if len(role_counts) == 0:
        return [curvars]

    argrole, n = role_counts[0]

    # match connector
    if argrole == "X":
        eitems = [edge[0]]
        pitems = [pattern[0]]
    # match any argrole
    elif argrole == "*":
        eitems = [e for e in edge if e not in matched]
        pitems = list(pattern[-n:])
    # match specific argrole
    else:
        eitems = edge.arguments_with_role(argrole)
        pitems = _defun_pattern_argroles(pattern).arguments_with_role(argrole)

    if len(eitems) < n:
        if len(curvars) >= min_vars:
            return [curvars]
        else:
            return []

    result: list[dict[str, Hyperedge]] = []

    if tok_pos:
        tok_pos_items = [
            tok_pos[i] for i, subedge in enumerate(edge) if subedge in eitems
        ]
        tok_pos_perms = tuple(itertools.permutations(tok_pos_items, r=n))

    for perm_n, perm in enumerate(tuple(itertools.permutations(eitems, r=n))):
        if tok_pos:
            tok_pos_perm = tok_pos_perms[perm_n]
        perm_result: list[dict[str, Hyperedge]] = [{}]
        for i, eitem in enumerate(perm):
            pitem = pitems[i]
            tok_pos_item = tok_pos_perm[i] if tok_pos else None
            item_result: list[dict[str, Hyperedge]] = []
            for variables in perm_result:
                item_result += matcher.match(
                    eitem, pitem, {**curvars, **variables}, tok_pos=tok_pos_item
                )
            perm_result = item_result
            if len(item_result) == 0:
                break

        for variables in perm_result:
            result += _match_by_argroles(
                matcher,
                edge,
                pattern,
                role_counts[1:],
                min_vars,
                matched + perm,
                {**curvars, **variables},
                tok_pos=tok_pos,
            )

    return result


def edge2rolemap(edge: Hyperedge) -> dict[str, list[Hyperedge]]:
    argroles = edge[0].argroles()
    if argroles[0] == "{":
        argroles = argroles[1:-1]
    args = list(zip(argroles, edge[1:], strict=False))
    rolemap: dict[str, list[Hyperedge]] = {}
    for role, subedge in args:
        if role not in rolemap:
            rolemap[role] = []
        rolemap[role].append(subedge)
    return rolemap


def rolemap2edge(pred: Hyperedge, rm: Mapping[str, Sequence[Hyperedge]]) -> Hyperedge:
    roles = list(rm.keys())
    argroles = ""
    subedges: list[Hyperedge] = [pred]
    for role in roles:
        for arg in rm[role]:
            argroles += role
            subedges.append(arg)
    result = hedge(subedges)
    assert result is not None
    return result.replace_argroles(argroles)


def rolemap_pairings(
    rm1: dict[str, list[Hyperedge]], rm2: dict[str, list[Hyperedge]]
) -> Iterator[
    tuple[dict[str, tuple[Hyperedge, ...]], dict[str, tuple[Hyperedge, ...]]]
]:
    roles = list(set(rm1.keys()) & set(rm2.keys()))
    role_counts: dict[str, int] = {}
    for role in roles:
        role_counts[role] = min(len(rm1[role]), len(rm2[role]))

    pairings: list[list[tuple[tuple[Hyperedge, ...], tuple[Hyperedge, ...]]]] = []
    for role in roles:
        role_pairings: list[tuple[tuple[Hyperedge, ...], tuple[Hyperedge, ...]]] = []
        n = role_counts[role]
        for args1_combs in itertools.combinations(rm1[role], n):
            for args1 in itertools.permutations(args1_combs):
                for args2 in itertools.combinations(rm2[role], n):
                    role_pairings.append((args1, args2))
        pairings.append(role_pairings)

    for pairing in itertools.product(*pairings):
        rm1_: dict[str, tuple[Hyperedge, ...]] = {}
        rm2_: dict[str, tuple[Hyperedge, ...]] = {}
        for role, role_pairing in zip(roles, pairing, strict=False):
            rm1_[role] = role_pairing[0]
            rm2_[role] = role_pairing[1]
        yield rm1_, rm2_
