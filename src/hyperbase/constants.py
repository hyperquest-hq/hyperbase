import re
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

# Atom URL-encoding table: char -> percent-encoded form
# Order matters for sequential replace, but with translate/re.sub it doesn't.
_ATOM_ENCODE_CHARS: dict[str, str] = {
    "%": "%25",
    "/": "%2f",
    " ": "%20",
    "(": "%28",
    ")": "%29",
    ".": "%2e",
    "*": "%2a",
    "&": "%26",
    "@": "%40",
    "\n": "%0a",
    "\r": "%0d",
}

# str.translate table for encoding (single char -> multi-char string)
ATOM_ENCODE_TABLE: dict[int, str] = {ord(k): v for k, v in _ATOM_ENCODE_CHARS.items()}

# Decode map: percent-encoded form -> char
_ATOM_DECODE_MAP: dict[str, str] = {v: k for k, v in _ATOM_ENCODE_CHARS.items()}

# Compiled pattern matching any percent-encoded token
_ATOM_DECODE_RE: re.Pattern[str] = re.compile(
    "|".join(re.escape(code) for code in _ATOM_DECODE_MAP)
)


def atom_decode(s: str) -> str:
    """Decode all percent-encoded sequences in a single pass."""
    return _ATOM_DECODE_RE.sub(lambda m: _ATOM_DECODE_MAP[m.group()], s)
