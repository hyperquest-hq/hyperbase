import unittest

from hyperbase.memory.permutations import *


class TestPermutations(unittest.TestCase):
    def test_fact1(self):
        self.assertEqual(fact(-10), 0)

    def test_fact2(self):
        self.assertEqual(fact(0), 0)

    def test_fact3(self):
        self.assertEqual(fact(1), 1)

    def test_fact4(self):
        self.assertEqual(fact(2), 2)

    def test_fact5(self):
        self.assertEqual(fact(3), 6)

    def test_fact6(self):
        self.assertEqual(fact(4), 24)

    def test_fact7(self):
        self.assertEqual(fact(5), 120)

    def test_nthperm(self):
        self.assertEqual(nthperm(10, 2), (0, 1, 2, 3, 4, 5, 6, 8, 7, 9))

    def test_permutations1(self):
        perm = permutate(('a', 'b'), 0)
        self.assertEqual(perm, ('a', 'b'))

    def test_permutations2(self):
        perm = permutate(('a', 'b'), 1)
        self.assertEqual(perm, ('b', 'a'))

    def test_permutations3(self):
        perm = permutate(('a', 'b', 'c'), 0)
        self.assertEqual(perm, ('a', 'b', 'c'))

    def test_permutations4(self):
        perm = permutate(('a', 'b', 'c'), 1)
        self.assertEqual(perm, ('a', 'c', 'b'))

    def test_permutations5(self):
        perm = permutate(('a', 'b', 'c'), 2)
        self.assertEqual(perm, ('b', 'a', 'c'))

    def test_permutations6(self):
        perm = permutate(('a', 'b', 'c'), 3)
        self.assertEqual(perm, ('b', 'c', 'a'))

    def test_permutations7(self):
        perm = permutate(('a', 'b', 'c'), 4)
        self.assertEqual(perm, ('c', 'a', 'b'))

    def test_permutations8(self):
        perm = permutate(('a', 'b', 'c'), 5)
        self.assertEqual(perm, ('c', 'b', 'a'))

    def test_permutations9(self):
        perm = permutate(('a', 'b', 'c', 'd'), 0)
        self.assertEqual(perm, ('a', 'b', 'c', 'd'))

    def test_permutations10(self):
        perm = permutate(('a', 'b', 'c', 'd'), 1)
        self.assertEqual(perm, ('a', 'b', 'd', 'c'))

    def test_permutations_complex1(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 0)
        self.assertEqual(perm, ('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'))

    def test_permutations_complex2(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 1)
        self.assertEqual(perm, ('is/Pd.sc', 'mary/Cp.s', ('my/M', 'name/Cn.s')))

    def test_permutations_complex3(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 2)
        self.assertEqual(perm, (('my/M', 'name/Cn.s'), 'is/Pd.sc', 'mary/Cp.s'))

    def test_permutations_complex4(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 3)
        self.assertEqual(perm, (('my/M', 'name/Cn.s'), 'mary/Cp.s', 'is/Pd.sc'))

    def test_permutations_complex5(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 4)
        self.assertEqual(perm, ('mary/Cp.s', 'is/Pd.sc', ('my/M', 'name/Cn.s')))

    def test_permutations_complex6(self):
        perm = permutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 5)
        self.assertEqual(perm, ('mary/Cp.s', ('my/M', 'name/Cn.s'), 'is/Pd.sc'))

    def test_unpermutate1(self):
        edge = unpermutate(('a', 'b'), 0)
        self.assertEqual(edge, ['a', 'b'])

    def test_unpermutate2(self):
        edge = unpermutate(('b', 'a'), 1)
        self.assertEqual(edge, ['a', 'b'])

    def test_unpermutate3(self):
        edge = unpermutate(('a', 'b', 'c'), 0)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate4(self):
        edge = unpermutate(('a', 'c', 'b'), 1)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate5(self):
        edge = unpermutate(('b', 'a', 'c'), 2)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate6(self):
        edge = unpermutate(('b', 'c', 'a'), 3)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate7(self):
        edge = unpermutate(('c', 'a', 'b'), 4)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate8(self):
        edge = unpermutate(('c', 'b', 'a'), 5)
        self.assertEqual(edge, ['a', 'b', 'c'])

    def test_unpermutate9(self):
        edge = unpermutate(('a', 'b', 'c', 'd'), 0)
        self.assertEqual(edge, ['a', 'b', 'c', 'd'])

    def test_unpermutate10(self):
        edge = unpermutate(('a', 'b', 'd', 'c'), 1)
        self.assertEqual(edge, ['a', 'b', 'c', 'd'])

    def test_unpermutate_complex1(self):
        edge = unpermutate(('is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'), 0)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_unpermutate_complex2(self):
        edge = unpermutate(('is/Pd.sc', 'mary/Cp.s', ('my/M', 'name/Cn.s')), 1)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_unpermutate_complex3(self):
        edge = unpermutate((('my/M', 'name/Cn.s'), 'is/Pd.sc', 'mary/Cp.s'), 2)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_unpermutate_complex4(self):
        edge = unpermutate((('my/M', 'name/Cn.s'), 'mary/Cp.s', 'is/Pd.sc'), 3)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_unpermutate_complex5(self):
        edge = unpermutate(('mary/Cp.s', 'is/Pd.sc', ('my/M', 'name/Cn.s')), 4)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_unpermutate_complex6(self):
        edge = unpermutate(('mary/Cp.s', ('my/M', 'name/Cn.s'), 'is/Pd.sc'), 5)
        self.assertEqual(edge, ['is/Pd.sc', ('my/M', 'name/Cn.s'), 'mary/Cp.s'])

    def test_first_permutation1(self):
        self.assertEqual(first_permutation(2, [0]), 0)

    def test_first_permutation2(self):
        self.assertEqual(first_permutation(3, [0]), 0)

    def test_first_permutation3(self):
        self.assertEqual(first_permutation(4, [0]), 0)

    def test_first_permutation4(self):
        self.assertEqual(first_permutation(4, [1]), 6)

    def test_first_permutation5(self):
        self.assertEqual(first_permutation(4, [0, 1]), 0)

    def test_first_permutation6(self):
        self.assertEqual(first_permutation(4, [0, 2]), 2)

    def test_first_permutation7(self):
        self.assertEqual(first_permutation(4, [1, 2]), 8)

    def test_first_permutation8(self):
        self.assertEqual(first_permutation(4, [1, 3]), 10)

    def test_first_permutation9(self):
        self.assertEqual(first_permutation(4, [0, 2, 4]), 4)

    def test_first_permutation10(self):
        self.assertEqual(first_permutation(4, [1, 2, 4]), 10)

    def test_do_with_edge_permutations(self):
        output = []

        def accumulate(perm_str):
            output.append(perm_str)

        do_with_edge_permutations(hedge('(a b c)'), accumulate)
        self.assertEqual(output, ['a b c 0', 'a c b 1', 'b a c 2', 'b c a 3', 'c a b 4', 'c b a 5'])

    def test_perm2edge1(self):
        edge = perm2edge(' a b c 0')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_perm2edge2(self):
        edge = perm2edge(' a c b 1')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_perm2edge3(self):
        edge = perm2edge(' b a c 2')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_perm2edge4(self):
        edge = perm2edge(' b c a 3')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_perm2edge5(self):
        edge = perm2edge(' c a b 4')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_perm2edge6(self):
        edge = perm2edge(' c b a 5')
        self.assertEqual(edge, hedge(('a', 'b', 'c')))

    def test_str_plus_1_1(self):
        self.assertEqual(str_plus_1('hyperbase'), 'hyperbasf')

    def test_str_plus_1_2(self):
        self.assertEqual(str_plus_1('zzz'), 'zz{')


if __name__ == '__main__':
    unittest.main()
