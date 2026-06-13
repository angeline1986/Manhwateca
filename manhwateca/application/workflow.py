from pathlib import Path

from manhwateca.application import (
    commands,
    local_menus,
    main_loop,
    mangaupdates_menus,
    notes,
    notion_menu as notion_navigation,
    operations,
    presentation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
subprocess = commands.subprocess
REVIEW_NOTES = PROJECT_ROOT / "reports" / "reviews" / "review_notes.md"
USE_COLOR = presentation.USE_COLOR
TITLE_COLOR = presentation.TITLE_COLOR
LOCAL_COLOR = presentation.LOCAL_COLOR
API_COLOR = presentation.API_COLOR
NOTION_COLOR = presentation.NOTION_COLOR
AUTOMATION_COLOR = presentation.AUTOMATION_COLOR
EXIT_COLOR = presentation.EXIT_COLOR
RESET_COLOR = presentation.RESET_COLOR
BANNER = presentation.BANNER
MENU = presentation.MENU
MANGAUPDATES_ID_COMMAND = commands.MANGAUPDATES_ID_COMMAND
MANGAUPDATES_REFRESH_CANDIDATES_COMMAND = (
    commands.MANGAUPDATES_REFRESH_CANDIDATES_COMMAND
)
MANGAUPDATES_CSV_COMMAND = commands.MANGAUPDATES_CSV_COMMAND
MANGAUPDATES_DETAILS_COMMAND = commands.MANGAUPDATES_DETAILS_COMMAND


def run_command(arguments):
    return commands.run_command(arguments, PROJECT_ROOT)


def generate_reports():
    return operations.generate_reports(run_command)


def standardization_menu():
    return local_menus.standardization_menu(
        TITLE_COLOR,
        EXIT_COLOR,
        RESET_COLOR,
        generate_reports,
        apply_file_names,
        register_review_note,
    )


def run_full_flow():
    return operations.run_full_flow(run_command)


def confirm_sync_batch():
    return operations.confirm_sync_batch(run_command)


def notion_menu():
    return notion_navigation.show(
        TITLE_COLOR,
        EXIT_COLOR,
        RESET_COLOR,
        run_command,
        confirm_sync_batch,
    )


def mangaupdates_csv_menu():
    return mangaupdates_menus.csv_menu(
        API_COLOR,
        EXIT_COLOR,
        RESET_COLOR,
        MANGAUPDATES_CSV_COMMAND,
        MANGAUPDATES_DETAILS_COMMAND,
        run_command,
    )


def mangaupdates_id_menu():
    return mangaupdates_menus.id_menu(
        API_COLOR,
        EXIT_COLOR,
        RESET_COLOR,
        MANGAUPDATES_ID_COMMAND,
        MANGAUPDATES_REFRESH_CANDIDATES_COMMAND,
        run_command,
    )


def confirm_library_change(label, action_label, command):
    return operations.confirm_library_change(
        label, action_label, command, run_command
    )


def apply_organization():
    return confirm_library_change(
        "move as pastas da biblioteca",
        "Aplicar organização alfabética",
        ["scripts/organize.py", "--apply"],
    )


def organization_menu():
    return local_menus.organization_menu(
        TITLE_COLOR,
        EXIT_COLOR,
        RESET_COLOR,
        apply_organization,
    )


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
    return notes.register_review_note(REVIEW_NOTES, PROJECT_ROOT, note)


def confirm_csv_notion_update():
    return operations.confirm_csv_notion_update(run_command)


def pause():
    input("\nPressione Enter para voltar ao menu...")


def main():
    actions = {
        "1": standardization_menu,
        "2": organization_menu,
        "3": lambda: run_command(["scripts/scan.py"]),
        "4": mangaupdates_id_menu,
        "5": mangaupdates_csv_menu,
        "6": notion_menu,
        "7": confirm_csv_notion_update,
        "8": run_full_flow,
        "9": run_tests,
    }
    main_loop.run(BANNER, MENU, actions, pause)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nMenu encerrado.")
