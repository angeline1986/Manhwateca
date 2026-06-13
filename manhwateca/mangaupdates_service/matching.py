import re
import unicodedata
from difflib import SequenceMatcher


BL_GENRES = {"yaoi", "shounen ai"}
SUPPORTED_TYPES = {"Manhwa", "Manhua", "Manga", "OEL"}


def normalize_title(value):
    value = unicodedata.normalize("NFD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.casefold().replace("_", " ")
    value = re.sub(r"\([^)]*novel[^)]*\)", " novel ", value)
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def choose_search_result(title, response):
    normalized = normalize_title(title)
    exact = []
    for result in response.get("results", []):
        record = result.get("record", {})
        names = [record.get("title", ""), result.get("hit_title", "")]
        if normalized in {normalize_title(name) for name in names if name}:
            exact.append(record)

    manhwa = [record for record in exact if record.get("type") == "Manhwa"]
    if len(manhwa) == 1:
        return manhwa[0], "Exata (Manhwa)"
    if len(exact) == 1:
        return exact[0], "Exata"
    if not exact:
        return None, "Não encontrada"
    return None, "Ambígua"


def title_tokens(value):
    ignored = {
        "a", "an", "as", "at", "by", "for", "from", "in", "into",
        "of", "on", "the", "to", "with",
    }
    return {
        token
        for token in normalize_title(value).split()
        if token not in ignored
    }


def title_similarity(source, candidate):
    normalized_source = normalize_title(source)
    normalized_candidate = normalize_title(candidate)
    sequence_score = SequenceMatcher(
        None,
        normalized_source,
        normalized_candidate,
    ).ratio()
    source_tokens = title_tokens(source)
    candidate_tokens = title_tokens(candidate)
    union = source_tokens | candidate_tokens
    token_score = (
        len(source_tokens & candidate_tokens) / len(union)
        if union
        else 0
    )
    containment = (
        len(source_tokens & candidate_tokens) / len(source_tokens)
        if source_tokens
        else 0
    )
    return round(max(sequence_score, token_score, containment * 0.9), 4)


def truncate_text(value, limit=734):
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[:limit - 1].rstrip() + "…"


def rank_search_results(title, response):
    candidates = []
    seen_ids = set()
    for position, result in enumerate(response.get("results", []), start=1):
        record = result.get("record", {})
        series_id = record.get("series_id")
        if not series_id or series_id in seen_ids:
            continue
        seen_ids.add(series_id)
        candidate_title = record.get("title") or result.get("hit_title") or ""
        score = title_similarity(title, candidate_title)
        if record.get("type") == "Manhwa":
            score = min(1.0, score + 0.05)
        genres = record.get("genres") or []
        normalized_genres = {str(genre).casefold() for genre in genres}
        candidates.append({
            "id": series_id,
            "titulo": candidate_title,
            "tipo": record.get("type"),
            "ano": record.get("year"),
            "url": record.get("url"),
            "descricao": truncate_text(record.get("description")),
            "generos": genres,
            "bl": bool(normalized_genres & BL_GENRES),
            "pontuacao": round(score, 4),
            "posicao": position,
        })
    return sorted(
        candidates,
        key=lambda item: (-item["pontuacao"], item["posicao"]),
    )


def filter_relevant_candidates(candidates):
    supported = [
        candidate
        for candidate in candidates
        if candidate.get("tipo") in SUPPORTED_TYPES
    ]
    bl_candidates = [
        candidate for candidate in supported if candidate.get("bl")
    ]
    return bl_candidates or supported


def select_ranked_candidate(candidates, threshold=0.72, margin=0.08):
    if not candidates:
        return None, "Não encontrada"
    best = candidates[0]
    second_score = candidates[1]["pontuacao"] if len(candidates) > 1 else 0
    if best["pontuacao"] >= 0.99 and second_score < 0.99:
        return best, "Confirmado automaticamente"
    if second_score >= 0.65:
        return None, "Revisar"
    if (
        best["pontuacao"] >= threshold
        and best["pontuacao"] - second_score >= margin
    ):
        return best, "Confirmado automaticamente"
    return None, "Revisar"
