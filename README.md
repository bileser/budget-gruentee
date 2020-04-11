# budget-gruentee

Find hundrets of green teas from the biggest german speaking shops and get them ordered by price, being able to manage updates regularly on the database

No fancy Javascript UI, for the sake of being visible to search engines. The content is plain serverside generated HTML and not created on the Client. There is also no bloated CSS framework. There are no tons of Javascript potentially being able to do all kind of stuff. There is only [Picnic CSS](https://picnicss.com/documentation), a lightweight CSS library. The only Javascript is used to toggle the menu between mobile and desktop mode.

The app is written in Python 3.7 and uses [Flask, the python micro framework for building web applications.](https://github.com/pallets/flask) and [Jinja Templates](https://jinja.palletsprojects.com/en/2.11.x/). I had to overcome the strong desire to engineer a complex UI using a modern Javascript framework. But choose the right tool for the job.

There are several spiders to scrape what I idenfified as the biggest german speaking shops für green tea. A spider follows the informal interface: If a spider object is initialized, it scrapes overview and detail pages to build list of products which can be obtained by calling `get_products` on the object.

The Flask app is defined in `reloadable_app.py`. The routes are cached and refreshed when the app reloads. Since the data does not change until the products are scraped again, why should complex database query happen again and again and provoke googles impatience. To reload the app the 'hidden' route `/reload` must be called. This might be not ideal. But hey, this is version 1

`manage.py` is used to manage the updates. It can be executed from a cron job to run the spiders every night. The script gathers all the products and updates their prices in the database and deletes products from the database that don't exist any more. Then it reloads the app.

[SQLAlchemy](https://www.sqlalchemy.org/) serves as the database layer, especially the ORM part. You can find the model in `model.py`

This is the app in real life: https://grüne-tees.de/
