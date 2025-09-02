
-- init.sql - Généré automatiquement
CREATE DATABASE mlflow_db;
-- Création de la table pour les utilisateurs
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table pour les projets
CREATE TABLE IF NOT EXISTS public."githubRepo" (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    owner TEXT,
    owner_url TEXT,
    description TEXT,
    description_translated TEXT,
    license TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    html_url TEXT,
    stargazers_count INT,
    forks_count INT,
    topics TEXT[],
    is_trending BOOLEAN,
    source TEXT,
    langue TEXT
);

-- Création de la table de liaison
CREATE TABLE IF NOT EXISTS public.user_liked_repos (
    user_id INT REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INT REFERENCES public."githubRepo"(id) ON DELETE CASCADE,
    liked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, project_id)
);

-- Vider la table avant l'insertion pour éviter les doublons
TRUNCATE TABLE public."githubRepo" RESTART IDENTITY CASCADE;

-- Insertion des données des projets via la commande COPY
-- Le fichier CSV doit être dans le même dossier que ce script dans le conteneur.
COPY public."githubRepo" FROM '/docker-entrypoint-initdb.d/sql_data.csv' DELIMITER ',' CSV HEADER;
