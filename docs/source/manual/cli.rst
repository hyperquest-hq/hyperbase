======================
Command-line interface
======================

hyperbase provides a command-line interface that can be used to execute a variety of tasks. You can access it either by using python to run the hyperbase root module as a script::

   python -m hyperbase ...

or using the provided command::

   hyperbase ...

All cases below work with both.

Here's an overview of the interface::

   usage: hyperbase [-h] [--col COL] [--corefs] [--hg HG]
                     [--indir INDIR] [--infile INFILE] [--lang LANG]
                     [--outfile OUTFILE] [--parser PARSER]
                     [--sequence SEQUENCE] [--url URL]
                     command

   positional arguments:
     command               command to execute

   optional arguments:
     -h, --help            show this help message and exit
     --col                 table column
     --corefs              perform coreference resolution
     --hg HG               hypergraph db
     --indir INDIR         input directory
     --infile INFILE       input file
     --lang LANG           language
     --outfile OUTFILE     output file
     --parser PARSER       parser
     --sequence SEQUENCE   sequence name
     --url URL             url

The only obligatory argument, command, is used to specify the task to perform. Each command uses a subset of the optional arguments. Presented below are the details for each command.

Commands
========

create
------

Creates an empty hypergraph database::

   hyperbase --hg <hypergraph_database> create


export
------

Exports a hypergraph database to a JSON file::

   hyperbase --hg <hypergraph_database> --outfile <json_file> export

import
------

Imports a hypergraph database from a JSON file::

   hyperbase --hg <hypergraph_database> --infile <json_file> import

txt
---

Takes a text file as input and converts each one of its sentences to hyperedges, adding them to the hypergraph.

This is a very simple but also useful, general-purpose reader/parser.

wikipedia
---------

Takes a wikipedia URL as input, extracts the contents and converts each one of its sentences to hyperedges, adding them to the hypergraph.

reddit
------

Takes a Reddit JSON corpus as input and converts each one of thread titles, and optionally thread comments to hyperedges, adding them to the hypergraph. Titles and comments are attributed to authors.

taxonomy
--------

Derives a taxonomy from concepts defined with builders of modifiers. For example, ``(of/Br.ma founder/Cc.s psychoanalysis/Cc.s)`` is a type of ``founder/Cc.s``, so the following hyperedge is added::

   (type_of/P/. (of/Br.ma founder/Cc.s psychoanalysis/Cc.s) founder/Cc.s)

Or, if we consider modifier-defined concepts such as ``(black/Ma cat/Cc.s)``::

   (type_of/P/. (black/Ma cat/Cc.s) cat/Cc.s)

names
-----

Performs `coreference resolution <https://hyperbase.net/reference/special-relations.html#coreferences>`_ for compound proper name concepts, for example detecting that "Barack Obama" and "Obama" refer to the same person but "Michelle Obama" refers to someone else).

onto
----

**Depends on**: taxonomy

Performs `coreference resolution <https://hyperbase.net/reference/special-relations.html#coreferences>`_ based on probabilistic reasoning over taxonomies. For example, detecting that "United States" and "United States of America" refer to the same entity.

actors
------

**Depends on**: coreference resolution

We define actors as specific entities that are capable of acting in some sense. This simple command identifies hyperedges corresponding to actor by applying the following criteria:

1. The hyperedge or one of its coreferences appears at least two times as the subject of a declarative relation
2. The hyperedge is of type concept and subtype proper concept
3. If coreferences are used, the hyperedge is the main coreference

This command transverses the entire hypergraph to identify actors, and then adds hyperedges like the following::

   (actor/P/. mary/Cp.s/en)

The above simply means that ``mary/Cp.s/en`` was identified as an actor.

claims
------

**Depends on**: coreference resolution

Identifies hyperedges that represent a claim. Claims are sentences such as: "North Korea says it's not afraid of US military strike". The claim is that "North Korea is not afraid of US military strike" and the author of the claim is "North Korea".

More specifically, claims are detected according to the following criteria:

1. Hyperedge is a relation with predicate of type ``Pd``.
2. The deep predicate atom of the predicate hyperedge has a lemma belonging to a predetermined lists of verb lemmas that denote a claim (e.g.: "say", "claim").
3. The hyperedge has a subject and a clausal complement. The first is used to identify the actor making the claim, the second the claim itself.

Claim relations follow the format::

   (claim/P/. *actor* *claim* *edge*)

Furthermore, simple anaphora resolution on the claim is performed (e.g. in "Pink Panther says that she loves pink.", the hyperedge for "she" is replaced with the hyperedge for "Pink Panther" in the claim). In these cases, pronouns are used to guess gender or nature of actors. Actors can be classified as female::

   (female/P/. *actor*)

Or as a group::

   (group/P/. *actor*)

Or as male::

   (male/P/. *actor*)

Or as non-human::

   (non-human/P/. *actor*)

conflicts
---------

**Depends on**: coreference resolution

Identifies hyperedges that represent a conflict. Conflicts are sentences such as: "Germany warns Russia against military engagement in Syria". The source of the expression of conflict here is "Germany", the target is "Russia" and the topic is "military engagement in Syria".

More specifically, claims are detected according to the following criteria:

1. Hyperedge is a relation with predicate of type ``Pd``.
2. The deep predicate atom of the predicate hyperedge has a lemma belonging to a predetermined lists of verb lemmas that denote an expression of conflict (e.g.: "warn", "kill").
3. The hyperedge has a subject and an object. The first is used to identify the actor originating the expression of conflict and the second the actor which is the target of this expression.
4. [optional] Beyond subject and object, if any specifier arguments are present, and their trigger atoms belong to a predetermined list (e.g. "over", "against"), then topics of conflict are extracted from these specifiers.

Conflict relations follow the format::

   (conflict/P/. *actor_orig* *actor_targ* *edge*)

These conflict relations are connected to their topics by further relations with the format::

   (conflict-topic/P/. *actor_orig* *actor_targ* *concept* *edge*)