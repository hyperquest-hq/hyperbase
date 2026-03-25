from hyperbase import hedge
from hyperbase.cli import wrapper
from hyperbase.parsers import create_parser
from hyperbase.parsers import print_tree


def test_parser(args):
    parser = create_parser(lang=args.lang, parser_class=args.parser)

    total = 0
    wrong = 0

    sentence = None
    with open(args.infile) as f:
        for line in f:
            if sentence:
                total += 1
                correct_edge = hedge(line.strip())
                parser_output = parser.parse(sentence)
                parsed_sentence = parser_output['parses'][0]
                edge = parsed_sentence['main_edge']
                sent = parsed_sentence['spacy_sentence']
                if edge != correct_edge:
                    wrong += 1
                    print_tree(sent.root)
                    print('expected:')
                    print(correct_edge)
                    print('result:')
                    print(edge)
                sentence = None
            else:
                sentence = line.strip()

    print('%s wrong out of %s.' % (wrong, total))


if __name__ == '__main__':
    wrapper(test_parser, text='parser tests')
