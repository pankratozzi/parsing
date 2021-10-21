import scrapy
from scrapy.http import HtmlResponse
from books.items import BooksItem


class LabirintSpider(scrapy.Spider):
    name = 'labirint'
    allowed_domains = ['labirint.ru']
    start_urls = ['https://www.labirint.ru/search/python/?stype=0',
                  'https://www.labirint.ru/search/data%20science/?stype=0']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//div[@class='pagination-next']/a/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        links = response.xpath("//a[@class='product-title-link']/@href").getall()
        for link in links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        name = response.xpath("//h1/text()").get()
        link = response.url
        authors = response.xpath("//div[@class='authors'][1]//a/text()").getall()
        price = response.xpath("//span[@class='buying-priceold-val-number']/text()").get()
        price_disc = response.xpath("//span[@class='buying-pricenew-val-number']/text()").get()  # check if None
        rating = response.xpath("//div[@id='rate']/text()").get()
        item = BooksItem(name=name, link=link, authors=authors, price=price, price_disc=price_disc,
                         rating=rating)
        yield item
