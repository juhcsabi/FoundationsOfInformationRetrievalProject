from elasticsearch_dsl import Search, Q


def read_qrels_file(qrels_file):  # reads the content of he qrels file
    trec_relevant = dict()  # query_id -> set([docid1, docid2, ...])
    with open(qrels_file, 'r') as qrels:
        for line in qrels:
            (qid, q0, doc_id, rel) = line.strip().split()
            if qid not in trec_relevant:
                trec_relevant[qid] = set()
            if rel == "1":
                trec_relevant[qid].add(doc_id)
    return trec_relevant


def read_run_file(run_file):
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


def read_eval_files(qrels_file, run_file):
    return read_qrels_file(qrels_file), read_run_file(run_file)


# def make_trec_run(es, topics_file_name, run_file_name, index_name="genomics"):
#     with open(run_file_name, 'w') as run_file:
#         with open(topics_file_name, 'r') as test_queries:
#             for line in test_queries:
#                 (qid, query) = line.strip().split('\t')
#                 s = Search(using=es, index=index_name)
#                 s = s.extra(size=1000)

#                 q = Q("multi_match", query=query, fields=['TI', 'AB'])

#                 response = s.query(q).execute()
#                 for i, hit in enumerate(response['hits']['hits']):
#                     run_file.write(f"{qid} Q0 {hit['_source']['PMID']} {i} {hit['_score']} cj_search\n")

                
def make_trec_run(es, topics_file_name, run_file_name, index_name="genomics", run_name="test", pseudo_relevance=False):
    with open(run_file_name, 'w') as run_file:
        with open(topics_file_name, 'r') as test_queries:
            for line in test_queries:
                (qid, query) = line.strip().split('\t')
                s = Search(using=es, index=index_name)
                s = s.extra(size=1000)
                
                q = Q("multi_match", query=query, fields=['TI', 'AB'])

                response = s.query(q).execute()
                
                if pseudo_relevance:
                    # PSEUDOPRELEVANCE HERE:
                    # Call trec_run(pseudo_relevance=False) based on the new query
                    pass
                
                for i, hit in enumerate(response['hits']['hits']):
                    run_file.write(f"{qid} Q0 {hit['_source']['PMID']} {i} {hit['_score']} cj_search\n")



# Probably this one should be used
def make_trec_run2(es, topics_file_name, run_file_name, index_name="genomics", run_name="test", field="title-abstract"):
    with open(run_file_name, 'w') as run_file:
        with open(topics_file_name, 'r') as test_queries:
            for line in test_queries:
                print("test")
                (qid, query) = line.strip().split('\t')
                search_type = "dfs_query_then_fetch"
                body = {
                    "query": {
                        "match": {field: query}
                    },
                    "size": 1000
                }
                response = es.search(index=index_name, search_type=search_type, body=body)
                print(response)
                for i, hit in enumerate(response['hits']['hits']):
                    run_file.write(f"{qid} {run_name} {hit['_source']['PMID']} {i} {hit['_score']} cj_search2\n")
