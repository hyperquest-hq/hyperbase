"""Error-path tests for check_correctness.

Tests truly broken structures that exercise every error branch in
correctness.py, including malformed edges, invalid types, wrong arities,
and recursive error propagation.
"""

from hyperbase.builders import hedge
from hyperbase.correctness import check_correctness
from hyperbase.hyperedge import Atom, Hyperedge


class TestAtomTypeErrors:
    """check_correctness on atoms with invalid types."""

    def test_invalid_atom_type_R(self):
        atom = Atom("thing/R")
        errors = check_correctness(atom)
        assert atom in errors
        codes = [e[0] for e in errors[atom]]
        assert "bad-atom-type" in codes

    def test_invalid_atom_type_S(self):
        atom = Atom("thing/S")
        errors = check_correctness(atom)
        assert atom in errors
        codes = [e[0] for e in errors[atom]]
        assert "bad-atom-type" in codes

    def test_valid_atom_types_produce_no_errors(self):
        for t in ["C", "P", "M", "B", "T", "J"]:
            atom = Atom(f"thing/{t}")
            errors = check_correctness(atom)
            assert atom not in errors, f"Type {t} should be valid"

    def test_completely_unknown_type(self):
        atom = Atom("thing/Z")
        errors = check_correctness(atom)
        assert atom in errors


class TestConnectorTypeErrors:
    """Edges whose connector has an invalid type."""

    def test_concept_as_connector(self):
        """Concept atom as connector should fail."""
        edge = hedge("(bob/C alice/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "conn-bad-type" in codes

    def test_relation_as_connector(self):
        """R-type as connector is not valid for edge connector."""
        # Build manually since R isn't a valid connector
        edge = Hyperedge((Atom("rel/R"), Atom("a/C")))
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "conn-bad-type" in codes


class TestModifierErrors:
    """Modifier edges must have exactly 1 argument."""

    def test_modifier_zero_args(self):
        """(mod/M) — modifier with no argument."""
        edge = Hyperedge((Atom("big/M"),))
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "mod-1-arg" in codes

    def test_modifier_two_args(self):
        """(mod/M a/C b/C) — modifier with two arguments."""
        edge = hedge("(big/M thing/C other/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "mod-1-arg" in codes

    def test_modifier_one_arg_valid(self):
        """(mod/M a/C) — valid modifier."""
        edge = hedge("(big/M thing/C)")
        errors = check_correctness(edge)
        assert edge not in errors


class TestBuilderErrors:
    """Builder edges must have exactly 2 arguments, both of type C."""

    def test_builder_one_arg(self):
        edge = hedge("(+/B.m a/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "build-2-args" in codes

    def test_builder_three_args(self):
        edge = hedge("(+/B.ma a/C b/C c/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "build-2-args" in codes

    def test_builder_wrong_arg_type(self):
        """Builder with a predicate argument instead of concept."""
        edge = hedge("(+/B.ma is/P a/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "build-arg-bad-type" in codes

    def test_builder_valid(self):
        edge = hedge("(+/B.ma a/C b/C)")
        errors = check_correctness(edge)
        assert edge not in errors


class TestTriggerErrors:
    """Trigger edges must have exactly 1 argument of type C or R."""

    def test_trigger_zero_args(self):
        edge = Hyperedge((Atom("to/T"),))
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "trig-1-arg" in codes

    def test_trigger_two_args(self):
        edge = hedge("(to/T place/C time/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "trig-1-arg" in codes

    def test_trigger_wrong_arg_type(self):
        """Trigger with a predicate argument."""
        edge = hedge("(to/T is/P)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "trig-bad-arg-type" in codes

    def test_trigger_valid_concept(self):
        edge = hedge("(to/T place/C)")
        errors = check_correctness(edge)
        assert edge not in errors

    def test_trigger_valid_relation(self):
        """Trigger with R-type argument should be valid."""
        edge = Hyperedge((Atom("to/T"), hedge("(is/P.s bob/C)")))
        errors = check_correctness(edge)
        # The trigger itself should have no errors
        codes = [e[0] for e in errors.get(edge, [])]
        assert "trig-bad-arg-type" not in codes


class TestPredicateErrors:
    """Predicate argument type checking."""

    def test_predicate_modifier_arg(self):
        """Predicate with a modifier argument (M is not C/R/S)."""
        edge = hedge("(is/P.s big/M)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "pred-arg-bad-type" in codes

    def test_predicate_valid_args(self):
        """Predicate with C and R args should be valid."""
        edge = hedge("(is/P.sc bob/C happy/C)")
        errors = check_correctness(edge)
        assert edge not in errors


class TestConjunctionErrors:
    """Conjunction edges must have at least 2 arguments."""

    def test_conjunction_one_arg(self):
        edge = hedge("(and/J bob/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "conj-2-args-min" in codes

    def test_conjunction_two_args_valid(self):
        edge = hedge("(and/J bob/C alice/C)")
        errors = check_correctness(edge)
        assert edge not in errors


class TestArgroleErrors:
    """Argrole validation on predicates and builders."""

    def test_predicate_invalid_argrole(self):
        """'z' is not a valid predicate argrole."""
        edge = hedge("(is/P.z bob/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "pred-bad-arg-role" in codes

    def test_builder_invalid_argrole(self):
        """'s' is not a valid builder argrole (only m and a)."""
        edge = hedge("(+/B.sa a/C b/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "build-bad-arg-role" in codes

    def test_argrole_count_mismatch(self):
        """Argrole count doesn't match argument count."""
        edge = hedge("(is/P.sco bob/C happy/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "bad-num-argroles" in codes

    def test_duplicate_special_argrole(self):
        """Duplicate 's' argrole should be flagged."""
        edge = hedge("(is/P.ss bob/C alice/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "argrole-s-1-max" in codes

    def test_no_argroles_on_predicate(self):
        """Predicate without argroles should be flagged."""
        edge = hedge("(is/P bob/C)")
        errors = check_correctness(edge)
        assert edge in errors
        codes = [e[0] for e in errors[edge]]
        assert "no-argroles" in codes


class TestRecursiveErrorPropagation:
    """Errors in deeply nested subedges should propagate to root."""

    def test_error_in_nested_subedge(self):
        """A broken inner edge should appear in the error dict."""
        # Inner: (big/M a/C b/C) — modifier with 2 args
        edge = hedge("(is/P.sc (big/M a/C b/C) happy/C)")
        errors = check_correctness(edge)
        inner = hedge("(big/M a/C b/C)")
        assert inner in errors
        codes = [e[0] for e in errors[inner]]
        assert "mod-1-arg" in codes

    def test_multiple_errors_in_tree(self):
        """Multiple broken subedges should all appear."""
        # Outer: predicate with bad arg type (M)
        # Inner: builder with 3 args
        edge = hedge("(is/P.sc (+/B.ma a/C b/C c/C) happy/C)")
        errors = check_correctness(edge)
        # The outer edge should flag pred-arg-bad-type for the builder connector
        # The inner builder should flag build-2-args
        all_codes = set()
        for errs in errors.values():
            for e in errs:
                all_codes.add(e[0])
        assert "build-2-args" in all_codes

    def test_deeply_nested_error(self):
        """Error 5 levels deep should still be found."""
        edge = hedge(
            "(is/P.sc (the/M (big/M (very/M (super/M (bad/M a/C b/C))))) happy/C)"
        )
        errors = check_correctness(edge)
        # The innermost (bad/M a/C b/C) has too many args
        all_codes = set()
        for errs in errors.values():
            for e in errs:
                all_codes.add(e[0])
        assert "mod-1-arg" in all_codes
