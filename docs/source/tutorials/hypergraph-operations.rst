=====================
Hypergraph operations
=====================

An hypergraph can also be seen as a type of database, that stores knowledge in the form of sets of hyperedges, and provides functions that make it easy to add and search for hyperedges in useful ways. We will see here how to perform some fundamental tasks with hypergraphs.

The notebook for this tutorial can be found here:

https://github.com/hyperbase/hyperbase/blob/master/notebooks/hypergraph.ipynb

Form here on, the following imports are assumed:

::

    from hyperbase import *
    from hyperbase.notebook import *
    from hyperbase.parsers import *

Create an hypergraph
====================

Creating an hypergraph is straightforward:

::

    hg = hgraph('example.db')

This assigns a hypergraph instance to ``hg``, which is physically stored as 'example.db'. If this hypergraph already exists, it is simply opened. If it does not exist, an empty one is created.

Parse sentence and add hyperedge to hypergraph
==============================================

Let's create a parser to obtain an hyperedge from a sentence, and then add it to the hypergraph:

::


    parser = create_parser(lang='en')
    text = "Mary is playing a very old violin."

    parses = parser.parse(text)
    for parse in parses['parses']:
        edge = parse['main_edge']
        hg.add(edge)

Notice that the ``add()`` function works recursively. We will see in the next subsection that not only the top hyperedge, but all of their children are added to the hypergraph.

Iterate through all edges
=========================

Hyoergraph objects include the function ``all()``, which returns an iterator that can be used to transverse all the hyperedges contained in the hypergraph. Let's see an example, in this case assuming that we are in a notebook environment:

::

    for edge in hg.all():
        show(edge, style='oneline')

.. raw:: html

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#377eb8">is</span><span style="color:#7F7F6F;font-size:8pt">/Mv.|f--3s-/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">playing</span><span style="color:#7F7F6F;font-size:8pt">/Pd.so.|pg----/en</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">mary</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span> <span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#377eb8">a</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span> <span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">violin</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#377eb8">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">violin</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#a65628">a</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span> <span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#4daf4a">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">violin</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#a65628">is</span><span style="color:#7F7F6F;font-size:8pt">/Mv.|f--3s-/en</span></span> <span style="font-size:11pt;"><span style="color:#404040">playing</span><span style="color:#7F7F6F;font-size:8pt">/Pd.so.|pg----/en</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#a65628">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span> <span style="font-size:11pt;"><span style="color:#404040">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">a</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">is</span><span style="color:#7F7F6F;font-size:8pt">/Mv.|f--3s-/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">mary</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">playing</span><span style="color:#7F7F6F;font-size:8pt">/Pd.so.|pg----/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span></div>

    <div class="output_subarea output_html rendered_html"><span style="font-size:11pt;"><span style="color:#000">violin</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span></div>

    <br /><br />

Search with patterns
====================

Hypergraph objects have a generic ``search()`` function, which returns iterators corresponding to sets of hyperedges that match a given pattern.

::

    edge_iterator = hg.search(pattern)

For example, with the current hypergraph, executing the below code would produce the shown result:

::

    # '...' at the end indicates that the edge may have an arbitrary number of extra entities
    for edge in hg.search('((is/Mv.|f--3s-/en playing/Pd.so.|pg----/en) ...)'):
        show(edge, style='oneline')

.. raw:: html

    <div class="output_subarea output_html rendered_html"><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#377eb8">is</span><span style="color:#7F7F6F;font-size:8pt">/Mv.|f--3s-/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">playing</span><span style="color:#7F7F6F;font-size:8pt">/Pd.so.|pg----/en</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">mary</span><span style="color:#7F7F6F;font-size:8pt">/Cp.s/en</span></span> <span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#377eb8">a</span><span style="color:#7F7F6F;font-size:8pt">/Md/en</span></span> <span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">(</span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">(</span><span style="font-size:11pt;"><span style="font-weight:bold;color:#984ea3">very</span><span style="color:#7F7F6F;font-size:8pt">/M/en</span></span> <span style="font-size:11pt;"><span style="font-weight:bold;color:#404040">old</span><span style="color:#7F7F6F;font-size:8pt">/Ma/en</span></span><span style="color:#984ea3"><span style="font-weight:bold;font-size:11pt;">)</span></span></span> <span style="font-size:11pt;"><span style="color:#404040">violin</span><span style="color:#7F7F6F;font-size:8pt">/Cc.s/en</span></span><span style="color:#4daf4a"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#377eb8"><span style="font-weight:bold;font-size:11pt;">)</span></span><span style="color:#a65628"><span style="font-weight:bold;font-size:11pt;">)</span></span></span></span></span></div>

    <br /><br />

For all the details about how to define search patterns, refer to the ``search()`` function documentation:

https://hyperbase.net/api.html#hyperbase.hypergraph.Hypergraph.search
