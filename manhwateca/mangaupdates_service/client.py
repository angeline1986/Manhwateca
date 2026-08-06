import json
import random
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode


API_BASE = "https://api.mangaupdates.com/v1"


def request_json(
    url,
    payload=None,
    retries=4,
    base_delay=3.0,
    timeout=30,
):
    data = None
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Manhwateca/1.0",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == retries:
                raise
            retry_after = error.headers.get("Retry-After")
            wait = (
                float(retry_after)
                if retry_after
                else base_delay * (2 ** attempt) + random.uniform(0, 1)
            )
            print(f"[LIMITE] Aguardando {wait:.1f}s antes de tentar novamente.")
            time.sleep(wait)
        except urllib.error.URLError:
            if attempt == retries:
                raise
            wait = base_delay * (2 ** attempt)
            print(f"[REDE] Aguardando {wait:.1f}s antes de tentar novamente.")
            time.sleep(wait)


def search_series(title, per_page=5, timeout=30, retries=4):
    return request_json(
        f"{API_BASE}/series/search",
        {"search": title, "page": 1, "perpage": per_page},
        timeout=timeout,
        retries=retries,
    )


def get_series(series_id):
    return request_json(f"{API_BASE}/series/{series_id}")


def list_releases_by_day(page=1, per_page=100, timeout=30, retries=4):
    query = urlencode({"page": page, "perpage": per_page})
    return request_json(
        f"{API_BASE}/releases/days?{query}",
        timeout=timeout,
        retries=retries,
    )
