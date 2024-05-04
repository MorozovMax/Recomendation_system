from flask import Flask, render_template, request
from elasticsearch import Elasticsearch
import pymongo
import random
from Trends import *

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")
client = pymongo.MongoClient()
db = client["neuroinformatics_data"]


def get_max_page(query, size=10):
    # Выполняем запрос для подсчета общего количества результатов
    count_results = es.count(index='neuroinformatics_data',
                             body={'query': {'multi_match': {'query': query, 'fields': ["title", "abstract"]}}})
    total_hits = count_results['count']

    # Вычисляем количество страниц
    max_page = -(-total_hits // size)  # округление вверх

    return max_page

@app.route('/')
def index():
    collection = db["topics"]
    keywords_list = list(collection.find())
    # Создаем словарь с цветами для каждой группы
    group_colors = {}
    for keyword in keywords_list:
        group_id = keyword.get('topic_id')
        if group_id not in group_colors:
            # Генерируем случайный цвет для группы
            group_colors[group_id] = "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Ограничиваем количество ключевых слов в каждой группе
    MAX_KEYWORDS_PER_GROUP = 3
    limited_keywords_list = []
    for keyword in keywords_list:
        topic_id = keyword.get('topic_id')
        topic = keyword.get('topic', {})
        limited_topic = {key: topic[key] for key in list(topic)[:MAX_KEYWORDS_PER_GROUP]}
        limited_keyword = {'topic_id': topic_id, 'topic': limited_topic}
        limited_keywords_list.append(limited_keyword)
    trends_list = find_year_trends(client)
    return render_template('index.html', keywords_list=limited_keywords_list, group_colors=group_colors, trends_list=trends_list)

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    page = request.args.get('page', default=1, type=int)  # Получаем номер текущей страницы
    size = 10  # Размер страницы - количество результатов на странице
    from_ = (page - 1) * size  # Смещение для запроса к Elasticsearch
    results = es.search(index='neuroinformatics_data',
                        body={'query':
                                  {'multi_match':
                                      {
                                       "query" : query,
                                      "fields" : ["title", "snippet"]
                                      }
                                  },
                            'sort': [{'created': {'order': 'desc'}}],
                            'from_' : from_,
                            'size' : size
                              }
                        )
    # Выполняем запрос для подсчета общего количества результатов
    count_results = es.count(index='neuroinformatics_data',
                             body={'query': {'multi_match': {'query': query, 'fields': ["title", "abstract"]}}})
    total_hits = count_results['count']

    # Вычисляем количество страниц
    max_page = -(-total_hits // size)  # округление вверх
    return render_template('results.html', results=results['hits']['hits'], page=page, max_page=max_page)

if __name__ == '__main__':
    app.run(debug=True)
