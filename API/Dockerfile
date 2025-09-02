# Étape 1: Utiliser une image Python de base
FROM python:3.12

# Étape 2: Définir le répertoire de travail standard
WORKDIR /app
ENV PYTHONPATH=/app

# Étape 3: Copier le fichier des dépendances et les installer
COPY Requirements/requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Étape 4: Copier TOUT le code source du projet dans l'image
# C'est la version "de base" pour la production.
# Le volume de docker-compose l'écrasera en mode développement.
COPY API/ ./API
COPY Database/ ./Database
COPY IA/ ./IA
COPY Data/ ./Data
COPY Class/ ./Class
COPY Function/ ./Function

# Étape 5: Exposer le port
EXPOSE 8000

# Étape 6: Définir la commande de production par défaut
CMD ["uvicorn", "API.main:app", "--host", "0.0.0.0", "--port", "8000"]