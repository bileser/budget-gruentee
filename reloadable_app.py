from flask import Flask, render_template, jsonify
from flask_caching import Cache
from model import Product, Price
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from werkzeug.serving import run_simple
from sqlalchemy import func

engine = create_engine('postgresql://gruentee:@localhost:5432/gruentee', echo=True)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

# set to True to inform that the app needs to be re-created
to_reload = False


def get_app():
    app = Flask(__name__)
    cache_config = {
        "DEBUG": True,  # some Flask specific configs
        "CACHE_TYPE": "simple",  # Flask-Caching related configs
        "CACHE_DEFAULT_TIMEOUT": 90000
    }
    app.config.from_mapping(cache_config)
    app_cache = Cache(app)

    @app.route('/clear-cache')
    def clear_cache():
        global app_cache
        app_cache.clear()
        return jsonify({'hello': 'clear-cache'})

    @app.route('/impressum-datenschutz')
    def show_impressum_datenschutz():
        return render_template('impressum-datenschutz.html')

    @app.route('/')
    @app_cache.cached()
    def show_home():
        print("showing home, not cached yet")
        pages = {}
        keywords = ['sencha', 'gyokuro', 'bancha', 'genmaicha', 'matcha', 'china', 'korea']
        step = 20
        products_count = 0
        for keyword in keywords:
            offset = 0
            total_count, products = get_products(keyword, offset, step)
            if not len(products):
                continue
            products_count += len(products)
            pages[keyword] = [
                {'url': '/{}/{}/{}'.format(keyword, offset, step), 'lowest_price': products[0].current_price,
                 'highest_price': products[-1].current_price, 'count': len(products)}]
            while offset + step <= total_count:
                offset += step
                total_count, products = get_products(keyword, offset, step)
                products_count += len(products)
                pages[keyword].append({'url': '/{}/{}/{}'.format(keyword, offset, step),
                                       'lowest_price': products[0].current_price,
                                       'highest_price': products[-1].current_price, 'count': len(products)})
        return render_template('home.html', pages=pages, step=step, products_count=products_count)

    def get_products(keyword, offset, count):
        search_expr = "%{}%".format(keyword)
        query = session.query(Product).filter(
            or_(
                Product.description.ilike(search_expr),
                Product.title.ilike(search_expr)
            )
        )
        total_count = query.count()
        products = query.order_by(Product.current_price).slice(offset, offset + count).all()
        return total_count, products

    @app.route('/<keyword>/<int:offset>/<int:count>')
    @app_cache.cached()
    def show_products_by_keyword(keyword, offset, count):
        total_count, products = get_products(keyword, offset, count)
        max_date = session.query(func.max(Price.date)).all()[0][0]
        date = max_date.strftime('%d.%m.%Y')
        previous_link = False
        next_link = False
        if offset - count >= 0:
            previous_link = "/{}/{}/{}".format(keyword, offset - count, count)
        if offset + count <= total_count:
            next_link = "/{}/{}/{}".format(keyword, offset + count, count)

        return render_template('products.html', products=products, term=keyword.capitalize(),
                               lowest_price=products[0].current_price, highest_price=products[-1].current_price,
                               count=len(products), previous_link=previous_link, next_link=next_link, date=date)

    @app.route('/reload')
    def reload():
        global to_reload
        to_reload = True
        return "reloaded"

    return app


class AppReloader(object):
    def __init__(self, create_app):
        self.create_app = create_app
        self.app = create_app()

    def get_application(self):
        global to_reload
        if to_reload:
            self.app = self.create_app()
            to_reload = False

        return self.app

    def __call__(self, environ, start_response):
        app = self.get_application()
        return app(environ, start_response)


# This application object can be used in any WSGI server
# for example in gunicorn, you can run "gunicorn app"
application = AppReloader(get_app)

if __name__ == '__main__':
    run_simple('127.0.0.1', 8000, application,
               use_reloader=True, use_debugger=True, use_evalex=True)
