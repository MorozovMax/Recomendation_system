import datetime
import pprint

import pymongo
from gensim import corpora, models
from elasticsearch import Elasticsearch
from elastic import Elastic_search_API
from Model.Model import preprocessing
import re

def load_word_friq(data, client):
    database = client["neuroinformatics_data"]
    database.drop_collection("articles")
    collection = database["articles"]
    l = [elem["abstract"] for elem in data]
    id2word = corpora.Dictionary(l)
    id2word.filter_extremes(no_below=1, no_above=0.8)
    corpus = [id2word.doc2bow(text) for text in l]
    data_to_load = [{
        "_id_elastic" : elastic_elem["_id"],
        "articles" : dict((id2word[id], freq) for id, freq in cp),
        "created" : elastic_elem["created"]
    } for cp,elastic_elem in zip(corpus, data)]
    collection.insert_many(data_to_load)
    print(database.list_collection_names())

def load_current_topics(model, client):
    database = client["neuroinformatics_data"]
    database.drop_collection("topics")
    collection = database["topics"]
    data_to_load = []
    for i in range(0, model.num_topics):
        topic = str(model.print_topic(i)).split(" + ")
        topic = [list(reversed(elem.split("*"))) for elem in topic]
        topic_dict = dict([re.sub('\W+','',elem[0]),elem[1]]for elem in topic)
        tmp_dict = {
            "topic_id" : i,
            "topic" : topic_dict
        }
        data_to_load.append(tmp_dict)

    collection.insert_many(data_to_load)
    print(database.list_collection_names())

#client = pymongo.MongoClient()
#model = models.LdaModel.load(("../Model/lda.model"))
#load_current_topics(model, client)