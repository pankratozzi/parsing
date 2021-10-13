import scrapy
from scrapy.http import HtmlResponse
from books.items import BooksItem
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions as se


class Book24Spider(scrapy.Spider):
    name = 'book24'
    allowed_domains = ['book24.ru']
    start_urls = ['https://book24.ru/search/?q=python',
                  'https://book24.ru/search/?q=data%20science']

    def parse(self, response: HtmlResponse):
        next_page = self.get_next_page_url(response.url)
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
        links = response.xpath("//div[@class='product-card__content']/a/@href").getall()
        for link in links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        name = response.xpath("//h1/text()").get()
        link = response.url
        authors = response.xpath("//ul/li[1]/div/div[@class='product-characteristic__value']//text()").getall()
        price = response.xpath("//span[contains(@class, 'price-old')]/text()").get()
        price_disc = response.xpath("//div[contains(@class, 'main-price')]/span[contains(@class, 'price__price')]/text()").get()
        rating = response.xpath("//span[@class='rating-widget__main-text']/text()").get()
        item = BooksItem(name=name, link=link, authors=authors, price=price, price_disc=price_disc,
                         rating=rating)
        yield item

    @staticmethod
    def get_next_page_url(url):
        chromedriver = '/usr/local/bin/chromedriver'
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(executable_path=chromedriver, options=chrome_options)
        driver.get(url)
        try:
            next_page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH,
                                                                                    "//li[contains(@class, '_next')]/a"))).get_attribute('href')
        except se.TimeoutException:
            next_page = None

        return next_page
