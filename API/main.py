import sys
import os

# Ajouter le dossier parent (contenant IA et Database)
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException,Query
from bson import ObjectId
from .database import *
import numpy as np
from bertopic import BERTopic
from sentence_transformers import util
import torch
from IA.data_prep import *
from contextlib import asynccontextmanager
from starlette_prometheus import metrics, PrometheusMiddleware
from .api_auth import * 
from .schemas import *
from . import api_auth, schemas, auth_routes, model
# Variables globales pour stocker les modèles et données chargés
topic_model = None
embeddings = None
df = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Charge le modèle BERTopic, les embeddings et le DataFrame au démarrage de l'API.
    Ceci est fait une seule fois pour éviter de recharger à chaque requête.
    """
    global topic_model, embeddings, df

    db = SessionLocal()
    if not os.path.exists(os.environ['MODEL_SAVE_PATH']):
        raise RuntimeError(f"Le fichier du modèle BERTopic est introuvable à l'emplacement : {os.environ['MODEL_SAVE_PATH']}")
    if not os.path.exists(os.environ['EMBEDDINGS_SAVE_PATH']):
        raise RuntimeError(f"Le fichier des embeddings est introuvable à l'emplacement : {os.environ['EMBEDDINGS_SAVE_PATH']}")
    try : 
        print("Chargement du modèle BERTopic...")
        
        print(os.environ['MODEL_SAVE_PATH'])
        embedding_model = os.environ['MODEL_EMBEDDING_NAME'] 
        topic_model     = BERTopic.load(os.environ['MODEL_SAVE_PATH'],embedding_model=embedding_model)
        
        print("Chargement des embeddings de documents...")
        embeddings = np.load(os.environ['EMBEDDINGS_SAVE_PATH'])
        
        print("Chargement du jeu de données...")
        df  = run_full_preparation_pipeline(db)
        # S'assurer que l'index correspond aux lignes des embeddings
        df.reset_index(drop=True, inplace=True)
    finally:
        db.close()
    print("API prête à recevoir des requêtes.")
    yield

app = FastAPI(
    title="R.A.I.N. - AI Project Recommendation API",
    description="API pour explorer les thèmes de projets IA et trouver des projets similaires.",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

data_router = APIRouter(
    prefix="/data",
    tags=["Data Access"],
    dependencies=[Depends(api_auth.verify_token)] 
)


@data_router.get("/repos")
async def get_repos(current_user: schemas.UserPublic = Depends(api_auth.verify_token)):
    current_user: schemas.UserPublic = Depends(api_auth.verify_token)
    docs = await collection.find().to_list(10)
    for doc in docs:
        doc["_id"] = str(doc["_id"])  # Conversion ObjectId -> str
    return docs


@data_router.get("/repos/{repo_id_or_name}", dependencies=[Depends(verify_token)])
async def get_repo(repo_id_or_name: str):
    query = {}

    if ObjectId.is_valid(repo_id_or_name):
        query = {"_id": ObjectId(repo_id_or_name)}
    else:
        query = {"name": repo_id_or_name}

    repo = await collection.find_one(query)

    if not repo:
        raise HTTPException(status_code=404, detail="Repo non trouvé")

    repo["_id"] = str(repo["_id"])
    return repo

ai_router = APIRouter(
    prefix="/ai",
    tags=["AI Service"],
    dependencies=[Depends(api_auth.verify_token)]
)

@ai_router.get("/topics", summary="Lister tous les thèmes découverts")
async def get_all_topics():
    """
    Retourne une liste de tous les thèmes identifiés par le modèle BERTopic,
    avec leurs mots-clés et le nombre de projets associés.
    """
    if topic_model is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas encore chargé.")
    
    # Exclure le thème -1 (bruit)
    topic_info = topic_model.get_topic_info()
    return topic_info[topic_info.Topic != -1].to_dict(orient="records")


@ai_router.get("/similar/{project_name}", summary="Trouver des projets similaires")
async def get_similar_projects(project_name: str, top_k: int = 5):
    """
    Trouve les `top_k` projets les plus similaires à un projet donné.
    
    Args:
        project_name (str): Le nom exact du projet de référence.
        top_k (int): Le nombre de projets similaires à retourner.
    
    Returns:
        Une liste de projets similaires avec leur score de similarité.
    """
    if embeddings is None or df is None:
        raise HTTPException(status_code=503, detail="Les modèles/données ne sont pas encore chargés.")

    # Trouver l'index du projet de référence
    try:
        # Utiliser .loc pour une recherche plus robuste et explicite
        project_index = df.loc[df['name'] == project_name].index[0]
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Projet '{project_name}' non trouvé.")

    # Obtenir le vecteur du projet de référence
    query_embedding = torch.tensor(embeddings[project_index])
    
    # Calculer la similarité cosinus avec tous les autres projets
    cos_scores = util.cos_sim(query_embedding, embeddings)[0]
    
    # Trouver les indices des meilleurs scores
    top_results_indices = torch.topk(cos_scores, k=top_k + 1).indices.tolist()

    # Préparer la réponse
    similar_projects = []
    for idx in top_results_indices:
        # Ignorer le projet lui-même
        if idx == project_index:
            continue
        
        project_info = df.iloc[idx].to_dict()
        result = {
            "owner": project_info.get("owner"),
            "name": project_info.get("name"),
            "similarity_score": round(cos_scores[idx].item(), 4),
            "description": project_info.get("description_translated"),
            "url": project_info.get("html_url"),
            "stars": int(project_info.get("stargazers_count", 0)) # S'assurer que c'est un entier
        }
        similar_projects.append(result)
        
    return similar_projects

@ai_router.get("/repos/by_keywords", summary="Lister les repos pour plusieurs mots-clés")
async def get_repos_by_keywords(keywords: List[str] = Query(..., min_length=1)):
    """
    Retourne la liste des projets contenant TOUS les mots-clés (topics) spécifiés.
    """
    if df is None:
        raise HTTPException(status_code=503, detail="Le jeu de données n'est pas encore chargé.")

    try:
        # Convertit les mots-clés de la requête en un ensemble pour une recherche efficace
        search_keywords = set(k.lower() for k in keywords)

        # La fonction lambda vérifie si l'ensemble des mots-clés de recherche
        # est un sous-ensemble des topics du projet.
        mask = df['topics'].apply(
            lambda topics_list: isinstance(topics_list, list) and search_keywords.issubset(set(str(t).lower() for t in topics_list))
        )
        
        repos_with_keywords = df[mask]
        
        if repos_with_keywords.empty:
            return []
            
        # On s'assure que les types sont standards avant d'envoyer
        repos_list = repos_with_keywords.to_dict(orient="records")
        for repo in repos_list:
            repo['id'] = int(repo['id'])
            
        return repos_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


app.include_router(auth_routes.router)
app.include_router(ai_router)
app.include_router(data_router)

