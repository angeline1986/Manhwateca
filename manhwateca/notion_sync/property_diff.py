def changed_properties(page, expected_properties):
    current = page.get("properties", {})
    changed = {}
    for name, expected in expected_properties.items():
        if _normalize_current(current.get(name)) != _normalize_expected(expected):
            changed[name] = expected
    return changed


def _normalize_expected(property_value):
    if "number" in property_value:
        return ("number", property_value.get("number"))
    if "url" in property_value:
        return ("url", property_value.get("url") or None)
    if "select" in property_value:
        selected = property_value.get("select")
        return ("select", selected.get("name") if selected else None)
    if "multi_select" in property_value:
        return (
            "multi_select",
            tuple(
                sorted(
                    item.get("name")
                    for item in property_value.get("multi_select", [])
                    if item.get("name")
                )
            ),
        )
    if "rich_text" in property_value:
        return (
            "rich_text",
            "".join(
                item.get("plain_text")
                or item.get("text", {}).get("content", "")
                for item in property_value.get("rich_text", [])
            ),
        )
    return ("unsupported", property_value)


def _normalize_current(property_value):
    if not property_value:
        return None
    property_type = property_value.get("type")
    if property_type == "number":
        return ("number", property_value.get("number"))
    if property_type == "url":
        return ("url", property_value.get("url") or None)
    if property_type == "select":
        selected = property_value.get("select")
        return ("select", selected.get("name") if selected else None)
    if property_type == "multi_select":
        return (
            "multi_select",
            tuple(
                sorted(
                    item.get("name")
                    for item in property_value.get("multi_select", [])
                    if item.get("name")
                )
            ),
        )
    if property_type == "rich_text":
        return (
            "rich_text",
            "".join(
                item.get("plain_text")
                or item.get("text", {}).get("content", "")
                for item in property_value.get("rich_text", [])
            ),
        )
    return ("unsupported", property_value)
