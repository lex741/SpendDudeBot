from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id    = Column(Integer, primary_key=True, index=True)
    balance    = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    categories = relationship("Category", back_populates="user", cascade="all, delete")

class Category(Base):
    __tablename__ = "categories"
    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.user_id"))
    name     = Column(String, index=True)

    user     = relationship("User", back_populates="categories")