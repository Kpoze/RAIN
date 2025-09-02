import sys
import os

# Ajouter le dossier parent (contenant IA et Database)
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from IA.data_prep import *

import pandas as pd
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import spacy

def train_and_save_model(output_model_path):
    """
    Charge le jeu de données nettoyé, entraîne le modèle BERTopic final
    et le sauvegarde sur le disque.

    Args:
        input_filepath (str): Chemin vers le fichier CSV du DataFrame "parfait".
        output_model_path (str): Chemin où sauvegarder le modèle BERTopic entraîné.
    """
    print("--- Début de l'entraînement du modèle final ---")
    df  = run_full_preparation_pipeline()

    # S'assurer que la colonne de texte existe
    if 'cleaned_text' not in df.columns:
        print("Erreur : La colonne 'cleaned_text' est manquante dans le DataFrame.")
        return
        
    # La lemmatisation n'est pas nécessaire ici car le texte est déjà nettoyé.
    # On utilise directement la colonne 'cleaned_text'.
    corpus = df['cleaned_text'].dropna().tolist()
    print(f"{len(corpus)} documents chargés.")

    # --- 2. Configuration du Modèle ---
    # Utilisation de la configuration optimale identifiée lors du benchmark
    
    # Modèle d'embedding
    embedding_model = SentenceTransformer(os.environ['MODEL_EMBEDDING_NAME'])

    # Vectoriseur pour la représentation des thèmes
    vectorizer_model = CountVectorizer(ngram_range=(1, 2), min_df=5, stop_words="english")

    # Configuration de BERTopic
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        min_topic_size=15,
        verbose=True
    )

    # --- 3. Entraînement ---
    print("\nEntraînement du modèle BERTopic...")
    topics, _ = topic_model.fit_transform(corpus)

    # --- 4. Sauvegarde ---
    print(f"\nSauvegarde du modèle entraîné à l'emplacement : {output_model_path}")
    # La méthode .save() gère la sérialisation de tous les composants du modèle
    #topic_model.save(output_model_path)
    topic_model.save(output_model_path, save_embedding_model=False)

    print("\n--- Processus terminé. L'artefact du modèle a été créé. ---")
    
    # Afficher un aperçu des thèmes découverts
    print("\nAperçu des thèmes découverts :")
    print(topic_model.get_topic_info().head(10))



train_and_save_model(os.environ['MODEL_SAVE_PATH'])