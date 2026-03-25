import random

from hyperbase.cli import wrapper
from hyperbase.parsers import create_parser


def extract_sentences(args):
    parser = create_parser(lang=args.lang, parser_class=args.parser)
    sentences = []

    count = 0
    with open(args.infile, 'r') as infile, open(args.outfile, 'w') as outfile:
        for line in infile.readlines():
            paragraph = line.strip()
            if len(paragraph) > 0:
                parse_results = parser.parse(paragraph)
                for parse in parse_results['parses']:
                    sentences.append(parse['text'])
                    count += 1
                    if count % 100 == 0:
                        print('{} sentences found'.format(count))

    random.shuffle(sentences)

    with open(args.outfile, 'w') as outfile:
        for sentence in sentences:
            outfile.write('{}\n'.format(sentence))


if __name__ == '__main__':
    wrapper(extract_sentences, text='extract sentences')
