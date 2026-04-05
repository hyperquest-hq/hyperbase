from __future__ import annotations

from collections import Counter

from hyperbase import hedge
from hyperbase.hyperedge import Hyperedge


class PatternCounter:
    def __init__(
        self,
        depth: int = 2,
        count_subedges: bool = True,
        expansions: set[str] | None = None,
        match_roots: set[str] | None = None,
        match_subtypes: set[str] | None = None,
    ) -> None:
        self.patterns: Counter[Hyperedge | None] = Counter()
        self.depth = depth
        self.count_subedges = count_subedges
        if expansions is None:
            self.expansions: set[str] = {"*"}
        else:
            self.expansions = expansions
        if match_roots is None:
            self.match_roots: set[str] = set()
        else:
            self.match_roots = match_roots
        if match_subtypes is None:
            self.match_subtypes: set[str] = set()
        else:
            self.match_subtypes = match_subtypes

    def _matches_expansions(self, edge: Hyperedge) -> bool:
        return any(edge.match(expansion) for expansion in self.expansions)

    def _force_subtypes(self, edge: Hyperedge) -> bool:
        force_subtypes = False
        for st_pattern in self.match_subtypes:
            if edge.match(st_pattern):
                force_subtypes = True
        return force_subtypes

    def _force_root_expansion(self, edge: Hyperedge) -> tuple[bool, bool]:
        force_root = False
        force_expansion = False
        for root_pattern in self.match_roots:
            if edge.match(root_pattern):
                force_root = True
                force_expansion = True
            elif _inner_edge_matches_pattern(edge, root_pattern):
                force_expansion = True
        return force_root, force_expansion

    def _list2patterns(
        self,
        ledge: list[Hyperedge],
        depth: int = 1,
        force_expansion: bool = False,
        force_root: bool = False,
        force_subtypes: bool = False,
    ) -> list[list[Hyperedge | None]]:
        if depth > self.depth:
            return []

        first = ledge[0]

        f_force_subtypes = force_subtypes | self._force_subtypes(first)

        f_force_root, f_force_expansion = self._force_root_expansion(first)
        f_force_root |= force_root
        f_force_expansion |= force_expansion
        root = force_root | f_force_root

        if f_force_expansion and not first.atom:
            hpats: list[Hyperedge | None] = []
        else:
            hpats = [_edge2pattern(first, root=root, subtype=f_force_subtypes)]

        if not first.atom and (self._matches_expansions(first) or f_force_expansion):
            hpats += self._list2patterns(
                list(first),
                depth + 1,
                force_expansion=f_force_expansion,  # type: ignore[arg-type]
                force_root=f_force_root,
                force_subtypes=f_force_subtypes,
            )
        if len(ledge) == 1:
            patterns: list[list[Hyperedge | None]] = [[hpat] for hpat in hpats]
        else:
            patterns = []
            for pattern in self._list2patterns(
                ledge[1:],
                depth=depth,
                force_expansion=force_expansion,
                force_root=force_root,
                force_subtypes=force_subtypes,
            ):
                for hpat in hpats:
                    patterns.append([hpat, *pattern])
        return patterns

    def _edge2patterns(self, edge: Hyperedge) -> list[Hyperedge]:
        force_subtypes = self._force_subtypes(edge)
        force_root, _ = self._force_root_expansion(edge)
        normalized = edge.normalise()
        return [
            hedge(pattern)
            for pattern in self._list2patterns(
                list(normalized), force_subtypes=force_subtypes, force_root=force_root
            )
        ]

    def count(self, edge: Hyperedge | str) -> None:
        parsed = hedge(edge)
        if parsed.not_atom:
            if self._matches_expansions(parsed):
                for pattern in self._edge2patterns(parsed):
                    self.patterns[pattern] += 1
            if self.count_subedges:
                for subedge in parsed:
                    self.count(subedge)


def _edge2pattern(
    edge: Hyperedge, root: bool = False, subtype: bool = False
) -> Hyperedge:
    root_str = edge.root() if root and edge.atom else "*"  # type: ignore[attr-defined]
    et = edge.type() if subtype else edge.mtype()
    pattern = f"{root_str}/{et}"
    ar = edge.argroles()
    if ar == "":
        return hedge(pattern)
    else:
        return hedge(f"{pattern}.{ar}")


def _inner_edge_matches_pattern(edge: Hyperedge, pattern: str) -> bool:
    if edge.atom:
        return False
    for subedge in edge:
        if subedge.match(pattern):
            return True
    return any(_inner_edge_matches_pattern(subedge, pattern) for subedge in edge)
