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

## Installing parsers

TODO
