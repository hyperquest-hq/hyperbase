import json
import random

from hyperbase.cli import wrapper


def split_parser_training_data(args):
    infile = args.infile
    if infile[-5:] != '.json':
        raise RuntimeError("Input file must have '.json' extension.")

    cases = []

    with open(infile, 'rt') as f:
        for line in f:
            case = json.loads(line)
            if not case['ignore']:
                cases.append(case)

    random.shuffle(cases)

    n_cases = len(cases)
    n_test = int(n_cases / 3)

    train_cases = cases[n_test:]
    test_cases = cases[:n_test]

    file_main_name = infile[:-5]
    train_file_name = '{}-train.json'.format(file_main_name)
    test_file_name = '{}-test.json'.format(file_main_name)

    with open(train_file_name, 'wt') as f:
        for case in train_cases:
            f.write('{}\n'.format(json.dumps(case)))

    with open(test_file_name, 'wt') as f:
        for case in test_cases:
            f.write('{}\n'.format(json.dumps(case)))

    print('{} total cases found'.format(n_cases))
    print('wrote {} train cases to {}'.format(
        len(train_cases), train_file_name))
    print('wrote {} test cases to {}'.format(len(test_cases), test_file_name))


if __name__ == '__main__':
    wrapper(
        split_parser_training_data, text='split parser training data')
