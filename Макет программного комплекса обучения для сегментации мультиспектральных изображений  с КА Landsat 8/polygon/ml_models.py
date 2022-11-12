import os
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from imblearn.datasets import make_imbalance
from imblearn.under_sampling import NearMiss
from imblearn.pipeline import make_pipeline
from imblearn.metrics import classification_report_imbalanced

class MLModels():

    def __init__(self, dataset, dataset_for_learning):
        print("Подготовка датасетов")
        self.dataset_for_learning_1 = pd.DataFrame(dataset_for_learning)
        # array = np.array([[0,0,0,0,0,0,0,0,255,0,0]])
        # dt = pd.DataFrame(array)
        # print('DT:\n', dt)
        # self.dataset_for_learning = pd.concat([self.dataset_for_learning_1, dt])
        self.dataset_for_learning = self.dataset_for_learning_1.drop([8, 9, 10], axis=1)
        print("1\n", self.dataset_for_learning)
        self.dataset = pd.DataFrame(dataset)
        self.dataset = self.dataset.fillna(1)
        print("2\n", self.dataset)
        self.X = self.dataset_for_learning.drop([7], axis=1)
        print("3\n", self.X)
        self.y = self.dataset_for_learning.drop([0, 1, 2, 3, 4, 5, 6], axis=1).values.ravel()
        print("4\n", self.y)

        sc = StandardScaler(copy=True, with_mean=True, with_std=True)
        sc.fit(self.X)
        self.X_train_std = sc.transform(self.X)
        self.dataset_std = sc.transform(self.dataset)

        self.Xs, self.ys = make_imbalance(
            self.X_train_std,
            self.y,
            sampling_strategy={1: 10000, 2: 10000, 3: 10000},
        )
        print('=' * 50)
        print(self.Xs)
        print('=' * 50)
        print(self.ys)

    def random_forest(self):
        print("Обучение")
        classifier = RandomForestClassifier()
        classifier.fit(self.Xs, self.ys)

        print("Предсказание")
        y_pred = classifier.predict(self.dataset)
        df = pd.DataFrame(y_pred)
        self.dataset[''] = df
        print(self.dataset)
        return self.dataset


if __name__ == "__main__":
    rf = MLModels()
    rf.random_forest()
