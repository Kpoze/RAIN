from motor.motor_asyncio import AsyncIOMotorClient
import os 
from Database.db import * 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv 
load_dotenv()


client = AsyncIOMotorClient(f'mongodb://{os.environ['MONGODB_USER']}:{os.environ['MONGODB_PASSWORD']}@{os.environ['MONGODB_HOST']}:27017/{os.environ['MONGODB_NAME']}')
db = client["Rain"]
collection = db["Repos_Git"]

engine = connect_to_db(
    os.environ['DB_NAME'],
    os.environ['DB_USER'],
    os.environ['DB_PASSWORD'],
    os.environ['DB_HOST'],
    os.environ['DB_PORT']
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()