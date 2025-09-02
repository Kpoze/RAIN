from sqlalchemy import create_engine,inspect,Table, Column, MetaData, Text, Integer, Float, Boolean,DateTime,Date,text,JSON
from sqlalchemy.dialects.postgresql import ARRAY
import os
from dotenv import load_dotenv
from datetime import datetime, date
import pandas as pd
import numpy as np
from .mongodb import *
import csv 
import ast 
load_dotenv()


def connect_to_db(db_name, db_user, db_password, db_host, db_port):
    print(repr(db_name))
    print(repr(db_user))
    print(repr(db_password))
    print(repr(db_host))
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url, echo=False, future=True, connect_args={'client_encoding': 'utf8'})
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connexion réussie :", result.scalar())  # Doit afficher : Connexion réussie : 1
    except Exception as e:
        print("Échec de la connexion :", e)
    return engine



def table_exists(engine, table_name):
    inspector = inspect(engine)
    return inspector.has_table(table_name)


def create_table(engine, table_name, columns):
    metadata = MetaData()

    sqlalchemy_columns = []
    for col_name, col_type in columns.items():
        sqlalchemy_columns.append(Column(col_name, col_type))

    Table(table_name, metadata, *sqlalchemy_columns)
    metadata.create_all(engine)

def sql_type(value):
    if isinstance(value, bool):
        return Boolean()
    elif isinstance(value, int):
        return Integer()
    elif isinstance(value, float):
        return Float()
    elif isinstance(value, str):
        return Text()
    else:
        return Text()

def copy_db(sql_table, collection_name):
        # Connexion destination Postgres (via SQLAlchemy)
    engine = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
    )
    # Lire la table souhaitée
    df = pd.read_sql_table(sql_table, engine)
    df_clean = df.replace({np.nan: None, pd.NaT: None})


    db = connect_mongodb(os.environ["MONGODB_HOST"],os.environ["MONGODB_NAME"])
    collection = db[collection_name]
    records = df_clean.to_dict(orient="records")

    if records:
        try:
            collection.insert_many(records)
            print(f"{len(records)} documents insérés.")
        except Exception as e:
            print("Erreur pendant l'insertion :", e)
    else:
        print("Aucune donnée à insérer.")

def format_list_for_sql(topics_str):
    try:
        # Convertit la chaîne "['ia', 'python']" en une vraie liste
        topics_list = ast.literal_eval(str(topics_str))
        if not isinstance(topics_list, list):
            return '{}'
        # Formate pour PostgreSQL : {"ia","python"}
        return '{' + ','.join([f'"{topic.replace("\"", "\"\"")}"' for topic in topics_list]) + '}'
    except (ValueError, SyntaxError):
        # En cas d'erreur (champ vide, mal formé), retourne un tableau vide
        return '{}'

# --- Voici la fonction MODIFIÉE ---
def export_sql_data(sql_table, csv_path):
    engine = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
    )
    
    # Lire la table
    df = pd.read_sql_table(sql_table, engine)
    
    # --- MODIFICATION 1 : Appliquer la transformation pour la colonne 'topics' ---
    if 'topics' in df.columns:
        print("Formatage de la colonne 'topics' pour PostgreSQL...")
        df['topics'] = df['topics'].apply(format_list_for_sql)
    
    # --- MODIFICATION 2 : Modifier l'export CSV pour plus de robustesse ---
    print(f"Exportation des données formatées vers {csv_path}...")
    df.to_csv(
        csv_path, 
        index=False, 
        encoding='utf-8',
        quoting=csv.QUOTE_ALL # Force les guillemets partout, évite les erreurs
    )
    print("Exportation terminée avec succès !")