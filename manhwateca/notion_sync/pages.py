from manhwateca.notion_sync.matching import normalize_title


TITLE_PROPERTY = "Nome"


def extract_title(page, property_name=TITLE_PROPERTY):
    title_items = (
        page.get("properties", {})
        .get(property_name, {})
        .get("title", [])
    )
    return "".join(
        item.get("plain_text", "") for item in title_items
    ).strip()


def load_existing_pages(notion, database_id, property_name=TITLE_PROPERTY):
    pages_by_name = {}
    cursor = None
    while True:
        request = {"database_id": database_id, "page_size": 100}
        if cursor:
            request["start_cursor"] = cursor
        response = notion.databases.query(**request)
        for page in response.get("results", []):
            name = extract_title(page, property_name)
            if name:
                pages_by_name.setdefault(normalize_title(name), []).append(page)
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return pages_by_name
