import csv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

def load_data_from_csv(es, file_name):
    with open(file_name, encoding='utf-8') as f:
        index_name = 'neuroinformatics_data'
        mapping = {
            "mappings" :{
                "properties" :{
                    "title" : {"type" : "text"},
                    "link" : {"type" : "text"},
                    "abstract": {"type": "text"},
                    "authors": {"type": "text"},
                    "created": {"type": "date"}
                }
            }
        }
        reader = csv.DictReader(f)
        try:
            es.indices.create(index=index_name, body=mapping)
            print('Index was created.')
        except:
            print('Index already created.')

        for doc_id, doc in enumerate(reader):
            es.index(index=index_name, id=doc_id, document=doc)
            if doc_id % 100 == 0:
                print(f"{doc_id} articles was loaded")


def get_all_data(es, index_name):
    query = {
        "query":{
            "match":{
                "symbols.keyword":"created"
            }
        }
    }
    resp = scan(client=es,
                scroll="1m",
                index=index_name,
                raise_on_error=True,
                preserve_order=False,
                clear_scroll=True
                )
    temp = []
    for hit in resp:
        hit["_source"]["_id"] = hit["_id"]
        temp.append(hit["_source"])
    return  temp

#es = Elasticsearch("http://localhost:9200")
#es.indices.delete(index="neuroinformatics_data",)
#load_data_from_csv(es, "springer_organic_results.csv")