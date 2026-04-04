from __future__ import annotations

from collections import Counter
from typing import Any

from hyperbase import hedge
from hyperbase.hyperedge import Atom, Hyperedge
from hyperbase.patterns.argroles import _match_by_argroles
from hyperbase.patterns.atoms import _matches_atomic_pattern
from hyperbase.patterns.properties import is_fun_pattern, is_pattern, FUNS
from hyperbase.patterns.utils import _defun_pattern_argroles, _atoms_and_tok_pos
from hyperbase.patterns.variables import _varname, _assign_edge_to_var

# tok_pos can be nested lists/ints matching the edge structure
TokPos = Any


class Matcher:
    def __init__(
            self,
            edge: Hyperedge,
            pattern: Hyperedge,
            curvars: dict[str, Hyperedge] | None = None,
            tok_pos: TokPos = None
    ) -> None:
        self.results: list[dict[str, Hyperedge]] = self.match(edge, pattern, curvars=curvars, tok_pos=tok_pos)

    def match(
            self,
            edge: Hyperedge,
            pattern: Hyperedge,
            curvars: dict[str, Hyperedge] | None = None,
            tok_pos: TokPos = None
    ) -> list[dict[str, Hyperedge]]:
        if curvars is None:
            curvars = {}

        # functional patterns
        if is_fun_pattern(pattern):
            return self._match_fun_pat(
                edge,
                pattern,
                curvars,
                tok_pos=tok_pos
            )

        # function pattern on edge can never match non-functional pattern
        if is_fun_pattern(edge):
            return []

        # atomic patterns
        if pattern.atom:
            if _matches_atomic_pattern(edge, pattern):
                variables: dict[str, Hyperedge] = {}
                if is_pattern(pattern):
                    varname = _varname(pattern)
                    if len(varname) > 0:
                        variables[varname] = _assign_edge_to_var({**curvars, **variables}, varname, edge)[varname]
                return [{**curvars, **variables}]
            else:
                return []

        min_len = len(pattern)
        max_len: int | float = min_len
        # open-ended?
        if str(pattern[-1]) == '...':
            new_pattern = hedge(pattern[:-1])
            if new_pattern is None:
                return []
            pattern = new_pattern
            min_len -= 1
            max_len = float('inf')

        result: list[dict[str, Hyperedge]] = [{}]
        argroles_posopt = _defun_pattern_argroles(pattern)[0].argroles().split('-')[0]
        if len(argroles_posopt) > 0 and argroles_posopt[0] == '{':
            match_by_order = False
            argroles_posopt = argroles_posopt[1:-1]
        else:
            match_by_order = True
        argroles = argroles_posopt.split(',')[0]
        argroles_opt = argroles_posopt.replace(',', '')

        if len(argroles) > 0:
            min_len = 1 + len(argroles)
            max_len = float('inf')
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
                        varname = _varname(pitem)
                        if _matches_atomic_pattern(eitem, pitem):
                            if len(varname) > 0 and varname[0].isupper():
                                variables[varname] = _assign_edge_to_var(
                                    {**curvars, **variables}, varname, eitem)[varname]
                        else:
                            continue
                        _result.append(variables)
                    else:
                        tok_pos_item = None
                        if tok_pos is not None:
                            try:
                                assert len(tok_pos) > i
                            except AssertionError:
                                raise RuntimeError(f"Index '{i}' in tok_pos '{tok_pos}' is out of range")
                            tok_pos_item = tok_pos[i]
                        _result += self.match(
                            eitem,
                            pitem,
                            {**curvars, **variables},
                            tok_pos=tok_pos_item
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
                    role_counts.append(('*', unknown_roles))
                # add connector pseudo-argrole
                role_counts = [('X', 1)] + role_counts
                result = _match_by_argroles(
                    self,
                    edge,
                    pattern,
                    role_counts,
                    len(argroles),
                    curvars=curvars,
                    tok_pos=tok_pos
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
            matched_atoms: list[Atom] | None = None
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
                        matched_atoms=matched_atoms + [atom]
                    )

        return results

    def _match_fun_pat(
            self,
            edge: Hyperedge,
            fun_pattern: Hyperedge,
            curvars: dict[str, Hyperedge],
            tok_pos: TokPos = None
    ) -> list[dict[str, Hyperedge]]:
        fun = fun_pattern[0].root()

        try:
            assert fun in FUNS
        except AssertionError:
                raise ValueError(f"Unknown pattern function: {fun}")

        if fun == 'var':
            if len(fun_pattern) != 3:
                raise RuntimeError('var pattern function must have two arguments')
            pattern = fun_pattern[1]
            var_name = fun_pattern[2].root()
            if edge.not_atom and str(edge[0]) == 'var' and len(edge) == 3 and str(edge[2]) == var_name:
                this_var = _assign_edge_to_var(curvars, var_name, edge[1])
                return self.match(
                    edge[1],
                    pattern,
                    curvars={**curvars, **this_var},
                    tok_pos=tok_pos
                )
            else:
                this_var = _assign_edge_to_var(curvars, var_name, edge)
                return self.match(
                    edge,
                    pattern,
                    curvars={**curvars, **this_var},
                    tok_pos=tok_pos
                )
        elif fun == 'atoms':
            if tok_pos:
                atoms_list, atoms_tok_pos = _atoms_and_tok_pos(edge, tok_pos)
            else:
                atoms_list = list(edge.atoms())
                atoms_tok_pos = None
            atom_patterns = fun_pattern[1:]
            return self._match_atoms(
                atom_patterns,
                atoms_list,
                curvars,
                atoms_tok_pos=atoms_tok_pos
            )
        elif fun == 'any':
            for pattern in fun_pattern[1:]:
                matches = self.match(
                    edge,
                    pattern,
                    curvars=curvars,
                    tok_pos=tok_pos
                )
                if len(matches) > 0:
                    return matches
            return []
        else:
            raise NotImplementedError(f"Pattern function '{fun}' not implemented.")
