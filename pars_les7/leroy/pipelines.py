import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from PIL import Image
from pymongo import MongoClient


class LeroyPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.leroy

    def process_item(self, item, spider):
        if spider.name == 'leroyscraper':
            item['params'] = dict(zip(item['params_dt'], item['params_dd']))
            del item['params_dt']
            del item['params_dd']
        collection = self.db[spider.name]
        collection.insert_one(item)
        print()
        return item


class LeroyImgPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photo']:
            for img in item['photo']:
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        item['photo'] = [itm[1] for itm in results if itm[0]]
        for photo in item['photo']:
            path = photo['path']
            image = Image.open('photos/' + path)
            image = image.resize((300, 300), Image.ANTIALIAS)
            image.save('photos/' + path)
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        image_guid = request.url.split('/')[-1]
        img_path = item['link'].split('-')[-1]
        return f'{img_path}{image_guid}'
