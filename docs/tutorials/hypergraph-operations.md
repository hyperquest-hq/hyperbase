# Hypergraph Operations

An hypergraph can also be seen as a type of database, that stores knowledge in the form of sets of hyperedges, and provides functions that make it easy to add and search for hyperedges in useful ways. We will see here how to perform some fundamental tasks with hypergraphs.

The notebook for this tutorial can be found here:

<https://github.com/hyperbase/hyperbase/blob/master/notebooks/hypergraph.ipynb>

From here on, the following imports are assumed:

```python
from hyperbase import *
from hyperbase.notebook import *
from hyperbase.parsers import *
```

## Create an hypergraph

Creating an hypergraph is straightforward:

```python
hg = hgraph('example.db')
```

This assigns a hypergraph instance to `hg`, which is physically stored as 'example.db'. If this hypergraph already exists, it is simply opened. If it does not exist, an empty one is created.

## Parse sentence and add hyperedge to hypergraph

Let's create a parser to obtain an hyperedge from a sentence, and then add it to the hypergraph:

```python
parser = create_parser(lang='en')
text = "Mary is playing a very old violin."

parses = parser.parse(text)
for parse in parses['parses']:
    edge = parse['main_edge']
    hg.add(edge)
```

Notice that the `add()` function works recursively. We will see in the next subsection that not only the top hyperedge, but all of their children are added to the hypergraph.

## Iterate through all edges

Hypergraph objects include the function `all()`, which returns an iterator that can be used to traverse all the hyperedges contained in the hypergraph. Let's see an example, in this case assuming that we are in a notebook environment:

```python
for edge in hg.all():
    show(edge, style='oneline')
```

## Search with patterns

Hypergraph objects have a generic `search()` function, which returns iterators corresponding to sets of hyperedges that match a given pattern.

```python
edge_iterator = hg.search(pattern)
```

For example, with the current hypergraph, executing the below code would produce matching results:

```python
# '...' at the end indicates that the edge may have an arbitrary number of extra entities
for edge in hg.search('((is/Mv.|f--3s-/en playing/Pd.so.|pg----/en) ...)'):
    show(edge, style='oneline')
```

For all the details about how to define search patterns, refer to the `search()` function documentation:

<https://hyperbase.net/manual/api.html>
