from hyperbase import hedge
from hyperbase.patterns.utils import is_valid


def _extract_any_edges(edge):
    if edge.not_atom and str(edge[0]) == 'any':
        return list(edge[1:])
    else:
        return [edge]


def _merge_patterns(edge1, edge2):
    # edges with different sizes cannot be merged
    if len(edge1) != len(edge2):
        return None

    # atoms are not to be merged
    if edge1.atom or edge2.atom:
        return None

    # edges with no subedge in common are not to be merged
    if all(subedge1 != subedge2 for subedge1, subedge2 in zip(edge1, edge2)):
        return None

    merged_edge = []
    for subedge1, subedge2 in zip(edge1, edge2):
        if subedge1 == subedge2:
            merged_edge.append(subedge1)
        else:
            submerged = merge_patterns(subedge1, subedge2)
            if submerged:
                merged_edge.append(submerged)
            else:
                alternatives = _extract_any_edges(subedge1) + _extract_any_edges(subedge2)
                # heuristic: more complex edges first, likely to be more specific
                alternatives = sorted(alternatives, key=lambda x: x.size(), reverse=True)
                merged_edge.append(['any'] + alternatives)

    return hedge(merged_edge)


def merge_patterns(edge1, edge2):
    edge = _merge_patterns(edge1, edge2)
    if is_valid(edge):
        return edge
    else:
        return None
