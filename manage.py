from model import Base, Product, Price, Shop
from kolodziej_spider import KolodziejSpider
from nibelungen_spider import NibelungenSpider
from sunday_spider import SundaySpider
from teaworld_spider import TeaworldSpider
from kobu_spider import KobuSpider
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import datetime
import logging
import requests


logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M',
                    filename='manage.log', filemode='w', level=logging.DEBUG)
logging.info("Und los geht's!")

engine = create_engine('postgresql://gruentee:@localhost:5432/gruentee', echo=True)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def save_product(session, product_dict, shop):
    print("save_product")
    if product_dict['price'] == 0:
        return
    product = session.query(Product).filter_by(
        external_id=product_dict['external_id'], shop_id=shop.id
    ).first()
    if not product:
        product = Product(
            title=product_dict['title'], description=product_dict['description'], url=product_dict['url'],
            current_price=product_dict['price'], lowest_price=product_dict['price'], lowest_price_aberrance=1.0,
            external_id=product_dict['external_id']
        )
        shop.products.append(product)
        session.add(product)
        logging.info("added product with url: {}, title: {}".format(product.url, product.title))
        print("added product with url: {}, title: {}".format(product.url, product.title))
    else:
        logging.info("shop {}, product id {} existiert schon als name {} und url {}\n".format(
            shop.name, product_dict['external_id'], product.title, product.url
        ))
        print("shop {}, product id {} existiert schon als name {} und url {}\n".format(
            shop.name, product_dict['external_id'], product.title, product.url
        ))
        product.title = product_dict['title']
        product.description = product_dict['description']
        product.url = product_dict['url']
        product.current_price = product_dict['price']
        product.lowest_price = min(product_dict['price'], product.lowest_price)
        product.lowest_price_aberrance = product.current_price / product.lowest_price

    product.prices.append(Price(value=product_dict['price'], date=datetime.date.today()))


logging.info("creating db.")
print("creating db.")
Base.metadata.create_all(engine)
session.commit()

shop_handlings = [
    {'url': 'https://www.kobu-teeversand.de', 'name': "Kobu Tee ® und Futon", 'spider': KobuSpider},
   {'url': 'https://www.teehandel-kolodziej-shop.de/', 'name': "Teehandel Kolodziej e.K.",
    'spider': KolodziejSpider},
   {'url': 'https://www.nibelungentee.de', 'name': "Nibelungentee  internet-connect GmbH",
    'spider': NibelungenSpider},
   {'url': 'https://www.sunday.de', 'name': "Sunday Natural Products GmbH", 'spider': SundaySpider},
   {'url': 'https://www.teaworld.de/', 'name': "Teaworld OHG", 'spider': TeaworldSpider}
]

for shop_handling in shop_handlings:
    shop = session.query(Shop).filter_by(name=shop_handling['name']).first()
    if not shop:
        shop = Shop(name=shop_handling['name'], url=shop_handling['url'])
        session.add(shop)
    try:
        spider = shop_handling['spider'](shop_handling['url'], logging)
        products = spider.get_products()
        for product in products:
            save_product(session, product, shop)
        session.commit()
    except:
        logging.info("exception in spider {}".format(shop_handling.spider))
        pass

# clean
max_date = session.query(func.max(Price.date)).all()[0]
logging.info("delete products with date < {}".format(max_date))
print("delete products with date < {}".format(max_date))
q = session.query(Product).join(Product.prices).group_by(Product.id).having(func.max(Price.date) < max_date)
products = q.all()
for p in products:
    logging.info("delete product {}".format(p.url))
    session.delete(p)
session.commit()

r = requests.get("http://127.0.0.1:8000/reload")
logging.info(r)
print(r)
