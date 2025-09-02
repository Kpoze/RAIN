import pytest
from fastapi.testclient import TestClient
import uuid

# On ne crée PAS le client ici. On le fera dans une fixture.

@pytest.fixture(scope="module")
def client():
    """
    Fixture qui crée et fournit un TestClient.
    Garantit que l'environnement (via conftest.py) est configuré AVANT
    que l'application FastAPI ne soit importée et démarrée.
    """
    from API.main import app # On importe l'app ICI, à l'intérieur de la fixture
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def test_user_credentials():
    """Crée des identifiants uniques pour une session de test."""
    return {
        "email": f"testuser_{uuid.uuid4()}@example.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture(scope="module")
def auth_token(client, test_user_credentials): # Le client est maintenant une dépendance
    """
    Enregistre un utilisateur et se connecte pour obtenir un token.
    """
    reg_response = client.post("/auth/register", json=test_user_credentials)
    assert reg_response.status_code == 201, f"La création de l'utilisateur a échoué : {reg_response.text}"
    
    login_data = {
        "username": test_user_credentials["email"], 
        "password": test_user_credentials["password"]
    }
    auth_response = client.post("/auth/login", data=login_data)
    assert auth_response.status_code == 200, f"La connexion a échoué : {auth_response.text}"
    
    token = auth_response.json().get("access_token")
    assert token is not None
    return token

# --- LES TESTS ---
# Tous les tests qui font un appel à l'API doivent maintenant recevoir la fixture "client"

def test_api_is_alive(client):
    response = client.get("/docs")
    assert response.status_code == 200

def test_login_fails_with_wrong_password(client, test_user_credentials):
    login_data = {"username": test_user_credentials["email"], "password": "wrongpassword"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 403

def test_protected_endpoint_fails_without_token(client):
    response = client.get("/ai/similar/fastapi")
    assert response.status_code == 401

def test_protected_endpoint_succeeds_with_token(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_name = "crewAI"
    
    response = client.get(f"/ai/similar/{project_name}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)