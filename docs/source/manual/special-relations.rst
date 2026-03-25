=================
Special relations
=================

Coreferences
============

Coreferences indicate hyperedges that refer to the same thing. They are specified in the hypergraph using hyperedges with the special connector ``coref/P/.``. For example::

   (coref/P/. turing/Cp.s (+/B/. alan/Cp.s turing/Cp.s))

Coreference pairs such as the above define sets of coreferences that point to the same thing. Naturally, they can have arbitrary sizes. It is useful to specify the hyperedge that acts as the preferred representation for the entire coreference set. An hyperedge can also be connected to its main coreference with hyperedges such as this one::

   (main_coref/P/. (of/B.ma city/Cc.s berlin/Cp.s) berlin/Cp.s)

In the above case, ``berlin/Cp.s`` is the main coreference for the coreference set that ``(of/B.ma city/Cc.s berlin/Cp.s)`` belongs to.


Taxonomies
==========

Taxonomies can be built using *type-of* relations between hyperedges, with the help of the special predicate ``type_of/P/.``. For example::

   (type_of/P/. (of/B.ma city/Cc.s berlin/Cp.s) city/Cc.s)


Lemmas
======

In informal and simple terms, *lemma* refers to the root of a word. Words and derived from lemma for example by verb conjugation, gender, number, grammatical case, etc. It can be useful to know that two atoms share the same lemma, e.g. to infer that two predicates refer to the same verb.

Lemma relations are stored in the hypergraph using the following hyperedge format::

   (lemma/P/. asked/Pd.so.<pf----/en ask/P/en)

The last parameter of the hyperedge is the lemma atom. Lemma atoms only have the main type, with no further specification (e.g. ``ask/P/en`` but not ``ask/Pd/en`` or ``ask/Pd.so.|pf----/en``). The intent is to keep an appropriate level of generality.

The parsers provided with hyperbase generate lemma relations by default.