from collections import OrderedDict

from asciitree import LeftAligned
from termcolor import colored


def with_color(text, color, colors=True):
    if colors:
        return colored(text, color)
    else:
        return text


def token2str(token, colors=False):
    word = with_color(token.lower_.strip(), 'cyan', colors=colors)
    lemma = token.lemma_.strip()
    tag = with_color(token.tag_, 'green', colors=colors)
    dep = with_color(token.dep_, 'yellow', colors=colors)
    named_entity = token.ent_type_

    if named_entity != '':
        named_entity = with_color('{{{}}}'.format(named_entity),
                                  'magenta', colors=colors)

    return '{}/{}/{} ({}) {}'.format(word, lemma, tag, dep, named_entity)


def _token2label_tree(token, prefix='*', colors=True):
    children = [_token2label_tree(leaf, '<') for leaf in token.lefts] +\
               [_token2label_tree(leaf, '>') for leaf in token.rights]

    label = '{} {}'.format(with_color(prefix, 'red', colors=colors),
                           token2str(token))
    return label, OrderedDict(children)


def print_tree(token, colors=True):
    label, children = _token2label_tree(token, colors=colors)
    tr = LeftAligned()
    print(tr({label: children}))
