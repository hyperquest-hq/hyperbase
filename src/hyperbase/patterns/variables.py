from __future__ import annotations

from collections import Counter
from typing import Any

from hyperbase import hedge
from hyperbase.hyperedge import Hyperedge
from hyperbase.patterns.properties import is_pattern
import hyperbase.constants as const


def apply_vars(edge: Hyperedge, variables: dict[str, Hyperedge]) -> Hyperedge:
    if edge.atom:
        if is_pattern(edge):
            varname = _varname(edge)
            if len(varname) > 0 and varname in variables:
                return variables[varname]
        return edge
    else:
        result = hedge([apply_vars(subedge, variables) for subedge in edge])
        assert result is not None
        return result


def _varname(atom: Hyperedge) -> str:
    if not atom.atom:
        return ''
    label: str = atom.parts()[0]  # type: ignore[attr-defined]
    if len(label) == 0:
        return label
    elif label[0] in {'*', '.'}:
        return label[1:]
    elif label[:3] == '...':
        return label[3:]
    elif label[0].isupper():
        return label
    else:
        return ''


def _assign_edge_to_var(
        curvars: dict[str, Hyperedge],
        var_name: str,
        edge: Hyperedge
) -> dict[str, Hyperedge]:
    new_edge: Hyperedge = edge
    if var_name in curvars:
        cur_edge = curvars[var_name]
        if cur_edge.not_atom and str(cur_edge[0]) == const.list_or_matches_builder:
            new_edge = cur_edge + (edge,)
        else:
            result = hedge((hedge(const.list_or_matches_builder), cur_edge, edge))
            assert result is not None
            new_edge = result
    return {var_name: new_edge}


def is_variable(edge: Hyperedge) -> bool:
    if edge.not_atom:
        return edge[0].atom and edge[0].root() == 'var'  # type: ignore[no-any-return]
    return False


def contains_variable(edge: Hyperedge) -> bool:
    if edge.atom:
        return False
    else:
        if is_variable(edge):
            return True
        return any(contains_variable(subedge) for subedge in edge)


def all_variables(edge: Hyperedge | None, _vars: Counter[Any] | None = None) -> Counter[Any]:
    if _vars is None:
        _vars = Counter()
    if edge is None:
        return _vars
    if edge.atom:
        return _vars
    else:
        if is_variable(edge):
            _vars[edge[2]] += 1
        for subedge in edge:
            all_variables(subedge, _vars=_vars)
    return _vars


def extract_vars_map(
        edge: Hyperedge | None,
        _vars: dict[str, Hyperedge] | None = None
) -> dict[str, Hyperedge]:
    if _vars is None:
        _vars = {}

    if edge is None:
        return _vars
    if edge.not_atom:
        if is_variable(edge):
            new_edge: Hyperedge = edge[1]
            var_name = str(edge[2])
            if var_name in _vars:
                cur_edge = _vars[var_name]
                if cur_edge.not_atom and str(cur_edge[0]) == const.list_or_matches_builder:
                    new_edge = cur_edge + (new_edge,)
                else:
                    result = hedge((hedge(const.list_or_matches_builder), cur_edge, new_edge))
                    assert result is not None
                    new_edge = result
            _vars[var_name] = new_edge
        for subedge in edge:
            extract_vars_map(subedge, _vars=_vars)
    return _vars


def remove_variables(edge: Hyperedge) -> Hyperedge:
    if is_variable(edge):
        return remove_variables(edge[1])
    if edge.atom:
        return edge
    else:
        result = hedge([remove_variables(subedge) for subedge in edge])
        assert result is not None
        return result


def apply_variable(
        edge: Hyperedge,
        var_name: str,
        var_edge: Hyperedge | list[Hyperedge]
) -> tuple[Hyperedge, bool]:
    clean_edge = remove_variables(edge)
    if clean_edge == var_edge or (type(var_edge) == list and clean_edge in var_edge):
        result = hedge(('var', clean_edge, var_name))
        assert result is not None
        return result, True

    subedges: list[Hyperedge] = []
    found = False
    if edge.not_atom:
        for subedge in edge:
            vedge, vresult = apply_variable(subedge, var_name, var_edge)
            subedges.append(vedge)
            if vresult:
                found = True
        hedge_result = hedge(subedges)
        assert hedge_result is not None
        return hedge_result, found

    return edge, False


def apply_variables(
        edge: Hyperedge,
        variables: dict[str, Hyperedge | list[Hyperedge]]
) -> Hyperedge | None:
    new_edge = edge
    for var_name, var_edge in variables.items():
        new_edge, found = apply_variable(new_edge, var_name, var_edge)
        if not found:
            return None
    return new_edge
