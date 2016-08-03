import sys
import pdb
import numpy as np
import pandas as pd
import statistics
from sklearn import metrics
from . import dataset

def compute_AUC(test_labels, test_predictions):
    fpr, tpr, thresholds = metrics.roc_curve(
        test_labels, test_predictions, pos_label=1)
    return metrics.auc(fpr, tpr)

def compute_avg_false_positive_rate(test_labels, test_predictions):
    fpr, tpr, thresholds = metrics.roc_curve(
        test_labels, test_predictions, pos_label=1)
    return statistics.mean(fpr)


def compute_avg_true_positive_rate(test_labels, test_predictions):
    fpr, tpr, thresholds = metrics.roc_curve(
        test_labels, test_predictions, pos_label=1)

    return statistics.mean(tpr)

def compute_result_at_x_proportion(test_labels, test_predictions, metric, x_proportion=0.01):

    """
    Returns the raw number of a given metric:
        'TP' = true positives,
        'TN' = true negatives,
        'FP' = false positives,
        'FN' = false negatives

    for a threshold of the results stated as a proportion:
        x_proportion
        where x_proportion = 0.01 represents 1.0%

    """

    #Get Binary Predictions at Threshold
    cutoff_index = int(len(test_predictions) * x_proportion)
    cutoff_index = min(cutoff_index, len(test_predictions) - 1)

    sorted_by_probability = np.sort(test_predictions)[::-1]
    cutoff_probability = sorted_by_probability[cutoff_index]

    test_predictions_binary = np.copy(test_predictions)
    test_predictions_binary[test_predictions_binary >= cutoff_probability] = 1
    test_predictions_binary[test_predictions_binary < cutoff_probability] = 0


    #Recode Test Labels to Correctly id TP, TN, FP, FN from a Difference of Lists
    test = [99 if y==1 else 0 for y in test_labels]
    pred = [99 if y==1 else 5 for y in test_predictions_binary]
    results = [(x-y) for x,y in zip(test,pred)]


    # KEY WORKED OUT
    #True Positive:     Test_Label=99 and Test_Prediction   = 99::  x-y == 0
    #True Negative:     Test_Label=0 and True_Prediction    = 5::   x-y == -5
    #False Positive:    Test_Label=0 and Test_Prediction    = 99::  x-y== -99
    #False Negative:    Test_Label=99 and Test_Prediction   = 5::   x-y==94

    # KEY RESULTS
    #   0   = TP
    #   -5  = TN
    #   -99 = FP
    #   94  = FN

    #Get Counts of Results
    TP = len([y for y in results if y==0])
    TN = len([y for y in results if y==-5])
    FP = len([y for y in results if y==-99])
    FN = len([y for y in results if y==94])

    #Return Requested Metric
    if metric=='TP':
        return TP
    elif metric=='TN':
        return TN
    elif metric=='FP':
        return FP
    elif metric=='FN':
        return FN
    else:
        pass



def precision_at_x_proportion(test_labels, test_predictions, x_proportion=0.01,
                           return_cutoff=False):

    cutoff_index = int(len(test_predictions) * x_proportion)
    cutoff_index = min(cutoff_index, len(test_predictions) - 1)

    sorted_by_probability = np.sort(test_predictions)[::-1]
    cutoff_probability = sorted_by_probability[cutoff_index]

    test_predictions_binary = np.copy(test_predictions)
    test_predictions_binary[test_predictions_binary >= cutoff_probability] = 1
    test_predictions_binary[test_predictions_binary < cutoff_probability] = 0

    precision, _, _, _ = metrics.precision_recall_fscore_support(
        test_labels, test_predictions_binary)
    precision = precision[1]  # only interested in precision for label 1

    if return_cutoff:
        return precision, cutoff_probability
    else:
        return precision


def recall_at_x_proportion(test_labels, test_predictions, x_proportion=0.01,
                        return_cutoff=False):

    cutoff_index = int(len(test_predictions) * x_proportion)
    cutoff_index = min(cutoff_index, len(test_predictions) - 1)

    sorted_by_probability = np.sort(test_predictions)[::-1]
    cutoff_probability = sorted_by_probability[cutoff_index]

    test_predictions_binary = np.copy(test_predictions)
    test_predictions_binary[test_predictions_binary >= cutoff_probability] = 1
    test_predictions_binary[test_predictions_binary < cutoff_probability] = 0

    _, recall, _, _ = metrics.precision_recall_fscore_support(
        test_labels, test_predictions_binary)
    recall = recall[1]  # only interested in precision for label 1

    if return_cutoff:
        return recall, cutoff_probability
    else:
        return recall

def get_test_predictions_binary(test_predictions, cutoff_probability=0.8):

    test_predictions_binary = np.copy(test_predictions)
    test_predictions_binary[test_predictions_binary >= cutoff_probability] = 1
    test_predictions_binary[test_predictions_binary < cutoff_probability] = 0

    return test_predictions_binary


def calculate_all_evaluation_metrics( test_label, test_predictions, test_predictions_binary, time_for_model_in_seconds ):
    """ Calculate several evaluation metrics using sklearn for a set of
        labels and predictions.
    :param list test_labels: list of true labels for the test data.
    :param list test_predictions: list of risk scores for the test data.
    :return: all_metrics
    :rtype: dict
    """

    all_metrics = dict()
    #FORMAT FOR DICTIONARY KEY
    #all_metrics["metric|parameter|comment"] OR
    #all_metrics["metric|parameter"] OR
    #all_metrics["metric||comment"] OR
    #all_metrics["metric"]

    #Standard Metrics
    all_metrics["accuracy"] = metrics.accuracy_score( test_label, test_predictions_binary )
    all_metrics["auc|roc"]  = metrics.roc_auc_score( test_label, test_predictions )
    all_metrics["average precision score"] = metrics.average_precision_score( test_label, test_predictions )
    all_metrics["f1"] = metrics.f1_score( test_label, test_predictions_binary )
    all_metrics["fbeta@|0.75 beta"] = metrics.fbeta_score( test_label, test_predictions_binary, 0.75)
    all_metrics["fbeta@|1.25 beta"] = metrics.fbeta_score( test_label, test_predictions_binary, 1.25)
    all_metrics["precision@|default"] = metrics.precision_score( test_label, test_predictions_binary )
    all_metrics["recall@|default"] = metrics.recall_score( test_label, test_predictions_binary )
    all_metrics["time|seconds"] = time_for_model_in_seconds


    # Threshold Metrics by Percentage
    percents = [ 0.01, 0.10, 0.25, 0.50, 1.0, 5.0, 10.0, 25.0, 50.0, 75.0 ]
    for percent in percents:

        # Precision
        all_metrics["precision@|{}".format( str(percent)) ] = precision_at_x_proportion(test_label, test_predictions, x_proportion=percent/100.00)

        # Recall
        all_metrics["recall@|{}".format( str(percent)) ] = recall_at_x_proportion(test_label, test_predictions, x_proportion=percent/100.00)


        # Raw counts of officers we are flagging correctly and incorrectly at various fractions of the test set.
        all_metrics["false positives@|{}".format( str(percent)) ] = compute_result_at_x_proportion(test_label, test_predictions, 'FP', x_proportion=percent/100.0)
        all_metrics["false negatives@|{}".format( str(percent)) ] = compute_result_at_x_proportion(test_label, test_predictions, 'FN', x_proportion=percent/100.0)
        all_metrics["true positives@|{}".format( str(percent)) ] = compute_result_at_x_proportion(test_label, test_predictions, 'TP', x_proportion=percent/100.0)
        all_metrics["true negatives@|{}".format( str(percent)) ] = compute_result_at_x_proportion(test_label, test_predictions, 'TN', x_proportion=percent/100.0)


    return all_metrics



def test_thresholds(testid, testprobs, start_date, end_date):
    """
    Compute confusion matrices for a range of thresholds for the DSaPP model
    """

    perc_thresholds = [x/100. for x in range(10, 85, 5)]
    confusion_matrices = {}
    for each_threshold in perc_thresholds:
        cm_eis, cm_dsapp = compute_confusion(testid, testprobs, each_threshold,
                                             start_date, end_date)
        confusion_matrices.update({each_threshold: {'eis': cm_eis,
                                                    'dsapp': cm_dsapp}})

    return confusion_matrices


def compute_confusion(testid, testprobs, at_x_perc, start_date, end_date):
    """
    Compute confusion matrices for baseline EIS performance during this time period
    as well as DSaPP model at x percent during this time period

    Args:
    testid - test ids for the DSaPP model
    testprobs - probabilities produced by the model
    at_x_perc - float between 0 and 1 defining the probability cutoff
    start_date - beginning of testing period
    end_date - end of testing period

    Returns:
    cm_eis - confusion matrix for the existing EIS during this time period
    cm_dsapp - confusion matrix for the DSaPP EIS during this time period
    and probability cutoff
    """

    # Score the existing EIS performance
    df = dataset.get_baseline(start_date, end_date)
    df['eisflag'] = 1

    # Score the DSaPP performance
    df_dsapp = assign_classes(testid, testprobs, at_x_perc)

    # Combine the old EIS and DSaPP EIS dataframes
    df_combined = df.merge(df_dsapp, on='officer_id', how='outer')
    df_combined['eisflag'] = df_combined['eisflag'].fillna(0)

    # Get whether these officers had adverse incidents or not
    df_adverse = dataset.get_labels_for_ids(df_combined['officer_id'], start_date, end_date)

    # Add the new column
    df_final = df_combined.merge(df_adverse, on='officer_id', how='outer').fillna(0)

    cm_eis = metrics.confusion_matrix(df_final['adverse_by_ourdef'].values, df_final['eisflag'].values)
    cm_dsapp = metrics.confusion_matrix(df_final['adverse_by_ourdef'].values, df_final['ourflag'].values)

    return cm_eis, cm_dsapp


def assign_classes(testid, predictions, x_proportion):
    """
    Args:
    testid - list of ids
    predictions - list of probabilities
    x_proportion - probability cutoff for positive and negative classes

    Returns:
    df - pandas DataFrame that contains test ids and integer class
    """
    cutoff_index = int(len(predictions) * x_proportion)
    cutoff_index = min(cutoff_index, len(predictions) - 1)

    sorted_by_probability = np.sort(predictions)[::-1]
    cutoff_probability = sorted_by_probability[cutoff_index]

    predictions_binary = np.copy(predictions)
    predictions_binary[predictions_binary >= cutoff_probability] = 1
    predictions_binary[predictions_binary < cutoff_probability] = 0

    df = pd.DataFrame({'officer_id': testid, 'ourflag': predictions_binary})

    return df
