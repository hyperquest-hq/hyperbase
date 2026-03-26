# Basic Hyperedge Operations

At the heart of Hyperbase lies the Semantic Hypergraph (SH). In practical terms, we will talk simply about *hypergraphs*. Hypergraphs are a collections of hyperedges. The Hyperedge class is the fundamental data structure in Hyperbase.

Hyperbase provides abstractions to create, inspect and modify hyperedges. In this section we introduce these basic operations, upon which all aspects of the library rely on.

## The central function of Hyperbase: hedge()

The root namespace `hyperbase` contains the most fundamental function of the library: `hedge(source)`, which creates a hyperedge from a string, or a Python list, or a tuple. In fact, this function is implemented in `hyperbase.hyperedge`, but it is imported to the root namespace by default for convenience.

## Creating and manipulating hyperedges

Hyperbase defines the object class `Hyperedge`, which provides a variety of methods to work with hyperedges. The full interface of this class is described in the API reference. However, these objects are not meant to be instantiated directly. Instead, the `hedge` function can be used to create such an object directly from a string representation conforming to the SH notation. For example:

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
