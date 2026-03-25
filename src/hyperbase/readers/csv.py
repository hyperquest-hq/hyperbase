import csv
import re
import sys

import progressbar

from hyperbase.readers.reader import Reader


def file_lines(filename):
    with open(filename, 'r') as f:
        for i, _ in enumerate(f, 1):
            pass
    return i


def text_parts(title):
    parts = re.split('\|| - | -- |^\[([^\]]*)\] | \[([^\]]*)\]$', title)
    parts = [part.strip() for part in parts if part]
    return parts


class CsvReader(Reader):
    def __init__(self, infile, column, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None,
                 infsrcs=False):
        super().__init__(hg=hg, sequence=sequence, lang=lang, corefs=corefs, parser=parser, parser_class=parser_class,
                         infsrcs=infsrcs)
        self.infile = infile
        self.column = column
        csv.field_size_limit(sys.maxsize)

    def _parse_row(self, row):
        try:
            parts = text_parts(row[self.column])
            for part in parts:
                self.parser.parse_and_add(part, self.hg, sequence=self.sequence, infsrcs=self.infsrcs)
        except TypeError as e:
            print(e)

    def read(self):
        lines = file_lines(self.infile) - 1
        i = 0
        with progressbar.ProgressBar(max_value=lines) as bar:
            with open(self.infile, 'r') as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    self._parse_row(row)
                    i += 1
                    bar.update(i)
