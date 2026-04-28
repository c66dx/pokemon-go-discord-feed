from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    image_url = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    source = Column(String, nullable=True)
    hash_value = Column(String, unique=True, nullable=True)