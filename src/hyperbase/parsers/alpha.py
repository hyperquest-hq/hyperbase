from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder


class Alpha(object):
    def __init__(self, cases_str):
        X = []
        y = []

        for line in cases_str.strip().split('\n'):
            sline = line.strip()
            if len(sline) > 0:
                row = sline.strip().split('\t')
                true_value = row[0]
                tag = row[3]
                dep = row[4]
                hpos = row[6]
                hdep = row[8]
                pos_after = row[19]

                y.append([true_value])
                X.append((tag, dep, hpos, hdep, pos_after))

        if len(y) > 0:
            self.empty = False

            self.encX = OneHotEncoder(handle_unknown='ignore')
            self.encX.fit(X)
            self.ency = OneHotEncoder(handle_unknown='ignore')
            self.ency.fit(y)

            X_ = self.encX.transform(X).toarray()
            y_ = self.ency.transform(y).toarray()

            self.clf = RandomForestClassifier(random_state=777)
            self.clf.fit(X_, y_)
        else:
            self.empty = True

    def predict(self, X):
        # an empty classifier allways predicts 'C'
        if self.empty:
            return tuple('C' for _ in range(len(X)))

        X_ = self.encX.transform(X).toarray()
        preds = self.ency.inverse_transform(self.clf.predict(X_))
        return tuple(pred[0] if pred else 'C' for pred in preds)
