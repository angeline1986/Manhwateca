import re

from manhwateca.mangaupdates_service.client import search_series


def _five_sentences(value):
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", "", value or "")
    text = re.sub(r"[*#_`]+", "", text)
    text = " ".join(text.split())
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:5]).strip()


def search_payload(query, per_page=5):
    query = str(query or "").strip()
    if len(query) < 2:
        raise ValueError("Informe ao menos 2 caracteres para pesquisar.")
    response = search_series(query, per_page=per_page)
    results = []
    for item in response.get("results", []):
        record = item.get("record") or {}
        series_id = record.get("series_id")
        if not series_id:
            continue
        results.append({
            "series_id": series_id,
            "title": record.get("title") or item.get("hit_title") or "",
            "url": record.get("url") or "",
            "description": _five_sentences(record.get("description")),
        })
    return {"query": query, "results": results}
