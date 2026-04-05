from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from hyperbase.parsers.parse_result import ParseResult


argrole_order: dict[str, int] = {
    "m": -1,
    "s": 0,
    "p": 1,
    "a": 2,
    "c": 3,
    "o": 4,
    "i": 5,
    "t": 6,
    "j": 7,
    "x": 8,
    "r": 9,
    "?": 10,
}


valid_p_argroles: set[str] = {"s", "p", "a", "c", "o", "i", "t", "j", "x", "r", "?"}
valid_b_argroles: set[str] = {"m", "a"}


def str_to_atom(s: str) -> str:
    """Converts a string into a valid atom."""
    atom = s.lower()

    atom = atom.replace("%", "%25")
    atom = atom.replace("/", "%2f")
    atom = atom.replace(" ", "%20")
    atom = atom.replace("(", "%28")
    atom = atom.replace(")", "%29")
    atom = atom.replace(".", "%2e")
    atom = atom.replace("*", "%2a")
    atom = atom.replace("&", "%26")
    atom = atom.replace("@", "%40")
    atom = atom.replace("\n", "%0a")
    atom = atom.replace("\r", "%0d")

    return atom


def _edge_str_has_outer_parens(edge_str: str) -> bool:
    """Check if string representation of edge is delimited by outer
    parenthesis.
    """
    if len(edge_str) < 2:
        return False
    return edge_str[0] == "("


def split_edge_str(edge_str: str) -> tuple[str, ...]:
    """Shallow split into tokens of a string representation of an edge,
    without outer parenthesis.
    """
    start = 0
    depth = 0
    str_length = len(edge_str)
    active = 0
    tokens: list[str] = []
    for i in range(str_length):
        c = edge_str[i]
        if c == " ":
            if active and depth == 0:
                tokens.append(edge_str[start:i])
                active = 0
        elif c == "(":
            if depth == 0:
                active = 1
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                tokens.append(edge_str[start : i + 1])
                active = 0
            elif depth < 0:
                raise ValueError(f"Unbalanced parenthesis in edge string: '{edge_str}'")
        else:
            if not active:
                active = 1
                start = i

    if active:
        if depth > 0:
            raise ValueError(f"Unbalanced parenthesis in edge string: '{edge_str}'")
        else:
            tokens.append(edge_str[start:])

    return tuple(tokens)


def _parsed_token(token: str) -> Hyperedge:
    if _edge_str_has_outer_parens(token):
        return hedge(token)
    else:
        return Atom((token,))


def _collect_positions(tok_pos: Hyperedge) -> list[int]:
    """Collect all valid (>= 0) token positions from a tok_pos tree."""
    if tok_pos.atom:
        pos = int(tok_pos[0])
        return [pos] if pos >= 0 else []
    else:
        positions: list[int] = []
        for sub in tok_pos:
            positions.extend(_collect_positions(sub))
        return positions


def _rebuild_with_text(
    edge: Hyperedge,
    tok_pos: Hyperedge,
    tokens: list[str],
) -> Hyperedge:
    """Recursively rebuild an edge, assigning text from tokens and tok_pos."""
    if edge.atom:
        pos = int(tok_pos[0])
        text = tokens[pos] if pos >= 0 else None
        return Atom(edge, edge.parens, text=text)
    else:
        new_children = tuple(
            _rebuild_with_text(sub_edge, sub_tok_pos, tokens)
            for sub_edge, sub_tok_pos in zip(edge, tok_pos, strict=False)
        )
        positions = _collect_positions(tok_pos)
        if positions:
            min_pos = min(positions)
            max_pos = max(positions)
            text = " ".join(tokens[min_pos : max_pos + 1])
        else:
            text = None
        return Hyperedge(new_children, text=text)


def hedge(
    source: str | Hyperedge | list | tuple | ParseResult,
) -> Hyperedge:
    """Create a hyperedge."""
    # Check for ParseResult via duck typing to avoid circular import
    if (
        hasattr(source, "tok_pos")
        and hasattr(source, "tokens")
        and hasattr(source, "edge")
    ):
        edge = _rebuild_with_text(source.edge, source.tok_pos, source.tokens)
        object.__setattr__(edge, "text", source.text)
        return edge
    if type(source) in {tuple, list}:
        return Hyperedge(tuple(hedge(item) for item in source))
    elif type(source) is str:
        edge_str = source.strip().replace("\n", " ")
        edge_inner_str = edge_str

        parens = _edge_str_has_outer_parens(edge_str)
        if parens:
            edge_inner_str = edge_str[1:-1]

        tokens = split_edge_str(edge_inner_str)
        if not tokens:
            raise ValueError(f"Edge string is empty: '{source}'")
        edges = tuple(_parsed_token(token) for token in tokens)
        if len(edges) == 1 and isinstance(edges[0], Atom):
            return Atom(edges[0], parens)
        elif len(edges) > 0:
            return Hyperedge(edges)
        else:
            raise ValueError(f"Edge string is empty: '{source}'")
    elif type(source) in {Hyperedge, Atom, UniqueAtom}:
        return source  # type: ignore
    else:
        raise TypeError(
            f"Cannot create hyperedge from {type(source).__name__}: {source!r}"
        )


def build_atom(text: str, *parts: str) -> Atom:
    """Build an atom from text and other parts."""
    atom = str_to_atom(text)
    parts_str = "/".join([part for part in parts if part])
    if len(parts_str) > 0:
        atom = "".join((atom, "/", parts_str))
    return Atom((atom,))


@dataclass(frozen=True, init=False, eq=False, repr=False)
class Hyperedge:
    """Non-atomic hyperedge."""

    _edges: tuple[Hyperedge, ...]
    text: str | None

    def __init__(
        self, edges: Iterable[Hyperedge | None], text: str | None = None
    ) -> None:
        object.__setattr__(self, "_edges", tuple(edges))
        object.__setattr__(self, "text", text)

    def __iter__(self) -> Iterator[Hyperedge | None]:
        return iter(self._edges)

    @overload
    def __getitem__(self, key: int) -> Hyperedge: ...
    @overload
    def __getitem__(self, key: slice) -> tuple[Hyperedge | None, ...]: ...

    def __getitem__(self, key):
        return self._edges[key]

    def __len__(self) -> int:
        return len(self._edges)

    def __hash__(self) -> int:
        return hash(self._edges)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Hyperedge):
            return self._edges == other._edges
        if isinstance(other, tuple):
            return self._edges == other
        return NotImplemented

    def __bool__(self) -> bool:
        return True

    @property
    def atom(self) -> bool:
        """True if edge is an atom."""
        return False

    @property
    def not_atom(self) -> bool:
        """True if edge is not an atom."""
        return True

    @property
    def t(self) -> str:
        """Edge type.
        (this porperty is a shortcut for Hyperedge.type())
        """
        return self.type()

    @property
    def mt(self) -> str:
        """Edge main type.
        (this porperty is a shortcut for Hyperedge.mtype())
        """
        return self.mtype()

    @property
    def ct(self) -> str | None:
        """Edge connector type.
        (this porperty is a shortcut for Hyperedge.connector_type())
        """
        return self.connector_type()

    @property
    def cmt(self) -> str | None:
        """Edge connector main type.
        (this porperty is a shortcut for Hyperedge.mconnector_type())
        """
        return self.connector_mtype()

    def match(
        self, pattern: Hyperedge | str | list[object] | tuple[object, ...]
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
        from hyperbase.patterns import match_pattern

        return match_pattern(self, pattern)

    def label(self) -> str:
        """Generate human-readable label for edge."""
        conn_atom = self.connector_atom()
        if len(self) == 2:
            edge: tuple[Any, ...] = self
        elif conn_atom is not None and conn_atom.parts()[-1] == ".":
            edge = self[1:]
        else:
            edge = (self[1], self[0], *self[2:])
        return " ".join([item.label() for item in edge])

    def inner_atom(self) -> Atom:
        """The inner atom inside of a modifier structure.

        For example, condider:
        (red/M shoes/C)
        The inner atom is:
        shoes/C
        Or, the more complex case:
        ((and/J slow/M steady/M) go/P)
        Yields:
        gp/P

        This method should not be used on structures that contain more than
        one inner atom, for example concepts constructed with builders or
        relations.

        The inner atom of an atom is itself.
        """
        return self[1].inner_atom()  # type: ignore[no-any-return]

    def connector_atom(self) -> Atom | None:
        """The inner atom of the connector.

        For example, condider:
        (does/M (not/M like/P.so) john/C chess/C)
        The connector atom is:
        like/P.so

        The connector atom of an atom is None.
        """
        return self[0].inner_atom()  # type: ignore[no-any-return]

    def atoms(self) -> set[Atom]:
        """Returns the set of atoms contained in the edge.

        For example, consider the edge:
        (the/md (of/br mayor/cc (the/md city/cs)))
        in this case, edge.atoms() returns:
        [the/md, of/br, mayor/cc, city/cs]
        """
        atom_set: set[Atom] = set()
        for item in self:
            for atom in item.atoms():
                atom_set.add(atom)
        return atom_set

    def all_atoms(self) -> list[Atom]:
        """Returns a list of all the atoms contained in the edge. Unlike
        atoms(), which does not return repeated atoms, all_atoms() does
        return repeated atoms if they are different objects.

        For example, consider the edge:
        (the/md (of/br mayor/cc (the/md city/cs)))
        in this case, edge.all_atoms() returns:
        [the/md, of/br, mayor/cc, the/md, city/cs]
        """
        atoms: list[Atom] = []
        for item in self:
            atoms += item.all_atoms()
        return atoms

    def size(self) -> int:
        """The size of an edge is its total number of atoms, at all depths."""
        return sum([edge.size() for edge in self])

    def depth(self) -> int:
        """Returns maximal depth of edge, an atom has depth 0."""
        max_d = 0
        for item in self:
            d = item.depth()
            if d > max_d:
                max_d = d
        return max_d + 1

    def contains(self, needle: str) -> bool:
        """Checks recursively if 'needle' is contained in edge."""
        for item in self:
            if item == needle:
                return True
            if item.contains(needle):
                return True
        return False

    def subedges(self) -> set[Hyperedge]:
        """Returns all the subedges contained in the edge, including atoms
        and itself.
        """
        edges: set[Hyperedge] = {self}
        for item in self:
            edges = edges.union(item.subedges())
        return edges

    def simplify(
        self, subtypes: bool = False, argroles: bool = False, namespaces: bool = True
    ) -> Hyperedge:
        """Returns a version of the edge with simplified atoms, for example
        removing subtypes, subroles or namespaces.

        Keyword arguments:
        subtypes -- include subtypes (default: False).
        argroles --include argroles (default: False).
        namespaces -- include namespaces (default: True).
        """
        return hedge(
            [
                subedge.simplify(
                    subtypes=subtypes, argroles=argroles, namespaces=namespaces
                )
                for subedge in self
            ]
        )

    def type(self) -> str:
        """Returns the type of this edge as a string.
        Type inference is performed.
        """
        ptype = self[0].type()
        if ptype[0] == "P":
            outter_type = "R"
        elif ptype[0] == "M":
            if len(self) < 2:
                raise RuntimeError(
                    f"Edge is malformed, type cannot be determined: {self!s}"
                )
            return self[1].type()  # type: ignore[no-any-return]
        elif ptype[0] == "T":
            outter_type = "S"
        elif ptype[0] == "B":
            outter_type = "C"
        elif ptype[0] == "J":
            if len(self) < 2:
                raise RuntimeError(
                    f"Edge is malformed, type cannot be determined: {self!s}"
                )
            return self[1].mtype()  # type: ignore[no-any-return]
        else:
            raise RuntimeError(
                f"Edge is malformed, type cannot be determined: {self!s}"
            )

        return f"{outter_type}{ptype[1:]}"

    def connector_type(self) -> str | None:
        """Returns the type of the edge's connector.
        If the edge has no connector (i.e. it's an atom), then None is
        returned.
        """
        return self[0].type()  # type: ignore[no-any-return]

    def mtype(self) -> str:
        """Returns the main type of this edge as a string of one character.
        Type inference is performed.
        """
        return self.type()[0]

    def connector_mtype(self) -> str | None:
        """Returns the main type of the edge's connector.
        If the edge has no connector (i.e. it's an atom), then None is
        returned.
        """
        ct = self.connector_type()
        if ct:
            return ct[0]
        else:
            return None

    def atom_with_type(self, atom_type: str) -> Atom | None:
        """Returns the first atom found in the edge that has the given
        'atom_type', or whose type starts with 'atom_type'.
        If no such atom is found, returns None.

        For example, given the edge (+/B a/Cn b/Cp) and the 'atom_type'
        c, this function returns:
        a/Cn
        If the 'atom_type' is 'Cp', the it will return:
        b/Cp
        """
        for item in self:
            atom: Atom | None = item.atom_with_type(atom_type)
            if atom:
                return atom
        return None

    def contains_atom_type(self, atom_type: str) -> bool:
        """Checks if the edge contains any atom with the given type.
        The edge is searched recursively, so the atom can appear at any depth.
        """
        return self.atom_with_type(atom_type) is not None

    def argroles(self) -> str:
        """Returns the argument roles string of the edge, if it exists.
        Otherwise returns empty string.

        Argument roles can be return for the entire edge that they apply to,
        which can be a relation (R) or a concept (C). For example:

        ((not/M is/P.sc) bob/C sad/C) has argument roles "sc",
        (of/B.ma city/C berlin/C) has argument roles "ma".

        Argument roles can also be returned for the connectors that define
        the outer edge, which can be of type predicate (P) or builder (B). For
        example:

        (not/M is/P.sc) has argument roles "sc",
        of/B.ma has argument roles "ma".
        """
        et = self.mtype()
        if et in {"R", "C"} and self[0].mtype() in {"B", "P"}:
            return self[0].argroles()  # type: ignore[no-any-return]
        if et not in {"B", "P"}:
            return ""
        return self[1].argroles()  # type: ignore[no-any-return]

    def has_argroles(self) -> bool:
        """Returns True if the edge has argroles, False otherwise."""
        return self.argroles() != ""

    def replace_argroles(self, argroles: str | None) -> Hyperedge:
        """Returns an edge with the argroles of the connector atom replaced
        with the provided string.
        Returns same edge if the atom does not contain a role part."""
        st = self.mtype()
        if st in {"C", "R"}:
            new_edge = [self[0].replace_argroles(argroles)]
            new_edge += self[1:]
            return Hyperedge(new_edge)
        elif st in {"P", "B"}:
            new_edge = [self[0], self[1].replace_argroles(argroles)]
            new_edge += list(self[2:])
            return Hyperedge(new_edge)
        return self

    def insert_argrole(self, argrole: str, pos: int) -> Hyperedge:
        """Returns an edge with the given argrole inserted at the specified
        position in the argroles of the connector atom.
        Same restrictions as in replace_argroles() apply."""
        st = self.mtype()
        if st in {"C", "R"}:
            new_edge = [self[0].insert_argrole(argrole, pos)]
            new_edge += self[1:]
            return Hyperedge(new_edge)
        elif st in {"P", "B"}:
            new_edge = [self[0], self[1].insert_argrole(argrole, pos)]
            new_edge += list(self[2:])
            return Hyperedge(new_edge)
        return self

    def insert_edge_with_argrole(
        self, edge: Hyperedge, argrole: str, pos: int
    ) -> Hyperedge:
        """Returns a new edge with the provided edge and its argroles inserted
        at the specified position."""
        new_edge = self.insert_argrole(argrole, pos)
        combined = (*tuple(new_edge[: pos + 1]), edge, *tuple(new_edge[pos + 1 :]))
        return Hyperedge(combined)

    def edges_with_argrole(self, argrole: str) -> list[Hyperedge]:
        """Returns the list of edges with the given argument role."""
        edges: list[Hyperedge] = []
        connector = self[0]

        argroles = connector.argroles()
        if len(argroles) > 0 and argroles[0] == "{":
            argroles = argroles[1:-1]
        argroles = argroles.replace(",", "")
        for pos, role in enumerate(argroles):
            if role == argrole and pos < len(self) - 1:
                edges.append(self[pos + 1])
        return edges

    def main_concepts(self) -> list[Hyperedge]:
        """Returns the list of main concepts in an concept edge.
        A main concept is a central concept in a built concept, e.g.:
        in ('s/Bp.am zimbabwe/Cp economy/Cn.s), economy/Cn.s is the main
        concept.

        If entity is not an edge, or its connector is not of type builder,
        or the builder does not contain concept role annotations, or no
        concept is annotated as the main one, then an empty list is
        returned.
        """
        if self[0].mtype() == "B":
            return self.edges_with_argrole("m")
        return []

    def replace_main_concept(self, new_main: Hyperedge) -> Hyperedge:
        """TODO: document and test"""
        if self.mtype() != "C":
            raise ValueError(
                "replace_main_concept requires type 'C', "
                f"got '{self.mtype()}': {self!s}"
            )
        if self[0].mtype() == "M":
            return hedge((self[0], new_main))
        elif self[0].mtype() == "B" and len(self) == 3:
            if self[0].argroles() == "ma":
                return hedge((self[0], new_main, self[2]))
            elif self[0].argroles() == "am":
                return hedge((self[0], self[1], new_main))
        raise ValueError(f"Cannot replace main concept in edge: {self!s}")

    def check_correctness(self) -> dict[Hyperedge, list[tuple[str, str]]]:
        output: dict[Hyperedge, list[tuple[str, str]]] = {}
        errors: list[tuple[str, str]] = []

        ct = self[0].mtype()
        # check if connector has valid type
        if ct not in {"P", "M", "B", "T", "J"}:
            errors.append(("conn-bad-type", f"connector has incorrect type: {ct}"))
        # check if modifier structure is correct
        if ct == "M":
            if len(self) != 2:
                errors.append(("mod-1-arg", "modifiers can only have one argument"))
        # check if builder structure is correct
        elif ct == "B":
            if len(self) != 3:
                errors.append(("build-2-args", "builders can only have two arguments"))
            for arg in self[1:]:
                at = arg.mtype()
                if at != "C":
                    e = f"builder argument {arg!s} has incorrect type: {at}"
                    errors.append(("build-arg-bad-type", e))
        # check if trigger structure is correct
        elif ct == "T":
            if len(self) != 2:
                errors.append(("trig-1-arg", "triggers can only have one arguments"))
            for arg in self[1:]:
                at = arg.mtype()
                if at not in {"C", "R"}:
                    e = f"trigger argument {arg!s} has incorrect type: {at}"
                    errors.append(("trig-bad-arg-type", e))
        # check if predicate structure is correct
        elif ct == "P":
            for arg in self[1:]:
                at = arg.mtype()
                if at not in {"C", "R", "S"}:
                    e = f"predicate argument {arg!s} has incorrect type: {at}"
                    errors.append(("pred-arg-bad-type", e))
        # check if conjunction structure is correct
        elif ct == "J" and len(self) < 3:
            errors.append(
                ("conj-2-args-min", "conjunctions must have at least two arguments")
            )

        # check argrole counts
        if ct in {"P", "B"}:
            try:
                ars = self.argroles()
                if len(ars) > 0:
                    if ct == "P":
                        for ar in ars:
                            if ar not in valid_p_argroles:
                                errors.append(
                                    (
                                        "pred-bad-arg-role",
                                        f"{ar} is not a valid argument role "
                                        "for connector of type P",
                                    )
                                )
                    elif ct == "B":
                        for ar in ars:
                            if ar not in valid_b_argroles:
                                errors.append(
                                    (
                                        "build-bad-arg-role",
                                        f"{ar} is not a valid argument role "
                                        "for connector of type B",
                                    )
                                )

                    if len(ars) != len(self) - 1:
                        errors.append(
                            (
                                "bad-num-argroles",
                                "number of argroles must match number of arguments",
                            )
                        )

                    ars_counts = Counter(ars)
                    if ars_counts["s"] > 1:
                        errors.append(
                            ("argrole-s-1-max", "argrole s can only be used once")
                        )
                    if ars_counts["o"] > 1:
                        errors.append(
                            ("argrole-o-1-max", "argrole o can only be used once")
                        )
                    if ars_counts["c"] > 1:
                        errors.append(
                            ("argrole-c-1-max", "argrole c can only be used once")
                        )
                    if ars_counts["i"] > 1:
                        errors.append(
                            ("argrole-i-1-max", "argrole i can only be used once")
                        )
                    if ars_counts["p"] > 1:
                        errors.append(
                            ("argrole-p-1-max", "argrole p can only be used once")
                        )
                    if ars_counts["a"] > 1:
                        errors.append(
                            ("argrole-a-1-max", "argrole a can only be used once")
                        )
                else:
                    errors.append(
                        (
                            "no-argroles",
                            "Connectors of type P or B must have argument roles",
                        )
                    )
            except RuntimeError:
                # malformed edges are detected elsewhere
                pass

        if len(errors) > 0:
            output[self] = errors

        for subedge in self:
            output.update(subedge.check_correctness())

        return output

    def normalized(self) -> Hyperedge:
        edge: Hyperedge = self
        conn = edge[0]
        ar = conn.argroles()
        if ar != "":
            if ar[0] == "{":
                ar = ar[1:-1]
            roles_edges_sorted = sorted(
                zip(ar, edge[1:], strict=False),
                key=lambda role_edge: argrole_order[role_edge[0]],
            )
            edge = hedge([conn, *[role_edge[1] for role_edge in roles_edges_sorted]])
        return hedge([subedge.normalized() for subedge in edge])

    def __add__(self, other: Hyperedge | tuple[Any, ...] | list[Any]) -> Hyperedge:
        if isinstance(other, (list, tuple)) and not isinstance(other, Hyperedge):
            return Hyperedge(self._edges + tuple(other))
        elif isinstance(other, Hyperedge) and other.atom:
            return Hyperedge((*self._edges, other))
        else:
            return Hyperedge(self._edges + tuple(other))

    def __str__(self) -> str:
        s = " ".join([str(edge) for edge in self._edges if edge])
        return f"({s})"

    def __repr__(self) -> str:
        return str(self)


@dataclass(frozen=True, init=False, eq=False, repr=False)
class Atom(Hyperedge):
    """Atomic hyperedge."""

    parens: bool

    def __init__(
        self,
        edge: tuple[str, ...] | Atom | Any,  # noqa: ANN401
        parens: bool = False,
        text: str | None = None,
    ) -> None:
        object.__setattr__(self, "_edges", tuple(edge))
        object.__setattr__(self, "parens", parens)
        object.__setattr__(self, "text", text)

    @property
    def atom(self) -> bool:
        """True if edge is an atom."""
        return True

    @property
    def not_atom(self) -> bool:
        """True if edge is not an atom."""
        return False

    def parts(self) -> list[str]:
        """Splits atom into its parts."""
        return self[0].split("/")  # type: ignore[no-any-return]

    def root(self) -> str:
        """Extracts the root of an atom
        (e.g. the root of hyperbase/C/1 is hyperbase)."""
        return self.parts()[0]

    def replace_atom_part(self, part_pos: int, part: str) -> Atom:
        """Build a new atom by replacing an atom part in a given atom."""
        parts = self.parts()
        parts[part_pos] = part
        atom = "/".join([part for part in parts if part])
        return Atom((atom,))

    def label(self) -> str:
        """Generate human-readable label from entity."""
        label = self.root()

        label = label.replace("%25", "%")
        label = label.replace("%2f", "/")
        label = label.replace("%20", " ")
        label = label.replace("%28", "(")
        label = label.replace("%29", ")")
        label = label.replace("%2e", ".")
        label = label.replace("%2a", "*")
        label = label.replace("%26", "&")
        label = label.replace("%40", "@")

        return label

    def inner_atom(self) -> Atom:
        """The inner atom inside of a modifier structure.

        For example, condider:
        (red/M shoes/C)
        The inner atom is:
        shoes/C
        Or, the more complex case:
        ((and/J slow/M steady/M) go/P)
        Yields:
        gp/P

        This method should not be used on structures that contain more than
        one inner atom, for example concepts constructed with builders or
        relations.

        The inner atom of an atom is itself.
        """
        return self

    def connector_atom(self) -> Atom | None:
        """The inner atom of the connector.

        For example, condider:
        (does/M (not/M like/P.so) john/C chess/C)
        The connector atom is:
        like/P.so

        The connector atom of an atom is None.
        """
        return None

    def atoms(self) -> set[Atom]:
        """Returns the set of atoms contained in the edge.

        For example, consider the edge:
        (the/Md (of/Br mayor/Cc (the/Md city/Cs)))
        in this case, edge.atoms() returns:
        [the/Md, of/Br, mayor/Cc, city/Cs]
        """
        return {self}

    def all_atoms(self) -> list[Atom]:
        """Returns a list of all the atoms contained in the edge. Unlike
        atoms(), which does not return repeated atoms, all_atoms() does
        return repeated atoms if they are different objects.

        For example, consider the edge:
        (the/Md (of/Br mayor/Cc (the/Md city/Cs)))
        in this case, edge.all_atoms() returns:
        [the/Md, of/Br, mayor/Cc, the/Md, city/Cs]
        """
        return [self]

    def size(self) -> int:
        """The size of an edge is its total number of atoms, at all depths."""
        return 1

    def depth(self) -> int:
        """Returns maximal depth of edge, an atom has depth 0."""
        return 0

    def roots(self) -> Atom:
        """Returns edge with root-only atoms."""
        return Atom((self.root(),))

    def contains(self, needle: str) -> bool:
        """Checks recursively if 'needle' is contained in edge."""
        return self[0] == needle

    def subedges(self) -> set[Hyperedge]:
        """Returns all the subedges contained in the edge, including atoms
        and itself.
        """
        return {self}

    def role(self) -> list[str]:
        """Returns the role of this atom as a list of the subrole strings.

        The role of an atom is its second part, right after the root.
        A dot notation is used to separate the subroles. For example,
        the role of hyperbase/Cp.s/1 is:

            Cp.s

        For this case, this function returns:

            ['Cp', 's']

        If the atom only has a root, it is assumed to be a conjunction.
        In this case, this function returns the role with just the
        generic conjunction type:

            ['J'].
        """
        parts: list[str] = self[0].split("/")
        if len(parts) < 2:
            return list("J")
        else:
            return parts[1].split(".")

    def simplify(
        self, subtypes: bool = False, argroles: bool = False, namespaces: bool = True
    ) -> Atom:
        """Returns a simplified version of the atom, for example removing
        subtypes, subroles or namespaces.

        Keyword arguments:
        subtypes -- include subtype (default: False).
        argroles --include argroles (default: False).
        namespaces -- include namespaces (default: True).
        """
        parts = self.parts()

        if len(parts) < 2:
            return self

        role = self.type() if subtypes else self.mtype()

        if argroles:
            ar = self.argroles()
            if len(ar) > 0:
                role = f"{role}.{ar}"

        parts[1] = role

        if len(parts) > 2 and not namespaces:
            parts = parts[:2]

        atom_str = "/".join(parts)
        return Atom((atom_str,))

    def type(self) -> str:
        """Returns the type of the atom.

        The type of an atom is its first subrole. For example, the
        type of hyperbase/Cp.s/1 is 'Cp'.

        If the atom only has a root, it is assumed to be a conjunction.
        In this case, this function returns the generic conjunction type: 'J'.
        """
        return self.role()[0]

    def connector_type(self) -> str | None:
        """Returns the type of the edge's connector.
        If the edge has no connector (i.e. it's an atom), then None is
        returned.
        """
        return None

    def atom_with_type(self, atom_type: str) -> Atom | None:
        """Returns the first atom found in the edge that has the given
        'atom_type', or whose type starts with 'atom_type'.
        If no such atom is found, returns None.

        For example, given the edge (+/B a/Cn b/Bp) and the 'atom_type'
        C, this function returns:
        a/Cn
        If the 'atom_type' is 'Cp', the it will return:
        b/Cp
        """
        n = len(atom_type)
        et = self.type()
        if len(et) >= n and et[:n] == atom_type:
            return self
        else:
            return None

    def argroles(self) -> str:
        """Returns the argument roles string of the edge, if it exists.
        Otherwise returns empty string.

        Argument roles can be return for the entire edge that they apply to,
        which can be a relation (R) or a concept (C). For example:

        ((not/M is/P.sc) bob/C sad/C) has argument roles "sc",
        (of/B.ma city/C berlin/C) has argument roles "ma".

        Argument roles can also be returned for the connectors that define
        the outer edge, which can be of type predicate (P) or builder (B). For
        example:

        (not/M is/P.sc) has argument roles "sc",
        of/B.ma has argument roles "ma".
        """
        et = self.mtype()
        if et not in {"B", "P"}:
            return ""
        role = self.role()
        if len(role) < 2:
            return ""
        return role[1]

    def replace_argroles(self, argroles: str | None) -> Atom:
        """Returns an atom with the argroles replaced with the provided string."""
        if argroles is None or argroles == "":
            return self.remove_argroles()
        parts = self[0].split("/")
        if len(parts) < 2:
            return self
        role = parts[1].split(".")
        if len(role) < 2:
            role.append(argroles)
        else:
            role[1] = argroles
        parts = [parts[0], ".".join(role), *parts[2:]]
        return Atom(("/".join(parts),))

    def remove_argroles(self) -> Atom:
        """Returns an atom with the argroles removed."""
        parts = self[0].split("/")
        if len(parts) < 2:
            return self
        role = parts[1].split(".")
        parts[1] = role[0]
        return Atom(("/".join(parts),))

    def insert_argrole(self, argrole: str, pos: int) -> Atom:
        """Returns an atom with the given argrole inserted at the specified
        position. Same restrictions as in replace_argroles() apply."""
        argroles = self.argroles()
        argroles = argroles[:pos] + argrole + argroles[pos:]
        return self.replace_argroles(argroles)

    def edges_with_argrole(self, argrole: str) -> list[Hyperedge]:
        """Returns the list of edges with the given argument role"""
        return []

    def main_concepts(self) -> list[Hyperedge]:
        """Returns the list of main concepts in an concept edge.
        A main concept is a central concept in a built concept, e.g.:
        in ('s/Bp.am zimbabwe/Mp economy/Cn.s), economy/Cn.s is the main
        concept.

        If entity is not an edge, or its connector is not of type builder,
        or the builder does not contain concept role annotations, or no
        concept is annotated as the main one, then an empty list is
        returned.
        """
        return []

    def replace_main_concept(self, new_main: Hyperedge) -> Hyperedge:
        """TODO: document and test"""
        if self.mtype() != "C":
            raise ValueError(
                "replace_main_concept requires type 'C', "
                f"got '{self.mtype()}': {self!s}"
            )

        return new_main

    def check_correctness(self) -> dict[Hyperedge, list[tuple[str, str]]]:
        output: dict[Hyperedge, list[tuple[str, str]]] = {}
        errors: list[tuple[str, str]] = []

        at = self.mtype()
        if at not in {"C", "P", "M", "B", "T", "J"}:
            errors.append(("bad-atom-type", f"{at} is not a valid atom type"))

        if len(errors) > 0:
            output[self] = errors

        return output

    def normalized(self) -> Atom:
        if self.mtype() in {"B", "P"}:
            ar = self.argroles()
            if len(ar) > 0:
                if ar[0] == "{":
                    ar = ar[1:-1]
                    unordered = True
                else:
                    unordered = False
                ar = "".join(sorted(ar, key=lambda argrole: argrole_order[argrole]))
                if unordered:
                    ar = f"{{{ar}}}"
                return self.replace_argroles(ar)
        return self

    def __add__(self, other: Hyperedge | tuple[Any, ...] | list[Any]) -> Hyperedge:
        if isinstance(other, (list, tuple)) and not isinstance(other, Hyperedge):
            return Hyperedge((self, *tuple(other)))
        elif isinstance(other, Hyperedge) and other.atom:
            return Hyperedge((self, other))
        else:
            return Hyperedge((self, *tuple(other)))

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        atom_str = str(self._edges[0])
        if self.parens:
            return f"({atom_str})"
        else:
            return atom_str


class UniqueAtom(Atom):
    atom_obj: Atom

    def __init__(self, atom: Atom) -> None:
        super().__init__(atom._edges)
        object.__setattr__(self, "atom_obj", atom)

    def __hash__(self) -> int:
        return id(self.atom_obj)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UniqueAtom) and id(self.atom_obj) == id(other.atom_obj)


def unique(edge: Hyperedge) -> Hyperedge:
    if edge.atom:
        if isinstance(edge, UniqueAtom):
            return edge
        else:
            return UniqueAtom(edge)  # type: ignore[arg-type]
    else:
        return hedge([unique(subedge) for subedge in edge])


def non_unique(edge: Hyperedge) -> Hyperedge:
    if edge.atom:
        if isinstance(edge, UniqueAtom):
            return edge.atom_obj
        else:
            return edge
    else:
        return hedge([non_unique(subedge) for subedge in edge])
