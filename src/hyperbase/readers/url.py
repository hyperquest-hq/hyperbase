import progressbar
from trafilatura import fetch_url, extract, extract_metadata

from hyperbase import hedge
from hyperbase.readers.reader import Reader


class URLReader(Reader):
    def __init__(self, url, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None,
                 infsrcs=False, outfile=None):
        if sequence is None:
            sequence = url
        super().__init__(hg=hg, sequence=sequence, lang=lang, corefs=corefs, parser=parser, parser_class=parser_class,
                         infsrcs=infsrcs)
        self.url = url
        self.outfile = outfile

    def read(self):
        document = fetch_url(self.url)
        metadata = extract_metadata(document).as_dict()
        text = extract(document)

        content = {
            'title':  [line.strip() for line in metadata['title'].split('\n')],
            'description': [line.strip() for line in metadata['description'].split('\n')],
            'text': [line.strip() for line in text.split('\n')]
        }

        nlines = sum(len(lines) for lines in content.values())
        nedges = {}
        with progressbar.ProgressBar(max_value=nlines) as bar:
            i = 0
            for field, lines in content.items():
                for line in lines:
                    if self.outfile is not None:
                        with open(self.outfile, 'at') as f:
                            f.write(f'{line}\n')
                    try:
                        parse_result = self.parser.parse_and_add(line, self.hg, sequence=self.sequence,
                                                                 infsrcs=self.infsrcs)
                        for parse in parse_result['parses']:
                            edge = parse['main_edge']
                            if edge:
                                if field not in nedges:
                                    nedges[field] = 0
                                nedges[field] += 1
                                if field != 'text':
                                    self.hg.add(hedge([field, edge]))
                    except RuntimeError as e:
                        print(e)
                    i += 1
                    bar.update(i)

        for field, n in nedges.items():
            print('{}: {} edges added'.format(field, str(n)))
