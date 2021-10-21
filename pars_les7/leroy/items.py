import scrapy
from itemloaders.processors import MapCompose, TakeFirst, Compose, Join
from PIL import Image


def clear_price(value):
    try:
        value = int(value.replace(' ', '').replace('\xa0', ''))
    except:
        return value
    return value


def clear_param_dt(value):
    return value


class LeroyItem(scrapy.Item):
    name = scrapy.Field(output_processor=TakeFirst())
    link = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(clear_price), output_processor=TakeFirst())
    photo = scrapy.Field()
    params_dd = scrapy.Field(input_processor=MapCompose(lambda x: x.replace('\n', '').strip()))
    params_dt = scrapy.Field(input_processor=MapCompose(clear_param_dt))
    params = scrapy.Field()
    _id = scrapy.Field()
