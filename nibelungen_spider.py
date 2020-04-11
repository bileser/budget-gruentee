from bs4 import BeautifulSoup
import requests
import re


class NibelungenSpider:

    def __init__(self, shop_url, logging):
        self.logging = logging
        self.shop_url = shop_url
        self.products = []
        self.QUEUE = [(self._parse_list_page, 'https://www.nibelungentee.de/tee/gruener-tee/')]
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

        product_boxes = soup.select('div[class="product--box box--minimal hover-actions"]')
        for product_box in product_boxes:
            product_url = product_box.select_one('a').attrs['href']
            data_ordernumber_parts = product_box.attrs['data-ordernumber'].split('-')
            if len(data_ordernumber_parts) == 2 and data_ordernumber_parts[1] != '100':
                product_url = "{}&number={}-100".format(product_url, data_ordernumber_parts[0])

            self.QUEUE.append((self._parse_detail_page, product_url))

    def _parse_detail_page(self, url):
        print("processing detail " + url)
        self.logging.info("processing detail " + url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        sku_tag = \
            soup.select_one('td[class="product--properties-value entry--sku"] > span[class="entry--content"]')

        if not sku_tag:
            return

        external_id = sku_tag.text.strip()

        variant_group = soup.select_one('div[class="variant--group"]')
        if variant_group:
            option_100g = variant_group.select_one('div[class="variant--option"] > input[title="100g"]')
            if option_100g:
                if 'checked' in option_100g.attrs:
                    price_tag = soup.select_one('span[class="price--content content--default"] > meta[itemprop="price"]')
                    price = float(price_tag.attrs['content'])
                else:
                    product_url = "{}&number={}-100".format(url, external_id)
                    self.QUEUE.append((self._parse_detail_page, product_url))
                    return
            else:
                return
        else:
            price_unit = soup.select_one('div[class="product--price price--unit"]')
            if not price_unit:
                return
            price_text = price_unit.text  # 30 Gramm (83,00 € / 100 Gramm)
            price_text = price_text.replace('.', '')
            price_text = price_text.replace(',', '.')
            price_numbers = re.findall(r'-?\d+\.?\d*', price_text)
            price = float(price_numbers[1])

        title = soup.select_one('h1[class="product--title"]').text.strip()

        description = ""
        product_description = soup.select_one('div[class="product--description"]').text.strip()
        description += product_description

        properties_rows = soup.select('tr[class="product--properties-row"]')
        properties = {}
        for row in properties_rows:
            key = row.select_one('td[class="product--properties-label is--bold"]')
            value = row.select_one('td[class="product--properties-value"]')
            properties.update({key.text: value.text} if value and key else {})

        description += " " + ". ".join(["{} {}".format(k, properties[k]) for k in ['Art:', 'Zutaten:', 'Eigenschaft:']
                                         if k in properties])

        product_dict = dict(title=title, description=description, url=url, price=price, external_id=external_id)
        self.products.append(product_dict)
