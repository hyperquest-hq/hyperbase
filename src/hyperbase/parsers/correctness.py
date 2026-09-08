"""Parser-agnostic parse-correctness checking for parsed edges.

Where :func:`hyperbase.correctness.check_correctness` validates a hyperedge in
isolation, this module checks a whole *parse*: the edge plus how its atoms map
onto the original tokens. :func:`check_parse_correctness` combines the hard
grammar errors, the soft structural-quality errors, and token-matching
validation so any parser plugin can score the output of a parse against the
original tokens. The third value in each error tuple is a severity (lower is
worse): ``0`` for hard correctness failures -- which includes the vocabulary
failures of :func:`check_vocabulary` -- ``1`` for token-mismatch issues -- which
includes the alignment failures of :func:`check_alignment` -- ``2`` for argrole
problems, ``3`` for junction issues.

Token matching alone is a *multiset* check: it asks whether the parse's atom
roots and the sentence's tokens account for each other, not which atom sits on
which token. When the caller also has the ``tok_pos`` tree -- the parallel tree
naming, per atom, the token it was aligned to -- passing it turns on
:func:`check_alignment`, which checks that correspondence position by position.
The two are not redundant: a sentence whose text spells out a connector
character (``19:18``) balances perfectly as a multiset while the alignment has
the no-token ``:/J/.`` sitting on the colon and the real ``:/Bx.ma`` on nothing.

When ``strict`` is ``True``, the underlying :func:`check_correctness` also
enforces that every predicate specification-role (``x``) argument is a
specifier (``S``), emitting a ``spec-arg-not-specifier`` failure otherwise.
Default (``strict=False``) behaviour is unchanged.

:func:`parse_coverage` exposes the same token↔atom matching as structured
data — which original tokens went unused and which atoms no token accounts for —
so callers (e.g. a correctness-guided search) can attribute coverage failures
to specific tokens instead of only reading the error messages.

Matching is by exact, case-insensitive surface identity: an atom's root must
*be* one of the tokens. It used to be fuzzy — punctuation stripped from both
sides, then a cascade of concatenation fallbacks so a parse built on one
tokenizer could be scored against another's tokens (spaCy's ``U.S.`` against
``u`` + ``s``, an atom pair ``1`` + ``m`` against the token ``1m``). Every
parser in the ecosystem now shares one tokenizer, and that tolerance quietly
accepted parses no per-token model can represent: ``c'`` cleaned to ``c`` and
matched the token ``c``, so nothing flagged an atom that no token can carry.
"""

from hyperbase.constants import atom_decode
from hyperbase.correctness import check_structural_quality
from hyperbase.hyperedge import Hyperedge
from hyperbase.parsers.utils import clean_alphanumeric, is_structural_atom
from hyperbase.parsers.vocabulary import (
    is_admissible_atom_type,
    is_admissible_special_atom,
    may_carry_argroles,
)


def _surface(text: str) -> str:
    """Comparable surface form of a token or an atom root.

    Atom roots are percent-encoded (``str_to_atom`` maps ``%`` to ``%25``, ``.``
    to ``%2e``, ...), and a gold corpus written by hand may spell either form,
    so both sides are decoded before they meet. Case is folded because atom
    roots are lowercased where tokens keep their casing.
    """
    return atom_decode(text).lower()


def parse_coverage(
    edge: Hyperedge, tokens: list[str]
) -> tuple[list[int], list[Hyperedge]]:
    """Attribute a parse's token-coverage failures to their sources.

    Runs the same token↔atom matching as :func:`check_parse_correctness` and
    returns ``(unused_tokens, unaligned_atoms)``: the indices (into ``tokens``)
    of tokens no atom claims, and the non-structural atoms left without one --
    either because the root is nowhere in the sentence or because earlier atoms
    used up every instance of it. Returns ``([], [])`` when matching cannot run
    (e.g. a malformed edge).
    """
    try:
        # Every token instance, by surface form: an atom claims one of them, and
        # a second atom with the same root needs a second instance.
        available: dict[str, list[int]] = {}
        for i, tok in enumerate(tokens):
            available.setdefault(_surface(tok), []).append(i)

        claimed: set[int] = set()
        unaligned: list[Hyperedge] = []
        for atom in edge.all_atoms():
            if is_structural_atom(atom):
                continue  # stands for a connector the text does not spell out
            instances = available.get(_surface(atom.root()))
            if instances:
                claimed.add(instances.pop(0))
            else:
                unaligned.append(atom)

        # A token no atom claimed is only a failure if it carries content:
        # punctuation is expected to go unused.
        unused = [
            i
            for i in range(len(tokens))
            if i not in claimed and clean_alphanumeric(tokens[i])
        ]
        return unused, unaligned
    except Exception:
        return [], []


def check_vocabulary(
    edge: Hyperedge,
) -> dict[Hyperedge, list[tuple[str, str, int]]]:
    """Check every atom against the vocabulary a parser is allowed to produce.

    Core :func:`hyperbase.correctness.check_correctness` only validates *main*
    types, because a hand-written or domain-specific hyperedge may carry any
    subtype it likes (``union/Pmath``). A parse is held to the narrower contract
    of :mod:`hyperbase.parsers.vocabulary`: the subtype tables of
    ``docs/manual/notation.md``, and the fixed inventory of special atoms. These
    are hard failures, so they carry severity ``0``.
    """
    errors: dict[Hyperedge, list[tuple[str, str, int]]] = {}
    if not edge:
        return errors

    for atom in edge.all_atoms():
        if is_structural_atom(atom):
            # A reserved-namespace atom is matched whole: it carries its
            # argroles in the type slot, so its ``type()`` is only a main type.
            if not is_admissible_special_atom(str(atom)):
                errors[atom] = [
                    (
                        "special-atom-unknown",
                        f"Atom '{atom}' uses the reserved '.' namespace but is "
                        "not one of the special atoms a parser may produce.",
                        0,
                    )
                ]
            continue

        atom_type = atom.type()
        atom_errors: list[tuple[str, str, int]] = []
        if not is_admissible_atom_type(atom_type):
            atom_errors.append(
                (
                    "atom-type-unknown",
                    f"Atom '{atom}' has type '{atom_type}', which is not an "
                    "admissible atom type; a parser must annotate every atom "
                    "with a main type and a subtype from the tables in "
                    "docs/manual/notation.md.",
                    0,
                )
            )
        # An argrole signature on a type that takes none. ``Atom.type`` stops at
        # the '.', and ``Atom.argroles`` returns '' for these, so the trailing
        # part is invisible to every other check -- yet it is in the atom string,
        # so the atom is not one the assembler can ever produce.
        parts = atom.parts()
        if len(parts) > 1 and "." in parts[1] and not may_carry_argroles(atom_type):
            atom_errors.append(
                (
                    "atom-argroles-not-allowed",
                    f"Atom '{atom}' has type '{atom_type}', which carries no "
                    "argroles; only predicates and builders take an argrole "
                    "signature.",
                    0,
                )
            )
        # ``(101/Cq)`` -- an atom written as a one-element edge. It parses, and
        # compares equal to the bare atom, but it serialises with the brackets,
        # so a parse built atom by atom can never reproduce it.
        if atom.parens:
            atom_errors.append(
                (
                    "atom-in-unary-edge",
                    f"Atom '{atom}' is wrapped in a one-element edge; an edge "
                    "has a connector and at least one argument, so the brackets "
                    "are not part of any structure.",
                    0,
                )
            )
        if atom_errors:
            errors[atom] = errors.get(atom, []) + atom_errors

    return errors


def check_alignment(
    edge: Hyperedge, tok_pos: Hyperedge, tokens: list[str]
) -> list[tuple[str, str, int]]:
    """Check the atom->token alignment a parse is stored with.

    ``tok_pos`` mirrors *edge* node for node, each atom replaced by the index of
    the token it was aligned to, or ``-1`` for none. That tree -- not the edge --
    is what the trainer reads to build per-token supervision, so an alignment
    that disagrees with the edge corrupts the targets even when the edge itself
    is impeccable. Returns ``(code, message, severity)`` triples, all at
    severity ``1`` (the token-matching class):

    ``alignment-shape-mismatch``
        ``tok_pos`` is not parallel to *edge*.
    ``structural-atom-aligned``
        A no-token atom (reserved ``.`` namespace) claims a token. It stands
        for a connector the text does not spell out, so the token it took
        belongs to some other atom -- and, if that atom's root is the same
        character, was stolen from it.
    ``atom-unaligned``
        A token-backed atom was aligned to nothing.
    ``alignment-out-of-range`` / ``alignment-not-an-index``
        The index names no token / is not an integer.
    ``alignment-token-mismatch``
        The atom sits on a token that is not its surface form.
    ``alignment-token-reused``
        Two atoms claim the same token.
    """
    errors: list[tuple[str, str, int]] = []
    claimed: dict[int, Hyperedge] = {}

    def walk(sub: Hyperedge, pos: Hyperedge) -> None:
        if sub.atom != pos.atom or (not sub.atom and len(sub) != len(pos)):
            errors.append(
                (
                    "alignment-shape-mismatch",
                    f"The tok_pos tree '{pos}' is not parallel to the edge "
                    f"'{sub}' it aligns.",
                    1,
                )
            )
            return
        if not sub.atom:
            for child, child_pos in zip(sub, pos, strict=True):
                walk(child, child_pos)
            return

        try:
            index = int(str(pos))
        except ValueError:
            errors.append(
                (
                    "alignment-not-an-index",
                    f"Atom '{sub}' is aligned to '{pos}', which is not a token index.",
                    1,
                )
            )
            return

        if is_structural_atom(sub):
            if index >= 0:
                took = (
                    f"token {index} ('{tokens[index]}')"
                    if index < len(tokens)
                    else f"token {index}"
                )
                errors.append(
                    (
                        "structural-atom-aligned",
                        f"Atom '{sub}' stands for a connector the text does not "
                        f"spell out, so it must consume no token, but it claims "
                        f"{took}.",
                        1,
                    )
                )
            return

        if index < 0:
            errors.append(
                (
                    "atom-unaligned",
                    f"Atom '{sub}' carries a surface form but is aligned to no token.",
                    1,
                )
            )
            return
        if index >= len(tokens):
            errors.append(
                (
                    "alignment-out-of-range",
                    f"Atom '{sub}' is aligned to token {index}, but the sentence "
                    f"has {len(tokens)} token(s).",
                    1,
                )
            )
            return
        if _surface(sub.root()) != _surface(tokens[index]):
            errors.append(
                (
                    "alignment-token-mismatch",
                    f"Atom '{sub}' is aligned to token {index} "
                    f"('{tokens[index]}'), which is not its surface form.",
                    1,
                )
            )
            return
        if index in claimed:
            errors.append(
                (
                    "alignment-token-reused",
                    f"Atoms '{claimed[index]}' and '{sub}' are both aligned to "
                    f"token {index} ('{tokens[index]}').",
                    1,
                )
            )
        claimed[index] = sub

    walk(edge, tok_pos)
    return errors


def check_parse_correctness(
    edge: Hyperedge,
    tokens: list[str],
    strict: bool = False,
    tok_pos: Hyperedge | None = None,
) -> dict[str | Hyperedge, list[tuple[str, str, int]]]:

    # Hard grammar failures (severity 0), keyed by subedge.
    errors: dict[str | Hyperedge, list[tuple[str, str, int]]] = {
        k: list(v) for k, v in edge.check_correctness(strict=strict).items()
    }

    for extra in (check_vocabulary(edge), check_structural_quality(edge)):
        for k, v in extra.items():
            if k in errors:
                errors[k].extend(v)
            else:
                errors[k] = v

    # Only check token matching if we have a valid edge
    if edge:
        try:
            unused, unaligned = parse_coverage(edge, tokens)
            present = {_surface(token) for token in tokens}

            token_matching_errors: list[tuple[str, str, int]] = []
            for atom in unaligned:
                root = atom.root()
                if _surface(root) in present:
                    token_matching_errors.append(
                        (
                            "root-without-token",
                            f"Atom root '{root}' in the parse is used more times than "
                            "it appears in the source sentence.",
                            1,
                        )
                    )
                else:
                    token_matching_errors.append(
                        (
                            "atom-not-a-token",
                            f"Atom root '{root}' is not one of the source tokens; an "
                            "atom must carry exactly one token's surface form.",
                            1,
                        )
                    )

            for token_idx in unused:
                token_matching_errors.append(
                    (
                        "token-unused",
                        f"Token '{tokens[token_idx]}' from the source sentence is not "
                        "used by any atom in the parse.",
                        1,
                    )
                )

            if len(token_matching_errors) > 0:
                errors["token-matching"] = token_matching_errors

        except (AttributeError, Exception):
            # If token counting fails (e.g., edge is invalid), skip it
            pass

        # Positional atom<->token correspondence, when the caller has it. Kept
        # out of the try above so an alignment bug is reported rather than
        # swallowed by the token-matching guard.
        if tok_pos is not None:
            alignment_errors = check_alignment(edge, tok_pos, tokens)
            if alignment_errors:
                errors["alignment"] = alignment_errors

    return errors
