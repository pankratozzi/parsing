from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from instagram.spiders.instaspawn import InstaspawnSpider
from instagram import settings

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    users = input('Enter user names to parse using space: ').split()

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(InstaspawnSpider, users_for_parse=users)

    process.start()
