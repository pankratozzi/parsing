# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BooksItem(scrapy.Item):
    name = scrapy.Field()
    authors = scrapy.Field()
    link = scrapy.Field()
    price = scrapy.Field()
    price_disc = scrapy.Field()
    rating = scrapy.Field()
    _id = scrapy.Field()
