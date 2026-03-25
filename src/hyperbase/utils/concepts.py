def strip_concept(edge):
    """Strip away nesting edges with connectors such as triggers and
    subpredicates, to expose the outmost and leftmost concept that can be
    found. May be the edge itself.

    For example:

    (against/T (the/M (of/B treaty/C paris/C)))

    becomes

    (the/M (of/B treaty/C paris/C))
    """
    if edge.mtype() == 'C':
        return edge
    elif edge.not_atom:
        return strip_concept(edge[1])
    else:
        return None


def has_proper_concept(edge):
    """Check if the concept either is a proper edge, or contains one."""
    if edge.atom:
        return edge.type()[:2] == 'Cp'
    else:
        for subedge in edge[1:]:
            if has_proper_concept(subedge):
                return True
        return False


def has_common_or_proper_concept(edge):
    """Check if the concept either is a common/proper edge, or contains one."""
    if edge.atom:
        return edge.type()[:2] == 'Cp' or edge.type()[:2] == 'Cc'
    else:
        for subedge in edge[1:]:
            if has_proper_concept(subedge):
                return True
        return False


def all_concepts(edge):
    """Recursively search for all concepts contained in the edge, returning
    a set that can also contain itself."""
    concepts = set()
    if edge.mtype() == 'C':
        concepts.add(edge)
    if edge.not_atom:
        for item in edge:
            concepts |= all_concepts(item)
    return concepts
