import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_NOTES = PROJECT_ROOT / "reports" / "reviews" / "review_notes.md"
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
TITLE_COLOR = "\033[1;36m" if USE_COLOR else ""
LOCAL_COLOR = "\033[1;36m" if USE_COLOR else ""
API_COLOR = "\033[1;33m" if USE_COLOR else ""
NOTION_COLOR = "\033[1;35m" if USE_COLOR else ""
AUTOMATION_COLOR = "\033[1;32m" if USE_COLOR else ""
EXIT_COLOR = "\033[1;31m" if USE_COLOR else ""
RESET_COLOR = "\033[0m" if USE_COLOR else ""

MANGAUPDATES_ID_COMMAND = [
    "scripts/mangaupdates.py",
    "--fill-ids",
    "reports/integrations/buscaIds.json",
    "--delay",
    "3",
    "--limit",
    "10",
]

MANGAUPDATES_CSV_COMMAND = [
    "scripts/mangaupdates.py",
    "--update-csv-from-ids",
    "reports/integrations/buscaIds.json",
]

MANGAUPDATES_DETAILS_COMMAND = [
    "scripts/mangaupdates.py",
    "--fetch-details-from-ids",
    "reports/integrations/buscaIds.json",
    "--delay",
    "3",
    "--limit",
    "10",
]

BANNER = """
📖 MANHWATECA | Gestão e Sincronização
📂 Catálogo: data/mangas.json
────────────────────────────────────────────────
"""

MENU = f"""
📋 ESCOLHA UMA OPÇÃO:

  {LOCAL_COLOR}[ ETAPA 1: ORGANIZAÇÃO LOCAL ]{RESET_COLOR}

  {LOCAL_COLOR}1. 📄 Padronização e Auditoria{RESET_COLOR}
     Analisa pastas, capítulos e capas.

  {LOCAL_COLOR}2. 🔤 Organização Estrutural{RESET_COLOR}
     Organiza as obras em grupos alfabéticos.

  {AUTOMATION_COLOR}[ ETAPA 2: CATALOGAR BIBLIOTECA ]{RESET_COLOR}

  {AUTOMATION_COLOR}3. 📚 Catalogar Biblioteca{RESET_COLOR}
     Lê o Drive e atualiza data/mangas.json.

  {API_COLOR}[ ETAPA 3: ENRIQUECER DADOS ]{RESET_COLOR}

  {API_COLOR}4. 🔎 MangaUpdates: Localizar IDs{RESET_COLOR}
     Busca IDs e atualiza buscaIds.json.

  {API_COLOR}5. 🌐 MangaUpdates: Dados e CSV{RESET_COLOR}
     Usa dados salvos ou consulta novos detalhes na API.

  {NOTION_COLOR}[ ETAPA 4: SINCRONIZAR COM NOTION ]{RESET_COLOR}

  {NOTION_COLOR}6. 🔄 Sincronizar Catálogo{RESET_COLOR}
     Simula, importa ou atualiza páginas no Notion.

  {NOTION_COLOR}7. 📥 Atualizar Metadados{RESET_COLOR}
     Atualiza páginas existentes usando o CSV.

  {AUTOMATION_COLOR}[ AUTOMAÇÃO E SUPORTE ]{RESET_COLOR}

  {AUTOMATION_COLOR}8. 🚀 Executar Fluxo Completo{RESET_COLOR}
     Gera relatórios, cataloga e simula a sincronização.

  {AUTOMATION_COLOR}9. 🧹 Executar Testes{RESET_COLOR}
     Verifica automaticamente as principais regras do projeto.

  {EXIT_COLOR}0. ❌ Sair{RESET_COLOR}
"""


def run_command(arguments):
    command = [sys.executable, *arguments]
    print(f"\nExecutando: {' '.join(arguments)}\n")
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)

    if result.returncode == 0:
        print("\n[OK] Operação concluída.")
    else:
        print(f"\n[ERRO] Operação encerrada com código {result.returncode}.")

    return result.returncode == 0


def generate_reports():
    organize_ok = run_command(["scripts/organize.py"])
    rename_ok = run_command(["scripts/rename_files.py"])
    audit_ok = run_command(["scripts/chapter_audit.py"])
    return organize_ok and rename_ok and audit_ok


def standardization_menu():
    while True:
        print("\nPADRONIZAÇÃO DOS ARQUIVOS")
        print()
        print(f"  {TITLE_COLOR}1. 📄 Verificar organização e nomes{RESET_COLOR}")
        print("     Gera relatórios HTML com pastas e arquivos a padronizar.")
        print("     Não altera a biblioteca.")
        print()
        print(f"  {TITLE_COLOR}2. ✏️ Aplicar padronização dos arquivos{RESET_COLOR}")
        print("     Renomeia os capítulos conforme a prévia após confirmação.")
        print()
        print(f"  {TITLE_COLOR}3. 📝 Registrar ajustes da revisão{RESET_COLOR}")
        print("     Salva críticas e correções pendentes para revisão manual.")
        print()
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return generate_reports()
        if option == "2":
            return apply_file_names()
        if option == "3":
            return register_review_note()
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0, 1, 2 ou 3.")


def run_full_flow():
    steps = [
        ("Preview de organização", ["scripts/organize.py"]),
        ("Preview de renomeação", ["scripts/rename_files.py"]),
        ("Catálogo da biblioteca", ["scripts/scan.py"]),
        (
            "Simulação do próximo lote do Notion",
            ["scripts/sync.py", "--simulate-batch", "--batch-size", "25"],
        ),
    ]

    for label, command in steps:
        print(f"\n--- {label} ---")
        if not run_command(command):
            print("\nFluxo interrompido para evitar resultados incompletos.")
            return False

    return True


def confirm_sync_batch():
    print("\nEsta opção importa até 25 obras novas.")
    print("As próximas obras são escolhidas em ordem alfabética.")
    print("  1. Importar próximo lote de 25 obras")
    print("  2. Cancelar")
    confirmation = input("Escolha uma opção: ").strip()

    if confirmation != "1":
        print("\nOperação cancelada.")
        return False

    return run_command(["scripts/sync.py", "--apply-batch", "--batch-size", "25"])


def notion_menu():
    while True:
        print("\nSINCRONIZAÇÃO COM NOTION")
        print()
        print(f"  {TITLE_COLOR}1. 🔄 Simular próximo lote no Notion{RESET_COLOR}")
        print("     Mostra as próximas 25 obras e quantas ainda ficarão pendentes.")
        print()
        print(f"  {TITLE_COLOR}2. ✅ Importar próximo lote no Notion{RESET_COLOR}")
        print("     Cria até 25 obras ausentes sem duplicar as já importadas.")
        print()
        print(f"  {TITLE_COLOR}3. 🌐 Atualizar dados do MangaUpdates{RESET_COLOR}")
        print("     Consulta somente as obras com ID confirmado na configuração.")
        print()
        print(f"  {TITLE_COLOR}4. ♻️ Atualizar páginas já importadas{RESET_COLOR}")
        print("     Atualiza campos e contagens sem criar novas páginas.")
        print()
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return run_command(
                ["scripts/sync.py", "--simulate-batch", "--batch-size", "25"]
            )
        if option == "2":
            return confirm_sync_batch()
        if option == "3":
            if not run_command(["scripts/mangaupdates.py"]):
                return False
            return run_command(["scripts/scan.py"])
        if option == "4":
            return run_command(["scripts/sync.py", "--update-existing"])
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0, 1, 2, 3 ou 4.")


def mangaupdates_csv_menu():
    while True:
        print("\nMANGAUPDATES: DADOS E CSV")
        print()
        print(f"  {API_COLOR}1. 📄 Atualizar CSV com dados salvos{RESET_COLOR}")
        print("     Usa somente o cache local. Não consulta a API.")
        print()
        print(f"  {API_COLOR}2. 🌐 Consultar próximo lote na API{RESET_COLOR}")
        print("     Busca detalhes de até 10 IDs e atualiza o CSV.")
        print()
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return run_command(MANGAUPDATES_CSV_COMMAND)
        if option == "2":
            if not run_command(MANGAUPDATES_DETAILS_COMMAND):
                return False
            return run_command(MANGAUPDATES_CSV_COMMAND)
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0, 1 ou 2.")


def confirm_library_change(label, action_label, command):
    print(f"\nEsta opção {label}.")
    print(f"  1. {action_label}")
    print("  2. Cancelar")
    confirmation = input("Escolha uma opção: ").strip()

    if confirmation != "1":
        print("\nOperação cancelada.")
        return False

    return run_command(command)


def apply_organization():
    return confirm_library_change(
        "move as pastas da biblioteca",
        "Aplicar organização alfabética",
        ["scripts/organize.py", "--apply"],
    )


def organization_menu():
    while True:
        print("\nORGANIZAÇÃO ALFABÉTICA")
        print()
        print(f"  {TITLE_COLOR}1. 📚 Aplicar organização alfabética{RESET_COLOR}")
        print("     Move as pastas para os grupos alfabéticos após confirmação.")
        print()
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return apply_organization()
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0 ou 1.")


def run_tests():
    return run_command([
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ])


def apply_file_names():
    return confirm_library_change(
        "renomeia arquivos de capítulos",
        "Aplicar padronização dos arquivos",
        ["scripts/rename_files.py", "--apply"],
    )


def register_review_note():
    print("\nDescreva o ajuste necessário.")
    note = input("Observação: ").strip()

    if not note:
        print("\nNenhuma observação registrada.")
        return False

    REVIEW_NOTES.parent.mkdir(parents=True, exist_ok=True)
    if not REVIEW_NOTES.exists():
        REVIEW_NOTES.write_text(
            "# Ajustes pendentes da revisão\n\n",
            encoding="utf-8",
        )

    with REVIEW_NOTES.open("a", encoding="utf-8") as file:
        file.write(f"- [ ] {note}\n")

    try:
        display_path = REVIEW_NOTES.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = REVIEW_NOTES

    print(f"\nObservação registrada em {display_path}.")
    return True


def confirm_csv_notion_update():
    print("\nEsta opção atualiza páginas existentes usando o CSV.")
    print("Nenhuma página nova será criada.")
    print("  1. Atualizar Notion com reports/integrations/manhwateca_import.csv")
    print("  2. Cancelar")
    confirmation = input("Escolha uma opção: ").strip()
    if confirmation != "1":
        print("\nOperação cancelada.")
        return False

    if not run_command(["scripts/notion_csv.py"]):
        return False

    print("\nA simulação foi concluída.")
    print("  1. Aplicar as atualizações")
    print("  2. Cancelar")
    confirmation = input("Escolha uma opção: ").strip()
    if confirmation != "1":
        print("\nAplicação cancelada.")
        return False
    return run_command(["scripts/notion_csv.py", "--apply"])


def pause():
    input("\nPressione Enter para voltar ao menu...")


def main():
    actions = {
        "1": standardization_menu,
        "2": organization_menu,
        "3": lambda: run_command(["scripts/scan.py"]),
        "4": lambda: run_command(MANGAUPDATES_ID_COMMAND),
        "5": mangaupdates_csv_menu,
        "6": notion_menu,
        "7": confirm_csv_notion_update,
        "8": run_full_flow,
        "9": run_tests,
    }

    while True:
        print(BANNER)
        print(MENU)
        option = input("Opção: ").strip()

        if option == "0":
            print("\nAté a próxima.")
            return

        action = actions.get(option)
        if action is None:
            print("\nOpção inválida. Escolha um número de 0 a 9.")
            pause()
            continue

        action()
        pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nMenu encerrado.")
