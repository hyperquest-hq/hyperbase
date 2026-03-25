from collections import Counter

from hyperbase.utils.corefs import main_coref
from hyperbase.processor import Processor
from hyperbase.utils.concepts import has_proper_concept, strip_concept
from hyperbase.utils.lemmas import deep_lemma


def is_actor(hg, edge):
    """Checks if the edge is a coreference to an actor."""
    if edge.mtype() == 'C':
        return hg.exists(('actor/P/.', main_coref(hg, edge)))
    else:
        return False


def find_actors(hg, edge):
    """Returns set of all coreferences to actors found in the edge."""
    _actors = set()
    if is_actor(hg, edge):
        _actors.add(main_coref(hg, edge))
    if edge.not_atom:
        for item in edge:
            _actors |= find_actors(hg, item)
    return _actors


def actors(hg):
    """"Returns an iterator over all actors."""
    return [edge[1] for edge in hg.search('(actor/P/. *)', strict=True)]


ACTOR_PRED_LEMMAS = {'say', 'claim', 'warn', 'kill', 'accuse', 'condemn',
                     'slam', 'arrest', 'clash', 'blame', 'want', 'call',
                     'tell'}


class Actors(Processor):
    def __init__(self, hg, sequence=None):
        super().__init__(hg=hg, sequence=sequence)
        self.actor_counter = Counter()

    def process_edge(self, edge):
        if edge.not_atom:
            ct = edge.connector_type()
            if ct[0] == 'P':
                subjects = edge.edges_with_argrole('s')
                if len(subjects) == 1:
                    subject = strip_concept(subjects[0])
                    if subject and has_proper_concept(subject):
                        pred = edge[0]
                        dlemma = deep_lemma(self.hg, pred).root()
                        if dlemma in ACTOR_PRED_LEMMAS:
                            try:
                                actor = main_coref(self.hg, subject)
                                self.actor_counter[actor] += 1
                            except Exception as e:
                                print(str(e))

    def on_end(self):
        for actor in self.actor_counter:
            self.hg.add(('actor/P/.', actor))

    def report(self):
        return 'actors found: {}'.format(len(self.actor_counter))
