import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def parse_springer_magazine():
    params = {
        'site':'https://link.springer.com',
        'page':'1',
        'query':'neuroinformatics',
        'language':'En'
    }
    results = []
    end_flag = True
    while(end_flag):
        if int(params['page']) == 50:
            end_flag = False
        url = (params['site']
               + '/search?new-search=true'
               + '&query=' + params['query']
               + '&content-type=article'
               + '&language=' + params['language']
               + '&page=' + params['page']
               )

        response = requests.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        data = soup.select('[class~=app-card-open]')

        for item in data:
            try:
                title = item.select_one('h3').text.strip()
            except:
                title = None
            try:
                link = item.select_one('a')['href']
            except:
                link = None
            try:
                authors = item.select_one('[data-test="authors"]').text.strip()
            except:
                authors = None
            try:
                snippet = item.select_one('.app-listing__intro p').text.strip()
            except:
                snippet = None
            try:
                abstract_response = requests.get(link)
            except:
                abstract_response = requests.get(params['site'] + link)
            abstract_data = BeautifulSoup(abstract_response.content, 'html.parser')
            try:
                abstract = abstract_data.select_one('.c-article-section__content p').text.strip()
            except:
                abstract = None

            try:
                #created = abstract_data.select_one('.c-bibliographic-information__value time').text.rstrip()
                created = item.select_one('[data-test="published"]').text.strip()
                created = datetime.strptime(created, "%d %B %Y")
            except:
                created = None

            results.append({
                'title': title,
                'snippet': snippet,
                'link': params['site'] + link,
                'abstract': abstract,
                'authors': authors,
                'created': created
            })

        print(f"Page {params['page']} parsed from {url}")
        new_page = int(params['page']) + 1
        params['page'] = str(new_page)

    return results


pd.DataFrame(data=parse_springer_magazine()) \
    .to_csv("elastic/springer_organic_results.csv", encoding="utf-8", index=False)
