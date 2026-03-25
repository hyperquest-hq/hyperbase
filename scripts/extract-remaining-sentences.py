import json
import random
from collections import Counter
from collections import defaultdict
from os import listdir
from os.path import isfile
from os.path import join

from hyperbase.cli import wrapper


class SentenceExtractor(object):
    def __init__(self):
        self.sentences = set()
        self.input_files = None

    def load_sentences(self, file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f.readlines():
                    case = json.loads(line)
                    self.sentences.add(case['sentence'])
        except FileNotFoundError:
            pass
        return self.sentences

    def _open_input_files(self, indir):
        self.input_files = {}

        file_names = [f for f in listdir(indir) if isfile(join(indir, f))]

        for file_name in file_names:
            name = file_name.split('.')[0]
            self.input_files[name] = open(join(indir, file_name), 'r')

    def _close_input_files(self):
        for name in self.input_files:
            self.input_files[name].close()

    def _sentences(self):
        while True:
            for name in self.input_files:
                f = self.input_files[name]
                yield f.readline(), name

    def extract(self, indir, infile, outdir):
        self._open_input_files(indir)

        self.load_sentences(infile)

        sources = Counter()
        sentences_by_source = defaultdict(list)
        remaining = 0
        empty = 0
        for sentence, source in self._sentences():
            sentence = sentence.strip()
            if len(sentence) > 0:
                empty = 0
                if sentence not in self.sentences:
                    remaining += 1
                    source_name = source[:-1]
                    sources[source_name] += 1
                    sentences_by_source[source_name].append(sentence)
            else:
                empty += 1
                if empty > len(self.input_files):
                    break

        self._close_input_files()

        # write files per source
        for source in sentences_by_source:
            sentences = sentences_by_source[source]
            random.shuffle(sentences)
            with open(join(outdir, '{}.csv'.format(source)), 'w') as f:
                for sentence in sentences:
                    f.write('{}\n'.format(sentence))

        print('existing: {}; remaining: {}'.format(
            len(self.sentences), remaining))
        print(sources)


def extract_remaining_sentences(args):
    SentenceExtractor().extract(args.indir, args.infile, args.outdir)


if __name__ == '__main__':
    wrapper(
        extract_remaining_sentences, text='extract remaining sentences')
