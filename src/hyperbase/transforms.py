from __future__ import annotations

from typing import cast

import hyperbase.constants as const
from hyperbase.builders import hedge
from hyperbase.constants import EdgeType
from hyperbase.hyperedge import Atom, Hyperedge, UniqueAtom


def normalise(edge: Hyperedge) -> Hyperedge:
    """Return a normalised copy of the edge (argument roles sorted)."""
    if edge.atom:
        atom = cast(Atom, edge)
        if atom.mtype() in {EdgeType.BUILDER, EdgeType.PREDICATE}:
            ar = atom.argroles()
            if len(ar) > 0:
                if ar[0] == "{":
                    ar = ar[1:-1]
                    unordered = True
                else:
                    unordered = False
                if "[" not in ar:
                    ar = "".join(
                        sorted(ar, key=lambda argrole: const.argrole_order[argrole])
                    )
                if unordered:
                    ar = f"{{{ar}}}"
                return replace_argroles(atom, ar)  # type: ignore[return-value]
        return atom
    else:
        conn = edge[0]
        ar = conn.argroles()
        if ar != "":
            if ar[0] == "{":
                ar = ar[1:-1]
            roles_edges_sorted = sorted(
                zip(ar, edge[1:], strict=False),
                key=lambda role_edge: const.argrole_order[role_edge[0]],
            )
            edge = hedge([conn, *[role_edge[1] for role_edge in roles_edges_sorted]])
        return hedge([normalise(subedge) for subedge in edge])


def simplify(
    edge: Hyperedge, subtypes: bool = False, namespaces: bool = False
) -> Hyperedge:
    """Return a simplified copy of the edge."""
    if edge.atom:
        atom = cast(Atom, edge)
        parts = atom.parts()
        if len(parts) < 2:
            return atom
        role = atom.type() if subtypes else atom.mtype()
        ar = atom.argroles()
        if len(ar) > 0:
            role = f"{role}.{ar}"
        parts[1] = role
        if len(parts) > 2 and not namespaces:
            parts = parts[:2]
        atom_str = "/".join(parts)
        return Atom(atom_str)
    else:
        return hedge(
            [
                simplify(subedge, subtypes=subtypes, namespaces=namespaces)
                for subedge in edge
            ]
        )


def replace_atom(
    edge: Hyperedge, old: Atom, new: Hyperedge, unique: bool = False
) -> Hyperedge:
    """Return a copy with every instance of *old* replaced by *new*."""
    if edge.atom:
        if unique:
            if UniqueAtom(edge) == UniqueAtom(old):  # type: ignore[arg-type]
                return new
        else:
            if edge == old:
                return new
        return edge
    else:
        return Hyperedge(
            tuple(replace_atom(item, old, new, unique=unique) for item in edge)
        )


def replace_argroles(edge: Hyperedge, argroles: str | None) -> Hyperedge:
    """Return a copy with the connector's argument roles replaced."""
    if edge.atom:
        atom = cast(Atom, edge)
        if argroles is None or argroles == "":
            return _remove_argroles(atom)
        parts = atom.atom_str.split("/")
        if len(parts) < 2:
            return atom
        role = parts[1].split(".")
        if len(role) < 2:
            role.append(argroles)
        else:
            role[1] = argroles
        parts = [parts[0], ".".join(role), *parts[2:]]
        return Atom("/".join(parts))
    else:
        st = edge.mtype()
        if st in {EdgeType.CONCEPT, EdgeType.RELATION}:
            new_edge = [replace_argroles(edge[0], argroles)]
            new_edge += edge[1:]
            return Hyperedge(new_edge)
        elif st in {EdgeType.PREDICATE, EdgeType.BUILDER}:
            new_edge = [edge[0], replace_argroles(edge[1], argroles)]
            new_edge += list(edge[2:])
            return Hyperedge(new_edge)
        return edge


def _remove_argroles(atom: Atom) -> Atom:
    parts = atom.atom_str.split("/")
    if len(parts) < 2:
        return atom
    role = parts[1].split(".")
    parts[1] = role[0]
    return Atom("/".join(parts))


def insert_argrole(edge: Hyperedge, argrole: str, pos: int) -> Hyperedge:
    """Return a copy with *argrole* inserted at *pos* in the connector's roles."""
    if edge.atom:
        argroles = edge.argroles()
        argroles = argroles[:pos] + argrole + argroles[pos:]
        return replace_argroles(edge, argroles)
    else:
        st = edge.mtype()
        if st in {EdgeType.CONCEPT, EdgeType.RELATION}:
            new_edge = [insert_argrole(edge[0], argrole, pos)]
            new_edge += edge[1:]
            return Hyperedge(new_edge)
        elif st in {EdgeType.PREDICATE, EdgeType.BUILDER}:
            new_edge = [edge[0], insert_argrole(edge[1], argrole, pos)]
            new_edge += list(edge[2:])
            return Hyperedge(new_edge)
        return edge


def add_argument(
    edge: Hyperedge, arg: Hyperedge, argrole: str, pos: int | None = None
) -> Hyperedge:
    """Return a copy with *arg* and its *argrole* inserted at *pos*."""
    if pos is None:
        pos = len(edge) - 1
    new_edge = insert_argrole(edge, argrole, pos)
    combined = (*tuple(new_edge[: pos + 1]), arg, *tuple(new_edge[pos + 1 :]))
    return Hyperedge(combined)
