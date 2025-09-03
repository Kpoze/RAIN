import sys
import os

# Ajouter le dossier parent (contenant IA et Database)
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from IA.data_prep import run_full_preparation_pipeline


import pandas as pd
from bertopic import BERTopic
import mlflow
from gensim.corpora import Dictionary
from gensim.models.coherencemodel import CoherenceModel
import time
import os

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URL"])

def monitor_production_model():
    """
    Charge un modèle BERTopic pré-entraîné, l'utilise pour faire de l'inférence
    sur un nouvel échantillon de données, et enregistre les métriques de performance
    dans MLflow.
    """
    print("--- Début du script de monitoring du modèle en production ---")
    start_time = time.time()
    # --- 1. Chargement des artefacts ---
    print(f"Chargement du modèle BERTopic depuis : {os.environ['MODEL_SAVE_PATH']}")
    try:
        embedding_model = os.environ['MODEL_EMBEDDING_NAME'] 
        topic_model     = BERTopic.load(os.environ['MODEL_SAVE_PATH'],embedding_model=embedding_model)
    except Exception as e:
        print(f"Erreur : Impossible de charger le modèle sauvegardé. {e}")
        return

    try:
        df  = run_full_preparation_pipeline()
    except FileNotFoundError:
        print(f"Erreur : Le fichier de données est introuvable. {e}")
        return

    # --- 2. Simulation de nouvelles données ---
    # On prend un échantillon aléatoire pour simuler un nouveau lot de données
    #df_sample = df.sample(n=min(2000, len(df)))
    corpus_new_data = df['cleaned_text'].dropna().tolist()
    tokenized_corpus = [doc.split() for doc in corpus_new_data]

    # --- 3. Inférence avec le modèle chargé ---
    # Utilisation de .transform() pour classifier les nouvelles données, SANS ré-entraînement.
    print("Classification des nouvelles données avec le modèle chargé...")
    topics, _ = topic_model.transform(corpus_new_data)

    # --- 4. Calcul des métriques de monitoring ---
    # Métrique 1 : Pourcentage de bruit (indicateur de data drift)
    noise_count = (topics == -1).sum()
    noise_percentage = (noise_count / len(corpus_new_data)) * 100 if len(corpus_new_data) > 0 else 0
    
    # Métrique 2 : Score de cohérence thématique (C_v)
    coherence_score = 0.0
    # Récupérer les thèmes du modèle chargé
    all_topics = topic_model.get_topics()
    # Exclure le thème -1 (bruit)
    topic_words = [[word for word, score in all_topics[topic_id]] for topic_id in all_topics if topic_id != -1]

    if topic_words:
        dictionary = Dictionary(tokenized_corpus)
        bow_corpus = [dictionary.doc2bow(doc) for doc in tokenized_corpus]
        coherence_model = CoherenceModel(topics=topic_words, 
                                         texts=tokenized_corpus, 
                                         corpus=bow_corpus, 
                                         dictionary=dictionary, 
                                         coherence='c_v',
                                         processes=1) # CORRECTION : Forcer l'exécution sur un seul processus
        coherence_score = coherence_model.get_coherence()

    # Métrique 3 : Temps d'exécution
    execution_time = time.time() - start_time

    print(f"\nPourcentage de bruit sur les nouvelles données : {noise_percentage:.2f}%")
    print(f"Score de cohérence (C_v) sur les nouvelles données : {coherence_score:.4f}")
    print(f"Temps d'exécution total du monitoring : {execution_time:.2f} secondes")

    # --- 5. Logging dans MLflow ---
    print("\nEnregistrement des métriques dans MLflow...")
    mlflow.set_experiment("RAIN - BERTopic Monitoring")
    print(">>> AVANT le bloc mlflow.start_run()") # <-- Espion 1
    with mlflow.start_run() as run:
    # On récupère l'ID du run qui vient d'être créé
        run_id = run.info.run_id
        print(f">>> DANS le bloc mlflow.start_run(). ID du run = {run_id}") # <-- Espion 2
        # On peut logger l'ID du modèle utilisé si on le souhaite
        # mlflow.log_param("model_version", "v1.0.0") 
        mlflow.log_metric("pourcentage_bruit_inference", noise_percentage)
        mlflow.log_metric("coherence_cv_inference", coherence_score)
        mlflow.log_metric("execution_time_s", execution_time)

        print(f">>> FIN du bloc 'with'. Run ID = {run_id}") # <-- Espion 3

        print(">>> APRÈS le bloc mlflow.start_run()") # <-- Espion 4
        print("\n--- Monitoring terminé. Métriques enregistrées dans MLflow. ---")
monitor_production_model()

    # --- Comment visualiser les résultats ---
    # 1. Ouvrez votre terminal dans le dossier racine de votre projet.
    # 2. Exécutez la commande : mlflow ui
    # 3. Ouvrez votre navigateur à l'adresse http://127.0.0.1:5000
    # 4. Sélectionnez l'expérience "RAIN - BERTopic Monitoring". Chaque exécution
    #    de ce script apparaîtra comme une nouvelle ligne, vous permettant de
    #    suivre l'évolution du pourcentage de bruit dans le temps.