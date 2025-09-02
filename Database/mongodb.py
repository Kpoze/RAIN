from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
import datetime
load_dotenv()
def connect_mongodb(host,name):
    client = MongoClient(host)  
    db = client[name]           
    return db

def json_converter(o):
    """
    Fonction d'aide pour convertir les types non sérialisables, comme les dates.
    """
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def export_big_data(collection_name,output_path):
    db = connect_mongodb(os.environ["MONGODB_HOST"],os.environ["MONGODB_NAME"])
    collection = db[collection_name]
    documents = list(collection.find({}, {'_id': 0}))
    with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2, default=json_converter)