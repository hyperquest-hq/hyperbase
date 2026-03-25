import json
import re

import progressbar

from hyperbase.readers.reader import Reader


def file_lines(filename):
    with open(filename, 'r') as f:
        for i, _ in enumerate(f, 1):
            pass
    return i


def title_parts(title):
    parts = re.split('\|| - | -- |^\[([^\]]*)\] | \[([^\]]*)\]$', title)
    parts = [part.strip() for part in parts if part]
    return parts


class RedditReader(Reader):
    def __init__(self, infile, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None,
                 infsrcs=False):
        super().__init__(hg=hg, sequence=sequence, lang=lang, corefs=corefs, parser=parser, parser_class=parser_class,
                         infsrcs=infsrcs)
        self.infile = infile

    def _parse_post(self, post):
        parts = title_parts(post['title'])

        title_edge = ['title/J/.reddit']
        for part in parts:
            parse_results = self.parser.parse_and_add(part, self.hg, sequence=self.sequence, infsrcs=self.infsrcs)

            for parse in parse_results['parses']:
                main_edge = parse['resolved_corefs']
                if main_edge:
                    title_edge.append(main_edge)

        if len(title_edge) > 1:
            # add title edge
            self.hg.add(title_edge)
            self.hg.set_attribute(title_edge, 'author', post['author'])
            self.hg.set_attribute(title_edge, 'url', post['url'])
            self.hg.set_attribute(title_edge, 'created', post['created'])

    def read(self):
        num_lines = sum(1 for line in open(self.infile, 'rt'))
        i = 0
        with progressbar.ProgressBar(max_value=num_lines) as bar:
            with open(self.infile, 'rt') as f:
                for line in f:
                    post = json.loads(line)
                    self._parse_post(post)
                    i += 1
                    bar.update(i)
