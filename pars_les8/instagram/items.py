# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstagramItem(scrapy.Item):
    main_username = scrapy.Field()
    main_user_id = scrapy.Field()
    username = scrapy.Field()
    user_id = scrapy.Field()
    user_avatar = scrapy.Field()
    follow_flag = scrapy.Field()
    _id = scrapy.Field()
