# Parsers

The `hyperbase.parsers` module provides the interface for parsing natural language into Semantic Hypergraphs. Hyperbase uses a plugin architecture: the core package defines an abstract `Parser` class and a discovery mechanism, while concrete parser implementations are installed as separate Python packages.

## Available parsers

| Package | Plugin name | Description |
| ------- | ----------- | ----------- |
| `hyperbase-parser-ab` | `alphabeta` | AlphaBeta parser, based on spaCy. Open source (MIT). |
| `hyperbase-parser-gen` | `generative` | Multilingual generative parser, based on a fine-tuned transformer model. Proprietary. |

**AlphaBeta** is the classical parser for Semantic Hypergraphs. It supports any language for which a spaCy model is available (see the [installation guide](../installation.md) for language-specific setup).

**Generative** is the modern parser that produces high-quality parses across many languages. It requires a GPU for acceptable speed. Contact us if you are a researcher and wish to have early access.

## Getting a parser

Parsers are obtained by name with `get_parser()`:

```python
from hyperbase import get_parser

parser = get_parser("alphabeta", lang="en")
```

The keyword arguments are forwarded to the parser constructor. Each parser plugin defines its own parameters -- for example, `alphabeta` takes a `lang` code, while `generative` accepts `model_path`, `device`, `max_length`, and others. Run `hyperbase repl --parser <name> --help` (or `hyperbase read --parser <name> --help`) to see the full set of CLI flags injected by the active plugin.

To see which parsers are installed:

```python
from hyperbase.parsers import list_parsers

for name, entry_point in list_parsers().items():
    print(f"{name}: {entry_point.value}")
```

Or from the command line:

```bash
hyperbase parsers
```

## Parsing text

### Single sentence

The `parse()` method takes a text string, splits it into sentences, and yields one `ParseResult` per sentence:

```python
for result in parser.parse("The sky is blue."):
    print(result.edge)
```

For a single sentence, you can also use `parse_sentence()` directly, which returns a list of `ParseResult` objects:

```python
results = parser.parse_sentence("The sky is blue.")
print(results[0].edge)
```

### Longer texts

For texts with many sentences, `parse()` handles splitting into sentences and batching automatically:

```python
results = parser.parse(
    "The sky is blue. Birds are singing.",
    batch_size=8,
    progress=True,  # shows a tqdm progress bar
)
for result in results:
    print(result.text, "->", result.edge)
```

Under the hood, `parse()` splits the text into sentences, groups them into batches, and calls `parse_batch()` on each batch. Parser plugins can override `parse_batch()` to exploit hardware parallelism (e.g. batched GPU inference).

### Writing results to JSONL

The `parse_to_jsonl()` method parses text and writes results directly to a JSONL file:

```python
parser.parse_to_jsonl("The sky is blue. Birds are singing.", "output.jsonl")
```

### Reading and parsing sources

The `Parser` class integrates with the [readers](readers.md) module to read a source and parse its text in a single call:

```python
# Iterate over parse results block by block
for results in parser.parse_source("article.txt"):
    for result in results:
        print(result.edge)

# Or write everything to a JSONL file
parser.parse_source_to_jsonl("article.txt", "output.jsonl", progress=True)
```

Both methods accept an optional `reader` argument to force a specific reader instead of relying on auto-detection. See the [readers](readers.md) documentation for details.

When parsing through a reader, each `ParseResult` has its `source` field populated with metadata from the reader (e.g. source type and file name). See the [readers](readers.md) documentation for the metadata a reader provides.

## ParseResult

Every parse operation returns `ParseResult` objects. This is a dataclass with the following fields:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `edge` | `Hyperedge` | The parsed Semantic Hypergraph edge. |
| `text` | `str` | The original sentence text. |
| `tokens` | `list[str]` | The tokens extracted from the sentence. |
| `tok_pos` | `Hyperedge` | A hyperedge mapping token positions to atoms. |
| `failed` | `bool` | `True` if the parse failed. Defaults to `False`. |
| `errors` | `list[str]` | Error messages, if any. |
| `extra` | `dict` | Parser-specific extra data (e.g. raw model output, candidates). |
| `source` | `dict` | Metadata about the source of the text. |

### Serialization

`ParseResult` can be serialized to and from JSON:

```python
# To JSON string
json_str = result.to_json()

# From JSON string
result = ParseResult.from_json(json_str)

# To/from dict
d = result.to_dict()
result = ParseResult.from_dict(d)
```

This is what `parse_source_to_jsonl()` uses internally -- each line in the output file is one `ParseResult` serialized as JSON.

## Quality checking

`hyperbase.parsers.correctness.check_parse_correctness(edge, tokens)` combines structural validation with token-matching validation against the original input tokens. It returns a dict mapping a context (the offending sub-edge, or a string naming the class of problem -- `"token-matching"`, `"alignment"`, `"symbol-coverage"`) to a list of `(error_type, message, severity)` tuples, where lower severities are worse (`0` for hard correctness failures, `1` for token-mismatch issues, `2` for argrole problems, `3` for junction issues). An empty result means no issues were found.

```python
from hyperbase import hedge
from hyperbase.parsers.correctness import check_parse_correctness

edge = hedge("(is/Pv.so (the/Md sky/Cc) blue/Ca)")
errors = check_parse_correctness(edge, ["the", "sky", "is", "blue"])
```

Passing `tok_pos` (the parallel tree naming, per atom, the token it was aligned to) and `text` turns on two further checks: the atom-to-token alignment, and connective symbols the parse dropped into a connector's gap.

Inside the REPL, set `check_badness` to `true` to display a badness panel after every parse:

```text
> /set check_badness true
```

### Extending the checks

A parser can add checks of its own by overriding `correctness_checks()`. Use this for what *your parser* cannot represent but hyperbase has no reason to forbid in general -- a model's vocabulary, a tokenizer invariant, a structure your architecture never emits. A rule that holds for every Semantic Hypergraph belongs in hyperbase instead.

A check takes a `CheckContext` and returns errors in the same shape `check_parse_correctness` does:

```python
from hyperbase.parsers import CheckContext, Parser
from hyperbase.parsers.utils import is_structural_atom

# This parser's classifier head was trained on these labels only, so an atom
# type outside the set is one it can never produce -- even though the wider
# Semantic Hypergraph notation allows it.
MY_ATOM_TYPES = frozenset({"Cc", "Cp", "Ca", "Cq", "Md", "Ma", "Pv", "Jx"})


def only_trained_types(ctx: CheckContext):
    return {
        atom: [(
            "atom-type-untrained",
            f"Atom '{atom}' has type '{atom.type()}', which is not in this "
            "parser's label set.",
            0,
        )]
        for atom in ctx.edge.all_atoms()
        if not is_structural_atom(atom) and atom.type() not in MY_ATOM_TYPES
    }


class MyParser(Parser):
    def correctness_checks(self):
        return [only_trained_types]
```

The checks run whenever `check_parse_correctness` is called with `parser=`, and what they report is merged into the same map:

```python
errors = check_parse_correctness(edge, tokens, parser=my_parser)
```

Three things to know:

- **Checks are additive only.** What a check returns is merged in, never used to remove or relax what the built-in checks found. A parser can make the gate stricter for its own output, never more lenient.
- **Each check is isolated.** One that raises, or returns something that is not a well-formed error map, is reported under the `"parser-checks"` key at severity `0` and the others still run. A broken check is reported rather than skipped quietly, so a gate never silently stops gating.
- **The parser has to be on hand.** `check_parse_correctness` only reaches these when the caller passes `parser=`. If your own pipeline assembles parses somewhere the `Parser` object is not available -- a worker subprocess, say, which should never have a parser pickled into it -- call `run_parser_checks(...)` there with module-level check functions instead.

## CLI

### Listing parsers

```bash
hyperbase parsers
```

Shows all installed parser plugins and their entry point values.

### Interactive REPL

The REPL lets you parse sentences interactively:

```bash
hyperbase repl --parser alphabeta --lang en
```

Inside the REPL, type a sentence to parse it. Use `/help` to see available commands, `/settings` to view current configuration, and `/set` to change settings on the fly (e.g. `/set parser generative`). The REPL caches parser instances, so switching between parsers is fast after the first load.

### Reading and parsing files

```bash
# Parse a file to JSONL
hyperbase read article.txt -o output.jsonl --parser alphabeta --lang en

# Extract raw text blocks, without parsing
hyperbase read article.txt -o output.txt
```

See the [readers](readers.md) documentation for the full set of `hyperbase read` options.

## REPL API for parsers

Parser plugins can extend the interactive REPL by overriding the `install_repl(session)` method. The session object provides:

- `register_command(name, help, handler)` -- add a slash command callable as `/name`.
- `register_setting(name, default, type_, description="")` -- expose an extra REPL-only setting changeable via `/set`.
- `register_pre_result_hook(hook)` -- run a hook after parsing but before the result panel is rendered.
- `register_post_result_hook(hook)` -- run a hook after the result panel is rendered.
- `register_stats_provider(provider)` -- supply extra `(label, value)` rows for the statistics table.

Hooks receive a `ReplContext` object (available from `hyperbase.parsers`).

## Custom parsers

To create a custom parser, subclass `Parser` and implement:

- `__init__(params)` -- constructor accepting a dictionary of parser parameters.
- `get_sentences(text)` -- split a text string into a list of sentences.
- `parse_sentence(sentence)` -- parse a single sentence and return a list of `ParseResult` objects.
- `accepted_params()` (classmethod) -- return a dict describing the parameters the parser accepts.

Optionally, override:

- `parse_batch(sentences)` -- if your parser can process multiple sentences more efficiently in a single call.
- `correctness_checks()` -- to add parser-specific checks to the parse gate (see [Extending the checks](#extending-the-checks)).
- `install_repl(session)` -- to extend the interactive REPL (see [REPL API for parsers](#repl-api-for-parsers)).
- `close()` -- to release subprocess pools, GPU contexts or open files. Must be idempotent.

```python
from hyperbase.parsers import Parser, ParseResult
from hyperbase.hyperedge import hedge

class MyParser(Parser):
    @classmethod
    def accepted_params(cls):
        return {
            "lang": {
                "type": str, "default": None,
                "description": "Language code.", "required": True,
            },
        }

    def __init__(self, params=None):
        super().__init__(params)
        self.lang = self.params["lang"]

    def get_sentences(self, text):
        # simple sentence splitting
        return [s.strip() for s in text.split(".") if s.strip()]

    def parse_sentence(self, sentence):
        edge = hedge(f"(says/P someone/C {sentence.split()[0]}/C)")
        return [ParseResult(
            edge=edge,
            text=sentence,
            tokens=sentence.split(),
            tok_pos=edge,
        )]
```

### Registering as a plugin

To make a parser discoverable by `get_parser()`, register it as an entry point in your package's `pyproject.toml`:

```toml
[project.entry-points."hyperbase.parsers"]
myparser = "my_package:MyParser"
```

After installation, `get_parser("myparser")` will instantiate your parser, and `hyperbase parsers` will list it alongside the built-in ones.
