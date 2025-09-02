from Database.db import *
import pandas as pd
import numpy as np
import json
import os 

export_sql_data("githubRepo","Docker/sql_data.csv")
#export_big_data("Repos_Git","Docker/big_data.json")

# --- Configuration ---
# Chemin vers le fichier CSV source
CSV_INPUT_PATH = "Docker/sql_data.csv"

# Chemins pour les fichiers de sortie
SQL_OUTPUT_PATH = "Docker/init.sql"
MONGO_JS_OUTPUT_PATH = "Docker/init-mongo.js"

# Nom de la table SQL
SQL_TABLE_NAME = "githubRepo"

# Configuration pour MongoDB
MONGO_DB_NAME = os.environ["MONGODB_NAME"]
MONGO_USER = os.environ["MONGODB_USER"]
MONGO_PASSWORD = os.environ["MONGODB_PASSWORD"]

def generate_init_sql_from_df(df):
    """
    Génère un script d'initialisation SQL à partir d'un DataFrame.
    """
    print("Génération du script init.sql pour PostgreSQL...")

    sql_script_content = f"""
-- init.sql - Généré automatiquement
CREATE DATABASE mlflow_db;

-- Création de la table pour les utilisateurs
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table pour les projets
CREATE TABLE IF NOT EXISTS public."{SQL_TABLE_NAME}" (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    owner TEXT,
    owner_url TEXT,
    description TEXT,
    description_translated TEXT,
    license TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    html_url TEXT,
    stargazers_count INT,
    forks_count INT,
    topics TEXT[],
    is_trending BOOLEAN,
    source TEXT,
    langue TEXT
);

-- Création de la table de liaison
CREATE TABLE IF NOT EXISTS public.user_liked_repos (
    user_id INT REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INT REFERENCES public."{SQL_TABLE_NAME}"(id) ON DELETE CASCADE,
    liked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, project_id)
);

-- Vider la table avant l'insertion pour éviter les doublons
TRUNCATE TABLE public."{SQL_TABLE_NAME}" RESTART IDENTITY CASCADE;

-- Insertion des données des projets via la commande COPY
-- Le fichier CSV doit être dans le même dossier que ce script dans le conteneur.
COPY public."{SQL_TABLE_NAME}" FROM '/docker-entrypoint-initdb.d/{os.path.basename(CSV_INPUT_PATH)}' DELIMITER ',' CSV HEADER;
"""
    with open(SQL_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(sql_script_content)
        print(f"Script {SQL_OUTPUT_PATH} généré avec succès.")

def generate_mongo_init_from_df():
    """
    Génère un script d'initialisation MongoDB à partir d'un DataFrame.
    """
    print("\nGénération du script init-mongo.js pour MongoDB...")
    engine = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
    )
    # Lire la table souhaitée
    df = pd.read_sql_table("githubRepo", engine)

    # --- MODIFICATION CLÉ : Convertir les Timestamps en chaînes ISO 8601 ---
    # JSON ne sait pas comment gérer les objets Timestamp. On les convertit
    # en chaînes de caractères, un format standard que MongoDB peut réinterpréter comme une date.
    date_columns = ['created_at', 'updated_at']
    for col in date_columns:
        if col in df.columns:
            # La fonction lambda gère les dates valides et laisse les valeurs nulles (None/NaT) tranquilles.
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
    # --- FIN DE LA MODIFICATION ---

    # Remplacer les NaN restants par None pour une compatibilité JSON parfaite
    df_mongo = df.replace({np.nan: None})
    documents = df_mongo.to_dict(orient='records')
    
    # Le reste de votre fonction est parfait
    try:
        data_as_json_string = json.dumps(documents, indent=2, ensure_ascii=False)
    except TypeError as e:
        print(f"Une erreur de sérialisation JSON persiste : {e}")
        # Optionnel : inspecter le premier document qui pose problème
        for doc in documents:
            try:
                json.dumps(doc)
            except TypeError:
                print("Document problématique :", doc)
                break
        return # Arrêter la fonction si l'erreur persiste

    js_content = f"""
        // init-mongo.js - Généré automatiquement

        db = db.getSiblingDB('{MONGO_DB_NAME}');

        db.createUser({{
        user: '{MONGO_USER}',
        pwd: '{MONGO_PASSWORD}',
        roles: [ {{ role: 'readWrite', db: '{MONGO_DB_NAME}' }} ],
        }});

        db.createCollection('projects');
        db.projects.deleteMany({{}});

        print("Insertion de {len(documents)} documents dans la collection 'projects'...");
        db.projects.insertMany({data_as_json_string});

        print("Initialisation de la base de données MongoDB terminée.");
        """

    with open(MONGO_JS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Script {MONGO_JS_OUTPUT_PATH} généré avec succès.")

if __name__ == "__main__":
    print(f"Lecture du fichier source : {CSV_INPUT_PATH}...")
    try:
        main_df = pd.read_csv(CSV_INPUT_PATH)
        
        # Lancer la génération pour les deux bases de données
        generate_init_sql_from_df(main_df)
        generate_mongo_init_from_df()
        
        print("\nProcessus de génération des scripts d'initialisation terminé.")

    except FileNotFoundError:
        print(f"Erreur : Le fichier source {CSV_INPUT_PATH} est introuvable.")