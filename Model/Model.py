import json
import pprint
import time

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import string
import enchant
from elasticsearch import Elasticsearch
from elastic import Elastic_search_API
import re
from gensim import corpora, models, similarities
import matplotlib.pyplot as plt
import pyLDAvis
import pyLDAvis.gensim_models as gensims
import os
from numba import njit
import webbrowser
from multiprocessing import Process, freeze_support


def download_nltk_packages() -> None:
    nltk.download('stopwords')
    nltk.download('omw-1.4')
    nltk.download('punkt')
    nltk.download('wordnet')

def delete_non_english(titles: list[str]) -> list[str]:
    d = enchant.Dict("en")

    titles = [" ".join(w.lower() for w in title.split(" ") \
                       if d.check(w)) for title in titles]
    return titles
def data_lowercase(titles: list[str]) -> list[str]:
    titles = [" ".join(re.sub('\W+','',word.lower()) for word in title.split(" ")) for title in titles]
    return titles

def delete_stop_words(titles: list[str]) -> list[str]:
    titles = [" ".join(word for word in title.split(" ") if word not in stopwords.words('english')) for title in titles]
    return titles
def lemmatization(titles: list[str]) -> list[str]:
    lemmatizer = WordNetLemmatizer()
    titles = [" ".join(lemmatizer.lemmatize(word) for word in title.split(" ")) for title in titles]
    return titles

def delete_bad_titles(titles: list[str]) -> list[str]:
    titles = [title for title in titles if len(title.split(" ")) > 2]
    return titles

def delete_bad_words(titles: list[str]) -> list[str]:
    titles = [" ".join(word for word in title.split(" ") if len(word) > 3 and not word.isdigit()) for title in titles]
    return titles

# preprocessing abstracts
def preprocessing(data: list[dict]) -> list[dict]:

    abstracts = [d["abstract"] for d in data]

    abstracts = [abstract.translate(str.maketrans('', '', string.punctuation)) for abstract in abstracts] #delete punctuation
    abstracts = data_lowercase(abstracts) # data to lower case
    abstracts = delete_stop_words(abstracts) # delete stop words
    abstracts = lemmatization(abstracts) # lemmatization
    #abstracts = delete_non_english(abstracts) # delete non english phrases
    #abstracts = delete_bad_titles(abstracts) # delete bad data
    abstracts = delete_bad_words(abstracts)  # delete bad words(digit or words with len<3)
    result = []
    for d, abstract in zip(data, abstracts):
        d["abstract"] = abstract
        result.append(d)

    for id,elem in enumerate(result):
        if len(elem["abstract"].split(" ")) < 2:
            result.pop(id)

    for elem in result:
        elem["abstract"] = word_tokenize(elem["abstract"])

    return result


def model_train(data):
    l = [elem["abstract"] for elem in data]
    id2word = corpora.Dictionary(l)
    id2word.filter_extremes(no_below=1, no_above=0.8)
    corpus = [id2word.doc2bow(text) for text in l]
    lda_model = models.LdaModel(corpus=corpus,
                                           id2word=id2word,
                                           num_topics=4,
                                           random_state=100,
                                           update_every=1,
                                           chunksize=100,
                                           passes=10,
                                           alpha='auto',
                                           per_word_topics=True)


    lda_model.save("lda.model")
    vis = pyLDAvis.gensim_models.prepare(lda_model, corpus, id2word)
    pyLDAvis.save_html(vis, "hdpvis.html")
    vis_path = os.path.relpath("hdpvis.html")
    webbrowser.open('file://' + os.getcwd() + '/' + vis_path, new=2)

def find_num_topics(data):
    l = [elem["abstract"] for elem in data]
    id2word = corpora.Dictionary(l)
    id2word.filter_extremes(no_below=1, no_above=0.8)
    corpus = [id2word.doc2bow(text) for text in l]

    models_list = []

    for i in range(1, 15):
        lda_model = models.LdaModel(corpus=corpus,
                                    id2word=id2word,
                                    num_topics=i,
                                    random_state=100,
                                    update_every=1,
                                    chunksize=100,
                                    passes=10,
                                    alpha='auto',
                                    per_word_topics=True)
        models_list.append(lda_model)

    x = np.array(range(1,15))
    y = [models.coherencemodel.CoherenceModel(model=model, texts=l, dictionary=id2word, coherence='u_mass').get_coherence() for model in models_list]
    plt.plot(x, y, "ro")
    plt.xlabel("num_topics")
    plt.ylabel("umass")
    plt.show()


#es = Elasticsearch("http://localhost:9200")
#data = Elastic_search_API.get_all_data(es, "neuroinformatics_data")
#preprocessed_data = preprocessing(data)
#odel_train(preprocessed_data)

