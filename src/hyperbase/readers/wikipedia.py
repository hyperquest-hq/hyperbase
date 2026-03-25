from urllib.parse import urlparse

import progressbar
import mwparserfromhell
import requests

from hyperbase.readers.reader import Reader


IGNORE_SECTIONS = {'See also',
                   'Explanatory notes',
                   'References',
                   'Other sources',
                   'Further reading',
                   'External links',
                   'Sources',
                   'Selected bibliography',
                   'Awards and recognition',
                   'Selected works',
                   'Notes',
                   'Citations'}


def _url2title_and_lang(url):
    p = urlparse(url)

    netloc = p.netloc.split('.')
    if len(netloc) < 3 or 'wikipedia' not in netloc:
        raise RuntimeError('{} is not a valid wikipedia url.'.format(url))
    lang = netloc[0]

    path = [part for part in p.path.split('/') if part != '']
    if len(path) != 2 or path[0] != 'wiki':
        raise RuntimeError('{} is not a valid wikipedia url.'.format(url))
    title = path[1]

    return title, lang


def read_wikipedia(url):
    title, lang = _url2title_and_lang(url)
    params = {
        'action': 'query',
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'rvlimit': 1,
        'titles': title,
        'format': 'json',
        'formatversion': '2',
    }
    headers = {'User-Agent': 'hyperbase/1.0'}
    req = requests.get(f'https://{lang}.wikipedia.org/w/api.php',
                       headers=headers, params=params)
    res = req.json()
    revision = res['query']['pages'][0]['revisions'][0]
    text = revision['slots']['main']['content']
    return mwparserfromhell.parse(text)


class WikicodeTextExtractor:
    def __init__(self):
        self.cur_section = []
        self.sections = {'': self.cur_section}

    def _extract(self, wikicode):
        for node in wikicode.nodes:
            if type(node) == mwparserfromhell.nodes.heading.Heading:
                self.cur_section = []
                self._extract(node.title)
                title = ''.join(self.cur_section).strip()
                self.cur_section = []
                self.sections[title] = self.cur_section
            elif type(node) == mwparserfromhell.nodes.text.Text:
                self.cur_section.append(str(node))
            elif type(node) == mwparserfromhell.nodes.tag.Tag:
                if str(node.tag) not in {'ref', 'div'}:
                    _cur_section = self.cur_section
                    self.cur_section = []
                    self._extract(node.contents)
                    text = ''.join(self.cur_section).strip()
                    self.cur_section = _cur_section
                    self.cur_section.append(text)
            elif type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
                if 'File:' not in str(node.title):
                    _wikicode = node.title if node.text is None else node.text
                    _cur_section = self.cur_section
                    self.cur_section = []
                    self._extract(_wikicode)
                    text = ''.join(self.cur_section).strip()
                    self.cur_section = _cur_section
                    self.cur_section.append(text)

    def extract(self, wikicode):
        self._extract(wikicode)
        return {section: ''.join(texts).strip() for section, texts in self.sections.items()
                if section not in IGNORE_SECTIONS}


class WikipediaReader(Reader):
    def __init__(self, url, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None,
                 infsrcs=False):
        if sequence is None:
            sequence = url
        super().__init__(hg=hg, sequence=sequence, lang=lang, corefs=corefs, parser=parser, parser_class=parser_class,
                         infsrcs=infsrcs)
        self.url = url

    def read(self):
        wikicode = read_wikipedia(self.url)
        sections = WikicodeTextExtractor().extract(wikicode)

        nedges = 0
        with progressbar.ProgressBar(max_value=len(sections)) as bar:
            i = 0
            for section, text in sections.items():
                for line in text.split('\n'):
                    parse_result = self.parser.parse_and_add(line.strip(), self.hg, sequence=self.sequence,
                                                             infsrcs=self.infsrcs)
                    nedges += len([parse for parse in parse_result['parses'] if parse['main_edge']])
                i += 1
                bar.update(i)
        print(f'{nedges} edges added')
