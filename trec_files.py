import os
import evaluation
import elasticsearch
from elasticsearch_dsl import Search, Q
import typing
import pseudo_relevance


def read_qrels_file(qrels_file: os.PathLike) -> dict:  # reads the content of he qrels file
    trec_relevant = dict()  # query_id -> set([docid1, docid2, ...])
    with open(qrels_file, 'r') as qrels:
        for line in qrels:
            (qid, q0, doc_id, rel) = line.strip().split()
            if qid not in trec_relevant:
                trec_relevant[qid] = set()
            if rel == "1":
                trec_relevant[qid].add(doc_id)
    return trec_relevant


def read_run_file(run_file: os.PathLike) -> dict:
    # read the content of the run file produced by our IR system
    # (in the following exercises you will create your own run_files)
    trec_retrieved = dict()  # query_id -> [docid1, docid2, ...]
    with open(run_file, 'r') as run:
        for line in run:
            (qid, q0, doc_id, rank, score, tag) = line.strip().split()
            if qid not in trec_retrieved:
                trec_retrieved[qid] = []
            trec_retrieved[qid].append(doc_id)
    return trec_retrieved


def read_eval_files(qrels_file: os.PathLike, run_file: os.PathLike) -> typing.Tuple[dict, dict]:
    return read_qrels_file(qrels_file), read_run_file(run_file)


def make_trec_run(es: elasticsearch.Elasticsearch, topics_file_name: os.PathLike, run_file_name: os.PathLike, index_name="genomics", k_docs=10, terms_frac=0.2):
    with open(run_file_name, 'w') as run_file:
        with open(topics_file_name, 'r') as test_queries:
            q_index = 0
            for line in test_queries:
                (qid, query) = line.strip().split('\t')
                search_type = "dfs_query_then_fetch"
                body = {
                    "query": {
                        "match": {'title-abstract': query}
                    },
                    "size": 1000
                }
                print(f"Index name {index_name}")
                response = es.search(index=index_name, search_type=search_type, body=body)
                enhanced_query = pseudo_relevance.pseudo_rel(es, query, response, k_docs, terms_frac, q_index)
                print(query)
                print("--------")
                print(enhanced_query)
                print("_________________")
                body = {
                    "query": {
                        "match": {'title-abstract': enhanced_query}
                    },
                    "size": 1000
                }
                response = es.search(index=index_name, search_type=search_type, body=body)
                for i, hit in enumerate(response['hits']['hits']):
                    run_file.write(f"{qid} Q0 {hit['_source']['PMID']} {i} {hit['_score']} cj_search\n")
                output = evaluation.trec_eval_to_str('data01/FIR-s05-training-qrels.txt', run_file_name)
                with open(f"eval_{run_file_name}", "wt") as f:
                    f.write(output)


# Probably this one should be used
def make_trec_run2(es: elasticsearch.Elasticsearch, topics_file_name: os.PathLike, run_file_name: os.PathLike, index_name="genomics", run_name="test", field="title-abstract"):
    # run_file_name = run_file_name.replace("[", "").replace("]", "").replace("'", "")
    with open(run_file_name, 'w') as run_file:
        with open(topics_file_name, 'r') as test_queries:
            for line in test_queries:
                (qid, query) = line.strip().split('\t')
                search_type = "dfs_query_then_fetch"
                body = {
                    "query": {
                        "match": {field: query}
                    },
                    "size": 1000
                }
                print(f"Index name {index_name}")
                response = es.search(index=index_name, search_type=search_type, body=body)
                for i, hit in enumerate(response['hits']['hits']):
                    run_file.write(f"{qid} {run_name} {hit['_source']['PMID']} {i} {hit['_score']} cj_search2\n")
    output = evaluation.trec_eval_to_str('data01/FIR-s05-training-qrels.txt', run_file_name)
    with open(f"eval_{run_file_name}", "wt") as f:
        f.write(output)
