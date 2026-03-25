import itertools
from typing import TYPE_CHECKING

from hyperbase.hyperedge import Hyperedge, hedge
from hyperbase.patterns.utils import _defun_pattern_argroles

if TYPE_CHECKING:
    from hyperbase.patterns.matcher import Matcher


def _match_by_argroles(
        matcher: 'Matcher',
        edge: Hyperedge,
        pattern: Hyperedge,
        role_counts,
        min_vars,
        matched=(),
        curvars=None,
        tok_pos=None
):
    if curvars is None:
        curvars = {}

    if len(role_counts) == 0:
        return [curvars]

    argrole, n = role_counts[0]

    # match connector
    if argrole == 'X':
        eitems = [edge[0]]
        pitems = [pattern[0]]
    # match any argrole
    elif argrole == '*':
        eitems = [e for e in edge if e not in matched]
        pitems = pattern[-n:]
    # match specific argrole
    else:
        eitems = edge.edges_with_argrole(argrole)
        pitems = _defun_pattern_argroles(pattern).edges_with_argrole(argrole)

    if len(eitems) < n:
        if len(curvars) >= min_vars:
            return [curvars]
        else:
            return []

    result = []

    if tok_pos:
        tok_pos_items = [tok_pos[i] for i, subedge in enumerate(edge) if subedge in eitems]
        tok_pos_perms = tuple(itertools.permutations(tok_pos_items, r=n))

    for perm_n, perm in enumerate(tuple(itertools.permutations(eitems, r=n))):
        if tok_pos:
            tok_pos_perm = tok_pos_perms[perm_n]
        perm_result = [{}]
        for i, eitem in enumerate(perm):
            pitem = pitems[i]
            tok_pos_item = tok_pos_perm[i] if tok_pos else None
            item_result = []
            for variables in perm_result:
                item_result += matcher.match(
                    eitem,
                    pitem,
                    {**curvars, **variables},
                    tok_pos=tok_pos_item
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
                tok_pos=tok_pos
            )

    return result


def edge2rolemap(edge):
    argroles = edge[0].argroles()
    if argroles[0] == '{':
        argroles = argroles[1:-1]
    args = list(zip(argroles, edge[1:]))
    rolemap = {}
    for role, subedge in args:
        if role not in rolemap:
            rolemap[role] = []
        rolemap[role].append(subedge)
    return rolemap


def rolemap2edge(pred, rm):
    roles = list(rm.keys())
    argroles = ''
    subedges = [pred]
    for role in roles:
        for arg in rm[role]:
            argroles += role
            subedges.append(arg)
    edge = hedge(subedges)
    return edge.replace_argroles(argroles)


def rolemap_pairings(rm1, rm2):
    roles = list(set(rm1.keys()) & set(rm2.keys()))
    role_counts = {}
    for role in roles:
        role_counts[role] = min(len(rm1[role]), len(rm2[role]))

    pairings = []
    for role in roles:
        role_pairings = []
        n = role_counts[role]
        for args1_combs in itertools.combinations(rm1[role], n):
            for args1 in itertools.permutations(args1_combs):
                for args2 in itertools.combinations(rm2[role], n):
                    role_pairings.append((args1, args2))
        pairings.append(role_pairings)

    for pairing in itertools.product(*pairings):
        rm1_ = {}
        rm2_ = {}
        for role, role_pairing in zip(roles, pairing):
            rm1_[role] = role_pairing[0]
            rm2_[role] = role_pairing[1]
        yield rm1_, rm2_
