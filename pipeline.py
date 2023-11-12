import json
import os
import pprint
from collections import defaultdict

import elasticsearch
import elasticsearch_dsl
import queries
import evaluation
import trec_files
from elasticsearch.exceptions import NotFoundError

def get_max_word_length() -> int:
    lengths = defaultdict(int)
    #words = defaultdict(list)
    with open("data01/FIR-s05-medline.json") as f:
        for i, line in enumerate(f.readlines()):
            #if i % 10000:
                #print(i)
            line_dict = json.loads(line)
            if "AB" in line_dict:
                for word in line_dict["AB"].split(" "):
                    lengths[len(word)] += 1
                    #words[len(word)].append(word)
            if "TI" in line_dict:
                for word in line_dict["TI"].split(" "):
                    lengths[len(word)] += 1
                    #words[len(word)].append(word)
    #pprint.pprint(sorted(lengths.items()), indent=4)
    #pprint.pprint(words[max(words.keys())], indent=4)
    return max(lengths.keys())

def get_tokenizer_parameters() -> dict:
    max_word_length = get_max_word_length()
    return {"classic": [
            {
                "param_name": "max_token_length",
                "range_start": 2,
                "range_end": 20,
                "step": 4
            }]}
    return {
        "ngram": [
            {
                "param_name": "min_gram",
                "values": [3, 5, 8]
            },
            {
                "param_name": "max_gram",
                "values": [4, 6, 9]
            },
            {
                "param_name": "token_chars",
                "values": [[], ["letter"], ["letter", "digit"], ["letter", "digit", "symbol"]]
            }
        ],
        "keyword": [
        ],
        "standard": [
            {
                "param_name": "max_token_length",
                "range_start": 1,
                "range_end": max_word_length,
                "step": 10
            }
        ],
        "whitespace": [
            {
                "param_name": "max_token_length",
                "range_start": 1,
                "range_end": max_word_length,
                "step": 10
            }
        ],
        "letter": [],
        "lowercase": [],
        "classic": [
            {
                "param_name": "max_token_length",
                "range_start": 1,
                "range_end": max_word_length,
                "step": 10
            }
        ],


    }


def combine_parameters(es, body, parameters, parameter_names, i, parameter_count, name, tokenizer_type, params):
    name = name.replace(",", "").replace("'", "").replace("\\", "").replace("[", "").replace("]", "").replace(" ", "")
    if i == parameter_count:
        print(f"Indexing {tokenizer_type} - {name}")
        body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        f"{name}_analyzer": {
                            "type": "custom",
                            "tokenizer": f"{name}_tokenizer",
                            "filter": ["stemmer", "lowercase"]
                        }
                    },
                    "tokenizer": {
                        f"{name}_tokenizer": {
                            "type": tokenizer_type
                        }
                    },
                    "filter": {
                        "stemmer": {
                            "type": "stemmer",
                            "name": "english"
                        }
                    }
                }
            },
             "mappings": {
                "properties": {
                    "AB": {
                        "type": "text",
                        "copy_to": "title-abstract",
                        "similarity": "boolean"
                    },
                    "TI": {
                        "type": "text",
                        "copy_to": "title-abstract",
                        "similarity": "boolean"
                    },
                    "title-abstract": {  # compound field
                        "type": "text",
                        "similarity": "boolean",
                        "analyzer": f"{name}_analyzer"
                    }
                }
            }
        }
        for parameter_name in params:
            if f"{name}_tokenizer" not in body["settings"]["analysis"]["tokenizer"]:
                body["settings"]["analysis"]["tokenizer"][f"{name}_tokenizer"] = {}
            body["settings"]["analysis"]["tokenizer"][f"{name}_tokenizer"][parameter_name] = params[parameter_name]
        pprint.pprint(body, indent=4)
        try:
            es.indices.get(index=name)
        except NotFoundError:
            queries.index_documents(es, 'data01/FIR-s05-medline.json', name, body)
        trec_files.make_trec_run2(es, "data01/FIR-s05-training-queries-simple.txt", run_file_name=f"{name}.run", index_name=name, run_name=name, field="title-abstract")
        return
    parameter_name = parameter_names[i]
    if "range_start" in parameters[i]:
        if parameters[i]["range_start"] < parameters[i]["range_end"]:
            generator = range(parameters[i]["range_start"], parameters[i]["range_end"], parameters[i]["step"])
        else:
            return
    else:
        generator = parameters[i]["values"]
    for item in generator:
        if parameter_name == "max_gram" and (item - params["min_gram"] > 1 or item < params["min_gram"]):
            continue
        new_name = name + f"_{item}"
        params[parameter_name] = item
        combine_parameters(es, body, parameters, parameter_names, i + 1, parameter_count, new_name, tokenizer_type, params)



def base():
    es = queries.start_elastic_search()
    queries.index_documents(es, 'data01/FIR-s05-medline.json', f'genomics-base')
    trec_files.make_trec_run(es, 'data01/FIR-s05-training-queries-simple.txt', 'baseline.run', "genomics-base")

def main():
    es = queries.start_elastic_search()
    # mapping1 = es.indices.get_mapping(index='keyword_1')
    # mapping2 = es.indices.get_mapping(index='keyword_71')
    # print(mapping1)
    # print(mapping2)
    # input()
    # indices = es.indices.get_alias().keys()

    # # Delete each index
    # for index in indices:
    #     es.indices.delete(index=index)
    parameters = get_tokenizer_parameters()
    for tokenizer_type in parameters:

        body = {
            "settings": {
                "analysis": {
                    "tokenizer": {
                    }
                }
            }
        }
        params={}
        combine_parameters(es, body, parameters[tokenizer_type], [param["param_name"] for param in parameters[tokenizer_type]], 0, len(parameters[tokenizer_type]), tokenizer_type, tokenizer_type, params)


def evaluate_run_files():
    for root, dirs, files in os.walk():
        for file in files:
            if ".run" in file:
                output = evaluation.trec_eval_to_str('data01/FIR-s05-training-qrels.txt', os.path.join(root, file))
                with open(f"eval_{file}", "wt") as f:
                    f.write(output)


#main()

#trec_files.make_trec_run(queries.start_elastic_search(), "data01/FIR-s05-training-queries-simple.txt", "test.run", "classic_11")
evaluation.t_test_outputs("data01/FIR-s05-training-qrels.txt", "baseline.run", "results/classic_11.run")