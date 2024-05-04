import datetime
import pprint
import sys
import pymongo
from elasticsearch import Elasticsearch
from elastic import Elastic_search_API
from Model.Model import preprocessing
import faulthandler



def topic_words_friq(client, start_date, end_date):
    database = client["neuroinformatics_data"]
    topics = database["topics"]
    articles = database["articles"]
    all_articles = list(articles.find({
        "created" : {
            "$gte" : start_date,
            "$lte" : end_date
        }
    }))
    all_topics = list(topics.find())
    result = []
    for topic in all_topics:
        tmp = {}
        for key in topic["topic"].keys():
            tmp[f"{key}"] = count_topic_word_friq(key, all_articles)
        result.append({
            "topic_id" : topic["topic_id"],
            "topic" : tmp
        })
    min_freq = sys.maxsize
    for elem in result:
        for key in elem["topic"].keys():
            if elem["topic"][f'{key}'] < min_freq and elem["topic"][f'{key}']!=0.0:
                min_freq = elem["topic"][f'{key}']
    for elem in result:
        for key in elem["topic"].keys():
            if elem["topic"][f'{key}'] == 0.0:
                elem["topic"][f'{key}'] = min_freq
    return result

def count_topic_word_friq(word, all_articles):
    sum = 0
    for article in all_articles:
        #print(article)
        try:
            sum += int(article["articles"][f"{word}"])
        except:
            pass
    return sum/len(all_articles)

def find_year_trends(client):
    date_now = str(datetime.datetime.now()).split(" ")[0]

    date_year_ago = date_now.split("-")
    date_year_ago[0] = str(int(date_year_ago[0]) - 1)
    date_year_ago = "-".join(date_year_ago)

    date_2years_ago = date_now.split("-")
    date_2years_ago[0] = str(int(date_2years_ago[0]) - 2)
    date_2years_ago = "-".join(date_2years_ago)

    topic_words_friq_now = topic_words_friq(client, date_year_ago, date_now)
    topic_words_friq_year_ago = topic_words_friq(client, date_2years_ago,date_year_ago)
    result = []
    for elem1, elem2 in zip(topic_words_friq_now, topic_words_friq_year_ago):
        tmp = {}
        for key in elem1["topic"].keys():
            try:
                tmp[f'{key}'] = elem1["topic"][f'{key}'] / elem2["topic"][f'{key}']
            except ZeroDivisionError:
                tmp[f'{key}'] = elem1["topic"][f'{key}']
        result.append({
            "topic_id": elem1["topic_id"],
            "topic" : tmp
        })



    database = client["neuroinformatics_data"]
    collection = database["topics"]
    topics_important_data = list(collection.find())


    avg = 0
    keyw_counts = 0
    for elem1, elem2 in zip(result, topics_important_data):
        for key1, key2 in zip(elem1["topic"].keys(), elem2["topic"].keys()):
            #elem1["topic"][f"{key1}"] *= float(elem2["topic"][f"{key2}"])
            avg += elem1["topic"][f"{key1}"]
        keyw_counts += len(elem1["topic"].keys())
    avg = avg / keyw_counts
    res = []

    for elem in result:
        tmp = {}
        for key in elem["topic"].keys():
            if elem["topic"][f'{key}'] > avg:
                tmp[f'{key}'] = elem["topic"][f'{key}']
        res.append({
            "topic_id": elem["topic_id"],
            "topic" : tmp
        })


    return res

client = pymongo.MongoClient()
find_year_trends(client)
