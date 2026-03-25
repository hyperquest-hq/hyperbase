import hyperbase.constants as const


def lemma(hg, atom, same_if_none=False):
    """Returns the lemma of the given atom if it exists, None otherwise.

    Keyword argument:
    same_if_none -- if False, returns None when lemma does not exist. If True,
    returns atom items when lemma does not exist. (default: False)
    """
    if atom.atom:
        satom = atom.simplify()
        for lemma_edge in hg.search((const.lemma_connector, satom, '*'), strict=True):
            return lemma_edge[2]

    if same_if_none:
        return atom

    return None


def deep_lemma(hg, edge, same_if_none=False):
    """Returns the lemma of an atomic edge, or the lemma of the first atom
    found by recursively descending the hyperedge, always choosing the
    subedge immediatly after the connector.

    This is useful, for example, to find the lemma of the central verb
    in a non-atomic predicate edge. For example:

    (not/A (is/A going/P))

    could return

    go/P

    Keyword argument:
    same_if_none -- if False, returns None when lemma does not exist. If True,
    returns atom items when lemma does not exist. (default: False)
    """
    if edge.atom:
        return lemma(hg, edge, same_if_none)
    else:
        return deep_lemma(hg, edge[1])


def lemma_degrees(hg, edge):
    """Finds all the atoms that share the same given lemma
    and computes the sum of both their degrees and deep degrees.
    These two sums are returned.

    If the parameter edge is non-atomic, this function simply returns
    the degree and deep degree of that edge.
    """
    if edge.atom:
        roots = {edge.root()}

        # find lemma
        satom = edge.simplify()
        for edge in hg.search((const.lemma_connector, satom, '*'), strict=True):
            roots.add(edge[2].root())

        # compute degrees
        d = 0
        dd = 0
        for r in roots:
            atoms = set(hg.atoms_with_root(r))
            d += sum([hg.degree(atom) for atom in atoms])
            dd += sum([hg.deep_degree(atom) for atom in atoms])

        return d, dd
    else:
        return hg.degree(edge), hg.deep_degree(edge)
