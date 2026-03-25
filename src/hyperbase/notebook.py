from html import escape

from IPython.display import display, HTML

from hyperbase import hedge


TYPE_COLORS = {'C': '#268bd2',
               'M': '#dc322f',
               'B': '#859900',
               'P': '#cb4b16',
               'T': '#d33682',
               'J': '#b58900',
               'R': '#eee8d5',
               'S': '#6c71c4'}


def _edge2html_show(edge, style='indented', indent=False, close=True, close_html=''):
    ret_close_html = ''

    if indent:
        main_tag = 'div'
        margin = 'margin-left:20px;'
    else:
        main_tag = 'span'
        margin = ''

    et = edge.mtype()
    if et == 'R':
        color = '#303030'
    else:
        color = TYPE_COLORS[edge.mtype()]

    color_html = 'color:{}'.format(color)

    if edge.atom:
        html = '<span style="{}">{}</span>'.format(color_html, escape(str(edge.root())))

        if len(edge.parts()) > 1:
            escaped_codes = '/'.join(edge.parts()[1:])
            escaped_codes = escape(escaped_codes).strip()
            html = '{}<span style="color:#000000;font-weight:lighter">/{}</span>'.format(html, escaped_codes)
    else:
        arity = len(edge)
        contains_edges = any(not child.atom for child in edge)
        color_html = 'color:{}'.format(color)

        # render opening symbol
        html = '<span style="font-weight:bold">(</span>'

        close_html = '</{}>'.format(main_tag)

        # render edge children
        for i in range(arity):
            child = edge[i]

            child_indent = False
            # first edge (connector)?
            if i == 0:
                sep = ''
            # not connector
            else:
                # indent depending on style
                if style == 'indented':
                    # edges with only two items are rendered in one line
                    if arity > 2 and (child.not_atom or contains_edges):
                        child_indent = True

                sep = ' '

            if child.atom:
                child_html, _ = _edge2html_show(child, style=style, indent=child_indent)
            else:
                # Do not render closing html of children that are the last
                # edge in a hyperedge. Instead, let some higher-level edge
                # render it to avoid ugly multi-line staircases when closing
                # a sequence of edges.
                child_close = i < arity - 1

                child_html, child_cl_html = _edge2html_show(child, style=style, indent=child_indent, close=child_close)
                # accumulate close_html of child
                close_html = '{}{}'.format(child_cl_html, close_html)
            html = '{}{}{}'.format(html, sep, child_html)

        # if closing html should not be rendered at the end of this edge
        # representation, then return it to the parent
        if not close:
            ret_close_html = close_html
            close_html = ''

        # render close symbol
        html = '{}<span style="{}">'.format(html, color_html)
        html = '{}<span style="font-weight:bold">)</span></span>'.format(html)

    # render edge
    html = '<{} style="{}{}">{}{}'.format(main_tag, margin, color_html, html, close_html)

    return html, ret_close_html


def show(edge, style='indented'):
    """Displays a representation of the edge in the notebook.

    Keyword arguments:
    style -- render style ('indented', 'line')
    (default: 'indented')
    """
    edge = hedge(edge)
    html = _edge2html_show(edge, style=style)[0]
    display(HTML(html))


def _edge2html_vblocks(edge):
    tcolor = TYPE_COLORS[edge.mtype()]
    if edge.atom:
        html_atom = '<span style="color:#fdf6e3;font-weight:bold">{}</span>'.format(edge.root())
        parts = edge.parts()
        if len(parts) > 1:
            parts_str = '/'.join(edge.parts()[1:])
            html_parts = '<span style="color:#eee8d5;font-weight:lighter">/{}</span>'.format(parts_str)
            html_atom = ''.join((html_atom, html_parts))
        html = '<div style="padding:5px;background-color:{};border:2px solid #fdf6e3;border-radius:10px">{}'\
               '</div>'.format(tcolor, html_atom)
        return html
    elif len(edge) == 2 or all(subedge.atom for subedge in edge):
        conn_html = _edge2html_vblocks(edge[0])
        arg_htmls = ['<div style="display: table-cell;vertical-align: middle">{}</div>'.format(_edge2html_vblocks(arg))
                     for arg in edge[1:]]

        html = '<div style="display:table;border:2px solid #fdf6e3;'\
               'background-color:{};border-radius:10px;padding:3px">'\
               '<div style="display:table-row">'\
               '<div style="display: table-cell; vertical-align: middle;'\
               'background-color:{};padding-left:5px">{}</div>'\
               '<div style="display: table-cell; vertical-align: middle;'\
               'background-color:{};padding:5px">'\
               '<div style="display:table-row">{}</div></div>'\
               '</div></div>'.format(
                tcolor,
                tcolor,
                conn_html,
                tcolor,
                '<div style="width:5px"></div>'.join(arg_htmls))
        return html
    else:
        conn_html = _edge2html_vblocks(edge[0])
        arg_htmls = ['<div>{}</div>'.format(_edge2html_vblocks(arg)) for arg in edge[1:]]

        html = '<div style="display:table;border:2px solid #fdf6e3;'\
               'background-color:{};border-radius:10px;padding:3px">'\
               '<div style="display:table-row">'\
               '<div style="display: table-cell; vertical-align: top;'\
               'background-color:{};padding:5px">{}</div>'\
               '<div style="display: table-cell; vertical-align: top;'\
               'background-color:{};padding:5px">'\
               '<div style="display:table-row">{}</div></div>'\
               '</div></div>'.format(
                tcolor,
                tcolor,
                conn_html,
                tcolor,
                '<div style="height:5px"></div>'.join(arg_htmls))
        return html


def vblocks(edge, subtypes=False, argroles=True, namespaces=False):
    edge = hedge(edge)
    sedge = edge.simplify(subtypes=subtypes, argroles=argroles, namespaces=namespaces)
    html = _edge2html_vblocks(sedge)
    html = '<div style="background-color:#fcfcfc; padding:50px">{}</div>'.format(html)
    display(HTML(html))


def _edge2html_blocks(edge):
    tcolor = TYPE_COLORS[edge.mtype()]
    if edge.atom:
        html_atom = '<span style="color:#fdf6e3;font-weight:bold">{}</span>'.format(edge.root())
        parts = edge.parts()
        if len(parts) > 1:
            parts_str = '/'.join(edge.parts()[1:])
            html_parts = '<span style="color:#eee8d5;font-weight:lighter">/{}</span>'.format(parts_str)
            html_atom = ''.join((html_atom, html_parts))
        html = '<div style="padding:5px;background-color:{};'\
               'border:2px solid #fdf6e3;border-radius:10px;'\
               'text-align:center">{}</div>'.format(tcolor, html_atom)
        return html
    elif len(edge) > 2:
        conn_html = _edge2html_blocks(edge[0])
        arg_htmls = ['<div style="display: table-cell;vertical-align: middle">{}</div>'.format(_edge2html_blocks(arg))
                     for arg in edge[1:]]

        html = '<div style="display:table;border:2px solid #fdf6e3;'\
               'background-color:{};border-radius:10px;padding:3px">'\
               '<div style="display:table-row">'\
               '<div style="display: table-cell; vertical-align: middle;'\
               'background-color:{};padding-left:5px">{}</div>'\
               '<div style="display: table-cell; vertical-align: middle;'\
               'background-color:{};padding:5px">'\
               '<div style="display:table-row">{}</div></div>'\
               '</div></div>'.format(
                tcolor,
                tcolor,
                conn_html,
                tcolor,
                '<div style="width:5px"></div>'.join(arg_htmls))
        return html
    else:
        conn_html = _edge2html_blocks(edge[0])
        arg_htmls = ['<div style="display: table-row">{}</div>'.format(_edge2html_blocks(arg)) for arg in edge[1:]]

        html = '<div style="display:table;border:2px solid #fdf6e3;'\
               'background-color:{};border-radius:10px;padding:8px">'\
               '<div style="display:table-row">'\
               '<div style="display: table-row; vertical-align: top;'\
               'background-color:{};padding:5px">{}</div>'\
               '<div style="display: table-row; height:8px"></div>'\
               '<div style="display: table-row; vertical-align: top;'\
               'background-color:{};padding:5px">'\
               '<div style="display:table">{}</div></div>'\
               '</div></div>'.format(
                tcolor,
                tcolor,
                conn_html,
                tcolor,
                '<div style="height:5px"></div>'.join(arg_htmls))
        return html


def blocks(edge, subtypes=False, argroles=True, namespaces=False):
    edge = hedge(edge)
    sedge = edge.simplify(subtypes=subtypes, argroles=argroles, namespaces=namespaces)
    html = _edge2html_blocks(sedge)
    html = '<div style="background-color:#fcfcfc; padding:50px">{}</div>'.format(html)
    display(HTML(html))
