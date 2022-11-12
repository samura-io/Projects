import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Perceptron
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
import fcm_py
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import confusion_matrix
import seaborn as sn
import matplotlib.pyplot as plt

def fit_cluster_labels(y_cluster, y_real):
    n_different = 0
    for y in y_cluster:
        if y > n_different:
            n_different = y
    n_different += 1
    y_new = []
    for i in range(n_different):
        num_of_labels = []
        for tek in range(n_different):
            num_of_labels.append(0)
        for j in range(len(y_cluster)):
            if i == y_cluster[j]:
                num_of_labels[y_real[j]-1] = num_of_labels[y_real[j]-1] + 1
        y_new.append(np.argmax(num_of_labels)+1)

    for j in range(len(y_cluster)):
        y_cluster[j] = y_new[y_cluster[j]]

    return y_cluster

def save_cf_mrx(mrx, file_name,
                class_names=None, font_scale=1, figsize=(12, 10), cmap="coolwarm", dpi=600):
    # # Perceptually     Uniform     Sequential
    # ['viridis', 'plasma', 'inferno', 'magma']
    # # Sequential
    # ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
    #  'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']
    # Sequential(2)
    # ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool',
    #  'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper']
    # Diverging
    # ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']
    # Qualitative
    # ['Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c']
    # Miscellaneous
    # ['flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix',
    #  'brg', 'hsv', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']

    fig, ax = plt.subplots(figsize=figsize)  # Sample figsize in inches
    if class_names:
        df_cm = pd.DataFrame(mrx, index=[i for i in class_names],
                             columns=[i for i in class_names])
    else:
        df_cm = pd.DataFrame(mrx, index=[i for i in range(len(mrx[0]))],
                             columns=[i for i in range(len(mrx[0]))])
    sn.set(font_scale=font_scale)  # for label size
    sn.heatmap(df_cm, annot=True, cmap=cmap, ax=ax, fmt='d')  # font size

    plt.savefig(file_name, dpi=dpi)

def analyze(dataset_path, result_file_name,
            class_names,
            val_path="",
            methods=['lr', 'ppn', 'tree', 'forest', 'svm', 'kmeans', 'knn', 'ac', 'fcm'],
            test_size=0.3,
            neighbors_metric='minkowski',
            n_neighbors=5,
            forest_n_estimators=100,
            c_big=1000,
            svm_kernel='linear',
            krit='entropy',  #'entropy', 'gini'
            tree_max_depth=5,
            n_clusters=3,
            plt_fonsizes=[8, 10, 12],  # small, medium, big
            verbose=False):

    SMALL_SIZE = plt_fonsizes[0]
    MEDIUM_SIZE = plt_fonsizes[1]
    BIGGER_SIZE = plt_fonsizes[2]

    plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    df_burn = pd.read_csv(dataset_path, delimiter=';', index_col=0)

    if verbose:
        print("First 5 records of dataset:")
        print(df_burn.head())

    y = df_burn[['class']]['class'].tolist()
    X = df_burn.drop('class', axis=1)
    X = X.replace(',', '.', regex=True).astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=0)

    sc = StandardScaler()
    sc.fit(X_train)
    X_train_std = sc.transform(X_train)
    X_test_std = sc.transform(X_test)

    X_test['real'] = y_test


    # Perceptron
    if 'ppn' in methods:
        ppn = Perceptron()
        ppn.fit(X_train_std, y_train)
        ppn_predict = ppn.predict(X_test_std)
        X_test['ppn'] = ppn_predict

        cf_matrix = confusion_matrix(y_test, ppn_predict)
        save_cf_mrx(cf_matrix, "ppn_cf_mrx.png", class_names=class_names)

    # SVM
    if 'svm' in methods:
        svm = SVC(kernel=svm_kernel, C=c_big, gamma=0.1, random_state=0)
        svm.fit(X_train_std, y_train)
        svm_predict = svm.predict(X_test_std)
        X_test['svm'] = svm_predict

        cf_matrix = confusion_matrix(y_test, svm_predict)
        save_cf_mrx(cf_matrix, "svm_cf_mrx.png", class_names=class_names)


    # Trees
    if 'tree' in methods:
        tree = DecisionTreeClassifier(criterion=krit, max_depth=tree_max_depth, random_state=0)
        tree.fit(X_train_std, y_train)
        tree_predict = tree.predict(X_test_std)
        X_test['tree'] = tree_predict

        cf_matrix = confusion_matrix(y_test, tree_predict)
        save_cf_mrx(cf_matrix, "tree_cf_mrx.png", class_names=class_names)

    # Logistic Regression
    if 'lr' in methods:
        lr = LogisticRegression(C=c_big, random_state=0)
        lr.fit(X_train_std, y_train)
        lr_predict = lr.predict(X_test_std)
        X_test['lr'] = lr_predict

        cf_matrix = confusion_matrix(y_test, lr_predict)
        save_cf_mrx(cf_matrix, "lr_cf_mrx.png", class_names=class_names)

    # Forest
    if 'forest' in methods:
        forest = RandomForestClassifier(criterion=krit, n_estimators=forest_n_estimators, random_state=0, n_jobs=2)
        forest.fit(X_train_std, y_train)
        forest_predict = forest.predict(X_test_std)
        X_test['forest'] = forest_predict

        cf_matrix = confusion_matrix(y_test, forest_predict)
        save_cf_mrx(cf_matrix, "forest_cf_mrx.png", class_names=class_names)

    # Neighbors
    # metric = 'minkowski' sum(|x - y|^p)^(1/p)
    # metric = 'euclidean'  # sqrt(sum((x - y)^2))
    # metric = 'chebyshev'  # max(|x - y|)
    # metric = 'manhattan'  # sum(|x - y|)
    if 'knn' in methods:
        knn = KNeighborsClassifier(n_neighbors=n_neighbors, metric=neighbors_metric)
        knn.fit(X_train_std, y_train)
        knn_predict = knn.predict(X_test_std)
        X_test['knn'] = knn_predict

        cf_matrix = confusion_matrix(y_test, knn_predict)
        save_cf_mrx(cf_matrix, "knn_cf_mrx.png", class_names=class_names)

    # Agglomerative Clustering
    if 'ac' in methods:
        ac = AgglomerativeClustering(n_clusters=n_clusters, affinity='euclidean', linkage='complete')
        ac.fit(X_train_std)
        ac_predict = ac.fit_predict(X_test_std)
        ac_predict_labeled = fit_cluster_labels(ac_predict, y_test)
        X_test['ac'] = ac_predict_labeled

        cf_matrix = confusion_matrix(y_test, ac_predict_labeled)
        save_cf_mrx(cf_matrix, "ac_cf_mrx.png", class_names=class_names)

        if verbose:
            print('Метки кластеров Agglomerative Clustering %s' % ac_predict)

    #K-means
    if 'kmeans' in methods:
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X_train_std)
        k_means_predict = kmeans.predict(X_test_std)
        k_means_predict_labeled = fit_cluster_labels(k_means_predict, y_test)
        X_test['k_means'] = k_means_predict_labeled

        cf_matrix = confusion_matrix(y_test, k_means_predict_labeled)
        save_cf_mrx(cf_matrix, "k_means_cf_mrx.png", class_names=class_names)

        if verbose:
            print("Искажение k-means: {0:5.3f}".format(kmeans.inertia_))

    if 'fcm' in methods:
        fcm = fcm_py.FCM(n_clusters)
        fcm.fit(X_train_std)
        fcm_predict = fcm.predict(X_test_std)
        if verbose:
            print("Искажение FCM: {0:5.3f}".format(fcm.inertia_))

        fcm_class1_predict = []
        fcm_class2_predict = []
        fcm_class3_predict = []

        fcm_predict_max = fcm.predict_max(X_test_std)
        fcm_labeled = fit_cluster_labels(fcm_predict_max, y_test)

        cf_matrix = confusion_matrix(y_test, fcm_labeled)
        save_cf_mrx(cf_matrix, "fcm_cf_mrx.png", class_names=class_names)

        for i in range(len(X_test)):
            fcm_class1_predict.append(fcm_predict[i, 0])
            fcm_class2_predict.append(fcm_predict[i, 1])
            fcm_class3_predict.append(fcm_predict[i, 2])

        X_test['fcm 1'] = fcm_class1_predict
        X_test['fcm 2'] = fcm_class2_predict
        X_test['fcm 3'] = fcm_class3_predict
        X_test['fcm max'] = fcm_labeled

    X_test.to_csv(result_file_name, sep=';')


if __name__ == '__main__':

    analyze('../datasets/dataset4_pure.csv', 'results.csv',
            # class_names=['ВПП', 'Река', 'Песок', 'Пашня', 'Здание', 'ЧЗ', 'Оз'],  # для 3-го датасета
            # class_names=['ВПП', 'Волга', 'Хвоя', 'Листв', 'Песок', 'Пашня', 'Здание', 'Цист', 'ЧЗ', 'Оз'],
            class_names=['ВПП', 'Река', 'Хвоя', 'Листв', 'Песок', 'Пашня', 'Здание', 'ЧЗ', 'Оз'],
            methods=['lr',
                     'ppn',
                     'tree',
                     'forest',
                     'svm',
                     'kmeans',
                     'knn',
                     'ac'],
                     # 'fcm'],
            test_size=0.3,
            neighbors_metric='minkowski',
            n_neighbors=5,
            forest_n_estimators=100,
            c_big=1000,
            svm_kernel='linear',
            krit='entropy',  #'entropy', 'gini'
            tree_max_depth=5,
            n_clusters=10,
            verbose=True)
