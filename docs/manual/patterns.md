# Patterns

Hyperbase implements language to define hyperedge patterns. These patterns are valid hyperedges themselves, and are defined with the help of special atoms: *wildcards* and *variables*. The former are useful for simple matching, while the latter allow for the extraction of specific parts of a hyperedge.

## Searching with wildcards

The basic wildcard is `*`. It matches any hyperedge. It allows for the definition of patterns like this:

```
(plays/P * *)
```

We can use them to search the hypergraph for matching hyperedges. For example:

```pycon
>>> from hyperbase import *
>>> hg = hgraph('example.db')
>>> hg.add('(plays/P.so alice/C chess/C)')
(plays/P.so alice/C chess/C)
>>> list(hg.search('(plays/P.so * *)'))
[(plays/P.so alice/C chess/C)]
```

There are two more wildcards:

- `.`, which only matches atoms.
- `(*)`, which only matches non-atomic hyperedges.

Furthermore, it is possible to specify types and roles in wildcards, as in any other atom. For example `*/C` only matches hyperedges of type concept. `(*/C)` only matches non-atomic hyperedges of type concept, and so on.

It is possible to specify the optional presence of further arguments with the special atom `...`, which simply indicates that any number (including zero) hyperedges may be present at that point. For instance:

```
(plays/P * *)
```

does not match:

```
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

but this pattern does:

```
(plays/P * * ...)
```

## Non-strict search

Non-strict search allows for patterns to match atoms in the most general way, meaning that, if a subtype or other roles are not specified in the pattern, then any subtypes or argroles will match, as can be seen in this example:

```pycon
>>> from hyperbase import *
>>> hg = hgraph('example.db')
>>> hg.add('(plays/Pd.so alice/Cp.s chess/Cc.s)')
(plays/Pd.so alice/Cp.s chess/Cc.s)
>>> list(hg.search('(plays/P alice/C *)', strict=False))
[(plays/Pd.so alice/Cp.s chess/Cc.s)]
```

Even though the full type and roles of `plays/Pd.so` and `alice/Cp.s` are not specified in the pattern, they still match the more general corresponding atoms `plays/P` and `alice/C`.

Non-strict search is semantically more powerful, at the expense of performance. Strict search can take advantage of the structure of the hypergraph database to perform fast queries, while non-strict search iterates through all edges in the hypergraph looking for matches.

## Matching argroles

Argroles can be specified in patterns. So:

```
(plays/P.so * *)
```

matches:

```
(plays/P.so alice/C chess/C)
```

but not:

```
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

It is often desirable to match for the presence of a given set of argroles, independently of their respective positions, or of the presence of further argroles outside the set. This is indicated by surrounding with curly brackets the set of argroles that is to be matched in this way. For example:

```
(is/P.{sc} * */C)
```

The above pattern would match both (independently of position):

```
(is/P.sc (the/M sky/C) blue/C)
(is/P.cs blue/C (the/M sky/C))
```

and also (independently of the presence of further argroles outside the set):

```
(is/P.scx (the/M sky/C) blue/C (in/T (the/M morning/C)))
```

In fact, when specifying argroles, more often than not this is the behavior that is the most useful, because it allows for the matching of the participants of a relationship purely according to the role they play in it (subject, object, etc.).

Sometimes it is also desirable to explicitly forbid certain argument roles. This is achieved by indicating them after '-' in the argrole sequence. For example:

```
(plays/P.{so}-x * *)
```

does not match:

```
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

When using `Hypergraph.search()`, order-independent (curly-braces) and argrole exclusions (-) only work in non-strict mode.

## Patterns with variables for information extraction

Let us introduce the concept of *variable*. Like a wildcard, a variable indicates a placeholder that can match a hyperedge, but can then be used to refer to that matched hyperedge. In SH representation, an atom label that starts with upper case represents a variable. For example: `PLAYER/C`. One can define perfectly valid hyperedges that include variables, as well as wildcards, so for example:

```
(plays/P.{so} PLAYER/C *)
```

Then the `match_pattern(edge, pattern)` function can be used to apply patterns to edges. It works like this:

```pycon
>>> from hyperbase import hedge
>>> from hyperbase.patterns import match_pattern
>>> pattern = hedge('(plays/P.{so} PLAYER/C *)')
>>> edge = hedge('(plays/P.so mary/C *)')
>>> match_pattern(edge, pattern)
[{'PLAYER': mary/C}]
```

So, `match_pattern` gives a list of dictionaries (one pattern can match the same edge in several ways). Each dictionary represents a match, and assigns a value to a variable.

The `Hypergraph` object provides the `match()` method, which is similar to `search()` but returns dictionaries with the matched variables. Like search, it offers a non-strict mode with the same trade-offs:

```pycon
>>> hg.add('(is/Pd.cs blue/Ca (the/M sky/C))')
(is/Pd.cs blue/Ca (the/M sky/C))
>>> hg.add('(is/Pd.sc (the/M sky/C) blue/Ca)')
(is/Pd.sc (the/M sky/C) blue/Ca)
>>> list(hg.match('(is/P.{sc} OBJ/C PROP)', strict=False))
[((is/Pd.cs blue/Ca (the/M sky/C)), [{'OBJ': (the/M sky/C), 'PROP': blue/Ca}]),
 ((is/Pd.sc (the/M sky/C) blue/Ca), [{'OBJ': (the/M sky/C), 'PROP': blue/Ca}])]
```

The output is a list of tuples, where the first item is the matched hyperedge and the second is a dictionary with variables and their values.

## Functional patterns

Even more sophisticated patterns can be represented with the help of functional pattern expressions. These expressions are akin to function application in LISP-like languages, and take the general form:

```
(functional-pattern-name argument_1 ...)
```

!!! note
    To simplify the notation, hyperbase applies the convention that an atom without a type annotation defaults to the conjunction type (`/J`). This means that any edge with a functional pattern connector can contain arguments of any other type and remain itself valid within the Semantic Hypergraph representation.

### Atoms

The `atoms` functional pattern matches any edge that contains all the atoms provided as arguments, at any depth:

```
(atoms atom_1 ...)
```

For example this pattern:

```
(atoms going/P)
```

would match the edge:

```
(is/M (not/M going/P))
```

In the same vein, this pattern:

```
(atoms not/M going/P)
```

would equally match the edge:

```
(is/M (not/M going/P))
```

but not:

```
(is/M going/P)
```

Furthermore, the atoms can define wildcards and all the pattern syntax specified above, for example:

```
(atoms not/M */P)
```

### Lemma

The `lemma` functional pattern matches any atom which has the same lemma as the one specified. This functional pattern only works in the context of a hypergraph database that contains lemma information, that can be generated by the parsers provided with hyperbase.

For example, this pattern:

```
(lemma be/P)
```

could be used to match:

```
is/P
was/P
```

!!! note
    When using `lemma`, it is necessary to specify some semantic hypergraph object when calling the pattern matching function: `match_pattern(edge, pattern, hg=hg)`.

### Var

The `var` functional pattern is used to specify a part of a pattern while also capturing it as a variable. It has the general form:

```
(var pattern-edge variable-name)
```

This way, a complex expression such as the following can be captured in a variable:

```
(var (atoms not/M (lemma be/P)) PREDICATE)
```
