from Function.api_function import *
from Function.general_function import *
from Function.scraping_function import *

API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.environ['GIT_TOKEN'] 
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else None,
    "Accept": "application/vnd.github.mercy-preview+json"  # nécessaire pour les topics
}

######################### Get all repos #########################



def get_repo_create_and_update_date_and_id(repo):
    url = f"https://api.github.com/repos/{repo}"
    headers = HEADERS
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get('id',None), data.get("created_at", None), data.get("updated_at", None)
    else:
        print(f"Erreur API GitHub : {response.status_code}")
        return None


def get_repos_from_trending_pages():
    repos = {}  
    url = f"https://github.com/trending"
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
    (k := next(iter(repos)), repos.pop(k))  
    return repos


def scrap_repo_data(repo):
    repo_data = {}  
    url = f"https://github.com/{repo}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Erreur de chargement : {url}")

    soup                 = BeautifulSoup(response.text, "html.parser")
    description_html     = soup.find("p", class_="f4 my-3")
    tags_html            = soup.find_all("a", class_="topic-tag")
    license_html         = soup.find("a", class_="Link--muted", href=lambda x: x and "LICENSE" in x)
    stars_html           = soup.find("a", href=lambda x: x and x.endswith("/stargazers"))
    forks_html           = soup.find("a", href=lambda x: x and x.endswith("/forks"))


    parts              = repo.strip("/").split("/")
    author             = parts[0]
    repos_name         = parts[1]
    tags               = [a.get_text(strip=True) for a in tags_html] 
    description        = description_html.get_text(strip=True)  if description_html else None
    license            = license_html.get_text(strip=True).replace(" license", "") if license_html else None
    stars_count        = parse_count(stars_html.get_text(strip=True) if stars_html else "0")
    forks_count        = parse_count(forks_html.get_text(strip=True) if forks_html else "0")
    id,created,updated = get_repo_create_and_update_date_and_id(repo)
    
    repo_data['id']                      = id
    repo_data['owner']                   = author
    repo_data['owner_url']               = f"https://github.com/{author}"
    repo_data['name']                    = repos_name
    repo_data['full_name']               = f"{author}/{repos_name}"
    repo_data['description']             = description
    repo_data['topics']                  = tags
    repo_data['license']                 = license
    repo_data['stargazers_count']        = stars_count
    repo_data['forks_count']             = forks_count
    repo_data['created_at']              = created
    repo_data['updated_at']              = updated
    repo_data['html_url']                = url
    repo_data['is_trending']             = True
    return repo_data



def scraped_data_repos_trending():
    repos_trending = {}
    repos = get_repos_from_trending_pages()
    #print(repos)
    for author, repo_name in repos.items():
        full_name = f"{author}/{repo_name}"
        #print(full_name)
        repo_data = scrap_repo_data(full_name)
        if repo_data and is_open_source(repo_data["license"]):
            #print(repo_data)
            repos_trending[full_name] = repo_data
    return repos_trending