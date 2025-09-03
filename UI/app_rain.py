import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# --- Fonctions API (inchangées) ---

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

def get_repos_by_keywords(token, keywords_list):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keywords": keywords_list}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/repos/by_keywords", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_similar_repos(token, project_name):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/similar/{project_name}", headers=headers)
    response.raise_for_status()
    return response.json()

def get_topics(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/topics", headers=headers)
    response.raise_for_status()
    return pd.DataFrame(response.json())

def get_repos_for_topic(token, topic_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{os.environ['BASE_URL']}/ai/topics/{topic_id}/repos", headers=headers)
    response.raise_for_status()
    return response.json()

# --- Initialisation de l'état de la session (inchangée) ---
if 'token' not in st.session_state: st.session_state.token = None
if 'view' not in st.session_state: st.session_state.view = 'login'
if 'selected_repo' not in st.session_state: st.session_state.selected_repo = None
if 'search_results' not in st.session_state: st.session_state.search_results = None
if 'topic_repos' not in st.session_state: st.session_state.topic_repos = None
if 'selected_topic_name' not in st.session_state: st.session_state.selected_topic_name = None

# --- Fonctions de Rendu des Pages ---

def render_login_page():
    with st.sidebar:
        st.header("Authentification")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            token = login(email, password)
            if token:
                st.session_state.token = token
                st.session_state.view = 'main' # On passe à une vue neutre qui affichera les onglets
                st.rerun()
        st.divider()
        if st.button("Pas encore de compte ? S'inscrire"):
            st.session_state.view = 'register'
            st.rerun()
    st.warning("Veuillez vous connecter pour utiliser l'application.")

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
                st.session_state.view = 'login'
                st.rerun()
    if st.button("⬅️ Retour à la connexion"):
        st.session_state.view = 'login'
        st.rerun()
        
def render_search_page():
    st.subheader("Rechercher des projets par mots-clés")
    keyword_string = st.text_input("Entrez un ou plusieurs mots-clés séparés par des virgules (ex: python, api, ia) :", key="keyword_input")

    if st.button("Rechercher", key="search_button"):
        st.session_state.selected_repo = None
        if keyword_string:
            keywords_list = [k.strip().lower() for k in keyword_string.split(',')]
            with st.spinner(f"Recherche des projets avec les mots-clés : {', '.join(keywords_list)}..."):
                repos = get_repos_by_keywords(st.session_state.token, keywords_list)
                st.session_state.search_results = repos
        else:
            st.session_state.search_results = []
    
    if st.session_state.search_results is not None:
        if st.session_state.search_results:
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
                            st.session_state.view = 'details'
                            st.rerun()
        # else:
            # st.info("Aucun projet trouvé.") # Optionnel, peut être redondant si la recherche n'a pas été lancée

def render_details_page():
    repo = st.session_state.selected_repo
    
    # Amélioration : Un seul bouton de retour.
    # Il serait encore mieux de sauvegarder la page précédente pour un retour intelligent.
    if st.button("⬅️ Retour"):
        st.session_state.view = 'main' # Retourne à la vue principale avec les onglets
        st.session_state.selected_repo = None
        st.rerun()

    # Amélioration : Un seul header
    st.header(f"Détails de : {repo['owner']}/{repo['name']}")
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

def render_topic_explorer_page():
    st.subheader("Explorer les projets par thème sémantique")

    with st.spinner("Chargement des thèmes..."):
        topics_df = get_topics(st.session_state.token)
        if 'Representation' not in topics_df.columns:
            st.error("La colonne 'Representation' est manquante dans les données des thèmes.")
            return

    for index, row in topics_df.iterrows():
        st.markdown(f"#### {row['Name']}")
        keywords_str = ", ".join(row['Representation'])
        st.caption(f"Mots-clés : {keywords_str}")
        
   
        if st.button("Voir les projets de ce thème", key=f"topic_{row['Topic']}"):
            repos_from_api = get_repos_for_topic(st.session_state.token, row['Topic'])
            st.session_state.selected_topic_repos = repos_from_api if repos_from_api is not None else []
            st.session_state.selected_topic_name = row['Name']
            st.session_state.view = 'topic_repos'
            st.rerun()

def render_topic_repos_page():
    st.subheader(f"Projets pour le thème : {st.session_state.selected_topic_name}")

    if st.button("⬅️ Retour à l'explorateur de thèmes"):
        st.session_state.view = 'topic_explorer' # 'main' ou 'topic_explorer' pour revenir aux onglets
        st.session_state.selected_topic_repos = None
        st.rerun()

    repos = st.session_state.selected_topic_repos
    if not repos:
        st.info("Aucun projet trouvé pour ce thème.")
    else:
        num_columns = 4
        cols = st.columns(num_columns)
        for i, repo in enumerate(repos):
            with cols[i % num_columns]:
                with st.container(border=True):
                    st.subheader(repo['name'])
                    st.caption(f"{repo.get('description_translated', '')[:100]}...")
                    if st.button("Voir les détails et similaires", key=str(repo['id'])):
                        st.session_state.selected_repo = repo
                        st.session_state.view = 'details'
                        st.rerun()

# --- Interface Principale (CORRIGÉE) ---
st.set_page_config(page_title="RAIN Project Recommender", layout="wide")
st.title("🌧️ R.A.I.N. - Recommandation de Projets IA")

if not st.session_state.token:
    if st.session_state.view == 'register':
        render_register_page()
    else:
        render_login_page()
else:
    # L'utilisateur est connecté
    with st.sidebar:
        st.header(f"Bienvenue !")
        st.success("Connecté")
        if st.button("Se déconnecter"):
            # Pour éviter les erreurs, on ne modifie pas le dictionnaire sur lequel on itère
            keys_to_delete = list(st.session_state.keys())
            for key in keys_to_delete:
                del st.session_state[key]
            st.rerun()

    # --- NOUVELLE LOGIQUE DE ROUTAGE ---
    # On se base sur la valeur de 'view' pour savoir quoi afficher.
    
    if st.session_state.view == 'details':
        render_details_page()
    elif st.session_state.view == 'topic_repos':
        render_topic_repos_page()
    else:
        # Vue par défaut après connexion : les onglets
        tab1, tab2 = st.tabs(["Recherche par Mot-Clé", "Explorateur de Thèmes"])
        with tab1:
            render_search_page()
        with tab2:
            render_topic_explorer_page()
