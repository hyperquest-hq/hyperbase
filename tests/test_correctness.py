from hyperbase.builders import hedge
from hyperbase.parsers.correctness import badness_check, filter_alphanumeric_strings


class TestFilterAlphanumericStrings:
    """Tests for filter_alphanumeric_strings function"""

    def test_filter_basic(self):
        """Test basic filtering"""
        strings = ["hello", "(", ")", "world"]
        result = filter_alphanumeric_strings(strings)
        assert result == ["hello", "world"]

    def test_filter_mixed(self):
        """Test filtering with mixed content"""
        strings = ["test/C", "...", "word123", "   ", ""]
        result = filter_alphanumeric_strings(strings)
        # Special characters removed: "test/C" -> "testc", "word123" -> "word123"
        assert result == ["testc", "word123"]

    def test_filter_empty_list(self):
        """Test with empty list"""
        assert filter_alphanumeric_strings([]) == []

    def test_filter_all_special(self):
        """Test with only special characters"""
        strings = ["(", ")", "/", ":", "..."]
        result = filter_alphanumeric_strings(strings)
        assert result == []

    def test_filter_all_alphanumeric(self):
        """Test with all alphanumeric strings"""
        strings = ["abc", "123", "test"]
        result = filter_alphanumeric_strings(strings)
        assert result == strings

    def test_remove_special_characters(self):
        """Test that special characters are removed"""
        strings = ["hello!", "test-123", "foo/bar", "a.b.c"]
        result = filter_alphanumeric_strings(strings)
        assert result == ["hello", "test123", "foobar", "abc"]

    def test_lowercase_conversion(self):
        """Test that strings are converted to lowercase"""
        strings = ["HELLO", "TeSt", "WoRlD123"]
        result = filter_alphanumeric_strings(strings)
        assert result == ["hello", "test", "world123"]

    def test_mixed_case_and_special(self):
        """Test with mixed case and special characters"""
        strings = ["Test/C", "WORD-123", "Foo.Bar"]
        result = filter_alphanumeric_strings(strings)
        assert result == ["testc", "word123", "foobar"]


class TestBadnessCheck:
    """Tests for badness_check function"""

    def test_valid_parse_matching_tokens(self):
        """Test with valid parse and matching tokens"""
        valid_parse = "(is/P.sc (the/M sky/C) blue/C)"
        tokens = ["the", "sky", "is", "blue"]
        edge = hedge(valid_parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_with_original_text(self):
        """Test that passing original text orders roots correctly"""
        valid_parse = "(is/P.sc (the/M sky/C) blue/C)"
        tokens = ["the", "sky", "is", "blue"]
        edge = hedge(valid_parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_contiguous_token_sequence(self):
        """Test that contiguous sequences of roots are recognized"""
        # Parse with "newyork" as a single root
        parse = "(is/P.s newyork/C)"
        # Input has "new" and "york" as separate tokens
        tokens = ["new", "york", "is"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_valid_parse_missing_token(self):
        """Test when parse doesn't use all tokens"""
        parse = "(is/P.sc blue/C)"
        tokens = ["sky", "is", "blue"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        # Should have error: "sky" not used
        assert len(errors) > 0

    def test_valid_parse_extra_root(self):
        """Test when parse uses root not in tokens"""
        parse = "(is/P.sc (the/M sky/C) blue/C)"
        tokens = ["sky", "is", "blue"]  # Missing "the"
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        # Should have error: "the" used but not in tokens
        assert len(errors) > 0

    def test_token_count_mismatch(self):
        """Test when token appears multiple times"""
        parse = "(is/P.s blue/C)"
        tokens = ["blue", "blue", "is"]  # "blue" appears twice
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        # Should have error: "blue" used less than it appears
        assert len(errors) > 0

    def test_special_characters_filtered(self):
        """Test that special characters in tokens are filtered"""
        parse = "(is/P.s blue/C)"
        tokens = ["(", "is", "blue", ")"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_empty_tokens_list(self):
        """Test with empty tokens list"""
        parse = "(is/P.s blue/C)"
        tokens = []
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        # Should have errors: roots used but no tokens
        assert len(errors) > 0

    def test_tokenization_mismatch_us_case(self):
        """Test U.S. case: tokens ['u', 's'] should match root 'us' even if 's' appears elsewhere"""
        # Simplified version of: Russia regrets U.S. not pressing charges over boy's death
        # Tokens: 'u' and 's' (from U.S.) and 's' (from boy's)
        # Root: 'us' (combined) and 's' (possessive marker)
        parse = "(regrets/P.sr russia/C (pressing/P.so us/C (over/B.ma charges/C (s/B.am boy/C death/C))))"
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
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_tokenization_mismatch_us_case_error1(self):
        """Test U.S. case: tokens ['u', 's'] should match root 'us' even if 's' appears elsewhere (error 1)"""
        parse = "(regrets/P.sr russia/C (pressing/P.so us/C (over/B.ma charges/C (s/B.am boy/C death/C))))"
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
        errors = badness_check(edge, tokens)
        assert len(errors) > 0

    def test_tokenization_mismatch_us_case_error2(self):
        """Test U.S. case: tokens ['u', 's'] should match root 'us' even if 's' appears elsewhere (error 2)"""
        parse = "(regrets/P.sr russia/C (pressing/P us/C (over/B.ma charges/C (s/B.am boy/C death/C))))"
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
        errors = badness_check(edge, tokens)
        assert len(errors) > 0

    def test_tokenization_combined_token_case(self):
        """Test '1m' case: token '1m' should match root sequence ['1', 'm']"""
        # Simplified version of: RAF flies 1m euros to Cyprus
        # Token: '1m' (combined)
        # Roots: '1' and 'm' (separate)
        parse = "(flies/P.sxox raf/C (1/M m/C) euros/C (to/T cyprus/C))"
        tokens = ["raf", "flies", "1m", "euros", "to", "cyprus"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)

        # Should successfully match token '1m' with root sequence ['1', 'm']
        assert len(errors) == 0

    def test_overlapping_substring_case(self):
        """Test Malawi/37m case: avoid matching 'm' inside 'malawi'"""
        # Simplified version of: Malawi gets 37m in UK health aid
        # Token '37m' should match roots ['37', 'm']
        # Root 'm' should NOT match the 'm' inside 'malawi'
        parse = "(gets/P.sox malawi/C (37/M m/C) (in/T (uk/M (health/M aid/C))))"
        tokens = ["malawi", "gets", "37m", "in", "uk", "health", "aid"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_contraction_case_d(self):
        """Test case (d): multi-token to multi-root concatenation matching"""
        # Don't contraction case: tokens ['don', 't'] should match roots ['do', 'nt']
        parse = (
            "((off/Ml/en (do/Mv.-i-----/en (n't/Mn/en rip/P!.o.-i-----/en))) me/Ci/en)"
        )
        tokens = ["don", "t", "rip", "me", "off"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_simple_contraction_case(self):
        """Test a simple contraction case"""
        # Simple contraction: tokens ['don', 't'] should match roots ['do', 'nt']
        parse = "((do/Mv.-i-----/en (n't/Mn/en is/P.c)) blue/C)"
        tokens = ["don", "t", "is", "blue"]
        edge = hedge(parse)
        assert edge
        errors = badness_check(edge, tokens)
        assert len(errors) == 0

    def test_valid_edge(self):
        edge = hedge("(is/P.s bob/C)")
        assert edge
        errors = badness_check(edge, [])

        # Filter out token matching errors
        structural_errors = {k: v for k, v in errors.items() if k != "token-matching"}
        assert not structural_errors

    def test_invalid_argrole(self):
        # 'z' is not in mspaoixtjr
        edge = hedge("(is/P.z bob/C)")
        assert edge
        errors = badness_check(edge, [])
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

    def test_duplicate_argrole(self):
        # 's' appearing twice
        edge = hedge("(is/P.ss bob/C alice/C)")
        assert edge
        errors = badness_check(edge, [])

        found = False
        for _k, v in errors.items():
            if isinstance(v, list):
                for err in v:
                    if isinstance(err, tuple) and err[0] == "argrole-s-1-max":
                        assert len(err) == 3
                        assert err[2] == 0
                        found = True
                        break
        assert found, "Should detect duplicate argrole 's'"

    def test_invalid_junction_mixed(self):
        # Mixed types C and R
        # (and/J (bob/C) (runs/P.s bob/C))
        edge = hedge("(and/J bob/C (runs/P.s bob/C))")
        assert edge
        errors = badness_check(edge, [])

        found = False
        for _k, v in errors.items():
            if isinstance(v, list):
                for err in v:
                    if isinstance(err, tuple) and err[0] == "bad-junction-types":
                        assert len(err) == 3
                        assert err[2] == 3
                        found = True
                        break
        assert found, "Should detect bad junction types with severity 3"

    def test_valid_junction(self):
        # All C
        edge = hedge("(and/J bob/C alice/C)")
        assert edge
        errors = badness_check(edge, [])

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
        edge = hedge("(is/P.s blue/C)")
        tokens = ["is"]  # blue/C is missing
        assert edge
        errors = badness_check(edge, tokens)

        found = False
        if "token-matching" in errors:
            for err in errors["token-matching"]:
                if err[0] == "root-without-token":
                    assert err[2] == 1
                    found = True
        assert found, "Should have root-without-token with severity 1"

    def test_check_correctness_severity(self):
        # builders can only have two arguments
        edge = hedge("(+/B a/C b/C c/C)")
        assert edge
        errors = badness_check(edge, [])

        found = False
        for _k, v in errors.items():
            for err in v:
                if err[0] == "build-2-args":
                    assert err[2] == 0
                    found = True
        assert found, "Should have build-2-args with severity 0"
