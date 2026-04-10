from hyperbase.hyperedge import Hyperedge


def filter_alphanumeric_strings(strings: list[str]) -> list[str]:
    """
    Filter a list of strings to include only those containing alphanumeric characters,
    and remove all non-alphanumeric characters from each string.

    Args:
        strings: List of strings to filter

    Returns:
        Filtered list containing only lowercased alphanumeric characters
    """
    filtered: list[str] = []
    for s in strings:
        # Remove non-alphanumeric characters and lowercase
        cleaned = "".join(c.lower() for c in s if c.isalnum())
        # Only include if result is non-empty
        if cleaned:
            filtered.append(cleaned)
    return filtered


def edge_depth_exceeds(edge: Hyperedge, limit: int) -> bool:
    """Iteratively check whether an edge's nesting depth exceeds *limit*.

    Walks the edge with an explicit stack so it never triggers Python's
    recursion limit, even on pathologically deep edges that would crash a
    recursive ``Hyperedge.depth()`` call. Used by parsers to reject parses
    that are too deep to be safely transformed or serialised.
    """
    if edge.atom:
        return limit < 0
    stack: list[tuple[Hyperedge, int]] = [(edge, 1)]
    while stack:
        e, d = stack.pop()
        if d > limit:
            return True
        if e.atom:
            continue
        for sub in e:
            stack.append((sub, d + 1))
    return False
