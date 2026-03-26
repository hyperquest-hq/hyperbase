from __future__ import annotations

from collections.abc import Sequence

from hyperbase import hedge
from hyperbase.hyperedge import Hyperedge
from hyperbase.patterns.argroles import edge2rolemap, rolemap_pairings, rolemap2edge
from hyperbase.patterns.utils import more_general, is_valid
from hyperbase.patterns.variables import all_variables, is_variable, contains_variable


def common_pattern_argroles(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    rm1 = edge2rolemap(edge1)
    rm2 = edge2rolemap(edge2)

    _vars = all_variables(edge1) | all_variables(edge2)
    best_pattern: Hyperedge | None = None
    for rm1_, rm2_ in rolemap_pairings(rm1, rm2):
        edge1_ = rolemap2edge(edge1[0], rm1_)
        edge2_ = rolemap2edge(edge2[0], rm2_)

        subedges = [_common_pattern(se1, se2) for se1, se2 in zip(edge1_, edge2_)]
        if any(subedge is None for subedge in subedges):
            continue
        argroles = edge1_[0].argroles()
        if argroles == '':
            # deal with (*/P.{} or */B.{})
            pattern = hedge('*/{}'.format(edge1_.mtype()))
        else:
            pattern = hedge(subedges)
            if pattern is None:
                continue
            pattern = pattern.replace_argroles('{{{}}}'.format(edge1_[0].argroles()))

        if pattern is not None and _vars == all_variables(pattern):
            if best_pattern is None or more_general(best_pattern, pattern):
                best_pattern = pattern

    if best_pattern is None:
        return None

    return best_pattern.normalized()


def common_type(edges: Sequence[Hyperedge]) -> str | None:
    types = [edge.type() for edge in edges]
    if len(set(types)) == 1:
        return types[0]
    types = [edge.mtype() for edge in edges]
    if len(set(types)) == 1:
        return types[0]
    return None


def common_pattern_atoms(atoms: Sequence[Hyperedge]) -> Hyperedge | None:
    roots = [atom.root() for atom in atoms]  # type: ignore[attr-defined]

    if len(set(roots)) != 1 or '*' in roots:
        root = '*'
    else:
        root = roots[0]

    if any(len(str(atom).split('/')) == 1 for atom in atoms):
        atype: str | None = None
    else:
        atype = common_type(atoms)

    roles1: list[str | None] = []
    roles2: list[str | None] = []
    for atom in atoms:
        role = atom.role()  # type: ignore[attr-defined]
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
        role_str = '.'.join(role_parts)
        atom_str = '{}/{}'.format(root, role_str)

    return hedge(atom_str)


def _common_pattern(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    nedge1 = edge1
    nedge2 = edge2

    # variables
    if is_variable(nedge1):
        var1 = nedge1[2]
    else:
        var1 = None
    if is_variable(nedge2):
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
        if vedge is None or contains_variable(vedge):
            return None
        else:
            return hedge(('var', vedge, var))

    # both are atoms
    if nedge1.atom and nedge2.atom:
        return common_pattern_atoms((nedge1, nedge2))
    # at least one non-atom
    else:
        if nedge1.not_atom and nedge2.not_atom and nedge1.has_argroles() and nedge2.has_argroles():
            if nedge1.mt == nedge2.mt:
                common = common_pattern_argroles(nedge1, nedge2)
                if common:
                    return common

        # do not combine edges with argroles and edges without them
        perform_ordered_match = not ((nedge1.not_atom and nedge1.has_argroles())
                                        or (nedge2.not_atom and nedge2.has_argroles()))
        # same length
        if perform_ordered_match and nedge1.not_atom and nedge2.not_atom and len(nedge1) == len(nedge2):
            subedges = [_common_pattern(subedge1, subedge2) for subedge1, subedge2 in zip(nedge1, nedge2)]
            if any(subedge is None for subedge in subedges):
                return None
            return hedge(subedges)
        # not same length
        else:
            if contains_variable(nedge1) or contains_variable(nedge2):
                return None
            etype = common_type((nedge1, nedge2))
            if etype:
                return hedge('*/{}'.format(etype))
            else:
                return hedge('*')


def common_pattern(edge1: Hyperedge, edge2: Hyperedge) -> Hyperedge | None:
    edge = _common_pattern(edge1, edge2)
    if is_valid(edge):
        return edge
    else:
        return None
