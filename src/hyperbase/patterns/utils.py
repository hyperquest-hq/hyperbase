from typing import Union

from hyperbase import hedge
from hyperbase.hyperedge import Hyperedge
from hyperbase.hypergraph import Hypergraph
from hyperbase.patterns.properties import is_fun_pattern
from hyperbase.patterns.variables import is_variable


# remove pattern functions from pattern, so that .argroles() works normally
def _defun_pattern_argroles(edge):
    if edge.atom:
        return edge

    if edge[0].argroles() != '':
        return edge

    if is_fun_pattern(edge):
        fun = edge[0].root()
        if fun == 'atoms':
            for atom in edge.atoms():
                argroles = atom.argroles()
                if argroles != '':
                    return atom
            # if no atom with argroles is found, just return the first one
            return edge[1]
        else:
            return hedge([edge[0], _defun_pattern_argroles(edge[1])] + list(edge[2:]))
    else:
        return hedge([_defun_pattern_argroles(subedge) for subedge in edge])


def _atoms_and_tok_pos(edge, tok_pos):
    if edge.atom:
        return [edge], [tok_pos]
    atoms = []
    atoms_tok_pos = []
    for edge_item, tok_pos_item in zip(edge, tok_pos):
        _atoms, _atoms_tok_pos = _atoms_and_tok_pos(edge_item, tok_pos_item)
        for _atom, _atom_tok_pos in zip(_atoms, _atoms_tok_pos):
            if _atom not in atoms:
                atoms.append(_atom)
                atoms_tok_pos.append(_atom_tok_pos)
    return atoms, atoms_tok_pos


def _normalize_fun_patterns(pattern):
    if pattern.atom:
        return pattern

    pattern = hedge([_normalize_fun_patterns(subpattern) for subpattern in pattern])

    if is_fun_pattern(pattern):
        if str(pattern[0]) == 'lemma':
            if is_fun_pattern(pattern[1]) and str(pattern[1][0]) == 'any':
                new_pattern = ['any']
                for alternative in pattern[1][1:]:
                    new_pattern.append(['lemma', alternative])
                return hedge(new_pattern)

    return pattern


def _edge_tok_pos(edge: Hyperedge, hg: Hypergraph = None) -> Union[Hyperedge, None]:
    if hg is None:
        # logger.debug(f"No hypergraph given to retrieve 'tok_pos' attribute for edge")
        return None

    tok_pos_str: str = hg.get_str_attribute(edge, "tok_pos")
    # edge is not a root edge
    if not tok_pos_str:
        # logger.debug(f"Edge has no 'tok_pos' string attribute: {edge}")
        return None

    try:
        tok_pos_hedge: Hyperedge = hedge(tok_pos_str)
    except ValueError:
        # logger.warning(f"Edge has invalid 'tok_pos' attribute: {edge}")
        return None

    return tok_pos_hedge


def is_valid(edge, _vars=None):
    if _vars is None:
        _vars = set()
    if edge is None:
        return False
    if edge.atom:
        return True
    if is_variable(edge):
        if edge[2].not_atom:
            return False
        # if edge[2] in _vars:
        #     return False
        _vars.add(edge[2])
        return is_valid(edge[1], _vars=_vars)
    return all(is_valid(subedge, _vars=_vars) for subedge in edge)


def more_general(edge1, edge2):
    r1, s1, t1 = atom_pattern_counts(edge1)
    r2, s2, t2 = atom_pattern_counts(edge2)
    if r1 == r2:
        if s1 == s2:
            return t1 < t2
        return s1 < s2
    return r1 < r2


def atom_pattern_counts(edge):
    if edge.atom:
        parts = edge.parts()
        roots = 1 if parts[0] != '*' else 0
        subtyped = 1 if len(edge.type()) > 1 else 0
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
