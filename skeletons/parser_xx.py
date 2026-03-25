from hyperbase.parsers.alpha import Alpha
from hyperbase.parsers.alpha_beta import AlphaBeta


# Language code must be specified here
LANG = 'xx'
# Appropriate spaCy model must be specified here
SPACY_MODEL = 'xx_core_web_lg'


# =====================
# Parser class skeleton
# =====================
class ParserXX(AlphaBeta):
    def __init__(self, lemmas=False, resolve_corefs=False, beta='repair',
                 normalize=True, post_process=True):
        super().__init__(SPACY_MODEL, lemmas=lemmas,
                         resolve_corefs=resolve_corefs, beta=beta,
                         normalize=normalize, post_process=post_process)
        self.lang = LANG
        with open('atoms-xx.csv', 'rt') as f:
            cases_str = f.read()
        self.alpha = Alpha(cases_str)

    # ===========================================
    # Implementation of language-specific methods
    # ===========================================

    def atom_gender(self, atom):
        return None

    def atom_number(self, atom):
        return None

    def atom_person(self, atom):
        return None

    def atom_animacy(self, atom):
        return None

    def _concept_type_and_subtype(self, token):
        return 'C'

    def _modifier_type_and_subtype(self, token):
        return 'M'

    def _builder_type_and_subtype(self, token):
        return 'B'

    def _predicate_type_and_subtype(self, token):
        return 'P'

    def _predicate_post_type_and_subtype(self, edge, subparts, args_string):
        return subparts[0]

    def _relation_arg_role(self, edge):
        return '?'

    def _concept_arg_role(self, edge, concept):
        return 'm'

    def _builder_arg_roles(self, edge):
        return ''

    def _is_noun(self, token):
        return False

    def _is_verb(self, token):
        return False

    def _verb_features(self, token):
        return ''

    def _adjust_score(self, edges):
        return 0
