# Parsing Natural Language

Parsing natural language to semantic hypergraphs is another crucial aspect of hyperbase. This aspect of the library is covered by the `hyperbase.parsers` package. Let us see how to create a parser, and how to use it to parse a sentence:

```pycon
>>> from hyperbase.parsers import create_parser
>>> parser = create_parser(lang='en')
>>> parse_results = parser.parse('Einstein first published the theory of relativity in 1905')
>>> parse_results['parses'][0]['main_edge']
((first/M/en published/Pd.sox.<f-----/en) einstein/Cp.s/en (of/Br.ma/en (the/Md/en theory/Cc.s/en) relativity/Cc.s/en) (in/Tt/en 1905/C#/en))
```

Notice that `create_parser()` takes some time (10 to 20 seconds is normal), because it has to load the underlying language models. Here we pass it the only mandatory parameter, which is the name of the parser to use. This will typically correspond to the language to parse. Currently only one parser for English is provided ("en"), but hyperbase already comes with auxiliary scripts to help in the development of parsers for other languages.

We also see that we specify a position in the `parse_results` data structure (at the top-level, it is a dictionary) to directly access the hyperedge that corresponds to the parsed sentence. This is because `parse_results` includes useful additional information about the parsed text, and also because the parsed text can correspond to more than one hyperedge. So let us take a look at the full contents of `parse_results` from the example above:

```pycon
>>> parse_results
{'parses':
    ({'main_edge': ((first/M/en published/Pd.sox.<f-----/en) einstein/Cp.s/en (of/Br.ma/en (the/Md/en theory/Cc.s/en) relativity/Cc.s/en) (in/Tt/en 1905/C#/en)),
      'extra_edges': set(),
      'failed': False,
      'text': 'Einstein first published the theory of relativity in 1905',
      'atom2word': {first/M/en: ('first', 1),
                    published/Pd.sox.<f-----/en: ('published', 2),
                    einstein/Cp.s/en: ('Einstein', 0),
                    of/Br.ma/en: ('of', 5),
                    the/Md/en: ('the', 3),
                    theory/Cc.s/en: ('theory', 4),
                    relativity/Cc.s/en: ('relativity', 6),
                    in/Tt/en: ('in', 7),
                    1905/C#/en: ('1905', 8)},
      'atom2token': {einstein/Cp.s/en: Einstein,
                     first/M/en: first,
                     published/Pd.sox.<f-----/en: published: published,
                     the/Md/en: the,
                     theory/Cc.s/en: theory,
                     of/Br.ma/en: of,
                     relativity/Cc.s/en: relativity,
                     in/Tt/en: in,
                     1905/C#/en: 1905},
      'spacy_sentence': Einstein first published the theory of relativity in 1905},),
 'inferred_edges': []}
```

At the top level we have `parses` and `inferred_edges`. `parses` is a list of parse information for each sentence identified in the parsed text, while `inferred_edges` contains all inferences that could be derived during the parse stage from the entire piece of text that was provided. Here this latter field is empty. In the section about coreference resolution, we will see how it can be populated.

Each parse dictionary (i.e. each item in `parses`, corresponding to one sentence), contains the following fields:

- `main_edge`: contains the hyperedge that directly corresponds to the sentence.
- `extra_edges`: contains additional edges derived from the sentence. Here it is empty, but we will see that it can be populated, for example, with lemma relationships.
- `failed`: indicates if the parse was considered to have failed.
- `text`: the text of the sentence that corresponds to this parse.
- `atom2word`: a dictionary of correspondences from each atom in the main_edge to a word in the sentence. The word is represented by a tuple, where the first element is the string of the word itself, while the second indicates the position of this word in the sentence.
- `atom2token`: a dictionary of correspondences from each atom in the main_edge to the spaCy token from which it was derived.
- `spacy_sentence`: the spaCy structure representing the sentence.

## Lemmas

When creating a parser, it is possible to require it to also produce lemma relationships. Lemmas are linguistic roots of words, for example the infinitive tense of a verb or the singular form of a noun. They are represented by hyperbase in hyperedges like this:

```
(lemma/J/. published/P/en publish/P/en)
```

The special conjunction `lemma/J/.` indicates a lemma specification, followed by the atom and its lemma form. Notice that only the main type is considered and other role information is removed, because these are not relevant to the lemma relationship and would reduce generality. Let us see the example above with lemmas enabled:

```pycon
>>> from hyperbase.parsers import create_parser
>>> parser = create_parser(lang='en', lemmas=True)
>>> parser.parse('Einstein first published the theory of relativity in 1905')
{'parses':
    ({'main_edge': ((first/M/en published/Pd.sox.<f-----/en) einstein/Cp.s/en (of/Br.ma/en (the/Md/en theory/Cc.s/en) relativity/Cc.s/en) (in/Tt/en 1905/C#/en)),
      'extra_edges': {(lemma/J/. theory/C/en theory/C/en),
                      (lemma/J/. einstein/C/en einstein/C/en),
                      (lemma/J/. relativity/C/en relativity/C/en),
                      (lemma/J/. 1905/C/en 1905/C/en),
                      (lemma/J/. first/M/en first/M/en),
                      (lemma/J/. published/P/en publish/P/en),
                      (lemma/J/. of/B/en of/B/en),
                      (lemma/J/. the/M/en the/M/en),
                      (lemma/J/. in/T/en in/T/en)},
      'failed': False,
      'text': 'Einstein first published the theory of relativity in 1905',
      ...},),
 'inferred_edges': []}
```

## Parser-level coreference resolution and inference of gender, number and animacy

Consider the sentence:

```
"Alice says that she likes her dog."
```

Parser-level coreference resolution identifies that the pronouns "she" and "her" in the above sentence refer to "Alice". It then extends the parser_results with the `resolved_corefs` field, containing a hyperedge where such indirect references are made explicit:

```
(says/Pd.sr alice/C (that/T (likes/P.so alice/C (poss/Bp.am/. alice/C dog/C))))
```

Notice that the special builder `poss/Bp.am`, meant to indicate a general possessive construct, is employed to represent "her dog" explicitly as `(poss/Bp.am/. alice/C dog/C)`.

The correspondences of the pronouns "her" and "she" to "Alice" are also used to infer gender, number and animacy. The "inferred_edges" field in the parser results is populated with the following hyperedges:

```
(gender/P/. alice/Cp.s/en female),
(number/P/. alice/Cp.s/en singular),
(animacy/P/. alice/Cp.s/en animate)
```

To give the complete example:

```pycon
>>> parser = create_parser(lang='en', corefs=True)
>>> parser.parse('Alice says that she likes her dog.')
{'parses':
    ({'main_edge': (says/Pd.sr.|f--3s-/en alice/Cp.s/en (that/T/en (likes/P.so.|f--3s-/en she/Ci/en (her/Mp/en dog/Cc.s/en)))),
      ...
      'resolved_corefs': (says/Pd.sr.|f--3s-/en alice/Cp.s/en (that/T/en (likes/P.so.|f--3s-/en alice/Cp.s/en (poss/Bp.am/. alice/Cp.s/en dog/Cc.s/en))))},),
 'inferred_edges': [(gender/P/. alice/Cp.s/en female),
                    (number/P/. alice/Cp.s/en singular),
                    (animacy/P/. alice/Cp.s/en animate)]}
```
