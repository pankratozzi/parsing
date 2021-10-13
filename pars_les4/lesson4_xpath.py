from pprint import pprint
import requests
from lxml import html
from pymongo import MongoClient
import datetime
import re


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
                self.collection.update_one({'link': data['link']}, {'$set': data}, upsert=True)
            except Exception as exc:
                print(f'Cannot add doc # {idx}, reason: {exc}')
                continue

    def save_to_DataFrame(self):
        return pd.DataFrame(self.collection.find({}))

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

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}

client = MongoClient('127.0.0.1', 27017)
db = client['news']
collection = db.news

date_format = '%Y-%m-%dT%H:%M:%S'
months_vocab = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06',
                'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11',
                'декабря': '12'}

mongo_collection = MongoCollectionJob(collection)

def get_lenta():
    lenta = 'https://lenta.ru'
    response = requests.get(lenta, headers=headers)
    collection = []
    if response.ok:
        dom = html.fromstring(response.text)
        items = dom.xpath("//div[contains(@class, 'b-yellow-box__wrap')]/div/a")
        for item in items:
            news_vocab = {}
            news_vocab['title'] = ''.join(item.xpath(".//text()")).replace(u'\xa0', u' ')
            news_vocab['link'] = lenta + item.xpath("./@href")[0]
            local_response = requests.get(news_vocab.get('link'))
            if local_response.ok:
                if not ('extlink' in news_vocab['link'].lower()):
                    local_dom = html.fromstring(local_response.text)
                    timestamp = local_dom.xpath("//time[@class='g-date']/@datetime")[0]
                    news_vocab['datetime'] = datetime.datetime.strptime(timestamp.split('+')[0], date_format)
                    source = local_dom.xpath("//p[contains(@class, 'b-topic')]/a/span/text()")
                    news_vocab['source'] = source[0] + '/lenta.ru' if len(source) > 0 else 'lenta.ru'
                else:
                    news_vocab['datetime'], news_vocab['source'] = 'external_link', 'lenta.ru'
            else:
                print(f'{response.status_code}')
                continue
            collection.append(news_vocab)
    return collection


def get_mail():
    news_mail_link = 'https://news.mail.ru/'
    response = requests.get(news_mail_link, headers=headers)
    if response.ok:
        dom = html.fromstring(response.text)
        links = dom.xpath("//div[contains(@class, 'daynews__item')]/a/@href | //li/a/@href")
        collection = []
        for link in links:
            new_vocab = {}
            new_vocab['link'] = link
            local_response = requests.get(link, headers=headers)
            if local_response.ok:
                local_dom = html.fromstring(local_response.text)
                item = local_dom.xpath("//span[@class='breadcrumbs__item']")[0]
                # timestamp = local_dom.xpath("//span[@class='breadcrumbs__item']//span/@datetime")[0]
                timestamp = item.xpath(".//span/@datetime")[0]
                new_vocab['datetime'] = datetime.datetime.strptime(timestamp.split('+')[0], date_format)
                new_vocab['source'] = local_dom.xpath("//a[contains(@class, 'breadcrumbs__link')]/span/text()")[0]
                #new_vocab['source'] = item.xpath(".//a/span/text()")
                #new_vocab['source'] = local_dom.xpath("//span[@class='breadcrumbs__item']//a/span/text()")
                new_vocab['title'] = local_dom.xpath("//h1/text()")[0]
                collection.append(new_vocab)
            else:
                print(local_response.status_code)
                continue
        return collection
    else:
        print(response.status_code)
        return None

def get_yandex():
    yandex_link = 'https://yandex.ru/news/'
    response = requests.get(yandex_link, headers=headers)
    collection = []
    if response.ok:
        response.encoding = 'utf-8'
        dom = html.fromstring(response.text)
        items = dom.xpath("//article[contains(@class, 'mg-card')]")
        for item in items:
            new_vocab = {}
            new_vocab['title'] = item.xpath(".//h2/text()")[0].replace(u'\xa0', u' ')
            new_vocab['link'] = item.xpath(".//a[@class='mg-card__link']/@href")[0]
            new_vocab['source'] = item.xpath("//span[contains(@class, 'source__source')]/a/text()")[0]
            timestamp = item.xpath(".//span[contains(@class, 'source__time')]/text()")[0]
            if timestamp.lower().find('вчера') != -1:
                try:
                    end_stamp = timestamp.split()[-1]
                except IndexError:
                    end_stamp = '00:00'
                yesterday = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
                timestamp = yesterday + 'T' + end_stamp + ':00'
                new_vocab['datetime'] = datetime.datetime.strptime(timestamp, date_format)
            elif re.match(r'\d{2}:\d{2}', timestamp):
                current_day = datetime.datetime.today().strftime('%Y-%m-%d') + 'T'
                new_vocab['datetime'] = datetime.datetime.strptime(current_day + timestamp + ':00', date_format)
            elif re.match(r'\d+', timestamp):
                timestamp = '2021-' + months_vocab.get(timestamp.split()[1].replace(' ', '').lower()) + '-' \
                            + timestamp.split()[0] + 'T' + '00:00:00'
                new_vocab['datetime'] = datetime.datetime.strptime(timestamp, date_format)
            else:
                new_vocab['datetime'] = None
            collection.append(new_vocab)
        return collection
    else:
        print(response.status_code)
        return None


if __name__ == '__main__':
    mongo_collection.clear_collection()

    lenta_collection = get_lenta()
    mongo_collection.insert_docs(lenta_collection)

    mail_collection = get_mail()
    mongo_collection.insert_docs(mail_collection)

    yandex_collection = get_yandex()
    mongo_collection.insert_docs(yandex_collection)

    print(mongo_collection, '\n', f'The size of mongo: {len(mongo_collection)}')
