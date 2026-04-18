# Installation

Hyperbase requires Python >=3.10.

## Install with pip

```bash
pip install hyperbase
```

## Install with uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. To add hyperbase to your project:

```bash
uv add hyperbase
```

Or to install it in a standalone environment:

```bash
uv pip install hyperbase
```

## Install from source

Clone the repository and install:

```bash
git clone https://github.com/hyperbase/hyperbase.git
cd hyperbase
pip install .
```

Or using uv:

```bash
git clone https://github.com/hyperbase/hyperbase.git
cd hyperbase
uv sync
```

To run the tests from the project root:

```bash
pytest
```

Or using uv:

```bash
uv run pytest
```

## Parsers

Hyperbase uses a plugin architecture for parsers. The core package does not include any parser, it only specifies the abstract parser interface. Parsers are installed separately as Python packages that register themselves via entry points.

| Package | Plugin name | Description | License |
| ------- | ----------- | ----------- | ------- |
| `hyperbase-parser-ab` | `alphabeta` | AlphaBeta parser using spaCy | Open source (MIT) |
| `hyperbase-parser-gen` | `generative` | Multilingual generative parser based on fine-tuned transformer model | Proprietary |

AlphaBeta is the "classical" parser developed for Semantic Hypergraphs. It is based on spaCy and depends on its language models, that have to be installed to support a given language. It is released under the same permissive open source license as hyperbase (MIT).

Generative is the "modern" multilingual parser, which produces high-quality parses for many languages. It is based on the fine-tuning of a more powerful transformer model and requires a GPU to run with acceptable speed. We plan on making this parser available for researchers and under a commercial license otherwise. Contact us if you are a researcher and wish to have early access to this parser.

### Installing a parser

Install a parser with pip:

```bash
pip install hyperbase-parser-ab
```

Or with uv:

```bash
uv add hyperbase-parser-ab
```

### AlphaBeta language support: installing spaCy models

For example, for English language support:

```bash
python -m spacy download en_core_web_trf
```

Or with uv:

```bash
uv run python -m spacy download en_core_web_trf
```

Replace with the appropriate model from the table below.

| Language | Code | Model |
| -------- | ---- | ----- |
| Chinese | `zh` | `zh_core_news_trf` |
| English | `en` | `en_core_web_trf` |
| French | `fr` | `fr_dep_news_trf` |
| German | `de` | `de_dep_news_trf` |
| Italy | `it` | `it_core_news_lg` |
| Portuguese | `pt` | `pt_core_news_lg` |
| Spanish | `es` | `es_dep_news_trf` |

The table shows the languages that are currently configured. In principle, any language for which a [spaCy model](https://spacy.io/models/) is available can be supported. If you are interested in adding a language and can verify accuracy, please add a pull request or open an issue in the [plugin's repository](https://github.com/hyperquest-hq/hyperbase-parser-ab).

### Verifying installation

You can list all installed parsers with the CLI:

```bash
hyperbase parsers
```

```bash
uv run hyperbase parsers
```

### Using parsers

Once installed, parsers can be used from the interactive REPL:

```bash
hyperbase repl --parser alphabeta --lang en
```

```bash
uv run hyperbase repl --parser alphabeta --lang en
```

Or programmatically:

```python
from hyperbase import get_parser

parser = get_parser("alphabeta", lang="en")
results = parser.parse("The sky is blue.")
```
