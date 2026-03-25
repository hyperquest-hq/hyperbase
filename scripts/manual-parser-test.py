import statistics

from termcolor import colored

from hyperbase import hedge
from hyperbase.cli import wrapper
from hyperbase.colored import colored_edge
from hyperbase.colored import indented
from hyperbase.parsers import create_parser


class ManualEvaluation(object):
    def __init__(self):
        self.correct = 0
        self.defect = 0
        self.wrong = 0
        self.edges = []
        self.defects = []
        self.defective_edges = []
        self.rel_defect_sizes = []

        correct = colored('c', 'green')
        minor = colored('d', 'yellow')
        wrong = colored('w', 'red')
        ignore = colored('i', 'blue')
        options_str = '{}/{}/{}/{}'.format(correct, minor, wrong, ignore)
        self.input_msg = 'correct, defect, wrong or ignore ({}) ? '.format(
            options_str)

    def input(self):
        answer = None
        while answer not in {'c', 'd', 'w', 'i'}:
            answer = input(self.input_msg)
        return answer

    def apply_evaluation(self, he, edge, defects):
        self.edges.append(edge)
        if he == 'c':
            self.correct += 1
        elif he == 'd':
            self.defect += 1
            self.defects.append(defects)
            self.defective_edges.append(edge)
            rds = 0.
            for defect in defects:
                rds += float(defect.size())
            rds = rds / float(edge.size())
            self.rel_defect_sizes.append(rds)
        elif he == 'w':
            self.wrong += 1

    def __str__(self):
        n = self.correct + self.defect + self.wrong
        ratio = float(self.correct) / float(n) if n > 0 else 0.
        correct_str = '{} ({}/{})'.format(ratio, self.correct, n)
        ratio = float(self.defect) / float(n) if n > 0 else 0.
        defect_str = '{} ({}/{})'.format(ratio, self.defect, n)
        ratio = float(self.wrong) / float(n) if n > 0 else 0.
        wrong_str = '{} ({}/{})'.format(ratio, self.wrong, n)
        line1 = 'correct: {}; defect: {}; wrong: {}'.format(
            correct_str, defect_str, wrong_str)
        if len(self.defects) > 0:
            mrds = statistics.mean(self.rel_defect_sizes)
        else:
            mrds = 0.
        line2 = 'mean relative defect size: {}'.format(mrds)
        return '{}\n{}'.format(line1, line2)


def error_msg(msg):
    print('\n{} {}\n'.format(colored('Error: ', 'red'), msg))


def input_defects(sentence, edge):
    s = colored('s', 'magenta')
    h = colored('h', 'cyan')
    i = colored('i', 'yellow')
    options_str = '{}/{}/{}/subedge'.format(s, h, i)
    input_msg = 'wrong subedge ({}) ? '.format(options_str)

    defects = None
    while not defects:
        answer = input(input_msg)
        if answer == 's':
            print('\n{}\n'.format(sentence))
        elif answer == 'h':
            print('\n{}\n'.format(colored_edge(edge)))
        elif answer == 'i':
            print('\n{}\n'.format(indented(edge)))
        else:
            edge_strs = answer.split('&')
            subedges = []
            failed = False
            for edge_str in edge_strs:
                subedge = hedge(edge_str)
                if subedge is None:
                    error_msg('{} did not parse correctly.'.format(edge_str))
                    failed = True
                elif edge.contains(subedge, deep=True):
                    subedges.append(subedge)
                else:
                    error_msg('{} is not a subedge of {}.'.format(
                        subedge.to_str(), edge.to_str()))
                    failed = True
            if not failed:
                defects = subedges
    return defects


def manual_test(args):
    parser = create_parser(lang=args.lang, parser_class=args.parser)

    he = ManualEvaluation()

    sentences = []

    # read existing tests
    try:
        with open(args.outfile, 'r') as f:
            for line in f:
                parts = line.split('\t')
                if len(parts) == 4:
                    sentence = parts[0].strip()
                    sentences.append(sentence)
                    edge = hedge(parts[1].strip())
                    answer = parts[2].strip()
                    defects = list(
                        hedge(edge_str) for edge_str in parts[3].split('&'))

                    he.apply_evaluation(answer, edge, defects)
    except FileNotFoundError:
        pass

    with open(args.infile, 'r') as f:
        for line in f:
            print('GLOBAL:')
            print(colored(str(he), 'white'))

            sentence = line.strip()

            if sentence not in sentences:
                sentences.append(sentence)
                parser_output = parser.parse(sentence)
                parsed_sentence = parser_output['parses'][0]
                edge = parsed_sentence['main_edge']

                if edge:
                    print('\n{}\n{}\n'.format(sentence, indented(edge)))

                    answer = he.input()
                    if answer == 'd':
                        defects = input_defects(sentence, edge)
                    else:
                        defects = []
                    he.apply_evaluation(answer, edge, defects)

                    defect_str = '&'.join(
                        [defect.to_str() for defect in defects])
                    row_str = '\t'.join(
                        (sentence, edge.to_str(), answer, defect_str))
                    with open(args.outfile, 'a') as of:
                        of.write('{}\n'.format(row_str))


if __name__ == '__main__':
    wrapper(manual_test, text='manual test of parser')
