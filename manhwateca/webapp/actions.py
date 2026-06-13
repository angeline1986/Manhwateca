SAFE_ACTIONS = {
    "organization_preview": {
        "label": "Preview de organização",
        "command": ["scripts/organize.py"],
        "reports": ["reports/audits/organize_preview.html"],
        "group": "library",
    },
    "rename_preview": {
        "label": "Preview de padronização",
        "command": ["scripts/rename_files.py"],
        "reports": ["reports/audits/rename_preview.html"],
        "group": "library",
    },
    "chapter_audit": {
        "label": "Auditoria de capítulos",
        "command": ["scripts/chapter_audit.py"],
        "reports": ["reports/audits/chapter_audit.html"],
        "group": "library",
    },
    "catalog_scan": {
        "label": "Catalogar biblioteca",
        "command": ["scripts/scan.py"],
        "reports": [],
        "group": "library",
    },
    "run_tests": {
        "label": "Executar testes",
        "command": ["-m", "unittest", "discover", "-s", "tests"],
        "reports": [],
        "group": "tests",
    },
    "apply_organization": {
        "label": "Aplicar organização alfabética",
        "command": ["scripts/organize.py", "--apply"],
        "reports": ["reports/audits/organize_preview.html"],
        "group": "library",
        "requires_confirmation": True,
    },
    "apply_renaming": {
        "label": "Aplicar padronização dos arquivos",
        "command": ["scripts/rename_files.py", "--apply"],
        "reports": ["reports/audits/rename_preview.html"],
        "group": "library",
        "requires_confirmation": True,
    },
    "mangaupdates_search": {
        "label": "Buscar próximo lote de IDs",
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
        "command": [
            "scripts/mangaupdates.py", "--fetch-details-from-ids",
            "reports/integrations/buscaIds.json",
            "--delay", "3", "--limit", "10",
        ],
        "reports": [],
        "group": "mangaupdates",
    },
    "mangaupdates_csv": {
        "label": "Atualizar CSV com dados salvos",
        "command": [
            "scripts/mangaupdates.py", "--update-csv-from-ids",
            "reports/integrations/buscaIds.json",
        ],
        "reports": [],
        "group": "mangaupdates",
    },
    "notion_simulate_batch": {
        "label": "Simular próximo lote no Notion",
        "command": [
            "scripts/sync.py", "--simulate-batch", "--batch-size", "25",
        ],
        "reports": [],
        "group": "notion",
    },
    "notion_apply_batch": {
        "label": "Importar próximo lote no Notion",
        "command": [
            "scripts/sync.py", "--apply-batch", "--batch-size", "25",
        ],
        "reports": [],
        "group": "notion",
        "requires_confirmation": True,
    },
    "notion_update_existing": {
        "label": "Atualizar páginas já importadas",
        "command": ["scripts/sync.py", "--update-existing"],
        "reports": [],
        "group": "notion",
        "requires_confirmation": True,
    },
    "notion_csv_preview": {
        "label": "Simular atualização dos metadados",
        "command": ["scripts/notion_csv.py"],
        "reports": [],
        "group": "notion",
    },
    "notion_csv_apply": {
        "label": "Aplicar metadados do CSV",
        "command": ["scripts/notion_csv.py", "--apply"],
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
