from __future__ import annotations

from typing import Any

from hyperbase import hedge
from hyperbase.hyperedge import Atom, Hyperedge
from hyperbase.patterns.properties import is_fun_pattern
from hyperbase.patterns.variables import is_variable


# remove pattern functions from pattern, so that .argroles() works normally
def _defun_pattern_argroles(edge: Hyperedge) -> Hyperedge:
    if edge.atom:
        return edge

    if edge[0].argroles() != "":
        return edge

    if is_fun_pattern(edge):
        fun: str = edge[0].root()
        if fun == "atoms":
            for atom in edge.atoms():
                argroles = atom.argroles()
                if argroles != "":
                    return atom
            # if no atom with argroles is found, just return the first one
            return edge[1]  # type: ignore[no-any-return]
        else:
            result = hedge([edge[0], _defun_pattern_argroles(edge[1]), *list(edge[2:])])
            assert result is not None
            return result
    else:
        result = hedge([_defun_pattern_argroles(subedge) for subedge in edge])
        assert result is not None
        return result


def _atoms_and_tok_pos(edge: Hyperedge, tok_pos: int) -> tuple[list[Atom], list[Any]]:
    if edge.atom:
        return [edge], [tok_pos]  # type: ignore[list-item]
    atoms: list[Atom] = []
    atoms_tok_pos: list[Any] = []
    for edge_item, tok_pos_item in zip(edge, tok_pos, strict=False):
        _atoms, _atoms_tok_pos = _atoms_and_tok_pos(edge_item, tok_pos_item)
        for _atom, _atom_tok_pos in zip(_atoms, _atoms_tok_pos, strict=False):
            if _atom not in atoms:
                atoms.append(_atom)
                atoms_tok_pos.append(_atom_tok_pos)
    return atoms, atoms_tok_pos


def _normalize_fun_patterns(pattern: Hyperedge) -> Hyperedge:
    if pattern.atom:
        return pattern

    normalized = hedge([_normalize_fun_patterns(subpattern) for subpattern in pattern])
    assert normalized is not None
    pattern = normalized

    if (
        is_fun_pattern(pattern)
        and str(pattern[0]) == "lemma"
        and is_fun_pattern(pattern[1])
        and str(pattern[1][0]) == "any"
    ):
        new_pattern: list[str | Hyperedge | list[Any]] = ["any"]
        for alternative in pattern[1][1:]:
            new_pattern.append(["lemma", alternative])
        result = hedge(new_pattern)
        assert result is not None
        return result

    return pattern


def is_valid(edge: Hyperedge | None, _vars: set[Hyperedge] | None = None) -> bool:
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
        parts: list[str] = edge.parts()  # type: ignore[attr-defined]
        roots = 1 if parts[0] != "*" else 0
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
