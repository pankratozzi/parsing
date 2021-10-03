from lesson2_part1 import parse_hh, parse_sjob
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError as dke
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from pprint import pprint


vacancy = input('Enter vacancy name: ')

url_hunter = 'https://hh.ru/search/vacancy'
params_hunter = {
    'text': vacancy,
    'items_on_page': 20,
    'page': 0
}
# https://superjob.ru/vacancy/search/
url_super = 'https://superjob.ru'
params_super = {
    'keywords': vacancy,
    'page': 1,
    'noGeo': 1
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}

client = MongoClient('127.0.0.1', 27017)
db = client['vacancies']
collection = db.vacancy


class MongoCollectionJob:

    def __init__(self, collection):
        self.collection = collection

    def __len__(self):
        return self.collection.count_documents({})

    def fill_collection(self, list_of_documents):
        for idx, doc in enumerate(list_of_documents, 1):
            try:
                self.collection.insert_one(doc)
            except Exception as exc:
                print(f'Cannot insert doc # {idx}')
                continue

    def insert_docs(self, list_of_documents):
        for idx, data in enumerate(list_of_documents, 1):
            try:
                self.collection.update_one({'Vac_link': data['Vac_link']}, {'$set': data}, upsert=True)
            except Exception as exc:
                print(f'Cannot add doc # {idx}, reason: {exc}')
                continue

    def _convert_currency(self):
        currency_dict = {
            'EUR': 0,
            'KZT': 0,
            'UAH': 0,
            'USD': 0,
            'руб.': 1,
        }
        response = requests.get('https://www.cbr.ru/currency_base/daily/', headers=headers)
        if response.ok:
            soup = bs(response.text, 'html.parser')
            table = soup.find('div', attrs={'class': 'table-wrapper'})
            trs = table.find_all('tr')[1:]
            for tr in trs:
                tds = tr.find_all('td')
                if tds[1].getText() in currency_dict.keys():
                    item = tds[1].getText()
                    if item in ('EUR', 'USD'):
                        currency_dict[item] = float(tds[-1].getText().replace(',', '.'))
                    elif item == 'KZT':
                        currency_dict[item] = float(tds[-1].getText().replace(',', '.')) / 100.
                    elif item == 'UAH':
                        currency_dict[item] = float(tds[-1].getText().replace(',', '.')) / 10.
                else:
                    continue
            return currency_dict
        else:
            return None

    def save_to_DataFrame(self):
        return pd.DataFrame(self.collection.find({}))

    def search_salary(self, salary_value):
        currency_dict = self._convert_currency()
        for key, value in currency_dict.items():
            for doc in self.collection.find({'Currency': key,
                                            '$or': [{'Salary_min': {'$gt': salary_value / value}},
                                            {'Salary_max': {'$gt': salary_value / value}}]}):
                pprint(doc)
                print()

    def __getitem__(self, _id: int):
        all_docs = list(self.collection.find({}))
        return all_docs[_id]

    def clear_collection(self):
        self.collection.delete_many({})

    def __str__(self):
        output = ''
        for doc in self.collection.find({}):
            output += str(doc) + '\n'
        return output


if __name__ == '__main__':

    job_store = MongoCollectionJob(collection)
    hh_dicts = parse_hh(url_hunter, params_hunter, headers, num_pages=5)
    sjob_dicts = parse_sjob(url_super, params_super, headers, num_pages=5)
    params_super['page'], params_hunter['page'] = 1, 0

    hh_new_list = parse_hh(url_hunter, params_hunter, headers, num_pages=6)
    sjob_new_list = parse_sjob(url_super, params_super, headers, num_pages=6)

    job_store.clear_collection()
    job_store.fill_collection(hh_dicts)
    job_store.fill_collection(sjob_dicts)
    print(len(job_store))
    data = job_store.save_to_DataFrame()
    print(f'Dataframe shape: {data.shape}')
    # print(job_store)

    job_store.insert_docs(hh_new_list)
    job_store.insert_docs(sjob_new_list)

    print(f'The size of updated storage is: {len(job_store)}')

    job_store.search_salary(300000.0)

    print('Over')
    print()
