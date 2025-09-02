import sys
import os

# Ajoute le dossier parent (où se trouvent Data/ et Function/) au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



from Function.api_function import *
from Function.general_function import *
from Function.scraping_function import *
import os
import csv
from repos_sql import *
from repos_csv import *
from repos_api import *
from Database.db import *
from Database.mongodb import *
from repos_scraping import *
from repos_big_data import *
from sqlalchemy.exc import SQLAlchemyError
from Class.rain_class import *
from sqlalchemy.orm import Session
import numpy as np
def get_scraped_repos_from_topics(output_file):
    all_keywords = ["neural-network","reinforcement-learning","nlp", "mcp", "ai", "machine-learning", "deep-learning","artificial-intelligence", "rag", "llm", "gpt", "ai-agent"]

    # Entêtes du CSV
    fieldnames = ["owner", "repos", "topic"]

    # 1. Charger les dépôts déjà présents dans le fichier CSV
    seen_repos = set()

    if os.path.isfile(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['owner']}/{row['repos']}"
                seen_repos.add(key)

    # 2. Initialiser le fichier s’il n’existe pas
    if not os.path.isfile(output_file):
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # 3. Scraping et écriture sans doublons
    for topic in all_keywords:
            print(topic)
            all_repos = scrap_all_repos(topic)  # { "owner/repo": (owner, repo) }

            data_rows = []
            for key, (owner, repo) in all_repos.items():
                if key not in seen_repos:
                    data_rows.append({"owner": owner, "repos": repo, "topic": topic})
                    seen_repos.add(key)

            if data_rows:
                with open(output_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerows(data_rows)
        
    return output_file


def get_data_from_all_repo(output_file):
    if os.path.isfile(output_file):
        repos_sql(output_file)
        repos_mongodb(output_file)
        repos_csv(output_file)
    else :
        file = get_scraped_repos_from_topics(output_file)
        repos_sql(file)
        repos_mongodb(file)
        repos_csv(file)



def data_in_db(table_src, collection_src):
    """Récupération et fusion des données depuis plusieurs sources, puis insertion SQL"""

    #Postgres
    engine_src = connect_to_db(
        os.environ['DB_GIT_NAME'],
        os.environ['DB_GIT_USER'],
        os.environ['DB_GIT_PASSWORD'],
        os.environ['DB_GIT_HOST'],
        os.environ['DB_GIT_PORT']
    )
    query = f"SELECT * FROM {table_src};"
    df_sql = pd.read_sql_query(query, engine_src)
    df_sql['source'] = 'sql'
    # MongoDB
    db = connect_mongodb(os.environ["MONGODB_HOST"], os.environ["MONGODB_NAME"])
    collection = db[collection_src]
    documents = list(collection.find({}))
    df_big_data = pd.DataFrame(documents)
    df_big_data['source'] = 'big_data'
    # CSV
    df_csv = pd.read_csv("Data/repos_github.csv")
    df_csv['source'] = 'csv'

    # API
    repos_api = get_repos_by_api()
    df_api = pd.DataFrame(repos_api)
    df_api['source'] = 'api'

    # Scraping
    repos_scraping = scraped_data_repos_trending()
    data_scraped = list(repos_scraping.values())
    df_scraping = pd.DataFrame(data_scraped)
    df_scraping.drop("full_name", axis=1, inplace=True)
    df_scraping['source'] = 'scraping'
    # Colonnes d’intérêt
    table_dsc_columns = [
        "id", "name", "owner", "description", "license",
        "created_at", "updated_at", "html_url", "stargazers_count",
        "forks_count", "topics","source"
    ]

    # Fusion
    df = pd.concat([df_sql, df_big_data, df_csv, df_api], ignore_index=True)
    df_cleaned = df[table_dsc_columns]
    # Nettoyer les champs owner
    df_cleaned['owner'] = df_cleaned['owner'].apply(safe_eval)

    # Remplacer None/NaN par {} pour éviter erreurs dans json_normalize
    owner_list = df_cleaned['owner'].apply(lambda x: x if isinstance(x, dict) else {}).tolist()

    # Normalisation
    owners_df = pd.json_normalize(owner_list)[['login', 'html_url']]
    owners_df = owners_df.rename(columns={'login': 'owner', 'html_url': 'owner_url'})

    # Fusionner sans perdre de lignes
    df_cleaned = df_cleaned.drop(columns=['owner']).reset_index(drop=True)
    owners_df = owners_df.reset_index(drop=True)
    df_cleaned = pd.concat([df_cleaned, owners_df], axis=1)

    # Évaluer proprement license
    df_cleaned['license'] = df_cleaned['license'].apply(safe_eval)

    # Remplacer valeurs nulles par {} puis normaliser
    license_list = df_cleaned['license'].apply(lambda x: x if isinstance(x, dict) else {}).tolist()
    license_df = pd.json_normalize(license_list)[['spdx_id']]

    # Remplacer la colonne
    df_cleaned['license'] = license_df['spdx_id'].fillna(np.nan)

    print(len(df_cleaned))
    df_all = pd.concat([df_cleaned, df_scraping], ignore_index=True)
    df_all["is_trending"] = df_all.get("is_trending", False).fillna(False)
    df_all_cleaned = df_all.drop_duplicates(subset=["id"], keep="last")
    df_all_cleaned['topics'] = df_all_cleaned['topics'].apply(safe_parse_topics)

    translated = []
    lang = []

    for row in df_all_cleaned.itertuples():
        desc = getattr(row, 'description', '')
        translated_text,lang_text = translate_multilang(desc)
        translated.append(translated_text)
        lang.append(lang_text)

    df_all_cleaned['description_translated'] = translated
    df_all_cleaned['langue'] = lang


    print(len(df_cleaned))
    print(len(df_all))
    print(len(df_all_cleaned))

    repos = [GitHubRepo(**row) for row in df_all_cleaned.to_dict(orient="records")]
    #print(repos)

    # Connexion destination Postgres (via SQLAlchemy)
    engine_dst = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
    )

    # Nom de la table cible
    table_name = "githubRepo"

    if not table_exists(engine_dst, table_name):
        columns = {
            'id': Integer,
            'name': Text,
            'owner': Text,
            'owner_url' : Text,
            'description': Text,
            'description_translated': Text,
            'license': Text,
            'created_at': DateTime,
            'updated_at': DateTime,
            'html_url': Text,
            'stargazers_count': Integer,
            'forks_count': Integer,
            'topics': ARRAY(Text),
            'is_trending': Boolean,
            'source': Text,
            'langue': Text,
        }

        create_table(engine_dst, table_name, columns)

    # Insère toujours les données, que la table existe ou non
    with Session(engine_dst) as session:
        session.add_all(repos)
        session.commit()

#get_data_from_all_repo("Data/repos_scraped.csv")
data_in_db('repos_github','github_repos')
copy_db("githubRepo","Repos_Git")