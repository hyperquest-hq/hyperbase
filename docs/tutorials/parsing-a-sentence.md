# Parsing a Sentence

We start by creating a parser, in this case an AlphaBeta parser for the English language:

```python
from hyperbase import get_parser
parser = get_parser("alphabeta", lang="en")
```

Initializing the parser requires loading potentially large language models. This can take from a few seconds to a minute. Let's assign some text to a variable, in this case a simple sentence:

```python
text = "The Turing test, developed by Alan Turing in 1950, is a test of machine intelligence."
```

Finally, let us parse the text and print the result:

```python
results = parser.parse(text)
for result in results:
    print(result.edge)
```

Calling the `parse()` method on a parser object returns a list of `ParseResult` objects -- one per sentence. Each `ParseResult` contains an `edge` attribute with the hyperedge that directly corresponds to the sentence, along with the original `text`, `tokens`, and other metadata. Printing a hyperedge displays its SH notation string. The code above should cause a single hyperedge to be printed to the screen.

You can also inspect the original text and tokens:

```python
for result in results:
    print(result.text, "->", result.edge)
```

Experiment with changing the text that is passed to the parser object and see what happens.
