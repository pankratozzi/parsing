from itemadapter import ItemAdapter
from pymongo import MongoClient
import re


class BooksPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.books

    def process_item(self, item, spider):

        if spider.name == 'labirint':
            item['name'], item['price'], item['price_disc'], item['authors'], item['rating'] = \
            self.process_labirint(item['name'], item['price'], item['price_disc'], item['authors'],
                                  item['rating'])
        elif spider.name == 'book24':
            item['name'], item['price'], item['price_disc'], item['authors'], item['rating'] = \
                self.process_book24(item['name'], item['price'], item['price_disc'], item['authors'],
                                      item['rating'])
        collection = self.db[spider.name]
        collection.insert_one(item)
        return item

    def process_labirint(self, name, price, price_disc, authors, rating):
        name = ''.join(name.split(':')[1:])
        authors = ', '.join(authors)
        try:
            price = float(price)
        except:
            pass
        try:
            price_disc = float(price_disc)
        except:
            pass
        try:
            rating = float(rating)
        except:
            pass
        return name, price, price_disc, authors, rating

    def process_book24(self, name, price, price_disc, authors, rating):
        if price is None and price_disc is not None:
            price, price_disc = price_disc, price
        if price is not None:
            price = price.replace(u'\xa0', u'')
            try:
                price = re.search('\d+', price).group(0)
                price = float(price)
            except:
                pass
        if price_disc is not None:
            price_disc = price_disc.replace(u'\xa0', u'')
            try:
                price_disc = re.search('\d+', price_disc).group(0)
                price_disc = float(price_disc)
            except:
                pass
        try:
            rating = float(rating.replace(' ', '').replace(',', '.'))
        except:
            pass
        if ':' in name:
            name = ''.join(name.split(':')[1:])
        authors = ''.join(authors)

        return name, price, price_disc, authors, rating
