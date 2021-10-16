from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from leroy.spiders.leroyscraper import LeroyscraperSpider
from leroy import settings


if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    query = input('Enter search query: ')
    process.crawl(LeroyscraperSpider, query=query)
    process.start()
