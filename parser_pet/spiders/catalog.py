
import scrapy

class CatalogSpider(scrapy.Spider):
    name = "catalog"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com"]

    pages_count = 5

    def start_requests(self):
        for page in range(1, 1 + self.pages_count):
            url = f'https://books.toscrape.com/catalogue/page-{page}.html'
            yield scrapy.Request(url, callback=self.parse_pages)

    def parse_pages(self, response, **kwargs):
        for href in response.css('.image_container a::attr("href")').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response, **kwargs):

        rating_mapping = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }
         
        for item in response.css('.star-rating'):
            rating_class = item.css('::attr(class)').get()
            rating_value = rating_class.split()[-1]  # Получаем последнее слово из класса
            rating_number = rating_mapping.get(rating_value)

        item = {
            'name': response.css('.product_main h1::text').extract_first('').strip(),
            'category': response.css('.breadcrumb a::text')[-2].get(),
            'price': response.css('.price_color::text').extract_first('').strip(),
            'rating': rating_number,
            'stock': response.css('.instock.availability::text')[1].extract().replace("\n", "").strip()
        }
        yield item