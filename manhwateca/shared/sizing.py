def classify_manga_size(last_chapter: int) -> str:
    if last_chapter >= 81:
        return "Longo"
    if last_chapter >= 55:
        return "Grande"
    if last_chapter >= 40:
        return "Médio"
    return "Curto"
