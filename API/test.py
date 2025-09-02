import pytest
import requests # Utilisation de la bibliothèque standard requests
import os

API_BASE_URL = "http://127.0.0.1:8000"

# --- Définition des Tests ---

def test_get_all_topics():
    """
    Teste le point de terminaison /ai/topics sur un serveur live.
    Vérifie que la réponse est réussie (code 200) et que les données
    retournées sont une liste.
    """
    print("\nLancement du test pour GET /topics...")
    response = requests.get(f"{API_BASE_URL}/topics")
    
    # Vérification 1 : Le statut de la réponse est 200 OK
    assert response.status_code == 200
    
    # Vérification 2 : La réponse est bien une liste (JSON array)
    response_data = response.json()
    assert isinstance(response_data, list)
    
    # Vérification 3 : Si la liste n'est pas vide, vérifier la structure d'un thème
    if response_data:
        first_topic = response_data[0]
        assert "Topic" in first_topic
        assert "Name" in first_topic
        assert "Count" in first_topic
    
    print("Test GET /topics réussi.")

def test_get_similar_projects_success():
    """
    Teste le point de terminaison /ai/similar/{project_name} avec un nom de projet valide.
    Vérifie que la réponse est réussie et que les données sont au bon format.
    """
    project_name = "crewAI"
    
    print(f"\nLancement du test pour GET /similar/{project_name} (cas succès)...")
    response = requests.get(f"{API_BASE_URL}/similar/{project_name}")
    
    # Vérification 1 : Le statut de la réponse est 200 OK
    assert response.status_code == 200
    
    # Vérification 2 : La réponse est une liste
    response_data = response.json()
    assert isinstance(response_data, list)
    
    # Vérification 3 : Si la liste n'est pas vide, vérifier la structure d'un projet similaire
    if response_data:
        first_project = response_data[0]
        assert "name" in first_project
        assert "similarity_score" in first_project
        assert "description" in first_project
        assert "stars" in first_project
        
    print(f"Test GET /similar/{project_name} (cas succès) réussi.")

def test_get_similar_projects_not_found():
    """
    Teste le point de terminaison /similar/{project_name} avec un nom de projet invalide.
    Vérifie que l'API retourne bien une erreur 404.
    """
    project_name = "un_projet_qui_n_existe_pas_12345"
    
    print(f"\nLancement du test pour GET /similar/{project_name} (cas erreur 404)...")
    response = requests.get(f"{API_BASE_URL}/similar/{project_name}")
    
    # Vérification 1 : Le statut de la réponse est 404 Not Found
    assert response.status_code == 404
    
    # Vérification 2 : Le message d'erreur est correct
    response_data = response.json()
    assert "detail" in response_data
    assert f"Projet '{project_name}' non trouvé" in response_data["detail"]
    
    print(f"Test GET /similar/{project_name} (cas erreur 404) réussi.")