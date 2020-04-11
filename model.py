from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Shop(Base):
    __tablename__ = 'shops'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    url = Column(String, unique=True)


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    external_id = Column(String, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    url = Column(String, index=True)
    lowest_price = Column(Float, index=True)
    current_price = Column(Float, index=True)
    lowest_price_aberrance = Column(Float, index=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), index=True)
    shop = relationship('Shop', back_populates='products')


Shop.products = relationship('Product', order_by=Product.id, back_populates='shop')


class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True)
    value = Column(Float, index=True)
    date = Column(Date, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), index=True)
    product = relationship('Product', back_populates='prices')


Product.prices = relationship('Price', order_by=Price.id, back_populates='product')
