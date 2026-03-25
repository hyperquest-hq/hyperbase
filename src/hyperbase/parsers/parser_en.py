from importlib.resources import files

import spacy

from hyperbase import hedge
from hyperbase.parsers.alpha import Alpha
from hyperbase.parsers.alpha_beta import AlphaBeta
from hyperbase.utils.english import to_american


LANG = 'en'


_female = {"she/Ci/en", "her/Ci/en", "herself/Ci/en", "hers/Ci/en", "her/Mp/en"}
_male = {"he/Ci/en", "him/Ci/en", "himself/Ci/en", "his/Mp/en"}
_neutral = {"it/Ci/en", "itself/Ci/en", "its/Mp/en"}

_singular = {"it/Ci/en", "i/Ci/en", "she/Ci/en", "he/Ci/en", "her/Ci/en", "herself/Ci/en", "me/Ci/en", "him/Ci/en",
             "itself/Ci/en", "yourself/Ci/en", "myself/Ci/en", "himself/Ci/en", "one/Ci/en", "hers/Ci/en", "mine/Ci/en",
             "somebody/Ci/en", "oneself/Ci/en", "yours/Ci/en", "her/Mp/en", "his/Mp/en", "my/Mp/en", "its/Mp/en"}
_plural = {"they/Ci/en", "them/Ci/en", "we/Ci/en", "us/Ci/en", "'em/Ci/en", "themselves/Ci/en", "theirs/Ci/en",
           "ourselves/Ci/en", "their/Mp/en", "our/Mp/en"}

_animate = {"i/Ci/en", "she/Ci/en", "you/Ci/en", "he/Ci/en", "her/Ci/en", "herself/Ci/en", "me/Ci/en", "him/Ci/en",
            "we/Ci/en", "us/Ci/en", "yourself/Ci/en", "myself/Ci/en", "himself/Ci/en", "one/Ci/en", "themselves/Ci/en",
            "hers/Ci/en", "mine/Ci/en", "somebody/Ci/en", "oneself/Ci/en", "yours/Ci/en", "ourselves/Ci/en",
            "her/Mp/en", "his/Mp/en", "your/Mp/en", "my/Mp/en", "our/Mp/en", "thy/Mp/en"}
_inanimate = {"it/Ci/en", "itself/Ci/en", "its/Mp/en"}

_p1 = {"i/Ci/en", "me/Ci/en", "we/Ci/en", "us/Ci/en", "myself/Ci/en", "mine/Ci/en", "oneself/Ci/en", "ourselves/Ci/en",
       "my/Mp/en", "our/Mp/en"}
_p2 = {"you/Ci/en", "yourself/Ci/en", "yours/Ci/en", "your/Mp/en", "thy/Mp/en"}
_p3 = {"it/Ci/en", "she/Ci/en", "they/Ci/en", "he/Ci/en", "them/Ci/en", "her/Ci/en", "herself/Ci/en", "him/Ci/en",
       "itself/Ci/en", "himself/Ci/en", "one/Ci/en", "'em/Ci/en", "themselves/Ci/en", "hers/Ci/en", "somebody/Ci/en",
       "theirs/Ci/en", "her/Mp/en", "his/Mp/en", "its/Mp/en", "their/Mp/en", "whose/Mp/en"}


def tail_atom(edge):
    if edge.atom:
        return edge
    else:
        return tail_atom(edge[-1])


def first_predicate(edge):
    if edge.mt == 'R':
        if edge[0].mt == 'P':
            return edge[0]
        else:
            return first_predicate(edge[1])
    return None


class ParserEN(AlphaBeta):
    def __init__(self, lemmas=False, corefs=False, beta='repair', normalize=True, post_process=True):
        if spacy.util.is_package('en_core_web_trf'):
            nlp = spacy.load('en_core_web_trf')
            print('Using language model: {}'.format('en_core_web_trf'))
        else:
            if corefs:
                raise RuntimeError(
                    'Coreference resolution requires en_core_web_trf English language model to be installed.')
            elif spacy.util.is_package('en_core_web_lg'):
                nlp = spacy.load('en_core_web_lg')
                print('Using language model: {}'.format('en_core_web_lg'))
            else:
                raise RuntimeError('Either en_core_web_trf or en_core_web_lg English language model must be installed.')
        if corefs:
            nlp_coref = spacy.load('en_coreference_web_trf')
            nlp.add_pipe('transformer', name='coref_transformer', source=nlp_coref)
            nlp.add_pipe('coref', source=nlp_coref)
            nlp.add_pipe('span_resolver', source=nlp_coref)
            nlp.add_pipe('span_cleaner', source=nlp_coref)
             
        super().__init__(nlp, lemmas=lemmas, corefs=corefs, beta=beta, normalize=normalize, post_process=post_process)
        self.lang = LANG
        cases_str = files('hyperbase').joinpath('data/atoms-en.csv').read_text(encoding='utf-8')
        self.alpha = Alpha(cases_str)

    # ===========================================
    # Implementation of language-specific methods
    # ===========================================

    def atom_gender(self, atom):
        atom_str = atom.to_str()
        if atom_str in _female:
            return 'female'
        elif atom_str in _male:
            return 'male'
        elif atom_str in _neutral:
            return 'neutral'
        else:
            return None

    def atom_number(self, atom):
        atom_str = atom.to_str()
        if atom_str in _singular:
            return 'singular'
        elif atom_str in _plural:
            return 'plural'
        else:
            return None

    def atom_person(self, atom):
        atom_str = atom.to_str()
        if atom_str in _p1:
            return 1
        elif atom_str in _p2:
            return 2
        elif atom_str in _p3:
            return 3
        else:
            return None

    def atom_animacy(self, atom):
        atom_str = atom.to_str()
        if atom_str in _animate:
            return 'animate'
        elif atom_str in _inanimate:
            return 'inanimate'
        else:
            return None

    def _concept_type_and_subtype(self, token):
        tag = token.tag_
        dep = token.dep_
        if dep == 'nmod':
            return 'Cm'
        if tag[:2] == 'JJ':
            return 'Ca'
        elif tag[:2] == 'NN':
            subtype = 'p' if 'P' in tag else 'c'
            sing_plur = 'p' if tag[-1] == 'S' else 's'
            return 'C{}.{}'.format(subtype, sing_plur)
        elif tag == 'CD':
            return 'C#'
        elif tag == 'DT':
            return 'Cd'
        elif tag == 'WP':
            return 'Cw'
        elif tag == 'PRP':
            return 'Ci'
        else:
            return 'C'

    def _modifier_type_and_subtype(self, token):
        tag = token.tag_
        dep = token.dep_
        if dep == 'neg':
            return 'Mn'
        elif dep == 'poss':
            return 'Mp'
        elif dep == 'prep':
            return 'Mt'  # preposition
        elif dep == 'preconj':
            return 'Mj'  # conjunctional
        elif tag in {'JJ', 'NNP'}:
            return 'Ma'
        elif tag == 'JJR':
            return 'Mc'
        elif tag == 'JJS':
            return 'Ms'
        elif tag == 'DT':
            return 'Md'
        elif tag == 'WDT':
            return 'Mw'
        elif tag == 'CD':
            return 'M#'
        elif tag == 'MD':
            return 'Mm'  # modal
        elif tag == 'TO':
            return 'Mi'  # infinitive
        elif tag == 'RB':  # adverb
            return 'M'  # quintissential modifier, no subtype needed
        elif tag == 'RBR':
            return 'M='  # comparative
        elif tag == 'RBS':
            return 'M^'  # superlative
        elif tag == 'RP' or token.dep_ == 'prt':
            return 'Ml'  # particle
        elif tag == 'EX':
            return 'Me'  # existential
        else:
            return 'M'

    def _builder_type_and_subtype(self, token):
        tag = token.tag_
        dep = token.dep_
        if tag == 'IN':
            return 'Br'  # relational (proposition)
        elif dep == 'case':
            # if token.head.dep_ == 'poss':
            return 'Bp'
        elif tag == 'DT':
            return 'Bd'
        else:
            return 'B'

    def _predicate_type_and_subtype(self, token):
        dep = token.dep_
        if dep in {'advcl', 'csubj', 'csubjpass', 'parataxis'}:
            return 'Pd'
        elif dep in {'relcl', 'ccomp', 'acl', 'pcomp', 'xcomp'}:
            return 'P'
        elif self._is_verb(token):
            return 'Pd'
        else:
            return 'P'

    def _predicate_post_type_and_subtype(self, edge, subparts, args_string):
        # detecte imperative
        if subparts[0] == 'Pd':
            if ((subparts[2][1] == 'i' or subparts[2][0:2] == '|f') and
                    subparts[2][5] in {'-', '2'} and
                    's' not in args_string and
                    'c' not in args_string):
                if hedge('to/Mi/en') not in edge[0].atoms():
                    return 'P!'
        # keep everything else the same
        return subparts[0]

    def _relation_arg_role(self, edge):
        dep = self._head_token(edge).dep_

        if dep == 'nsubj':
            return 's'
        # passive subject
        elif dep == 'nsubjpass':
            return 'p'
        # agent
        elif dep == 'agent':
            return 'a'
        # subject complement
        elif dep in {'acomp', 'attr'}:
            return 'c'
        # direct object
        elif dep in {'dobj', 'pobj', 'prt', 'oprd'}:
            return 'o'
        # indirect object
        elif dep in {'dative'}:
            return 'i'
        # specifier
        elif dep in {'advcl', 'prep', 'npadvmod'}:
            return 'x'
        # parataxis
        elif dep == 'parataxis':
            return 't'
        # interjection
        elif dep == 'intj':
            return 'j'
        # clausal complement
        elif dep in {'xcomp', 'ccomp'}:
            return 'r'
        else:
            return '?'

    def _concept_arg_role(self, edge, concept):
        min_depth = min(
            [self.depths[self.token2atom[self._head_token(subedge)]] for subedge in edge[1:]])
        concept_head = self._head_token(concept)
        depth = self.depths[self.token2atom[concept_head]]
        if depth > min_depth and (concept_head.dep_ == 'compound') or 'mod' in concept_head.dep_:
            return 'a'
        else:
            return 'm'

    def _builder_arg_roles(self, edge):
        builder = edge[0].atom_with_type('B')
        parts = builder.parts()
        if parts[0] == '+' and parts[2] == '.':
            args = [self._concept_arg_role(edge, param)
                    for param in edge[1:]]
            return ''.join(args)
        elif len(edge) == 3:
            ct = builder.type()
            if ct == 'Br':
                return 'ma'
            elif ct == 'Bp':
                return 'am'
        return ''

    def _is_noun(self, token):
        return token.tag_[:2] == 'NN'

    def _is_verb(self, token):
        tag = token.tag_
        if len(tag) > 0:
            return token.tag_[0] == 'V'
        else:
            return False

    def _verb_features(self, token):
        tense = '-'
        verb_form = '-'
        aspect = '-'
        mood = '-'
        person = '-'
        number = '-'
        verb_type = '-'

        if token.tag_ == 'VB':
            verb_form = 'i'  # infinitive
        elif token.tag_ == 'VBD':
            verb_form = 'f'  # finite
            tense = '<'  # past
        elif token.tag_ == 'VBG':
            verb_form = 'p'  # participle
            tense = '|'  # present
            aspect = 'g'  # progressive
        elif token.tag_ == 'VBN':
            verb_form = 'p'  # participle
            tense = '<'  # past
            aspect = 'f'  # perfect
        elif token.tag_ == 'VBP':
            verb_form = 'f'  # finite
            tense = '|'  # present
        elif token.tag_ == 'VBZ':
            verb_form = 'f'  # finite
            tense = '|'  # present
            number = 's'  # singular
            person = '3'  # third person

        features = (tense, verb_form, aspect, mood, person, number, verb_type)
        return ''.join(features)

    def _adjust_score(self, edges):
        min_depth = 9999999
        appos = False
        min_appos_depth = 9999999

        if all([edge.mtype() == 'C' for edge in edges]):
            for edge in edges:
                token = self._head_token(edge)
                depth = self.depths[self.token2atom[token]]
                if depth < min_depth:
                    min_depth = depth
                if token and token.dep_ == 'appos':
                    appos = True
                    if depth < min_appos_depth:
                        min_appos_depth = depth

        if appos and min_appos_depth > min_depth:
            return -99
        else:
            return 0

    def _poss2text(self, edge, parse):
        part1 = self._edge2text(edge[1], parse).strip()
        part2 = self._edge2text(edge[2], parse)
        if part1[-1] == 's':
            poss = "'"
        else:
            poss = "'s"
        return f'{part1}{poss} {part2}'

    # ===============
    # Post-processing
    # ===============
    def _insert_arg_in_tail(self, edge, arg):
        if edge.atom:
            return edge

        if edge.cmt == 'P':
            ars = edge.argroles()
            ar = None
            if 'p' in ars:
                if 'a' not in ars:
                    ar = 'a'
            elif 'a' in ars:
                ar = 'p'
            elif 's' not in ars:
                ar = 's'
            elif 'o' not in ars:
                ar = 'o'
            if ar:
                return self._insert_edge_with_argrole(edge, arg, ar, len(edge))

        new_tail = self._insert_arg_in_tail(edge[-1], arg)
        if new_tail != edge[-1]:
            return hedge(list(edge[:-1]) + [new_tail])
        if edge.cmt != 'P':
            return edge
        ars = edge.argroles()
        if ars == '':
            return edge
        return self._insert_edge_with_argrole(edge, arg, 'x', len(edge))

    def _insert_spec_rightmost_relation(self, edge, arg):
        if edge.atom:
            return edge
        if 'P' in [atom.mt for atom in edge[-1].atoms()]:
            return hedge(list(edge[:-1]) + [self._insert_spec_rightmost_relation(edge[-1], arg)])
        if edge[0].mt == 'P':
            return self._insert_edge_with_argrole(edge, arg, 'x', len(edge))
        for pos, subedge in reversed(list(enumerate(edge))):
            if 'P' in [atom.mt for atom in subedge.atoms()]:
                new_edge = list(edge)
                new_edge[pos] = self._insert_spec_rightmost_relation(subedge, arg)
                return hedge(new_edge)
        return edge

    def _process_colon_conjunctions(self, edge):
        if edge.atom:
            return edge
        edge = hedge([self._process_colon_conjunctions(subedge) for subedge in edge])
        if str(edge[0]) == ':/J/.' and any(subedge.mt == 'R' for subedge in edge):
            if edge[1].mt == 'R':
                # RR
                if edge[2].mt == 'R':
                    if edge[2].connector_atom().root() in {'says', 'say', 'said'}:
                        # first inside second
                        return self._insert_edge_with_argrole(edge[2], edge[1], 'r', len(edge[1]))
                    tatom = tail_atom(edge[1])
                    pred = first_predicate(edge[2])
                    if tatom.t == 'Ca' and pred and hedge('to/Mi/en') in pred.atoms():
                        # Ca tail
                        return self._replace_atom(edge[1], tatom, hedge([':/Jr.ma', tatom, edge[2]]))
                    elif pred and hedge('to/Mi/en') in pred.atoms():
                        # second is specification of rightmost relation
                        return self._insert_spec_rightmost_relation(edge[1], edge[2])
                # RS
                elif edge[2].mt == 'S':
                    # second is specification
                    return self._insert_edge_with_argrole(edge[1], edge[2], 'x', len(edge[1]))
                # RC
                elif edge[2].mt == 'C':
                    return self._insert_arg_in_tail(edge[1], edge[2])
            # CR
            elif edge[1].mt == 'C':
                if edge[2].mt == 'R':
                    if not 's' in edge[2].argroles():
                        # concept is subject
                        return self._insert_edge_with_argrole(edge[2], edge[1], 's', 0)
            # SR
            elif edge[1].mt == 'S':
                if edge[2].mt == 'R':
                    # first is specification
                    return self._insert_edge_with_argrole(edge[2], edge[1], 'x', len(edge[2]))
        return edge

    def _fix_argroles(self, edge):
        if edge.atom:
            return edge
        edge = hedge([self._fix_argroles(subedge) for subedge in edge])
        ars = edge.argroles()
        if ars != '' and edge.mt == 'R':
            _ars = ''
            for ar, subedge in zip(ars, edge[1:]):
                _ar = ar
                if ar == '?':
                    if subedge.mt == 'R':
                        _ar = 'r'
                    elif subedge.mt == 'S':
                        _ar = 'x'
                elif ar == 'r':
                    pred = first_predicate(subedge)
                    if pred and hedge('to/Mi/en') in pred.atoms():
                        _ar = 'x'
                _ars += _ar
            return self._replace_argroles(edge, _ars)
        return edge

    def _post_process(self, edge):
        if edge is None:
            return None
        _edge = self._fix_argroles(edge)
        _edge = self._process_colon_conjunctions(_edge)
        return _edge
