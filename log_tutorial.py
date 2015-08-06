import optunity
import optunity.metrics
import sklearn.svm
import numpy as np

#print len(array)   #=> 1247
#print len(labels)  #=> 1247

# make dummy data
array = np.array([[i] for i in range(1247)])
labels = [True] * 100 + [False] * 1147

# score function: twice iterated 10-fold cross-validated accuracy
@optunity.cross_validated(x=array, y=labels, num_folds=10, num_iter=2)
def svm_auc(x_train, y_train, x_test, y_test, C, gamma):
    model = sklearn.svm.SVC(C=C, gamma=gamma).fit(x_train, y_train)
    decision_values = model.decision_function(x_test)
    return optunity.metrics.roc_auc(y_test, decision_values)

# perform tuning
optimal_pars, _, _ = optunity.maximize(svm_auc, num_evals=200, C=[0, 10], gamma=[0, 1])

# train model on the full training set with tuned hyperparameters
optimal_model = sklearn.svm.SVC(**optimal_pars).fit(array, labels)
print(optimal_pars)