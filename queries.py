import elasticsearch
import elasticsearch.helpers
import json


def start_elastic_search():
    return elasticsearch.Elasticsearch(host='localhost')


def read_documents(file_name):
    """
    Returns a generator of documents to be indexed by elastic, read from file_name
    """
    with open(file_name, 'r') as documents:
        for line in documents:
            doc_line = json.loads(line)
            if 'index' in doc_line:
                id = doc_line['index']['_id']
            elif 'PMID' in doc_line:
                doc_line['_id'] = id
                yield doc_line
            else:
                raise ValueError('Woops, error in index file')


def create_index(es, index_name, body=None):
    # delete index when it already exists
    if body is None:
        body = {}
    es.indices.delete(index=index_name, ignore=[400, 404])
    # create the index
    es.indices.create(index=index_name, body=body)


def index_documents(es, collection_file_name, index_name, body=None):
    if body is None:
        body = {}
    create_index(es, index_name, body)
    return elasticsearch.helpers.bulk(
        es,
        read_documents(collection_file_name),
        index=index_name,
        chunk_size=2000,
        request_timeout=30
    )


def number_of_indexed_documents(es, index):
    return es.count(index=index)


def get_number_of_results(es, query):
    search_results = es.search(index='genomics-base', body=query)
    return search_results['hits']['total']['value']


def search_for_str_in_all_fields(es, string, index):
    query = {
        "track_total_hits": True,
        "query": {
            "query_string": {
                "query": string,
                "fields": ["*"]
            }
        }
    }
    return es.search(index=index, body=query)


def search_for_all_str_in_all_fields(es, strings: list, index):
    query = {
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": string,
                            "fields": ["*"]
                        }
                    } for string in strings
                ]
            }
        }
    }
    return es.search(index=index, body=query)

