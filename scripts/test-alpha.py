from collections import Counter

from hyperbase.cli import wrapper
from hyperbase.parsers.alpha import Alpha


def test_alpha(args):
    training_data = args.training_data
    infile = args.infile

    with open(training_data, 'rt') as f:
        cases_str = f.read()
    alpha = Alpha(cases_str)

    n = 0
    correct = 0

    X = []
    y = []
    sources = []
    with open(infile, 'r') as f:
        for line in f.readlines():
            row = line.strip().split('\t')
            true_value = row[0]
            tag = row[3]
            dep = row[4]
            hpos = row[6]
            hdep = row[8]
            pos_after = row[19]
            source = row[25][:-1]
            X.append((tag, dep, hpos, hdep, pos_after))
            y.append(true_value)
            sources.append(source)
    preds = alpha.predict(X)

    n_source = Counter()
    correct_source = Counter()

    for pred, true_value, source in zip(preds, y, sources):
        n += 1
        n_source[source] += 1
        if pred == true_value:
            correct += 1
            correct_source[source] += 1

    for source in n_source:
        accuracy = float(correct_source[source]) / float(n_source[source])
        print('{} accuracy: {} [{} correct out of {}]'.format(
            source, accuracy, correct_source[source], n_source[source]))

    print()
    accuracy = float(correct) / float(n)
    print('overall accuracy: {} [{} correct out of {}]'.format(
        accuracy, correct, n))


if __name__ == '__main__':
    wrapper(test_alpha, text='test alpha classifier')
