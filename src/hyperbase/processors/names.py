import itertools

import networkx as nx
import progressbar

from hyperbase.utils.corefs import make_corefs
from hyperbase.processor import Processor
from hyperbase.hyperedge import hedge, build_atom
from hyperbase.utils.concepts import has_proper_concept


def clean_edge(edge):
    if edge.not_atom:
        return hedge([clean_edge(subedge) for subedge in edge])
    root = edge.label()
    root = root.replace('_', '').replace('.', '')
    return build_atom(root, *edge.parts()[1:])


def belongs_to_clique(edge, clique):
    if edge.atom:
        return clean_edge(edge) in clique
    else:
        return all([clean_edge(x) in clique for x in edge[1:]])


def clique_size(clique, concepts):
    return len(list(x for x in clique if x in concepts))


def clique_number(edge, cliques, concepts):
    best_clique_number = -1
    best_clique_size = -1

    for i, clique in enumerate(cliques):
        if belongs_to_clique(edge, clique):
            if clique_size(clique, concepts) > best_clique_size:
                best_clique_size = clique_size(clique, concepts)
                best_clique_number = i
    return best_clique_number


def main_concepts(edge):
    if not edge.mtype() == 'C':
        return []
    if edge.atom:
        return [edge]
    conn = edge[0]
    if conn.mtype() == 'B':
        return edge.main_concepts()
    if conn.mtype() == 'M':
        return main_concepts(edge[1])
    return []


def edges_with_seed(hg, seed):
    edges = []
    for edge in set(hg.edges_with_edges([seed])):
        mc = main_concepts(edge)
        if len(mc) == 1 and mc[0] == seed and hg.degree(edge) >= 5:
            edges.append(edge)
            edges += edges_with_seed(hg, edge)
    return edges


def infer_concepts(edge):
    concepts = set()
    if edge.mtype() == 'C':
        concepts.add(edge)
    if edge.not_atom:
        mc = main_concepts(edge)
        if len(mc) == 1:
            concepts.add(mc[0])
        concept_sets = [infer_concepts(subedge) for subedge in edge[1:]]
        for product in itertools.product(*concept_sets):
            concepts.add(hedge((edge[0],) + product))
    return concepts


def extract_concepts(edge):
    concepts = set()
    if edge.mtype() == 'C':
        concepts |= infer_concepts(edge)
    if edge.not_atom:
        for item in edge:
            for concept in extract_concepts(item):
                concepts |= infer_concepts(concept)
    return concepts


class CorefsNames(Processor):
    def __init__(self, hg, sequence=None):
        super().__init__(hg=hg, sequence=sequence)
        self.corefs = 0
        self.seeds = set()

    def corefs_from_seed(self, seed):
        concepts = edges_with_seed(self.hg, seed)

        subconcepts = set()
        graph_edges = set()
        for concept in concepts:
            edge_concepts = set()
            for item in extract_concepts(concept):
                if item != seed:
                    edge_concepts.add(clean_edge(item))
            subconcepts |= edge_concepts
            pairs = set(itertools.combinations(edge_concepts, 2))
            graph_edges |= pairs

        subconcepts = tuple(subconcepts)

        graph_edges = tuple((subconcepts.index(e[0]), subconcepts.index(e[1]))
                            for e in graph_edges)

        g = nx.Graph()
        g.add_nodes_from(range(len(subconcepts)))
        g.add_edges_from(graph_edges)

        cliques = []
        for clique in nx.find_cliques(g):
            members = tuple(subconcepts[i] for i in clique)
            cliques.append(members + (clean_edge(seed),))

        coref_sets = tuple(set() for _ in cliques)
        for concept in concepts:
            cliquen = clique_number(concept, cliques, concepts)
            if cliquen >= 0:
                coref_sets[cliquen].add(concept)

        return coref_sets

    def process_edge(self, edge):
        if edge.not_atom:
            conn = edge[0]
            ct = edge.connector_type()
            if ct[0] == 'B' and edge.connector_atom().root() == '+':
                if len(edge) > 2:
                    concepts = edge.main_concepts()
                    if len(concepts) == 1 and has_proper_concept(concepts[0]):
                        self.seeds.add(concepts[0])

    def on_end(self):
        i = 0
        with progressbar.ProgressBar(max_value=len(self.seeds)) as bar:
            for seed in self.seeds:
                crefs = self.corefs_from_seed(seed)

                # check if the seed should be assigned to a synonym set
                if len(crefs) > 0:
                    # find set with the highest degree and normalize set
                    # degrees by total degree
                    cref_degs = [self.hg.sum_deep_degree(cref)
                                 for cref in crefs]
                    total_deg = sum(cref_degs)
                    if total_deg == 0:
                        continue
                    cref_ratios = [cref_deg / total_deg
                                   for cref_deg in cref_degs]
                    max_ratio = 0.
                    best_pos = -1
                    for pos, ratio in enumerate(cref_ratios):
                        if ratio > max_ratio:
                            max_ratio = ratio
                            best_pos = pos

                    dd = self.hg.deep_degree(seed)

                    # ensure that the seed is used by itself
                    if total_deg < dd:
                        # print('seed: {}'.format(seed))
                        # print('crefs: {}'.format(crefs))
                        # print('max_ratio: {}'.format(max_ratio))
                        # print('total coref dd: {}'.format(total_deg))
                        # print('seed dd: {}'.format(dd))

                        # add seed if coreference set is sufficiently dominant
                        if max_ratio >= .7:
                            crefs[best_pos].add(seed)
                            # print('seed added to cref: {}'.format(
                            #     crefs[best_pos]))

                    for cref in crefs:
                        for edge1, edge2 in itertools.combinations(cref, 2):
                            # print('are corefs: {} | {}'.format(
                            #     edge1.to_str(), edge2.to_str()))
                            self.corefs += 1
                            make_corefs(self.hg, edge1, edge2)

                i += 1
                bar.update(i)

    def report(self):
        return '{} coreferences were added.'.format(str(self.corefs))
