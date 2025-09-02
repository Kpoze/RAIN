from dotenv import load_dotenv
from sqlalchemy import text
load_dotenv()


def insert_owner_repo(engine, table_name, owner, repo):
    with engine.begin() as conn:
        query = text(f"""
            INSERT INTO "{table_name}" (owner, repo)
            VALUES (:owner, :repo)
            ON CONFLICT DO NOTHING;
        """)
        conn.execute(query, {"owner": owner, "repo": repo})

def insert_repo(engine, table_name, repo_info):
    with engine.begin() as conn:
        keys = repo_info.keys()
        placeholders = ", ".join([f":{k}" for k in keys])
        columns = ", ".join([f'"{k}"' for k in keys])  # sécurise les noms de colonnes
        query = text(f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})')
        conn.execute(query, repo_info)