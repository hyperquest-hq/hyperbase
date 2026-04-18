# Readers

The `hyperbase.readers` module provides a way to read and parse text from various sources directly into Semantic Hypergraphs. A reader handles the extraction and segmentation of text into paragraph-sized blocks, which can then be fed to a parser. Hyperbase ships with three built-in readers -- plain text files, URLs and Wikipedia articles -- and provides a registration mechanism for custom readers.

## Reading and parsing sources

The preferred way to read and parse a source is through the `Parser` methods `parse_source()` and `parse_source_to_jsonl()`. These handle reader selection automatically, so you only need a parser instance:

```python
from hyperbase import get_parser

parser = get_parser("generative")

# Iterate over parse results block by block
for results in parser.parse_source("article.txt"):
    for result in results:
        print(result.edge)

# Or write everything to a JSONL file in one call
parser.parse_source_to_jsonl("article.txt", "output.jsonl", progress=True)
```

Both methods accept an optional `reader` argument to force a specific reader instead of auto-detection:

```python
# Force the generic URL reader on a Wikipedia link
for results in parser.parse_source(
    "https://en.wikipedia.org/wiki/Hypergraph", reader="url"
):
    ...
```

### Extracting raw text (no parsing)

To extract text blocks without parsing, use a reader directly via `get_reader()` (available from `hyperbase.readers`):

```python
from hyperbase.readers import get_reader

reader = get_reader("article.txt")

# Iterate over text blocks
for block in reader.read("article.txt"):
    print(block)

# Or write blocks to a plain text file
reader.read_to_text("article.txt", "output.txt", progress=True)
```

When a named reader is given, the source is not required to obtain the reader instance:

```python
reader = get_reader(reader="wikipedia")
```

Either `source` or a named `reader` must be provided -- calling `get_reader()` with neither raises a `ValueError`.

## CLI

The `hyperbase read` command provides a convenient way to read and parse sources from the command line:

```bash
# Parse a local file to JSONL
hyperbase read article.txt -o output.jsonl

# Extract raw text blocks (no parsing)
hyperbase read article.txt -o output.txt

# Parse a Wikipedia article
hyperbase read https://en.wikipedia.org/wiki/Hypergraph -o output.jsonl

# Specify reader and parser explicitly
hyperbase read source.txt -o output.jsonl --reader plain_text --parser alphabeta --lang en
```

## Source information

Readers attach metadata to each `ParseResult` through the `source_info()` method. When parsing through a reader (via `parse_source()` or `parse_source_to_jsonl()`), the `source` field of each `ParseResult` is automatically populated with this metadata:

```python
for results in parser.parse_source("article.txt"):
    for result in results:
        print(result.source)
        # {"source_type": "txt", "source": "article.txt"}
```

Each built-in reader provides the following source metadata:

| Reader | Fields |
| ------ | ------ |
| `plain_text` | `source_type`, `source` (file name) |
| `url` | `source_type`, `source` (URL), `title` (page title, if available) |
| `wikipedia` | `source_type`, `source` (URL), `title` (article title) |

Custom readers can override `source_info(source)` to provide their own metadata.

## Built-in readers

### `plain_text`

Reads local text files. Accepts any source that is a valid file path. The text is split into paragraph-sized blocks: if blank lines are found, they are used as paragraph separators; otherwise each line becomes its own block.

### `url`

Reads web pages via HTTP/HTTPS. Uses [trafilatura](https://trafilatura.readthedocs.io/) to extract the main text content from the HTML, stripping navigation, ads and other boilerplate.

### `wikipedia`

Reads Wikipedia articles directly from the MediaWiki API. Accepts any URL matching `*.wikipedia.org/wiki/*`. It parses the wikicode markup to extract clean text, organized by section. Boilerplate sections (e.g. "References", "See also", "External links") are automatically discarded based on the article language. The Wikipedia reader declares `url` as `more_general`, so it takes priority over the URL reader when the source is a Wikipedia link.

## Auto-detection

When a reader is not explicitly specified, all registered readers are checked and those whose `accepts()` method returns `True` for the given source are collected. If more than one reader matches, the `more_general` mechanism is used to pick the most specific one. For example, a Wikipedia URL is accepted by both the `url` and `wikipedia` readers, but because `WikipediaReader` declares `more_general = ['url']`, the Wikipedia reader is selected.

## Custom readers

You can create and register your own readers. A custom reader must subclass `Reader` and implement two methods:

- `accepts(source)` -- a static method that returns `True` if the reader can handle the given source string.
- `read(source)` -- a generator that yields text blocks from the source.

Optionally, you can implement `block_count(source)` to return the total number of blocks (enabling progress bars), `source_info(source)` to provide metadata for parse results, and set the `more_general` class attribute to declare that this reader is more specific than others.

Here is an example:

```python
from hyperbase.readers import Reader, register_reader

class RSSReader(Reader):
    more_general = ("url",)  # take priority over the generic URL reader

    @staticmethod
    def accepts(source: str) -> bool:
        return source.endswith(".rss") or source.endswith("/feed")

    def read(self, source: str):
        import feedparser
        feed = feedparser.parse(source)
        for entry in feed.entries:
            # yield the text content of each entry as a block
            yield entry.get("summary", "")

    def source_info(self, source: str):
        return {"source_type": "rss", "source": source}

register_reader("rss", RSSReader)
```

After registration, the new reader is automatically considered during auto-detection. It can also be requested by name:

```python
parser.parse_source_to_jsonl("https://example.com/feed", "feed.jsonl", reader="rss")
```

## Listing registered readers

To see all currently registered readers:

```python
from hyperbase.readers import list_readers

for name, cls in list_readers().items():
    print(f"{name}: {cls.__name__}")
```
