from bs4 import BeautifulSoup
import requests
import re


class TeaworldSpider:

    def __init__(self, shop_url, logging):
        self.logging = logging
        self.QUEUE = [(self._parse_list_page, shop_url + "tee/gruener-tee.html")]
        self.products = []
        while len(self.QUEUE):
            call_back, url = self.QUEUE.pop(0)
            call_back(url)

    def _parse_list_page(self, url):
        print("processing " + url)
        self.logging.info("processing " + url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        links = soup.select('a[class="next i-next"]')
        if links:
            next_link = links[0].attrs['href']
            self.QUEUE.append(
                (self._parse_list_page, next_link)
            )

        links = soup.select('h3[class="product-name"] > a')
        for link in links:
            product_url = link.attrs['href']
            self.QUEUE.append(
                (self._parse_detail_page, product_url)
            )

    def _parse_detail_page(self, url):
        print("processing " + url)
        self.logging.info("processing " + url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.select_one('h1').text
        description = soup.select_one('div[id="product_tabs_description_contents"] > div[class="std"] > p').text
        product_essential = soup.select_one('div[class="product-essential"]')
        external_id = soup.select_one('input[name="product"]').attrs['value']
        baseprice_price = product_essential.select_one('span[class="baseprice-price"]')
        if not baseprice_price:
            return
        price_text = baseprice_price.text #  '5,63 € / 100g'
        price_text = price_text.replace('.', '')
        price_text = price_text.replace(',', '.')
        price = float(re.findall(r'-?\d+\.?\d*', price_text)[0])

        product_dict = dict(title=title, description=description, url=url, price=price, external_id=external_id)
        self.products.append(product_dict)

    def get_products(self):
        return self.products

