import statistics
from collections import Counter

import progressbar
from scipy.stats import ks_2samp
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from hyperbase.cli import wrapper


P_VALUE = .005
RUNS = 100

ALL_FEATURES = ['word15', 'word25', 'word50', 'word100', 'pos', 'tag', 'dep',
                'hword15', 'hword25', 'hword50', 'hword100', 'hpos', 'htag',
                'hdep', 'is_root', 'has_lefts', 'has_rights', 'ent_type',
                'shape', 'word_before15', 'word_before25', 'word_before50',
                'word_before100', 'word_after15', 'word_after25',
                'word_after50', 'word_after100', 'punct_before', 'punct_after',
                'pos_before', 'pos_after', 'dep_before', 'dep_after']


class FeatureSelector(object):
    def __init__(self, atoms_file, outfile):
        self.atoms_file = atoms_file
        self.outfile = outfile
        self.common_words15 = None
        self.common_words25 = None
        self.common_words50 = None
        self.common_words100 = None
        self._find_common_words()

    def _log(self, msg):
        print(msg)
        with open(self.outfile, 'at') as f:
            f.write('{}\n'.format(msg))

    def _find_common_words(self):
        words = Counter()
        with open(self.atoms_file, 'rt') as f:
            for line in f.readlines():
                row = line.strip().split('\t')
                word = row[1]
                words[word] += 1
        self.common_words15 = set([item[0] for item in words.most_common(15)])
        self.common_words25 = set([item[0] for item in words.most_common(25)])
        self.common_words50 = set([item[0] for item in words.most_common(50)])
        self.common_words100 = set(
            [item[0] for item in words.most_common(100)])

    def _train_classifier(self, feature_names):
        X = []
        y = []

        sources = Counter()

        with open(self.atoms_file, 'rt') as f:
            for line in f.readlines():
                row = line.strip().split('\t')

                features = {}
                features['word15'] =\
                    row[1] if row[1] in self.common_words15 else ''
                features['word25'] =\
                    row[1] if row[1] in self.common_words25 else ''
                features['word50'] =\
                    row[1] if row[1] in self.common_words50 else ''
                features['word100'] =\
                    row[1] if row[1] in self.common_words100 else ''
                features['pos'] = row[2]
                features['tag'] = row[3]
                features['dep'] = row[4]
                features['hword15'] =\
                    row[5] if row[5] in self.common_words15 else ''
                features['hword25'] =\
                    row[5] if row[5] in self.common_words25 else ''
                features['hword50'] =\
                    row[5] if row[5] in self.common_words50 else ''
                features['hword100'] =\
                    row[5] if row[5] in self.common_words100 else ''
                features['hpos'] = row[6]
                features['htag'] = row[7]
                features['hdep'] = row[8]
                features['is_root'] = row[9]
                features['has_lefts'] = row[10]
                features['has_rights'] = row[11]
                features['ent_type'] = row[12]
                features['shape'] = row[13]
                features['word_before15'] =\
                    row[14] if row[14] in self.common_words15 else ''
                features['word_before25'] =\
                    row[14] if row[14] in self.common_words25 else ''
                features['word_before50'] =\
                    row[14] if row[14] in self.common_words50 else ''
                features['word_before100'] =\
                    row[14] if row[14] in self.common_words100 else ''
                features['word_after15'] =\
                    row[15] if row[15] in self.common_words15 else ''
                features['word_after25'] =\
                    row[15] if row[15] in self.common_words25 else ''
                features['word_after50'] =\
                    row[15] if row[15] in self.common_words50 else ''
                features['word_after100'] =\
                    row[15] if row[15] in self.common_words100 else ''
                features['punct_before'] = row[16]
                features['punct_after'] = row[17]
                features['pos_before'] = row[18]
                features['pos_after'] = row[19]
                features['tag_before'] = row[20]
                features['tag_after'] = row[21]
                features['dep_before'] = row[22]
                features['dep_after'] = row[23]

                source = row[25]

                y.append([row[0]])
                X.append(list(features[feature] for feature in feature_names))
                sources[source[:-1]] += 1

        encX = OneHotEncoder(handle_unknown='ignore')
        encX.fit(X)
        ency = OneHotEncoder(handle_unknown='ignore')
        ency.fit(y)

        X_ = encX.transform(X).toarray()
        y_ = ency.transform(y).toarray()

        X_train, X_test, y_train, y_test = train_test_split(
            X_, y_, test_size=0.33)

        clf = RandomForestClassifier()
        clf.fit(X_train, y_train)

        return clf, encX, ency, X_test, y_test

    def _gen_accs(self, features, n=RUNS):
        accs = []
        for _ in progressbar.progressbar(range(n)):
            clf, encX, ency, X_test, y_test = self._train_classifier(features)
            y_pred = clf.predict(X_test)
            accs.append(metrics.accuracy_score(y_test, y_pred))
        return accs

    def _gen_accs_ablation(self, features):
        accs_ablation = {}

        for ab_feat in features:
            afeatures = list(feature for feature in features
                             if feature != ab_feat)
            accs = self._gen_accs(afeatures)
            accs_ablation[ab_feat] = accs
        return accs_ablation

    def _gen_accs_regrowth(self, features):
        accs_regrowth = {}

        for add_feat in [feature for feature in ALL_FEATURES
                         if feature not in features]:
            afeatures = features + [add_feat]
            accs = self._gen_accs(afeatures)
            accs_regrowth[add_feat] = accs
        return accs_regrowth

    def _find_worst_feature(self, features, accs_ablation):
        base_accs = self._gen_accs(features)
        base_acc = statistics.median(base_accs)

        self._log('base accuracy: {}'.format(base_acc))

        max_pvalue = P_VALUE
        max_pvalue_feature = None
        max_damage = 0.
        max_damage_feature = None
        for ab_feat in features:
            acc = statistics.median(accs_ablation[ab_feat])
            pvalue = ks_2samp(base_accs, accs_ablation[ab_feat]).pvalue
            keep = ''
            if pvalue < P_VALUE:
                keep = '*'
            if pvalue > max_pvalue:
                max_pvalue = pvalue
                max_pvalue_feature = ab_feat
            damage = acc - base_acc
            if damage > max_damage:
                max_damage = damage
                max_damage_feature = ab_feat
            self._log('{} {} {} [{}] p-value: {}'.format(
                keep, ab_feat, acc, acc - base_acc, pvalue))
        return max_damage_feature if max_damage_feature else max_pvalue_feature

    def _find_best_feature(self, features, accs_regrowth):
        base_accs = self._gen_accs(features)
        base_acc = statistics.median(base_accs)

        self._log('base accuracy: {}'.format(base_acc))

        min_pvalue = 1.
        min_pvalue_feature = None
        for add_feat in [feature for feature in ALL_FEATURES
                         if feature not in features]:
            acc = statistics.median(accs_regrowth[add_feat])
            pvalue = ks_2samp(base_accs, accs_regrowth[add_feat]).pvalue
            keep = ''
            if acc > base_acc:
                if pvalue < P_VALUE:
                    keep = '*'
                    if pvalue < min_pvalue:
                        min_pvalue = pvalue
                        min_pvalue_feature = add_feat
            self._log('{} {} {} [{}] p-value: {}'.format(
                keep, add_feat, acc, acc - base_acc, pvalue))
        return min_pvalue_feature

    def _ablate(self, features):
        accs_ablation = self._gen_accs_ablation(features)
        worst_feature = self._find_worst_feature(features, accs_ablation)
        self._log('FEATURE REMOVED: {}'.format(worst_feature))
        return list(feature for feature in features
                    if feature != worst_feature)

    def _regrow(self, features):
        accs_regrowth = self._gen_accs_regrowth(features)
        best_feature = self._find_best_feature(features, accs_regrowth)
        self._log('FEATURE ADDED: {}'.format(best_feature))
        if best_feature:
            return features + [best_feature]
        else:
            return features

    def run(self):
        new_features = ALL_FEATURES
        cur_features = None
        i = 1

        # ablation stage
        while new_features != cur_features:
            self._log('\n>>> ITERATION {} <<<'.format(i))
            i += 1
            cur_features = new_features
            new_features = self._ablate(cur_features)

        # regrowth stage
        cur_features = None
        while new_features != cur_features:
            self._log('\n>>> ITERATION {} <<<'.format(i))
            i += 1
            cur_features = new_features
            new_features = self._regrow(cur_features)


def select_alpha_features(args):
    infile = args.infile
    outfile = args.outfile
    FeatureSelector(infile, outfile).run()


if __name__ == '__main__':
    wrapper(
        select_alpha_features, text='select features for alpha classifier')
