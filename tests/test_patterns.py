import unittest

from hyperbase import hedge
from hyperbase.patterns import (match_pattern, edge_matches_pattern, is_wildcard, is_pattern, is_full_pattern,
                                 apply_vars, is_unordered_pattern, common_pattern, more_general,
                                 is_variable, contains_variable, merge_patterns)


class TestPatterns(unittest.TestCase):
    def test_is_wildcard1(self):
        self.assertFalse(is_wildcard(hedge('thing/C')))

    def test_is_wildcard2(self):
        self.assertTrue(is_wildcard(hedge('*/C')))

    def test_is_wildcard3(self):
        self.assertTrue(is_wildcard(hedge('./M')))

    def test_is_wildcard4(self):
        self.assertTrue(is_wildcard(hedge('...')))

    def test_is_wildcard5(self):
        self.assertTrue(is_wildcard(hedge('VARIABLE/C')))

    def test_is_wildcard6(self):
        self.assertTrue(is_wildcard(hedge('*VARIABLE/C')))

    def test_is_wildcard7(self):
        self.assertFalse(is_wildcard(hedge('go/Pd.so')))

    def test_is_wildcard8(self):
        self.assertFalse(is_wildcard(hedge('go/Pd.{so}')))

    def test_is_wildcard9(self):
        self.assertFalse(is_wildcard(hedge('(is/P.sc */M */Cn.s)')))

    def test_is_pattern1(self):
        self.assertFalse(is_pattern(hedge("('s/Bp.am zimbabwe/M economy/Cn.s)")))

    def test_is_pattern2(self):
        self.assertTrue(is_pattern(hedge("('s/Bp.am * economy/Cn.s)")))

    def test_is_pattern3(self):
        self.assertTrue(is_pattern(hedge("('s/Bp.am * ...)")))

    def test_is_pattern4(self):
        self.assertFalse(is_pattern(hedge('thing/C')))

    def test_is_pattern5(self):
        self.assertTrue(is_pattern(hedge('(*)')))

    def test_is_pattern6(self):
        self.assertFalse(is_pattern(hedge('go/Pd.so')))

    def test_is_pattern7(self):
        self.assertTrue(is_pattern(hedge('go/Pd.{so}')))

    def test_is_pattern8(self):
        self.assertFalse(is_pattern(hedge('(is/P.sc x/C y/Cn.s)')))

    def test_is_pattern9(self):
        self.assertTrue(is_pattern(hedge('(is/P.{sc} x/C y/Cn.s)')))

    def test_is_full_pattern1(self):
        self.assertFalse(is_full_pattern(hedge("('s/Bp.am zimbabwe/M economy/Cn.s)")))

    def test_is_full_pattern2(self):
        self.assertFalse(is_full_pattern(hedge("('s/Bp.am * economy/Cn.s)")))

    def test_is_full_pattern3(self):
        self.assertFalse(is_full_pattern(hedge("('s/Bp.am * ...)")))

    def test_is_full_pattern4(self):
        self.assertFalse(is_full_pattern(hedge('thing/C')))

    def test_is_full_pattern5(self):
        self.assertTrue(is_full_pattern(hedge('(*)')))

    def test_is_full_pattern6(self):
        self.assertTrue(is_full_pattern(hedge('(* * *')))

    def test_is_full_pattern7(self):
        self.assertTrue(is_full_pattern(hedge('(* * * ...)')))

    def test_is_full_pattern8(self):
        self.assertTrue(is_full_pattern(hedge('(. * (*) ...)')))

    def test_is_unordered_pattern1(self):
        self.assertFalse(is_unordered_pattern(hedge("('s/Bp.am * ...)")))

    def test_is_unordered_pattern2(self):
        self.assertFalse(is_unordered_pattern(hedge('thing/C')))

    def test_is_unordered_pattern3(self):
        self.assertFalse(is_unordered_pattern(hedge('*')))

    def test_is_unordered_pattern4(self):
        self.assertFalse(is_unordered_pattern(hedge('go/Pd.so')))

    def test_is_unordered_pattern5(self):
        self.assertTrue(is_unordered_pattern(hedge('go/Pd.{so}')))

    def test_is_unordered_pattern6(self):
        self.assertFalse(is_unordered_pattern(hedge('(is/P.sc x/C y/Cn.s)')))

    def test_is_unordered_pattern7(self):
        self.assertTrue(is_unordered_pattern(hedge('(is/P.{sc} x/C y/Cn.s)')))

    def test_is_unordered_pattern8(self):
        self.assertTrue(is_unordered_pattern(hedge('((not/M is/P.{sc}) x/C y/Cn.s)')))

    def test_main_apply_vars(self):
        edge = hedge('(PRED zimbabwe/C PROP)')
        nedge = apply_vars(edge, {'PRED': hedge('is/P'), 'PROP': hedge('(sehr/M schön/C)')})
        self.assertEqual(nedge, hedge('(is/P zimbabwe/C (sehr/M schön/C))'))

    def test_match_pattern_simple1(self):
        self.assertEqual(match_pattern('(a b)', '(a b)'), [{}])

    def test_match_pattern_simple2(self):
        self.assertEqual(match_pattern('(a b)', '(a a)'), [])

    def test_match_pattern_wildcard1(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s *X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_wildcard2(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s *)'), [{}])

    def test_match_pattern_wildcard3(self):
        self.assertEqual(match_pattern('(was/Pd hyperbase /Cp.s great/C)', '(is/Pd hyperbase/Cp.s *X)'), [])

    def test_match_pattern_atomic_wildcard1(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s .PROP)'),
                         [{'PROP': hedge('great/C')}])

    def test_match_pattern_atomic_wildcard2(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s .)'), [{}])

    def test_match_pattern_atomic_wildcard3(self):
        self.assertEqual(match_pattern('(was/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s .PROP)'), [])

    def test_match_pattern_atomic_wildcard4(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s (fairly/M great/C))', '(is/Pd hyperbase/Cp.s .PROP)'),
                         [])

    def test_match_pattern_non_atomic_wildcard1(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s (fairly/M great/C))', '(is/Pd hyperbase/Cp.s (PROP))'),
                         [{'PROP': hedge('(fairly/M great/C)')}])

    def test_match_pattern_non_atomic_wildcard2(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s (fairly/M great/C))', '(is/Pd hyperbase/Cp.s (*))'),
                         [{}])

    def test_match_pattern_non_atomic_wildcard3(self):
        self.assertEqual(match_pattern('(was/Pd hyperbase/Cp.s (fairly/M great/C))', '(is/Pd hyperbase/Cp.s (PROP))'),
                         [])

    def test_match_pattern_non_atomic_wildcard4(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s (PROP))'), [])

    def test_match_pattern_open_ended1(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s *X ...)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_open_ended2(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd hyperbase/Cp.s * ...)'), [{}])

    def test_match_pattern_open_ended3(self):
        self.assertEqual(match_pattern('(was/Pd hyperbase /Cp.s great/C)', '(is/Pd hyperbase/Cp.s *X ...)'), [])

    def test_match_pattern_open_ended4(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd .OBJ ...)'),
                         [{'OBJ': hedge('hyperbase/Cp.s')}])

    def test_match_pattern_open_ended5(self):
        self.assertEqual(match_pattern('(is/Pd hyperbase/Cp.s great/C)', '(is/Pd .OBJ)'), [])

    def test_match_pattern_argroles1(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.sc hyperbase/Cp.s *X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles2(self):
        self.assertEqual(match_pattern('(is/Pd.cs great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s *X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles3(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{scx} hyperbase/Cp.s *X *Y)'), [])

    def test_match_pattern_argroles4(self):
        self.assertEqual(
            match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s *X ...)'),
            [{'X': hedge('great/C')}])

    def test_match_pattern_argroles5(self):
        self.assertEqual(
            match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s *X)'),
            [{'X': hedge('great/C')}])

    def test_match_pattern_argroles6(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{sc} hyperbase/Cp.s *)'), [{}])

    def test_match_pattern_argroles7(self):
        self.assertEqual(match_pattern('(was/Pd.sc hyperbase /Cp.s great/C)', '(is/Pd.{sc} hyperbase/Cp.s *X)'), [])

    def test_match_pattern_argroles8(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(+/Pd.{sc} hyperbase/Cp.s *X)'), [])

    def test_match_pattern_argroles_ordered1(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.sc hyperbase/Cp.s *X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_ordered2(self):
        self.assertEqual(match_pattern('(is/Pd.cs great/C hyperbase/Cp.s)', '(is/Pd.sc hyperbase/Cp.s *X)'), [])

    def test_match_pattern_argroles_ordered3(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.scx hyperbase/Cp.s *X *Y)'), [])

    def test_match_pattern_argroles_ordered4(self):
        self.assertEqual(
            match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.sc hyperbase/Cp.s *X ...)'), [])

    def test_match_pattern_argroles_ordered5(self):
        self.assertEqual(match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.sc hyperbase/Cp.s *X)'),
                         [])

    def test_match_pattern_argroles_ordered6(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.sc hyperbase/Cp.s *)'), [{}])

    def test_match_pattern_argroles_ordered7(self):
        self.assertEqual(match_pattern('(was/Pd.sc hyperbase /Cp.s great/C)', '(is/Pd.sc hyperbase/Cp.s *X)'), [])

    def test_match_pattern_argroles_ordered8(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(+/Pd.sc hyperbase/Cp.s *X)'), [])

    def test_match_pattern_argroles_vars(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{sc} hyperbase/Cp.s PROP)'),
                         [{'PROP': hedge('great/C')}])

    def test_match_pattern_argroles_vars1(self):
        self.assertEqual(match_pattern('(is/Pd.cs great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_vars2(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{scx} hyperbase/Cp.s X Y)'), [])

    def test_match_pattern_argroles_vars3(self):
        self.assertEqual(
            match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s X ...)'),
            [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_vars4(self):
        self.assertEqual(match_pattern('(is/Pd.xcs today/C great/C hyperbase/Cp.s)', '(is/Pd.{sc} hyperbase/Cp.s X)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_vars5(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{sc} hyperbase/Cp.s XYZ)'),
                         [{'XYZ': hedge('great/C')}])

    def test_match_pattern_argroles_vars6(self):
        self.assertEqual(match_pattern('(was/Pd.sc hyperbase /Cp.s great/C)', '(is/Pd.{sc} hyperbase/Cp.s X)'), [])

    def test_match_pattern_argroles_unknown(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)', '(is/Pd.{sc} hyperbase/Cp.s PROP ...)'),
            [{'PROP': hedge('great/C')}])

    def test_match_pattern_argroles_unknown1(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)', '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA)'),
            [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_argroles_unknown2(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C')},
                          {'PROP': hedge('great/C'), 'EXTRA': hedge('(after/J x/C)')}])

    def test_match_pattern_argroles_unknown3(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA ...)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C')},
                          {'PROP': hedge('great/C'), 'EXTRA': hedge('(after/J x/C)')}])

    def test_match_pattern_argroles_unknown4(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP (EXTRA1) EXTRA2)'),
                         [{'PROP': hedge('great/C'), 'EXTRA1': hedge('(after/J x/C)'), 'EXTRA2': hedge('today/C')}])

    def test_match_pattern_argroles_unknown5(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C (after/J x/C) today/C)',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP (EXTRA1) EXTRA2)'),
                         [{'PROP': hedge('great/C'), 'EXTRA1': hedge('(after/J x/C)'), 'EXTRA2': hedge('today/C')}])

    def test_match_pattern_repeated_vars1(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP EXTRA EXTRA)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C (after/J x/C))')}])

    def test_match_pattern_repeated_vars2(self):
        self.assertEqual(
            match_pattern('(is/P hyperbase/Cp.s great/C today/C today/C)', '(is/P hyperbase/Cp.s PROP EXTRA EXTRA)'),
            [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C today/C)')}])

    def test_match_pattern_argroles_repeated_vars1(self):
        self.assertEqual(match_pattern('(is/Pd.scxx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{scxx} hyperbase/Cp.s PROP EXTRA EXTRA)'),
                         [{'EXTRA': hedge('(list/J/. today/C (after/J x/C))'), 'PROP': hedge('great/C')},
                          {'EXTRA': hedge('(list/J/. (after/J x/C) today/C)'), 'PROP': hedge('great/C')}])

    def test_match_pattern_argroles_repeated_vars2(self):
        self.assertEqual(match_pattern('(is/Pd.scxx hyperbase/Cp.s great/C today/C today/C)',
                                       '(is/Pd.{scxx} hyperbase/Cp.s PROP EXTRA EXTRA)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C today/C)')}])

    def test_match_pattern_repeated_vars_external1(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C)', '(is/P hyperbase/Cp.s PROP EXTRA)',
                                       curvars={'PROP': hedge('great/C')}),
                         [{'PROP': hedge('(list/J/. great/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_repeated_vars_external2(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C)', '(is/P hyperbase/Cp.s PROP EXTRA)',
                                       curvars={'PROP': hedge('abc/C')}),
                         [{'PROP': hedge('(list/J/. abc/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_argroles_repeated_var_external1(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)', '(is/Pd.{scx} hyperbase/Cp.s PROP EXTRA)',
                          curvars={'PROP': hedge('great/C')}),
            [{'PROP': hedge('(list/J/. great/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_argroles_repeated_vars_external2(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)', '(is/P.{sc} hyperbase/Cp.s PROP EXTRA)',
                          curvars={'PROP': hedge('abc/C')}),
            [{'EXTRA': hedge('today/C'), 'PROP': hedge('(list/J/. abc/C great/C)')}])

    def test_match_pattern_deep1(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP EXTRA (after/J X))'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C'), 'X': hedge('x/C')}])

    def test_match_pattern_deep2(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP EXTRA (before/J X))'),
                         [])

    def test_match_pattern_deep3(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP EXTRA (after/J EXTRA))'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C x/C)')}])

    def test_match_pattern_deep4(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP X (after/J X))'),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. x/C x/C)')}])

    def test_match_pattern_deep5(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP X (after/J X))', curvars={'X': hedge('x/C')}),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. x/C x/C x/C)')}])

    def test_match_pattern_deep6(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s PROP X (after/J X))', curvars={'X': hedge('y/C')}),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. y/C x/C x/C)')}])

    def test_match_pattern_argroles_deep1(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA (after/J X))'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C'), 'X': hedge('x/C')}])

    def test_match_pattern_argroles_deep2(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA (before/J X))'),
                         [])

    def test_match_pattern_argroles_deep3(self):
        self.assertEqual(match_pattern('(is/Pd.scxx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{scxx} hyperbase/Cp.s PROP EXTRA (after/J EXTRA))'),
                         [{'EXTRA': hedge('(list/J/. today/C x/C)'), 'PROP': hedge('great/C')}])

    def test_match_pattern_argroles_deep4(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP X (after/J X))'),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. x/C x/C)')}])

    def test_match_pattern_argroles_deep5(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP X (after/J X))', curvars={'X': hedge('x/C')}),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. x/C x/C x/C)')}])

    def test_match_pattern_argroles_deep6(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C x/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP X (after/J X))', curvars={'X': hedge('y/C')}),
                         [{'PROP': hedge('great/C'), 'X': hedge('(list/J/. y/C x/C x/C)')}])

    def test_match_pattern_argroles_multiple_results1(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA ...)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('today/C')},
                          {'PROP': hedge('great/C'), 'EXTRA': hedge('(after/J x/C)')}])

    def test_match_pattern_argroles_multiple_results2(self):
        self.assertEqual(match_pattern('(is/Pd.sscxx i/C hyperbase/Cp.s great/C today/C x/C)',
                                       '(is/Pd.{sc} hyperbase/Cp.s PROP EXTRA ...)'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('i/C')},
                          {'PROP': hedge('great/C'), 'EXTRA': hedge('today/C')},
                          {'PROP': hedge('great/C'), 'EXTRA': hedge('x/C')}])

    def test_match_pattern_argroles_exclusions1(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.sc-x hyperbase/Cp.s X ...)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_exclusions2(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/J)', '(is/Pd.sc-x hyperbase/Cp.s X ...)'),
            [])

    def test_match_pattern_argroles_exclusions3(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.sc-s hyperbase/Cp.s X ...)'),
                         [{'X': hedge('great/C')}])

    def test_match_pattern_argroles_exclusions4(self):
        self.assertEqual(
            match_pattern('(is/Pd.sc i/Cp.s hyperbase/Cp.s great/C)', '(is/Pd.sc-s hyperbase/Cp.s X ...)'),
            [])

    def test_match_pattern_argroles_optionals1(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(is/Pd.{sc,x} X Y Z)'),
                         [{'X': hedge('hyperbase/Cp.s'), 'Y': hedge('great/C')}])

    def test_match_pattern_argroles_optionals2(self):
        self.assertEqual(match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/J)', '(is/Pd.{sc,x} X Y Z)'),
                         [{'X': hedge('hyperbase/Cp.s'), 'Y': hedge('great/C'), 'Z': hedge('today/J')}])

    def test_match_pattern_match_connectors1(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C)', '(PRED/P hyperbase/Cp.s X ...)'),
                         [{'PRED': hedge('is/P'), 'X': hedge('great/C')}])

    def test_match_pattern_match_connectors2(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C)', '(X/P hyperbase/Cp.s X ...)'),
                         [{'X': hedge('(list/J/. is/P great/C)')}])

    def test_match_pattern_argroles_match_connectors1(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(PRED/Pd.sc hyperbase/Cp.s X ...)'),
                         [{'PRED': hedge('is/Pd.sc'), 'X': hedge('great/C')}])

    def test_match_pattern_argroles_match_connectors2(self):
        self.assertEqual(match_pattern('(is/Pd.sc hyperbase/Cp.s great/C)', '(X/Pd.sc hyperbase/Cp.s X ...)'),
                         [{'X': hedge('(list/J/. is/Pd.sc great/C)')}])

    def test_match_pattern_predicate_singleton(self):
        self.assertEqual(match_pattern('keep/Pd..-i-----/en', 'keep/Pd..-i-----'), [{}])

    def test_match_pattern_debug_case_1(self):
        self.assertEqual(
            match_pattern('(said/Pd.sr.<f-----/en entner/Cp.s/en (did/P.so.<f-----/en (of/Br.ma/en all/Cd/en ('
                          'the/Md/en people/Cc.p/en)) (the/Md/en (right/Ma/en thing/Cc.s/en))))',
                          '(said/Pd.{sr}.<f----- */C *)'),
            [{}])

    def test_match_pattern_debug_case_2(self):
        self.assertEqual(
            match_pattern('(said/Pd.sxr.<f-----/en (+/B.ma/. providers/Cc.p/en service/Cc.s/en) (on/Tt/en (+/B.ma/. ('
                          'with/Br.ma/en (a/Md/en call/Cc.s/en) (+/B.ma/. (+/B.ma/. pai/Cp.s/en ajit/Cp.s/en) '
                          'chairman/Cp.s/en)) (last/Ma/en week/Cc.s/en))) (by/T/en ((up/M/en was/P.s.<f-----/en) ('
                          'cellular/Ma/en usage/Cc.s/en))))', '(said/Pd.{sr}.<f----- */C *)'),
            [{}])

    def test_edge_matches_pattern_simple1(self):
        self.assertTrue(edge_matches_pattern(hedge('(a b)'), '(a b)'))

    def test_edge_matches_pattern_simple2(self):
        self.assertFalse(edge_matches_pattern(hedge('(a b)'), '(a a)'))

    def test_edge_matches_pattern_wildcard1(self):
        self.assertTrue(edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s great/C)'), '(is/Pd hyperbase/Cp.s *)'))

    def test_edge_matches_pattern_wildcard2(self):
        self.assertFalse(edge_matches_pattern(hedge('(was/Pd hyperbase/Cp.s great/C)'), '(is/Pd hyperbase/Cp.s *)'))

    def test_edge_matches_pattern_atomic_wildcard1(self):
        self.assertTrue(edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s great/C)'), '(is/Pd hyperbase/Cp.s .)'))

    def test_edge_matches_pattern_atomic_wildcard2(self):
        self.assertFalse(
            edge_matches_pattern(hedge('(was/Pd hyperbase /Cp.s great/C)'), '(is/Pd.sc hyperbase/Cp.s .)'))

    def test_edge_matches_pattern_atomic_wildcard3(self):
        self.assertFalse(
            edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s (fairly/M great/C))'), '(is/Pd hyperbase/Cp.s .)'))

    def test_edge_matches_pattern_edge_wildcard1(self):
        self.assertTrue(
            edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s (fairly/M great/C))'), '(is/Pd hyperbase/Cp.s (*))'))

    def test_edge_matches_pattern_edge_wildcard2(self):
        self.assertFalse(edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s great/C)'), '(is/Pd hyperbase/Cp.s (*))'))

    def test_edge_matches_pattern_open_ended1(self):
        self.assertTrue(edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s great/C)'), '(is/Pd hyperbase/Cp.s * ...)'))

    def test_edge_matches_pattern_open_ended2(self):
        self.assertTrue(
            edge_matches_pattern(hedge('(is/Pd hyperbase/Cp.s great/C extra/C)'), '(is/Pd hyperbase/Cp.s * ...)'))

    def test_edge_matches_pattern_open_ended3(self):
        self.assertFalse(
            edge_matches_pattern(hedge('(is/Pd humanity/Cp.s great/C extra/C)'), '(is/Pd hyperbase/Cp.s * ...)'))

    def test_match_pattern_complex(self):
        s = ('(says/Pd.rr.|f--3s-/en (calls/Pr.so.|f--3s-/en */C (*/M (draconian/Ma/en (+/B.am/. coronavirus/Cc.s/en '
             'restrictions/Cc.p/en)))) */R)')
        pattern = hedge(s)
        s = ("(says/Pd.rr.|f--3s-/en ((+/B.aaa/. ali/Cp.s/en wentworth/Cp.s/en"
             " tests/Cp.p/en) (+/B.aaa/. ali/Cp.s/en wentworth/Cp.s/en "
             "tests/Cp.p/en) (for/T/en coronavirus/Cp.s/en)) "
             "('s/Pr.s.|f--3s-/en (+/B.aaa/. ali/Cp.s/en wentworth/Cp.s/en "
             "tests/Cp.p/en)))")
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [])

    def test_match_pattern_fun_var1(self):
        s = "((var */P PRED) */C */C)"
        pattern = hedge(s)
        s = "(says/Pd x/C y/C)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'PRED': hedge('says/Pd')}])

    def test_match_pattern_fun_var2(self):
        s = "((var (*/M VERB/P) PRED) */C */C)"
        pattern = hedge(s)
        s = "((will/M say/Pd) x/C y/C)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'PRED': hedge('(will/M say/Pd)'), 'VERB': hedge('say/Pd')}])

    def test_match_pattern_fun_var3(self):
        s = "((var (*/M VERB/P) PRED) */C */C)"
        pattern = hedge(s)
        s = "((var (will/M say/Pd) PRED) x/C y/C)"
        edge = hedge(s)
        self.assertEqual(
            match_pattern(edge, pattern), [{'PRED': hedge('(will/M say/Pd)'), 'VERB': hedge('say/Pd')}])

    ##########################
    def test_match_pattern_repeated_var_funs1(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/P hyperbase/Cp.s (var */C PROP) (var */C EXTRA) (var */C EXTRA))'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C (after/J x/C))')}])

    def test_match_pattern_repeated_var_funs2(self):
        self.assertEqual(
            match_pattern('(is/P hyperbase/Cp.s great/C today/C today/C)',
                          '(is/P hyperbase/Cp.s (var * PROP) (var * EXTRA) (var * EXTRA))'),
            [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C today/C)')}])

    def test_match_pattern_repeated_var_funs3(self):
        self.assertEqual(match_pattern('(is/Pd.scxx hyperbase/Cp.s great/C today/C (after/J x/C))',
                                       '(is/Pd.{scxx} hyperbase/Cp.s (var * PROP) (var * EXTRA) (var * EXTRA))'),
                         [{'EXTRA': hedge('(list/J/. today/C (after/J x/C))'), 'PROP': hedge('great/C')},
                          {'EXTRA': hedge('(list/J/. (after/J x/C) today/C)'), 'PROP': hedge('great/C')}])

    def test_match_pattern_repeated_var_funs4(self):
        self.assertEqual(match_pattern('(is/Pd.scxx hyperbase/Cp.s great/C today/C today/C)',
                                       '(is/Pd.{scxx} hyperbase/Cp.s (var * PROP) (var * EXTRA) (var * EXTRA))'),
                         [{'PROP': hedge('great/C'), 'EXTRA': hedge('(list/J/. today/C today/C)')}])

    def test_match_pattern_repeated_var_funs5(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C)',
                                       '(is/P hyperbase/Cp.s (var * PROP) (var * EXTRA))',
                                       curvars={'PROP': hedge('great/C')}),
                         [{'PROP': hedge('(list/J/. great/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_repeated_var_funs6(self):
        self.assertEqual(match_pattern('(is/P hyperbase/Cp.s great/C today/C)',
                                       '(is/P hyperbase/Cp.s (var * PROP) (var * EXTRA))',
                                       curvars={'PROP': hedge('abc/C')}),
                         [{'PROP': hedge('(list/J/. abc/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_repeated_var_funs7(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)',
                          '(is/Pd.{scx} hyperbase/Cp.s (var */C PROP) (var */C EXTRA))',
                          curvars={'PROP': hedge('great/C')}),
            [{'PROP': hedge('(list/J/. great/C great/C)'), 'EXTRA': hedge('today/C')}])

    def test_match_pattern_repeated_var_funs8(self):
        self.assertEqual(
            match_pattern('(is/Pd.scx hyperbase/Cp.s great/C today/C)',
                          '(is/P.{sc} hyperbase/Cp.s (var * PROP) (var * EXTRA))',
                          curvars={'PROP': hedge('abc/C')}),
            [{'EXTRA': hedge('today/C'), 'PROP': hedge('(list/J/. abc/C great/C)')}])
    ##########################

    def test_match_pattern_fun_atoms1(self):
        s = "(atoms */P)"
        pattern = hedge(s)
        s = "says/Pd.rr.|f--3s-/en"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_atoms2(self):
        s = "(atoms says/P)"
        pattern = hedge(s)
        s = "says/Pd.rr.|f--3s-/en"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_atoms3(self):
        s = "(atoms say/P)"
        pattern = hedge(s)
        s = "says/Pd.rr.|f--3s-/en"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [])

    def test_match_pattern_fun_atoms4(self):
        s = "(atoms VERB/P)"
        pattern = hedge(s)
        s = "says/Pd.rr.|f--3s-/en"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'VERB': hedge('says/Pd.rr.|f--3s-/en')}])

    def test_match_pattern_fun_atoms5(self):
        s = "(atoms VERB/P)"
        pattern = hedge(s)
        s = "(will/M say/Pd)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'VERB': hedge('say/Pd')}])

    def test_match_pattern_fun_atoms6(self):
        s = "(atoms */M VERB/P)"
        pattern = hedge(s)
        s = "(will/M say/Pd)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'VERB': hedge('say/Pd')}])

    def test_match_pattern_fun_atoms7(self):
        s = "(atoms not/M VERB/P)"
        pattern = hedge(s)
        s = "(will/M say/Pd)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [])

    def test_match_pattern_fun_atoms8(self):
        s = "(atoms will/M VERB/P)"
        pattern = hedge(s)
        s = "(will/M (not/M say/Pd))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'VERB': hedge('say/Pd')}])

    def test_match_pattern_fun_atoms9(self):
        s = "(atoms MOD/M VERB/P)"
        pattern = hedge(s)
        s = "(will/M (not/M say/Pd))"
        edge = hedge(s)
        result = match_pattern(edge, pattern)
        self.assertIn({'MOD': hedge('not/M'), 'VERB': hedge('say/Pd')}, result)
        self.assertIn({'MOD': hedge('will/M'), 'VERB': hedge('say/Pd')}, result)
        self.assertEqual(len(result), 2)

    def test_match_pattern_fun_atoms10(self):
        s = "((atoms MOD/M VERB/P.so) * *)"
        pattern = hedge(s)
        s = "((will/M (not/M say/Pd.so)) x/C y/C)"
        edge = hedge(s)
        result = match_pattern(edge, pattern)
        self.assertIn({'MOD': hedge('not/M'), 'VERB': hedge('say/Pd.so')}, result)
        self.assertIn({'MOD': hedge('will/M'), 'VERB': hedge('say/Pd.so')}, result)
        self.assertEqual(len(result), 2)

    def test_match_pattern_fun_atoms11(self):
        s = "((atoms MOD/M VERB/P.so) X Y)"
        pattern = hedge(s)
        s = "((will/M (not/M say/Pd.so)) x/C y/C)"
        edge = hedge(s)
        result = match_pattern(edge, pattern)
        self.assertIn(
            {'MOD': hedge('not/M'), 'VERB': hedge('say/Pd.so'), 'X': hedge('x/C'), 'Y': hedge('y/C')}, result)
        self.assertIn(
            {'MOD': hedge('will/M'), 'VERB': hedge('say/Pd.so'), 'X': hedge('x/C'), 'Y': hedge('y/C')}, result)
        self.assertEqual(len(result), 2)

    def test_match_pattern_fun_any1(self):
        s = "((any says/P.sr writes/P.sr) * *)"
        pattern = hedge(s)
        s = "(says/P.sr mary/Cp.s (are/P.sc you/Ci nice/Ca))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_any2(self):
        s = "((any says/P.{sr} writes/P.{sr}) * *)"
        pattern = hedge(s)
        s = "(writes/P.sr mary/Cp.s (are/P.sc you/Ci nice/Ca))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_any3(self):
        s = "((any says/P.{sr} writes/P.{sr}) * *)"
        pattern = hedge(s)
        s = "(shouts/P.sr mary/Cp.s (are/P.sc you/Ci nice/Ca))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [])

    def test_match_pattern_fun_any4(self):
        s = "(says/P.sr * (any (are/P.{sc} */Ci (var */Ca PROP)) (var */R X)))"
        pattern = hedge(s)
        s = "(says/P.sr mary/Cp.s (are/P.sc you/Ci nice/Ca))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'PROP': hedge('nice/Ca')}])

    def test_match_pattern_fun_any5(self):
        s = "(says/P.{sr} * (any (are/P.{sc} */Ci (var */Ca PROP)) (var */R X)))"
        pattern = hedge(s)
        s = "(says/P.sr mary/Cp.s (is/P.sc he/Ci nice/Ca))"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{'X': hedge('(is/P.sc he/Ci nice/Ca)')}])

    def test_match_pattern_fun_atoms_any1(self):
        s = "((atoms (any say/P.{s} speak/P.{s})) *)"
        pattern = hedge(s)
        s = "((does/M (not/M speak/P.s)) mary/Cp.s)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_atoms_any2(self):
        s = "((atoms (any say/P.{s} speak/P.{s}) does/M) *)"
        pattern = hedge(s)
        s = "((does/M (not/M speak/P.s)) mary/Cp.s)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])

    def test_match_pattern_fun_argroles2(self):
        s = "((atoms has/M said/P.{so}) */C */C)"
        pattern = hedge(s)
        s = "((has/M said/Pd.so) x/C y/C)"
        edge = hedge(s)
        self.assertEqual(match_pattern(edge, pattern), [{}])
    
    def test_match_pattern_fun_argroles8(self):
        s = ("""
        (says/Pd.{r}.|f--3s-/en (var (executes/P.{o}.|f--3s-/en (+/B.{mm}/. (15/M#/en people/Cc.p/en)
        (for/Br.{ma}/en 10/C#/en (+/B.{ma}/. convictions/Cc.p/en terrorism/Cc.s/en)))) CLAIM))
        """)
        pattern = hedge(s)
        s = ("""
        (says/Pd.r.|f--3s-/en (var (executes/P.o.|f--3s-/en (+/B.mm/. (15/M#/en people/Cc.p/en) (for/Br.ma/en 10/C#/en
        (+/B.am/. terrorism/Cc.s/en convictions/Cc.p/en)))) CLAIM))
        """)
        edge = hedge(s)
        matches = match_pattern(edge, pattern)
        self.assertFalse(matches == [])
        # self.assertEqual(matches[0]['ACTOR'], hedge('jordan/Cp.s/en'))

    def test_match_pattern_fun_argroles9(self):
        s = ("""
        (says/Pd.{sr}.|f--3s-/en (var jordan/Cp.s/en ACTOR) (var (executes/P.{o}.|f--3s-/en (+/B.{mm}/.
        (15/M#/en people/Cc.p/en) (for/Br.{ma}/en 10/C#/en (+/B.{ma}/. convictions/Cc.p/en terrorism/Cc.s/en)))) CLAIM))
        """)
        pattern = hedge(s)
        s = ("""
        (says/Pd.sr.|f--3s-/en (var jordan/Cp.s/en ACTOR) (var (executes/P.o.|f--3s-/en (+/B.mm/.
        (15/M#/en people/Cc.p/en) (for/Br.ma/en 10/C#/en (+/B.am/. terrorism/Cc.s/en convictions/Cc.p/en)))) CLAIM))
        """)
        edge = hedge(s)
        matches = match_pattern(edge, pattern)
        self.assertFalse(matches == [])
        self.assertEqual(matches[0]['ACTOR'], hedge('jordan/Cp.s/en'))

    def test_match_pattern_real_case1(self):
        s = """((atoms heavily/M/en also/M/en influenced/Pd.{pa}.<pf----/en was/Mv.<f-----/en)
                    (var * ORIG) (* (var * TARG)))"""
        pattern = hedge(s)
        s = """((was/Mv.<f-----/en (also/M/en (heavily/M/en influenced/Pd.{pa}.<pf----/en)))
                    he/Ci/en (by/T/en macy/Cp.s/en))"""
        edge = hedge(s)
        matches = match_pattern(edge, pattern)
        self.assertEqual(matches, [{'ORIG': hedge('he/Ci/en'), 'TARG': hedge('macy/Cp.s/en')}])

    def test_match_pattern_real_ca2(self):
        s = """(*/J (*/J (var */R CAUSE) *) (var * EFFECT))"""
        pattern = hedge(s)
        s = """(and/J/en (var ((to/Mi/en (have/Mv.-i-----/en been/P.c.<pf----/en)) (extremely/M/en busy/Ca/en)) CAUSE)
                   (var (could/Mm/en (not/Mn/en (be/Mv.-i-----/en blamed/Pd..<pf----/en))) EFFECT))"""
        edge = hedge(s)
        matches = match_pattern(edge, pattern)
        self.assertEqual(matches, [])

    def test_more_general1(self):
        edge1 = hedge('*')
        edge2 = hedge('moon/C')
        self.assertTrue(more_general(edge1, edge2))

    def test_more_general2(self):
        edge1 = hedge('*')
        edge2 = hedge('((going/M is/P.sx) mary/C (to/T (the/M moon/C)))')
        self.assertTrue(more_general(edge1, edge2))

    def test_more_general3(self):
        edge1 = hedge('((going/M is/P.sx) */C (to/T (the/M moon/C)))')
        edge2 = hedge('((going/M is/P.sx) mary/C (to/T (the/M moon/C)))')
        self.assertTrue(more_general(edge1, edge2))

    def test_more_general4(self):
        edge1 = hedge('((going/M is/P.sx) */C (to/T */C))')
        edge2 = hedge('((going/M is/P.sx) */C (to/T (the/M moon/C)))')
        self.assertTrue(more_general(edge1, edge2))

    def test_is_variable1(self):
        edge = hedge('((going/M is/P.sx) */C (to/T */C))')
        self.assertFalse(is_variable(edge))

    def test_is_variable2(self):
        edge = hedge('(var ((going/M is/P.sx) */C (to/T */C)) X)')
        self.assertTrue(is_variable(edge))
    
    def test_contains_variable1(self):
        edge = hedge('((going/M is/P.sx) */C (to/T */C))')
        self.assertFalse(contains_variable(edge))

    def test_contains_variable2(self):
        edge = hedge('(var ((going/M is/P.sx) */C (to/T */C)) X)')
        self.assertTrue(contains_variable(edge))

    def test_contains_variable3(self):
        edge = hedge('((going/M is/P.sx) (var */C XYZ) (to/T */C))')
        self.assertTrue(contains_variable(edge))

    def test_contains_variable4(self):
        edge = hedge('apples/C')
        self.assertFalse(contains_variable(edge))

    def test_common_pattern1(self):
        edge1 = hedge('(likes/P.so mary/C chess/C)')
        edge2 = hedge('(likes/P.so john/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(likes/P.{so} */C */C)')

    def test_common_pattern2(self):
        edge1 = hedge('(likes/P.so mary/C chess/C)')
        edge2 = hedge('(likes/P.sox john/C mary/C x/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(likes/P.{so} */C */C)')

    def test_common_pattern3(self):
        edge1 = hedge('(likes/P mary/C chess/C)')
        edge2 = hedge('(likes/P john/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(likes/P */C */C)')

    def test_common_pattern4(self):
        edge1 = hedge('(likes/P.so mary/C chess/C)')
        edge2 = hedge('(loves/P.so john/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(*/P.{so} */C */C)')

    def test_common_pattern5(self):
        edge1 = hedge('(likes/P.so mary/C chess/C)')
        edge2 = hedge('(loves/P.so mary/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(*/P.{so} mary/C */C)')

    def test_common_pattern6(self):
        edge1 = hedge('(loves/P.so mary/C chess/C)')
        edge2 = hedge('(loves/P.so mary/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(loves/P.{so} mary/C */C)')

    def test_common_pattern7(self):
        edge1 = hedge('mary/C')
        edge2 = hedge('john/C')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '*/C')

    def test_common_pattern8(self):
        edge1 = hedge('mary/C')
        edge2 = hedge('red/M')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '*')

    def test_common_pattern9(self):
        edge1 = hedge('mary/C')
        edge2 = hedge('(loves/P.so mary/C mary/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '*')

    def test_common_pattern10(self):
        edge1 = hedge('(likes/P mary/C chess/C)')
        edge2 = hedge('(likes/P john/C mary/C x/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '*/R')

    def test_common_pattern11(self):
        edge1 = hedge('(likes/P.so mary/C (of/B.ma games/C chess/C))')
        edge2 = hedge('(likes/P.sox john/C (of/B.ma games/C go/C) x/C)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(likes/P.{so} */C (of/B.{ma} games/C */C))')

    def test_common_pattern12(self):
        edge1 = hedge('(likes/P.so/en mary/C/en (of/B.ma/en games/C/en chess/C/en))')
        edge2 = hedge('(likes/P.sox/en joe/C/en (of/B.ma/en games/C/en go/C/en) x/C/en)')
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(likes/P.{so} */C (of/B.{ma} games/C */C))')

    def test_common_pattern13(self):
        edge1 = hedge(
            """
            (said/Pd.rs.<f-----/en
                (is/P.sc.|f--3s-/en
                    (the/Md/en (only/Ma/en difference/Cc.s/en))
                    (for/Br.ma/en
                        (of/Br.ma/en (the/Md/en amount/Cc.s/en) pixels/Cc.p/en)
                        (of/Br.ma/en (a/Md/en lot/Cc.s/en) content/Cc.s/en)))
                neikirk/Cp.s/en)
            """)
        edge2 = hedge(
            """
            (said/Pd.xsorr.<f-----/en (spent/Pd.xxx.<pf----/en ((and/Mj/en
            with/T/en) (vast/Ma/en (+/B.mm/. numbers/Cc.p/en (of/Jr.ma/en
            people/Cc.p/en (and/J/en ((now/M/en working/P.x.|pg----/en)
            (from/T/en home/Cc.s/en)) (using/Pd.or.|pg----/en (and/J/en
            (+/B.am/. video/Cc.s/en chat/Cc.s/en) (digital/Ma/en
            messages/Cc.p/en)) ((to/Mi/en stay/P.x.-i-----/en) (in/T/en
            (with/Br.ma/en touch/Cc.s/en (and/J/en friends/Cc.p/en
            family/Cc.s/en)))))))))) (as/T/en (increase/Pd.so.|f-----/en
            users/Cc.p/en (their/Mp/en time/Cc.s/en))) (on/T/en (+/B.am/.
            streaming/Cc.s/en platforms/Cc.p/en))) breton/Cp.s/en
            streamers/Cc.p/en (had/P.o?.<f-----/en (a/Md/en role/Cc.s/en)
            ((to/Mi/en play/P.x.-i-----/en) (in/T/en (ensuring/P.o.|pg----/en
            (+/B.am/. telecom/Cc.s/en operators/Cc.p/en))))) ((n’t/Mn/en
            were/P.c.<f-----/en) overwhelmed/Ca/en))
            """)
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(said/Pd.{sr}.<f----- */Cp.s (*/P.{c} */C))')

    def test_common_pattern14(self):
        edge1 = hedge(
            """
            (said/Pd.rsx.<f-----/en (think/P.sr.|f-----/en i/Ci/en (that/T/en
            (is/P.sc.|f--3s-/en (the/Md/en impact/Cc.s/en) (somewhat/M/en
            marginal/Ca/en)))) he/Ci/en (noting/Pd.r.|pg----/en (that/T/en
            (makes/P.sr.|f--3s-/en (of/Br.ma/en (’s/Bp.am/en youtube/Cm/en
            lack/Cc.s/en) (+/B.am/. 4/C#/en (+/B.am/. k/Cp.s/en
            content/Cc.s/en))) (+/J.mm/. (in/Jr.ma/en (of/Jr.ma/en
            (less/P.s.-------/en it/Ci/en) (a/Md/en factor/Cc.s/en))
            (of/Br.ma/en (the/Md/en (((most/M^/en bandwidth/Ma/en) heavy/Ma/en)
            sort/Cc.s/en)) video/Cc.s/en)) (than/Jr.ma/en (paid/Mv.<pf----/en
            services/Cc.p/en) (producing/P.o.|pg----/en (their/Mp/en (own/Ma/en
            (4/M#/en (+/B.am/. k/Cc.s/en fare/Cc.s/en)))))))))))
            """)
        edge2 = hedge(
            """
            (said/Pd.sr.<f-----/en he/Ci/en ((again/M/en (would/Mm/en
            speak/P.sx.-i-----/en)) he/Ci/en (with/T/en hastings/Cp.s/en)))
            """)
        self.assertEqual(common_pattern(edge1, edge2).to_str(), '(said/Pd.{sr}.<f----- he/Ci (*/P.{s} */Ci))')

    def test_common_pattern_var1(self):
        edge1 = hedge(
            """(said/Pd.rsx.<f-----/en (think/P.sr.|f-----/en (var i/Ci/en SUBJ)
            (that/T/en (is/P.sc.|f--3s-/en (the/Md/en impact/Cc.s/en)
            (somewhat/M/en marginal/Ca/en)))) he/Ci/en (noting/Pd.r.|pg----/en
            (that/T/en (makes/P.sr.|f--3s-/en (of/Br.ma/en (’s/Bp.am/en
            youtube/Cm/en lack/Cc.s/en) (+/B.am/. 4/C#/en (+/B.am/. k/Cp.s/en
            content/Cc.s/en))) (+/J.mm/. (in/Jr.ma/en (of/Jr.ma/en
            (less/P.s.-------/en it/Ci/en) (a/Md/en factor/Cc.s/en))
            (of/Br.ma/en (the/Md/en (((most/M^/en bandwidth/Ma/en) heavy/Ma/en)
            sort/Cc.s/en)) video/Cc.s/en)) (than/Jr.ma/en (paid/Mv.<pf----/en
            services/Cc.p/en) (producing/P.o.|pg----/en (their/Mp/en (own/Ma/en
            (4/M#/en (+/B.am/. k/Cc.s/en fare/Cc.s/en)))))))))))
            """)
        edge2 = hedge("""(said/Pd.sr.<f-----/en he/Ci/en ((again/M/en (would/Mm/en
                      speak/P.sx.-i-----/en)) (var he/Ci/en SUBJ) (with/T/en hastings/Cp.s/en)))""")
        self.assertEqual(common_pattern(edge1, edge2).to_str(),
                         '(said/Pd.{sr}.<f----- he/Ci (*/P.{s} (var */Ci SUBJ)))')

    def test_common_pattern_var2(self):
        edge1 = hedge('(likes/P.so (var mary/C PERSON) (of/B.ma games/C (var chess/C GAME)))')
        edge2 = hedge('(likes/P.sox john/C zzz/C x/C)')
        self.assertEqual(common_pattern(edge1, edge2), None)
            
    def test_common_pattern_var3(self):
        edge1 = hedge('(likes/P.{sox} (var mary/C PERSON) (of/B.ma games/C (var chess/C GAME)) (var sometimes/C WHEN))')
        edge2 = hedge('(likes/P.so john/C (of/B.ma games/C go/C))')
        self.assertEqual(common_pattern(edge1, edge2), None)

    def test_common_pattern_repeated_vars_1(self):
        edge1 = hedge('((var is/P.sc X) (var (my/M name/C) X) (var telmo/C Z))')
        edge2 = hedge('((var is/P.sc X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), hedge('((var is/P.{sc} X) (var (*/M name/C) X) (var */C Z))'))

    def test_common_pattern_repeated_vars_2(self):
        edge1 = hedge('((var is/P.sc X) (var (my/M name/C) Y) (var telmo/C Z))')
        edge2 = hedge('((var is/P.sc X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), None)

    def test_common_pattern_repeated_vars_3(self):
        edge1 = hedge('((var is/P.scx X) (var (my/M name/C) X) (var telmo/C Z) (in/T 2023/C))')
        edge2 = hedge('((var is/P.sc X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), hedge('((var is/P.{sc} X) (var (*/M name/C) X) (var */C Z))'))

    def test_common_pattern_repeated_vars_4(self):
        edge1 = hedge('((var is/P.sc X) (my/M name/C) (var telmo/C Z))')
        edge2 = hedge('((var is/P.sc X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), None)

    def test_common_pattern_repeated_vars_5(self):
        edge1 = hedge('((var is/J X) (my/M name/C) (var telmo/C Z))')
        edge2 = hedge('((var is/J X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), None)

    def test_common_pattern_repeated_vars_6(self):
        edge1 = hedge('((var is/P.c X) (var telmo/C Z))')
        edge2 = hedge('((var is/P.sc X) (var (her/M name/C) X) (var maria/C Z))')
        self.assertEqual(common_pattern(edge1, edge2), None)

    def test_common_pattern_misc1(self):
        edge1 = hedge('(*/P.{sx} (var */C EFFECT) (*/T (var * CAUSE)))')
        edge2 = hedge('(*/P.{sxx} (var */C EFFECT) * (*/T (var * CAUSE)))')
        self.assertEqual(common_pattern(edge1, edge2), edge1)

    def test_merge_edges1(self):
        edge1 = hedge('(likes/P.{sox} */C (of/B.ma games/C */C) sometimes/C)')
        edge2 = hedge('(loves/P.{sox} */C */C sometimes/C)')
        self.assertEqual(merge_patterns(edge1, edge2),
                         hedge('((any likes/P.{sox} loves/P.{sox}) */C (any (of/B.ma games/C */C) */C) sometimes/C)'))

    def test_merge_edges2(self):
        edge1 = hedge('(likes/P.{sox} */C (of/B.ma games/C */C) sometimes/C)')
        edge2 = hedge('(loves/P.{so} */C */C)')
        self.assertEqual(merge_patterns(edge1, edge2), None)

    def test_merge_edges3(self):
        edge1 = hedge('(likes/P.{so} */C (of/B.ma games/C */R))')
        edge2 = hedge('(loves/P.{so} */C (of/B.ma games/C */C))')
        self.assertEqual(merge_patterns(edge1, edge2),
                         hedge('((any likes/P.{so} loves/P.{so}) */C (of/B.ma games/C (any */R */C)))'))

    def test_merge_edges4(self):
        edge1 = hedge('(likes/P.{so} */C (of/B.ma games/C */R))')
        edge2 = hedge('(likes/P.{so} */C (of/B.ma games/C */R))')
        self.assertEqual(merge_patterns(edge1, edge2), hedge('(likes/P.{so} */C (of/B.ma games/C */R))'))

    def test_merge_edges5(self):
        edge1 = hedge('((any likes/P.{so} prefers/P.{so}) */C */C)')
        edge2 = hedge('(loves/P.{so} */C */C)')
        self.assertEqual(merge_patterns(edge1, edge2),
                         hedge('((any likes/P.{so} prefers/P.{so} loves/P.{so}) */C */C)'))


if __name__ == '__main__':
    unittest.main()
