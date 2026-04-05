# Hyperedges

At the heart of Hyperbase lies the Semantic Hypergraph (SH). In practical terms, we will talk simply about *hypergraphs*. Hypergraphs are collections of hyperedges. Hyperbase provides abstractions to create, inspect and modify hyperedges. In this section we introduce these abstractions, upon which all aspects of the library rely on.

## The central function of Hyperbase: hedge()

The root namespace `hyperbase` contains the most fundamental function of the library: `hedge()`, which creates a hyperedge from a variety of sources. This function is implemented in `hyperbase.hyperedge`, but it is imported to the root namespace for convenience.

`hedge()` accepts the following input types:

- **str** -- a string representation in SH notation
- **list** or **tuple** -- a Python sequence, recursively converted
- **Hyperedge** or **Atom** -- returned as-is
- **ParseResult** -- a parse result from a parser, including text-to-atom mappings

It returns an instance of `Hyperedge` (or its subclass `Atom` for atomic edges), or `None` if the input cannot be parsed.

```python
from hyperbase import hedge

# From a string
edge = hedge('(plays/P.so mary/C chess/C)')

# From a list
edge = hedge(['plays/P.so', 'mary/C', 'chess/C'])

# Atoms are returned for atomic inputs
atom = hedge('mary/C')
```

## Hyperedge and Atom

Hyperbase defines two object classes: `Hyperedge` and `Atom`. `Atom` is a subclass of `Hyperedge`, and `Hyperedge` itself is derived from Python's `tuple`. These objects are not meant to be instantiated directly -- instead, use the `hedge()` function to create them.

### Atoms

An atom is the most basic unit of the Semantic Hypergraph. It is a single token with an internal structure defined by the [notation](notation.md): a root, a role (type, subtypes, argument roles), and optionally a namespace.

```pycon
>>> atom = hedge('mary/Cp.s/en')
>>> atom.atom
True
>>> atom.root()
'mary'
>>> atom.parts()
['mary', 'Cp.s', 'en']
>>> atom.role()
['Cp', 's']
>>> atom.type()
'Cp'
>>> atom.mtype()
'C'
>>> atom.label()
'mary'
```

The `root()` method extracts just the root string (the first part before `/`). The `parts()` method splits the atom into all its slash-delimited components. The `role()` method returns the role as a list of dot-separated subroles, and `type()` returns the first subrole (the type string). The `mtype()` method returns only the main type character.

The `label()` method generates a human-readable label by URL-decoding the root. This is useful because atom roots use URL-encoding for special characters:

```pycon
>>> atom = hedge('new%20york/Cp.s/en')
>>> atom.label()
'new york'
```

Atoms that have only a root and no type annotation are treated as conjunctions:

```pycon
>>> hedge('and').type()
'J'
```

#### Atom parts manipulation

You can build new atoms by replacing specific parts:

```pycon
>>> atom = hedge('mary/Cp.s/en')
>>> atom.replace_atom_part(0, 'john')
john/Cp.s/en
```

There is also a utility function `build_atom()` for constructing atoms from a text string and role parts:

```python
from hyperbase.hyperedge import build_atom

atom = build_atom('new york', 'Cp', 's', 'en')
# new%20york/Cp/s/en
```

And `str2atom()` for converting arbitrary strings into valid atom roots (URL-encoding special characters):

```python
from hyperbase.hyperedge import str2atom

str2atom('hello world')
# 'hello%20world'
```

### Non-atomic hyperedges

A non-atomic hyperedge is an ordered, recursive structure -- a sequence of hyperedges where the first element is the connector and the remaining elements are arguments. Since `Hyperedge` is derived from `tuple`, it makes it possible to do things such as:

```python
edge = hedge('(plays/P.so mary/C chess/C)')
person = edge[1]
```

In this case, `person` will be assigned the second element of the initial hyperedge, which happens to be the atom `mary/C`. Range selectors also work, but they do not automatically produce hyperedges, because subranges of the elements of a semantic hyperedge are not guaranteed to be valid semantic hyperedges themselves. Instead, simple tuples are returned:

```pycon
>>> edge = hedge('(plays/P.so mary/C chess/C)')
>>> edge[1:]
(mary/C, chess/C)
>>> type(edge[1:])
<class 'tuple'>
```

### Distinguishing atoms from non-atomic hyperedges

The `.atom` and `.not_atom` properties provide a clean way to test whether a hyperedge is atomic:

```pycon
>>> edge = hedge('(plays/P.so mary/C chess/C)')
>>> edge.atom
False
>>> edge.not_atom
True
>>> edge[1].atom
True
```

## Types and type inference

Every hyperedge has a type. For atoms, the type is explicit in the annotation. For non-atomic hyperedges, the type is inferred from the connector type according to the rules described in the [notation](notation.md) section.

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.type()
'R'
>>> edge.mtype()
'R'
>>> edge[0].type()
'P'
>>> edge[1].type()
'C'
```

The `type()` method returns the full type string (e.g. `'R'`, `'Cp'`), while `mtype()` returns just the main type character. For non-atomic hyperedges, `connector_type()` and `connector_mtype()` return the type of the edge's connector:

```pycon
>>> edge.connector_type()
'P'
>>> edge.connector_mtype()
'P'
```

Shortcut properties are also available: `.t` for `type()`, `.mt` for `mtype()`, `.ct` for `connector_type()`, and `.cmt` for `connector_mtype()`.

## Exploring hyperedge structure

### Atoms and size

The `atoms()` method returns the set of unique atoms in a hyperedge, while `all_atoms()` returns a list including duplicates:

```pycon
>>> edge = hedge('(the/Md (of/Br mayor/Cc (the/Md city/Cs)))')
>>> edge.atoms()
{the/Md, of/Br, mayor/Cc, city/Cs}
>>> edge.all_atoms()
[the/Md, of/Br, mayor/Cc, the/Md, city/Cs]
```

The `size()` method returns the total number of atoms at all depths, and `depth()` returns the maximal nesting depth (atoms have depth 0):

```pycon
>>> edge.size()
5
>>> edge.depth()
3
>>> hedge('mary/C').depth()
0
```

### Subedges

The `subedges()` method returns the set of all subedges contained in a hyperedge, including atoms and the edge itself:

```pycon
>>> edge = hedge('(is/P.sc (the/Md sky/Cc) blue/Cc)')
>>> edge.subedges()
{(is/P.sc (the/Md sky/Cc) blue/Cc), is/P.sc, (the/Md sky/Cc), the/Md, sky/Cc, blue/Cc}
```

### Containment

The `contains()` method checks whether a needle string is contained in an edge. With `deep=True`, the search is recursive:

```pycon
>>> edge = hedge('(is/P.sc (the/Md sky/Cc) blue/Cc)')
>>> edge.contains('blue/Cc')
True
>>> edge.contains('sky/Cc')
False
>>> edge.contains('sky/Cc', deep=True)
True
```

You can also check for atoms of a given type:

```pycon
>>> edge.contains_atom_type('Cc')
True
>>> edge.atom_with_type('Cc')
sky/Cc
```

### Connector and inner atoms

The `connector_atom()` method returns the innermost atom of the connector, traversing through modifier structures:

```pycon
>>> edge = hedge('(does/M (not/M like/P.so) john/C chess/C)')
>>> edge.connector_atom()
like/P.so
```

The `inner_atom()` method returns the inner atom of a modifier structure:

```pycon
>>> edge = hedge('(red/M shoes/C)')
>>> edge.inner_atom()
shoes/C
```

For atoms, `inner_atom()` returns the atom itself, and `connector_atom()` returns `None`.

### Roots

The `roots()` method returns a version of the edge where all atoms are reduced to their root form (no type annotations):

```pycon
>>> edge = hedge('(is/P.sc berlin/Cp.s nice/Cc)')
>>> edge.roots()
(is berlin nice)
```

## String representations and labels

The `to_str()` method converts a hyperedge back to its SH notation string. With `roots_only=True`, only atom roots are used:

```pycon
>>> edge = hedge('(is/P.sc berlin/Cp.s nice/Cc)')
>>> edge.to_str()
'(is/P.sc berlin/Cp.s nice/Cc)'
>>> edge.to_str(roots_only=True)
'(is berlin nice)'
```

The `label()` method generates a human-readable label. It rearranges elements to approximate natural language word order and URL-decodes atom roots:

```pycon
>>> hedge('(is/P.sc berlin/Cp.s nice/Cc)').label()
'berlin is nice'
>>> hedge('(red/M shoes/C)').label()
'red shoes'
```

Both `__str__` and `__repr__` return the SH notation string, so printing a hyperedge shows its notation directly.

## Pattern matching

The `match()` method matches a hyperedge against a pattern. Patterns are themselves edges, using special wildcard atoms:

- `*` -- general wildcard (matches any entity)
- `.` -- atomic wildcard (matches any atom)
- `(*)` -- edge wildcard (matches any non-atom)
- `...` at the end -- open-ended pattern (matches remaining elements)

Wildcards can be named to capture matched entities into variables (e.g. `*NAME`, `.ACTOR`, `(*CLAUSE)`). The method returns a list of match dictionaries. An empty list means no match; a list with an empty dictionary means the pattern matched but captured no variables.

```pycon
>>> edge = hedge('(is/P.so (my/Mp name/Cn) mary/Cp)')
>>> edge.match('(is/P.so (my/Mp name/Cn) *)')
[{}]
>>> edge.match('(is/P.so (my/Mp name/Cn) *NAME)')
[{'NAME': mary/Cp}]
>>> edge.match('(is/P.so . *NAME)')
[]
```

For more about patterns, see the [patterns](patterns.md) section.

## Building and modifying hyperedges

Since hyperedges are immutable (based on `tuple`), modification methods return new hyperedge objects.

### Concatenation with +

The `+` operator combines hyperedges:

```pycon
>>> hedge('is/P.sc') + hedge('berlin/C')
(is/P.sc berlin/C)
>>> hedge('(is/P.sc berlin/C)') + hedge('nice/C')
(is/P.sc berlin/C nice/C)
```

### insert_first_argument()

Places an argument as the first item after the connector:

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.insert_first_argument(hedge('really/M'))
(is/P.sc really/M berlin/C nice/C)
```

When called on an atom, the atom becomes the connector:

```pycon
>>> hedge('is/P.sc').insert_first_argument(hedge('berlin/C'))
(is/P.sc berlin/C)
```

### connect()

Adds arguments to the end of an edge:

```pycon
>>> edge = hedge('(is/P.sc berlin/C)')
>>> edge.connect((hedge('nice/C'),))
(is/P.sc berlin/C nice/C)
```

### sequence()

Sequences an entity before or after the elements of the edge:

```pycon
>>> edge = hedge('(a/C b/C)')
>>> edge.sequence(hedge('c/C'), before=True)
(c/C a/C b/C)
>>> edge.sequence(hedge('c/C'), before=False)
(a/C b/C c/C)
```

With `flat=False`, both sides are treated as self-contained edges:

```pycon
>>> edge.sequence(hedge('(c/C d/C)'), before=True, flat=False)
((c/C d/C) (a/C b/C))
```

### replace_atom()

Replaces every instance of an atom with a new hyperedge:

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.replace_atom(hedge('berlin/C'), hedge('(the/M city/C)'))
(is/P.sc (the/M city/C) nice/C)
```

With `unique=True`, only the exact same object instance is replaced (using object identity rather than value equality).

### simplify()

Returns a simplified version of a hyperedge, controlling which annotation parts to retain:

```pycon
>>> edge = hedge('(is/Pd.sc berlin/Cp.s/en nice/Cc)')
>>> edge.simplify()
(is/P berlin/C/en nice/C/en)
>>> edge.simplify(subtypes=True)
(is/Pd berlin/Cp/en nice/Cc/en)
>>> edge.simplify(argroles=True)
(is/P.sc berlin/C/en nice/C/en)
>>> edge.simplify(namespaces=False)
(is/P berlin/C nice/C)
```

## Argument roles

Argument roles specify the role each argument plays in a relation or built concept (see the [notation](notation.md) section for the full list of role codes).

### Querying argument roles

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.argroles()
'sc'
>>> edge.has_argroles()
True
```

### Retrieving edges by role

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.edges_with_argrole('s')
[berlin/C]
>>> edge.edges_with_argrole('c')
[nice/C]
```

### Modifying argument roles

`replace_argroles()` returns an edge with its connector's argument roles replaced:

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.replace_argroles('so')
(is/P.so berlin/C nice/C)
```

`insert_argrole()` inserts a role at a given position:

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.insert_argrole('o', 1)
(is/P.soc berlin/C nice/C)
```

`add_argument()` inserts both an edge and its corresponding argument role at a position:

```pycon
>>> edge = hedge('(is/P.sc berlin/C nice/C)')
>>> edge.add_argument(hedge('very/M'), 'x', 2)
(is/P.scx berlin/C nice/C very/M)
```

## Concepts

### Main concepts

In builder structures, `main_concepts()` returns the list of main concepts (those annotated with the `m` role):

```pycon
>>> edge = hedge("(of/B.ma founder/C psychoanalysis/C)")
>>> edge.main_concepts()
[founder/C]
```

### Replacing the main concept

`replace_main_concept()` returns a new edge with the main concept replaced:

```pycon
>>> edge = hedge("(of/B.ma founder/C psychoanalysis/C)")
>>> edge.replace_main_concept(hedge('creator/C'))
(of/B.ma creator/C psychoanalysis/C)
```

## Validation and normalization

### check_correctness()

Returns a dictionary of structural errors found in the edge. Each key is the problematic subedge, and the value is a list of `(code, message)` tuples. An empty dictionary means the edge is well-formed.

```pycon
>>> hedge('(is/P.sc berlin/C nice/C)').check_correctness()
{}
>>> hedge('(berlin/C nice/C)').check_correctness()
{(berlin/C nice/C): [('conn-bad-type', 'connector has incorrect type: C')]}
```

The checks include connector type validation, modifier and builder structure, trigger structure, predicate argument types, conjunction arity, and argument role counts and validity.

### normalized()

Returns a normalized version of the edge where argument roles (and their corresponding arguments) are sorted into a canonical order:

```pycon
>>> edge = hedge('(is/P.cs nice/C berlin/C)')
>>> edge.normalized()
(is/P.sc berlin/C nice/C)
```

## The text attribute

Both `Hyperedge` and `Atom` objects have a `text` attribute that stores the original natural language text from which the hyperedge was parsed. This is set automatically when creating a hyperedge from a `ParseResult`:

```python
for result in parser.parse("Mary plays chess."):
    edge = hedge(result)
    print(edge.text)  # "Mary plays chess."
```

## UniqueAtom

By default, atoms are compared by value -- two atom objects with the same string are considered equal. When you need identity-based comparison (e.g. to distinguish two different occurrences of the same atom within a hyperedge), Hyperbase provides `UniqueAtom` and the utility functions `unique()` and `non_unique()`:

```python
from hyperbase.hyperedge import unique, non_unique

edge = hedge('(the/Md (of/Br mayor/Cc (the/Md city/Cs)))')
u_edge = unique(edge)
# Now the two the/Md atoms are distinguishable

original = non_unique(u_edge)
# Back to normal value-based comparison
```
