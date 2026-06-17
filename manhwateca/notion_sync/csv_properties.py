MULTI_VALUE_SEPARATOR = "|"


def split_values(value):
    return [
        item.strip()
        for item in (value or "").split(MULTI_VALUE_SEPARATOR)
        if item.strip()
    ]


def optional_number(value):
    value = (value or "").strip()
    if not value:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def build_properties(row):
    properties = {
        "Alias": {
            "rich_text": [{
                "text": {"content": ", ".join(split_values(row.get("Alias")))}
            }]
        },
        "Último cap disponível": {
            "number": optional_number(row.get("Último capítulo disponível"))
        },
        "Caps encontrados": {
            "number": optional_number(row.get("Capítulos encontrados"))
        },
        "Side stories": {
            "number": optional_number(row.get("Side stories"))
        },
        "Status da contagem": {
            "select": (
                {"name": row["Status da contagem"]}
                if row.get("Status da contagem")
                else None
            )
        },
        "Cap MangaUpdates": {
            "number": optional_number(row.get("Capítulo MangaUpdates"))
        },
        "MangaUpdates": {"url": row.get("MangaUpdates") or None},
        "ID da obra": {"number": optional_number(row.get("ID da obra"))},
    }
    last_read = optional_number(row.get("Último lido"))
    if last_read is not None:
        properties["Último lido"] = {"number": last_read}
    _add_optional_fields(properties, row)
    return properties


def _add_optional_fields(properties, row):
    multi_selects = {"Temática": "Temática", "Universo": "Universo"}
    selects = {
        "Formato": "Formato",
        "Tamanho": "Tamanho",
        "Picância": "Picância",
        "Interesse": "Interesse",
    }
    for source, target in multi_selects.items():
        if row.get(source):
            properties[target] = {
                "multi_select": [
                    {"name": value} for value in split_values(row[source])
                ]
            }
    for source, target in selects.items():
        if row.get(source):
            properties[target] = {"select": {"name": row[source]}}
