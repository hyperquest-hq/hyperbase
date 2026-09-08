"""The symbolic vocabulary SH parsers are expected to produce.

Core hyperbase treats subtypes as opaque, arbitrarily extensible strings (see
``docs/manual/notation.md``): ``union/Pmath`` is a perfectly legal atom. Parsers
are held to a stricter contract -- the single-character subtypes of the notation
tables, the narrow argrole sets, and a fixed inventory of special atoms in the
reserved ``.`` namespace. This module is the one place those inventories are
written down; :mod:`hyperbase.parsers.correctness` enforces them and parser
plugins (e.g. ``hyperparser.types``) build their label vocabularies from them.
"""

# Admissible full atom types (main type + subtype), per the subtype tables of
# ``docs/manual/notation.md``. Only the six atomic types appear: ``R`` and ``S``
# are always implicit and can never annotate an atom.
ATOM_TYPES: tuple[str, ...] = (
    # concepts
    "Cc",
    "Cp",
    "Ci",
    "Cd",
    "Cw",
    "Ca",
    "Cq",
    "Cg",
    "Ce",
    "Cx",
    # modifiers
    "Md",
    "Ma",
    "Mq",
    "Mm",
    "Mb",
    "Mg",
    "Mn",
    "Mp",
    "Me",
    "Mw",
    "Mx",
    # predicates
    "Pv",
    "Pi",
    "Pj",
    "Pn",
    "Pe",
    "Px",
    # builders
    "Bp",
    "Bm",
    "Bx",
    # triggers
    "Tt",
    "Tl",
    "Ti",
    "Ta",
    "Tb",
    "Ts",
    "Tn",
    "Tw",
    "Tr",
    "Tq",
    "Tv",
    "Tf",
    "Tc",
    "Tp",
    "To",
    "Tg",
    "Te",
    "Td",
    "Tx",
    # conjunctions
    "Jx",
)

# Every argrole letter a parser may emit, on any connector. The order is the
# label order of the arc-role head in the parser plugins -- keep it stable.
ARGROLE_LETTERS: tuple[str, ...] = ("s", "o", "x", "m", "a")
# Main types whose atoms carry argroles at all. Triggers and conjunctions take
# their argument without naming a role, and modifiers take exactly one, so a
# subtype followed by a '.' is only meaningful on a predicate or a builder --
# ``que/Td.x`` is not an atom a parser may produce.
TYPES_WITH_ARGROLES: frozenset[str] = frozenset("PB")
# Valid argrole letters by connector main type.
VALID_P_ARGROLES: frozenset[str] = frozenset("sox")
VALID_B_ARGROLES: frozenset[str] = frozenset("ma")
# Roles that may appear at most once on a single connector.
SINGLETON_ARGROLES: tuple[str, ...] = ("s", "o", "a", "m")

# Concept subtype a modifier's atom becomes when a modifier construction is
# rewritten as a builder -- ``(low/Ma density/Cc)`` spells a hyphen the parse
# dropped, and ``(-/Bx.am low/Ca density/Cc)`` puts it back. A builder is
# ``(B C C+) -> C``, so the modifier atom has to become a concept, and the
# subtype tables of ``docs/manual/notation.md`` decide which one. Where the two
# tables name the same category the mapping is that category; the rest fall back
# to the nearest nominal, or to ``Cx`` where the concept table has no counterpart
# at all.
#
# Two letter-coincidences are false friends, so this cannot be done by keeping
# the letter: ``Mg`` is *degree* while ``Cg`` is *gerund*, and ``Mp`` is
# *possessive* while ``Cp`` is *proper*.
MODIFIER_TO_CONCEPT: dict[str, str] = {
    # same category in both tables
    "Ma": "Ca",  # adjective
    "Mq": "Cq",  # quantitative
    "Mx": "Cx",  # unclassified
    "Md": "Cd",  # determinant
    "Me": "Ce",  # demonstrative: determiner -> pronoun
    "Mw": "Cw",  # interrogative: determiner -> wh-nominal
    # no counterpart in the concept table
    "Mp": "Ci",  # possessive determiner -> the nearest nominal, a pronoun
    "Mg": "Cx",  # degree / intensifier
    "Mn": "Cx",  # negation
    "Mb": "Cx",  # adverbial / manner
    "Mm": "Cx",  # modal / tense / auxiliary
}

# The subtypes a *repair* may actually rewrite, narrower than the table above.
# These three describe lexical content, which is what a compound is made of.
#
# The determiner class (``Md``, ``Me``, ``Mw``) is deliberately absent even
# though it maps exactly: a determiner is never a member of a compound, so a
# symbol between it and its head is something else -- the hyphen of
# ``state-of-the-art``, or the ``#`` of ``die #MeToo``, which binds to
# ``MeToo`` and not to ``die``. ``Mg``/``Mn``/``Mb``/``Mm`` are absent because
# their fallback asserts a concept category for an intensifier or a negation
# particle, which is worse than leaving the construction alone.
CONVERTIBLE_MODIFIERS: frozenset[str] = frozenset({"Ma", "Mq", "Mx"})

# Special atoms: connectors the surface text does not spell out, marked by the
# reserved ``.`` namespace. The special triggers are derived from the trigger
# entries of ATOM_TYPES so the two inventories cannot drift apart.
#
# The system atoms in :mod:`hyperbase.constants` (``poss/Bp.am/.``,
# ``list/J/.``) are deliberately absent: they belong to the pattern machinery
# and never occur in a parse.
SPECIAL_ATOMS: tuple[str, ...] = (
    # compound-noun / relational builders
    "+/B.am/.",
    "+/B.ma/.",
    # implicit conjunction
    ":/J/.",
    # one special trigger per trigger subtype
    *(f"_/{atom_type}/." for atom_type in ATOM_TYPES if atom_type[0] == "T"),
)

_ATOM_TYPE_SET: frozenset[str] = frozenset(ATOM_TYPES)
_SPECIAL_ATOM_SET: frozenset[str] = frozenset(SPECIAL_ATOMS)


def is_admissible_atom_type(atom_type: str) -> bool:
    """True if *atom_type* is a full type a parser may annotate an atom with.

    Expects the value of :meth:`hyperbase.hyperedge.Atom.type` -- main type plus
    subtype, with argroles and namespace already stripped. A bare main type
    (``'C'``) is *not* admissible: parsers must commit to a subtype.
    """
    return atom_type in _ATOM_TYPE_SET


def may_carry_argroles(atom_type: str) -> bool:
    """True if an atom of *atom_type* is allowed an argrole signature.

    Expects the value of :meth:`hyperbase.hyperedge.Atom.type` -- main type plus
    subtype. Only predicates and builders qualify; everything else must be a
    bare subtype.
    """
    return atom_type[:1] in TYPES_WITH_ARGROLES


def is_admissible_special_atom(atom: str) -> bool:
    """True if *atom* is one of the special atoms a parser may produce.

    Matched on the atom's full string (``'+/B.am/.'``), not on its type: a
    special atom carries its argroles and its reserved namespace with it.
    """
    return atom in _SPECIAL_ATOM_SET
