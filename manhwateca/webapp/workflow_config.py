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
        "action_page": "organization",
        "action_label": "Ir para Organização",
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
        "manual": True,
        "action_page": "flows",
        "action_label": "Ir para Fluxos",
        "instructions": (
            "Use o fluxo operacional oficial para buscar candidatos no "
            "MangaUpdates e resolver IDs no PostgreSQL."
        ),
    },
    {
        "id": "review_ids",
        "label": "Revisar correspondências de IDs",
        "manual": True,
        "action_page": "mangaupdates",
        "action_label": "Ir para MangaUpdates",
        "instructions": (
            "Revise as obras pendentes no painel MangaUpdates e aplique "
            "as decisões antes de continuar."
        ),
    },
    {
        "id": "details",
        "label": "Consultar detalhes no banco",
        "manual": True,
        "action_page": "flows",
        "action_label": "Ir para Fluxos",
        "instructions": (
            "Use a etapa Atualizar metadados do fluxo operacional oficial. "
            "As ações web legadas do MangaUpdates foram aposentadas."
        ),
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
        "action_page": "notion",
        "action_label": "Ir para Notion",
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
        "action_page": "notion",
        "action_label": "Ir para Notion",
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
            "action_page": step.get("action_page"),
            "action_label": step.get("action_label"),
        }
        for step in WORKFLOW_STEPS
    ]
