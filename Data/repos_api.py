from Function.api_function import *
from Function.general_function import is_open_source
import time


API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.environ['GIT_TOKEN'] 
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else None,
    "Accept": "application/vnd.github.mercy-preview+json"  # nécessaire pour les topics
}

######################### Get Recent Repo Git by API #########################
all_keywords = ["reinforcement-learning", "neural-network", "nlp", "mcp", "ai", "machine-learning", "deep-learning","artificial-intelligence", "rag", "llm", "gpt", "ai-agent"]

def get_most_recent_repos(topic, start_date, end_date):
    repos = []
    for page in range(1, 11):
        query = f"topic:{topic} created:{start_date}..{end_date}"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": page
        }
        print(f"Fetching topic '{topic}' {start_date}..{end_date} page {page}")
        response = requests.get(API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Erreur: {response.status_code}")
            break
        data = response.json()
        repos += [repo for repo in data.get("items", []) if is_open_source(repo.get("license"))]
        if len(data.get("items", [])) < 100:
            break
        time.sleep(1)
    return repos


######################### Count recent repos #########################
def count_recent_repos(topic, start_date, end_date):
    query = f"topic:{topic} created:{start_date}..{end_date}"
    params = {
        "q": query,
        "per_page": 1
    }
    response = requests.get(API_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        return 0
    return min(response.json().get("total_count", 0), 1000)


######################### fetch recent repos ##########################
def fetch_all_recent_repos(topic):
    start_date = datetime(datetime.now().year, datetime.now().month, 1)
    end_date   = datetime.today()
    repos = []
    count = count_recent_repos(topic, start_date, end_date)
    if count >= 1000:
        mid_date = start_date + (end_date - start_date) // 2
        repos += fetch_all_recent_repos(topic, start_date, mid_date)
        repos += fetch_all_recent_repos(topic, mid_date + timedelta(days=1), end_date)
    else:
        repos += get_most_recent_repos(topic, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    return repos


############################# API ##########################

def get_repos_by_api():

    all_repositories = []

    for topic in all_keywords:
        repo_info = fetch_all_recent_repos(topic)
        #print(repos)
        all_repositories += repo_info
    return all_repositories