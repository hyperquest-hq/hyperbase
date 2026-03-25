from collections import Counter

from hyperbase import hedge
from hyperbase.patterns.properties import is_pattern
import hyperbase.constants as const


def apply_vars(edge, variables):
    if edge.atom:
        if is_pattern(edge):
            varname = _varname(edge)
            if len(varname) > 0 and varname in variables:
                return variables[varname]
        return edge
    else:
        return hedge([apply_vars(subedge, variables) for subedge in edge])


def _varname(atom):
    if not atom.atom:
        return ''
    label = atom.parts()[0]
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


def _assign_edge_to_var(curvars, var_name, edge):
    new_edge = edge
    if var_name in curvars:
        cur_edge = curvars[var_name]
        if cur_edge.not_atom and str(cur_edge[0]) == const.list_or_matches_builder:
            new_edge = cur_edge + (edge,)
        else:
            new_edge = hedge((hedge(const.list_or_matches_builder), cur_edge, edge))
    return {var_name: new_edge}


def is_variable(edge):
    if edge.not_atom:
        return edge[0].atom and edge[0].root() == 'var'
    return False


def contains_variable(edge):
    if edge.atom:
        return False
    else:
        if is_variable(edge):
            return True
        return any(contains_variable(subedge) for subedge in edge)


def all_variables(edge, _vars=None):
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


def extract_vars_map(edge, _vars=None):
    if _vars is None:
        _vars = {}

    if edge is None:
        return _vars
    if edge.not_atom:
        if is_variable(edge):
            new_edge = edge[1]
            var_name = str(edge[2])
            if var_name in _vars:
                cur_edge = _vars[var_name]
                if cur_edge.not_atom and str(cur_edge[0]) == const.list_or_matches_builder:
                    new_edge = cur_edge + (new_edge,)
                else:
                    new_edge = hedge((hedge(const.list_or_matches_builder), cur_edge, new_edge))
            _vars[var_name] = new_edge
        for subedge in edge:
            extract_vars_map(subedge, _vars=_vars)
    return _vars


def remove_variables(edge):
    if is_variable(edge):
        return remove_variables(edge[1])
    if edge.atom:
        return edge
    else:
        return hedge([remove_variables(subedge) for subedge in edge])


def apply_variable(edge, var_name, var_edge):
    clean_edge = remove_variables(edge)
    if clean_edge == var_edge or (type(var_edge) == list and clean_edge in var_edge):
        return hedge(('var', clean_edge, var_name)), True

    subedges = []
    found = False
    if edge.not_atom:
        for subedge in edge:
            vedge, result = apply_variable(subedge, var_name, var_edge)
            subedges.append(vedge)
            if result:
                found = True
        return hedge(subedges), found

    return edge, False


def apply_variables(edge, variables):
    new_edge = edge
    for var_name, var_edge in variables.items():
        new_edge, found = apply_variable(new_edge, var_name, var_edge)
        if not found:
            return None
    return new_edge
