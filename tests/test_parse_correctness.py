from hyperbase import hedge
from hyperbase.parsers.correctness import (
    check_alignment,
    check_parse_correctness,
    check_vocabulary,
    parse_coverage,
)
from hyperbase.parsers.parser import Parser
from hyperbase.parsers.utils import clean_alphanumeric
from hyperbase.parsers.vocabulary import (
    ATOM_TYPES,
    CONVERTIBLE_MODIFIERS,
    MODIFIER_TO_CONCEPT,
    is_admissible_atom_type,
)


class TestParseCoverage:
    """Tests for parse_coverage: coverage failures attributed to their sources."""

    def test_full_coverage(self):
        edge = hedge("(plays/Pv.so maria/Cp chess/Cc)")
        unused, overused = parse_coverage(edge, ["Maria", "plays", "chess"])
        assert unused == []
        assert overused == []

    def test_unused_token_reported_with_original_index(self):
        edge = hedge("(plays/Pv.s maria/Cp)")
        unused, overused = parse_coverage(edge, ["Maria", "plays", "chess"])
        assert unused == [2]
        assert overused == []

    def test_punctuation_tokens_never_unused(self):
        # ',' cleans to empty and is excluded from matching, exactly as in
        # check_parse_correctness; indices still refer to the original list.
        edge = hedge("(plays/Pv.s maria/Cp)")
        unused, overused = parse_coverage(edge, ["Maria", ",", "plays", "chess"])
        assert unused == [3]
        assert overused == []

    def test_overused_root_returns_the_atom(self):
        edge = hedge("(plays/Pv.so maria/Cp maria/Cp)")
        unused, overused = parse_coverage(edge, ["Maria", "plays", "chess"])
        assert unused == [2]
        assert [str(a) for a in overused] == ["maria/Cp"]

    def test_agrees_with_check_parse_correctness(self):
        edge = hedge("(plays/Pv.s maria/Cp)")
        tokens = ["Maria", "plays", "chess"]
        unused, overused = parse_coverage(edge, tokens)
        issues = check_parse_correctness(edge, tokens).get("token-matching", [])
        assert len([c for c, _, _ in issues if c == "token-unused"]) == len(unused)
        assert len([c for c, _, _ in issues if c == "root-without-token"]) == len(
            overused
        )


class TestCleanAlphanumeric:
    """The helper that decides whether an unclaimed token is worth reporting."""

    def test_lowercases_and_strips_punctuation(self):
        assert clean_alphanumeric("Test/C") == "testc"
        assert clean_alphanumeric("WORD-123") == "word123"

    def test_punctuation_only_cleans_to_empty(self):
        # This is what exempts '.' and ',' from the token-unused report.
        assert clean_alphanumeric("...") == ""
        assert clean_alphanumeric("(") == ""

    def test_keeps_non_ascii_letters(self):
        assert clean_alphanumeric("Ῥωμαϊκά") == "ῥωμαϊκά"


class TestCheckParseCorrectness:
    """Tests for check_parse_correctness function"""

    def test_valid_parse_matching_tokens(self):
        """Test with valid parse and matching tokens"""
        valid_parse = "(is/Pv.so (the/Md sky/Cc) blue/Ca)"
        tokens = ["the", "sky", "is", "blue"]
        edge = hedge(valid_parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert len(errors) == 0

    def test_with_original_text(self):
        """Test that passing original text orders roots correctly"""
        valid_parse = "(is/Pv.so (the/Md sky/Cc) blue/Ca)"
        tokens = ["the", "sky", "is", "blue"]
        edge = hedge(valid_parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert len(errors) == 0

    def test_atom_spanning_several_tokens_is_reported(self):
        """An atom must carry one token: 'newyork' over ['new', 'york'] cannot."""
        parse = "(is/Pv.s newyork/Cp)"
        tokens = ["new", "york", "is"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        found = [e[0] for e in errors["token-matching"]]
        assert "atom-not-a-token" in found  # newyork
        assert found.count("token-unused") == 2  # new, york

    def test_valid_parse_missing_token(self):
        """Test when parse doesn't use all tokens"""
        parse = "(is/Pv.so blue/Ca)"
        tokens = ["sky", "is", "blue"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        # Should have error: "sky" not used
        assert len(errors) > 0

    def test_valid_parse_extra_root(self):
        """Test when parse uses root not in tokens"""
        parse = "(is/Pv.so (the/Md sky/Cc) blue/Ca)"
        tokens = ["sky", "is", "blue"]  # Missing "the"
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        # Should have error: "the" used but not in tokens
        assert len(errors) > 0

    def test_token_count_mismatch(self):
        """Test when token appears multiple times"""
        parse = "(is/Pv.s blue/Ca)"
        tokens = ["blue", "blue", "is"]  # "blue" appears twice
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        # Should have error: "blue" used less than it appears
        assert len(errors) > 0

    def test_special_characters_filtered(self):
        """Test that special characters in tokens are filtered"""
        parse = "(is/Pv.s blue/Ca)"
        tokens = ["(", "is", "blue", ")"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert len(errors) == 0

    def test_empty_tokens_list(self):
        """Test with empty tokens list"""
        parse = "(is/Pv.s blue/Ca)"
        tokens = []
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        # Should have errors: roots used but no tokens
        assert len(errors) > 0

    # -- parses tokenized differently from the token list --------------------- #
    # These four came from the spaCy-based Alpha-Beta parser, whose atoms were
    # scored against another tokenizer's tokens; matching used to strip
    # punctuation and try concatenations so they passed. Every parser in the
    # ecosystem now shares one tokenizer, and an atom that carries no single
    # token is a parse no per-token model can produce -- so they are reported.

    def test_atom_joining_tokens_the_tokenizer_split(self):
        """'U.S.' as one atom over the tokens ['u', 's']."""
        # From: Russia regrets U.S. not pressing charges over boy's death
        parse = "(regrets/Pv.so russia/Cp (pressing/Pv.so us/Cp (over/Bp.ma charges/Cc (s/Bp.am boy/Cc death/Cc))))"
        tokens = [
            "russia",
            "regrets",
            "u",
            "s",
            "pressing",
            "charges",
            "over",
            "boy",
            "s",
            "death",
        ]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        found = [e[0] for e in errors["token-matching"]]
        assert "atom-not-a-token" in found  # us
        assert "token-unused" in found  # the 'u' it was built from

    def test_tokenization_mismatch_us_case_error1(self):
        """Same parse with a missing token: still an error, as it always was."""
        parse = "(regrets/Pv.sr russia/Cp (pressing/Pv.so us/Cp (over/Bp.ma charges/Cc (s/Bp.am boy/Cc death/Cc))))"
        tokens = [
            "russia",
            "regrets",
            "u",
            "pressing",
            "charges",
            "over",
            "boy",
            "s",
            "death",
        ]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert len(errors) > 0

    def test_tokenization_mismatch_us_case_error2(self):
        """Same parse with a bad argrole: still an error, as it always was."""
        parse = "(regrets/Pv.sr russia/Cp (pressing/Pv us/Cp (over/Bp.ma charges/Cc (s/Bp.am boy/Cc death/Cc))))"
        tokens = [
            "russia",
            "regrets",
            "u",
            "s",
            "pressing",
            "charges",
            "over",
            "boy",
            "s",
            "death",
        ]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert len(errors) > 0

    def test_atoms_splitting_a_token_the_tokenizer_kept_whole(self):
        """Atoms '1' + 'm' over the single token '1m'."""
        # From: RAF flies 1m euros to Cyprus
        parse = "(flies/Pv.sxox raf/Cp (1/Mq m/Cc) euros/Cc (to/Tl cyprus/Cp))"
        tokens = ["raf", "flies", "1m", "euros", "to", "cyprus"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        found = [e[0] for e in errors["token-matching"]]
        assert found.count("atom-not-a-token") == 2  # 1, m
        assert "token-unused" in found  # 1m

    def test_atom_never_matches_a_substring_of_a_token(self):
        """'m' must not be satisfied by the 'm' inside 'malawi'."""
        # From: Malawi gets 37m in UK health aid
        parse = (
            "(gets/Pv.sox malawi/Cp (37/Mq m/Cc) (in/Tl (uk/Md (health/Md aid/Cc))))"
        )
        tokens = ["malawi", "gets", "37m", "in", "uk", "health", "aid"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        found = [e[0] for e in errors["token-matching"]]
        assert found.count("atom-not-a-token") == 2  # 37, m -- not 'malawi'
        assert "token-unused" in found  # 37m

    def test_contraction_split_differently_from_the_tokens(self):
        """Atoms 'do' + \"n't\" over the tokens ['don', 't']."""
        parse = (
            "((off/Ml/en (do/Mv.-i-----/en (n't/Mn/en rip/P!.o.-i-----/en))) me/Ci/en)"
        )
        tokens = ["don", "t", "rip", "me", "off"]
        edge = hedge(parse)
        assert edge
        errors = check_parse_correctness(edge, tokens)
        found = [e[0] for e in errors["token-matching"]]
        assert found.count("atom-not-a-token") == 2  # do, n't
        assert found.count("token-unused") == 2  # don, t

    def test_contraction_matching_the_tokens_passes(self):
        """The same contraction is clean once the atoms carry the real tokens."""
        parse = "((doesn/Mv.-i-----/en ('t/Mn/en is/Pv.o)) blue/Ca)"
        tokens = ["doesn", "'t", "is", "blue"]
        edge = hedge(parse)
        assert edge
        assert "token-matching" not in check_parse_correctness(edge, tokens)

    def test_valid_edge(self):
        edge = hedge("(is/Pv.s bob/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [])

        # Filter out token matching errors
        structural_errors = {k: v for k, v in errors.items() if k != "token-matching"}
        assert not structural_errors

    def test_invalid_argrole(self):
        # 'z' is not in mspaoixtjr
        edge = hedge("(is/Pv.z bob/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [])
        # errors is a dict {edge: list of errors} or {string: list of errors}
        # We look for 'bad-argrole' in the errors

        found = False
        for _k, v in errors.items():
            if isinstance(v, list):
                for err in v:
                    if isinstance(err, tuple) and err[0] == "bad-argrole":
                        assert len(err) == 3
                        assert err[2] == 2
                        found = True
                        break
        assert found, "Should detect bad argrole 'z' with severity 2"

    def test_valid_junction(self):
        # All C
        edge = hedge("(and/Jx bob/Cp alice/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [])

        # Ignore token matching errors if any (tokens is empty so maybe some?)
        # But structural errors should be absent.
        structural_errors = []
        for _k, v in errors.items():
            if isinstance(v, list):
                for err in v:
                    if isinstance(err, tuple) and err[0] in [
                        "bad-argrole",
                        "bad-junction-types",
                    ]:
                        structural_errors.append(err)
                    if isinstance(err, tuple) and str(err[0]).startswith(
                        "duplicate-argrole"
                    ):
                        structural_errors.append(err)

        assert not structural_errors, "Should be valid junction"

    def test_token_matching_severity(self):
        edge = hedge("(is/Pv.s blue/Ca)")
        tokens = ["is"]  # blue/Ca is not a token at all
        assert edge
        errors = check_parse_correctness(edge, tokens)
        assert [(e[0], e[2]) for e in errors["token-matching"]] == [
            ("atom-not-a-token", 1)
        ]

    def test_percent_encoded_root_matches_its_token(self):
        # The assembler encodes an atom root ('%' -> '%25'); the token does not.
        edge = hedge("(is/Pv.so (el/Md (25/Mq %25/Cc)) mujeres/Cc)")
        tokens = ["el", "25", "%", "is", "mujeres"]
        assert "token-matching" not in check_parse_correctness(edge, tokens)

    def test_overused_root_is_distinguished_from_a_missing_one(self):
        # 'blue' IS a token, but two atoms want it and there is only one.
        edge = hedge("(is/Pv.so blue/Ca blue/Ca)")
        errors = check_parse_correctness(edge, ["blue", "is"])
        assert [(e[0], e[2]) for e in errors["token-matching"]] == [
            ("root-without-token", 1)
        ]

    def test_check_correctness_severity(self):
        # builders can only have two arguments
        edge = hedge("(+/Bp.ma a/Cc b/Cc c/Cc)")
        assert edge
        errors = check_parse_correctness(edge, [])

        found = False
        for _k, v in errors.items():
            for err in v:
                if err[0] == "build-2-args":
                    assert err[2] == 0
                    found = True
        assert found, "Should have build-2-args with severity 0"


def _codes(errors):
    return {code for v in errors.values() for code, _msg, _sev in v}


class TestStrictMode:
    """Strict mode enforces that x-role arguments are specifiers (S)."""

    def test_strict_flags_bare_specification_argument(self):
        # "peter" fills the x slot but is a bare concept, not a specifier
        edge = hedge("(gave/Pv.sox maria/Cp book/Cc peter/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [], strict=True)
        assert "spec-arg-not-specifier" in _codes(errors)

    def test_strict_error_has_severity_zero(self):
        edge = hedge("(gave/Pv.sox maria/Cp book/Cc peter/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [], strict=True)
        severities = [
            sev
            for v in errors.values()
            for code, _msg, sev in v
            if code == "spec-arg-not-specifier"
        ]
        assert severities == [0]

    def test_default_mode_does_not_flag_bare_specification(self):
        # Same edge, default (non-strict) mode: behaviour unchanged.
        edge = hedge("(gave/Pv.sox maria/Cp book/Cc peter/Cp)")
        assert edge
        errors = check_parse_correctness(edge, [])
        assert "spec-arg-not-specifier" not in _codes(errors)

    def test_strict_passes_wrapped_specification(self):
        # Wrapping the recipient in a special trigger atom makes it an S.
        edge = hedge("(gave/Pv.sox maria/Cp book/Cc (_/Ti/. peter/Cp))")
        assert edge
        errors = check_parse_correctness(edge, [], strict=True)
        assert "spec-arg-not-specifier" not in _codes(errors)

    def test_strict_allows_relation_specification(self):
        # A trigger applied to a relation is an S and is accepted in the x slot.
        edge = hedge("(plays/Pv.sox maria/Cp chess/Cc (when/Tt (rains/Pv.s it/Ci)))")
        assert edge
        errors = check_parse_correctness(edge, [], strict=True)
        assert "spec-arg-not-specifier" not in _codes(errors)


class TestNewSubtypeModifierRules:
    """Soft modifier-target checks cover the newly added modifier subtypes."""

    def test_interrogative_determiner_on_predicate_flagged(self):
        edge = hedge("(which/Mw (ran/Pv.sox he/Ci))")
        assert edge
        assert "bad-mw-target" in _codes(check_parse_correctness(edge, []))

    def test_demonstrative_determiner_on_concept_ok(self):
        edge = hedge("(this/Me book/Cc)")
        assert edge
        assert "bad-me-target" not in _codes(check_parse_correctness(edge, []))

    def test_manner_adverb_on_concept_flagged(self):
        edge = hedge("(quickly/Mb sky/Cc)")
        assert edge
        assert "bad-mb-target" in _codes(check_parse_correctness(edge, []))


class TestVocabulary:
    """A parse may only use admissible atom types and special atoms."""

    def test_fully_subtyped_parse_is_clean(self):
        edge = hedge("(is/Pv.so (the/Md sky/Cc) blue/Ca)")
        assert check_vocabulary(edge) == {}

    def test_bare_main_type_is_rejected(self):
        # Parsers must commit to a subtype, even though core hyperbase accepts
        # 'C' as a perfectly valid atom type.
        edge = hedge("(is/Pv.so sky/C blue/Ca)")
        assert "atom-type-unknown" in _codes(check_parse_correctness(edge, []))

    def test_unknown_subtype_is_rejected(self):
        edge = hedge("(is/Pv.so thing/Cz blue/Ca)")
        assert "atom-type-unknown" in _codes(check_parse_correctness(edge, []))

    def test_namespace_does_not_hide_the_type(self):
        edge = hedge("(is/Pv.so sky/Cc/en blue/Ca/en)")
        assert check_vocabulary(edge) == {}

    def test_vocabulary_failure_is_severity_zero(self):
        edge = hedge("(is/Pv.so sky/C blue/Ca)")
        errors = check_vocabulary(edge)
        assert [(c, sev) for v in errors.values() for c, _m, sev in v] == [
            ("atom-type-unknown", 0)
        ]

    def test_known_special_atom_is_clean(self):
        edge = hedge("(+/B.am/. alan/Cp turing/Cp)")
        assert check_vocabulary(edge) == {}

    def test_special_trigger_is_clean(self):
        edge = hedge("(gave/Pv.sox maria/Cp book/Cc (_/Ti/. peter/Cp))")
        assert check_vocabulary(edge) == {}

    def test_unknown_special_atom_is_rejected(self):
        edge = hedge("(&/Jz/. a/Cc b/Cc)")
        assert "special-atom-unknown" in _codes(check_parse_correctness(edge, []))

    def test_token_backed_atom_in_dot_namespace_is_not_a_special_atom(self):
        # '%26/Jx' spells a real token ('&') and is an ordinary atom; only the
        # reserved '.' namespace makes an atom special. The root is written
        # encoded because '&' is reserved -- see the root-canonicality check.
        edge = hedge("(%26/Jx a/Cc b/Cc)")
        assert check_vocabulary(edge) == {}

    def test_special_atom_is_exempt_from_the_atom_type_check(self):
        # ':/J/.' has type 'J', which is not an admissible atom type -- it is
        # checked whole, against the special-atom inventory instead.
        assert check_vocabulary(hedge("(:/J/. a/Cc b/Cc)")) == {}


class TestAlignment:
    """The atom->token alignment, checked position by position.

    Token matching alone is a multiset check; these are the failures only the
    ``tok_pos`` tree can show.
    """

    def test_correct_alignment_is_clean(self):
        edge = hedge("(plays/Pv.so maria/Cp chess/Cc)")
        tokens = ["Maria", "plays", "chess"]
        assert check_alignment(edge, hedge("(1 0 2)"), tokens) == []
        assert "alignment" not in check_parse_correctness(
            edge, tokens, tok_pos=hedge("(1 0 2)")
        )

    def test_structural_atom_may_not_claim_a_token(self):
        # The colon of '19:18' belongs to the ':/Bx.ma' builder that spells it;
        # the ':/J/.' junction stands for a connector the text never writes, so
        # its taking that token leaves the builder with none. The edge itself
        # accounts for the tokens perfectly -- only the alignment is wrong.
        edge = hedge("(:/J/. inés/Cp (:/Bx.ma 19/Cq 18/Cq))")
        tokens = ["Inés", "19", ":", "18"]
        assert "token-matching" not in check_parse_correctness(edge, tokens)
        errors = check_parse_correctness(edge, tokens, tok_pos=hedge("(2 0 (-1 1 3))"))
        assert [e[0] for e in errors["alignment"]] == [
            "structural-atom-aligned",
            "atom-unaligned",
        ]
        assert {e[2] for e in errors["alignment"]} == {1}

    def test_atom_on_the_wrong_token_is_reported(self):
        edge = hedge("(plays/Pv.so maria/Cp chess/Cc)")
        errors = check_alignment(edge, hedge("(1 2 0)"), ["Maria", "plays", "chess"])
        assert [e[0] for e in errors] == [
            "alignment-token-mismatch",
            "alignment-token-mismatch",
        ]

    def test_two_atoms_on_one_token_are_reported(self):
        edge = hedge("(is/Pv.so blue/Ca blue/Ca)")
        errors = check_alignment(edge, hedge("(1 0 0)"), ["blue", "is"])
        assert [e[0] for e in errors] == ["alignment-token-reused"]

    def test_index_outside_the_sentence_is_reported(self):
        edge = hedge("(is/Pv.s blue/Ca)")
        errors = check_alignment(edge, hedge("(1 7)"), ["blue", "is"])
        assert [e[0] for e in errors] == ["alignment-out-of-range"]

    def test_non_parallel_tree_is_reported(self):
        edge = hedge("(is/Pv.so blue/Ca sky/Cc)")
        errors = check_alignment(edge, hedge("(0 1)"), ["blue", "is", "sky"])
        assert [e[0] for e in errors] == ["alignment-shape-mismatch"]

    def test_a_percent_encoded_root_matches_its_token(self):
        # Same decoding as token matching: the atom root is encoded, the token
        # is not, and they are still the same surface form.
        edge = hedge("(is/Pv.so %25/Cc mujeres/Cc)")
        tokens = ["%", "is", "mujeres"]
        assert check_alignment(edge, hedge("(1 0 2)"), tokens) == []

    def test_alignment_is_only_checked_when_a_tree_is_given(self):
        # Every caller that has no tok_pos keeps its old result.
        edge = hedge("(:/J/. inés/Cp (:/Bx.ma 19/Cq 18/Cq))")
        assert check_parse_correctness(edge, ["Inés", "19", ":", "18"]) == {}


class TestArgrolesOnlyOnPredicatesAndBuilders:
    def test_a_trigger_with_argroles_is_rejected(self):
        # 'Atom.type' stops at the '.', and 'Atom.argroles' returns '' for a
        # trigger, so nothing else in the checker can see the trailing part.
        errors = check_parse_correctness(
            hedge("(from/Tr.x (of/Bp.ma respect/Cc imports/Cc))"),
            ["from", "of", "respect", "imports"],
        )
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-argroles-not-allowed" in codes

    def test_a_trailing_dot_with_no_letters_is_rejected_too(self):
        errors = check_parse_correctness(hedge("(du/Tr. a/Cc)"), ["du", "a"])
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-argroles-not-allowed" in codes

    def test_predicates_and_builders_keep_their_argroles(self):
        assert not check_parse_correctness(
            hedge("(plays/Pv.so maria/Cp chess/Cc)"), ["Maria", "plays", "chess"]
        )
        assert not check_parse_correctness(
            hedge("(of/Bp.ma city/Cc berlin/Cp)"), ["city", "of", "Berlin"]
        )

    def test_a_special_trigger_is_not_flagged_for_its_namespace(self):
        # '_/Tt/.' ends in the reserved namespace, not an argrole signature.
        errors = check_parse_correctness(hedge("(_/Tt/. (a/Md day/Cc))"), ["a", "day"])
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-argroles-not-allowed" not in codes


class TestAtomInUnaryEdge:
    def test_an_atom_wrapped_in_a_one_element_edge_is_rejected(self):
        errors = check_parse_correctness(hedge("(in/Tl (101/Cq))"), ["in", "101"])
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-in-unary-edge" in codes

    def test_the_same_edge_without_the_brackets_is_clean(self):
        assert not check_parse_correctness(hedge("(in/Tl 101/Cq)"), ["in", "101"])


class TestModifierToConceptMapping:
    def test_every_target_is_an_admissible_concept_subtype(self):
        for modifier, concept in MODIFIER_TO_CONCEPT.items():
            assert modifier[0] == "M", modifier
            assert is_admissible_atom_type(modifier), modifier
            assert is_admissible_atom_type(concept), concept
            assert concept[0] == "C", concept

    def test_it_covers_every_modifier_subtype(self):
        modifiers = {t for t in ATOM_TYPES if t[0] == "M"}
        assert set(MODIFIER_TO_CONCEPT) == modifiers

    def test_the_applied_set_is_a_subset_of_the_table(self):
        assert set(MODIFIER_TO_CONCEPT) >= CONVERTIBLE_MODIFIERS

    def test_the_two_false_friends_do_not_keep_their_letter(self):
        # Mg is degree but Cg is gerund; Mp is possessive but Cp is proper.
        assert MODIFIER_TO_CONCEPT["Mg"] != "Cg"
        assert MODIFIER_TO_CONCEPT["Mp"] != "Cp"

    def test_the_determiner_class_is_defined_but_not_applied(self):
        # It maps exactly, but a determiner is never part of a compound.
        for determiner in ("Md", "Me", "Mw"):
            assert determiner in MODIFIER_TO_CONCEPT
            assert determiner not in CONVERTIBLE_MODIFIERS


class TestAtomRootIsCanonical:
    def test_a_raw_reserved_character_is_rejected(self):
        # build_atom -- the only thing that mints an atom from a token --
        # encodes unconditionally, so '%/Cc' is a form no parse assembles into.
        errors = check_parse_correctness(
            hedge("(in/Bp.ma (50/Mq %/Cc) cells/Cc)"), ["50", "%", "in", "cells"]
        )
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-root-not-canonical" in codes

    def test_the_encoded_form_is_clean(self):
        assert not check_parse_correctness(
            hedge("(in/Bp.ma (50/Mq %25/Cc) cells/Cc)"), ["50", "%", "in", "cells"]
        )

    def test_an_already_encoded_root_is_not_re_encoded(self):
        # '%25' must not be read as needing to become '%2525'.
        assert not check_parse_correctness(
            hedge("(%2f/Bx.am mg/Cc dl/Cc)"), ["mg", "/", "dl"]
        )

    def test_an_uppercase_root_is_rejected(self):
        errors = check_parse_correctness(hedge("(the/Md CE/Cp)"), ["the", "CE"])
        codes = [c for issues in errors.values() for c, _, _ in issues]
        assert "atom-root-not-canonical" in codes


class TestConnectiveSymbolCoverage:
    def _codes(self, edge, tokens, tok_pos=None, text=None):
        errors = check_parse_correctness(
            hedge(edge), tokens, tok_pos=hedge(tok_pos) if tok_pos else None, text=text
        )
        return [c for issues in errors.values() for c, _, _ in issues]

    def test_a_structural_connector_over_a_spelled_symbol_is_rejected(self):
        # "3-5": the hyphen is spelled out, so ':/J/.' makes it vanish.
        assert "connective-symbol-dropped" in self._codes(
            "(:/J/. 3/Cq 5/Cq)", ["3", "-", "5"], "(-1 0 2)", "3-5"
        )

    def test_a_modifier_that_swallowed_the_symbol_is_rejected(self):
        assert "connective-symbol-dropped" in self._codes(
            "(low/Ma density/Cc)", ["low", "-", "density"], "(0 2)", "low-density"
        )

    def test_the_repaired_form_is_clean(self):
        assert "connective-symbol-dropped" not in self._codes(
            "(-/Jx 3/Cq 5/Cq)", ["3", "-", "5"], "(1 0 2)", "3-5"
        )
        assert "connective-symbol-dropped" not in self._codes(
            "(-/Bx.am low/Ca density/Cc)",
            ["low", "-", "density"],
            "(1 0 2)",
            "low-density",
        )

    def test_a_claimed_symbol_is_not_reported(self):
        # ':' belongs to the ':/Bx.ma' beside the junction, not to the junction.
        assert "connective-symbol-dropped" not in self._codes(
            "(:/J/. inés/Cp (:/Bx.ma 19/Cq 18/Cq))",
            ["Inés", "19", ":", "18"],
            "(-1 0 (2 1 3))",
            "Inés 19:18",
        )

    def test_nothing_is_reported_without_tok_pos(self):
        # The check needs the argument spans, like check_alignment.
        assert "connective-symbol-dropped" not in self._codes(
            "(:/J/. 3/Cq 5/Cq)", ["3", "-", "5"]
        )

    def test_an_ambiguous_gap_is_left_alone(self):
        # "May 03 2017": several gaps, so no rule can say which symbol the
        # connector stands for. A real defect, but not one a repair could act on.
        assert "connective-symbol-dropped" not in self._codes(
            "(:/J/. may/Cp 03/Cq 2017/Cq)",
            ["May", "03", ",", "2017", "-", "x"],
            "(-1 0 1 3)",
            "May 03, 2017 - x",
        )

    def test_punctuation_needs_the_flush_test_and_therefore_the_text(self):
        spaced = ["205", "Live", ".", "Neville"]
        # Spaced: a sentence period, left alone.
        assert "connective-symbol-dropped" not in self._codes(
            "(:/J/. live/Cp neville/Cp)", spaced, "(-1 1 3)", "205 Live. Neville"
        )
        # Flush: part of a number, so it joins.
        assert "connective-symbol-dropped" in self._codes(
            "(+/B.am/. 19/Cq 3/Cq)", ["19", ".", "3"], "(-1 0 2)", "19.3"
        )
        # Without text the two cannot be told apart, so neither is reported.
        assert "connective-symbol-dropped" not in self._codes(
            "(+/B.am/. 19/Cq 3/Cq)", ["19", ".", "3"], "(-1 0 2)"
        )

    def test_a_never_punctuation_symbol_needs_no_text(self):
        assert "connective-symbol-dropped" in self._codes(
            "(:/J/. 3/Cq 5/Cq)", ["3", "-", "5"], "(-1 0 2)"
        )


class _StubParser(Parser):
    """A Parser that contributes exactly the checks it was handed.

    ``correctness_checks`` raises instead of returning when *raises* is set, so
    the hook's own failure can be tested apart from a check's.
    """

    def __init__(self, checks=None, raises=False):
        super().__init__()
        self._checks = list(checks or [])
        self._raises = raises

    def correctness_checks(self):
        if self._raises:
            raise RuntimeError("hook exploded")
        return self._checks


def _codes(errors):
    """Every error code in a result, regardless of which key it landed under."""
    return [code for issues in errors.values() for code, _, _ in issues]


# A known-bad edge: 'chess' is never used, so the built-ins always have
# something to say about it. Used to prove extensions never subtract.
BAD_EDGE = "(plays/Pv.s maria/Cp)"
BAD_TOKENS = ["Maria", "plays", "chess"]


class TestParserSuppliedChecks:
    """Checks a parser plugin adds on top of the built-in gate."""

    def test_parser_none_is_the_old_behaviour(self):
        edge, tokens = hedge(BAD_EDGE), BAD_TOKENS
        assert check_parse_correctness(edge, tokens, parser=None) == (
            check_parse_correctness(edge, tokens)
        )

    def test_a_parser_with_no_checks_changes_nothing(self):
        edge, tokens = hedge(BAD_EDGE), BAD_TOKENS
        assert check_parse_correctness(edge, tokens, parser=_StubParser()) == (
            check_parse_correctness(edge, tokens)
        )

    def test_a_check_adds_its_errors(self):
        def check(ctx):
            return {"mine": [("my-code", "my message", 2)]}

        errors = check_parse_correctness(
            hedge("(plays/Pv.so maria/Cp chess/Cc)"),
            ["Maria", "plays", "chess"],
            parser=_StubParser([check]),
        )
        assert errors["mine"] == [("my-code", "my message", 2)]

    def test_errors_merge_onto_a_shared_string_key(self):
        def check(ctx):
            return {"token-matching": [("my-code", "my message", 1)]}

        errors = check_parse_correctness(
            hedge(BAD_EDGE), BAD_TOKENS, parser=_StubParser([check])
        )
        codes = [code for code, _, _ in errors["token-matching"]]
        # The built-in finding survives and the extension's is appended after it.
        assert "token-unused" in codes
        assert codes[-1] == "my-code"

    def test_errors_merge_onto_a_shared_subedge_key(self):
        # 'Cz' is not an admissible subtype, so the atom itself is a key.
        edge = hedge("(plays/Pv.so maria/Cp chess/Cz)")
        tokens = ["Maria", "plays", "chess"]
        builtin = check_parse_correctness(edge, tokens)
        # Pick a subedge the built-ins already reported on.
        key = next(k for k in builtin if not isinstance(k, str))

        def check(ctx):
            return {key: [("my-code", "my message", 3)]}

        errors = check_parse_correctness(edge, tokens, parser=_StubParser([check]))
        assert len(errors[key]) == len(builtin[key]) + 1
        assert errors[key][: len(builtin[key])] == builtin[key]

    def test_a_check_cannot_remove_built_in_errors(self):
        def silent(ctx):
            return {}

        edge, tokens = hedge(BAD_EDGE), BAD_TOKENS
        assert check_parse_correctness(
            edge, tokens, parser=_StubParser([silent])
        ) == check_parse_correctness(edge, tokens)

    def test_the_context_carries_the_whole_parse(self):
        seen = []

        def check(ctx):
            seen.append(ctx)
            return {}

        check_parse_correctness(
            hedge("(:/J/. 3/Cq 5/Cq)"),
            ["3", "-", "5"],
            strict=True,
            tok_pos=hedge("(-1 0 2)"),
            text="3-5",
            parser=_StubParser([check]),
        )
        (ctx,) = seen
        assert str(ctx.edge) == "(:/J/. 3/Cq 5/Cq)"
        assert ctx.tokens == ["3", "-", "5"]
        assert str(ctx.tok_pos) == "(-1 0 2)"
        assert ctx.text == "3-5"
        assert ctx.strict is True

    def test_tok_pos_and_text_are_none_when_absent(self):
        seen = []

        def check(ctx):
            seen.append(ctx)
            return {}

        check_parse_correctness(
            hedge("(plays/Pv.so maria/Cp chess/Cc)"),
            ["Maria", "plays", "chess"],
            parser=_StubParser([check]),
        )
        (ctx,) = seen
        assert ctx.tok_pos is None
        assert ctx.text is None
        assert ctx.strict is False

    def test_a_raising_check_is_reported_not_swallowed(self):
        def boom(ctx):
            raise RuntimeError("kaboom")

        errors = check_parse_correctness(
            hedge(BAD_EDGE), BAD_TOKENS, parser=_StubParser([boom])
        )
        (issue,) = errors["parser-checks"]
        code, message, severity = issue
        assert code == "check-failed"
        assert severity == 0
        assert "boom" in message
        assert "RuntimeError" in message
        assert "kaboom" in message
        # The built-in findings are untouched by the failure.
        assert "token-unused" in _codes(errors)

    def test_a_raising_hook_is_reported_not_propagated(self):
        errors = check_parse_correctness(
            hedge(BAD_EDGE), BAD_TOKENS, parser=_StubParser(raises=True)
        )
        (issue,) = errors["parser-checks"]
        assert issue[0] == "check-failed"
        assert "hook exploded" in issue[1]

    def test_one_bad_check_does_not_stop_the_others(self):
        def boom(ctx):
            raise RuntimeError("kaboom")

        def good(ctx):
            return {"mine": [("my-code", "my message", 2)]}

        errors = check_parse_correctness(
            hedge(BAD_EDGE), BAD_TOKENS, parser=_StubParser([boom, good])
        )
        assert errors["mine"] == [("my-code", "my message", 2)]
        assert "check-failed" in _codes(errors)

    def test_a_malformed_return_is_reported_and_discarded(self):
        cases = [
            ("not a dict", lambda ctx: [("my-code", "my message", 1)]),
            ("a two-tuple", lambda ctx: {"mine": [("my-code", "my message")]}),
            ("a non-int severity", lambda ctx: {"mine": [("c", "m", "bad")]}),
            ("a non-str code", lambda ctx: {"mine": [(1, "m", 1)]}),
            ("a bad key", lambda ctx: {1: [("c", "m", 1)]}),
            ("a non-list value", lambda ctx: {"mine": ("c", "m", 1)}),
        ]
        for label, check in cases:
            errors = check_parse_correctness(
                hedge(BAD_EDGE), BAD_TOKENS, parser=_StubParser([check])
            )
            (issue,) = errors["parser-checks"]
            assert issue[0] == "check-malformed", label
            assert issue[2] == 0, label
            # Nothing the malformed check reported was merged.
            assert "mine" not in errors, label
            assert "my-code" not in _codes(errors), label
            # The built-ins still ran.
            assert "token-unused" in _codes(errors), label

    def test_a_check_runs_even_when_the_edge_is_empty(self):
        # An unparseable edge is exactly the case a parser may want to flag.
        def check(ctx):
            return {"mine": [("my-code", "my message", 0)]}

        errors = check_parse_correctness(
            hedge("(*/Cx)"), ["x"], parser=_StubParser([check])
        )
        assert errors["mine"] == [("my-code", "my message", 0)]

    def test_the_default_hook_supplies_nothing(self):
        assert Parser().correctness_checks() == []
