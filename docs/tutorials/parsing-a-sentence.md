# Parsing a Sentence

We start by creating a parser, in this case an AlphaBeta parser for the English language:

```python
from hyperbase import get_parser
parser = get_parser('alphabeta', lang='en')
```

Initializing the parser requires loading potentially large language models. This can take from a few seconds to a minute. Let's assign some text to a variable, in this case a simple sentence:

```python
text = "The Turing test, developed by Alan Turing in 1950, is a test of machine intelligence."
```

Finally, let us parse the text and print the result:

```python
parses = parser.parse(text)['parses']
for parse in parses:
    edge = parse['main_edge']
    print(edge.to_str())
```

Calling the `parse()` method on a parser object returns a collection of parses -- one per sentence. Each parse object is a dictionary, where 'main_edge' contains the hyperedge that directly corresponds to the sentence. Hyperedge objects have a `to_str()` method that can be used to produce a string representation. The code above should cause a single hyperedge to be printed to the screen.

Experiment with changing the text that is passed to the parser object and see what happens.
