from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import hyperbase.constants as const

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
    if at not in {"C", "P", "M", "B", "T", "J"}:
        errors.append(("bad-atom-type", f"{at} is not a valid atom type"))

    if len(errors) > 0:
        output[atom] = errors

    return output


def _check_edge(edge: Hyperedge) -> dict[Hyperedge, list[tuple[str, str]]]:
    output: dict[Hyperedge, list[tuple[str, str]]] = {}
    errors: list[tuple[str, str]] = []

    ct = edge[0].mtype()
    # check if connector has valid type
    if ct not in {"P", "M", "B", "T", "J"}:
        errors.append(("conn-bad-type", f"connector has incorrect type: {ct}"))
    # check if modifier structure is correct
    if ct == "M":
        if len(edge) != 2:
            errors.append(("mod-1-arg", "modifiers can only have one argument"))
    # check if builder structure is correct
    elif ct == "B":
        if len(edge) != 3:
            errors.append(("build-2-args", "builders can only have two arguments"))
        for arg in edge[1:]:
            at = arg.mtype()
            if at != "C":
                e = f"builder argument {arg!s} has incorrect type: {at}"
                errors.append(("build-arg-bad-type", e))
    # check if trigger structure is correct
    elif ct == "T":
        if len(edge) != 2:
            errors.append(("trig-1-arg", "triggers can only have one arguments"))
        for arg in edge[1:]:
            at = arg.mtype()
            if at not in {"C", "R"}:
                e = f"trigger argument {arg!s} has incorrect type: {at}"
                errors.append(("trig-bad-arg-type", e))
    # check if predicate structure is correct
    elif ct == "P":
        for arg in edge[1:]:
            at = arg.mtype()
            if at not in {"C", "R", "S"}:
                e = f"predicate argument {arg!s} has incorrect type: {at}"
                errors.append(("pred-arg-bad-type", e))
    # check if conjunction structure is correct
    elif ct == "J" and len(edge) < 3:
        errors.append(
            ("conj-2-args-min", "conjunctions must have at least two arguments")
        )

    # check argrole counts
    if ct in {"P", "B"}:
        try:
            ars = edge.argroles()
            if len(ars) > 0:
                if ct == "P":
                    for ar in ars:
                        if ar not in const.valid_p_argroles:
                            errors.append(
                                (
                                    "pred-bad-arg-role",
                                    f"{ar} is not a valid argument role "
                                    "for connector of type P",
                                )
                            )
                elif ct == "B":
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
        output[edge] = errors

    for subedge in edge:
        output.update(check_correctness(subedge))

    return output
