import unittest

from hyperbase.hyperedge import hedge, build_atom, str2atom, split_edge_str


class TestHyperedge(unittest.TestCase):
    def test_hedge1(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').to_str(), '(is hypercore/1 great/1)')

    def test_hedge2(self):
        self.assertEqual(hedge('(src hypercore/1 (is hypercore/1 great/1))').to_str(),
                         '(src hypercore/1 (is hypercore/1 great/1))')

    def test_hedge3(self):
        self.assertEqual(hedge('((is my) brain/1 (super great/1))').to_str(), '((is my) brain/1 (super great/1))')

    def test_hedge4(self):
        self.assertEqual(hedge('.'), ('.',))

    def test_hedge5(self):
        self.assertEqual(hedge('(VAR/C)').to_str(), '(VAR/C)')

    def test_hedge6(self):
        self.assertEqual(hedge('((is my) (brain/1) (super great/1))').to_str(), '((is my) (brain/1) (super great/1))')

    def test_atom1(self):
        self.assertTrue(hedge('a').atom)

    def test_atom2(self):
        self.assertTrue(hedge('hypercore/C').atom)

    def test_atom3(self):
        self.assertTrue(hedge('hypercore/Cn.p/1').atom)

    def test_atom4(self):
        self.assertTrue(hedge('(X/C)').atom)

    def test_atom5(self):
        self.assertFalse(hedge('(is/Pd.sc hypercore/Cp.s great/C)').atom)

    def test_atom_parts1(self):
        self.assertEqual(hedge('hypercore/C').parts(), ['hypercore', 'C'])

    def test_atom_parts2(self):
        self.assertEqual(hedge('hypercore').parts(), ['hypercore'])

    def test_atom_parts3(self):
        self.assertEqual(hedge('go/P.so/1').parts(), ['go', 'P.so', '1'])

    def test_atom_parts4(self):
        self.assertEqual(hedge('(X/P.so/1)').parts(), ['X', 'P.so', '1'])

    def test_root1(self):
        self.assertEqual(hedge('hypercore/C').root(), 'hypercore')

    def test_root2(self):
        self.assertEqual(hedge('go/P.so/1').root(), 'go')

    def test_build_atom1(self):
        self.assertEqual(build_atom('hypercore', 'C'), hedge('hypercore/C'))

    def test_build_atom2(self):
        self.assertEqual(build_atom('go', 'P.so', '1'), hedge('go/P.so/1'))

    def test_replace_atom_part1(self):
        self.assertEqual(hedge('hypercore/C').replace_atom_part(0, 'x'), hedge('x/C'))

    def test_replace_atom_part2(self):
        self.assertEqual(hedge('xxx/1/yyy').replace_atom_part(1, '77'), hedge('xxx/77/yyy'))

    def test_replace_atom_part3(self):
        self.assertEqual(hedge('(XXX/1/yyy)').replace_atom_part(1, '77'), hedge('(XXX/77/yyy)'))

    def test_str2atom1(self):
        self.assertEqual(str2atom('abc'), 'abc')

    def test_str2atom2(self):
        self.assertEqual(str2atom('abc%'), 'abc%25')

    def test_str2atom3(self):
        self.assertEqual(str2atom('/abc'), '%2fabc')

    def test_str2atom4(self):
        self.assertEqual(str2atom('a bc'), 'a%20bc')

    def test_str2atom5(self):
        self.assertEqual(str2atom('ab(c'), 'ab%28c')

    def test_str2atom6(self):
        self.assertEqual(str2atom('abc)'), 'abc%29')

    def test_str2atom7(self):
        self.assertEqual(str2atom('.abc'), '%2eabc')

    def test_str2atom8(self):
        self.assertEqual(str2atom('a*bc'), 'a%2abc')

    def test_str2atom9(self):
        self.assertEqual(str2atom('ab&c'), 'ab%26c')

    def test_str2atom10(self):
        self.assertEqual(str2atom('abc@'), 'abc%40')

    def test_str2atom11(self):
        self.assertEqual(str2atom('graph brain/(1).'), 'graph%20brain%2f%281%29%2e')

    def test_split_edge_str1(self):
        self.assertEqual(split_edge_str('is hypercore/1 great/1'), ('is', 'hypercore/1', 'great/1'))

    def test_split_edge_str2(self):
        self.assertEqual(split_edge_str('size hypercore/1 7'), ('size', 'hypercore/1', '7'))

    def test_split_edge_str3(self):
        self.assertEqual(split_edge_str('size hypercore/1 7.0'), ('size', 'hypercore/1', '7.0'))

    def test_split_edge_str4(self):
        self.assertEqual(split_edge_str('size hypercore/1 -7'), ('size', 'hypercore/1', '-7'))

    def test_split_edge_str5(self):
        self.assertEqual(split_edge_str('size hypercore/1 -7.0'), ('size', 'hypercore/1', '-7.0'))

    def test_split_edge_str6(self):
        self.assertEqual(split_edge_str('src hypercore/1 (is hypercore/1 great/1)'),
                         ('src', 'hypercore/1', '(is hypercore/1 great/1)'))

    def test_to_str(self):
        self.assertEqual(
            hedge('(is hypercore/C great/C)').to_str(), '(is hypercore/C great/C)')
        self.assertEqual(hedge('(src hypercore/C (is hypercore/C great/C))').to_str(),
                         '(src hypercore/C (is hypercore/C great/C))')

    def test_ent2str_roots_only(self):
        self.assertEqual(hedge('(is hypercore/C great/C)').to_str(roots_only=True), '(is hypercore great)')
        self.assertEqual(hedge('(src hypercore/C (is hypercore/C great/C))').to_str(roots_only=True),
                         '(src hypercore (is hypercore great))')

    def test_label1(self):
        self.assertEqual(hedge('graph%20brain%2f%281%29%2e/Cn.s/.').label(), 'graph brain/(1).')

    def test_label2(self):
        self.assertEqual(hedge('(red/M shoes/C)').label(), 'red shoes')

    def test_label3(self):
        self.assertEqual(hedge('(of/B capital/C germany/C)').label(), 'capital of germany')

    def test_label4(self):
        self.assertEqual(hedge('(+/B/. capital/C germany/C)').label(), 'capital germany')

    def test_label5(self):
        self.assertEqual(hedge('(of/B capital/C west/C germany/C)').label(), 'capital of west germany')

    def test_label6(self):
        self.assertEqual(hedge('(of/B capital/C (and/B belgium/C europe/C))').label(), 'capital of belgium and europe')

    def test_connector_atom1(self):
        edge = hedge('(is/P.sc hypercore/1 great/1)')
        self.assertEqual(edge.connector_atom(), hedge('is/P.sc'))

    def test_connector_atom2(self):
        edge = hedge('((not/M is/P.sc) hypercore/1 great/1)')
        self.assertEqual(edge.connector_atom(), hedge('is/P.sc'))

    def test_connector_atom3(self):
        edge = hedge('((maybe/M (not/M is/P.sc)) hypercore/1 great/1)')
        self.assertEqual(edge.connector_atom(), hedge('is/P.sc'))

    def test_connector_atom4(self):
        edge = hedge('(((and/J not/M nope/M) is/P.sc) hypercore/1 great/1)')
        self.assertEqual(edge.connector_atom(), hedge('is/P.sc'))

    def test_atoms1(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').atoms(),
                         {hedge('is'), hedge('hypercore/1'), hedge('great/1')})

    def test_atoms2(self):
        self.assertEqual(hedge('(src hypercore/2 (is hypercore/1 great/1))').atoms(),
                         {hedge('is'), hedge('hypercore/1'), hedge('great/1'), hedge('src'), hedge('hypercore/2')})

    def test_atoms3(self):
        self.assertEqual(hedge('hypercore/1').atoms(), {hedge('hypercore/1')})

    def test_atoms4(self):
        edge = hedge('(the/Md (of/Br mayor/Cc (the/Md city/Cs)))')
        self.assertEqual(edge.atoms(), {hedge('the/Md'), hedge('of/Br'), hedge('mayor/Cc'), hedge('city/Cs')})
        self.assertEqual(hedge('(is (X/C) great/1)').atoms(), {hedge('is'), hedge('(X/C)'), hedge('great/1')})

    def test_all_atoms1(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').all_atoms(),
                         [hedge('is'), hedge('hypercore/1'), hedge('great/1')])

    def test_all_atoms2(self):
        self.assertEqual(hedge('(src hypercore/2 (is hypercore/1 great/1))').all_atoms(),
                         [hedge('src'), hedge('hypercore/2'), hedge('is'), hedge('hypercore/1'), hedge('great/1')])

    def test_all_atoms3(self):
        self.assertEqual(hedge('hypercore/1').all_atoms(), [hedge('hypercore/1')])

    def test_all_atoms4(self):
        edge = hedge('(the/Md (of/Br mayor/Cc (the/Md city/Cs)))')
        self.assertEqual(edge.all_atoms(),
                         [hedge('the/Md'), hedge('of/Br'), hedge('mayor/Cc'), hedge('the/Md'), hedge('city/Cs')])

    def test_all_atoms5(self):
        edge = hedge('(the/Md (of/Br (X/C) (the/Md city/Cs)))')
        self.assertEqual(edge.all_atoms(),
                         [hedge('the/Md'), hedge('of/Br'), hedge('(X/C)'), hedge('the/Md'), hedge('city/Cs')])

    def test_size1(self):
        self.assertEqual(hedge('hypercore/1').size(), 1)

    def test_size2(self):
        self.assertEqual(hedge('(X/C)').size(), 1)

    def test_size3(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').size(), 3)

    def test_size4(self):
        self.assertEqual(hedge('(is hypercore/1 (super great/1))').size(), 4)

    def test_depth1(self):
        self.assertEqual(hedge('hypercore/1').depth(), 0)

    def test_depth2(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').depth(), 1)

    def test_depth3(self):
        self.assertEqual(hedge('(is hypercore/1 (super great/1))').depth(), 2)

    def test_depth4(self):
        self.assertEqual(hedge('(is hypercore/1 (super (X/C)))').depth(), 2)

    def test_roots1(self):
        self.assertEqual(hedge('hypercore/1').roots(), hedge('hypercore'))

    def test_roots2(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').roots(), hedge('(is hypercore great)'))

    def test_roots3(self):
        self.assertEqual(hedge('(is hypercore/1 (super great/1))').roots(), hedge('(is hypercore (super great))'))

    def test_contains(self):
        edge = hedge('(is/Pd.sc piron/C (of/B capital/C piripiri/C))')
        self.assertTrue(edge.contains(hedge('is/Pd.sc')))
        self.assertTrue(edge.contains(hedge('piron/C')))
        self.assertTrue(edge.contains(hedge('(of/B capital/C piripiri/C)')))
        self.assertFalse(edge.contains(hedge('piripiri/C')))
        self.assertFalse(edge.contains(hedge('1111/C')))

    def test_contains_pares_atom(self):
        edge = hedge('(is/Pd.sc (X/C) (of/B capital/C piripiri/C))')
        self.assertTrue(edge.contains(hedge('is/Pd.sc')))
        self.assertTrue(edge.contains(hedge('(X/C)')))
        self.assertTrue(edge.contains(hedge('(of/B capital/C piripiri/C)')))
        self.assertFalse(edge.contains(hedge('piripiri/C')))
        self.assertFalse(edge.contains(hedge('1111/C')))

    def test_contains_deep(self):
        edge = hedge('(is/Pd.sc piron/C (of/B capital/C piripiri/C))')
        self.assertTrue(edge.contains(hedge('is/Pd.sc'), deep=True))
        self.assertTrue(edge.contains(hedge('piron/C'), deep=True))
        self.assertTrue(edge.contains(hedge('(of/B capital/C piripiri/C)'), deep=True))
        self.assertTrue(edge.contains(hedge('piripiri/C'), deep=True))
        self.assertFalse(edge.contains(hedge('1111/C'), deep=True))

    def test_contains_deep_pares_atom(self):
        edge = hedge('(is/Pd.sc piron/C (of/B capital/C (XYZ)))')
        self.assertTrue(edge.contains(hedge('is/Pd.sc'), deep=True))
        self.assertTrue(edge.contains(hedge('piron/C'), deep=True))
        self.assertTrue(edge.contains(hedge('(of/B capital/C (XYZ))'), deep=True))
        self.assertTrue(edge.contains(hedge('(XYZ)'), deep=True))
        self.assertFalse(edge.contains(hedge('1111/C'), deep=True))

    def test_subedges1(self):
        self.assertEqual(hedge('hypercore/1').subedges(), {hedge('hypercore/1')})

    def test_subedges2(self):
        self.assertEqual(hedge('(is hypercore/1 great/1)').subedges(),
                         {hedge('is'), hedge('hypercore/1'), hedge('great/1'), hedge('(is hypercore/1 great/1)')})

    def test_subedges3(self):
        self.assertEqual(hedge('(is hypercore/1 (super great/1))').subedges(),
                         {hedge('is'), hedge('hypercore/1'), hedge('super'), hedge('great/1'),
                          hedge('(super great/1)'), hedge('(is hypercore/1 (super great/1))')})

    def test_subedges4(self):
        self.assertEqual(hedge('(is hypercore/1 (X/C))').subedges(),
                         {hedge('is'), hedge('hypercore/1'), hedge('(X/C)'), hedge('(is hypercore/1 (X/C))')})

    def test_insert_first_argument1(self):
        self.assertEqual(hedge('a').insert_first_argument(hedge('b')).to_str(), '(a b)')

    def test_insert_first_argument2(self):
        result = hedge('(a b)').insert_first_argument(hedge('(c d)'))
        self.assertEqual(result.to_str(), '(a (c d) b)')

    def test_connect1(self):
        self.assertEqual(hedge('(a b)').connect(hedge('(c d)')).to_str(), '(a b c d)')

    def test_connect2(self):
        self.assertEqual(hedge('(a b)').connect(hedge('()')).to_str(), '(a b)')

    def test_sequence(self):
        ab = hedge('(a b)')
        c = hedge('c')
        cd = hedge('(c d)')
        self.assertEqual(ab.sequence(c, before=True).to_str(), '(c a b)')
        self.assertEqual(ab.sequence(c, before=False).to_str(), '(a b c)')
        self.assertEqual(ab.sequence(cd, before=True).to_str(), '(c d a b)')
        self.assertEqual(ab.sequence(cd, before=False).to_str(), '(a b c d)')
        self.assertEqual(ab.sequence(cd, before=True, flat=False).to_str(), '((c d) (a b))')
        self.assertEqual(ab.sequence(cd, before=False, flat=False).to_str(), '((a b) (c d))')

    def test_replace_atom(self):
        x = hedge('x')
        xc = hedge('x/C')
        self.assertEqual(hedge('x').replace_atom(x, xc).to_str(), 'x/C')
        self.assertEqual(hedge('(a b x)').replace_atom(x, xc).to_str(), '(a b x/C)')
        self.assertEqual(hedge('(a b c)').replace_atom(x, xc).to_str(), '(a b c)')
        self.assertEqual(hedge('(a x (b x))').replace_atom(x, xc).to_str(), '(a x/C (b x/C))')

    def test_replace_atom_unique(self):
        edge = hedge('(a/P x/C x/C)')
        x1 = edge[1]
        x2 = edge[2]
        y = hedge('y/C')
        self.assertEqual(edge.replace_atom(x1, y, unique=True).to_str(), '(a/P y/C x/C)')
        self.assertEqual(edge.replace_atom(x2, y, unique=True).to_str(), '(a/P x/C y/C)')
        self.assertEqual(edge.replace_atom(hedge('x/C'), y, unique=True).to_str(), '(a/P x/C x/C)')

    def test_atom_role(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').role(), ['Cp', 's'])

    def test_atom_role_implied_conjunction(self):
        self.assertEqual(hedge('and').role(), ['J'])

    def test_atom_simplify_atom1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').simplify(), hedge('hypercore/C/1'))

    def test_atom_simplify_atom2(self):
        self.assertEqual(hedge('hypercore').simplify(), hedge('hypercore'))

    def test_atom_simplify_atom3(self):
        self.assertEqual(hedge('say/Pd.sr.|f----/en').simplify(), hedge('say/P/en'))

    def test_atom_simplify_atom4(self):
        self.assertEqual(hedge('say/Pd.sr.|f----/en').simplify(subtypes=True), hedge('say/Pd/en'))

    def test_atom_simplify_atom5(self):
        self.assertEqual(hedge('say/Pd.sr.|f----/en').simplify(argroles=True), hedge('say/P.sr/en'))

    def test_atom_simplify_atom6(self):
        self.assertEqual(hedge('say/Pd.sr.|f----/en').simplify(namespaces=False), hedge('say/P'))

    def test_atom_simplify_atom7(self):
        self.assertEqual(hedge('say/Pd.sr.|f----/en').simplify(subtypes=True, namespaces=False), hedge('say/Pd'))

    def test_atom_simplify_edge(self):
        edge = hedge('is/Pd.sc.|f----/en mary/Cp.s/en nice/Ca/en')
        self.assertEqual(edge.simplify(), hedge('is/P/en mary/C/en nice/C/en'))
        self.assertEqual(edge.simplify(subtypes=True), hedge('is/Pd/en mary/Cp/en nice/Ca/en'))
        self.assertEqual(edge.simplify(argroles=True), hedge('is/P.sc/en mary/C/en nice/C/en'))
        self.assertEqual(edge.simplify(argroles=True, namespaces=False), hedge('is/P.sc mary/C nice/C'))

    def test_atom_type(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').type(), 'Cp')

    def test_atom_mtype(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').mtype(), 'C')

    def test_atom_type_implied_conjunction(self):
        self.assertEqual(hedge('and').type(), 'J')

    def test_non_atom_type1(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').type(), 'Rd')

    def test_non_atom_type2(self):
        self.assertEqual(hedge('(red/M shoes/Cc.p)').type(), 'Cc')

    def test_non_atom_type3(self):
        self.assertEqual(hedge('(before/Tt noon/C)').type(), 'St')

    def test_non_atom_type4(self):
        self.assertEqual(hedge('(very/M large/M)').type(), 'M')

    def test_non_atom_type5(self):
        self.assertEqual(hedge('((very/M large/M) shoes/Cc.p)').type(), 'Cc')

    def test_non_atom_type6(self):
        self.assertEqual(hedge('(will/M be/Pd.sc)').type(), 'Pd')

    def test_non_atom_type7(self):
        self.assertEqual(hedge('((will/M be/Pd.sc) john/Cp.s rich/C)').type(), 'Rd')

    def test_non_atom_type8(self):
        self.assertEqual(hedge('(play/T piano/Cc.s)').type(), 'S')

    def test_non_atom_type9(self):
        self.assertEqual(hedge('(and/J meat/Cc.s potatoes/Cc.p)').type(), 'C')

    def test_non_atom_type10(self):
        self.assertEqual(hedge('(and/J (is/Pd.so hypercore/Cp.s great/C))').type(), 'R')

    def test_non_atom_mtype1(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').type(), 'Rd')

    def test_non_atom_mtype2(self):
        self.assertEqual(hedge('(red/M shoes/Cc.p)').mtype(), 'C')

    def test_non_atom_mtype3(self):
        self.assertEqual(hedge('(before/Tt noon/C)').mtype(), 'S')

    def test_non_atom_mtype4(self):
        self.assertEqual(hedge('(very/M large/M)').mtype(), 'M')

    def test_non_atom_mtype5(self):
        self.assertEqual(hedge('((very/M large/M) shoes/Cc.p)').mtype(), 'C')

    def test_non_atom_mtype6(self):
        self.assertEqual(hedge('(will/M be/Pd.sc)').mtype(), 'P')

    def test_non_atom_mtype7(self):
        self.assertEqual(hedge('((will/M be/Pd.sc) john/Cp.s rich/C)').mtype(), 'R')

    def test_non_atom_mtype8(self):
        self.assertEqual(hedge('(play/T piano/Cc.s)').mtype(), 'S')

    def test_non_atom_mtype9(self):
        self.assertEqual(hedge('(and/J meat/Cc.s potatoes/Cc.p)').mtype(), 'C')

    def test_non_atom_mtype10(self):
        self.assertEqual(hedge('(and/J (is/Pd.so hypercore/Cp.s great/C))').mtype(), 'R')

    def test_connector_type1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').connector_type(), None)

    def test_connector_type2(self):
        self.assertEqual(hedge('hypercore').connector_type(), None)

    def test_connector_type3(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').connector_type(), 'Pd')

    def test_connector_type4(self):
        self.assertEqual(hedge('(red/M shoes/Cn.p)').connector_type(), 'M')

    def test_connector_type5(self):
        self.assertEqual(hedge('(before/Tt noon/C)').connector_type(), 'Tt')

    def test_connector_type6(self):
        self.assertEqual(hedge('(very/M large/M)').connector_type(), 'M')

    def test_connector_type7(self):
        self.assertEqual(hedge('((very/M large/M) shoes/Cn.p)').connector_type(), 'M')

    def test_connector_type8(self):
        self.assertEqual(hedge('(will/M be/Pd.sc)').connector_type(), 'M')

    def test_connector_type9(self):
        self.assertEqual(hedge('((will/M be/Pd.sc) john/Cp.s rich/C)').connector_type(), 'Pd')

    def test_connector_type10(self):
        self.assertEqual(hedge('(play/T piano/Cn.s)').connector_type(), 'T')

    def test_connector_mtype1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').connector_mtype(), None)

    def test_connector_mtype2(self):
        self.assertEqual(hedge('hypercore').connector_mtype(), None)

    def test_connector_mtype3(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').connector_mtype(), 'P')

    def test_connector_mtype4(self):
        self.assertEqual(hedge('(red/M shoes/Cn.p)').connector_mtype(), 'M')

    def test_connector_mtype5(self):
        self.assertEqual(hedge('(before/Tt noon/C)').connector_mtype(), 'T')

    def test_connector_mtype6(self):
        self.assertEqual(hedge('(very/M large/M)').connector_mtype(), 'M')

    def test_connector_mtype7(self):
        self.assertEqual(hedge('((very/M large/M) shoes/Cn.p)').connector_mtype(), 'M')

    def test_connector_mtype8(self):
        self.assertEqual(hedge('(will/M be/Pd.sc)').connector_mtype(), 'M')

    def test_connector_mtype9(self):
        self.assertEqual(hedge('((will/M be/Pd.sc) john/Cp.s rich/C)').connector_mtype(), 'P')

    def test_connector_mtype10(self):
        self.assertEqual(hedge('(play/T piano/Cn.s)').connector_mtype(), 'T')

    def test_t1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').t, 'Cp')

    def test_t2(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').t, 'Rd')

    def test_t3(self):
        self.assertEqual(hedge('(very/M large/M)').t, 'M')

    def test_mt1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').mt, 'C')

    def test_mt2(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').mt, 'R')

    def test_mt3(self):
        self.assertEqual(hedge('(very/M large/M)').mt, 'M')

    def test_ct1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').ct, None)

    def test_ct2(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').ct, 'Pd')

    def test_ct3(self):
        self.assertEqual(hedge('(red/M shoes/Cn.p)').ct, 'M')

    def test_cmt1(self):
        self.assertEqual(hedge('hypercore/Cp.s/1').cmt, None)

    def test_cmt2(self):
        self.assertEqual(hedge('(is/Pd.so hypercore/Cp.s great/C)').cmt, 'P')

    def test_cmt3(self):
        self.assertEqual(hedge('(red/M shoes/Cn.p)').cmt, 'M')

    def test_atom_with_type1(self):
        self.assertEqual(hedge('(+/B a/Cn b/Cp)').atom_with_type('C'), hedge('a/Cn'))

    def test_atom_with_type2(self):
        self.assertEqual(hedge('(+/B a/C b/Cp)').atom_with_type('Cp'), hedge('b/Cp'))

    def test_atom_with_type3(self):
        self.assertEqual(hedge('(+/B a/C b/Cp)').atom_with_type('P'), None)

    def test_atom_with_type4(self):
        self.assertEqual(hedge('a/Cn').atom_with_type('C'), hedge('a/Cn'))

    def test_atom_with_type5(self):
        self.assertEqual(hedge('a/Cn').atom_with_type('Cn'), hedge('a/Cn'))

    def test_atom_with_type6(self):
        self.assertEqual(hedge('a/Cn').atom_with_type('Cp'), None)

    def test_atom_with_type7(self):
        self.assertEqual(hedge('a/Cn').atom_with_type('P'), None)

    def test_contains_atom_type1(self):
        self.assertTrue(hedge('(+/B a/Cn b/Cp)').contains_atom_type('C'))

    def test_contains_atom_type2(self):
        self.assertTrue(hedge('(+/B a/C b/Cp)').contains_atom_type('Cp'))

    def test_contains_atom_type3(self):
        self.assertFalse(hedge('(+/B a/C b/Cp)').contains_atom_type('P'))

    def test_contains_atom_type4(self):
        self.assertTrue(hedge('a/Cn').contains_atom_type('C'))

    def test_contains_atom_type5(self):
        self.assertTrue(hedge('a/Cn').contains_atom_type('Cn'))

    def test_contains_atom_type6(self):
        self.assertFalse(hedge('a/Cn').contains_atom_type('Cp'))

    def test_contains_atom_type7(self):
        self.assertFalse(hedge('a/Cn').contains_atom_type('P'))

    def test_argroles_connector_atom1(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.argroles(), 'am')

    def test_argroles_connector_atom2(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.argroles(), 'sx')

    def test_argroles_connector_atom3(self):
        edge = hedge('come/Pd')
        self.assertEqual(edge.argroles(), '')

    def test_argroles_connector_atom4(self):
        edge = hedge('red/M')
        self.assertEqual(edge.argroles(), '')

    def test_argroles_connector_atom5(self):
        edge = hedge('berlin/Cp.s/de')
        self.assertEqual(edge.argroles(), '')

    def test_argroles_connector_edge1(self):
        edge = hedge('(is/Mv.|f--3s/en influenced/Pd.xpa.<pf---/en)')
        self.assertEqual(edge.argroles(), 'xpa')

    def test_argroles_connector_edge2(self):
        edge = hedge('(is/Mv.|f--3s/en influenced/Pd)')
        self.assertEqual(edge.argroles(), '')

    def test_argroles_edge1(self):
        edge = hedge('((not/M is/P.sc) bob/C sad/C)')
        self.assertEqual(edge.argroles(), 'sc')

    def test_argroles_edge2(self):
        edge = hedge('(of/B.ma city/C berlin/C)')
        self.assertEqual(edge.argroles(), 'ma')

    def test_argroles_edge3(self):
        edge = hedge('(of/B city/C berlin/C)')
        self.assertEqual(edge.argroles(), '')

    def test_replace_argroles_atom1(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.replace_argroles('ma').to_str(), 's/Bp.ma')

    def test_replace_argroles_atom2(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.replace_argroles('scx').to_str(), 'come/Pd.scx.-i----/en')

    def test_replace_argroles_atom3(self):
        edge = hedge('come/Pd/en')
        self.assertEqual(edge.replace_argroles('scx').to_str(), 'come/Pd.scx/en')

    def test_replace_argroles_atom4(self):
        edge = hedge('xxx')
        self.assertEqual(edge.replace_argroles('scx').to_str(), 'xxx')

    def test_insert_argrole_atom1(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.insert_argrole('m', 0).to_str(), 's/Bp.mam')

    def test_insert_argrole_atom2(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.insert_argrole('m', 1).to_str(), 's/Bp.amm')

    def test_insert_argrole_atom3(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.insert_argrole('m', 2).to_str(), 's/Bp.amm')

    def test_insert_argrole_atom4(self):
        edge = hedge('s/Bp.am')
        self.assertEqual(edge.insert_argrole('m', 3).to_str(), 's/Bp.amm')

    def test_insert_argrole_atom5(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.insert_argrole('x', 0).to_str(), 'come/Pd.xsx.-i----/en')

    def test_insert_argrole_atom6(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.insert_argrole('x', 1).to_str(), 'come/Pd.sxx.-i----/en')

    def test_insert_argrole_atom7(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.insert_argrole('x', 2).to_str(), 'come/Pd.sxx.-i----/en')

    def test_insert_argrole_atom8(self):
        edge = hedge('come/Pd.sx.-i----/en')
        self.assertEqual(edge.insert_argrole('x', 100).to_str(), 'come/Pd.sxx.-i----/en')

    def test_insert_argrole_atom9(self):
        edge = hedge('come/Pd/en')
        self.assertEqual(edge.insert_argrole('s', 0).to_str(), 'come/Pd.s/en')

    def test_insert_argrole_atom10(self):
        edge = hedge('come/Pd/en')
        self.assertEqual(edge.insert_argrole('s', 1).to_str(), 'come/Pd.s/en')

    def test_insert_argrole_atom11(self):
        edge = hedge('come/Pd/en')
        self.assertEqual(edge.insert_argrole('s', 100).to_str(), 'come/Pd.s/en')

    def test_insert_argrole_atom12(self):
        edge = hedge('xxx')
        self.assertEqual(edge.insert_argrole('s', 0).to_str(), 'xxx')

    def test_insert_argrole_atom13(self):
        edge = hedge('xxx')
        self.assertEqual(edge.insert_argrole('s', 1).to_str(), 'xxx')

    def test_insert_argrole_atom14(self):
        edge = hedge('xxx')
        self.assertEqual(edge.insert_argrole('s', 100).to_str(), 'xxx')

    def test_replace_argroles_edge1(self):
        edge = hedge('(s/Bp.am x/C y/C)')
        self.assertEqual(edge.replace_argroles('ma').to_str(), '(s/Bp.ma x/C y/C)')

    def test_replace_argroles_edge2(self):
        edge = hedge('((m/M s/Bp.am) x/C y/C)')
        self.assertEqual(edge.replace_argroles('ma').to_str(), '((m/M s/Bp.ma) x/C y/C)')

    def test_replace_argroles_edge3(self):
        edge = hedge('(come/Pd.sx.-i----/en you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '(come/Pd.scx.-i----/en you/C here/C)')

    def test_replace_argroles_edge4(self):
        edge = hedge('(come/Pd/en you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '(come/Pd.scx/en you/C here/C)')

    def test_replace_argroles_edge5(self):
        edge = hedge('((do/M come/Pd/en) you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '((do/M come/Pd.scx/en) you/C here/C)')

    def test_replace_argroles_edge6(self):
        edge = hedge('(come you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '(come you/C here/C)')

    def test_insert_argrole_edge1(self):
        edge = hedge('(s/Bp.am x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 0).to_str(), '(s/Bp.mam x/C y/C)')

    def test_insert_argrole_edge2(self):
        edge = hedge('(s/Bp.am x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 1).to_str(), '(s/Bp.amm x/C y/C)')

    def test_insert_argrole_edge3(self):
        edge = hedge('(s/Bp.am x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 2).to_str(), '(s/Bp.amm x/C y/C)')

    def test_insert_argrole_edge4(self):
        edge = hedge('(s/Bp.am x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 3).to_str(), '(s/Bp.amm x/C y/C)')

    def test_insert_argrole_edge5(self):
        edge = hedge('((m/M s/Bp.am) x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 0).to_str(), '((m/M s/Bp.mam) x/C y/C)')

    def test_insert_argrole_edge6(self):
        edge = hedge('(come/Pd.sx.-i----/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 0).to_str(), '(come/Pd.xsx.-i----/en you/C here/C)')

    def test_insert_argrole_edge7(self):
        edge = hedge('(come/Pd.sx.-i----/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 1).to_str(), '(come/Pd.sxx.-i----/en you/C here/C)')

    def test_insert_argrole_edge8(self):
        edge = hedge('(come/Pd.sx.-i----/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 2).to_str(), '(come/Pd.sxx.-i----/en you/C here/C)')

    def test_insert_argrole_edge9(self):
        edge = hedge('(come/Pd.sx.-i----/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 100).to_str(), '(come/Pd.sxx.-i----/en you/C here/C)')

    def test_insert_argrole_edge10(self):
        edge = hedge('(come/Pd/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 0).to_str(), '(come/Pd.s/en you/C here/C)')

    def test_insert_argrole_edge11(self):
        edge = hedge('(come/Pd/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 1).to_str(), '(come/Pd.s/en you/C here/C)')

    def test_insert_argrole_edge12(self):
        edge = hedge('(come/Pd/en you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 100).to_str(), '(come/Pd.s/en you/C here/C)')

    def test_insert_argrole_edge13(self):
        edge = hedge('(come you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 0).to_str(), '(come you/C here/C)')

    def test_insert_argrole_edge14(self):
        edge = hedge('(come you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 1).to_str(), '(come you/C here/C)')

    def test_insert_argrole_edge15(self):
        edge = hedge('(come you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 100).to_str(), '(come you/C here/C)')

    def test_insert_argrole_edge16(self):
        edge = hedge('((do/M come/Pd.sx.-i----/en) you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 2).to_str(), '((do/M come/Pd.sxx.-i----/en) you/C here/C)')

    def test_insert_edge_with_argrole1(self):
        edge = hedge('(is/Pd.sc/en sky/C blue/C)')
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 0),
                         hedge('(is/Pd.xsc/en today/C sky/C blue/C)'))
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 1),
                         hedge('(is/Pd.sxc/en sky/C today/C blue/C)'))
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 2),
                         hedge('(is/Pd.scx/en sky/C blue/C today/C)'))
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 100),
                         hedge('(is/Pd.scx/en sky/C blue/C today/C)'))

    def test_insert_edge_with_argrole2(self):
        edge = hedge('((not/M is/Pd.sc/en) sky/C blue/C)')
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 1),
                         hedge('((not/M is/Pd.sxc/en) sky/C today/C blue/C)'))

    def test_insert_edge_with_argrole3(self):
        edge = hedge('((m/M b/B.am) x/C y/C)')
        self.assertEqual(edge.insert_edge_with_argrole(hedge('z/C'), 'a', 2),
                         hedge('((m/M b/B.ama) x/C y/C z/C)'))

    def test_replace_argroles_var1(self):
        edge = hedge('((var s/Bp.am V) x/C y/C)')
        self.assertEqual(edge.replace_argroles('ma').to_str(), '((var s/Bp.ma V) x/C y/C)')

    def test_replace_argroles_var2(self):
        edge = hedge('((var (m/M s/Bp.am) V) x/C y/C)')
        self.assertEqual(edge.replace_argroles('ma').to_str(), '((var (m/M s/Bp.ma) V) x/C y/C)')

    def test_replace_argroles_var3(self):
        edge = hedge('((var come/Pd.sx.-i----/en V) you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '((var come/Pd.scx.-i----/en V) you/C here/C)')

    def test_replace_argroles_var4(self):
        edge = hedge('((var come/Pd/en V) you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '((var come/Pd.scx/en V) you/C here/C)')

    def test_replace_argroles_var5(self):
        edge = hedge('((var (do/M come/Pd/en) V) you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '((var (do/M come/Pd.scx/en) V) you/C here/C)')

    def test_replace_argroles_var6(self):
        edge = hedge('((var come V) you/C here/C)')
        self.assertEqual(edge.replace_argroles('scx').to_str(), '((var come V) you/C here/C)')

    def test_insert_argrole_var1(self):
        edge = hedge('((var s/Bp.am V) x/C y/C)')
        self.assertEqual(edge.insert_argrole('m', 0).to_str(), '((var s/Bp.mam V) x/C y/C)')

    def test_insert_argrole_var2(self):
        edge = hedge('((var come/Pd.sx.-i----/en V) you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 1).to_str(), '((var come/Pd.sxx.-i----/en V) you/C here/C)')

    def test_insert_argrole_var3(self):
        edge = hedge('((var come/Pd/en V) you/C here/C)')
        self.assertEqual(edge.insert_argrole('s', 100).to_str(), '((var come/Pd.s/en V) you/C here/C)')

    def test_insert_argrole_var4(self):
        edge = hedge('((var (do/M come/Pd.sx.-i----/en) V) you/C here/C)')
        self.assertEqual(edge.insert_argrole('x', 2).to_str(), '((var (do/M come/Pd.sxx.-i----/en) V) you/C here/C)')

    def test_insert_edge_with_var1(self):
        edge = hedge('((var is/Pd.sc/en V) sky/C blue/C)')
        self.assertEqual(edge.insert_edge_with_argrole(hedge('today/C'), 'x', 0),
                         hedge('((var is/Pd.xsc/en V) today/C sky/C blue/C)'))

    def test_insert_edge_with_var2(self):
        edge = hedge('((var (m/M b/B.am) V) x/C y/C)')
        self.assertEqual(edge.insert_edge_with_argrole(hedge('z/C'), 'a', 2),
                         hedge('((var (m/M b/B.ama) V) x/C y/C z/C)'))

    def test_edges_with_argrole(self):
        edge_str = ("((have/Mv.|f----/en (been/Mv.<pf---/en tracking/Pd.sox.|pg---/en)) (from/Br.ma/en "
                    "satellites/Cc.p/en (and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en))) "
                    "(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en) (since/Tt/en 1979/C#/en))")
        edge = hedge(edge_str)

        subj = hedge("(from/Br.ma/en satellites/Cc.p/en (and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en)))")
        obj = hedge("(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en)")
        spec = hedge("(since/Tt/en 1979/C#/en)")

        self.assertEqual(edge.edges_with_argrole('s'), [subj])
        self.assertEqual(edge.edges_with_argrole('o'), [obj])
        self.assertEqual(edge.edges_with_argrole('x'), [spec])
        self.assertEqual(edge.edges_with_argrole('p'), [])

    def test_edges_with_argrole_no_roles(self):
        edge_str = ("((have/Mv.|f----/en (been/Mv.<pf---/en tracking/Pd)) (from/Br.ma/en satellites/Cc.p/en "
                    "(and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en))) "
                    "(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en) (since/Tt/en 1979/C#/en))")
        edge = hedge(edge_str)

        self.assertEqual(edge.edges_with_argrole('s'), [])
        self.assertEqual(edge.edges_with_argrole('o'), [])
        self.assertEqual(edge.edges_with_argrole('x'), [])
        self.assertEqual(edge.edges_with_argrole('p'), [])

    def test_edges_with_argrole_atom(self):
        edge = hedge('tracking/Pd.sox.|pg---/en')

        self.assertEqual(edge.edges_with_argrole('s'), [])
        self.assertEqual(edge.edges_with_argrole('o'), [])
        self.assertEqual(edge.edges_with_argrole('x'), [])
        self.assertEqual(edge.edges_with_argrole('p'), [])

    def test_main_concepts1(self):
        concept = hedge("('s/Bp.am zimbabwe/Mp economy/Cn.s)")
        self.assertEqual(concept.main_concepts(), [hedge('economy/Cn.s')])

    def test_main_concepts2(self):
        concept = hedge("('s/Bp zimbabwe/Mp economy/Cn.s)")
        self.assertEqual(concept.main_concepts(), [])

    def test_main_concepts3(self):
        concept = hedge('(+/B.am?/. hiv/Ca kit/Cn.s (testing/M self/Cn.s))')
        self.assertEqual(concept.main_concepts(), [hedge('kit/Cn.s')])

    def test_main_concepts4(self):
        concept = hedge('(+/B.?a?/. hiv/Ca kit/Cn.s (testing/M self/Cn.s))')
        self.assertEqual(concept.main_concepts(), [])

    def test_main_concepts5(self):
        concept = hedge('(a/M thing/C)')
        self.assertEqual(concept.main_concepts(), [])

    def test_main_concepts6(self):
        concept = hedge('thing/C')
        self.assertEqual(concept.main_concepts(), [])

    def test_check_correctness_ok1(self):
        edge = hedge('(red/M shoes/C)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok2(self):
        edge = hedge('(+/B.am john/C smith/C)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok3(self):
        edge = hedge('(in/T 1976/C)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok4(self):
        edge = hedge('(happened/P.sxx it/C before/C (in/T 1976/C))')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok5(self):
        edge = hedge('(and/J red/C green/C blue/C)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok6(self):
        edge = hedge('(likes/P.sc x/C y/C)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_ok7(self):
        edge = hedge('(not/M likes/P.sc)')
        output = edge.check_correctness()
        self.assertEqual(output, {})

    def test_check_correctness_wrong1(self):
        edge = hedge('x/G')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong2(self):
        edge = hedge('(of/C capital/C mars/C)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong3(self):
        edge = hedge('(+/B john/C smith/C iii/C)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong4(self):
        edge = hedge('(of/B capital/C red/M)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong5(self):
        edge = hedge('(in/T 1976/C 1977/C)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong6(self):
        edge = hedge('(in/T red/M)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong7(self):
        edge = hedge('(is/P red/M)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong8(self):
        edge = hedge('(and/J one/C)')
        output = edge.check_correctness()
        self.assertTrue(edge in output)

    def test_check_correctness_wrong_deep1(self):
        edge = hedge('(:/J x/C x/G)')
        output = edge.check_correctness()
        self.assertTrue(hedge('x/G') in output)

    def test_check_correctness_wrong_deep2(self):
        edge = hedge('(:/J x/C (of/C capital/C mars/C))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(of/C capital/C mars/C)') in output)

    def test_check_correctness_wrong_deep3(self):
        edge = hedge('(:/J x/C (+/B john/C smith/C iii/C))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(+/B john/C smith/C iii/C)') in output)

    def test_check_correctness_wrong_deep4(self):
        edge = hedge('(:/J x/C (of/B capital/C red/M))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(of/B capital/C red/M)') in output)

    def test_check_correctness_wrong_deep5(self):
        edge = hedge('(:/J x/C (in/T 1976/C 1977/C))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(in/T 1976/C 1977/C)') in output)

    def test_check_correctness_wrong_deep6(self):
        edge = hedge('(:/J x/C (in/T red/M))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(in/T red/M)') in output)

    def test_check_correctness_wrong_deep7(self):
        edge = hedge('(:/J x/C (is/P red/M))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(is/P red/M)') in output)

    def test_check_correctness_wrong_deep8(self):
        edge = hedge('(:/J x/C (and/J one/C))')
        output = edge.check_correctness()
        self.assertTrue(hedge('(and/J one/C)') in output)

    def test_check_correctness_wrong_argroles1(self):
        edge = hedge('(likes/P.ss x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/P.ss x/C y/C)') in output)

    def test_check_correctness_wrong_argroles2(self):
        edge = hedge('(likes/P.cc x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/P.cc x/C y/C)') in output)

    def test_check_correctness_wrong_argroles3(self):
        edge = hedge('(likes/P.scx x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/P.scx x/C y/C)') in output)

    def test_check_correctness_wrong_argroles4(self):
        edge = hedge('(likes/P.sz x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/P.sz x/C y/C)') in output)

    def test_check_correctness_wrong_argroles5(self):
        edge = hedge('(likes/B.sc x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/B.sc x/C y/C)') in output)

    def test_check_correctness_wrong_argroles6(self):
        edge = hedge('(likes/P x/C y/C)')
        output = edge.check_correctness()
        self.assertTrue(hedge('(likes/P x/C y/C)') in output)
    
    def test_normalized_1(self):
        edge = hedge('(plays/Pd.os chess/C mary/C)')
        self.assertEqual(edge.normalized(), hedge('(plays/Pd.so mary/C chess/C)'))

    def test_normalized_2(self):
        edge = hedge('(plays/Pd chess/C mary/C)')
        self.assertEqual(edge.normalized(), hedge('(plays/Pd chess/C mary/C)'))

    def test_normalized_3(self):
        edge = hedge('(plays/Pd.os (of/B.am chess/C games/C) mary/C)')
        self.assertEqual(edge.normalized(), hedge('(plays/Pd.so mary/C (of/B.ma games/C chess/C))'))

    def test_normalized_4(self):
        edge = hedge('(plays/Pd.os.xxx/en chess/C mary/C)')
        self.assertEqual(edge.normalized(), hedge('(plays/Pd.so.xxx/en mary/C chess/C)'))

    def test_normalized_5(self):
        edge = hedge('plays/Pd.os.xxx/en')
        self.assertEqual(edge.normalized(), hedge('plays/Pd.so.xxx/en'))

    def test_normalized_6(self):
        edge = hedge('of/Br.am/en')
        self.assertEqual(edge.normalized(), hedge('of/Br.ma/en'))

    def test_normalized_7(self):
        edge = hedge('plays/Pd.{os}.xxx/en')
        self.assertEqual(edge.normalized(), hedge('plays/Pd.{so}.xxx/en'))

    def test_bug_fix1(self):
        edge_str = '((ahead/M/en (would/Mm/en go/P..-i-----/en)))'
        edge = hedge(edge_str)
        self.assertEqual(edge_str, str(edge))

    def test_remove_argroles_atom1(self):
        edge = hedge('come/Pd.sx')
        self.assertEqual(edge.remove_argroles().to_str(), 'come/Pd')

    def test_remove_argroles_atom2(self):
        edge = hedge('come/Pd')
        self.assertEqual(edge.remove_argroles().to_str(), 'come/Pd')

    def test_replace_argroles_atom_none(self):
        edge = hedge('come/Pd.sx')
        self.assertEqual(edge.replace_argroles(None).to_str(), 'come/Pd')

    def test_replace_argroles_atom_empty(self):
        edge = hedge('come/Pd.sx')
        self.assertEqual(edge.replace_argroles('').to_str(), 'come/Pd')

    def test_replace_argroles_edge_none(self):
        edge = hedge('(come/Pd.sx you/C here/C)')
        self.assertEqual(edge.replace_argroles(None).to_str(), '(come/Pd you/C here/C)')

    def test_replace_argroles_edge_empty(self):
        edge = hedge('(come/Pd.sx you/C here/C)')
        self.assertEqual(edge.replace_argroles('').to_str(), '(come/Pd you/C here/C)')

    def test_replace_argroles_deep_none(self):
        edge = hedge('((not/M is/P.sc) bob/C sad/C)')
        self.assertEqual(edge.replace_argroles(None).to_str(), '((not/M is/P) bob/C sad/C)')

if __name__ == '__main__':
    unittest.main()
