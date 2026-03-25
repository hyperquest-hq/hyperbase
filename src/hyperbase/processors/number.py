from collections import defaultdict

import progressbar

import hyperbase.constants as const
from hyperbase.utils.corefs import make_corefs
from hyperbase.processor import Processor
from hyperbase.utils.number import make_singular_plural
from hyperbase.utils.number import number
from hyperbase.utils.ontology import subtypes


class Number(Processor):
    def __init__(self, hg, sequence=None):
        super().__init__(hg=hg, sequence=sequence)
        self.sng_pl = 0
        self.corefs = 0

    def _make_singular_plural_relation(self, singular, plural):
        make_singular_plural(self.hg, singular, plural)
        self.sng_pl += 1

        make_corefs(self.hg, singular, plural)

        self.corefs += 1

        for subtype in subtypes(self.hg, singular):
            plural_edge = subtype.replace_main_concept(plural)
            if plural_edge and self.hg.exists(plural_edge):
                self._make_singular_plural_relation(subtype, plural_edge)

    def _check_apply_plural(self, pair):
        numbers = {'s': [], 'p': [], '?': []}
        for edge in pair:
            numbers[number(edge)].append(edge)
        if len(numbers['s']) == 1 and len(numbers['p']) == 1:
            singular = numbers['s'][0]
            plural = numbers['p'][0]
            self._make_singular_plural_relation(singular, plural)

    def on_end(self):
        lemmas = defaultdict(set)
        i = 0
        lemma_edge_count = self.hg.count((const.lemma_connector, '*', '*'))
        with progressbar.ProgressBar(max_value=lemma_edge_count) as bar:
            for edge in self.hg.search((const.lemma_connector, '*', '*'), strict=True):
                lemmas[edge[2]].add(edge[1])
            i += 1
            bar.update(i)

        i = 0
        with progressbar.ProgressBar(max_value=len(lemmas)) as bar:
            for lemma in lemmas:
                type_atoms = defaultdict(set)
                for atom in lemmas[lemma]:
                    type_atoms[atom.type()].add(atom)
                if len(type_atoms['Cc']) == 2:
                    self._check_apply_plural(type_atoms['Cc'])
                if len(type_atoms['Cp']) == 2:
                    self._check_apply_plural(type_atoms['Cp'])
                i += 1
                bar.update(i)

    def report(self):
        line1 = '{} singular/plural relations were added'.format(self.sng_pl)
        line2 = '{} coreferences were added'.format(self.corefs)
        return '{}; {}.'.format(line1, line2)
