# Pre-defined system atoms
compound_noun_builder = "+/B/."
possessive_builder = "poss/Bp.am/."
list_of_matches_builder = "list/J/."

# Pattern functions
PATTERN_FUNCTIONS: set[str] = {"var", "atoms", "lemma", "any"}

# Argument role ordering for normalisation
argrole_order: dict[str, int] = {
    "m": -1,
    "s": 0,
    "p": 1,
    "a": 2,
    "c": 3,
    "o": 4,
    "i": 5,
    "t": 6,
    "j": 7,
    "x": 8,
    "r": 9,
    "?": 10,
}

# Valid argument roles by connector type
valid_p_argroles: set[str] = {"s", "p", "a", "c", "o", "i", "t", "j", "x", "r", "?"}
valid_b_argroles: set[str] = {"m", "a"}
