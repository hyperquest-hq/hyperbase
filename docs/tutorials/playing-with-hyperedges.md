# Playing with Hyperedges

Hyperedges are the fundamental building blocks of Semantic Hypergraphs. In this tutorial, we will learn how to create, inspect and manipulate them.

## Creating hyperedges with hedge()

The `hedge()` function is the main entry point for creating hyperedges.

```python
from hyperbase import hedge
```

The simplest thing we can create is an **atom** -- a single concept:

```pycon
>>> mary = hedge('mary/C')
>>> mary
mary/C
```

Here, `mary` is the root (the word itself) and `C` is the type, in this case a concept.

We can also create non-atomic hyperedges -- structures that combine multiple elements:

```pycon
>>> edge = hedge('(likes/P.so mary/C chess/C)')
>>> edge
(likes/P.so mary/C chess/C)
```

This represents the idea "Mary likes chess". The first element (`likes/P.so`) is the **connector** -- it defines the relationship. The remaining elements are **arguments**: the subject and the object. `P` indicates another type, predicate. Notice that the `.so` annotation specifies the argument roles. There is one letter per argument, in this case `s` indicating that the first argument is the subject (`mary/C`) and `o` that the second is the object (`chess/C)`).

Atoms often have subtypes, which are represented by lowercase letters after the uppercase main type. For example, `mary/Cp` indicates a *proper noun concept* and `chess/Cc` a *common noun concept*. Then:

```pycon
>>> edge = hedge('(likes/P.so mary/Cp chess/Cc)')
>>> edge
(likes/P.so mary/C chess/C)
```

### From Python lists

You can also build hyperedges from Python lists:

```pycon
>>> edge = hedge(['likes/P.so', 'mary/Cp', 'chess/Cc'])
>>> edge
(likes/P.so mary/Cp chess/Cc)
```

This produces the same result. Lists are handy when you are constructing edges programmatically.

## Atoms vs. non-atomic hyperedges

Every hyperedge is either atomic or non-atomic. You can check which one you have:

```pycon
>>> atom = hedge('mary/Cp')
>>> atom.atom
True

>>> edge = hedge('(likes/P.so mary/Cp chess/Cc)')
>>> edge.atom
False
>>> edge.not_atom
True
```

## Inspecting atoms

Here are some often used ways to inspect atoms:

```pycon
>>> atom = hedge('paris/Cp')
>>> atom.root()
'paris'
>>> atom.t
'Cp'
>>> atom.mt
'C'
>>> atom.label()
'paris'
```

- `root()` -- the word itself
- `t` or `type()` -- the full type string (e.g., `Cp` for proper noun concept)
- `mt` or `mtype()` -- just the main type character (`C`)
- `label()` -- a human-readable label (URL-decodes the root)

The label is especially useful when roots contain encoded characters:

```pycon
>>> hedge('new%20york/Cp').label()
'new york'
```

## Indexing into hyperedges

Since hyperedges are based on Python tuples, you can index into them:

```pycon
>>> edge = hedge('(likes/P.so mary/Cp chess/Cc)')
>>> edge[0]
likes/P.so
>>> edge[1]
mary/Cp
>>> edge[2]
chess/Cc
```

The first element (`edge[0]`) is always the connector. The rest are arguments. You can also iterate over the elements:

```pycon
>>> for element in edge:
...     print(element)
likes/P.so
mary/Cp
chess/Cc
```

## Types and type inference

Every hyperedge has a type. For atoms, the type is written explicitly. For non-atomic hyperedges, the type is **inferred** from the connector:

```pycon
>>> edge = hedge('(likes/P.so mary/Cp chess/Cc)')
>>> edge.t
'R'
>>> edge.mt
'R'
```

The edge has type `R` (Relation), because a predicate (`P`) applied to arguments produces a relation. Meanwhile, the connector itself is of type `P`:

```pycon
>>> edge.ct  # connector type
'P'
```

## Exploring structure

Hyperedges can be nested. Let's work with a richer example:

```pycon
>>> edge = hedge('(is/P.so (the/Md sky/Cc) blue/Cc)')
>>> edge
(is/P.so (the/Md sky/Cc) blue/Cc)
```

This represents "the sky is blue". Notice how `(the/Md sky/Cc)` is itself a hyperedge nested inside the outer one.

### Size and depth

```pycon
>>> edge.size()
4
>>> edge.depth()
2
```

The `size()` counts total atoms (4: `is`, `the`, `sky`, `blue`). The `depth()` measures the deepest nesting level.

### Atoms

```pycon
>>> edge.atoms()
{is/P.so, the/Md, sky/Cc, blue/Cc}
>>> edge.all_atoms()
[is/P.so, the/Md, sky/Cc, blue/Cc]
```

`atoms()` returns a set (unique atoms), while `all_atoms()` returns a list preserving order and duplicates.

### Subedges

```pycon
>>> edge.subedges()
{(is/P.so (the/Md sky/Cc) blue/Cc), is/P.so, (the/Md sky/Cc), the/Md, sky/Cc, blue/Cc}
```

This gives you every subedge at every level, including atoms and the edge itself.

### Containment

```pycon
>>> edge.contains('blue/Cc')
True
>>> edge.contains('sky/Cc')
False
>>> edge.contains('sky/Cc', deep=True)
True
```

By default, `contains()` only checks direct children. Use `deep=True` to search recursively.

## Labels

The `label()` method produces a human-readable version of a hyperedge, rearranging elements to approximate natural language:

```pycon
>>> hedge('(is/P.so paris/Cp nice/Cc)').label()
'paris is nice'
>>> hedge('(red/M shoes/Cc)').label()
'red shoes'
```

## Building new hyperedges

Hyperedges are immutable -- every operation returns a new object.

### Replacing atoms

```pycon
>>> edge = hedge('(is/P.so paris/Cp nice/Cc)')
>>> edge.replace_atom(hedge('paris/Cp'), hedge('paris/Cp'))
(is/P.so paris/Cp nice/Cc)
```

You can even replace an atom with a non-atomic hyperedge:

```pycon
>>> edge.replace_atom(hedge('paris/Cp'), hedge('(the/Md city/Cc)'))
(is/P.so (the/Md city/Cc) nice/Cc)
```

### Inserting arguments

```pycon
>>> edge = hedge('(is/P.so paris/Cp nice/Cc)')
>>> spec = hedge('(in/T (the/M spring/Cc))')
>>> edge.add_argument(spec, 'x', 3)
(is/P.sox really/M paris/Cp nice/Cc (in/T (the/M spring/Cc)))
```

## Argument roles

The letters after the dot in a predicate encode the **argument roles** -- what role each argument plays:

```pycon
>>> edge = hedge('(is/P.so paris/Cp nice/Cc)')
>>> edge.argroles()
'so'
```

Here, `s` means "subject" and `o` means "object". You can retrieve arguments by their role:

```pycon
>>> edge.arguments_with_role('s')
[paris/Cp]
>>> edge.arguments_with_role('o')
[nice/Cc]
```

## Validation

You can check whether a hyperedge is structurally correct:

```pycon
>>> hedge('(is/P.so paris/Cp nice/Cc)').check_correctness()
{}
>>> hedge('(paris/Cp nice/Cc)').check_correctness()
{(paris/Cp nice/Cc): [('cosnn-bad-type', 'connector has incorrect type: C')]}
```

An empty dictionary means the edge is well-formed. Otherwise, you get a description of what is wrong -- in this case, a concept (`C`) cannot be used as a connector.
