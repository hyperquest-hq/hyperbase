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

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from hyperbase.builders import str_to_atom
from hyperbase.constants import atom_decode
from hyperbase.correctness import check_structural_quality
from hyperbase.hyperedge import Hyperedge
from hyperbase.parsers.utils import clean_alphanumeric, is_structural_atom
from hyperbase.parsers.vocabulary import (
    CONNECTIVE_SYMBOLS,
    CONVERTIBLE_MODIFIERS,
    FLUSH_ONLY_SYMBOLS,
    SPECIAL_ATOMS,
    is_admissible_atom_type,
    is_admissible_special_atom,
    may_carry_argroles,
)

if TYPE_CHECKING:
    from hyperbase.parsers.parser import Parser


# The shape every check -- built-in or parser-supplied -- reports in: a mapping
# from the offending subedge (or a string naming the class of problem, as
# "token-matching" and "alignment" do) to a list of ``(code, message, severity)``
# triples. Lower severity is worse.
ErrorMap = dict[str | Hyperedge, list[tuple[str, str, int]]]

# Where a parser check's own failures are reported. Deliberately not a key any
# built-in check uses, so a broken plugin is legible as such.
PARSER_CHECKS_KEY = "parser-checks"


@dataclass(frozen=True)
class CheckContext:
    """Everything a correctness check is given about one parse.

    A frozen record rather than a positional signature so a check declares one
    parameter instead of five, and so a field can be added here later without
    breaking the checks every installed parser already supplies. ``tok_pos`` and
    ``text`` are ``None`` when the caller does not have them -- the built-in
    alignment and symbol-coverage checks simply do not run in that case, and a
    parser check that needs them should do the same rather than assume.
    """

    edge: Hyperedge
    tokens: list[str]
    tok_pos: Hyperedge | None = None
    text: str | None = None
    strict: bool = False


CorrectnessCheck = Callable[["CheckContext"], ErrorMap]
"""A parser-supplied check: takes one parse, returns the errors it found."""


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
        # A root that spells a reserved character carries it percent-encoded:
        # ``build_atom`` -- the only thing that mints an atom from a token --
        # encodes and lowercases unconditionally, so a raw root is a form no
        # parse can be assembled into. Already-encoded roots are left alone, or
        # '%25' would be re-read as needing to become '%2525'.
        root = parts[0]
        if atom_decode(root) == root and str_to_atom(root) != root:
            atom_errors.append(
                (
                    "atom-root-not-canonical",
                    f"Atom root '{root}' is not in canonical form; a root is "
                    f"percent-encoded and lowercased, so this must be written "
                    f"'{str_to_atom(root)}'.",
                    0,
                )
            )
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


def token_spans(text: str, tokens: list[str]) -> list[tuple[int, int]] | None:
    """Character spans of *tokens* in *text*, or None if they cannot be located.

    A plain in-order scan: each token is found at or after the end of the
    previous one. It is deliberately not the tokenizer's own span logic --
    ``hyperparser`` depends on this package, not the other way round -- and it
    only has to answer one question: is there whitespace between two tokens.

    Returns ``None`` when a token is not found, which happens when the text
    holds a character the tokenizer folded (a curly apostrophe). The caller then
    skips the checks that need spacing rather than guessing.
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    for token in tokens:
        start = text.find(token, pos)
        if start < 0:
            return None
        pos = start + len(token)
        spans.append((start, pos))
    return spans


def _claimed_tokens(tree: Hyperedge, out: set[int] | None = None) -> set[int]:
    """Every token index a ``tok_pos`` subtree points at (``-1`` excluded)."""
    out = set() if out is None else out
    if tree.atom:
        try:
            index = int(str(tree))
        except ValueError:
            return out
        if index >= 0:
            out.add(index)
    else:
        for child in tree:
            _claimed_tokens(child, out)
    return out


def check_symbol_coverage(
    edge: Hyperedge,
    tok_pos: Hyperedge,
    tokens: list[str],
    text: str | None = None,
) -> list[tuple[str, str, int]]:
    """Report connective symbols the parse dropped into a connector's gap.

    ``:/J/.`` and ``+/B.am/.`` stand for a connector the text does *not* spell
    out. When the text does spell one, writing the structural atom instead makes
    the symbol vanish: the parse still scores clean, because
    :func:`parse_coverage` forgives an unclaimed token with no alphanumerics,
    and the token goes on to be supervised as something to discard. The same
    happens when a modifier swallows it -- ``(low/Ma density/Cc)`` for
    "low-density".

    Only an *unambiguous* gap is reported. A flat list with several symbol gaps
    ("May 03, 2017 15:22 pm") really is missing its symbols, but no rule can say
    which one the connector stands for, so it is left alone rather than reported
    as something no repair could act on.

    Without *text* the punctuation-doubles (``.``, ``,``, ``;``, ``:``) cannot be
    told from sentence punctuation and are skipped; the rest are still reported.
    """
    errors: list[tuple[str, str, int]] = []
    spans = token_spans(text, tokens) if text is not None else None
    claimed = _claimed_tokens(tok_pos)

    def flush(index: int) -> bool:
        return (
            spans is not None
            and 0 < index < len(spans) - 1
            and spans[index - 1][1] == spans[index][0]
            and spans[index][1] == spans[index + 1][0]
        )

    def walk(sub: Hyperedge, tree: Hyperedge) -> None:
        if sub.atom or tree.atom or len(sub) != len(tree):
            return
        connector = sub[0]
        arg_spans: list[list[int]] | None = None
        if connector.atom and str(connector) in SPECIAL_ATOMS:
            arg_spans = [sorted(_claimed_tokens(child)) for child in tree[1:]]
        elif (
            len(sub) == 2
            and connector.atom
            and (connector.type() or "") in CONVERTIBLE_MODIFIERS
            and (sub[1].mtype() or "") == "C"
        ):
            arg_spans = [
                sorted(_claimed_tokens(tree[0])),
                sorted(_claimed_tokens(tree[1])),
            ]
        if arg_spans is not None:
            gaps = {
                max(left) + 1
                for left, right in pairwise(arg_spans)
                if left and right and max(left) + 2 == min(right)
            }
            if len(gaps) == 1:
                index = gaps.pop()
                symbol = tokens[index] if 0 <= index < len(tokens) else ""
                joins = symbol in CONNECTIVE_SYMBOLS or (
                    symbol in FLUSH_ONLY_SYMBOLS and flush(index)
                )
                if joins and index not in claimed:
                    errors.append(
                        (
                            "connective-symbol-dropped",
                            f"Token '{symbol}' joins the arguments of "
                            f"'{connector}' but no atom carries it; the "
                            f"connector the text spells out must be used "
                            f"instead of a structural one.",
                            1,
                        )
                    )
        for child, sub_tree in zip(sub, tree, strict=False):
            walk(child, sub_tree)

    walk(edge, tok_pos)
    return errors


def _merge_errors(
    errors: ErrorMap, extra: Mapping[Any, list[tuple[str, str, int]]]
) -> None:
    """Fold *extra* into *errors* in place, appending where a key is shared.

    Nothing is ever replaced or dropped: two checks that both have something to
    say about the same subedge each keep their say. This is what makes a
    parser-supplied check purely additive -- there is no code path by which one
    can shorten a list a built-in check wrote.
    """
    for key, issues in extra.items():
        if key in errors:
            errors[key].extend(issues)
        else:
            errors[key] = list(issues)


def _validate(produced: object) -> ErrorMap:
    """Return *produced* as an :data:`ErrorMap`, or raise ``ValueError``.

    A parser check is plugin code, so its return value is checked before it is
    merged rather than trusted. The message names the specific breakage, because
    it is what the plugin author will see reported back.
    """
    if not isinstance(produced, dict):
        raise ValueError(f"returned {type(produced).__name__}, not a dict")
    out: ErrorMap = {}
    for key, issues in produced.items():
        # Atom subclasses Hyperedge, so one test covers both kinds of key.
        if not isinstance(key, (str, Hyperedge)):
            raise ValueError(
                f"keyed errors by {type(key).__name__}; a key is a subedge or a string"
            )
        if not isinstance(issues, list):
            raise ValueError(
                f"mapped {key!r} to {type(issues).__name__}, not a list of errors"
            )
        for issue in issues:
            if not isinstance(issue, tuple) or len(issue) != 3:
                raise ValueError(
                    f"reported {issue!r} under {key!r}; an error is a "
                    "(code, message, severity) triple"
                )
            code, message, severity = issue
            if (
                not isinstance(code, str)
                or not isinstance(message, str)
                or not isinstance(severity, int)
            ):
                raise ValueError(
                    f"reported {issue!r} under {key!r}; a triple is "
                    "(str code, str message, int severity)"
                )
        out[key] = list(issues)
    return out


def run_checks(checks: Iterable[CorrectnessCheck], context: CheckContext) -> ErrorMap:
    """Run *checks* against *context* and return what they found.

    Each check is isolated: one that raises, or returns something that is not an
    error map, is reported under :data:`PARSER_CHECKS_KEY` and the rest still
    run. A broken check is *reported* rather than skipped quietly -- elsewhere in
    this module a failed check degrades to fewer errors, which is right when the
    fallback is "this malformed edge yielded less detail", and wrong here, where
    it would turn a gate into a no-op nobody notices. Severity ``0`` for the same
    reason: a parse whose checks did not run is unverified, and the conservative
    reading of unverified is "worst", never "clean".

    Takes the checks themselves rather than the parser that supplies them, so it
    can be used where no ``Parser`` object is in reach: ``hyperparser`` assembles
    parses inside spawn workers that must not have a model pickled into them, and
    passes module-level check functions here instead.
    """
    errors: ErrorMap = {}

    def report(code: str, message: str) -> None:
        """Record a failure of the checking itself, not of the parse."""
        _merge_errors(errors, {PARSER_CHECKS_KEY: [(code, message, 0)]})

    for check in checks:
        name = getattr(check, "__name__", None) or repr(check)
        try:
            produced = check(context)
        except Exception as exc:  # one bad check must not take out the whole gate
            report(
                "check-failed",
                f"Parser check '{name}' raised {type(exc).__name__}: {exc}; "
                "this parse was not checked against it.",
            )
            continue
        # An empty map is the ordinary "nothing to report", and a check that
        # falls off its end returning None is read the same way: both say the
        # check ran and found nothing, and neither can be told from the other.
        if not produced:
            continue
        try:
            validated = _validate(produced)
        except ValueError as exc:
            # Discarded whole rather than merged in part: half an error map is
            # not something the callers downstream can reason about.
            report(
                "check-malformed",
                f"Parser check '{name}' {exc}; what it reported was discarded.",
            )
            continue
        _merge_errors(errors, validated)

    return errors


def run_parser_checks(parser: Parser, context: CheckContext) -> ErrorMap:
    """Run the checks *parser* contributes via :meth:`Parser.correctness_checks`.

    A thin resolution step in front of :func:`run_checks`: the hook itself is
    plugin code too, so a hook that raises is reported the same way a raising
    check is, rather than propagating out of the gate.
    """
    try:
        checks = list(parser.correctness_checks())
    except Exception as exc:  # a broken hook must not abort the gate
        return {
            PARSER_CHECKS_KEY: [
                (
                    "check-failed",
                    f"{type(parser).__name__}.correctness_checks() raised "
                    f"{type(exc).__name__}: {exc}; this parse was not checked "
                    "against the parser's own rules.",
                    0,
                )
            ]
        }
    return run_checks(checks, context)


def check_parse_correctness(
    edge: Hyperedge,
    tokens: list[str],
    strict: bool = False,
    tok_pos: Hyperedge | None = None,
    text: str | None = None,
    parser: Parser | None = None,
    checks: Iterable[CorrectnessCheck] | None = None,
) -> ErrorMap:
    """Check a whole parse: the edge, and how its atoms map onto the tokens.

    Extra checks run after the built-in ones and their findings are merged into
    the same map. They can only add: a parser makes the gate stricter for its own
    output, never more lenient. Leaving both *parser* and *checks* unset is
    exactly the behaviour this function had before the hook existed.

    *parser* contributes whatever :meth:`Parser.correctness_checks` returns, and
    is the ergonomic form for a caller that holds a parser. *checks* takes the
    check functions directly, for a caller that does not -- a parser's own worker
    subprocesses, which must not have a model pickled into them. Giving both runs
    both.
    """

    # Hard grammar failures (severity 0), keyed by subedge.
    errors: ErrorMap = {
        k: list(v) for k, v in edge.check_correctness(strict=strict).items()
    }

    for extra in (check_vocabulary(edge), check_structural_quality(edge)):
        _merge_errors(errors, extra)

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
            # Needs the argument spans, so it is gated on tok_pos the same way.
            symbol_errors = check_symbol_coverage(edge, tok_pos, tokens, text)
            if symbol_errors:
                errors["symbol-coverage"] = symbol_errors

    # Parser-supplied checks go last, so they see a complete built-in picture
    # layered underneath them. Outside the ``if edge`` above: an empty or
    # malformed edge is exactly the case a parser may have something to say
    # about, and nothing here depends on the edge being well-formed.
    if parser is not None or checks is not None:
        context = CheckContext(
            edge=edge,
            tokens=tokens,
            tok_pos=tok_pos,
            text=text,
            strict=strict,
        )
        if parser is not None:
            _merge_errors(errors, run_parser_checks(parser, context))
        if checks is not None:
            _merge_errors(errors, run_checks(checks, context))

    return errors
