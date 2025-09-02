
import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

load_dotenv()
######################### GITHUB #########################


######################### Get all repos by topics #########################


def get_repos_from_topic_page(topic: str, page: int):
    repos = {}  
    url = f"https://github.com/topics/{topic}?page={page}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Erreur de chargement : {url}")
        return repos

    soup       = BeautifulSoup(response.text, "html.parser")
    repos      = {}  

    repo_links = soup.find_all("a", class_="Link")

    for link in repo_links:
        href = link.get("href")
        if href:
            parts = href.strip("/").split("/")
            if len(parts) == 2 and parts[0] != "topics":
                repos[parts[0]] = parts[1]
        
    return repos  

def scrap_all_repos(keyword):
    all_repos  = {}
    page = 1
    print("####################################")
    print(keyword)
    print("####################################")
    while True:
        print(f"Récupération page {page} ...")
        repos = get_repos_from_topic_page(keyword, page)
        print(repos)
        if not repos:
            break

        for owner, repo in repos.items():
            key = f"{owner}/{repo}"
            if key not in all_repos:
                all_repos[key] = (owner, repo)               
        page += 1
        time.sleep(1)
    
    return all_repos