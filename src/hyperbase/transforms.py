from __future__ import annotations

from collections.abc import Iterator
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
        return Atom(atom_str, tok_pos=atom.tok_pos, text_span=atom.text_span)
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
        return Atom("/".join(parts), tok_pos=atom.tok_pos, text_span=atom.text_span)
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
    return Atom("/".join(parts), tok_pos=atom.tok_pos, text_span=atom.text_span)


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


def tok_pos_tree(edge: Hyperedge) -> Hyperedge:
    """Build a tok_pos parallel-tree Hyperedge mirroring *edge*'s structure.

    Each atom in the result holds the source token index of the corresponding
    atom in *edge* (``tok_pos`` if set, else ``-1`` for synthetic atoms).
    Suitable for serialisation as the ``tok_pos`` field of a parse-result
    JSONL row.
    """
    if edge.atom:
        atom = cast(Atom, edge)
        pos = atom.tok_pos if atom.tok_pos is not None else -1
        return Atom(str(pos))
    return Hyperedge(tuple(tok_pos_tree(c) for c in edge))


#############
# transform #
#############


def transform(
    edge: Hyperedge,
    origin_pattern: Hyperedge | str | list | tuple,
    target_pattern: Hyperedge | str | list | tuple,
    recursive: bool = True,
) -> Hyperedge:
    """Pattern-driven rewrite of *edge*.

    If ``origin_pattern`` matches *edge*, the edge is rewritten according to
    ``target_pattern`` using the variable bindings extracted from the match.
    If it does not match, the edge is returned unchanged.

    With ``{}`` argroles in the target, un-consumed arguments and argroles
    from the original edge at the matched (top) level are preserved alongside
    the target's. Without ``{}`` only what appears in the target is kept.

    Patterns must contain only named variables; anonymous wildcards
    (``*``, ``.``, ``(*)``, ``...``) and functional patterns (``var``, ``any``,
    ``atoms``, ``lemma``) raise ``ValueError``. The target's variables must be
    a subset of the origin's variables.

    By default the rewrite is applied recursively (depth-first, once per
    level). Pass ``recursive=False`` for a shallow rewrite.
    """
    origin = hedge(origin_pattern)
    target = hedge(target_pattern)
    _validate_transform_patterns(origin, target)
    return _transform_impl(edge, origin, target, recursive)


def _transform_impl(
    edge: Hyperedge,
    origin: Hyperedge,
    target: Hyperedge,
    recursive: bool,
) -> Hyperedge:
    from hyperbase.patterns import match_pattern

    if recursive and edge.not_atom:
        edge = Hyperedge(tuple(_transform_impl(c, origin, target, True) for c in edge))

    matches = match_pattern(edge, origin)
    if matches:
        edge = _instantiate(target, origin, edge, matches[0], top=True)
    return edge


def _validate_transform_patterns(origin: Hyperedge, target: Hyperedge) -> None:
    from hyperbase.patterns.checks import is_variable, is_wildcard

    for label, pattern in (("origin_pattern", origin), ("target_pattern", target)):
        if _contains_fun_pattern(pattern):
            raise ValueError(
                f"Functional patterns are not supported in {label}: {pattern}"
            )
        for atom in _walk_atoms(pattern):
            if is_wildcard(atom) and not is_variable(atom):
                raise ValueError(
                    f"Anonymous wildcard '{atom}' not allowed in {label}; "
                    f"use a named variable"
                )

    origin_vars = _collect_var_names(origin)
    target_vars = _collect_var_names(target)
    extra = target_vars - origin_vars
    if extra:
        raise ValueError(
            f"target_pattern uses variables not in origin_pattern: {sorted(extra)}"
        )


def _walk_atoms(edge: Hyperedge) -> Iterator[Atom]:
    if edge.atom:
        yield cast(Atom, edge)
    else:
        for child in edge:
            yield from _walk_atoms(child)


def _contains_fun_pattern(edge: Hyperedge) -> bool:
    from hyperbase.patterns.checks import is_fun_pattern

    if edge.atom:
        return False
    if is_fun_pattern(edge):
        return True
    return any(_contains_fun_pattern(c) for c in edge)


def _collect_var_names(pattern: Hyperedge) -> set[str]:
    from hyperbase.patterns.checks import is_variable, variable_name

    names: set[str] = set()
    for atom in _walk_atoms(pattern):
        if is_variable(atom):
            names.add(variable_name(atom))
    return names


def _find_var_atom(pattern: Hyperedge, name: str) -> Atom | None:
    from hyperbase.patterns.checks import is_variable, variable_name

    for atom in _walk_atoms(pattern):
        if is_variable(atom) and variable_name(atom) == name:
            return atom
    return None


def _strip_braces(s: str) -> str:
    if len(s) >= 2 and s[0] == "{" and s[-1] == "}":
        return s[1:-1]
    return s


def _atom_decoration_compatible(
    origin_parts: list[str], target_parts: list[str]
) -> bool:
    """True if origin and target atom decorations differ only in argroles."""
    o_role = origin_parts[1].split(".") if len(origin_parts) > 1 else [""]
    t_role = target_parts[1].split(".") if len(target_parts) > 1 else [""]
    if o_role[0] != t_role[0]:
        return False
    return origin_parts[2:] == target_parts[2:]


def _instantiate(
    target: Hyperedge,
    origin: Hyperedge,
    original: Hyperedge,
    bindings: dict[str, Hyperedge],
    top: bool,
) -> Hyperedge:
    from hyperbase.patterns.checks import is_variable

    if target.atom:
        if is_variable(target):
            return _substitute_var_atom(cast(Atom, target), origin, bindings)
        # Constant atom -- if a structurally-identical atom appears in the
        # original edge, inherit its source-position metadata so the rewrite
        # preserves tok_pos/text_span when the constant pin-points an atom
        # that survived the transform unchanged.
        return _attach_metadata_from_original(cast(Atom, target), original)

    if top and original.not_atom and target.argroles().startswith("{"):
        return _instantiate_with_preserve(target, origin, original, bindings)

    return Hyperedge(
        tuple(_instantiate(c, origin, original, bindings, top=False) for c in target)
    )


def _attach_metadata_from_original(target_atom: Atom, original: Hyperedge) -> Atom:
    """If ``target_atom`` matches an atom in ``original``, return a copy with
    that atom's tok_pos / text_span. Otherwise return ``target_atom`` as-is.
    """
    if target_atom.tok_pos is not None or target_atom.text_span is not None:
        return target_atom
    for atom in _walk_origin_atoms(original):
        if atom == target_atom and (
            atom.tok_pos is not None or atom.text_span is not None
        ):
            return Atom(
                target_atom.atom_str,
                target_atom.parens,
                tok_pos=atom.tok_pos,
                text_span=atom.text_span,
            )
    return target_atom


def _walk_origin_atoms(edge: Hyperedge) -> Iterator[Atom]:
    if edge.atom:
        yield cast(Atom, edge)
    else:
        for c in edge:
            yield from _walk_origin_atoms(c)


def _substitute_var_atom(
    target_atom: Atom,
    origin: Hyperedge,
    bindings: dict[str, Hyperedge],
) -> Hyperedge:
    from hyperbase.patterns.checks import variable_name

    name = variable_name(target_atom)
    if name not in bindings:
        raise ValueError(f"Variable '{name}' has no binding in matched origin pattern")
    binding = bindings[name]
    target_parts = target_atom.parts()
    if len(target_parts) == 1:
        return binding

    if binding.atom:
        binding_atom = cast(Atom, binding)
        new_parts = [binding_atom.root(), *target_parts[1:]]
        return Atom(
            "/".join(p for p in new_parts if p),
            tok_pos=binding_atom.tok_pos,
            text_span=binding_atom.text_span,
        )

    origin_atom = _find_var_atom(origin, name)
    origin_parts = origin_atom.parts() if origin_atom else [name]

    if _atom_decoration_compatible(origin_parts, target_parts):
        # Type/namespace match: only argroles may differ. Apply via
        # replace_argroles, which plumbs to the connector's inner predicate.
        t_role = target_parts[1].split(".") if len(target_parts) > 1 else [""]
        target_argroles = t_role[1] if len(t_role) > 1 else ""
        o_role = origin_parts[1].split(".") if len(origin_parts) > 1 else [""]
        origin_argroles = o_role[1] if len(o_role) > 1 else ""
        if target_argroles == origin_argroles:
            return binding
        bare = _strip_braces(target_argroles)
        if bare == "":
            return binding
        return replace_argroles(binding, bare)

    # Type/namespace change requested. Try to descend through a modifier-style
    # nesting (e.g. ``(immediately/M by/Ta)``) where the binding's outer type
    # is inherited from a single inner atom: rewrite that inner atom in place.
    inner = binding.inner_atom()
    if inner.type() == binding.type():
        new_inner = Atom(
            "/".join(p for p in [inner.root(), *target_parts[1:]] if p),
            tok_pos=inner.tok_pos,
            text_span=inner.text_span,
        )
        return replace_atom(binding, inner, new_inner)

    raise ValueError(
        f"Cannot change type or namespace on non-atomic binding for "
        f"variable '{name}': origin {origin_parts} vs target {target_parts}"
    )


def _instantiate_with_preserve(
    target: Hyperedge,
    origin: Hyperedge,
    original: Hyperedge,
    bindings: dict[str, Hyperedge],
) -> Hyperedge:
    consumed = _consumed_arg_indices(original, origin)
    edge_argroles = original.argroles()
    if edge_argroles.startswith("{"):
        edge_argroles = edge_argroles[1:-1]

    args = list(original[1:])
    preserved_args = [args[i] for i in range(len(args)) if i not in consumed]
    preserved_argroles = "".join(
        edge_argroles[i]
        for i in range(min(len(edge_argroles), len(args)))
        if i not in consumed
    )

    new_children = [
        _instantiate(c, origin, original, bindings, top=False) for c in target
    ]
    final = Hyperedge((new_children[0], *preserved_args, *new_children[1:]))

    target_spec = _strip_braces(target.argroles())
    new_argroles = preserved_argroles + target_spec
    if new_argroles == "":
        return final
    return replace_argroles(final, new_argroles)


def _consumed_arg_indices(
    original_edge: Hyperedge,
    origin_pattern: Hyperedge,
) -> set[int]:
    from hyperbase.patterns import match_pattern

    consumed: set[int] = set()
    if origin_pattern.atom or original_edge.atom:
        return consumed

    args = list(original_edge[1:])
    for arg_pattern in origin_pattern[1:]:
        for i, arg in enumerate(args):
            if i in consumed:
                continue
            if match_pattern(arg, arg_pattern):
                consumed.add(i)
                break
    return consumed
