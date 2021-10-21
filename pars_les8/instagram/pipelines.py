from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
import scrapy


class InstagramPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.instagram

    def process_item(self, item, spider):
        collection = self.db[item.get('main_username')]
        # collection.insert_one(item)
        collection.update_one({'user_id': item['user_id'], 'follow_flag': item['follow_flag']},
                              {'$set': item}, upsert=True)
        return item


class InstaImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['user_avatar']:
            try:
                yield scrapy.Request(item['user_avatar'])
            except Exception as e:
                print(e)

    def item_completed(self, results, item, info):
        item['user_avatar'] = [itm[1] for itm in results if itm[0]]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        if item['follow_flag']:
            image_path = item['main_username'] + '/followed/'
            image_guid = item['username'] + '.jpg'
        else:
            image_path = item['main_username'] + '/follows/'
            image_guid = item['username'] + '.jpg'
        return f'{image_path}{image_guid}'
