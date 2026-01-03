import requests

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "TrivalayaScraper/1.0"
})

def get(url, *, timeout=20):
    response = SESSION.get(url, timeout=timeout)
    response.raise_for_status()
    return response
