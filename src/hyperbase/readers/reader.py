from hyperbase.parsers import create_parser, parser_lang


class Reader:
    def __init__(self, hg=None, sequence=None, lang=None, corefs=False, parser=None, parser_class=None, infsrcs=False):
        self.hg = hg
        self.sequence = sequence
        self.lang = lang
        self.infsrcs = infsrcs
        
        if parser_class:
            plang = parser_lang(parser_class)
            if lang:
                if lang != plang:
                    msg = 'specified language ({}) and parser language ({}) do not match'.format(lang, plang)
                    raise RuntimeError(msg)
            else:
                self.lang = plang

        if parser is None:
            self.parser = create_parser(lang=lang, parser_class=parser_class, lemmas=True, corefs=corefs)
        else:
            self.parser = parser

    def read(self):
        pass
