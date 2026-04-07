from __future__ import annotations

import itertools
from collections import Counter
from typing import Any, cast

import hyperbase.constants as const
from hyperbase import hedge
from hyperbase.hyperedge import Atom, Hyperedge

# tok_pos can be nested lists/ints matching the edge structure
TokPos = Any


def match_pattern(
    edge: Hyperedge | str | list[object] | tuple[object, ...],
    pattern: Hyperedge | str | list[object] | tuple[object, ...],
    curvars: dict[str, Hyperedge] | None = None,
) -> list[dict[str, Hyperedge]]:
    """
    Matches an edge to a pattern. This means that, if the edge fits the
    pattern, then a list of dictionaries will be returned. If the pattern
    specifies variables, then the returned dictionaries will be populated
    with the values for each pattern variable. There can be more than one
    dictionary in the list if there are multiple ways of matching the
    variables. If the pattern specifies no variables but the edge matches
    it, then a list with a single empty dictionary is returned. If the
    edge does not match the pattern, an empty list is returned.

    Patterns are themselves edges. They can match families of edges
    by employing special atoms:

    - `\\*` represents a general wildcard (matches any entity)
    - `.` represents an atomic wildcard (matches any atom)
    - `(\\*)` represents an edge wildcard (matches any non-atom)
    - `...` at the end indicates an open-ended pattern.

    The wildcards (`\\*`, `.` and `(\\*)`) can be used to specify variables,
    for example `\\*x`, `(CLAIM)` or `.ACTOR`. In case of a match, these
    variables are assigned the hyperedge they correspond to. For example, consider
    the edge:

    `(is/P.so (my/Mp name/Cn) mary/Cp)`

    - matching to the pattern: `(is/P.so (my/Mp name/Cn) \\*)`
    produces the result: `[{}]`
    - matching to the pattern: `(is/P.so (my/Mp name/Cn) \\*NAME)`
    produces the result: `[{'NAME', mary/Cp}]`
    - matching to the pattern: `(is/P.so . \\*NAME)`
    produces the result: `[]`
    """
    _edge = hedge(edge)
    _pattern = hedge(pattern)
    if _edge is None or _pattern is None:
        return []
    _pattern = _normalise_fun_patterns(_pattern)

    matcher: Matcher = Matcher(
        edge=_edge,
        pattern=_pattern,
        curvars=curvars,
    )

    return matcher.results


def _normalise_fun_patterns(pattern: Hyperedge) -> Hyperedge:
    if pattern.atom:
        return pattern

    normalized = hedge([_normalise_fun_patterns(subpattern) for subpattern in pattern])
    assert normalized is not None
    pattern = normalized

    if (
        pattern.is_fun_pattern()
        and str(pattern[0]) == "lemma"
        and pattern[1].is_fun_pattern()
        and str(pattern[1][0]) == "any"
    ):
        new_pattern: list[str | Hyperedge | list[Any]] = ["any"]
        for alternative in pattern[1][1:]:
            new_pattern.append(["lemma", alternative])
        result = hedge(new_pattern)
        assert result is not None
        return result

    return pattern


# remove pattern functions from pattern, so that .argroles() works normally
def _defun_pattern_argroles(edge: Hyperedge) -> Hyperedge:
    if edge.atom:
        return edge

    if edge[0].argroles() != "":
        return edge

    if edge.is_fun_pattern():
        fun: str = cast(Atom, edge[0]).root()
        if fun == "atoms":
            for atom in edge.atoms():
                argroles = atom.argroles()
                if argroles != "":
                    return atom
            # if no atom with argroles is found, just return the first one
            return edge[1]
        else:
            result = hedge([edge[0], _defun_pattern_argroles(edge[1]), *list(edge[2:])])
            assert result is not None
            return result
    else:
        result = hedge([_defun_pattern_argroles(subedge) for subedge in edge])
        assert result is not None
        return result


def _atoms_and_tok_pos(
    edge: Hyperedge, tok_pos: TokPos
) -> tuple[list[Atom], list[Any]]:
    if edge.atom:
        atom = cast(Atom, edge)
        return [atom], [tok_pos]
    atoms: list[Atom] = []
    atoms_tok_pos: list[Any] = []
    for edge_item, tok_pos_item in zip(edge, tok_pos, strict=False):
        _atoms, _atoms_tok_pos = _atoms_and_tok_pos(edge_item, tok_pos_item)
        for _atom, _atom_tok_pos in zip(_atoms, _atoms_tok_pos, strict=False):
            if _atom not in atoms:
                atoms.append(_atom)
                atoms_tok_pos.append(_atom_tok_pos)
    return atoms, atoms_tok_pos


#########
# atoms #
#########


def _matches_atomic_pattern(edge: Hyperedge, atomic_pattern: Atom) -> bool:
    ap_parts = atomic_pattern.parts()

    if len(ap_parts) == 0 or len(ap_parts[0]) == 0:
        return False

    # structural match
    struct_code = ap_parts[0][0]
    if struct_code == ".":
        if edge.not_atom:
            return False
    elif atomic_pattern.parens:
        if edge.atom:
            return False
    elif struct_code != "*" and not struct_code.isupper():
        if edge.not_atom:
            return False
        atom = cast(Atom, edge)
        if atom.root() != atomic_pattern.root():
            return False

    # role match
    if len(ap_parts) > 1:
        pos = 1

        # type match
        ap_role = atomic_pattern.role()
        ap_type = ap_role[0]
        e_type = edge.type()
        n = len(ap_type)
        if len(e_type) < n or e_type[:n] != ap_type:
            return False

        e_atom = edge.inner_atom()

        if len(ap_role) > 1:
            e_role = e_atom.role()
            # check if edge role has enough parts to satisfy the wildcard
            # specification
            if len(e_role) < len(ap_role):
                return False

            # argroles match
            if ap_type[0] in {"B", "P"}:
                ap_argroles_parts = ap_role[1].split("-")
                if len(ap_argroles_parts) == 1:
                    ap_argroles_parts.append("")
                ap_negroles = ap_argroles_parts[1]

                # fixed order?
                ap_argroles_posopt = ap_argroles_parts[0]
                e_argroles = e_role[1]
                if len(ap_argroles_posopt) > 0 and ap_argroles_posopt[0] == "{":
                    ap_argroles_posopt = ap_argroles_posopt[1:-1]
                elif "[" not in ap_argroles_posopt:
                    ap_argroles_posopt = ap_argroles_posopt.replace(",", "")
                    if len(e_argroles) > len(ap_argroles_posopt):
                        return False
                    else:
                        return ap_argroles_posopt.startswith(e_argroles)  # type: ignore[no-any-return]
                # else: has [...] ordered subsequence brackets, fall through

                # check [...] contiguity constraints
                if "[" in ap_argroles_posopt:
                    i = 0
                    while i < len(ap_argroles_posopt):
                        if ap_argroles_posopt[i] == "[":
                            j = ap_argroles_posopt.index("]", i)
                            group = ap_argroles_posopt[i + 1 : j]
                            if group not in e_argroles:
                                return False
                            i = j + 1
                        else:
                            i += 1
                    # strip brackets for count checking below
                    ap_argroles_posopt = ap_argroles_posopt.replace("[", "").replace(
                        "]", ""
                    )

                ap_argroles_parts = ap_argroles_posopt.split(",")
                ap_posroles = ap_argroles_parts[0]
                ap_argroles = set(ap_posroles) | set(ap_negroles)
                for argrole in ap_argroles:
                    min_count = ap_posroles.count(argrole)
                    # if there are argrole exclusions
                    fixed = ap_negroles.count(argrole) > 0
                    count = e_argroles.count(argrole)
                    if count < min_count:
                        return False
                    # deal with exclusions
                    if fixed and count > min_count:
                        return False
                pos = 2

            # match rest of role
            while pos < len(ap_role):
                if e_role[pos] != ap_role[pos]:
                    return False
                pos += 1

    # match rest of atom
    if len(ap_parts) > 2:
        e_parts = e_atom.parts()
        # check if edge role has enough parts to satisfy the wildcard
        # specification
        if len(e_parts) < len(ap_parts):
            return False

        while pos < len(ap_parts):
            if e_parts[pos] != ap_parts[pos]:
                return False
            pos += 1

    return True


############
# argroles #
############


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


#############
# variables #
#############


def _assign_edge_to_var(
    curvars: dict[str, Hyperedge], var_name: str, edge: Hyperedge
) -> dict[str, Hyperedge]:
    new_edge: Hyperedge = edge
    if var_name in curvars:
        cur_edge = curvars[var_name]
        if cur_edge.not_atom and str(cur_edge[0]) == const.list_of_matches_builder:
            new_edge = hedge((*cur_edge, edge))
        else:
            new_edge = hedge((const.list_of_matches_builder, cur_edge, edge))
    return {var_name: new_edge}


#################
# Matcher class #
#################


class Matcher:
    def __init__(
        self,
        edge: Hyperedge,
        pattern: Hyperedge,
        curvars: dict[str, Hyperedge] | None = None,
        tok_pos: TokPos = None,
    ) -> None:
        self.results: list[dict[str, Hyperedge]] = self.match(
            edge, pattern, curvars=curvars, tok_pos=tok_pos
        )

    def match(
        self,
        edge: Hyperedge,
        pattern: Hyperedge,
        curvars: dict[str, Hyperedge] | None = None,
        tok_pos: TokPos = None,
    ) -> list[dict[str, Hyperedge]]:
        if curvars is None:
            curvars = {}

        # functional patterns
        if pattern.is_fun_pattern():
            return self._match_fun_pat(edge, pattern, curvars, tok_pos=tok_pos)

        # function pattern on edge can never match non-functional pattern
        if edge.is_fun_pattern():
            return []

        # atomic patterns
        if pattern.atom:
            atomic_pattern = cast(Atom, pattern)
            if _matches_atomic_pattern(edge, atomic_pattern):
                variables: dict[str, Hyperedge] = {}
                if pattern.is_variable():
                    varname = pattern.variable_name()
                    variables[varname] = _assign_edge_to_var(
                        {**curvars, **variables}, varname, edge
                    )[varname]
                return [{**curvars, **variables}]
            else:
                return []

        min_len = len(pattern)
        max_len: int | float = min_len
        # open-ended?
        if str(pattern[-1]) == "...":
            new_pattern = hedge(pattern[:-1])
            if new_pattern is None:
                return []
            pattern = new_pattern
            min_len -= 1
            max_len = float("inf")

        result: list[dict[str, Hyperedge]] = [{}]
        argroles_posopt = _defun_pattern_argroles(pattern)[0].argroles().split("-")[0]
        if len(argroles_posopt) > 0 and argroles_posopt[0] == "{":
            match_by_order = False
            argroles_posopt = argroles_posopt[1:-1]
        elif "[" in argroles_posopt:
            match_by_order = False
        else:
            match_by_order = True
        argroles = argroles_posopt.replace("[", "").replace("]", "").split(",")[0]
        argroles_opt = (
            argroles_posopt.replace("[", "").replace("]", "").replace(",", "")
        )

        if len(argroles) > 0:
            min_len = 1 + len(argroles)
            max_len = float("inf")
        else:
            match_by_order = True

        if len(edge) < min_len or len(edge) > max_len:
            return []

        # match by order
        if match_by_order:
            for i, pitem in enumerate(pattern):
                eitem = edge[i]
                _result: list[dict[str, Hyperedge]] = []

                for variables in result:
                    if pitem.atom:
                        aitem = cast(Atom, pitem)
                        if _matches_atomic_pattern(eitem, aitem):
                            if pitem.is_variable():
                                varname = pitem.variable_name()
                                if varname[0].isupper():
                                    variables[varname] = _assign_edge_to_var(
                                        {**curvars, **variables}, varname, eitem
                                    )[varname]
                        else:
                            continue
                        _result.append(variables)
                    else:
                        tok_pos_item = None
                        if tok_pos is not None:
                            try:
                                assert len(tok_pos) > i
                            except AssertionError as e:
                                raise RuntimeError(
                                    f"Index '{i}' in tok_pos '{tok_pos}' out of range"
                                ) from e
                            tok_pos_item = tok_pos[i]
                        _result += self.match(
                            eitem, pitem, {**curvars, **variables}, tok_pos=tok_pos_item
                        )
                result = _result
        # match by argroles
        else:
            result = []
            # match connector first
            ctok_pos = tok_pos[0] if tok_pos else None
            if self.match(edge[0], pattern[0], curvars, tok_pos=ctok_pos):
                role_counts = Counter(argroles_opt).most_common()
                unknown_roles = (len(pattern) - 1) - len(argroles_opt)
                if unknown_roles > 0:
                    role_counts.append(("*", unknown_roles))
                # add connector pseudo-argrole
                role_counts = [("X", 1), *role_counts]
                result = _match_by_argroles(
                    self,
                    edge,
                    pattern,
                    role_counts,
                    len(argroles),
                    curvars=curvars,
                    tok_pos=tok_pos,
                )

        unique_vars: list[dict[str, Hyperedge]] = []
        for variables in result:
            v = {**curvars, **variables}
            if v not in unique_vars:
                unique_vars.append(v)
        return unique_vars

    def _match_atoms(
        self,
        atom_patterns: tuple[Hyperedge, ...],
        atoms: set[Atom] | list[Atom],
        curvars: dict[str, Hyperedge],
        atoms_tok_pos: list[Any] | None = None,
        matched_atoms: list[Atom] | None = None,
    ) -> list[dict[str, Hyperedge]]:
        if matched_atoms is None:
            matched_atoms = []

        if len(atom_patterns) == 0:
            return [curvars]

        results: list[dict[str, Hyperedge]] = []
        atom_pattern = atom_patterns[0]

        for atom_pos, atom in enumerate(atoms):
            if atom not in matched_atoms:
                tok_pos = atoms_tok_pos[atom_pos] if atoms_tok_pos else None
                svars = self.match(atom, atom_pattern, curvars, tok_pos=tok_pos)
                for variables in svars:
                    results += self._match_atoms(
                        atom_patterns[1:],
                        atoms,
                        {**curvars, **variables},
                        atoms_tok_pos=atoms_tok_pos,
                        matched_atoms=[*matched_atoms, atom],
                    )

        return results

    def _match_fun_pat(
        self,
        edge: Hyperedge,
        fun_pattern: Hyperedge,
        curvars: dict[str, Hyperedge],
        tok_pos: TokPos = None,
    ) -> list[dict[str, Hyperedge]]:

        fun_atom = fun_pattern[0]
        try:
            assert fun_atom.atom
        except AssertionError as e:
            raise ValueError(f"Connector in fun pattern is not atom: {fun_atom}") from e
        fun = cast(Atom, fun_atom).root()
        try:
            assert fun in const.PATTERN_FUNCTIONS
        except AssertionError as e:
            raise ValueError(f"Unknown pattern function: {fun}") from e

        if fun == "var":
            if len(fun_pattern) != 3:
                raise RuntimeError("var pattern function must have two arguments")
            pattern = fun_pattern[1]

            var_name_atom = fun_pattern[2]
            try:
                assert var_name_atom.atom
            except AssertionError as e:
                raise ValueError(f"Bariable name is not atom: {var_name_atom}") from e
            var_name = cast(Atom, var_name_atom).root()
            if (
                edge.not_atom
                and str(edge[0]) == "var"
                and len(edge) == 3
                and str(edge[2]) == var_name
            ):
                this_var = _assign_edge_to_var(curvars, var_name, edge[1])
                return self.match(
                    edge[1], pattern, curvars={**curvars, **this_var}, tok_pos=tok_pos
                )
            else:
                this_var = _assign_edge_to_var(curvars, var_name, edge)
                return self.match(
                    edge, pattern, curvars={**curvars, **this_var}, tok_pos=tok_pos
                )
        elif fun == "atoms":
            if tok_pos:
                atoms_list, atoms_tok_pos = _atoms_and_tok_pos(edge, tok_pos)
            else:
                atoms_list = list(edge.atoms())
                atoms_tok_pos = None
            atom_patterns = fun_pattern[1:]
            return self._match_atoms(
                atom_patterns, atoms_list, curvars, atoms_tok_pos=atoms_tok_pos
            )
        elif fun == "any":
            for pattern in fun_pattern[1:]:
                matches = self.match(edge, pattern, curvars=curvars, tok_pos=tok_pos)
                if len(matches) > 0:
                    return matches
            return []
        else:
            raise NotImplementedError(f"Pattern function '{fun}' not implemented.")
