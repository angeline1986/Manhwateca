def infer_format(details):
    series_type = details.get("type")
    related_types = {
        item.get("relation_type", "").casefold()
        for item in details.get("related_series", [])
    }
    related_names = " ".join(
        item.get("related_series_name", "")
        for item in details.get("related_series", [])
    ).casefold()
    has_novel = "novel" in related_names and "adapted from" in related_types
    if series_type == "Manhwa" and has_novel:
        return "Manhwa e Novel"
    if series_type in {"Manhwa", "Novel"}:
        return series_type
    return series_type


def summarize_series(details):
    categories = [
        item["category"]
        for item in details.get("categories", [])
        if item.get("category")
    ]
    universe = []
    category_names = {category.casefold() for category in categories}
    if "omegaverse" in category_names:
        universe.append("Omegaverse")
    if any("fantasy" in category for category in category_names):
        universe.append("Fantasia")
    if "xianxia" in category_names:
        universe.append("Xianxia")

    return {
        "series_id": details["series_id"],
        "title": details["title"],
        "url": details.get("url"),
        "type": details.get("type"),
        "format": infer_format(details),
        "year": details.get("year"),
        "latest_chapter": details.get("latest_chapter"),
        "status": details.get("status"),
        "completed": details.get("completed"),
        "genres": [
            item["genre"]
            for item in details.get("genres", [])
            if item.get("genre")
        ],
        "categories": categories,
        "associated_titles": [
            item["title"]
            for item in details.get("associated", [])
            if item.get("title")
        ],
        "universe": universe,
    }
