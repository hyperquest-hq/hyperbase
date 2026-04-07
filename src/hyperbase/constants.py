from enum import Enum


class EdgeType(str, Enum):
    """SH edge types."""

    CONCEPT = "C"
    PREDICATE = "P"
    MODIFIER = "M"
    BUILDER = "B"
    TRIGGER = "T"
    CONJUNCTION = "J"
    RELATION = "R"
    SPECIFIER = "S"


class ArgRole(str, Enum):
    """Argument roles for predicates and builders."""

    MAIN = "m"
    SUBJECT = "s"
    PASSIVE = "p"
    AGENT = "a"
    COMPLEMENT = "c"
    OBJECT = "o"
    INDIRECT = "i"
    PARATAXIS = "t"
    INTERJECTION = "j"
    SPECIFICATION = "x"
    RELATIVE = "r"
    UNDETERMINED = "?"


# Pre-defined system atoms
compound_noun_builder = "+/B/."
possessive_builder = "poss/Bp.am/."
list_of_matches_builder = "list/J/."

# Pattern functions
PATTERN_FUNCTIONS: set[str] = {"var", "atoms", "lemma", "any"}

# Argument role ordering for normalisation
argrole_order: dict[str, int] = {
    ArgRole.MAIN: -1,
    ArgRole.SUBJECT: 0,
    ArgRole.PASSIVE: 1,
    ArgRole.AGENT: 2,
    ArgRole.COMPLEMENT: 3,
    ArgRole.OBJECT: 4,
    ArgRole.INDIRECT: 5,
    ArgRole.PARATAXIS: 6,
    ArgRole.INTERJECTION: 7,
    ArgRole.SPECIFICATION: 8,
    ArgRole.RELATIVE: 9,
    ArgRole.UNDETERMINED: 10,
}

# Valid argument roles by connector type
valid_p_argroles: set[str] = {
    ArgRole.SUBJECT,
    ArgRole.PASSIVE,
    ArgRole.AGENT,
    ArgRole.COMPLEMENT,
    ArgRole.OBJECT,
    ArgRole.INDIRECT,
    ArgRole.PARATAXIS,
    ArgRole.INTERJECTION,
    ArgRole.SPECIFICATION,
    ArgRole.RELATIVE,
    ArgRole.UNDETERMINED,
}
valid_b_argroles: set[str] = {ArgRole.MAIN, ArgRole.AGENT}
