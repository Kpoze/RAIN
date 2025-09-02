import sys
import os

# Ajouter le dossier parent (contenant IA et Database)
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from IA.data_prep import *

import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

def generate_and_save_embeddings(model_name, output_filepath):
    """
    Charge le jeu de données, génère les embeddings sémantiques pour la colonne
    'cleaned_text' et les sauvegarde dans un fichier numpy.

    Args:
        df_filepath (str): Chemin vers le fichier CSV du DataFrame "parfait".
        model_name (str): Nom du modèle SentenceTransformer à utiliser.
        output_filepath (str): Chemin où sauvegarder le fichier .npy des embeddings.
    """
    print("--- Début de la génération des embeddings ---")

    print("--- Début de l'entraînement du modèle final ---")
    df  = run_full_preparation_pipeline()

    # S'assurer que la colonne de texte existe
    if 'cleaned_text' not in df.columns:
        print("Erreur : La colonne 'cleaned_text' est manquante dans le DataFrame.")
        return
        
    corpus = df['cleaned_text'].dropna().tolist()
    print(f"{len(corpus)} documents à vectoriser.")

    # --- 2. Vectorisation ---
    print(f"Chargement du modèle d'embedding : {model_name}")
    model = SentenceTransformer(model_name)

    print("Génération des embeddings (cela peut prendre un moment)...")
    embeddings = model.encode(corpus, show_progress_bar=True, normalize_embeddings=True)

    # --- 3. Sauvegarde ---
    print(f"Sauvegarde des embeddings dans : {output_filepath}")
    np.save(output_filepath, embeddings)

    print(f"\n--- Processus terminé. {embeddings.shape[0]} embeddings de dimension {embeddings.shape[1]} ont été sauvegardés. ---")



generate_and_save_embeddings(os.environ['MODEL_EMBEDDING_NAME'], os.environ['EMBEDDINGS_SAVE_PATH'])