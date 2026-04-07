from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import hyperbase.constants as const
from hyperbase.constants import EdgeType

if TYPE_CHECKING:
    from hyperbase.hyperedge import Atom, Hyperedge


def check_correctness(edge: Hyperedge) -> dict[Hyperedge, list[tuple[str, str]]]:
    """Check correctness of a hyperedge, returning errors keyed by subedge."""
    if edge.atom:
        return _check_atom(edge)  # type: ignore[arg-type]
    return _check_edge(edge)


def _check_atom(atom: Atom) -> dict[Hyperedge, list[tuple[str, str]]]:
    output: dict[Hyperedge, list[tuple[str, str]]] = {}
    errors: list[tuple[str, str]] = []

    at = atom.mtype()
    if at not in {
        EdgeType.CONCEPT,
        EdgeType.PREDICATE,
        EdgeType.MODIFIER,
        EdgeType.BUILDER,
        EdgeType.TRIGGER,
        EdgeType.CONJUNCTION,
    }:
        errors.append(("bad-atom-type", f"{at} is not a valid atom type"))

    if len(errors) > 0:
        output[atom] = errors

    return output


def _check_edge(edge: Hyperedge) -> dict[Hyperedge, list[tuple[str, str]]]:
    output: dict[Hyperedge, list[tuple[str, str]]] = {}
    errors: list[tuple[str, str]] = []

    ct = edge[0].mtype()
    # check if connector has valid type
    if ct not in {
        EdgeType.PREDICATE,
        EdgeType.MODIFIER,
        EdgeType.BUILDER,
        EdgeType.TRIGGER,
        EdgeType.CONJUNCTION,
    }:
        errors.append(("conn-bad-type", f"connector has incorrect type: {ct}"))
    # check if modifier structure is correct
    if ct == EdgeType.MODIFIER:
        if len(edge) != 2:
            errors.append(("mod-1-arg", "modifiers can only have one argument"))
    # check if builder structure is correct
    elif ct == EdgeType.BUILDER:
        if len(edge) != 3:
            errors.append(("build-2-args", "builders can only have two arguments"))
        for arg in edge[1:]:
            at = arg.mtype()
            if at != EdgeType.CONCEPT:
                e = f"builder argument {arg!s} has incorrect type: {at}"
                errors.append(("build-arg-bad-type", e))
    # check if trigger structure is correct
    elif ct == EdgeType.TRIGGER:
        if len(edge) != 2:
            errors.append(("trig-1-arg", "triggers can only have one arguments"))
        for arg in edge[1:]:
            at = arg.mtype()
            if at not in {EdgeType.CONCEPT, EdgeType.RELATION}:
                e = f"trigger argument {arg!s} has incorrect type: {at}"
                errors.append(("trig-bad-arg-type", e))
    # check if predicate structure is correct
    elif ct == EdgeType.PREDICATE:
        for arg in edge[1:]:
            at = arg.mtype()
            if at not in {EdgeType.CONCEPT, EdgeType.RELATION, EdgeType.SPECIFIER}:
                e = f"predicate argument {arg!s} has incorrect type: {at}"
                errors.append(("pred-arg-bad-type", e))
    # check if conjunction structure is correct
    elif ct == EdgeType.CONJUNCTION and len(edge) < 3:
        errors.append(
            ("conj-2-args-min", "conjunctions must have at least two arguments")
        )

    # check argrole counts
    if ct in {EdgeType.PREDICATE, EdgeType.BUILDER}:
        try:
            ars = edge.argroles()
            if len(ars) > 0:
                if ct == EdgeType.PREDICATE:
                    for ar in ars:
                        if ar not in const.valid_p_argroles:
                            errors.append(
                                (
                                    "pred-bad-arg-role",
                                    f"{ar} is not a valid argument role "
                                    "for connector of type P",
                                )
                            )
                elif ct == EdgeType.BUILDER:
                    for ar in ars:
                        if ar not in const.valid_b_argroles:
                            errors.append(
                                (
                                    "build-bad-arg-role",
                                    f"{ar} is not a valid argument role "
                                    "for connector of type B",
                                )
                            )

                if len(ars) != len(edge) - 1:
                    errors.append(
                        (
                            "bad-num-argroles",
                            "number of argroles must match number of arguments",
                        )
                    )

                ars_counts = Counter(ars)
                for role in "socipam":
                    if ars_counts[role] > 1:
                        errors.append(
                            (
                                f"argrole-{role}-1-max",
                                f"argrole {role} can only be used once",
                            )
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
        output[edge] = errors

    for subedge in edge:
        output.update(check_correctness(subedge))

    return output
