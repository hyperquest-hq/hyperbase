import json

from hyperbase import hedge
from hyperbase.cli import wrapper
from hyperbase.parsers import create_parser


def generate_alpha_training_data(args):
    total_sentences = 0
    ignored_sentences = 0
    failed_parses = 0
    total_atoms = 0

    parser = create_parser(lang=args.lang, parser_class=args.parser)

    with open(args.infile, 'r') as infile, open(args.outfile, 'w') as outfile:
        for line in infile.readlines():
            case = json.loads(line)
            sentence = case['sentence']
            atoms = case['atoms']
            parse_results = parser.parse(sentence)
            parse = parse_results['parses'][0]
            spacy_sentence = parse['spacy_sentence']
            if case['ignore']:
                ignored_sentences += 1
            elif len(atoms) == len(spacy_sentence):
                total_sentences += 1
                total_atoms += len(atoms)

                for i in range(len(atoms)):
                    atom = atoms[i]
                    token = spacy_sentence[i]

                    word_before = ''
                    word_after = ''
                    pos_before = ''
                    pos_after = ''
                    tag_before = ''
                    tag_after = ''
                    dep_before = ''
                    dep_after = ''
                    punct_before = False
                    punct_after = False
                    if i > 0:
                        word_before = str(spacy_sentence[i - 1])
                        pos_before = spacy_sentence[i - 1].pos_
                        tag_before = spacy_sentence[i - 1].tag_
                        dep_before = spacy_sentence[i - 1].dep_
                        if spacy_sentence[i - 1].pos_ == 'PUNCT':
                            punct_before = True
                    if i < len(atoms) - 1:
                        word_after = str(spacy_sentence[i + 1])
                        pos_after = spacy_sentence[i + 1].pos_
                        tag_after = spacy_sentence[i + 1].tag_
                        dep_after = spacy_sentence[i + 1].dep_
                        if spacy_sentence[i + 1].pos_ == 'PUNCT':
                            punct_after = True

                    head = token.head
                    is_root = head is None
                    has_lefts = token.n_lefts > 0
                    has_rights = token.n_rights > 0
                    outfile.write(('{}' + '\t{}' * 25 + '\n').format(
                        hedge(atom).mtype(),
                        str(token),
                        token.pos_,
                        token.tag_,
                        token.dep_,
                        str(head) if head else '',
                        head.pos_ if head else '',
                        head.tag_ if head else '',
                        head.dep_ if head else '',
                        is_root,
                        has_lefts,
                        has_rights,
                        token.ent_type_,
                        token.shape_[:2],
                        word_before,
                        word_after,
                        punct_before,
                        punct_after,
                        pos_before,
                        pos_after,
                        tag_before,
                        tag_after,
                        dep_before,
                        dep_after,
                        case['correct'],
                        case['source']))
            else:
                failed_parses += 1
            print('sentences: {}; ignored: {}; failed: {}; atoms: {}'.format(
                total_sentences, ignored_sentences, failed_parses,
                total_atoms))
        print('done.')


if __name__ == '__main__':
    wrapper(
        generate_alpha_training_data, text='generate alpha training data')
