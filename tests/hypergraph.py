import hyperbase.constants as const
from hyperbase import hedge, hgraph
from hyperbase import hopen


class Hypergraph:
    def setUp(self):
        self.hg = hgraph(self.hg_str)

    def tearDown(self):
        self.hg.close()

    def test_name(self):
        self.assertEqual(self.hg.name(), self.hg_str)

    def test_close(self):
        self.hg.close()

    def test_destroy(self):
        self.hg.destroy()
        self.hg.add(hedge('(src hyperbase/1 (size hyperbase/1 7))'))
        self.assertTrue(self.hg.exists(hedge('(src hyperbase/1 (size hyperbase/1 7))')))
        self.hg.destroy()
        self.assertFalse(self.hg.exists(hedge('(src hyperbase/1 (size hyperbase/1 7))')))

    def test_all(self):
        self.hg.destroy()
        self.hg.add('(size hyperbase/1 7)')
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(src mary/1 (is hyperbase/1 great/1))')

        labels = set([edge.to_str() for edge in self.hg.all()])
        self.assertEqual(labels,
                         {'size', 'hyperbase/1', '7', 'is', 'great/1', 'src', 'mary/1', '(size hyperbase/1 7)',
                          '(is hyperbase/1 great/1)', '(src mary/1 (is hyperbase/1 great/1))'})
        self.hg.destroy()
        labels = set(self.hg.all())
        self.assertEqual(labels, set())

    def test_atoms(self):
        self.hg.destroy()
        self.hg.add('(size hyperbase/1 7)')
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(src mary/1 (is hyperbase/1 great/1))')

        labels = set([edge.to_str() for edge in self.hg.all_atoms()])
        self.assertEqual(labels,
                         {'size', 'hyperbase/1', '7', 'is', 'great/1', 'src', 'mary/1'})
        self.hg.destroy()
        labels = set(self.hg.all())
        self.assertEqual(labels, set())

    def test_edges(self):
        self.hg.destroy()
        self.hg.add('(size hyperbase/1 7)')
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(src mary/1 (is hyperbase/1 great/1))')

        labels = set([edge.to_str() for edge in self.hg.all_non_atoms()])
        self.assertEqual(labels,
                         {'(size hyperbase/1 7)', '(is hyperbase/1 great/1)', '(src mary/1 (is hyperbase/1 great/1))'})
        self.hg.destroy()
        labels = set(self.hg.all())
        self.assertEqual(labels, set())

    def test_all_attributes(self):
        self.hg.destroy()
        self.hg.add('(size hyperbase/1 7)')
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(src mary/1 (is hyperbase/1 great/1))')

        labels = set(['%s %s' % (t[0].to_str(), t[1]['d'])
                      for t in self.hg.all_attributes()])
        self.assertEqual(labels, {'size 1', 'hyperbase/1 2', '7 1', 'is 1', 'great/1 1', 'src 1', 'mary/1 1',
                                  '(size hyperbase/1 7) 0', '(is hyperbase/1 great/1) 1',
                                  '(src mary/1 (is hyperbase/1 great/1)) 0'})
        self.hg.destroy()
        labels = set(self.hg.all_attributes())
        self.assertEqual(labels, set())

    def test_get_attributes(self):
        self.hg.destroy()
        edge = hedge('(is/Pd hyperbase/Cp great/C)')
        self.hg.add(edge)
        self.assertEqual(self.hg.get_attributes(edge), {'p': 1, 'd': 0, 'dd': 0})
        
    # exists, add, remove
    def test_ops1(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.assertTrue(self.hg.exists(hedge('(is/Pd hyperbase/Cp great/C)')))
        self.hg.remove(hedge('(is/Pd hyperbase/Cp great/C)'))
        self.assertFalse(
            self.hg.exists(hedge('(is/Pd hyperbase/Cp great/C)')))

    # exists, add, remove
    def test_ops_2(self):
        self.hg.destroy()
        self.hg.add('(src hyperbase/1 (size hyperbase/1 7))')
        self.assertTrue(self.hg.exists(hedge('(src hyperbase/1 (size hyperbase/1 7))')))
        self.hg.remove(hedge('(src hyperbase/1 (size hyperbase/1 7))'))
        self.assertFalse(self.hg.exists(hedge('(src hyperbase/1 (size hyperbase/1 7))')))

    # test add with count=True
    def test_add_count(self):
        self.hg.destroy()
        edge = hedge('(is/Pd hyperbase/Cp great/C)')
        self.hg.add(edge, count=True)
        self.assertEqual(self.hg.get_int_attribute(edge, 'count'), 1)
        self.hg.add(edge, count=True)
        self.assertEqual(self.hg.get_int_attribute(edge, 'count'), 2)

    def test_search(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(list(self.hg.search('(* hyperbase/Cp *)')), [hedge('(is/Pd hyperbase/Cp great/C)')])
        self.assertEqual(list(self.hg.search('(is/Pd hyperbase/Cp *)')), [hedge('(is/Pd hyperbase/Cp great/C)')])
        self.assertEqual(list(self.hg.search('(x * *)')), [])
        self.assertEqual(list(self.hg.search('(says/Pd * (is/Pd hyperbase/Cp great/C))')),
                         [hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')])
        self.assertEqual(list(self.hg.search('(says/Pd * (is/Pd * *))')),
                         [hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')])

    def test_search_open_ended(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(list(self.hg.search('(* hyperbase/Cp * ...)')), [hedge('(is/Pd hyperbase/Cp great/C)')])
        self.assertEqual(list(self.hg.search('(is/Pd hyperbase/Cp * ...)')), [hedge('(is/Pd hyperbase/Cp great/C)')])
        self.assertEqual(list(self.hg.search('(x * * ...)')), [])

        self.assertEqual(list(self.hg.search('(says/Pd * (is/Pd hyperbase/Cp great/C) ...)')),
                         [hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))'),
                          hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')])

    def test_search_star(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(set(self.hg.search('*')),
                         {hedge('(is/Pd hyperbase/Cp great/C)'), hedge('(says/Pd mary/Cp)'),
                          hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))'),
                          hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)'), hedge('extra/C'),
                          hedge('hyperbase/Cp'), hedge('great/C'), hedge('is/Pd'), hedge('mary/Cp'), hedge('says/Pd')})

    def test_search_at(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(set(self.hg.search('.')),
                         {hedge('extra/C'), hedge('hyperbase/Cp'), hedge('great/C'), hedge('is/Pd'), hedge('mary/Cp'),
                          hedge('says/Pd')})

    def test_search_amp(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(set(self.hg.search('(*)')),
                         {hedge('(is/Pd hyperbase/Cp great/C)'), hedge('(says/Pd mary/Cp)'),
                          hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))'),
                          hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')})

    def test_search_non_atomic_pred(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd ) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) ...)')), [edge])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) * *)')), [edge])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) . (*))')), [edge])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) . .)')), [])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) (*) (*))')), [])
        self.assertEqual(list(self.hg.search('(* mary/Cp.s *)')), [edge])
        self.assertEqual(list(self.hg.search('(mary/Cp.s * *)')), [])
        self.assertEqual(list(self.hg.search('(* * (a/Md ((very/M old/Ma) violin/Cn.s)))')), [edge])
        self.assertEqual(list(self.hg.search('((a/Md ((very/M old/Ma) violin/Cn.s)) * *)')), [])

    def test_search_non_atomic_pred_vars(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd ) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) *X *Y)')), [edge])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) .X (Y))')), [edge])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) .X .Y)')), [])
        self.assertEqual(list(self.hg.search('((is/M playing/Pd) (X) (Y))')), [])
        self.assertEqual(list(self.hg.search('(* mary/Cp.s X)')), [edge])
        self.assertEqual(list(self.hg.search('(mary/Cp.s X Y)')), [])
        self.assertEqual(list(self.hg.search('(X Y (a/Md ((very/M old/Ma) violin/Cn.s)))')), [edge])
        self.assertEqual(list(self.hg.search('((a/Md ((very/M old/Ma) violin/Cn.s)) X Y)')), [])

    def test_search_pred_with_roles(self):
        self.hg.destroy()
        self.hg.add('(says/Pd.so.|f--3s-/en mary/C hello/C)')
        self.hg.add('(says/Pd.os.|f--3s-/en hello/C mary/C)')
        self.assertEqual(list(self.hg.search('(says/Pd.so.|f--3s-/en * *)')),
                         [hedge('(says/Pd.so.|f--3s-/en mary/C hello/C)')])

    def test_search_pred_with_roles_and_ellipsis(self):
        self.hg.destroy()
        edge = hedge(('(is/Mv.|f--3s-/en playing/Pd.so.|pg----/en)', 'mary/Cp.s/en',
                      '(a/Md/en ((very/M/en old/Ma/en) violin/Cc.s/en))'))
        pattern = hedge('((is/Mv.|f--3s-/en playing/Pd.so.|pg----/en) ...)')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.search(pattern)), [edge])

    def test_search_pred_with_deep_pattern(self):
        self.hg.destroy()
        edge = hedge(('(is/Mv.|f--3s-/en playing/Pd.so.|pg----/en)', 'mary/Cp.s/en',
                      '(a/Md/en ((very/M/en old/Ma/en) violin/Cc.s/en))'))
        pattern = hedge('(*/Pd.so */C (*/M ((*/M */M) violin/Cc.s/en)))')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.search(pattern)), [edge])

    def test_search_pred_with_multiple_incomplete_atoms(self):
        self.hg.destroy()
        self.hg.add('(says/Pd.so.|f--3s-/en mary/Cp hello/Cs)')
        self.assertEqual(list(self.hg.search('(says/Pd.{so} mary/C hello/C)')),
                         [hedge('(says/Pd.so.|f--3s-/en mary/Cp hello/Cs)')])

    def test_count(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(self.hg.count('(* hyperbase/Cp *)'), 1)
        self.assertEqual(self.hg.count('(is/Pd hyperbase/Cp *)'), 1)
        self.assertEqual(self.hg.count('(x * *)'), 0)
        self.assertEqual(self.hg.count('(says/Pd * (is/Pd hyperbase/Cp great/C))'), 1)
        self.assertEqual(self.hg.count('(says/Pd * (is/Pd * *))'), 1)

    def test_count_open_ended(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(self.hg.count('(* hyperbase/Cp * ...)'), 1)
        self.assertEqual(self.hg.count('(is/Pd hyperbase/Cp * ...)'), 1)
        self.assertEqual(self.hg.count('(x * * ...)'), 0)
        self.assertEqual(
            self.hg.count('(says/Pd * (is/Pd hyperbase/Cp great/C) ...)'), 2)

    def test_count_star(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(self.hg.count('*'), 10)

    def test_count_at(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(self.hg.count('.'), 6)

    def test_count_amp(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(self.hg.count('(*)'), 4)

    def test_count_non_atomic_pred(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd ) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(self.hg.count('((is/M playing/Pd) ...)'), 1)
        self.assertEqual(self.hg.count('((is/M playing/Pd) * *)'), 1)
        self.assertEqual(self.hg.count('((is/M playing/Pd) . (*))'), 1)
        self.assertEqual(self.hg.count('((is/M playing/Pd) . .)'), 0)
        self.assertEqual(self.hg.count('((is/M playing/Pd) (*) (*))'), 0)
        self.assertEqual(self.hg.count('(* mary/Cp.s *)'), 1)
        self.assertEqual(self.hg.count('(mary/Cp.s * *)'), 0)
        self.assertEqual(self.hg.count('(* * (a/Md ((very/M old/Ma) violin/Cn.s)))'), 1)
        self.assertEqual(self.hg.count('((a/Md ((very/M old/Ma) violin/Cn.s)) * *)'), 0)

    def test_count_non_atomic_pred_vars(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd ) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(self.hg.count('((is/M playing/Pd) *X *Y)'), 1)
        self.assertEqual(self.hg.count('((is/M playing/Pd) .X (Y))'), 1)
        self.assertEqual(self.hg.count('((is/M playing/Pd) .X .Y)'), 0)
        self.assertEqual(self.hg.count('((is/M playing/Pd) (X) (Y))'), 0)
        self.assertEqual(self.hg.count('(* mary/Cp.s X)'), 1)
        self.assertEqual(self.hg.count('(mary/Cp.s X Y)'), 0)
        self.assertEqual(self.hg.count('(X Y (a/Md ((very/M old/Ma) violin/Cn.s)))'), 1)
        self.assertEqual(self.hg.count('((a/Md ((very/M old/Ma) violin/Cn.s)) X Y)'), 0)

    def test_count_pred_with_roles(self):
        self.hg.destroy()
        self.hg.add('(says/Pd.so.|f--3s-/en mary/C hello/C)')
        self.hg.add('(says/Pd.os.|f--3s-/en hello/C mary/C)')
        self.assertEqual(self.hg.count('(says/Pd.so.|f--3s-/en * *)'), 1)

    def test_count_pred_with_roles_and_ellipsis(self):
        self.hg.destroy()
        edge = hedge(('(is/Mv.|f--3s-/en playing/Pd.so.|pg----/en)', 'mary/Cp.s/en',
                      '(a/Md/en ((very/M/en old/Ma/en) violin/Cc.s/en))'))
        pattern = hedge('((is/Mv.|f--3s-/en playing/Pd.so.|pg----/en) ...)')
        self.hg.add(edge)
        self.assertEqual(self.hg.count(pattern), 1)

    def test_count_pred_with_deep_pattern(self):
        self.hg.destroy()
        edge = hedge(('(is/Mv.|f--3s-/en playing/Pd.so.|pg----/en)', 'mary/Cp.s/en',
                      '(a/Md/en ((very/M/en old/Ma/en) violin/Cc.s/en))'))
        pattern = hedge('(*/Pd.so */C (*/M ((*/M */M) violin/Cc.s/en)))')
        self.hg.add(edge)
        self.assertEqual(self.hg.count(pattern), 1)

    def test_match(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.match('((is/M playing/Pd) *X *Y)')),
                         [(edge, [{'X': hedge('mary/Cp.s'), 'Y': hedge('(a/Md ((very/M old/Ma) violin/Cn.s))')}])])
        self.assertEqual(list(self.hg.match('(PRED mary/Cp.s X)')),
                         [(edge, [{'PRED': hedge('(is/M playing/Pd)'), 'X': hedge('(a/Md ((very/M old/Ma) violin/Cn.s))')}])])
        self.assertEqual(list(self.hg.match('(X Y (a/Md ((very/M old/Ma) violin/Cn.s)))')),
                         [(edge, [{'X': hedge('(is/M playing/Pd)'), 'Y': hedge('mary/Cp.s')}])])

    def test_match_argroles1(self):
        self.hg.destroy()
        edge = hedge('((is/M playing/Pd.so) mary/Cp.s (a/Md ((very/M old/Ma) violin/Cn.s)))')
        self.hg.add(edge)
        self.assertEqual(list(self.hg.match('((is/M playing/Pd.so) *X *Y)')),
                         [(edge, [{'X': hedge('mary/Cp.s'), 'Y': hedge('(a/Md ((very/M old/Ma) violin/Cn.s))')}])])
        self.assertEqual(list(self.hg.match('(PRED mary/Cp.s X)')),
                         [(edge, [{'PRED': hedge('(is/M playing/Pd.so)'),
                                   'X': hedge('(a/Md ((very/M old/Ma) violin/Cn.s))')}])])
        self.assertEqual(list(self.hg.match('(X Y (a/Md ((very/M old/Ma) violin/Cn.s)))')),
                         [(edge, [{'X': hedge('(is/M playing/Pd.so)'), 'Y': hedge('mary/Cp.s')}])])
        self.assertEqual(list(self.hg.match('(*/Pd.so X Y)')),
                         [(edge, [{'X': hedge('mary/Cp.s'), 'Y': hedge('(a/Md ((very/M old/Ma) violin/Cn.s))')}])])

    def test_match_argroles2(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/M sky/C))')
        edge2 = hedge('(is/Pd.sc (the/M sky/C) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(list(self.hg.match('(is/Pd.sc OBJ/C blue/Ca)')), [(edge2, [{'OBJ': hedge('(the/M sky/C)')}])])
        self.assertEqual(list(self.hg.match('(is/P.sc OBJ/C blue/C)')), [(edge2, [{'OBJ': hedge('(the/M sky/C)')}])])

    def test_match_argroles_curly_brackets1(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/M sky/C))')
        edge2 = hedge('(is/Pd.sc (the/M sky/C) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(list(self.hg.match('(is/P.{sc} OBJ/C PROP)')),
                         [(edge1, [{'OBJ': hedge('(the/M sky/C)'), 'PROP': hedge('blue/Ca')}]),
                          (edge2, [{'OBJ': hedge('(the/M sky/C)'), 'PROP': hedge('blue/Ca')}])])

    def test_match_argroles_curly_brackets2(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/Md sky/Cc))')
        edge2 = hedge('(is/Pd.sc (the/Md sky/Cc) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(list(self.hg.match('(is/P.{sc} (the/M sky/C) blue/C)')), [(edge1, [{}]), (edge2, [{}])])

    def test_match_fun_patterns(self):
        self.hg.destroy()
        edge1 = hedge('((not/M is/Pd.cs) blue/Ca (the/M sky/C))')
        edge2 = hedge('(is/Pd.sc (the/M sky/C) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(
            list(self.hg.match('((atoms is/P.{sc}) (var */C OBJ) (var * PROP))')),
            [(edge1, [{'OBJ': hedge('(the/M sky/C)'), 'PROP': hedge('blue/Ca')}]),
             (edge2, [{'OBJ': hedge('(the/M sky/C)'), 'PROP': hedge('blue/Ca')}])])

    def test_match_strict1(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/Md sky/Cc))')
        edge2 = hedge('(is/Pd.sc (the/Md sky/Cc) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(list(self.hg.match('(is/P.sc (the/M sky/C) blue/C)', strict=True)), [])

    def test_match_strict2(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/Md sky/Cc))')
        edge2 = hedge('(is/Pd.sc (the/Md sky/Cc) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        self.assertEqual(list(self.hg.match('(is/Pd.sc (the/Md sky/Cc) blue/Ca)', strict=True)), [(edge2, [{}])])

    def test_match_argroles_curly_brackets_strict(self):
        self.hg.destroy()
        edge1 = hedge('(is/Pd.cs blue/Ca (the/Md sky/Cc))')
        edge2 = hedge('(is/Pd.sc (the/Md sky/Cc) blue/Ca)')

        self.hg.add(edge1)
        self.hg.add(edge2)

        with self.assertRaises(RuntimeError):
            list(self.hg.match('(is/P.{sc} (the/Md sky/Cc) blue/Ca)', strict=True))

    def test_star(self):
        self.hg.destroy()
        edge1 = hedge('(is hyperbase/1 great/1)')
        self.hg.add(edge1)
        self.assertEqual(list(self.hg.star(hedge('hyperbase/1'))), [edge1])
        self.assertEqual(list(self.hg.star(hedge('hyperbase/2'))), [])
        self.hg.remove(edge1)
        edge2 = hedge('(says mary/1 (is hyperbase/1 great/1))')
        self.hg.add(edge2)
        self.assertEqual(list(self.hg.star(edge1)), [edge2])

    def test_star_limit(self):
        self.hg.destroy()
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(is hyperbase/1 great/2)')
        self.hg.add('(is hyperbase/1 great/3)')
        center = hedge('hyperbase/1')
        self.assertEqual(len(list(self.hg.star(center))), 3)
        self.assertEqual(len(list(self.hg.star(center, limit=1))), 1)
        self.assertEqual(len(list(self.hg.star(center, limit=2))), 2)
        self.assertEqual(len(list(self.hg.star(center, limit=10))), 3)

    def test_atoms_with_root(self):
        self.hg.destroy()
        self.hg.add('(is hyperbase/1 great/1)')
        self.assertEqual(list(self.hg.atoms_with_root('hyperbase')), [hedge('hyperbase/1')])
        self.hg.add('(is hyperbase/2 great/1)')
        self.assertEqual(list(self.hg.atoms_with_root('hyperbase')), [hedge('hyperbase/1'), hedge('hyperbase/2')])

    def test_edges_with_edges(self):
        self.hg.destroy()
        edge1 = hedge('(is hyperbase/1 great/1)')
        self.hg.add(edge1)
        edge2 = hedge('(is hyperbase/1 great/2)')
        self.hg.add(edge2)
        self.assertEqual(list(self.hg.edges_with_edges((hedge('hyperbase/1'),), 'great')), [edge1, edge2])
        self.assertEqual(list(self.hg.edges_with_edges((hedge('hyperbase/1'), hedge('is')), 'great')), [edge1, edge2])
        self.assertEqual(list(self.hg.edges_with_edges((hedge('hyperbase/1'),), 'grea')), [])

    def test_edges_with_edges2(self):
        self.hg.destroy()
        self.hg.add(hedge('(syns/P (of/B city/C lights/C) paris/C)'))
        self.hg.add(hedge('(syns/P (of/B city/C light/C) paris/C)'))
        self.hg.add(hedge('(going/P i/C (of/B city/C lights/C))'))

        res = self.hg.edges_with_edges([hedge('(of/B city/C lights/C)')])
        res = set([edge.to_str() for edge in res])
        self.assertEqual(res, {'(syns/P (of/B city/C lights/C) paris/C)', '(going/P i/C (of/B city/C lights/C))'})

        res = self.hg.edges_with_edges([hedge('(of/B city/C lights/C)'), hedge('paris/C')])
        res = set([edge.to_str() for edge in res])
        self.assertEqual(res, {'(syns/P (of/B city/C lights/C) paris/C)'})

        res = self.hg.edges_with_edges([hedge('(of/B city/C lights/C)'), hedge('paris/C')], 'syns')
        res = set([edge.to_str() for edge in res])
        self.assertEqual(res, {'(syns/P (of/B city/C lights/C) paris/C)'})

    # set_attribute, inc_attribute, dec_attribute, get_str_attribute,
    # get_int_attribute, get_float_attribute
    def test_attributes_atom(self):
        self.hg.destroy()
        self.hg.add('(is hyperbase/1 great/1)')
        atom = hedge('hyperbase/1')
        self.assertEqual(self.hg.get_int_attribute(atom, 'foo'), None)
        self.assertEqual(self.hg.get_int_attribute(atom, 'foo', 0), 0)
        self.hg.set_attribute(atom, 'foo', 66)
        self.assertEqual(self.hg.get_int_attribute(atom, 'foo'), 66)
        self.hg.inc_attribute(atom, 'foo')
        self.assertEqual(self.hg.get_int_attribute(atom, 'foo'), 67)
        self.hg.dec_attribute(atom, 'foo')
        self.assertEqual(self.hg.get_int_attribute(atom, 'foo'), 66)
        self.hg.set_attribute(atom, 'bar', -.77)
        self.assertEqual(self.hg.get_float_attribute(atom, 'bar'), -.77)
        self.hg.set_attribute(atom, 'label', '{"abc": "defg", "": 23}')
        self.assertEqual(self.hg.get_str_attribute(atom, 'label'), '{"abc": "defg", "": 23}')

    # set_attribute, inc_attribute, dec_attribute, get_str_attribute,
    # get_int_attribute, get_float_attribute
    def test_attributes_edge(self):
        self.hg.destroy()
        edge = hedge('(is hyperbase/1 great/1)')
        self.hg.add(edge)
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), None)
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo', 0), 0)
        self.hg.set_attribute(edge, 'foo', 66)
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 66)
        self.hg.inc_attribute(edge, 'foo')
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 67)
        self.hg.dec_attribute(edge, 'foo')
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 66)
        self.hg.set_attribute(edge, 'bar', -.77)
        self.assertEqual(self.hg.get_float_attribute(edge, 'bar'), -.77)
        self.hg.set_attribute(edge, 'label', '{"abc": "defg", "": 23}')
        self.assertEqual(self.hg.get_str_attribute(edge, 'label'), '{"abc": "defg", "": 23}')

    # increment attribute that does not exist yet
    def test_inc_attributes_does_not_exist(self):
        self.hg.destroy()
        edge = hedge('(is hyperbase/1 great/1)')
        self.hg.add(edge)
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), None)
        self.hg.inc_attribute(edge, 'foo')
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 1)
        self.hg.inc_attribute(edge, 'foo')
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 2)

    def test_degrees(self):
        self.hg.destroy()
        hyperbase = hedge('hyperbase/1')
        great = hedge('great/1')
        self.assertEqual(self.hg.degree(hyperbase), 0)
        self.hg.add('(is hyperbase/1 great/1)')
        self.assertEqual(self.hg.degree(hyperbase), 1)
        self.assertEqual(self.hg.degree(great), 1)
        self.hg.add('(size hyperbase/1 7)')
        self.assertEqual(self.hg.degree(hyperbase), 2)
        self.assertEqual(self.hg.degree(great), 1)
        self.hg.remove(hedge('(is hyperbase/1 great/1)'))
        self.assertEqual(self.hg.degree(hyperbase), 1)
        self.assertEqual(self.hg.degree(great), 0)
        self.hg.remove(hedge('(size hyperbase/1 7)'))
        self.assertEqual(self.hg.degree(hyperbase), 0)

    def test_deep_degrees(self):
        self.hg.destroy()
        edge1 = hedge('((is/M going/P) mary/C (to (the/M gym/C)))')
        self.hg.add(edge1)
        mary = hedge('mary/C')
        gym = hedge('gym/C')
        is_going = hedge('(is/M going/P)')
        self.assertEqual(self.hg.deep_degree(edge1), 0)
        self.assertEqual(self.hg.degree(mary), 1)
        self.assertEqual(self.hg.deep_degree(mary), 1)
        self.assertEqual(self.hg.degree(gym), 0)
        self.assertEqual(self.hg.deep_degree(gym), 1)
        self.assertEqual(self.hg.degree(is_going), 1)
        self.assertEqual(self.hg.deep_degree(is_going), 1)
        self.assertEqual(self.hg.deep_degree(gym), 1)
        edge2 = hedge('((is/M going/P) john/C (to (the/M gym/C)))')
        self.hg.add(edge2)
        self.assertEqual(self.hg.degree(gym), 0)
        self.assertEqual(self.hg.deep_degree(gym), 2)
        self.assertEqual(self.hg.degree(is_going), 2)
        self.assertEqual(self.hg.deep_degree(is_going), 2)

    def test_ego(self):
        self.hg.destroy()
        self.hg.add('(is hyperbase/1 great/1)')
        self.hg.add('(is hyperbase/1 great/2)')
        self.assertEqual(self.hg.ego(hedge('hyperbase/1')),
                         {hedge('hyperbase/1'), hedge('is'), hedge('great/1'), hedge('great/2')})

    def test_remove_by_pattern(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/Cp great/C)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C) extra/C)')
        self.assertEqual(set(self.hg.search('(says/Pd * (is/Pd hyperbase/Cp great/C))')),
                         {hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')})
        self.hg.remove_by_pattern('(says/Pd * *)')
        self.assertFalse(self.hg.exists(hedge('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C))')))
        self.assertTrue(self.hg.exists(hedge('(is/Pd hyperbase/Cp great/C)')))

    def test_root_degrees(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/C great/C/1)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cp great/C/2))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/Cs great/C) extra/C)')
        self.assertEqual(self.hg.root_degrees(hedge('hyperbase/Cp')), (1, 3))
        self.assertEqual(self.hg.root_degrees(hedge('great/C')), (1, 3))
        self.assertEqual(self.hg.root_degrees(hedge('says/Pd')), (3, 3))

    def test_sum_degree(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/C great/C/1)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/C great/C/2))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/C great/C) extra/C)')
        self.assertEqual(self.hg.sum_degree({hedge('hyperbase/C'), hedge('says/Pd')}), 4)

    def test_sum_deep_degree(self):
        self.hg.destroy()
        self.hg.add('(is/Pd hyperbase/C great/C/1)')
        self.hg.add('(says/Pd mary/Cp)')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/C great/C/2))')
        self.hg.add('(says/Pd mary/Cp (is/Pd hyperbase/C great/C) extra/C)')
        self.assertEqual(self.hg.sum_deep_degree({hedge('hyperbase/C'), hedge('says/Pd')}), 6)

    def test_primary_1(self):
        self.hg.destroy()
        edge1 = hedge('((is/M going/P) mary/C (to (the/M gym/C)))')
        self.hg.add(edge1)
        self.assertTrue(self.hg.is_primary(edge1))
        self.hg.set_primary(edge1, False)
        self.assertFalse(self.hg.is_primary(edge1))
        self.assertFalse(self.hg.is_primary(hedge('(is/M going/P)')))
        self.hg.set_primary(hedge('(is/M going/P)'), True)
        self.assertTrue(self.hg.is_primary(hedge('(is/M going/P)')))
        self.assertFalse(self.hg.is_primary(hedge('mary/C')))
        self.hg.set_primary(hedge('mary/C'), True)
        self.assertTrue(self.hg.is_primary(hedge('mary/C')))

    def test_primary_2(self):
        self.hg.destroy()
        edge1 = hedge('((is/M going/P) mary/C (to (the/M gym/C)))')
        self.hg.add(edge1, primary=False)
        self.assertFalse(self.hg.is_primary(edge1))
        self.hg.set_primary(edge1, True)
        self.assertTrue(self.hg.is_primary(edge1))
        self.assertFalse(self.hg.is_primary(hedge('(is/M going/P)')))
        self.hg.set_primary(hedge('(is/M going/P)'), True)
        self.assertTrue(self.hg.is_primary(hedge('(is/M going/P)')))
        self.assertFalse(self.hg.is_primary(hedge('mary/C')))
        self.hg.set_primary(hedge('mary/C'), True)
        self.assertTrue(self.hg.is_primary(hedge('mary/C')))

    def test_add_large_edge(self):
        s1 = ("(title/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(this/Md/en year/Cc.s/en))))")
        self.hg.destroy()
        self.hg.add(s1)
        self.assertTrue(self.hg.exists(s1))

    def test_add_large_edges(self):
        s1 = ("(title/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(this/Md/en year/Cc.s/en))))")
        s2 = ("(titles/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(this/Md/en year/Cc.s/en))))")
        s3 = ("(title/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(these/Md/en years/Cc.p/en))))")
        self.hg.destroy()
        self.hg.add(s1)
        self.assertTrue(self.hg.exists(s1))
        self.assertFalse(self.hg.exists(s2))
        self.assertFalse(self.hg.exists(s3))
        self.hg.add(s2)
        self.assertTrue(self.hg.exists(s2))
        self.assertFalse(self.hg.exists(s3))
        self.hg.add(s3)
        self.assertTrue(self.hg.exists(s3))

    def test_large_edges_all(self):
        s1 = ("(title/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(this/Md/en year/Cc.s/en))))")
        s2 = ("(titles/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(this/Md/en year/Cc.s/en))))")
        s3 = ("(title/P/.reddit anutensil/C/reddit.user "
              "(discovered/Pd.<f----.sr/en (+/B.aam/. energy/Cp.s/en "
              "company/Cp.s/en staff/Cp.s/en) (working/P.------.x/en "
              "(at/T/en (+/B.am/. climate/Cp.s/en ministry/Cp.s/en)))) "
              "(says/Pd.|f--3s.sr/en (green/Ma/en "
              "(+/B.am/. party/Cc.s/en mp/Cp.s/en)) "
              "(have/P.|f----.so/en (+/B.aam/. fossil/Ca/en fuel/Cc.s/en "
              "giants/Cc.p/en) (no/Md/en (there/M/en place/Cc.s/en)))) "
              "((even/M/en 's/Pd.|f--3s.s/en more/M/en outrageous/Ma/en "
              "taxpayers/Cc.p/en ((are/Mv.|f----/en footing/P.|pg---.o/en) "
              "(the/Md/en bill/Cc.s/en))) it/Ci/en) "
              "('s/Pd.|f--3s.xsr/en (at/T/en (:/J/. (a/Md/en time/Cc.s/en) "
              "((are/Mv.|f----/en struggling/P.|pg---.s/en) "
              "(+/B.aam/. british/Ca/en gas/Cp.s/en customers/Cc.p/en)))) "
              "it/Ci/en ((to/Mi/en make/P.-i----.ox/en) "
              "(£/M/en (+/B.am/. 1_4bn/C#/en profits/Cc.p/en)) "
              "(these/Md/en years/Cc.p/en))))")
        self.hg.destroy()
        self.hg.add(s1)
        self.hg.add(s2)
        self.hg.add(s3)
        res = set([edge.to_str() for edge in self.hg.all()])
        self.assertTrue(s1 in res)
        self.assertTrue(s2 in res)

    def test_sequence1(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        self.hg.add_to_sequence('test_seq', edge1)
        self.assertTrue(self.hg.exists((const.sequence_connector, 'test_seq', '0', edge1)))

    def test_sequence2(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        self.hg.add_to_sequence('test_seq', edge1)
        edges = list(self.hg.sequence('test_seq'))
        self.assertEqual(edges, [edge1])

    def test_sequence3(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        edge2 = hedge('(is/P this/C (second/M element/C))')
        self.hg.add_to_sequence('test_seq', edge1)
        self.hg.add_to_sequence('test_seq', edge2)
        edges = list(self.hg.sequence('test_seq'))
        self.assertEqual(edges, [edge1, edge2])

    def test_sequence4(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        edge2 = hedge('(is/P this/C (second/M element/C))')
        edge3 = hedge('(is/P this/C (third/M element/C))')
        self.hg.add_to_sequence('test_seq', edge1)
        self.hg.add_to_sequence('test_seq', edge2)
        self.hg.add_to_sequence('test_seq', edge3)
        edges = list(self.hg.sequence('test_seq'))
        self.assertEqual(edges, [edge1, edge2, edge3])

    def test_sequences1(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        edge2 = hedge('(is/P this/C (second/M element/C))')
        edge3 = hedge('(is/P this/C (third/M element/C))')
        self.hg.add_to_sequence('seq0', edge1)
        self.hg.add_to_sequence('seq1', edge2)
        self.hg.add_to_sequence('seq2', edge3)
        sequences = set(self.hg.sequences())
        self.assertEqual(sequences, {'seq0', 'seq1', 'seq2'})

    def test_sequences2(self):
        self.hg.destroy()
        edge1 = hedge('(is/P this/C (first/M element/C))')
        edge2 = hedge('(is/P this/C (second/M element/C))')
        edge3 = hedge('(is/P this/C (third/M element/C))')
        self.hg.add_to_sequence('seq0', edge1)
        self.hg.add_to_sequence('seq1', edge2)
        self.hg.add_to_sequence('seq1', edge3)
        sequences = set(self.hg.sequences())
        self.assertEqual(sequences, {'seq0', 'seq1'})

    def test_sequence5(self):
        self.hg.destroy()
        edges = list(self.hg.sequence('test_seq'))
        self.assertEqual(edges, [])

    def test_add_with_attributes1(self):
        self.hg.destroy()
        edge = hedge('(is hyperbase/1 great/1)')
        self.hg.add_with_attributes(edge, {'p': 1, 'd': 10, 'dd': 20, 'foo': 777, 'bar': -.77, 'xx': 'def'})
        self.assertTrue(self.hg.is_primary(edge))
        self.assertEqual(self.hg.degree(edge), 10)
        self.assertEqual(self.hg.deep_degree(edge), 20)
        self.assertEqual(self.hg.get_int_attribute(edge, 'foo'), 777)
        self.assertEqual(self.hg.get_float_attribute(edge, 'bar'), -.77)
        self.assertEqual(self.hg.get_str_attribute(edge, 'xx'), 'def')

    def test_add_with_attributes2(self):
        self.hg.destroy()
        edge = hedge('(is hyperbase/1 great/1)')
        self.hg.add_with_attributes(edge, {'p': 0, 'd': 10, 'dd': 20, 'foo': 777, 'bar': -.77, 'xx': 'def'})
        self.assertFalse(self.hg.is_primary(edge))

    def test_add_with_attributes_search(self):
        self.hg.destroy()
        edge = hedge('(is hyperbase/1 great/1)')
        self.hg.add_with_attributes(edge, {'p': 1, 'd': 10, 'dd': 20, 'foo': 777, 'bar': -.77, 'xx': 'def'})
        results = set(self.hg.search('(is * *)'))
        self.assertEqual(results, set([edge]))

    def test_non_primary_to_primary(self):
        self.hg.destroy()
        edge = hedge('(is/P (the/M sun/C) shining/C)')
        self.hg.add(edge, primary=False)
        self.assertFalse(self.hg.is_primary(edge))
        self.hg.add(edge, primary=True)
        self.assertTrue(self.hg.is_primary(edge))

    def test_batch_adds(self):
        self.hg.destroy()
        self.hg.close()
        edges = []
        for i in range(10):
            edges.append(hedge('(is/P {}/C number/C)'.format(i)))
        with hopen(self.hg_str) as hg:
            for edge in edges:
                hg.add(edge)
        self.hg = hgraph(self.hg_str)
        for edge in edges:
            self.assertTrue(self.hg.exists(edge))
