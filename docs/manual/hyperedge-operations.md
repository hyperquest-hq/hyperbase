# Basic Hypergraph Operations

At the heart of hyperbase lies the Semantic Hypergraph (SH). In practical terms, we will talk simply about *hypergraphs*, and we will treat them as a type of database, which contains a searchable collection of hyperedges.

hyperbase provides abstractions to create, modify and search persistent hypergraph databases, as well as to define and manipulate hyperedges. In this section we introduce these basic operations, upon which all aspects of the library rely on.

## The two central functions of hyperbase: hgraph() and hedge()

The root namespace `hyperbase` contains the two most fundamental functions of the library:

- `hgraph(locator_string)`, which creates/opens a persistent hypergraph.
- `hedge(source)`, which creates a hyperedge from a string or a Python list or tuple.

In fact, the latter is implemented in `hyperbase.hyperedge`, but it is imported to the root namespace by default for convenience. We will see that, with just these two functions, a lot can be achieved.

## Creating and manipulating hyperedges

hyperbase defines the object class `Hyperedge`, which provides a variety of methods to work with hyperedges. The full interface of this class is described in the API reference. However, these objects are not meant to be instantiated directly. Instead, the `hedge` function can be used to create such an object directly from a string representation conforming to the SH notation. For example:

```python
from hyperbase import hedge
edge = hedge('(plays/P.so mary/C chess/C)')
```

In the above example, `edge` is an instance of the `Hyperedge` class. Hyperedges are Python sequences. In fact, the class `Hyperedge` is derived from `tuple`, so it makes it possible to do things such as:

```python
person = edge[1]
```

In this case, `person` will be assigned the second element of the initial hyperedge, which happens to be the atom `mary/C`. Range selectors also work, but they do not automatically produce hyperedges, because subranges of the elements of a semantic hyperedge are not guaranteed to be valid semantic hyperedges themselves. Instead, simple tuples are returned. For example, `edge[1:]` from the example is not a valid hyperedge. Nevertheless, such tuples of hyperedges are often useful:

```pycon
>>> edge[1:]
(mary/C, chess/C)
>>> type(edge[1:])
<class 'tuple'>
```

It is possible to test a hyperedge for atomicity like this:

```pycon
>>> edge.is_atom()
False
>>> person.is_atom()
True
```

Another frequently useful task is that of determining the type of a hyperedge:

```pycon
>>> edge.type()
'R'
>>> edge[0].type()
'P'
>>> person.type()
'C'
```

## Creating and populating hypergraphs

hyperbase hypergraphs are created and/or opened like this:

```python
from hyperbase import hgraph
hg = hgraph('example.db')
```

The argument `'example.db'` corresponds to a local file in the filesystem, where the hypergraph is persisted. A full path can also be provided, e.g.: `hgraph('users/alice/books.db')`. The object returned by this function is of type `Hypergraph`. Like `Hyperedge`, it provides a number of general-purpose methods to work with hypergraphs and is not meant to be directly instantiated.

hyperbase comes with a default implementation of hypergraph database based on SQLite 3. This is a nice general-purpose option, because it is available in all popular operating systems and Python comes with native support for it. Files with extensions `.db`, `.sqlite` or `.sqlite3` will be opened as SQLite-based hypergraph databases. For other options, see [the section on hypergraph database backends](backends.md). One possible disadvantage of SQLite is that it is not very space-efficient. This can become a problem with large hypergraphs, and a better option in this case might be the LevelDB-based hypergraph database. This backend is not included by default because it is currently hard to install outside of Linux. To support LevelDB, you will need to build hyperbase from source with a special option, [as explained in the installation instructions](../installation.md).

Adding hyperedges to a hypergraph is simple. For example, let us add the edge that was defined above:

```python
hg.add(edge)
```

We can then check if this edge exists in the hypergraph:

```pycon
>>> hg.exists(edge)
True
```

Notice that adding a hyperedge to a hypergraph implies the recursive addition of all of the elements of the hyperedge, so it is also the case that:

```pycon
>>> hg.exists(edge[1])
True
```

A distinction is made with the notion of *primary hyperedge*. A primary hyperedge is, by default, one that was added directly, while the recursively added ones are considered non-primary. It is possible to check this:

```pycon
>>> hg.is_primary(edge)
True
>>> hg.is_primary(edge[1])
False
```

It is possible to add an edge as non-primary:

```pycon
>>> moon = hedge('(of/B.ma moon/C jupiter/C)')
>>> hg.add(moon, primary=False)
(of/B.ma moon/C jupiter/C)
>>> hg.is_primary(moon)
False
```

As with `Hyperedge`, the full range of methods of `Hypergraph` is documented in the API reference.

## Adding many hyperedges as a batch (for speed)

With some hypergraph database backends, as is the case for the default one (SQLite 3), adding a large number of edges can be much faster if done in a batch. To help define such batch operations, hyperbase includes the `hopen()` context manager, to be used with Python's `with` statements. This works in a very similar way to the `with open...` expressions often used with files:

```python
with hopen('example.db') as hg:
    for edge in large_edge_list:
        hg.add(edge)
```

Since it never hurts performance, it is advisable to always use `with hopen...` when adding large number of hyperedges to a hypergraph database.

## The neighborhood of a hyperedge (star)

Hypergraphs are fundamentally about relationships. In an analogous fashion to graphs/networks, the neighborhood of an entity (other entities that it is directly connected to) is a simple but powerful concept. With hyperbase, the `star()` method provides one type of neighborhood that is particularly natural for hypergraphs and has wide applicability: it produces the set of hyperedges that contain a given hyperedge. For example, let us populate a hypergraph like this:

```pycon
>>> hg.add(hedge('(of/B.ma moon/C jupiter/C)'))
>>> hg.add(hedge('(of/B.ma moon/C saturn/C)'))
```

So let us obtain the star of the atom `moon/C`:

```pycon
>>> hg.star(hedge('moon/C'))
<generator object at 0x102382d30>
```

It returns a generator, allowing for the iteration through a very large number of hyperedges without exhausting memory. In this case, let us just convert the generator into a list to see the results:

```pycon
>>> list(hg.star(hedge('moon/C')))
[(of/B.ma moon/C jupiter/C), (of/B.ma moon/C saturn/C)]
```

Let us combine several of the previous ideas to define a specific type of neighborhood: the set of hyperedges of type concept that are directly connected to `moon/C`:

```python
concepts = set()
for edge in hg.star(hedge('moon/C')):
    for subedge in edge:
        if edge.type() == 'C':
            concepts.add(subedge)
```

The set `concepts` will then contain: `moon/C`, `jupiter/C`, `saturn/C`.

## Hyperedges containing a given set of hyperedges

The hypergraph database provides a very efficient way to query for all hyperedges that include a given set of hyperedges, with the method `edges_with_edges()`:

```pycon
>>> hg.add('(plays/P mary/C chess/C)')
(plays/P mary/C chess/C)
>>> hg.add('(plays/P john/C chess/C)')
(plays/P john/C chess/C)
>>> hg.add('(plays/P alice/C handball/C)')
(plays/P alice/C handball/C)
>>> list(hg.edges_with_edges([hedge('plays/P'), hedge('chess/C')]))
[(plays/P john/C chess/C), (plays/P mary/C chess/C)]
```

An optional `root` argument can be added, further requiring the matching edges to contain an atom with that root (at the top level):

```pycon
>>> list(hg.edges_with_edges([hedge('plays/C'), hedge('chess/C')], root='john'))
[(plays/C john/C chess/C)]
```

## Searching for hyperedges

Another fundamental way to query a hyperedge is by search patterns. Search patterns are templates that match hyperedges. hyperbase provides a sophisticated pattern language that allows for semantically rich modes of matching. This will be discussed in greater detail in the next section. For now, let us just consider the wildcard `*`, which matches any hyperedge (atomic or not). For example, the pattern `(of/B.ma * *)` matches both of the previously defined hyperedges. The `search()` method of `Hypergraph` allows for search using these patterns. Like `star()`, it returns a generator:

```pycon
>>> list(hg.search('(of/B.ma * *)'))
[(of/B.ma moon/C jupiter/C), (of/B.ma moon/C saturn/C)]
```

## Degrees and deep degrees

In conventional graph theory, there is the notion of the degree of a node, which is the number of other nodes that it is directly connected to. This is a simple but generally useful measure of the *centrality* of a node in the graph. In hypergraphs we can also have the same notion of degree, with the only difference that a single hyperedge can connect one entity to several others. hyperbase keeps track of the degree of every hyperedge, and the `Hypergraph` class provides a method to obtain it:

```pycon
>>> from hyperbase import *
>>> hg = hgraph('example.db')
>>> hg.degree('alice/C')
0
```

The degree of any hyperedge that does not exist in the hypergraph is 0. Notice also that `degree()`, as well as many other `Hypergraph` methods, conveniently accept the string representation of hyperedge, and transparently perform the conversion.

Let us add a few hyperedges and check the resulting degrees:

```pycon
>>> hg.add('(in/B alice/C wonderland/C)')
(in/B alice/C wonderland/C)
>>> hg.degree('alice/C')
1
>>> hg.degree('(in/B alice/C wonderland/C)')
0
>>> hg.add('(reads/P john/C (in/B alice/C wonderland/C))')
(reads/P john/C (in/B alice/C wonderland/C))
>>> hg.degree('(in/B alice/C wonderland/C)')
1
>>> hg.add('(plays/P alice/C chess/C)')
(plays/P alice/C chess/C)
>>> hg.degree('alice/C')
2
```

Given that hyperedges can recursively contain other hyperedges, we can also consider the *deep degree*, which takes into account deep connections. For example, consider the edge `(reads/P john/C (in/B alice/C wonderland/C))`. For the calculation of degrees, `john/C` is not considered here to be connected to `alice/C`, but such a connection is counted for the deep degree:

```pycon
>>> hg.degree('alice/C')
2
>>> hg.deep_degree('alice/C')
3
```

## Hyperedge attributes

The hypergraph database allows for the association of attributes to hyperedges. These can be strings, integer or floats, and are identified by a label. For example, one can associate a hyperedge to the text that it corresponds to:

```pycon
>>> hg.set_attribute('(in/B alice/C wonderland/C)', 'text', 'Alice in Wonderland')
True
>>> hg.get_str_attribute('(in/B alice/C wonderland/C)', 'text')
'Alice in Wonderland'
```

Notice that the method `set_attribute()` is used to set attributes of any type, but it is up to the programmer to choose the getter method according to the desired output type:

```pycon
>>> hg.set_attribute('alice/C', 'age', 7)
True
>>> hg.get_int_attribute('alice/C', 'age')
7
>>> hg.set_attribute('alice/C', 'height', 1.2)
True
>>> hg.get_float_attribute('alice/C', 'height')
1.2
```

In fact, this is how degrees and deep degrees are stored, respectively in the attributes "d" and "dd", so these attribute names should not be used for other purposes. The call `hg.degree(edge)` is equivalent to `hg.get_int_attribute(edge, 'd')`.

Integer attributes can also be incremented and decremented:

```pycon
>>> hg.add('(red/M button/C)')
(red/M button/C)
>>> hg.set_attribute('(red/M button/C)', 'clicks', 0)
True
>>> hg.inc_attribute('(red/M button/C)', 'clicks')
True
>>> hg.get_int_attribute('(red/M button/C)', 'clicks')
1
>>> hg.dec_attribute('(red/M button/C)', 'clicks')
True
>>> hg.get_int_attribute('(red/M button/C)', 'clicks')
0
```

## Local and global counters

Normally, when adding a hyperedge that already exists, nothing is changed. It is sometimes useful to count occurrences while adding hyperedges, and in this case the `count=True` optional argument can be specified when calling `add()`. This increments the `count` integer argument of the hyperedge every time it is added:

```pycon
>>> hg.add('(counting/P sheep/C)', count=True)
(counting/P sheep/C)
>>> hg.get_int_attribute('(counting/P sheep/C)', 'count')
1
>>> hg.add('(counting/P sheep/C)', count=True)
(counting/P sheep/C)
>>> hg.get_int_attribute('(counting/P sheep/C)', 'count')
2
```

The hypergraph database also provides the following global counters:

- `Hypergraph.atom_count()`: total number of atoms
- `Hypergraph.edge_count()`: total number of hyperedges
- `Hypergraph.primary_atom_count()`: total number of primary atoms
- `Hypergraph.primary_edge_count()`: total number of primary hyperedges

## Working with hyperedge sequences

The hypergraph database provides for a mechanism to organize hyperedges into sequences. This is useful when storing hyperedges extracted from natural language sources where the order in which they appear can be relevant. For example, we might be interested in parsing every sentence in a book into a hyperedge and then being able to know which hyperedges correspond to the sentence that came before and after.

A hyperedge can be added to the end of a given sequence in the hypergraph (identified by a string label). For example:

```pycon
>>> hg.add_to_sequence('sentences', '(is/P this/C (the/M (first/M sentence/C)))')
(seq/P/. sentences 0 (is/P this/C (the/M (first/M sentence/C))))
```

The outer edge with the special predicate `seq/P/.` assigns the hyperedge to the sequence "sentences" at position 0. Furthermore, for every sequence a special hyperedge is created to store attributes related to the sequence:

```
(seq_attrs/P/. sentences)
```

In its current implementation, this is used only to store the current size of the sequence as an integer under attribute 'size'. This attribute is used and updated by `hg.add_to_sequence()`, to determine the position at which to insert the next element in the sequence.

The method `sequences()` returns a generator for all the sequences contained in the hypergraph:

```pycon
>>> list(hg.sequences())
[sentences]
```

The method `sequence()` provides a generator for all the hyperedges contained in a given sequence, in order:

```pycon
>>> hg.add_to_sequence('sentences', '(is/P this/C (the/M (second/M sentence/C)))')
(seq/P/. sentences 1 (is/P this/C (the/M (second/M sentence/C))))
>>> hg.add_to_sequence('sentences', '(is/P this/C (the/M (third/M sentence/C)))')
(seq/P/. sentences 2 (is/P this/C (the/M (third/M sentence/C))))
>>> list(hg.sequence('sentences'))
[(is/P this/C (the/M (first/M sentence/C))), (is/P this/C (the/M (second/M sentence/C))), (is/P this/C (the/M (third/M sentence/C)))]
```

No methods are provided to remove hyperedges from the sequence, or to insert hyperedges somewhere other than the end of the sequence. This is meant to be a very simple and fast mechanism.
