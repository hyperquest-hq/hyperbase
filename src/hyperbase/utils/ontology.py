import hyperbase.constants as const


def subtypes(hg, edge, deep=False):
    """Returns all subtypes of the given edge."""
    ont_edges = hg.search((const.type_of_connector, '*', edge), strict=True)
    subs = set([ont_edge[1] for ont_edge in ont_edges])
    if deep:
        new_subs = set()
        for sub in subs:
            new_subs |= subtypes(hg, sub, deep=True)
        subs |= new_subs
    return subs


def supertypes(hg, edge, deep=False):
    """Returns all supertypes of the given edge."""
    ont_edges = hg.search((const.type_of_connector, edge, '*'), strict=True)
    sups = set([ont_edge[2] for ont_edge in ont_edges])
    if deep:
        new_sups = set()
        for sup in sups:
            new_sups |= supertypes(hg, sup, deep=True)
        sups |= new_sups
    return sups
