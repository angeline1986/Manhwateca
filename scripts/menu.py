import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_NOTES = PROJECT_ROOT / "reports" / "review_notes.md"
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
TITLE_COLOR = "\033[1;36m" if USE_COLOR else ""
EXIT_COLOR = "\033[1;31m" if USE_COLOR else ""
RESET_COLOR = "\033[0m" if USE_COLOR else ""

BANNER = """
╔════════════════════════════════════════════════════════════════╗
║                         MANHWATECA                             ║
║                                                                ║
║  Cataloga, organiza e sincroniza sua biblioteca de manhwas.    ║
║                                                                ║
║  Catálogo principal: data/mangas.json                          ║
╚════════════════════════════════════════════════════════════════╝
"""

MENU = f"""
📋 ESCOLHA UMA OPÇÃO:

  ┌───────────── PRINCIPAL ─────────────┐

  {TITLE_COLOR}1. 📄 Padronização dos arquivos{RESET_COLOR}
     Verifica ou aplica a padronização das pastas e capítulos.

  {TITLE_COLOR}2. 📝 Registrar ajustes da revisão{RESET_COLOR}
     Salva críticas e correções pendentes em reports/review_notes.md.

  {TITLE_COLOR}3. 📚 Aplicar organização alfabética{RESET_COLOR}
     Move as pastas para os grupos alfabéticos após confirmação.

  {TITLE_COLOR}4. 🔄 Sincronização com Notion{RESET_COLOR}
     Cataloga a biblioteca, simula ou aplica a sincronização.

  {TITLE_COLOR}5. 🚀 Executar fluxo completo{RESET_COLOR}
     Gera os relatórios, atualiza o catálogo e simula o sync.

  {TITLE_COLOR}6. 🧹 Executar testes{RESET_COLOR}
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
    return organize_ok and rename_ok


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
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return generate_reports()
        if option == "2":
            return apply_file_names()
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0, 1 ou 2.")


def run_full_flow():
    steps = [
        ("Preview de organização", ["scripts/organize.py"]),
        ("Preview de renomeação", ["scripts/rename_files.py"]),
        ("Catálogo da biblioteca", ["scripts/scan.py"]),
        ("Simulação do Notion", ["scripts/sync.py"]),
    ]

    for label, command in steps:
        print(f"\n--- {label} ---")
        if not run_command(command):
            print("\nFluxo interrompido para evitar resultados incompletos.")
            return False

    return True


def confirm_sync():
    print("\nEsta opção altera páginas no Notion.")
    print("  1. Aplicar sincronização")
    print("  2. Cancelar")
    confirmation = input("Escolha uma opção: ").strip()

    if confirmation != "1":
        print("\nOperação cancelada.")
        return False

    return run_command(["scripts/sync.py", "--apply"])


def notion_menu():
    while True:
        print("\nSINCRONIZAÇÃO COM NOTION")
        print()
        print(f"  {TITLE_COLOR}1. 🔍 Catalogar biblioteca{RESET_COLOR}")
        print("     Lê as obras e capítulos e atualiza data/mangas.json.")
        print()
        print(f"  {TITLE_COLOR}2. 🔄 Simular sincronização com Notion{RESET_COLOR}")
        print("     Mostra quais páginas seriam criadas ou atualizadas.")
        print()
        print(f"  {TITLE_COLOR}3. ✅ Aplicar sincronização com Notion{RESET_COLOR}")
        print("     Cria e atualiza páginas após confirmação.")
        print()
        print(f"  {EXIT_COLOR}0. ↩ Voltar{RESET_COLOR}")
        option = input("\nEscolha uma opção: ").strip()

        if option == "1":
            return run_command(["scripts/scan.py"])
        if option == "2":
            return run_command(["scripts/sync.py"])
        if option == "3":
            return confirm_sync()
        if option == "0":
            return True

        print("\nOpção inválida. Escolha 0, 1, 2 ou 3.")


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


def pause():
    input("\nPressione Enter para voltar ao menu...")


def main():
    actions = {
        "1": standardization_menu,
        "2": register_review_note,
        "3": apply_organization,
        "4": notion_menu,
        "5": run_full_flow,
        "6": lambda: run_command(
            ["-m", "unittest", "discover", "-s", "tests", "-v"]
        ),
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
            print("\nOpção inválida. Escolha um número de 0 a 6.")
            pause()
            continue

        action()
        pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nMenu encerrado.")
