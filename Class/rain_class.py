from sqlalchemy import Column, Integer, Text, DateTime, ARRAY,Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class GitHubRepo(Base):
    __tablename__ = 'githubRepo'

    id               = Column(Integer, primary_key=True)
    name             = Column(Text)
    owner            = Column(Text)
    owner_url        = Column(Text)
    description      = Column(Text)
    description_translated = Column(Text)
    license          = Column(Text)
    created_at       = Column(DateTime)
    updated_at       = Column(DateTime)
    html_url         = Column(Text)
    stargazers_count = Column(Integer)
    forks_count      = Column(Integer)
    topics           = Column(ARRAY(Text))
    is_trending      = Column(Boolean,  default=False)
    source           = Column(Text)
    langue           = Column(Text)