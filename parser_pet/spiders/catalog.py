
import scrapy
from scrapy.crawler import CrawlerProcess
import sqlalchemy as db


# 1. Надо спарсить используя scrapy вот этот сайт https://books.toscrape.com/ (не нужно весь сайт, 5 страниц какой-нибудь категории будет достаточно) +
# 2. Записать в базу данных название, категорию, цену, рейтинг и наличие +
# 3. В качестве БД можно использовать что угодно, хоть CSV файл (попробуй сделать так, чтоб смена хранилища заняла как можно меньше времени) 
# 4. Будет круто, если сможешь подрубить Celery + Redis
# 5. Будет круто, если это всё обернешь в докер

class CatalogSpider(scrapy.Spider):
    name = "catalog"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com"]

    pages_count = 5
    engine = db.create_engine('sqlite:///parsed_items.db')
    conn = engine.connect()
    metadata = db.MetaData()
    items = db.Table('items', metadata,
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('name', db.Text),
                        db.Column('category', db.Text),
                        db.Column('rating', db.Integer),
                        db.Column('price', db.Float),
                        db.Column('stock', db.Text)
                     )
    metadata.create_all(engine)

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

        insertion_query = self.items.insert().values([
            {
            'name': response.css('.product_main h1::text').extract_first('').strip(),
            'category': response.css('.breadcrumb a::text')[-2].get(),
            'price': response.css('.price_color::text').extract_first('').strip()[1:],
            'rating': rating_number,
            'stock': response.css('.instock.availability::text')[1].extract().replace("\n", "").strip()
            }
        ])


        self.conn.execute(insertion_query)

        

    def closed(self, reason):
        select_all_query = self.items.select()
        select_all_results = self.conn.execute(select_all_query)
        for row in select_all_results.fetchall():
            print(row)

if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(CatalogSpider)
    process.start()