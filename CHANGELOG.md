# Changelog

## [0.10.1] - work in progress

### Added

- readers provide source information.

### Changed

### Removed

## [0.10.0] - 11-04-2026

### Added

- `[]` pattern notation for specifying sequences of arguments.
- EdgeType and ArgRole enums.
- safety cap for match (`_MAX_ARGROLE_ITEMS=10`) against pathological edge arities.
- caching of computed `Hyperedge`/`Atom` properties.
- `parse_to_jsonl` method on `Parser`.
- unified parameter interface for parsers.
- method `Parser.accepted_params`.
- maximum depth protection for parsers.
- repl api for parsers.

### Changed

- multiple patterns functions are now `Hyperedge`/`Atom` methods: `is_wildcard`, `is_pattern`, `is_fun_pattern`, `is_variable`, `contains_variable`, `variable_name`.
- `hyperbase.py` now delegating to smaller modules with well-defined concerns: `builders.py`, `correctness.py`, `transforms.py`, `patterns.checks.py` and `patterns.matcher.py`.
- replaced `itertools.permutations` with constraint-propagated backtracking in argrole matcher.
- `parse_text` renamed to `parse`; old iterator-based `parse` removed.
- `read_source` renamed to `parse_source`; `read_source_to_jsonl` renamed to `parse_source_to_jsonl`.
- renamed `sentensize` to `get_sentences`.
- hedge now uses an explicit stack instead of recursion (so that pathologically
    nested edge strings cannot exhaust Python's call stack).
- renamed parsers.correctness to parsers.badness.

### Removed

- `__add__` operator overloading in `Hyperedge`/`Atom`.

## [0.9.0] - 05-04-2026

### Added

- readers (txt, url, wikipedia).
- cli interface with repl, parsers, readers.
- hyperedge.Hyperedge.match function (calls parsers.match_pattern).
- ParseResults.
- HyperEdge.text.
- load_edges function.

### Changed

- added get_parser to main functions (at hyperbase root).
- improved documentation.
- hedge now accepts ParseResults and can recursively add Hyperedge.text strings.
- renamed function hyperedge.str2atom to str_to_atom.
- Hyperedge is not a frozen dataclasse, instead of inheriting from tuple.
- hedge now throws exceptions instead of returning None values.
- Hyperedge.contains always recursive, removed deep argument.
- simplified Hyperedge.simplify.
- Hyperedge.insert_argrole now private, renamed to Hyperedge._insert_argrole.
- Renamed Hyperedge.insert_edge_with_argrole to add_argument, pos optional (default to add at the end).
- Renamed Hyperedge.edges_with_argrole to arguments_with_role.
- Renamed Hyperedge.normalized to normalise.

### Removed

- function patterns.edge_matches_pattern.
- deprecated and obsolete methods from Hyperedge: is_atom, to_str, roots, insert_first_argument, connect, sequence, contains_atom_type, main_concepts, replace_main_concept, has_argroles.

## [0.8.0] - 26-03-2026 - hyperbase is the successor of graphbrain

### Added

- parser plugin foundation.
- more comprehensive Hyperedge.check_correctness.
- check parse correctness.
- type checking: full code coverage.

### Changed

- renamed library to hyperbase.
- trimmed down library to the essentials: hyperedge, patterns and parser foundations.
- converted documentation to Material for MkDocs.

### Removed

- hypergraph module, hypergraph database (memory module).
- alphabeta parser implementation.
- old scripts, examples, processors.
- ad hoc utils.
- cli.
- notebook utils.
- obsolete constants.

## [0.7.0] - 05-03-2026

### Added

- patterns.is_wildcard().
- Base class hypergraph.memory.keyvalue.KeyValue for key-value hypergraph databases, removing redundant code between LevelDB and SQLite.
- Tests for LevelDB (only the SQLite Hypergraph implementation was being directly tested).
- Hyperedge.is_unordered_pattern().
- Functional pattern: any.
- Parser-level inference of coreferences between proper nouns.
- Parser.parse_and_add() now adds token information to the main edge of a sentence: the attribute 'tokens' contains the list of tokens and 'tok_pos' a structure with the token position for each atom in the edge.
- Post-processing step improves parser.
- Hypergraph.get_attributes().

### Changed

- Entire project is now in pure Python
- Python >=3.10 now required.
- Hypergraph.search(), .match() and .count() now working with functional patterns and argument role matching.
- Fixed bug on match_pattern(), variables were not correctly matched when argument roles were specified past the first position in an atoms functional pattern.
- Simplified default systems connectors (breaks hypergraph DB backwards compatibility).
- max_text argument in parser.parse_and_add().
- Matches from patterns with repeated variables are collected in lists.

### Removed

- graphbrain.logic obsolete module.
- LevelDB backend

## [0.6.1] - 31-10-2022

### Changed

- Hyperedge.replace_argroles() .insert_argrole() and .add_argument() now works with functional patterns such as var.
- Fixed bug when matching patterns containing atoms functional pattern where no atom has argroles.

### Removed

- interactive_case_generator() from graphbrain.notebook.

## [0.6.0] - 27-10-2022

### Added

- Hyperedge.atom and .not_atom properties.
- Hyperedge.mtype() and .connector_mtype() methods.
- Hyperedge.t, .mt, .ct and .cmt type shortcut properties.
- Functional patterns: var, atoms, lemma.
- Moved all patterns functions to graphbrain.patterns.
- Hypergraph.text().
- Parser.parse_and_add().
- Parser.sentences().
- Hyperedge.normalise().
- New package graphbrain.readers, for text readers from various sources.
- New package graphbrain.processors, for miscellaneous processors.
- Processor class.

### Changed

- Coreference resolution now using the new spaCy experimental model.
- Now using spaCy transformer GPU models by default, can fallback to CPU model.
- Hyperedge.is_atom() deprecated.
- Improved Hyperedge.main_concepts().
- Hyperedge.atom() renamed to .inner_atom().
- Sequences keep track of their size, no need to specify position when adding edge to sequence.
- Improved wikipedia reader.
- Improved coreference resolution.
- LevelDB included by default again.
- Old package graphbrain.meaning renamed to graphbrain.utils.
- Hyperedge.argroles() now also works at relation/concept level.

### Removed

- graphbrain.patterns.normalize_edge().
- graphbrain.stats obsolete package.
- graphbrain.cognition obsolete package.
- graphbrain.op obsolete module.
- Hyperedge .predicate() and .predicate_atom().

## [0.5.0] - 28-07-2021

### Added

- SQLite3 hypergraph database backend.
- Hypergraph.add_with_attributes().
- import and export commands.
- Hypergraph context manager for batch writes (with hopen(hg_locator) as hg ...).

### Changed

- Main hypergraph database backend is now SQLite3.
- LevelDB backend becomes optional. (disabled by default)
- Neuralcoref becomes optional. (disabled by default)

### Removed

- Hypergraph.atom_count().
- Hypergraph.edge_count().
- Hypergraph.primary_atom_count().
- Hypergraph.primary_edge_count().
- info command.
- corefs_unidecode agent.

## [0.4.3] - 22-04-2021

### Changed

- Fixed AlphaBeta bug related to temporary atoms being removed too soon from atom2tokens.
- Hypergraph.add_sequence() converts sequence name directly to atom.
- Parser level coreference resolution (neuralcoref) disabled by default, requires dedicated build.

## [0.4.2] - 12-04-2021

### Changed

- Solving wheel compilation issue.

## [0.4.1] - 07-04-2021

### Changed

- Solving issue with inclusion of auxiliary data file in non-binary distributions.

## [0.4.0] - 07-04-2021

### Added

- Agents system.
- Conjunctions resolution agent.
- Number agent (singular/plural relations) and related meaning.number module.
- Wikipedia agent.
- Coreference resolution in the parser through local fork of neuralcoref.
- atom_gender(), atom_number(), atom_person(), atom_animacy() in parsers.
- Coreference inference: gender, number and animacy.
- Coreference inference:'X is Y' relationships.
- dir_parser agent (looks for text files in directory tree).
- Function meaning.concepts.has_common_or_proper_concept(edge).
- Function Hypergraph.add() now has optional 'count' parameter.
- Function Hypergraph.sequences().
- Function Hyperedge.replace_argroles().
- Function Hyperedge.insert_argrole().
- Function Hyperedge.add_argument().
- Function Hyperedge.all_atoms().
- Function Hyperedge.size().
- Function Hyperedge.predicate().
- Function Hyperedge.predicate_atom().
- Function Hyperedge.simplify().
- Function Hyperedge.connector_atom().
- Utility functions to show colored edges in the terminal.

### Changed

- Special characters in atoms are now percent-encoded.
- parse() now returns a dictionary that includes inferred edges.
- parse() now returns a dictionary of edges to text.
- New parser framework, improved English parser + scripts to help train and test new parsers.
- Hyperedge main type character codes become upercase (apple/C instead of apple/c).
- Conjunction hyperedge type, character code: "J" (e.g.: and/J).
- Modifier hyperedge type can now be applied to anything.
- Searching patterns can now include types, argument roles and other atom parts.
- Hypergraph.search_count() renamed to Hypergraph.count().
- corefs_names agent is simplified.
- corefs_onto agent is simplified.
- Tests now run with pytest instead of the deprecated './setup.py test'.
- Hyperedge.replace_atom() optional unique argument.

### Removed

- Meta-modifier hyperedge type.
- Auxiliary, subpredicate and dependency hyperedge types.
- Obsolete Hyperedge.nest() method.

## [0.3.2] - 10-02-2020

### Added

- simplify_role() on Atom objects produces an atom with only its simple type as role.

### Changed

- Lemmas are now based on atoms with simplified roles.
- Improved actors agent (more accurate identification of actors, English only for now).

## [0.3.1] - 03-02-2020

### Added

- German parser (experimental and incomplete).
- Documentation.
- Hyperedge sequences.

### Changed

- Improved hyperedge visualization in notebooks.
- Agents receive language and sequence.
- txt_parser agent creates a sequence.
- Refactored parsers code.
- Catching and logging exceptions during parse.
- Improved conflict agent.

## [0.3.0] - 28-09-2019

### Added

- Tests.
- Documentation.

### Changed

- Graphbrain is now beta (main APIs considered stable).
- LevelDB edge attributes encoded in JSON.
- Renamed hypergraph() to hgraph() and moved function to __jnit__.
- Fixed notebook examples.
- Moved Hypergraph.lemma_degrees() to meaning.lemmas.
- Argroles location is normalized (first position in both predicates and builders).
- In the parsers package, create_parser() was moved to __init__ and the factory module was removed.
- is_proper_concept() renamed to has_proper_concept() (meaning.concepts module).
- find_concept() renamed to strip_concept() (meaning.concepts module).
- Improved notebooks visualizations (show(), blocks(), vblocks()).

### Removed

- graphbrain.funs module.

## [0.2.2] - 13-09-2019

### Added

- txt_parser agent.
- MANIFEST.in to include VERSION file in distribution.

### Changed

- Fixing 'pip install graphbrain' on Linux/Windows.

## [0.2.1] - 04-09-2019

### Added

- claim_actors and corefs_dets agents.
- meaning.concepts module.

### Changed

- Fixed example.
- hypergraph.sum_degree() and .sum_deep_degree().
- Parser improvements.
- Agent corefs_atoms is now corefs_unidecode.
- Improved docs.

### Removed

- Obsolete 'work-in-progress' code.
- hg2json command.

## [0.2.0] - 04-08-2019

### Added

- Primary entities and deep degrees.
- Hyperedges have their own class, deriving from tuple.
- Atoms have a special class, deriving from Hyperedge.
- Restructuring of code files tree.
- Created agent system + first agents.

### Changed

- Parsers now have own package.

### Removed

- Old experimental code.

## [0.1.0] - 14-06-2019

### Added

- First release.
