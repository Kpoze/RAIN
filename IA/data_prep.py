import sys
import os

# Ajouter le dossier parent (contenant IA et Database)
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)



from Database.db import *

import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords

def group_rare_categories(series, threshold_ratio=0.01, new_category_name='other'):
    """Regroupe les catégories rares en une seule catégorie 'other'."""
    series_no_na = series.dropna()
    if len(series_no_na) == 0:
        return series
    counts = series_no_na.value_counts()
    threshold_count = len(series) * threshold_ratio
    rare_categories = counts[counts < threshold_count].index
    return series.replace(rare_categories, new_category_name)


def clean_text_features(df):
    """Étape 1: Nettoie les colonnes textuelles et crée 'cleaned_text'."""
    print("\n[1/5] Nettoyage du texte...")
    df_processed = df.copy()
    
    # Gestion des valeurs manquantes
    df_processed.replace([None, ''], np.nan, inplace=True)
    df_processed['topics'] = df_processed['topics'].apply(lambda x: np.nan if (isinstance(x, list) and not x) else x)
    df_processed['description_translated'].fillna('', inplace=True)
    df_processed['topics'].fillna('', inplace=True)
    
    # Définition des stopwords
    stop_words = set(stopwords.words('english'))
    custom_stop_words = {
        'repository', 'explore', 'contribute', 'project', 'github', 'app', 'application', 
        'tool', 'library', 'framework', 'platform', 'model', 'gui', 'api', 'backend', 'interface'
    }
    stop_words.update(custom_stop_words)

    def clean_text(text):
        if not isinstance(text, str): return ""
        text = text.lower()
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'[^\w\s-]', '', text)
        words = text.split()
        cleaned_words = [word for word in words if word not in stop_words and len(word) > 1]
        return ' '.join(cleaned_words)

    df_processed['cleaned_description'] = df_processed['description_translated'].apply(clean_text)

    def clean_topics(topics_data):
        if isinstance(topics_data, list): topics_list = [str(t).lower() for t in topics_data]
        elif isinstance(topics_data, str): topics_list = topics_data.lower().split()
        else: return ""
        unique_topics = sorted(list(set(topics_list)))
        cleaned_topics = [topic for topic in unique_topics if topic not in stop_words and len(topic) > 1]
        return ' '.join(cleaned_topics)

    df_processed['cleaned_topics'] = df_processed['topics'].apply(clean_topics)
    
    # Combiner la description et les topics nettoyés
    df_processed['cleaned_text'] = df_processed['cleaned_description'] + ' ' + df_processed['cleaned_topics']
    
    # Supprimer les espaces multiples
    df_processed['cleaned_text'] = df_processed['cleaned_text'].str.replace(r'\s+', ' ', regex=True).str.strip()

    
    return df_processed


def engineer_datetime_features(df):
    """Étape 2: Crée les features basées sur les dates."""
    print("\n[2/5] Création des features temporelles...")
    df_processed = df.copy()
    
    df_processed['created_at'] = pd.to_datetime(df_processed['created_at'], errors='coerce')
    df_processed['updated_at'] = pd.to_datetime(df_processed['updated_at'], errors='coerce')
    df_processed.dropna(subset=['created_at'], inplace=True)

    df_processed['updated_at'] = df_processed.apply(
        lambda row: row['created_at'] if pd.isna(row['updated_at']) or row['updated_at'] < row['created_at'] else row['updated_at'],
        axis=1
    )

    current_time = pd.Timestamp.now()
    df_processed['repo_age_days'] = (current_time - df_processed['created_at']).dt.days
    df_processed['days_since_last_update'] = (current_time - df_processed['updated_at']).dt.days
    df_processed['created_year'] = df_processed['created_at'].dt.year
    return df_processed


def clean_categorical_features(df):
    """Étape 3: Nettoie et regroupe les features catégorielles."""
    print("\n[3/5] Nettoyage des features catégorielles...")
    df_processed = df.copy()
    
    df_processed['license'].fillna('No License', inplace=True)
    df_processed['license'] = group_rare_categories(df_processed['license'], new_category_name='other_license')
    
    if 'langue' in df_processed.columns:
        df_processed['langue'].fillna('Unknown', inplace=True)
        df_processed['langue'] = group_rare_categories(df_processed['langue'], new_category_name='other_language')
        
    return df_processed


def transform_numeric_features(df):
    """Étape 4: Applique une transformation logarithmique aux features numériques."""
    print("\n[4/5] Transformation des features numériques...")
    df_processed = df.copy()
    
    for col in ['stargazers_count', 'forks_count']:
        if col in df_processed.columns:
            df_processed[f'{col}_log'] = np.log1p(df_processed[col].astype(float))
    
    return df_processed


def finalize_dataset(df):
    """Étape 5: Sélectionne les colonnes finales et effectue un dernier nettoyage."""
    print("\n[5/5] Sélection finale des colonnes...")
    df_processed = df.copy()
    
    final_columns = [
        'id','name','owner', 'description_translated', 'cleaned_text', 'topics', 'license', 'langue',
        'stargazers_count', 'forks_count', 'stargazers_count_log', 'forks_count_log',
        'repo_age_days', 'days_since_last_update', 'created_year', 'html_url'
    ]
    
    for col in final_columns:
        if col not in df_processed.columns:
            df_processed[col] = np.nan

    df_final = df_processed[final_columns]
    df_final = df_final[df_final['cleaned_text'] != ''].copy()
    
    return df_final

def run_full_preparation_pipeline(db_session = None):
    """
    Exécute toutes les étapes de nettoyage et de préparation en séquence.
    """
    print("--- Début du Pipeline de Préparation Complet ---")
    try:
        stopwords.words('english')
    except LookupError:
        print("Téléchargement des listes de stopwords de NLTK...")
        nltk.download('stopwords')
        print("Téléchargement terminé.")

    if db_session:
         df = pd.read_sql_table("githubRepo", db_session.connection())
    else :
        engine = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
        )
        # Lire la table souhaitée
        df = pd.read_sql_table("githubRepo", engine)
    
    df_cleaned = clean_text_features(df)
    df_cleaned = engineer_datetime_features(df_cleaned)
    df_cleaned = clean_categorical_features(df_cleaned)
    df_cleaned = transform_numeric_features(df_cleaned)
    df_cleaned = finalize_dataset(df_cleaned)
    
    print("\n--- Pipeline de Préparation Terminé ---")
    return df_cleaned
