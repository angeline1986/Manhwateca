WORKFLOW_STEPS = [
    {
        "id": "previews",
        "label": "Gerar previews e auditoria",
        "actions": [
            "organization_preview", "rename_preview", "chapter_audit",
        ],
    },
    {
        "id": "organize",
        "label": "Revisar e aplicar organização",
        "manual": True,
        "instructions": (
            "Revise os relatórios. Use as ações individuais para aplicar "
            "organização e padronização quando estiver tudo correto."
        ),
    },
    {
        "id": "catalog",
        "label": "Catalogar biblioteca",
        "actions": ["catalog_scan"],
    },
    {
        "id": "ids",
        "label": "Buscar IDs no MangaUpdates",
        "actions": ["mangaupdates_search", "mangaupdates_refresh"],
    },
    {
        "id": "review_ids",
        "label": "Revisar correspondências de IDs",
        "manual": True,
        "instructions": (
            "Revise as obras pendentes no painel MangaUpdates e aplique "
            "as decisões antes de continuar."
        ),
    },
    {
        "id": "details",
        "label": "Consultar detalhes e atualizar CSV",
        "actions": ["mangaupdates_details", "mangaupdates_csv"],
    },
    {
        "id": "notion_catalog",
        "label": "Simular sincronização do catálogo",
        "actions": ["notion_simulate_batch"],
    },
    {
        "id": "notion_catalog_apply",
        "label": "Aplicar sincronização do catálogo",
        "manual": True,
        "instructions": (
            "Revise a simulação e use Importar lote ou Atualizar páginas "
            "com a confirmação APLICAR."
        ),
    },
    {
        "id": "notion_metadata",
        "label": "Simular atualização de metadados",
        "actions": ["notion_csv_preview"],
    },
    {
        "id": "notion_metadata_apply",
        "label": "Aplicar metadados no Notion",
        "manual": True,
        "instructions": (
            "Revise ausentes, duplicadas e propriedades. Aplique os "
            "metadados separadamente com a confirmação APLICAR."
        ),
    },
]


def public_steps():
    return [
        {
            "id": step["id"],
            "label": step["label"],
            "manual": step.get("manual", False),
            "instructions": step.get("instructions"),
        }
        for step in WORKFLOW_STEPS
    ]
