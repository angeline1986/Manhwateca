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
    "release_check": {
        "label": "Verificar lançamentos",
        "description": "Consulta lançamentos recentes no MangaUpdates e atualiza o histórico local.",
        "result": "Atualiza os cards e a lista de lançamentos do Dashboard.",
        "command": ["scripts/check_releases.py"],
        "reports": [],
        "group": "release_monitor",
        "accepts_manga_id": True,
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
    if config.get("accepts_manga_id"):
        manga_id = str(parameters.get("manga_id", "")).strip()
        if manga_id.isdigit() and int(manga_id) > 0:
            command.extend(["--manga-id", manga_id])
    return command
