==================
Parsing a sentence
==================

Transforming a sentence in natural language into an hyperedge is the most fundamental and quintessential task one can perform with hyperbase.

We start by creating a parser, in this case for the English language:

::

   from hyperbase.parsers import *
   parser = create_parser(lang='en')

Initializing the parser requires loading potentially large language models. This can take from a few seconds to a minute. Let's assign some text to a variable, in this case a simple sentence:

::

    text = "The Turing test, developed by Alan Turing in 1950, is a test of machine intelligence."


Finally, let us parse the text and print the result:

::

    parses = parser.parse(text)['parses']
    for parse in parses:
        edge = parse['main_edge']
        print(edge.to_str())

Calling the ``parse()`` method on a parser object returns a collection of parses -- one per sentence. Each parse object is a dictionary, where 'main_edge' contains the hyperedge that directly corresponds to the sentence. Hyperedge objects have a ``to_str()`` method that can be used to produce a string representation. The code above should cause a single hyperedge to be printed to the screen.

Experiment with changing the text that is passed to the parser object and see what happens.


Working with notebooks
======================

Jupyter notebooks are a particularly handy way to perform exploratory computation with Python, and very popular for scientific applications. hyperbase is no exception. The notebook corresponding to this tutorial can be found here:

https://github.com/hyperbase/hyperbase/blob/master/notebooks/parser.ipynb

Notice how to import the utility functions that exist specifically for working with notebooks:

::

    from hyperbase.notebook import *

The ``show()`` function allows one to render hyperedges in a nicer way. In the example above, we could replace the ``print()`` call with ``show(edge)``, and obtain something like this:

.. raw:: html

    <span style="color:#a65628"><span style="font-weight:bold;font-size:14pt;">(</span><span style="font-size:14pt;"><span style="font-weight:bold;color:#a65628">is</span><span style="color:#7F7F6F;font-size:8pt">/Pd.sc.|f--3s-/en</span></span> <div style="margin-left:20px;color:#377eb8"><span style="font-weight:bold;font-size:13pt;">(</span><span style="font-size:13pt;"><span style="font-weight:bold;color:#377eb8">:</span><span style="color:#7F7F6F;font-size:8pt">/J/.</span></span> <div style="margin-left:20px;color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">(</span><span style="font-size:12pt;"><span style="font-weight:bold;color:#4daf4a">the</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span> <div style="margin-left:20px;color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">+</span><span style="color:#7F7F6F;font-size:8pt">/B.am/.</span></span> <span style="font-size:11pt;"><span style="color:#404040">turing</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span> <span style="font-size:11pt;"><span style="color:#404040">test</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">)</span></span></div></div> <div style="margin-left:20px;color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">(</span><span style="font-size:12pt;"><span style="font-weight:bold;color:#4daf4a">developed</span><span style="color:#7F7F6F;font-size:8pt">/P.ax.&lt;pf----/en</span></span> <div style="margin-left:20px;color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">by</span><span style="color:#7F7F6F;font-size:8pt">/T/en</span></span> <div style="margin-left:20px;color:#ff7f00"><span style="font-weight:bold;font-size:10pt;">(</span><span style="font-size:10pt;"><span style="font-weight:bold;color:#ff7f00">+</span><span style="color:#7F7F6F;font-size:8pt">/B.am/.</span></span> <span style="font-size:10pt;"><span style="color:#404040">alan</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span> <span style="font-size:10pt;"><span style="color:#404040">turing</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span><span style="color:#ff7f00"><span style="font-weight:bold;font-size:10pt;">)</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span></div></div> <div style="margin-left:20px;color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">in</span><span style="color:#7F7F6F;font-size:8pt">/Tt/en</span></span> <span style="font-size:11pt;"><span style="color:#404040">1950</span><span style="color:#7F7F6F;font-size:8pt">/C#/en</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">)</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:13pt;">)</span></span></div></div></div> <div style="margin-left:20px;color:#377eb8"><span style="font-weight:bold;font-size:13pt;">(</span><span style="font-size:13pt;"><span style="font-weight:bold;color:#377eb8">a</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span> <div style="margin-left:20px;color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">(</span><span style="font-size:12pt;"><span style="font-weight:bold;color:#4daf4a">of</span><span style="color:#7F7F6F;font-size:8pt">/Br.ma/en</span></span> <div style="margin-left:20px;font-size:12pt;"><span style="color:#404040">test</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></div> <div style="margin-left:20px;color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">+</span><span style="color:#7F7F6F;font-size:8pt">/B.am/.</span></span> <span style="font-size:11pt;"><span style="color:#404040">machine</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span> <span style="font-size:11pt;"><span style="color:#404040">intelligence</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:12pt;">)</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:13pt;">)</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:14pt;">)</span></span></div></div></div></span>
    <br /><br />

The ``show()`` function provides several visualization styles, and also the possibility of reducing visual clutter by only displaying the roots of the atoms. Refer to the `function signature <https://hyperbase.net/api.html#hyperbase.notebook.show>`_ for all the details.
