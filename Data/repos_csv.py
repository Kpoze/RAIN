from Function.api_function import *
from Function.general_function import *
from Function.scraping_function import *
import time
import os
import csv
import pandas as pd

all_keywords = ["reinforcement-learning", "neural-network", "nlp", "mcp", "ai", "machine-learning", "deep-learning","artificial-intelligence", "rag", "llm", "gpt", "ai-agent"]

keyword_CSV      = ["rag", "llm", "gpt", "ai-agent"]
def repos_csv(filename):
    df = pd.read_csv(filename)
    all_keys = set()
    all_data = []


    for owner, repo_name,topic in zip(df['owner'], df['repos'], df['topic']):
        if topic in keyword_CSV: 
            repo_info = get_repo_info(owner, repo_name)
            time.sleep(2)  # GitHub API rate limit
            if repo_info and is_open_source(repo_info.get("license")):
                repo_info["topic"] = topic  # facultatif
                all_keys.update(repo_info.keys())
                all_data.append(repo_info)

    all_keys = list(all_keys)

    with open("Data/repos_github.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(all_data)
