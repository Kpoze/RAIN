from .database import engine
from .model import User # Assurez-vous d'importer le fichier où votre classe User est définie

print("Création de la table 'users' si elle n'existe pas...")

# On cible la table du modèle 'User' et on la crée.
# checkfirst=True est l'équivalent de "CREATE TABLE IF NOT EXISTS".
User.__table__.create(bind=engine, checkfirst=True)

print("Table 'users' vérifiée/créée avec succès.")
