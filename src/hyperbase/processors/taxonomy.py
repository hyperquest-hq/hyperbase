import hyperbase.constants as const
from hyperbase.processor import Processor


class Taxonomy(Processor):
    def __init__(self, hg, sequence=None):
        super().__init__(hg=hg, sequence=sequence)
        self.relations = 0

    def process_edge(self, edge):
        if edge.not_atom:
            et = edge.type()
            if et[0] == 'C':
                ct = edge[0].connector_type()
                parent = None
                if ct[0] == 'B':
                    mcs = edge.main_concepts()
                    if len(mcs) == 1:
                        parent = mcs[0]
                elif ct[0] == 'M' and len(edge) == 2:
                    parent = edge[1]
                if parent:
                    ont_edge = (const.type_of_connector, edge, parent)
                    self.hg.add(ont_edge, primary=False)
                    self.relations += 1

    def report(self):
        return '{} relations were added.'.format(str(self.relations))
