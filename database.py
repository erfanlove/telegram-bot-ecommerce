from sqlalchemy import create_engine,Column,Integer,String,MetaData,Table,ForeignKey
from sqlalchemy.orm import sessionmaker,relationship,declarative_base
import os

engine = create_engine('sqlite:///bot.db', echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    _id = Column(Integer, primary_key=True)
    telegramid = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    orders = relationship("Order", back_populates="user")
    
        
class Product(Base):
    __tablename__ = 'products'
    _id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(String)
    description = Column(String)
    image = Column(String)
    orders = relationship("Order", back_populates="product")
    
    
class Order(Base):
    __tablename__ = 'order'
    _id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey('users._id'),unique=True)
    product_id = Column(Integer,ForeignKey('products._id'))
    quantity = Column(Integer)
    status = Column(String)
    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    
Run_Database = Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def save_user(telegramid, username, first_name):
    session = Session()
    user = session.query(User).filter_by(telegramid=telegramid).first()
    if not user:
        new_user = User(telegramid=telegramid, username=username, first_name=first_name)
        session.add(new_user)
        session.commit()
    session.close()

def products_list():
    session = Session()
    products = session.query(Product).all()
    session.close()
    return products

def get_user_by_telegramid(telegramid):
    session = Session()
    user = session.query(User).filter_by(telegramid=telegramid).first()
    session.close()
    if user:
        return user._id
    return None

def add_to_cart(user_id, product_id, quantity, status):
    session = Session()
    new_order = Order(user_id=user_id, product_id=product_id, quantity=quantity, status=status)
    session.add(new_order)
    session.commit()
    session.close()

def delete_product_from_cart(user_id, product_id):
    session = Session()
    order = session.query(Order).filter_by(user_id=user_id, product_id=product_id, status="in_cart").first()
    if order:
        session.delete(order)
        session.commit()
    session.close()

def delete_order(user_id):
    session = Session()
    order = session.query(Order).filter_by(user_id=user_id).first()
    if order:
        session.delete(order)
        session.commit()
    session.close()

    
def get_cart_items(user_id):
    session = Session()
    cart_items = session.query(Order).filter_by(user_id=user_id, status="in_cart").all()
    session.close()
    return cart_items

def get_orders_by_user(user_id):
    session = Session()
    orders = session.query(Order).filter_by(user_id=user_id).all()
    session.close()
    return orders