from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class App(Base):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    emoji = Column(String)
    link = Column(String)
    image = Column(String)

class Token(Base):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    login_time = Column(DateTime, default=datetime.datetime.utcnow)

class Rent(Base):
    __tablename__ = 'rents'
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey('apps.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)