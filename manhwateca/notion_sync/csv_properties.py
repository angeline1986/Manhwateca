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
    properties = build_progress_properties(row)
    properties.update(build_metadata_properties(row))
    return properties


def build_progress_properties(row):
    properties = {
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
    }
    last_read = optional_number(row.get("Último lido"))
    if last_read is not None:
        properties["Último lido"] = {"number": last_read}
    _add_select_fields(properties, row, {"Tamanho": "Tamanho"})
    return properties


def build_metadata_properties(row):
    properties = {
        "Cap MangaUpdates": {
            "number": optional_number(row.get("Capítulo MangaUpdates"))
        },
        "MangaUpdates": {"url": row.get("MangaUpdates") or None},
        "ID da obra": {"number": optional_number(row.get("ID da obra"))},
    }
    aliases = split_values(row.get("Alias"))
    if aliases:
        properties["Alias"] = {
            "rich_text": [{"text": {"content": ", ".join(aliases)}}]
        }
    _add_multi_select_fields(
        properties,
        row,
        {"Temática": "Temática", "Universo": "Universo"},
    )
    _add_select_fields(
        properties,
        row,
        {
            "Formato": "Formato",
            "Picância": "Picância",
            "Interesse": "Interesse",
        },
    )
    return properties


def _add_multi_select_fields(properties, row, fields):
    for source, target in fields.items():
        if row.get(source):
            properties[target] = {
                "multi_select": [
                    {"name": value} for value in split_values(row[source])
                ]
            }


def _add_select_fields(properties, row, fields):
    for source, target in fields.items():
        if row.get(source):
            properties[target] = {"select": {"name": row[source]}}
