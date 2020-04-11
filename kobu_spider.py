from bs4 import BeautifulSoup
import requests
import re


class KobuSpider:

    def __init__(self, shop_url, logging):
        self.logging = logging
        self.shop_url = shop_url
        self.products = []

        self.QUEUE = [(self._parse_list_page, 'https://www.kobu-teeversand.de/klassischer-tee/gruener-tee/'),
                      (self._parse_list_page, 'https://www.kobu-teeversand.de/bio-tee/bio-gruentee/')]

        while len(self.QUEUE):
            call_back, url = self.QUEUE.pop(0)
            call_back(url)

    def get_products(self):
        return self.products

    def _parse_list_page(self, url):
        print("processing list " + url)
        self.logging.info("processing list " + url)

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        paging = soup.select_one('div[class="listing--paging panel--paging"]')
        paging_next = paging.select_one('a[title="Nächste Seite"]')
        if paging_next:
            next_page_url = self.shop_url + paging_next.attrs['href']
            self.QUEUE.append(
                (self._parse_list_page, next_page_url)
            )

        links = soup.select('div[class="product--details"] > a')
        for link in links:
            product_url = link.attrs['href']
            self.QUEUE.append((self._parse_detail_page, product_url))

    def _parse_detail_page(self, url):
        print("processing detail " + url)
        self.logging.info("processing detail " + url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.select_one('h1[class="product--title"]').text.strip()
        description = soup.select_one('span[class="product--description"]').text.strip()
        price_unit = soup.select_one('div[class="product--price price--unit"]')
        if not price_unit:
            return
        price_text = price_unit.text  # '5,63 € / 100g'
        price_text = price_text.replace('.', '')
        price_text = price_text.replace(',', '.')
        price_numbers = re.findall(r'-?\d+\.?\d*', price_text)
        price = 0.0
        if len(price_numbers) == 3:
            price = float(price_numbers[1])
        elif len(price_numbers) == 1 and float(price_numbers[0]) == 100:
            product_price = soup.select_one('span[class="price--content content--default"]')
            product_price_text = product_price.text
            price_text = product_price_text.replace('.', '')
            price_text = price_text.replace(',', '.')
            price_numbers = re.findall(r'-?\d+\.?\d*', price_text)
            price = float(price_numbers[0])

        external_id = soup.select_one('form[name="sAddToBasket"] > input[name="sAdd"]').attrs['value']

        product_dict = dict(title=title, description=description, url=url, price=price, external_id=external_id)
        self.products.append(product_dict)

