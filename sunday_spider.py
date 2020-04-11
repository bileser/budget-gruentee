from bs4 import BeautifulSoup
import requests
import re


class SundaySpider:

    def __init__(self, shop_url, logging):
        self.processed_detail_urls = {}
        self.QUEUE = []
        self.products = []
        self.processed_detail_urls = {}
        self.EXCLUDE = [
            'https://www.sunday.de/tee-gruentee-extrakt/', 'https://www.sunday.de/gruener-tee-pulver/',
            'https://www.sunday.de/gruener-tee/sorten.html', 'https://www.sunday.de/gruener-tee/laboruntersuchung.html',
            'https://www.sunday.de/gruener-tee-top-angebote/', 'https://www.sunday.de/gruener-tee-sets/'
        ]
        self.shop_url = shop_url
        self.logging = logging
        self.QUEUE.append(
            (self._parse_overview_page, shop_url + "/gruener-tee/")
        )

        while len(self.QUEUE):
            call_back, url = self.QUEUE.pop(0)
            call_back(url)

    def _parse_overview_page(self, url):
        print("processing overview " + url)
        self.logging.info("processing overview " + url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        category_products = soup.select('div[class="category-products"]')
        links = category_products[1].select('a[class="product-image"]')
        for link in links:
            next_link = link.attrs['href']
            if next_link in self.EXCLUDE:
                continue
            self.QUEUE.append(
                (self._parse_category_page, next_link)
            )

    def _parse_category_page(self, url):
        print("processing category " + url)
        self.logging.info("processing category " + url)
        r = requests.get(self.shop_url + url)
        soup = BeautifulSoup(r.text, "lxml")
        links = soup.select('h2[class="product-name"] > a')

        for link in links:
            if not 'href' in link.attrs:
                continue
            product_url = link.attrs['href']
            if not 'www.sunday.de' in product_url:
                continue
            self.QUEUE.append(
                (self._parse_detail_page, product_url)
            )

    def _parse_detail_page(self, url):
        print("processing detail " + url)
        self.logging.info("processing detail " + url)
        if url in self.processed_detail_urls:
            print("url already processed")
            self.logging.info("url already processed")
            return
        self.processed_detail_urls[url] = True
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")
        product_view = soup.select_one('div[class="product-view"]')
        if not product_view:
            return
        title = product_view.select_one('h1').text
        short_description_std= product_view.select_one('div[class="short-description"] > div[class="std"]')
        description = short_description_std.text.strip()
        product_commons = product_view.select_one('div[class="product-commons"]')
        baseprice_box = product_commons.select_one('div[class="baseprice-box"]')
        if not baseprice_box:
            return
        # baseprice_price = baseprice_box.select_one('span[class="price"]')
        # if not baseprice_price:
        #     return
        # price_text = baseprice_price.text #  '5,63 € / 100g'
        price_text = baseprice_box.text
        price_text = price_text.replace('.', '')
        price_text = price_text.replace(',', '.')
        numbers = re.findall(r'-?\d+\.?\d*', price_text)
        if len(numbers) != 2:
            return
        price = float(numbers[0]) / 10 if '1kg' in numbers[1] else float(numbers[0])
        external_id = soup.select_one('input[name="product"]').attrs['value']
        product_dict = dict(title=title, description=description, url=url, price=price, external_id=external_id)
        self.products.append(product_dict)

    def get_products(self):
        return self.products