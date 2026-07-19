MIN_CANDIDATE_SCORE = 0.64
MAX_CANDIDATES_PER_ITEM = 5


def ranked_unique_candidates(
    candidates,
    *,
    id_key="id",
    title_key="titulo",
    score_key="pontuacao",
):
    unique = {}
    for candidate in candidates:
        if candidate.get("bl") is False:
            continue
        score = candidate_score(candidate, score_key)
        if score <= MIN_CANDIDATE_SCORE:
            continue
        key = str(candidate.get(id_key) or candidate.get(title_key) or "")
        if not key:
            continue
        current = unique.get(key)
        if current is None or score > candidate_score(current, score_key):
            unique[key] = candidate
    return sorted(
        unique.values(),
        key=lambda candidate: candidate_score(candidate, score_key),
        reverse=True,
    )[:MAX_CANDIDATES_PER_ITEM]


def candidate_score(candidate, score_key="pontuacao"):
    try:
        return float(candidate.get(score_key) or 0)
    except (TypeError, ValueError):
        return 0.0
