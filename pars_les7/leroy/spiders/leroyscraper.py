import scrapy
from scrapy.loader import ItemLoader
from scrapy.http import HtmlResponse
from leroy.items import LeroyItem


class LeroyscraperSpider(scrapy.Spider):
    name = 'leroyscraper'
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, query):
        super(LeroyscraperSpider, self).__init__()
        self.start_urls = [f'https://leroymerlin.ru/search/?q={query}']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//a[contains(@aria-label, 'Следующая')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        links = response.xpath("//a[contains(@data-qa, 'product-name')]")
        for link in links:
            yield response.follow(link, callback=self.parse_good)

    def parse_good(self, response: HtmlResponse):
        loader = ItemLoader(item=LeroyItem(), response=response)
        loader.add_value('link', response.url)
        loader.add_xpath('name', '//h1/text()')
        loader.add_xpath('price', "//span[@slot='price']/text()")
        loader.add_xpath('photo', "//source[contains(@media, '1024px')]/@srcset")
        loader.add_xpath('params_dd', "//div[@class='def-list__group']/dd/text()")
        loader.add_xpath('params_dt', "//div[@class='def-list__group']/dt/text()")
        yield loader.load_item()
