SAFE_ACTIONS = {
    "organization_preview": {
        "label": "Preview de organização",
        "description": "Analisa onde cada pasta deveria ficar na organização alfabética.",
        "result": "Gera organize_preview.html sem mover nenhuma pasta.",
        "command": ["scripts/organize.py"],
        "reports": ["reports/audits/organize_preview.html"],
        "group": "library",
    },
    "rename_preview": {
        "label": "Preview de padronização",
        "description": "Analisa nomes de capítulos, capas e títulos fora do padrão.",
        "result": "Gera rename_preview.html sem renomear arquivos.",
        "command": ["scripts/rename_files.py"],
        "reports": ["reports/audits/rename_preview.html"],
        "group": "library",
    },
    "chapter_audit": {
        "label": "Auditoria de capítulos",
        "description": "Explica divergências de capítulos e arquivos não interpretados.",
        "result": "Gera chapter_audit.html para revisão.",
        "command": ["scripts/chapter_audit.py"],
        "reports": ["reports/audits/chapter_audit.html"],
        "group": "library",
    },
    "catalog_scan": {
        "label": "Catalogar biblioteca",
        "description": "Lê novamente todas as pastas e capítulos da biblioteca.",
        "result": "Atualiza o PostgreSQL e os indicadores da Biblioteca.",
        "command": ["scripts/scan.py"],
        "reports": [],
        "group": "library",
    },
    "run_tests": {
        "label": "Executar testes",
        "description": "Verifica automaticamente as regras principais do sistema.",
        "result": "Exibe no histórico quais testes passaram ou falharam.",
        "command": ["-m", "unittest", "discover", "-s", "tests"],
        "reports": [],
        "group": "tests",
    },
    "apply_organization": {
        "label": "Aplicar organização alfabética",
        "description": "Move as pastas para os grupos alfabéticos corretos.",
        "result": "Altera a estrutura física da biblioteca após confirmação.",
        "command": ["scripts/organize.py", "--apply"],
        "reports": ["reports/audits/organize_preview.html"],
        "group": "library",
        "requires_confirmation": True,
    },
    "apply_renaming": {
        "label": "Aplicar padronização dos arquivos",
        "description": "Renomeia capítulos e capas conforme o preview revisado.",
        "result": "Altera os arquivos físicos após confirmação.",
        "command": ["scripts/rename_files.py", "--apply"],
        "reports": ["reports/audits/rename_preview.html"],
        "group": "library",
        "requires_confirmation": True,
    },
    "mangaupdates_search": {
        "label": "Buscar próximo lote de IDs",
        "description": "Pesquisa até 10 obras ainda sem correspondência confirmada.",
        "result": "Atualiza buscaIds.json; resultados duvidosos aparecem abaixo.",
        "command": [
            "scripts/mangaupdates.py", "--fill-ids",
            "reports/integrations/buscaIds.json",
            "--delay", "3", "--limit", "10",
        ],
        "reports": [],
        "group": "mangaupdates",
        "accepts_initials": True,
    },
    "mangaupdates_refresh": {
        "label": "Atualizar candidatos incompletos",
        "description": "Refaz consultas de candidatos sem link, descrição ou classificação.",
        "result": "Completa os candidatos existentes em buscaIds.json.",
        "command": [
            "scripts/mangaupdates.py", "--refresh-incomplete-candidates",
            "reports/integrations/buscaIds.json",
            "--delay", "3", "--limit", "10",
        ],
        "reports": [],
        "group": "mangaupdates",
    },
    "mangaupdates_details": {
        "label": "Consultar detalhes dos IDs",
        "description": "Consulta detalhes das obras cujos IDs já foram confirmados.",
        "result": "Atualiza o cache local em data/mangaupdates.json.",
        "command": [
            "scripts/mangaupdates.py", "--fetch-details-from-ids",
            "reports/integrations/buscaIds.json",
            "--delay", "3", "--limit", "10",
        ],
        "reports": [],
        "group": "mangaupdates",
    },
    "mangaupdates_force_refresh": {
        "label": "Forçar atualização do cache",
        "description": "Reconsulta IDs confirmados mesmo quando já existe cache válido.",
        "result": "Consome chamadas externas de propósito e respeita o delay.",
        "command": [
            "scripts/mangaupdates.py", "--fetch-details-from-ids",
            "reports/integrations/buscaIds.json",
            "--delay", "3", "--limit", "10", "--force-refresh",
        ],
        "reports": [],
        "group": "mangaupdates",
        "requires_confirmation": True,
    },
    "mangaupdates_csv": {
        "label": "Atualizar CSV com dados salvos",
        "description": "Usa IDs e detalhes já salvos, sem chamar a API.",
        "result": "Atualiza manhwateca_import.csv preservando campos manuais.",
        "command": [
            "scripts/mangaupdates.py", "--update-csv-from-ids",
            "reports/integrations/buscaIds.json",
        ],
        "reports": [],
        "group": "mangaupdates",
    },
    "notion_simulate_batch": {
        "label": "Simular próximo lote no Notion",
        "description": "Compara o catálogo local com as páginas existentes.",
        "result": "Mostra até 25 páginas que seriam criadas; não altera o Notion.",
        "command": [
            "scripts/sync.py", "--simulate-batch", "--batch-size", "25",
        ],
        "reports": [],
        "group": "notion",
    },
    "notion_apply_batch": {
        "label": "Importar próximo lote no Notion",
        "description": "Cria as próximas páginas ausentes identificadas na simulação.",
        "result": "Cria até 25 páginas no Notion após confirmação.",
        "command": [
            "scripts/sync.py", "--apply-batch", "--batch-size", "25",
        ],
        "reports": [],
        "group": "notion",
        "requires_confirmation": True,
    },
    "notion_update_existing": {
        "label": "Atualizar páginas já importadas",
        "description": "Envia progresso local e contagens para páginas existentes.",
        "result": "Não cria páginas novas e não altera metadados externos.",
        "command": ["scripts/sync.py", "--update-existing"],
        "reports": [],
        "group": "notion",
        "requires_confirmation": True,
    },
    "notion_csv_preview": {
        "label": "Simular atualização dos metadados",
        "description": "Compara a fonte enriquecida com as páginas existentes.",
        "result": "Lista campos que seriam alterados sem escrever no Notion.",
        "command": ["scripts/notion_csv.py", "--source", "auto"],
        "reports": [],
        "group": "notion",
    },
    "notion_csv_apply": {
        "label": "Aplicar metadados",
        "description": "Envia nomes oficiais, aliases e demais metadados enriquecidos.",
        "result": "Atualiza páginas existentes após confirmação.",
        "command": ["scripts/notion_csv.py", "--source", "auto", "--apply"],
        "reports": [],
        "group": "notion",
        "requires_confirmation": True,
    },
}


def public_actions():
    return {
        name: {
            "label": config["label"],
            "reports": config["reports"],
            "group": config["group"],
            "requires_confirmation": config.get(
                "requires_confirmation", False
            ),
            "accepts_initials": config.get("accepts_initials", False),
            "description": config.get("description", ""),
            "result": config.get("result", ""),
        }
        for name, config in SAFE_ACTIONS.items()
    }


def build_command(config, parameters):
    command = list(config["command"])
    if config.get("accepts_initials"):
        initials = "".join(
            character
            for character in str(parameters.get("initials", "")).upper()
            if character.isalpha()
            or character.isdigit()
            or character == "-"
        )[:30]
        if initials:
            command.extend(["--initials", initials])
    return command
