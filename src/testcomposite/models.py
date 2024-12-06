from sqlalchemy import Column, Integer, String

from src.database import Base


class ResearchProfile(Base):
    __tablename__ = "ResearchProfile"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    google_scholar_link = Column(String(255))
    personal_website_link = Column(String(255))
    organization = Column(String(255), index=True)
    title = Column(String(255))
    age = Column(Integer)
    sex = Column(String(10))
