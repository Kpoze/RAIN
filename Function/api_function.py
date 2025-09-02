import requests
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
######################### GITHUB #########################
API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN =os.environ['GIT_TOKEN'] 
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else None,
    "Accept": "application/vnd.github.mercy-preview+json"  # nécessaire pour les topics
}



######################### Get data by repo from api #########################
def get_repo_info(owner, repo,max_retries=5, backoff_factor=5):
    url      = f"https://api.github.com/repos/{owner}/{repo}"
    headers  = HEADERS
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            #print(response.json())
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[{owner}/{repo}] Tentative {attempt} échouée : {e}")

            if attempt == max_retries:
                print(f"❌ Abandon après {max_retries} tentatives.")
                return None

            wait_time = backoff_factor ** attempt
            print(f"⏳ Nouvelle tentative dans {wait_time} secondes...")
            time.sleep(wait_time)



def fetch_github_licenses():
    url = "https://api.github.com/licenses"
    response = requests.get(url)

    if response.status_code == 200:
        licenses = response.json()
        for lic in licenses:
            print(f"{lic['spdx_id']:15} | {lic['name']}")
    else:
        print(f"Erreur : {response.status_code} - {response.text}")

"""
with open("Data/github_repos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(["full_name", "html_url", "description", "created_at", "topics"])
    for repo in all_repositories:
        writer.writerow([
            repo["full_name"],
            repo["html_url"],
            repo["description"],
            repo["created_at"],
            ", ".join(repo.get("topics", []))
        ])"""