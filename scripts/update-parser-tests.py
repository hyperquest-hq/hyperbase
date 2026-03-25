from hyperbase import *
from hyperbase.cli import wrapper
from hyperbase.parsers import *


def update_tests(args):
    parser = create_parser(lang=args.lang, parser_class=args.parser)

    total = 0

    sentence = None
    with open(args.infile) as f_in:
        with open(args.outfile, 'w') as f_out:
            for line in f_in:
                if sentence:
                    total += 1
                    parser_output = parser.parse(sentence)
                    parsed_sentence = parser_output[0]
                    edge = parsed_sentence['main_edge']
                    f_out.write('{}\n{}\n'.format(sentence, edge.to_str()))
                    sentence = None
                else:
                    sentence = line.strip()

    print('Total cases processed: {}.'.format(total))


if __name__ == '__main__':
    wrapper(update_tests, text='update tests')
