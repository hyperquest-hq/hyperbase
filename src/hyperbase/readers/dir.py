import os
import re

from hyperbase.readers.reader import Reader
from hyperbase.readers.txt import TxtReader


def build_sequence_name(path, name):
    seq_name = '|'.join((path, name))
    seq_name = seq_name.lower()
    seq_name = seq_name.replace('/', '|')
    seq_name = seq_name.replace(' ', '-')
    seq_name = re.sub('[^a-z0-9\_\-|]+', '', seq_name)
    return seq_name


class DirReader(Reader):
    def __init__(self, indir, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None,
                 infsrcs=False):
        super().__init__(hg=hg, sequence=sequence, lang=lang, corefs=corefs, parser=parser, parser_class=parser_class,
                         infsrcs=infsrcs)
        self.indir = indir
        self.sequences = []

    def run(self):
        for dirpath, _, filenames in os.walk(self.indir):
            path = dirpath[len(self.indir) + 1:]
            for filename in filenames:
                name, extension = os.path.splitext(filename)
                if extension == '.txt':
                    while extension != '':
                        name, extension = os.path.splitext(name)
                    sequence = build_sequence_name(path, name)
                    infile = os.path.join(dirpath, filename)
                    TxtReader(infile=infile, sequence=sequence, parser=self.parser, infsrcs=self.infsrcs).read()
