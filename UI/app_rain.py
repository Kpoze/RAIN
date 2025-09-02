import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def register_user(email, password, first_name, last_name):
    try:
        user_data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name
        }
        response = requests.post(f"{os.environ['BASE_URL']}/auth/register", json=user_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        st.error(f"Erreur d'inscription : {err.response.json().get('detail', 'Erreur inconnue')}")
        return None


def login(email, password):
    try:
        response = requests.post(f"{os.environ['BASE_URL']}/auth/login", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.HTTPError as err:
        st.error(f"Erreur de connexion : {err.response.json().get('detail', 'Erreur inconnue')}")
        return None

def get_repos_by_keywords(token, keywords_list): # Accepte une liste
    headers = {"Authorization": f"Bearer {token}"}
    # La librairie requests gère la conversion de la liste en paramètres ?keywords=...&keywords=...
    params = {"keywords": keywords_list}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/repos/by_keywords", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_similar_repos(token, project_name):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/similar/{project_name}", headers=headers)
    response.raise_for_status()
    return response.json()

# --- Initialisation de l'état de la session ---
if 'token' not in st.session_state:
    st.session_state.token = None
if 'selected_repo' not in st.session_state:
    st.session_state.selected_repo = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'view' not in st.session_state:
    st.session_state.view = 'search'

# --- Fonctions d'affichage pour chaque "page" ---
def render_register_page():
    st.subheader("Créer un nouveau compte")
    with st.form("register_form"):
        new_email = st.text_input("Email")
        new_first_name = st.text_input("Prénom")
        new_last_name = st.text_input("Nom")
        new_password = st.text_input("Mot de passe", type="password")

        submitted = st.form_submit_button("Créer mon compte")
        if submitted:
            user = register_user(new_email, new_password, new_first_name, new_last_name)
            if user:
                st.success(f"Compte créé avec succès pour {user['email']} ! Vous pouvez maintenant vous connecter.")
                st.session_state.view = 'search' # On retourne à la page de connexion/recherche
                st.rerun()

    if st.button("⬅️ Retour à la connexion"):
        st.session_state.view = 'search'
        st.rerun()

        
def render_search_page():
    st.subheader("Rechercher des projets par mots-clés")
    # On change le message pour guider l'utilisateur
    keyword_string = st.text_input("Entrez un ou plusieurs mots-clés séparés par des virgules (ex: python, api, ia) :", key="keyword_input")

    if st.button("Rechercher", key="search_button"):
        st.session_state.selected_repo = None 
        if keyword_string:
            # On transforme la chaîne de caractères en une liste de mots-clés
            keywords_list = [k.strip().lower() for k in keyword_string.split(',')]

            with st.spinner(f"Recherche des projets avec les mots-clés : {', '.join(keywords_list)}..."):
                # On appelle la nouvelle fonction avec la liste
                repos = get_repos_by_keywords(st.session_state.token, keywords_list)
                st.session_state.search_results = repos
                print(repos[0])
        else:
            st.session_state.search_results = []
    if st.session_state.search_results is not None:    
        st.success(f"{len(st.session_state.search_results)} projets trouvés.")
        st.subheader(f"Résultats de la recherche :")
        num_columns = 4
        cols = st.columns(num_columns)
        for i, repo in enumerate(st.session_state.search_results):
            with cols[i % num_columns]:
                with st.container(border=True):
                    st.subheader(f"{repo['owner']}/{repo['name']}")
                    st.caption(f"{repo.get('description_translated', '')[:100]}...")
                    if st.button("Voir les détails", key=str(repo['id'])):
                        st.session_state.selected_repo = repo
                        st.session_state.view = 'details' # <-- On change de page
                        st.rerun()
    else:
        st.info("Aucun projet trouvé.")

def render_details_page():
    repo = st.session_state.selected_repo
    
    if st.button("⬅️ Retour à la recherche"):
        st.session_state.view = 'search'
        st.session_state.selected_repo = None
        st.rerun()

    st.header(f"Détails de :{repo['owner']}/{repo['name']}")
    st.markdown(f"**Description :** {repo['description_translated']}")
    st.markdown(f"**Lien GitHub :** [{repo['html_url']}]({repo['html_url']})")
    
    with st.spinner(f"Recherche de projets similaires à {repo['name']}..."):
        similar = get_similar_repos(st.session_state.token, repo['name'])
        st.subheader("5 Projets Similaires :")
        if not similar:
            st.info("Aucun projet similaire trouvé.")
        else:
            for sim_repo in similar:
                st.markdown(f"- **[{sim_repo['owner']}/{sim_repo['name']}]({sim_repo['url']})** (Score: {sim_repo['similarity_score']})")

# --- Interface Principale ---
st.set_page_config(page_title="RAIN Project Recommender", layout="wide")
st.title("🚀 R.A.I.N. - Recommandation de Projets IA")

# Sidebar pour la connexion (inchangée)
with st.sidebar:
    st.header("Authentification")
    if st.session_state.token:
        st.success("Connecté !")
        if st.button("Se déconnecter"):
            # Réinitialiser tous les états à la déconnexion
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    else: 
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            token = login(email, password)
            if token:
                st.session_state.token = token
                st.rerun()
        st.divider() # --- AJOUT ---
        if st.button("Pas encore de compte ? S'inscrire"):
            st.session_state.view = 'register' 
            st.rerun() 

if st.session_state.token:
    try:
        if st.session_state.view == 'search':
            render_search_page()
        elif st.session_state.view == 'details':
            render_details_page()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de communication avec l'API : {e}")
else:
    # Si pas connecté, on peut être sur la page de login ou d'inscription
    if st.session_state.view == 'register':
        render_register_page()
    else:
        st.warning("Veuillez vous connecter pour utiliser l'application.")