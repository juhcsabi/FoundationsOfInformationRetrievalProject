import os
import typing

from trec_files import read_qrels_file, read_run_file, read_eval_files
from scipy.stats import ttest_rel
from scipy.stats import binomtest


def success_at_1(relevant: list, retrieved: list) -> int:
    if len(retrieved) > 0 and retrieved[0] in relevant:
        return 1
    else:
        return 0


def success_at_k(relevant: list, retrieved: list, k: int) -> int:
    if len(retrieved) >= k:
        for element in retrieved[:k]:
            if element in relevant:
                return 1
    return 0


def success_at_5(relevant: list, retrieved: list) -> int:
    return success_at_k(relevant, retrieved, k=5)


def success_at_10(relevant: list, retrieved: list) -> int:
    return success_at_k(relevant, retrieved, k=10)


def relevant_items_retrieved(relevant: list, retrieved: list) -> int:
    return sum([retrieved_doc in relevant for retrieved_doc in retrieved])


def precision(relevant: list, retrieved: list) -> float:
    return (relevant_items_retrieved(relevant, retrieved) / len(retrieved)) if len(retrieved) > 0 else 0 


def recall(relevant: list, retrieved: list) -> float:
    return relevant_items_retrieved(relevant, retrieved) / len(relevant)


def f_measure(relevant: list, retrieved: list, beta=1) -> float:
    return (beta * beta + 1) * recall(relevant, retrieved) * precision(relevant, retrieved) / (
            (beta * beta) * precision(relevant, retrieved) + recall(relevant, retrieved))


def precision_at_k(relevant: list, retrieved: list, k: int) -> float:
    return precision(relevant, retrieved[:k])


def r_precision(relevant: list, retrieved: list) -> float:
    return precision_at_k(relevant, retrieved, len(relevant))


def recall_at_k(relevant: list, retrieved: list, k: int) -> float:
    return recall(relevant, retrieved[:k])


def interpolated_precision_at_recall_X(relevant: list, retrieved: list, X: float) -> float:
    max_prec = 0.0
    for k in range(len(retrieved)):
        re_at_k = recall_at_k(relevant, retrieved, k=k + 1)
        if re_at_k >= X:
            # print(re_at_k)
            prec_at_k = precision_at_k(relevant, retrieved, k=k + 1)
            if prec_at_k > max_prec:
                max_prec = prec_at_k
    return max_prec


def average_precision(relevant: list, retrieved: list) -> float:
    precisions = [0.0 for _ in range(len(relevant))]
    relevant_found = 0
    for i in range(len(retrieved)):
        if retrieved[i] in relevant:
            precisions[relevant_found] = precision_at_k(relevant, retrieved, k=i + 1)
            relevant_found += 1
    return sum(precisions) / len(precisions)


def mean_average_precision(all_relevant: list, all_retrieved: list) -> float:
    count = 0
    total = 0
    for key in all_relevant:
        count += 1
        total += average_precision(all_relevant[key], all_retrieved[key])
    return total / count


def mean_metric(measure, all_relevant: list, all_retrieved: list) -> typing.Tuple[str, float]:
    total = 0
    count = 0
    for qid in all_relevant:
        relevant = all_relevant[qid]
        retrieved = all_retrieved.get(qid, [])
        value = measure(relevant, retrieved)
        total += value
        count += 1
    return "mean " + measure.__name__, total / count


def trec_eval(qrels_file: os.PathLike, run_file: os.PathLike) -> typing.List[typing.Tuple[str, float]]:
    def precision_at_1(rel, ret): return precision_at_k(rel, ret, k=1)

    def precision_at_5(rel, ret): return precision_at_k(rel, ret, k=5)

    def precision_at_10(rel, ret): return precision_at_k(rel, ret, k=10)

    def precision_at_50(rel, ret): return precision_at_k(rel, ret, k=50)

    def precision_at_100(rel, ret): return precision_at_k(rel, ret, k=100)

    def precision_at_recall_00(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.0)

    def precision_at_recall_01(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.1)

    def precision_at_recall_02(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.2)

    def precision_at_recall_03(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.3)

    def precision_at_recall_04(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.4)

    def precision_at_recall_05(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.5)

    def precision_at_recall_06(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.6)

    def precision_at_recall_07(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.7)

    def precision_at_recall_08(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.8)

    def precision_at_recall_09(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=0.9)

    def precision_at_recall_10(rel, ret): return interpolated_precision_at_recall_X(rel, ret, X=1.0)

    (all_relevant, all_retrieved) = read_eval_files(qrels_file, run_file)

    unknown_qids = set(all_retrieved.keys()).difference(all_relevant.keys())
    if len(unknown_qids) > 0:
        raise ValueError("Unknown qids in run: {}".format(sorted(list(unknown_qids))))

    metrics = [success_at_1,
               success_at_5,
               success_at_10,
               r_precision,
               precision_at_1,
               precision_at_5,
               precision_at_10,
               precision_at_50,
               precision_at_100,
               precision_at_recall_00,
               precision_at_recall_01,
               precision_at_recall_02,
               precision_at_recall_03,
               precision_at_recall_04,
               precision_at_recall_05,
               precision_at_recall_06,
               precision_at_recall_07,
               precision_at_recall_08,
               precision_at_recall_09,
               precision_at_recall_10,
               average_precision]

    return [mean_metric(metric, all_relevant, all_retrieved) for metric in metrics]

def trec_eval_to_str(qrels_file, run_file):
    ret_str = f"Results for {run_file}\n"
    results = trec_eval(qrels_file, run_file)
    for (metric, score) in results:
        ret_str += "{:<30} {:.4}\n".format(metric, score)
    return ret_str


def sign_test_values(measure: callable, qrels_file: os.PathLike, run_file_1: os.PathLike, run_file_2: os.PathLike) -> typing.Tuple[int, int, int]:
    all_relevant = read_qrels_file(qrels_file)
    all_retrieved_1 = read_run_file(run_file_1)
    all_retrieved_2 = read_run_file(run_file_2)
    better = 0
    worse = 0
    equal = 0
    for key in all_relevant:
        if measure(all_relevant[key], all_retrieved_1[key]) > measure(all_relevant[key],
                                                                                        all_retrieved_2[key]):
            worse += 1
        elif measure(all_relevant[key], all_retrieved_1[key]) < measure(all_relevant[key],
                                                                                        all_retrieved_2[key]):
            better += 1
        else:
            equal += 1
    return better, worse, equal

def t_test_outputs(qrels_file, run_file_1, run_file_2):

    all_relevant = read_qrels_file(qrels_file)
    all_retrieved_1 = read_run_file(run_file_1)
    all_retrieved_2 = read_run_file(run_file_2)

    print([key for key in all_relevant])

    precisions_at_10_1 = [precision_at_k(all_relevant[key], all_retrieved_1[key], 10) for key in all_relevant]
    precisions_at_10_2 = [precision_at_k(all_relevant[key], all_retrieved_2[key], 10) for key in all_relevant]
    for prec1, prec2 in zip(precisions_at_10_1, precisions_at_10_2):
        print(prec1, prec2)

    t_statistic, p_value = ttest_rel(precisions_at_10_1, precisions_at_10_2)

    # Check the p-value to determine significance
    alpha = 0.05
    if p_value < alpha:
        print("There is a significant difference in precision_at_10 performance between the two systems.")
    else:
        print("There is no significant difference in precision_at_10 performance between the two systems.")
    print(t_statistic, p_value)


def precision_at_rank_5(rel: list, ret: list) -> float:
    return precision_at_k(rel, ret, k=5)

def precision_at_rank_20(rel: list, ret: list) -> float:
    return precision_at_k(rel, ret, k=20)
