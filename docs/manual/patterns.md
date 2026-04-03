# Patterns

Hyperbase implements language to define hyperedge patterns. These patterns are valid hyperedges themselves, and are defined with the help of special atoms: *wildcards* and *variables*. The former are useful for simple matching, while the latter allow for the extraction of specific parts of a hyperedge.

## Matching with wildcards

The basic wildcard is `*`. It matches any hyperedge. It allows for the definition of patterns like this:

```clojure
(plays/P.so * *)
```

Here's how it can be used to match hyperedges:

```python
from hyperbase import hedge
pattern = hedge("(plays/P.so * *)")
edge = hedge("(plays/P.so alice/C chess/C)")
edge.match(pattern)  # returns [{}]
edge = hedge("(likes/P.so alice/C chess/C)")
edge.match(pattern)  # returns []
```

Notice that, in the first case, a list with an empty dictionary is returned (`[{}]`) to indicate a match. We will see later how these dictionaries are used to return the values taken by pattern variables. In the second case the edge does not match the pattern, so an empty list is returned.

Since an empty list evaluates to False, this method can also be used as a boolean condition:

```python
from hyperbase import hedge
pattern = hedge("(plays/P.so * *)")
edge = hedge("(plays/P.so alice/C chess/C)")
if edge.match(pattern):
    print("match found")  # this is printed
else:
    print("no match")
```

There are two more wildcards:

- `.`, which only matches atoms.
- `(*)`, which only matches non-atomic hyperedges.

Furthermore, it is possible to specify types and roles in wildcards, as in any other atom. For example `*/C` only matches hyperedges of type concept. `(*/C)` only matches non-atomic hyperedges of type concept, and so on.

It is possible to specify the optional presence of further arguments with the special atom `...`, which simply indicates that any number (including zero) hyperedges may be present at that point. For instance:

```clojure
(plays/P * *)
```

does not match:

```clojure
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

but this pattern does:

```clojure
(plays/P * * ...)
```

## Type and subtype matching

If only a type but not a subtype is specified in the pattern, then any subtypes of the given type will match, as can be seen in this example:

```python
from hyperbase import hedge
pattern = hedge("(plays/P.so */C */C)")
edge = hedge("(plays/Pd.so alice/Cp chess/Cc)")
edge.match(pattern)  # returns [{}]
```

Even though the full types of `plays/Pd.so`, `alice/Cp` and `chess/Cc` are not specified in the pattern, they still match the more general corresponding atoms `plays/P.so` and `*/C`.

## Matching argroles

As we have seen, argroles can be specified in patterns. So:

```clojure
(plays/P.so * *)
```

matches:

```clojure
(plays/P.so alice/C chess/C)
```

but not:

```clojure
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

It is often desirable to match for the presence of a given set of argroles, independently of their respective positions, or of the presence of further argroles outside the set. This is indicated by surrounding with curly brackets the set of argroles that is to be matched in this way. For example:

```clojure
(is/P.{sc} * */C)
```

The above pattern would match both (independently of position):

```clojure
(is/P.sc (the/M sky/C) blue/C)
(is/P.cs blue/C (the/M sky/C))
```

and also (independently of the presence of further argroles outside the set):

```clojure
(is/P.scx (the/M sky/C) blue/C (in/T (the/M morning/C)))
```

In fact, when specifying argroles, more often than not this is the behavior that is the most useful, because it allows for the matching of the participants of a relationship purely according to the role they play in it (subject, object, etc.).

Sometimes it is also desirable to explicitly forbid certain argument roles. This is achieved by indicating them after '-' in the argrole sequence. For example:

```clojure
(plays/P.{so}-x * *)
```

does not match:

```clojure
(plays/P.sox alice/C chess/C (at/T (the/M club/C)))
```

## Patterns with variables for information extraction

Let us introduce the concept of *variable*. Like a wildcard, a variable indicates a placeholder that can match a hyperedge, but can then be used to refer to that matched hyperedge. In SH representation, an atom label that starts with upper case represents a variable. For example: `PLAYER/C`. One can define perfectly valid hyperedges that include variables, as well as wildcards, so for example:

```clojure
(plays/P.{so} PLAYER/C *)
```

Then `edge.match(pattern)` can be used to apply patterns to edges. It works like this:

```python
from hyperbase import hedge
pattern = hedge("(plays/P.{so} PLAYER/C *)")
edge = hedge("(plays/P.so mary/C *)")
edge.match(pattern)  # [{'PLAYER': mary/C}]
```

So, `edge.match(pattern)` gives a list of dictionaries (one pattern can match the same edge in several ways). Each dictionary represents a match, and assigns values to the pattern variable(s).

## Functional patterns

More sophisticated patterns can be represented with the help of functional pattern expressions. These expressions are akin to function application in LISP-like languages, and take the general form:

```clojure
(functional-pattern-name argument_1 ...)
```

!!! note
    To simplify the notation, hyperbase applies the convention that an atom without a type annotation defaults to the conjunction type (`/J`). This means that any edge with a functional pattern connector can contain arguments of any other type and remain itself valid within the Semantic Hypergraph representation.

### Atoms

The `atoms` functional pattern matches any edge that contains all the atoms provided as arguments, at any depth:

```clojure
(atoms atom_1 ...)
```

For example this pattern:

```clojure
(atoms going/P)
```

would match the edge:

```clojure
(is/M (not/M going/P))
```

In the same vein, this pattern:

```clojure
(atoms not/M going/P)
```

would equally match the edge:

```clojure
(is/M (not/M going/P))
```

but not:

```clojure
(is/M going/P)
```

Furthermore, the atoms can define wildcards and all the pattern syntax specified above, for example:

```clojure
(atoms not/M */P)
```

### Var

The `var` functional pattern is used to specify a part of a pattern while also capturing it as a variable. It has the general form:

```clojure
(var pattern-edge variable-name)
```

This way, a complex expression such as the following can be captured in a variable:

```clojure
(var (atoms not/M (lemma be/P)) PREDICATE)
```
