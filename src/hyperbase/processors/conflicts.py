from hyperbase import hedge
from hyperbase.processor import Processor
from hyperbase.utils.corefs import main_coref
from hyperbase.utils.concepts import all_concepts
from hyperbase.utils.concepts import has_proper_concept
from hyperbase.utils.concepts import strip_concept
from hyperbase.utils.lemmas import deep_lemma


CONFLICT_PRED_LEMMAS = {'warn', 'kill', 'accuse', 'condemn', 'slam', 'arrest',
                        'clash', 'blame'}

CONFLICT_TOPIC_TRIGGERS = {'of/T/en', 'over/T/en', 'against/T/en', 'for/T/en'}


class Conflicts(Processor):
    def __init__(self, hg, sequence=None):
        super().__init__(hg=hg, sequence=sequence)
        self.conflicts = 0
        self.conflict_topics = 0

    def _process_topics(self, actor_orig, actor_targ, edge):
        for item in edge[1:]:
            if item.mtype() == 'S':
                if item[0].to_str() in CONFLICT_TOPIC_TRIGGERS:
                    for concept in all_concepts(item[1]):
                        if self.hg.degree(concept) > 1:
                            self.hg.add(('conflict-topic/P/.', actor_orig,
                                        actor_targ, concept, edge))
                            self.conflict_topics += 1

    def process_edge(self, edge):
        if edge.not_atom:
            ct = edge.connector_type()
            if ct[0] == 'P':
                pred = edge[0]
                if (len(edge) > 2 and
                        deep_lemma(
                            self.hg,
                            pred,
                            same_if_none=True).root() in CONFLICT_PRED_LEMMAS):
                    subjects = edge.edges_with_argrole('s')
                    objects = edge.edges_with_argrole('o')
                    if len(subjects) == 1 and len(objects) == 1:
                        subject = strip_concept(subjects[0])
                        obj = strip_concept(objects[0])
                        if (subject and obj and
                                has_proper_concept(subject) and
                                has_proper_concept(obj)):
                            actor_orig = main_coref(self.hg, subject)
                            actor_targ = main_coref(self.hg, obj)
                            conflict_edge = hedge(
                                ('conflict/P/.', actor_orig, actor_targ, edge))
                            self.hg.add(conflict_edge)
                            self._process_topics(actor_orig, actor_targ, edge)
                            self.conflicts += 1

    def report(self):
        return 'conflict edges: {}; conflict-topic pairs: {}'.format(
            self.conflicts, self.conflict_topics)
