from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from typing import cast

from hyperbase import hedge
from hyperbase.hyperedge import Atom, Hyperedge

# common_pattern: what do these have in common?
#                 produces a generalized pattern with wildcards
# merge_patterns: match either of these
#                 produces a merged pattern with any-alternatives


def is_valid(edge: Hyperedge | None, _vars: set[Hyperedge] | None = None) -> bool:
    if _vars is None:
        _vars = set()
    if edge is None:
        return False
    if edge.atom:
        return True
    if edge.is_variable():
        if edge[2].not_atom:
            return False
        # if edge[2] in _vars:
        #     return False
        _vars.add(edge[2])
        return is_valid(edge[1], _vars=_vars)
    return all(is_valid(subedge, _vars=_vars) for subedge in edge)


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


def more_general(edge1: Hyperedge, edge2: Hyperedge) -> bool:
    r1, s1, t1 = atom_pattern_counts(edge1)
    r2, s2, t2 = atom_pattern_counts(edge2)
    if r1 == r2:
        if s1 == s2:
            return t1 < t2
        return s1 < s2
    return r1 < r2


def atom_pattern_counts(edge: Hyperedge) -> tuple[int, int, int]:
    if edge.atom:
        atom = cast(Atom, edge)
        parts: list[str] = atom.parts()
        roots = 1 if parts[0] != "*" else 0
        subtyped = 1 if len(atom.type()) > 1 else 0
        typed = 1 if len(parts) > 1 else 0
    else:
        roots = 0
        subtyped = 0
        typed = 0
        for subedge in edge:
            r, s, t = atom_pattern_counts(subedge)
            roots += r
            subtyped += s
            typed += t
    return roots, subtyped, typed


def all_variables(edge: Hyperedge, _vars: Counter | None = None) -> Counter:
    if _vars is None:
        _vars = Counter()
    if edge.atom:
        return _vars
    else:
        if edge.is_variable():
            _vars[edge[2]] += 1
        for subedge in edge:
            all_variables(subedge, _vars=_vars)
    return _vars


def common_pattern_argroles(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    rm1 = edge2rolemap(edge1)
    rm2 = edge2rolemap(edge2)

    _vars = all_variables(edge1) | all_variables(edge2)
    best_pattern: Hyperedge | None = None
    for rm1_, rm2_ in rolemap_pairings(rm1, rm2):
        edge1_ = rolemap2edge(edge1[0], rm1_)
        edge2_ = rolemap2edge(edge2[0], rm2_)

        subedges = [
            _common_pattern(se1, se2) for se1, se2 in zip(edge1_, edge2_, strict=False)
        ]
        if any(subedge is None for subedge in subedges):
            continue
        argroles = edge1_[0].argroles()
        if argroles == "":
            # deal with (*/P.{} or */B.{})
            pattern = hedge(f"*/{edge1_.mtype()}")
        else:
            pattern = hedge(subedges)
            pattern = pattern.replace_argroles(f"{{{edge1_[0].argroles()}}}")

        if _vars == all_variables(pattern) and (
            best_pattern is None or more_general(best_pattern, pattern)
        ):
            best_pattern = pattern

    if best_pattern is None:
        return None

    return best_pattern.normalise()


def common_type(edges: Sequence[Hyperedge]) -> str | None:
    types = [edge.type() for edge in edges]
    if len(set(types)) == 1:
        return types[0]
    types = [edge.mtype() for edge in edges]
    if len(set(types)) == 1:
        return types[0]
    return None


def common_pattern_atoms(atoms: Sequence[Atom]) -> Hyperedge:
    roots = [atom.root() for atom in atoms]

    root = "*" if len(set(roots)) != 1 or "*" in roots else roots[0]

    if any(len(str(atom).split("/")) == 1 for atom in atoms):
        atype: str | None = None
    else:
        atype = common_type(atoms)

    roles1: list[str | None] = []
    roles2: list[str | None] = []
    for atom in atoms:
        role = atom.role()
        r1: str | None = role[1] if len(role) > 1 else None
        r2: str | None = role[2] if len(role) > 2 else None
        roles1.append(r1)
        roles2.append(r2)

    final_role1: str | None = None
    final_role2: str | None = None
    if len(set(roles1)) == 1 and roles1[0] is not None:
        final_role1 = roles1[0]
        if len(set(roles2)) == 1 and roles2[0] is not None:
            final_role2 = roles2[0]

    if atype is None:
        atom_str = root
    else:
        role_parts = [atype]
        if final_role1 is not None:
            role_parts.append(final_role1)
            if final_role2 is not None:
                role_parts.append(final_role2)
        role_str = ".".join(role_parts)
        atom_str = f"{root}/{role_str}"

    return hedge(atom_str)


def _common_pattern(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    nedge1 = edge1
    nedge2 = edge2

    # variables
    var1 = nedge1[2] if nedge1.is_variable() else None
    if nedge2.is_variable():
        var2 = nedge2[2]
        if var1 is None:
            return None
    else:
        var2 = None
        if var1:
            return None
    if var1 or var2:
        # different variables on same position?
        if var1 and var2 and var1 != var2:
            return None
        var = None
        if var1:
            vedge1 = nedge1[1]
            var = var1
        else:
            vedge1 = nedge1
        if var2:
            vedge2 = nedge2[1]
            var = var2
        else:
            vedge2 = nedge2
        vedge = _common_pattern(vedge1, vedge2)
        if vedge is None or vedge.contains_variable():
            return None
        else:
            return hedge(("var", vedge, var))

    # both are atoms
    if nedge1.atom and nedge2.atom:
        natom1 = cast(Atom, nedge1)
        natom2 = cast(Atom, nedge2)
        return common_pattern_atoms((natom1, natom2))
    # at least one non-atom
    else:
        if (
            nedge1.not_atom
            and nedge2.not_atom
            and nedge1.argroles()
            and nedge2.argroles()
        ) and nedge1.mt == nedge2.mt:
            common = common_pattern_argroles(nedge1, nedge2)
            if common:
                return common

        # do not combine edges with argroles and edges without them
        perform_ordered_match = not (
            (nedge1.not_atom and nedge1.argroles())
            or (nedge2.not_atom and nedge2.argroles())
        )
        # same length
        if (
            perform_ordered_match
            and nedge1.not_atom
            and nedge2.not_atom
            and len(nedge1) == len(nedge2)
        ):
            subedges = [
                _common_pattern(subedge1, subedge2)
                for subedge1, subedge2 in zip(nedge1, nedge2, strict=False)
            ]
            if any(subedge is None for subedge in subedges):
                return None
            return hedge(subedges)
        # not same length
        else:
            if nedge1.contains_variable() or nedge2.contains_variable():
                return None
            etype = common_type((nedge1, nedge2))
            if etype:
                return hedge(f"*/{etype}")
            else:
                return hedge("*")


def common_pattern(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    edge = _common_pattern(edge1, edge2)
    if is_valid(edge):
        return edge
    else:
        return None


def _extract_any_edges(edge: Hyperedge) -> list[Hyperedge]:
    if edge.not_atom and str(edge[0]) == "any":
        return list(edge[1:])
    else:
        return [edge]


def _merge_patterns(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    # edges with different sizes cannot be merged
    if len(edge1) != len(edge2):
        return None

    # atoms are not to be merged
    if edge1.atom or edge2.atom:
        return None

    # edges with no subedge in common are not to be merged
    if all(
        subedge1 != subedge2 for subedge1, subedge2 in zip(edge1, edge2, strict=False)
    ):
        return None

    merged_edge = []
    for subedge1, subedge2 in zip(edge1, edge2, strict=False):
        if subedge1 == subedge2:
            merged_edge.append(subedge1)
        else:
            submerged = merge_patterns(subedge1, subedge2)
            if submerged:
                merged_edge.append(submerged)
            else:
                alternatives = _extract_any_edges(subedge1) + _extract_any_edges(
                    subedge2
                )
                # heuristic: more complex edges first, likely to be more specific
                alternatives = sorted(
                    alternatives, key=lambda x: x.size(), reverse=True
                )
                merged_edge.append(["any", *alternatives])

    return hedge(merged_edge)


def merge_patterns(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    edge = _merge_patterns(edge1, edge2)
    if is_valid(edge):
        return edge
    else:
        return None
