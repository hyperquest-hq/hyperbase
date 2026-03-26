# Parsing a Sentence

Transforming a sentence in natural language into an hyperedge is the most fundamental and quintessential task one can perform with hyperbase.

We start by creating a parser, in this case for the English language:

```python
from hyperbase.parsers import *
parser = create_parser(lang='en')
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

## Working with notebooks

Jupyter notebooks are a particularly handy way to perform exploratory computation with Python, and very popular for scientific applications. hyperbase is no exception. The notebook corresponding to this tutorial can be found here:

<https://github.com/hyperbase/hyperbase/blob/master/notebooks/parser.ipynb>

Notice how to import the utility functions that exist specifically for working with notebooks:

```python
from hyperbase.notebook import *
```

The `show()` function allows one to render hyperedges in a nicer way. In the example above, we could replace the `print()` call with `show(edge)`, and obtain a colorful, indented visualization of the hyperedge structure.

The `show()` function provides several visualization styles, and also the possibility of reducing visual clutter by only displaying the roots of the atoms. Refer to the [function signature](https://hyperbase.net/manual/api.html) for all the details.
