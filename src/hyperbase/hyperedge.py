from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any, overload

from hyperbase.constants import EdgeType


@dataclass(frozen=True, init=False, eq=False, repr=False)
class Hyperedge:
    """Non-atomic hyperedge."""

    _edges: tuple[Hyperedge, ...]
    text: str | None
    _cache: dict[str, Any] = field(
        default_factory=dict, repr=False, compare=False, hash=False
    )

    def __init__(self, edges: Iterable[Hyperedge], text: str | None = None) -> None:
        object.__setattr__(self, "_edges", tuple(edges))
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "_cache", {})

    def __iter__(self) -> Iterator[Hyperedge]:
        return iter(self._edges)

    @overload
    def __getitem__(self, key: int) -> Hyperedge: ...
    @overload
    def __getitem__(self, key: slice) -> tuple[Hyperedge, ...]: ...

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
        """Match this edge against a pattern. See ``match_pattern`` for details."""
        from hyperbase.patterns import match_pattern

        return match_pattern(self, pattern)

    def label(self) -> str:
        """Generate human-readable label for edge."""
        conn_atom = self.connector_atom()
        if len(self) == 2:
            edge = self
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
        if "size" not in self._cache:
            self._cache["size"] = sum(edge.size() for edge in self)
        return self._cache["size"]

    def depth(self) -> int:
        """Returns maximal depth of edge, an atom has depth 0."""
        if "depth" not in self._cache:
            max_d = 0
            for item in self:
                d = item.depth()
                if d > max_d:
                    max_d = d
            self._cache["depth"] = max_d + 1
        return self._cache["depth"]

    def contains(self, needle: Hyperedge) -> bool:
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

    def replace_atom(
        self, old: Atom, new: Hyperedge, unique: bool = False
    ) -> Hyperedge:
        """Returns edge built by replacing every instance of 'old' in
        this edge with 'new'.

        Keyword argument:
        unique -- match only the exact same instance of the atom, i.e.
        UniqueAtom(self) == UniqueAtom(old) (default: False)
        """
        from hyperbase.transforms import replace_atom

        return replace_atom(self, old, new, unique=unique)

    def simplify(self, subtypes: bool = False, namespaces: bool = False) -> Hyperedge:
        """Returns a version of the edge with simplified atoms.

        Keyword arguments:
        subtypes -- include subtypes (default: True).
        namespaces -- include namespaces (default: True).
        """
        from hyperbase.transforms import simplify

        return simplify(self, subtypes=subtypes, namespaces=namespaces)

    def type(self) -> str:
        """Returns the type of this edge as a string.
        Type inference is performed.
        """
        if "type" in self._cache:
            return self._cache["type"]
        ptype = self[0].type()
        if ptype[0] == EdgeType.PREDICATE:
            outter_type = EdgeType.RELATION
        elif ptype[0] == EdgeType.MODIFIER:
            if len(self) < 2:
                raise RuntimeError(
                    f"Edge is malformed, type cannot be determined: {self!s}"
                )
            result = self[1].type()
            self._cache["type"] = result
            return result
        elif ptype[0] == EdgeType.TRIGGER:
            outter_type = EdgeType.SPECIFIER
        elif ptype[0] == EdgeType.BUILDER:
            outter_type = EdgeType.CONCEPT
        elif ptype[0] == EdgeType.CONJUNCTION:
            if len(self) < 2:
                raise RuntimeError(
                    f"Edge is malformed, type cannot be determined: {self!s}"
                )
            result = self[1].mtype()
            self._cache["type"] = result
            return result
        else:
            raise RuntimeError(
                f"Edge is malformed, type cannot be determined: {self!s}"
            )

        result = outter_type + ptype[1:]
        self._cache["type"] = result
        return result

    def connector_type(self) -> str | None:
        """Returns the type of the edge's connector.
        If the edge has no connector (i.e. it's an atom), then None is
        returned.
        """
        if "connector_type" not in self._cache:
            self._cache["connector_type"] = self[0].type()
        return self._cache["connector_type"]

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
        if "argroles" in self._cache:
            return self._cache["argroles"]
        et = self.mtype()
        if et in {EdgeType.RELATION, EdgeType.CONCEPT} and self[0].mtype() in {
            EdgeType.BUILDER,
            EdgeType.PREDICATE,
        }:
            result = self[0].argroles()
        elif et not in {EdgeType.BUILDER, EdgeType.PREDICATE}:
            result = ""
        else:
            result = self[1].argroles()
        self._cache["argroles"] = result
        return result

    def replace_argroles(self, argroles: str | None) -> Hyperedge:
        """Returns an edge with the argroles of the connector atom replaced
        with the provided string.
        Returns same edge if the atom does not contain a role part."""
        from hyperbase.transforms import replace_argroles

        return replace_argroles(self, argroles)

    def _insert_argrole(self, argrole: str, pos: int) -> Hyperedge:
        """Returns an edge with the given argrole inserted at the specified
        position in the argroles of the connector atom.
        Same restrictions as in replace_argroles() apply."""
        from hyperbase.transforms import insert_argrole

        return insert_argrole(self, argrole, pos)

    def add_argument(
        self, edge: Hyperedge, argrole: str, pos: int | None = None
    ) -> Hyperedge:
        """Returns a new edge with the provided edge and its argroles inserted
        at the specified position. If pos is not provided, the argument is
        appended at the end."""
        from hyperbase.transforms import add_argument

        return add_argument(self, edge, argrole, pos)

    def arguments_with_role(self, argrole: str) -> list[Hyperedge]:
        """Returns the list of edges with the given argument role."""
        edges: list[Hyperedge] = []
        connector = self[0]

        argroles = connector.argroles()
        if len(argroles) > 0 and argroles[0] == "{":
            argroles = argroles[1:-1]
        argroles = argroles.replace(",", "").replace("[", "").replace("]", "")
        for pos, role in enumerate(argroles):
            if role == argrole and pos < len(self) - 1:
                edges.append(self[pos + 1])
        return edges

    def check_correctness(self) -> dict[Hyperedge, list[tuple[str, str]]]:
        from hyperbase.correctness import check_correctness

        return check_correctness(self)

    def normalise(self) -> Hyperedge:
        from hyperbase.transforms import normalise

        return normalise(self)

    ############
    # patterns #
    ############
    def is_wildcard(self) -> bool:
        from hyperbase.patterns.checks import is_wildcard

        return is_wildcard(self)

    def is_pattern(self) -> bool:
        from hyperbase.patterns.checks import is_pattern

        return is_pattern(self)

    def is_fun_pattern(self) -> bool:
        from hyperbase.patterns.checks import is_fun_pattern

        return is_fun_pattern(self)

    #############
    # variables #
    #############
    def is_variable(self) -> bool:
        from hyperbase.patterns.checks import is_variable

        return is_variable(self)

    def contains_variable(self) -> bool:
        from hyperbase.patterns.checks import contains_variable

        return contains_variable(self)

    def variable_name(self) -> str:
        from hyperbase.patterns.checks import variable_name

        return variable_name(self)

    def __str__(self) -> str:
        s = " ".join([str(edge) for edge in self._edges if edge])
        return f"({s})"

    def __repr__(self) -> str:
        return str(self)


@dataclass(frozen=True, init=False, eq=False, repr=False)
class Atom(Hyperedge):
    """Atomic hyperedge."""

    atom_str: str
    parens: bool

    def __init__(
        self,
        atom_str: str,
        parens: bool = False,
        text: str | None = None,
    ) -> None:
        object.__setattr__(self, "atom_str", atom_str)
        object.__setattr__(self, "parens", parens)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "_edges", ())
        object.__setattr__(self, "_cache", {})

    def __hash__(self) -> int:
        return hash(self.atom_str)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Atom):
            return self.atom_str == other.atom_str
        return False

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
        return self.atom_str.split("/")

    def root(self) -> str:
        """Extracts the root of an atom
        (e.g. the root of hyperbase/C/1 is hyperbase)."""
        return self.parts()[0]

    def replace_atom_part(self, part_pos: int, part: str) -> Atom:
        """Build a new atom by replacing an atom part in a given atom."""
        parts = self.parts()
        parts[part_pos] = part
        atom_str = "/".join([part for part in parts if part])
        return Atom(atom_str)

    def label(self) -> str:
        """Generate human-readable label from entity."""
        from hyperbase.constants import atom_decode

        return atom_decode(self.root())

    def inner_atom(self) -> Atom:
        return self

    def connector_atom(self) -> Atom | None:
        return None

    def atoms(self) -> set[Atom]:
        return {self}

    def all_atoms(self) -> list[Atom]:
        return [self]

    def size(self) -> int:
        return 1

    def depth(self) -> int:
        return 0

    def roots(self) -> Atom:
        """Returns edge with root-only atoms."""
        return Atom(self.root())

    def contains(self, needle: Hyperedge) -> bool:
        return self == needle

    def subedges(self) -> set[Hyperedge]:
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
        if "role" in self._cache:
            return self._cache["role"]
        parts: list[str] = self.atom_str.split("/")
        result = list("J") if len(parts) < 2 else parts[1].split(".")
        self._cache["role"] = result
        return result

    def type(self) -> str:
        """Returns the type of the atom (first subrole, default ``'J'``)."""
        if "type" in self._cache:
            return self._cache["type"]
        result = self.role()[0]
        self._cache["type"] = result
        return result

    def connector_type(self) -> str | None:
        return None

    def atom_with_type(self, atom_type: str) -> Atom | None:
        et = self.type()
        n = len(atom_type)
        if len(et) >= n and et[:n] == atom_type:
            return self
        else:
            return None

    def argroles(self) -> str:
        if "argroles" in self._cache:
            return self._cache["argroles"]
        et = self.mtype()
        if et not in {EdgeType.BUILDER, EdgeType.PREDICATE}:
            result = ""
        else:
            role = self.role()
            result = role[1] if len(role) >= 2 else ""
        self._cache["argroles"] = result
        return result

    def remove_argroles(self) -> Atom:
        from hyperbase.transforms import replace_argroles

        return replace_argroles(self, None)  # type: ignore[return-value]

    def arguments_with_role(self, argrole: str) -> list[Hyperedge]:
        return []

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if self.parens:
            return f"({self.atom_str})"
        else:
            return self.atom_str


class UniqueAtom(Atom):
    atom_obj: Atom

    def __init__(self, atom: Atom) -> None:
        super().__init__(atom.atom_str)
        object.__setattr__(self, "atom_obj", atom)

    def __hash__(self) -> int:
        return id(self.atom_obj)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UniqueAtom) and id(self.atom_obj) == id(other.atom_obj)


def unique(edge: Hyperedge) -> Hyperedge:
    from hyperbase.builders import hedge

    if edge.atom:
        if isinstance(edge, UniqueAtom):
            return edge
        else:
            return UniqueAtom(edge)  # type: ignore[arg-type]
    else:
        return hedge([unique(subedge) for subedge in edge])


def non_unique(edge: Hyperedge) -> Hyperedge:
    from hyperbase.builders import hedge

    if edge.atom:
        if isinstance(edge, UniqueAtom):
            return edge.atom_obj
        else:
            return edge
    else:
        return hedge([non_unique(subedge) for subedge in edge])
