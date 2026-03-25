import json
from os import listdir
from os.path import isfile
from os.path import join

from termcolor import colored

from hyperbase.cli import wrapper
from hyperbase.colored import colored_atom
from hyperbase.colored import colored_edge
from hyperbase.colored import colored_type
from hyperbase.hyperedge import build_atom
from hyperbase.parsers import create_parser
from hyperbase.parsers import print_tree


# 'X' here means that the atom should be discarded
ATOM_TYPES = ['C', 'P', 'M', 'B', 'J', 'T', 'X']


class TrainingDataGenerator:
    def __init__(self, lang=None, parser_class=None):
        self.parser = create_parser(lang=lang, parser_class=parser_class)

        self.sentences = set()
        self.tokens = 0
        self.correct_edges = 0
        self.ignored = 0

        self.input_files = None

        self.sentence = None
        self.source = None
        self.atoms = None
        self.spacy_sentence = None
        self.token2atom = None

    def update_counts(self, case):
        self.tokens += len(case['atoms'])
        if case['ignore']:
            self.ignored += 1
        if case['correct']:
            self.correct_edges += 1

    def load_sentences(self, file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f.readlines():
                    case = json.loads(line)
                    self.sentences.add(case['sentence'])
                    self.update_counts(case)
        except FileNotFoundError:
            pass
        return self.sentences

    def print_status(self):
        print()
        print('{} {}'.format(colored('sentence .. > ', 'blue'),
                             colored(self.sentence, 'white')))
        tokens = ' '.join([colored_atom(atom) for atom in self.atoms])
        print('{} {}'.format(colored('tokens .... > ', 'blue'), tokens))
        print('{} {}'.format(colored('source .... > ', 'blue'), self.source))
        print()

    def print_counts(self):
        print()
        msg = '{} sentences; {} correct; {} ignored; {} tokens;'
        msg += ' {} tokens/sentence'
        tokens_sentence = 0
        if len(self.sentences) > 0:
            tokens_sentence = int(
                float(self.tokens) / float(len(self.sentences)))
        msg = msg.format(
            len(self.sentences),
            self.correct_edges,
            self.ignored,
            self.tokens,
            tokens_sentence)
        print(msg)
        print()

    def annotate_token(self, token):
        if token in self.parser.token2atom:
            suggested_type = self.parser.token2atom[token].atom.mtype()
        else:
            suggested_type = 'X'

        atom_type = None
        while atom_type is None:
            self.print_status()
            options = '/'.join([colored_type(atype) for atype in ATOM_TYPES])
            options += '/u'
            prompt_msg = '{} ({}) [{}] ? '.format(
                colored(str(token), 'white'),
                options,
                colored_type(suggested_type))
            atom_type = input(prompt_msg).upper()
            if atom_type == '':
                atom_type = suggested_type
            elif atom_type == 'U':
                self.atoms = self.atoms[:-1]
                return 'u'
            elif atom_type not in ATOM_TYPES:
                print(colored('Invalid type. Please try again.', 'red'))
                atom_type = None
        atom = build_atom(str(token), atom_type)
        if atom_type != 'X':
            self.token2atom[token] = atom
        return atom

    def edge_correct(self, edge, failed):
        correct = None
        while correct is None:
            print()
            print('Parsed edge:')
            print(colored_edge(edge))
            if failed:
                print(colored('Parse failed.', 'red'))
            yes = colored('y', 'green')
            no = colored('n', 'red')
            tree = colored('t', 'blue')
            debug = colored('d', 'yellow')
            default = no if failed else yes
            answer = input(
                'is edge parse correct ({}/{}/{}/{}) [{}] ? '.format(
                    yes, no, tree, debug, default))
            if answer in {'', 'y'}:
                correct = True
            elif answer == 'n':
                correct = False
            elif answer == 't':
                print_tree(self.spacy_sentence.root)
            elif answer == 'd':
                self.parser.debug = True
                # run parser again
                atom_seq = self.parser.build_atom_sequence(
                    self.spacy_sentence, self.token2atom)
                self.parser.parse_spacy_sentence(self.spacy_sentence, atom_seq)
                self.parser.debug = False
            else:
                print(colored('Invalid answer. Please try again.', 'red'))
        return correct

    def accept_ignore_restart(self):
        while True:
            print()
            accept = colored('a', 'green')
            reject = colored('i', 'red')
            restart = colored('r', 'yellow')
            answer = input(
                'accept, ignore or restart ({}/{}/{}) ? '.format(
                    accept, reject, restart))
            if answer in {'a', 'i', 'r'}:
                return answer
            else:
                print(colored('Invalid answer. Please try again.', 'red'))

    def annotate_sentence(self, sentence, source):
        self.sentence = sentence
        self.source = source
        self.atoms = []
        self.token2atom = {}
        parse_results = self.parser.parse(sentence)
        parse = parse_results['parses'][0]
        self.spacy_sentence = parse['spacy_sentence']
        pos = 0
        while pos < len(self.spacy_sentence):
            token = self.spacy_sentence[pos]
            result = self.annotate_token(token)
            if result == 'u':
                if pos > 0:
                    pos -= 1
            else:
                self.atoms.append(result)
                pos += 1

        self.parser.reset(sentence)
        atom_seq = self.parser.manual_atom_sequence(
            self.spacy_sentence, self.token2atom)
        parse = self.parser.parse_spacy_sentence(
            self.spacy_sentence, atom_sequence=atom_seq)

        edge = parse['main_edge']
        correct = self.edge_correct(edge, parse['failed'])

        air = self.accept_ignore_restart()
        ignore = True
        if air == 'a':
            ignore = False
        elif air == 'r':
            return None

        return {'sentence': sentence,
                'source': self.source,
                'atoms': list(atom.to_str() for atom in self.atoms),
                'hyperedge': edge.to_str() if edge else None,
                'correct': correct,
                'ignore': ignore}

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

    def generate(self, indir, outfile):
        self._open_input_files(indir)

        self.load_sentences(outfile)

        with open(outfile, 'a') as outfile:
            for sentence, source in self._sentences():
                sentence = sentence.strip()
                if sentence not in self.sentences:
                    self.print_counts()
                    case = None
                    while case is None:
                        case = self.annotate_sentence(sentence, source)
                    outfile.write('{}\n'.format(json.dumps(case)))
                    self.sentences.add(sentence)
                    self.update_counts(case)

        self._close_input_files()


def generate_parser_training_data(args):
    TrainingDataGenerator(
        args.lang, args.parser).generate(args.indir, args.outfile)


if __name__ == '__main__':
    wrapper(
        generate_parser_training_data, text='generate parser training data')
