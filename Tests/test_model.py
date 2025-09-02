
import os
import pytest
import numpy as np
import pandas as pd
from bertopic import BERTopic
from dotenv import load_dotenv
from Database.db import connect_to_db 
from IA.data_prep import run_full_preparation_pipeline
from sqlalchemy.orm import sessionmaker, Session
# On charge les variables d'environnement (chemins des modèles, etc.)
load_dotenv('Docker/.env')

@pytest.fixture(scope="module")
def df_test():
    """
    Fixture Pytest : Se connecte à la base de données locale une seule fois
    pour tous les tests de ce fichier.
    """
    try:
        engine = connect_to_db(
        os.environ['DB_NAME'],
        os.environ['DB_USER'],
        os.environ['DB_PASSWORD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT']
        )
        Session = sessionmaker(bind=engine)
        with Session() as session:
            df = run_full_preparation_pipeline(session)
        yield df 
    except Exception as e:
        pytest.fail(f"échec de la préparation des données: {e}")



@pytest.fixture(scope="module")
def topic_model():
    """
    Fixture Pytest : Charge le modèle BERTopic une seule fois pour tous les tests.
    C'est plus efficace que de le charger dans chaque test.
    """
    model_path = os.getenv('MODEL_SAVE_PATH')
    embedding_model = os.getenv('MODEL_EMBEDDING_NAME')
    
    assert model_path is not None, "Variable MODEL_SAVE_PATH non définie"
    assert embedding_model is not None, "Variable MODEL_EMBEDDING_NAME non définie"
    
    try:
        model = BERTopic.load(model_path, embedding_model=embedding_model)
        return model
    except Exception as e:
        pytest.fail(f"Le chargement du modèle a échoué : {e}")

def test_model_is_loaded(topic_model):
    """Test 1: Vérifie que le modèle a bien été chargé."""
    print("Test de chargement du modèle...")
    assert topic_model is not None
    assert isinstance(topic_model, BERTopic)
    print("OK")

def test_transform_output_format(topic_model, df_test): 
    """Test 2: Vérifie que la sortie de la prédiction a le bon format."""
    print("Test du format de sortie de .transform()...")
    
    # On récupère 2 documents de la base de données
    sample_data = df_test['cleaned_text'].head(2).tolist()
    
    # Le reste du test est inchangé
    topics, probabilities = topic_model.transform(sample_data)
    
    assert isinstance(topics, list), "La sortie 'topics' devrait être une liste."
    assert isinstance(probabilities, np.ndarray), "La sortie 'probabilities' devrait être un tableau numpy."
    assert len(topics) == len(sample_data), "Le nombre de prédictions doit correspondre au nombre de documents en entrée."
    print("OK")

def test_performance_non_regression(topic_model, df_test): 
    """Test 3: Test de non-régression basé sur des données réelles de la BDD."""
    print("Test de non-régression sur la performance...")
    try:
        sorted_df = df_test.sort_values(by="stargazers_count", ascending=False).head(20)
        fixed_test_data = sorted_df['cleaned_text'].tolist()
        assert len(fixed_test_data) > 0, "Aucune donnée de test n'a été récupérée de la BDD."
    except Exception as e:
        pytest.fail(f"Impossible de récupérer les données de test : {e}")
    
    topics, _ = topic_model.transform(fixed_test_data)
    
    # On calcule le pourcentage de bruit (outliers)
    noise_count = topics.count(-1)
    noise_percentage = (noise_count / len(fixed_test_data)) * 100
    
    # On définit un seuil acceptable.
    assert noise_percentage <= 50.0, f"Le taux de bruit ({noise_percentage:.2f}%) est trop élevé."
    print("OK")