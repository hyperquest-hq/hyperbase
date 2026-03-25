from typing import Iterator, Union, Optional

import hyperbase.constants as const
from hyperbase.hyperedge import hedge, Hyperedge, str2atom


def _hedge_params(pattern, ref_edges=None):
    """Returns a tuple of the pattern and ref_edges parameters
    after they have been converted to hyperedges.
    """
    pattern = hedge(pattern)
    if ref_edges:
        ref_edges = [hedge(e) for e in ref_edges]
    return pattern, ref_edges


class Hypergraph(object):
    """Hypergraph interface."""

    def __init__(self):
        self.batch_mode = False

    # =======================================================
    # Interface methods, to be implemented in derived classes
    # =======================================================

    def close(self):
        """Closes the hypergraph."""
        raise NotImplementedError()

    def name(self):
        """Returns name of the hypergraph."""
        raise NotImplementedError()

    def destroy(self):
        """Erase the entire hypergraph."""
        raise NotImplementedError()

    def all(self):
        """Returns a generator of all the edges."""
        raise NotImplementedError()

    def all_attributes(self):
        """Returns a generator with a tuple for each edge.
           The first element of the tuple is the edge itself,
           the second is a dictionary of attribute values
           (as strings)."""
        raise NotImplementedError()

    def add_with_attributes(self, edge, attributes):
        """Adds an edge along with all its attributes, represented as a
        dictionary of attribute names to values."""
        raise NotImplementedError()

    def get_attributes(self, edge):
        """Return all attributes of an edge, represented as a
        dictionary of attribute names to values."""
        raise NotImplementedError()

    def begin_transaction(self):
        pass

    def end_transaction(self):
        pass

    # ============================
    # High-level interface methods
    # ============================

    def all_atoms(self):
        """Returns a generator of all the atoms."""
        for edge in self.all():
            if edge.atom:
                yield edge

    def all_non_atoms(self):
        """Returns a generator of all the edges that are not atoms."""
        for edge in self.all():
            if edge.not_atom:
                yield edge

    def exists(self, edge):
        """Checks if the given edge exists."""
        return self._exists(hedge(edge))

    def add(self, edge, primary=True, count=False):
        """Adds an edge if it does not exist yet, returns same edge.
        All children are recursively added as non-primary edge, for
        indexing purposes.

        Edges can be passed in both Hyperedge or string format.

        Keyword arguments:
        primary -- edge is primary, meaning, for example, that it counts
        towards degrees. Non-primary edges are used for indexing purposes,
        for example to make it easy to find the subedges contained in primary
        edges when performing queries.
        count -- an integer counter attribute is added to the edge. If the
        edge already exists, the counter is incremented.
        """
        if isinstance(edge, Hyperedge):
            if edge.atom:
                return edge
            else:
                # recursively add all sub-edges as non-primary edges.
                for child in edge:
                    self.add(child, primary=False)
                # add entity itself
                self._add(edge, primary=primary)

                # increment counter if requested
                if count:
                    self.inc_attribute(edge, 'count')

                return edge
        elif edge:
            return self.add(hedge(edge), primary=primary, count=count)
        return None

    def remove(self, edge, deep=False):
        """Removes an edge.

        Keyword argument:
        deep -- recursively remove all subedges (default False)
        """
        self._remove(hedge(edge), deep=deep)

    def is_primary(self, edge):
        """Check if an edge is primary."""
        return self._is_primary(hedge(edge))

    def set_primary(self, edge, value):
        """Make edge primary if value is True, make it non-primary
        otherwise.
        """
        self._set_primary(hedge(edge), value)

    def search(
            self,
            pattern: Union[Hyperedge, str, list, tuple],
            strict: bool = False,
            ref_edges: list[Union[Hyperedge, str, list, tuple]] = None
    ) -> Iterator[Hyperedge]:
        """Returns generator for all the edges that match a pattern.

        Patterns are themselves edges. They can match families of edges
        by employing special atoms:
        -> '*' represents a general wildcard (matches any edge)
        -> '.' represents an atomic wildcard (matches any atom)
        -> '(*)' represents a non-atomic wildcard (matches any non-atom)
        -> '...' at the end indicates an open-ended pattern.

        The pattern can be a string, that must represent an edge.
        Examples: '(is/Pd hyperbase/C .)'
        '(says/pd * ...)'

        Atomic patterns can also be used to match all edges in the
        hypergraph: *, all atoms: ., and all non-atoms: (*).

        Keyword argument:
        strict -- if True atoms are matched exactly and search is faster. If False, atoms in the pattern can match more
        specific versions, e.g.: apple/C in the pattern will match apple/Cc.s/en (default: False)
        """
        pattern, ref_edges = _hedge_params(pattern, ref_edges)

        if pattern.atom and len(pattern.parts()) == 1:
            if pattern.parens:
                return self.all_non_atoms()
            elif pattern[0][0] == '*':
                return self.all()
            elif pattern[0][0] == '.':
                return self.all_atoms()

        return self._search(pattern, strict, ref_edges=ref_edges)

    def match(
            self,
            pattern: Union[Hyperedge, str, list, tuple],
            strict: bool = False,
            skip_semsim: bool = False,
            curvars: Optional[dict[str, Hyperedge]] = None,
            ref_edges: list[Union[Hyperedge, str, list, tuple]] = None
    ) -> Iterator[tuple[Hyperedge, list[dict[str, Hyperedge]]]]:
        pattern, ref_edges = _hedge_params(pattern, ref_edges)
        return self._match(pattern, strict, skip_semsim=skip_semsim, curvars=curvars, ref_edges=ref_edges)

    def match_sequence(
            self,
            name: str,
            pattern: Union[Hyperedge, str, list, tuple],
            strict: bool = False,
            skip_semsim: bool = False,
            curvars: Optional[dict[str, Hyperedge]] = None,
            ref_edges: list[Union[Hyperedge, str, list, tuple]] = None
    ):
        pattern, ref_edges = _hedge_params(pattern, ref_edges)
        return self._match_edges(
            self.sequence(name), pattern, strict, skip_semsim=skip_semsim, curvars=curvars, ref_edges=ref_edges
        )

    def match_edges(
            self,
            edges: list[Union[Hyperedge, str, list, tuple]],
            pattern: Union[Hyperedge, str, list, tuple],
            strict: bool = False,
            skip_semsim: bool = False,
            curvars: Optional[dict[str, Hyperedge]] = None,
            ref_edges: list[Union[Hyperedge, str, list, tuple]] = None
    ):
        edges = [hedge(edge) for edge in edges]
        pattern, ref_edges = _hedge_params(pattern, ref_edges)
        return self._match_edges(edges, pattern, strict, skip_semsim=skip_semsim, curvars=curvars, ref_edges=ref_edges)

    def count(self, pattern: Union[Hyperedge, str, list, tuple]) -> int:
        """Number of edges that match a pattern.
        See search() method for an explanation of patterns.

        Keyword argument:
        strict -- if True atoms are matched exactly and search is faster. If False, atoms in the pattern can match more
        specific versions, e.g.: apple/C in the pattern will match apple/Cc.s/en (default: False)
        """
        return len(list(self.search(hedge(pattern))))

    def star(self, center, limit=None):
        """Returns generator of the edges that contain the center.

        Keyword argument:
        limit -- maximum number of results to return, infinite if None
        """
        return self._star(hedge(center), limit=limit)

    def atoms_with_root(self, root):
        """Returns generator of all atoms with the given root."""
        if len(root) == 0:
            return {}
        return self._atoms_with_root(root)

    def edges_with_edges(self, edges, root=None):
        """Returns generator of all edges containing the given edges,
        and optionally a given root.

        Keyword argument:
        root -- edge must also contain an atom with this root (default None)
        """
        return self._edges_with_edges(edges, root)

    def set_attribute(self, edge, attribute, value):
        """Sets the value of an attribute."""
        return self._set_attribute(hedge(edge), attribute, value)

    def inc_attribute(self, edge, attribute):
        """Increments an attribute of an entity, sets initial value to 1
        if attribute does not exist.
        """
        return self._inc_attribute(hedge(edge), attribute)

    def dec_attribute(self, edge, attribute):
        """Increments an attribute of an entity."""
        return self._dec_attribute(hedge(edge), attribute)

    def get_str_attribute(self, edge, attribute, or_else=None):
        """Returns attribute as string.

        Keyword argument:
        or_else -- value to return if the entity does not have the given
        attribute. (default None)
        """
        return self._get_str_attribute(hedge(edge), attribute, or_else=or_else)

    def get_int_attribute(self, edge, attribute, or_else=None):
        """Returns attribute as integer value.

        or_else -- value to return if the entity does not have
                   the give attribute. (default None)
        """
        return self._get_int_attribute(hedge(edge), attribute, or_else=or_else)

    def get_float_attribute(self, edge, attribute, or_else=None):
        """Returns attribute as float value.

        or_else -- value to return if the entity does not have
                   the give attribute. (default None)
        """
        return self._get_float_attribute(hedge(edge), attribute, or_else=or_else)

    def degree(self, edge):
        """Returns the degree of an entity."""
        return self._degree(hedge(edge))

    def deep_degree(self, edge):
        """Returns the deep degree of an entity."""
        return self._deep_degree(hedge(edge))

    def ego(self, center):
        """Returns all atoms directly connected to center
           by hyperedges.
        """
        edges = self.star(center)
        atom_set = set()
        for edge in edges:
            for atom in edge.atoms():
                atom_set.add(atom)
        return atom_set

    def remove_by_pattern(self, pattern, strict=False):
        """Removes all edges that match the pattern.

        Keyword argument:
        strict -- if True atoms are matched exactly and search is faster. If False, atoms in the pattern can match more
        specific versions, e.g.: apple/C in the pattern will match apple/Cc.s/en (default: False)
        """
        for edge in self.search(pattern, strict=strict):
            self.remove(edge)

    def root_degrees(self, edge):
        """Finds all the atoms that share the same root as the given edge
        and computes the sum of both their degrees and deep degrees.
        These two sums are returned.

        If the parameter edge is non-atomic, this function simply returns
        the degree and deep degree of that edge.
        """
        if edge.atom:
            atoms = tuple(self.atoms_with_root(edge.root()))
            d = sum([self.degree(atom) for atom in atoms])
            dd = sum([self.deep_degree(atom) for atom in atoms])
            return d, dd
        else:
            return self.degree(edge), self.deep_degree(edge)

    def sum_degree(self, edges):
        """Returns sum of the degrees of all edges contained in the parameter.
        """
        return sum([self.degree(edge) for edge in edges])

    def sum_deep_degree(self, edges):
        """Returns sum of the deep degrees of all edges contained in the
        parameter.
        """
        return sum([self.deep_degree(edge) for edge in edges])

    def add_to_sequence(self, name, edge, primary=True):
        """Adds 'edge' to sequence 'name'."""
        seq_atom = str2atom(name)
        seq_attrs_edge = hedge((const.sequence_attrs_connector, seq_atom))
        pos = self.get_int_attribute(seq_attrs_edge, 'size')
        if pos is None:
            pos = 0
        result = self.add((const.sequence_connector, seq_atom, str(pos), edge))
        self.set_attribute(seq_attrs_edge, 'size', pos + 1)
        if primary:
            self.set_primary(edge, True)
        return result

    def sequence(self, name):
        """Returns an iterator for a sequence of hyperedges, given the name
        of the sequence.
        """
        pos = 0
        stop = False
        while not stop:
            iteration = self.search((const.sequence_connector, name, str(pos), '*'), strict=True)
            next_edge = next(iteration, None)
            if next_edge:
                yield next_edge[3]
                pos += 1
            else:
                stop = True

    def sequences(self):
        """Returns an iterator for all the sequence names present in the
        hypergraph.
        """
        for edge in self.search((const.sequence_connector, '*', '0', '*'), strict=True):
            yield edge[1].to_str()

    def text(self, edge):
        """Returns the text representation of an edge."""
        txt = self.get_str_attribute(edge, 'text')
        if txt is None:
            return edge.label()
        else:
            return txt

    # ==============================================================
    # Private abstract methods, to be implemented in derived classes
    # ==============================================================

    def _exists(self, edge):
        raise NotImplementedError()

    def _add(self, edge, primary):
        raise NotImplementedError()

    def _remove(self, edge, deep):
        raise NotImplementedError()

    def _is_primary(self, edge):
        raise NotImplementedError()

    def _set_primary(self, edge, value):
        raise NotImplementedError()

    def _search(self, pattern, strict, ref_edges=None):
        raise NotImplementedError()

    def _match(self, pattern, strict, skip_semsim=False, curvars=None, ref_edges=None):
        raise NotImplementedError()

    def _match_edges(self, edges, pattern, strict, skip_semsim=False, curvars=None, ref_edges=None):
        raise NotImplementedError()

    def _star(self, center, limit=None):
        raise NotImplementedError()

    def _atoms_with_root(self, root):
        raise NotImplementedError()

    def _edges_with_edges(self, edges, root):
        raise NotImplementedError()

    def _set_attribute(self, edge, attribute, value):
        raise NotImplementedError()

    def _inc_attribute(self, edge, attribute):
        raise NotImplementedError()

    def _dec_attribute(self, edge, attribute):
        raise NotImplementedError()

    def _get_str_attribute(self, edge, attribute, or_else=None):
        raise NotImplementedError()

    def _get_int_attribute(self, edge, attribute, or_else=None):
        raise NotImplementedError()

    def _get_float_attribute(self, edge, attribute, or_else=None):
        raise NotImplementedError()

    def _degree(self, edge):
        raise NotImplementedError()

    def _deep_degree(self, edge):
        raise NotImplementedError()
