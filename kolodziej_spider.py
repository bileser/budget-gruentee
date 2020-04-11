from bs4 import BeautifulSoup
import requests
import re
import logging


class KolodziejSpider:
    def __init__(self, shop_url, log):
        self.log = log
        self.products = []

        page_url = shop_url + 'epages/61009178.sf/de_DE/?ViewAction=View&ObjectID=126420457&PageSize=1000'
        r = requests.get(page_url)

        soup = BeautifulSoup(r.text, "lxml")

        info_areas = soup.select('div[class="InfoArea"]')

        for info_area in info_areas:
            link = info_area.select_one('h3 > a')
            url = shop_url + "epages/61009178.sf/de_DE/" + link.attrs['href']
            title = link.text.strip()
            description = info_area.select_one('div[class="Description"]').text.strip()
            price = 0
            price_text = info_area.select_one('div[class="Description ClearBoth"]')
            if price_text:
                price_text = price_text.text.replace('.', '')
                price_text = price_text.replace(',', '.')
                price_kg = float(re.findall(r'-?\d+\.?\d*', price_text)[1])
                price = float("{0:.2f}".format(price_kg / 10))
            else:
                price_text = info_area.select_one('span[itemprop="price"]').attrs['content']
                price = float("{0:.2f}".format(float(price_text) / 10))
            product_no = info_area.select_one('span[class="ProductNo"]').text
            external_id = product_no.split()[-1]
            self.products.append(dict(title=title, description=description, url=url, price=price,
                                      external_id=external_id))

    def get_products(self):
        return self.products

