from Function.api_function import *
from Function.general_function import *
from Function.scraping_function import *
from Database.db import *
from Database.db_repos import *
from Class.repo_class import *
import time
import os
from dotenv import load_dotenv
import pandas as pd
import json
from sqlalchemy import inspect, text

load_dotenv()


keyword_SQL      = ["ai", "machine-learning", "deep-learning","artificial-intelligence"]
############################# POSTGRES ##########################
def ensure_columns_exist(engine, table_name, repo_info):
    inspector = inspect(engine)
    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
    
    with engine.begin() as conn:
        for key, value in repo_info.items():
            if key not in existing_cols:
                col_type = sql_type(value)
                col_type_sql = col_type.compile(dialect=engine.dialect)
                alter_query = f'ALTER TABLE "{table_name}" ADD COLUMN "{key}" {col_type_sql}'
                try:
                    conn.execute(text(alter_query))
                    print(f"✅ Colonne {key} ajoutée avec le type {col_type_sql}")
                except Exception as e:
                    print(f"⚠️ Colonne {key} non ajoutée : {e}")


def clean_repo_info(data):
    clean = {}
    for k, v in data.items():
        if isinstance(v, (dict, list)):
            clean[k] = json.dumps(v, ensure_ascii=False)
        else:
            clean[k] = v
    return clean

def repos_sql(filename, table_name="repos_github"):
    df = pd.read_csv(filename)
    engine = connect_to_db(os.environ['DB_GIT_NAME'], os.environ['DB_GIT_USER'], os.environ['DB_GIT_PASSWORD'], os.environ['DB_GIT_HOST'], os.environ['DB_GIT_PORT']) 
    table_created = False
    for owner, repo_name, topic in zip(df['owner'], df['repos'], df['topic']):
        if topic in keyword_SQL:
            repo_info = get_repo_info(owner, repo_name)
            time.sleep(2)
            if repo_info and is_open_source(repo_info.get("license")):
                repo_info["topic"] = topic
                repo_info = clean_repo_info(repo_info)

                if not table_created:
                    # Créer la table dynamiquement
                    columns = {key: sql_type(value) for key, value in repo_info.items()}
                    create_table(engine, table_name, columns)
                    table_created = True
                else:
                    ensure_columns_exist(engine, table_name, repo_info)

                insert_repo(engine, table_name, repo_info)