FROM python:3.12

WORKDIR /app
ENV PYTHONPATH=/app

# On installe les dépendances spécifiques au monitoring
COPY Requirements/requirements-monitoring.txt .
RUN pip install -r requirements-monitoring.txt

# On copie tout le code pour que les imports fonctionnent
COPY . .