from Function.api_function import *
from Function.general_function import *
from Function.scraping_function import *
from Database.mongodb import *
import time
import pandas as pd


keyword_Big_data = ["reinforcement-learning", "neural-network", "nlp", "mcp"]


def repos_mongodb(csv_file, collection_name="github_repos"):
    db = connect_mongodb(os.environ["MONGODB_GIT_HOST"],os.environ["MONGODB_GIT_NAME"])
    collection = db[collection_name]

    df = pd.read_csv(csv_file)
    for owner, repo_name,topic in zip(df['owner'], df['repos'], df['topic']):
        if topic in keyword_Big_data:

            repo_info = get_repo_info(owner, repo_name)
            time.sleep(2)

            if repo_info and is_open_source(repo_info.get("license")):
                repo_info["topic"] = topic  # facultatif

                # 👇 Évite les doublons en utilisant "full_name" comme identifiant unique
                if not collection.find_one({"full_name": repo_info.get("full_name")}):
                    collection.insert_one(repo_info)
                    print(f"✅ {repo_info['full_name']} ajouté")
                else:
                    print(f"⏭️ {repo_info['full_name']} déjà existant")