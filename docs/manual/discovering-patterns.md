# Discovering Patterns

Patterns are useful to identify hyperedge structures from which knowledge can be inferred. To facilitate the discovery of such patterns, hyperbase provides the `PatternCounter`, a class in the `hyperbase.patterns` module. By creating an instance of this class, one can feed it a collection of hyperedges and then obtain the most frequent patterns inferred from these hyperedges. This way, empirical sources can be used to guide the discovery of knowledge inference methods. We will see that `PatternCounter` can be tuned to focus on specific constructs and to operate at different levels of abstraction.

## A simple example

To exemplify, let us first generate a hypergraph parsed from real text. For this, we will use the "wikipedia" reader / parser, which extracts the text from a Wikipedia page identified by its URL, and then populates a hypergraph by parsing each sentence of the text into a hyperedge. Let us run this reader / parser from the command line:

```
$ hyperbase --hg ai.db --url https://en.wikipedia.org/wiki/Artificial_intelligence wikipedia
```

Once it finishes, we will have the `ai.db` hypergraph database in the current directory. Let us now simply find the most common patterns in this hypergraph:

```python
from hyperbase import hgraph
from hyperbase.patterns import PatternCounter

hg = hgraph('ai.db')
pc = PatternCounter()
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

We see above that we create a `PatternCounter` object and then iterate through all the primary hyperedges in the hypergraph, feeding it to the counter one at a time by way of calling the `count(edge)` method. By default, the `PatternCounter` recurses into the internal structure of each hyperedge, so inner constructs are also counted. Let us now query for the 10 most common patterns found:

```pycon
>>> pc.patterns.most_common(10)
[((*/M */C), 2208),
 ((*/J */C */C), 1867),
 ((*/B.ma */C */C), 1315),
 ((*/J */M */M), 708),
 ((*/J */P */P), 628),
 ((*/M (*/M */C)), 456),
 ((*/T */C), 448),
 ((*/B.ma (*/M */C) */C), 385),
 ((*/B.ma */C (*/M */C)), 315),
 ((*/B.mm */C */C), 266)]
```

We see that most patterns are related to concept construction. We can set the `count_subedges` argument to `False` to only focus on the top-level structures:

```python
pc = PatternCounter(count_subedges=False)
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

```pycon
>>> pc.patterns.most_common(10)
[((*/J */C */C), 1569),
 ((*/J */M */M), 708),
 ((*/J */P */P), 628),
 ((*/J */R */R), 131),
 ((*/J */T */T), 55),
 ((*/J */B */B), 30),
 ((*/B.mm */C */C), 29),
 ((*/J (*/J */R */R) */R), 29),
 ((*/P.so */C */C), 26),
 ((*/J */R */C), 24)]
```

Here we see that the results become more dominated by conjunctions, and relational constructs come more to the top.

## Focusing the exploration by controlling expansions

The `PatternCounter` works by recursively expanding the given hyperedge up to a maximum depth is reached (`max_depth` argument with default `2`). Notice that the atom `*` is the most general pattern possible, matching anything. For example, with typing, all relations would generalize to `*/R`. If instead we keep going, and recursively "expand" the hyperedge into its constituent elements, replacing these elements with typed wildcards, we get less general but possibly more useful patterns, as the ones we saw above.

By default, all hyperedges are expanded. The constructor argument `expansions` defaults to `{'*'}`. It is however possible to have more control, and focus the expansions on more specific things that interest us. This is achieved by specifying patterns. Each hyperedge that is fed to the counter is only expanded (and also recursively) if it happens to match one of the patterns in `expansions`. Let us say that we are interested in relations with at least two arguments:

```python
pc = PatternCounter(expansions={'(*/P * * ...)'})
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

```pycon
>>> pc.patterns.most_common(10)
[((*/P.so */C */C), 146),
 ((*/P.sc */C */C), 92),
 ((*/P.sx */C */S), 65),
 ((*/P.sr */C */R), 57),
 ((*/P.sox */C */C */S), 54),
 ((*/P.px */C */S), 37),
 ((*/P.ox */C */S), 37),
 ((*/P.sr */C */S), 35),
 ((*/P.o? */C */R), 27),
 ((*/P.s? */C */R), 23)]
```

Any pattern(s) can be used here to control the expansions and focus the exploration.

## Including explicit roots in the patterns

The examples we have seen so far produce completely abstract patterns. It is also useful to be able to discover patterns where certain hyperedges are not wildcards, but instead contain the roots of the atoms. This is achieved with the `match_roots` constructor argument. Here one can include patterns that, when matched, cause the expansion to produce explicit atoms instead of wildcards. For example, we could be interested in the actual predicates of the most common relations:

```python
pc = PatternCounter(expansions={'(*/P * * ...)'}, match_roots={'*/P'})
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

```pycon
>>> pc.patterns.most_common(10)
[((is/P.sc */C */C), 27),
 ((are/P.sc */C */C), 17),
 ((has/P.so */C */C), 6),
 ((include/P.so */C */C), 6),
 ((have/P.so */C */C), 5),
 (((can/M be/P.sc) */C */C), 3),
 ((developed/P.so */C */C), 3),
 ((maximize/P.so */C */C), 3),
 ((perceives/P.so */C */C), 3),
 (((could/M spell/P.so) */C */C), 2)]
```

Notice that `match_roots` also causes the expansion of the matched expression, even if it does not match any pattern in `expansions`. We see this case above with `(*/M */P)` structures. Exploiting the machinery of patterns, many variations can be achieved. For example, we might be interested in only matching the roots of the predicate atoms, but keep the rest of the predicate abstract. This can be achieved by using `match_roots={'./P'}` (remember that the `.` wildcard only matches atoms):

```python
pc = PatternCounter(expansions={'(*/P * * ...)'}, match_roots={'./P'})
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

```pycon
>>> pc.patterns.most_common(10)
[((is/P.sc */C */C), 27),
 ((are/P.sc */C */C), 17),
 (((*/M be/P.sc) */C */C), 9),
 ((has/P.so */C */C), 6),
 ((include/P.so */C */C), 6),
 (((*/M have/P.so) */C */C), 5),
 ((have/P.so */C */C), 5),
 (((*/M is/P.sc) */C */C), 5),
 ((developed/P.so */C */C), 3),
 ((maximize/P.so */C */C), 3)]
```

## Matching subtypes

One might also be interested in including subtypes in the patterns. Again, this is achievable by specifying a constructor argument, `match_subtypes`. Following the same logic of the previous arguments, this is a set of patterns that triggers subtype inclusion in expansions when matched. Let us say, for example, that we are interested in the most common concept modifiers including subtypes:

```python
pc = PatternCounter(expansions={'(*/M */C)'}, match_roots={'*/M'}, match_subtypes={'*/M'})
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)
```

```pycon
>>> pc.patterns.most_common(10)
[((the/Md */C), 341),
 ((a/Md */C), 118),
 ((human/Ma */C), 53),
 ((artificial/Ma */C), 45),
 ((an/Md */C), 36),
 ((its/Mp */C), 25),
 ((other/Ma */C), 24),
 ((this/Md */C), 23),
 ((some/Md */C), 21),
 ((intelligent/Ma */C), 18)]
```

## Build your own

The combination of `PatternCounter` and the expressiveness of SH patterns allows for countless semantically rich modes of pattern discovery in empirical data. Many more examples could be provided, but we hope that the building blocks that we described are enough to get you started. This is an open-ended exploration tool, certainly capable of being used in ways that the authors did not think of.
