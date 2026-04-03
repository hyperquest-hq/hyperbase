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

parser = get_parser("alphabeta", language="en")
```

The keyword arguments are forwarded to the parser constructor. Each parser plugin defines its own parameters -- for example, `alphabeta` takes a `language` code, while `generative` accepts `model_path`, `device`, `max_length`, and others.

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

For texts with many sentences, `parse_text()` handles sentensization and batching automatically:

```python
results = parser.parse_text(
    "The sky is blue. Birds are singing.",
    batch_size=8,
    progress=True,  # shows a tqdm progress bar
)
for result in results:
    print(result.text, "->", result.edge)
```

Under the hood, `parse_text()` splits the text into sentences, groups them into batches, and calls `parse_batch()` on each batch. Parser plugins can override `parse_batch()` to exploit hardware parallelism (e.g. batched GPU inference).

### Reading and parsing sources

The `Parser` class integrates with the [readers](readers.md) module to parse text from files, URLs and Wikipedia articles in a single call:

```python
# Iterate over parse results block by block
for results in parser.read_source("article.txt"):
    for result in results:
        print(result.edge)

# Or write everything to a JSONL file
parser.read_source_to_jsonl("article.txt", "output.jsonl", progress=True)
```

Both methods accept an optional `reader` argument to force a specific reader instead of relying on auto-detection. See the [readers](readers.md) documentation for details.

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

This is what `read_source_to_jsonl()` uses internally -- each line in the output file is one `ParseResult` serialized as JSON.

## Quality checking

The `hyperbase.parsers.correctness` module provides functions to assess the quality of a parse result.

### Badness check

`badness_check()` runs a comprehensive quality check on a parsed edge, combining structural validation with token-to-atom matching:

```python
from hyperbase.parsers.correctness import badness_check

errors = badness_check(result.edge, result.tokens)
if errors:
    for key, error_list in errors.items():
        for code, message, severity in error_list:
            print(f"[{code}] {message} (severity: {severity})")
else:
    print("No errors found.")
```

The function returns a dictionary mapping edge fragments (or the string `'token-matching'`) to lists of `(code, message, severity)` tuples. An empty dictionary means no errors were found.

The checks include:

- **Structural correctness** -- validates the hyperedge against the SH specification (via `Hyperedge.check_correctness()`).
- **Argument role validation** -- checks that argument roles are drawn from the valid set (`m`, `s`, `p`, `a`, `o`, `i`, `x`, `t`, `j`, `r`, `c`) and that roles like `s`, `p`, `o` are not duplicated.
- **Junction consistency** -- verifies that junction arguments are consistently typed (all relations or all concepts).
- **Token matching** -- ensures that every token in the original sentence maps to an atom root in the edge, and vice versa. Handles multi-token atoms, contractions and other non-trivial correspondences.

### Structural quality only

For a lighter check that skips token matching:

```python
from hyperbase.parsers.correctness import check_structural_quality

errors = check_structural_quality(result.edge)
```

## CLI

### Listing parsers

```bash
hyperbase parsers
```

Shows all installed parser plugins and their entry point values.

### Interactive REPL

The REPL lets you parse sentences interactively:

```bash
hyperbase repl --parser alphabeta --language en
```

Inside the REPL, type a sentence to parse it. Use `/help` to see available commands, `/settings` to view current configuration, and `/set` to change settings on the fly (e.g. `/set parser generative`). The REPL caches parser instances, so switching between parsers is fast after the first load.

### Reading and parsing files

```bash
# Parse a file to JSONL
hyperbase read article.txt -o output.jsonl --parser alphabeta --language en

# Parse a Wikipedia article
hyperbase read https://en.wikipedia.org/wiki/Hypergraph -o output.jsonl
```

See the [readers](readers.md) documentation for the full set of `hyperbase read` options.

## Custom parsers

To create a custom parser, subclass `Parser` and implement two methods:

- `sentensize(text)` -- split a text string into a list of sentences.
- `parse_sentence(sentence)` -- parse a single sentence and return a list of `ParseResult` objects.

Optionally, override `parse_batch(sentences)` if your parser can process multiple sentences more efficiently in a single call.

```python
from hyperbase.parsers import Parser, ParseResult
from hyperbase.hyperedge import hedge

class MyParser(Parser):
    def sentensize(self, text):
        # simple sentence splitting
        return [s.strip() for s in text.split('.') if s.strip()]

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
