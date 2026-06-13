def generate_reports(run_command):
    results = [
        run_command(["scripts/organize.py"]),
        run_command(["scripts/rename_files.py"]),
        run_command(["scripts/chapter_audit.py"]),
    ]
    return all(results)


def run_full_flow(run_command):
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


def confirm_sync_batch(run_command):
    print("\nEsta opção importa até 25 obras novas.")
    print("As próximas obras são escolhidas em ordem alfabética.")
    print("  1. Importar próximo lote de 25 obras")
    print("  2. Cancelar")
    if input("Escolha uma opção: ").strip() != "1":
        print("\nOperação cancelada.")
        return False
    return run_command(["scripts/sync.py", "--apply-batch", "--batch-size", "25"])


def confirm_library_change(label, action_label, command, run_command):
    print(f"\nEsta opção {label}.")
    print(f"  1. {action_label}")
    print("  2. Cancelar")
    if input("Escolha uma opção: ").strip() != "1":
        print("\nOperação cancelada.")
        return False
    return run_command(command)


def confirm_csv_notion_update(run_command):
    print("\nEsta opção atualiza páginas existentes usando o CSV.")
    print("Nenhuma página nova será criada.")
    print("  1. Atualizar Notion com reports/integrations/manhwateca_import.csv")
    print("  2. Cancelar")
    if input("Escolha uma opção: ").strip() != "1":
        print("\nOperação cancelada.")
        return False
    if not run_command(["scripts/notion_csv.py"]):
        return False
    print("\nA simulação foi concluída.")
    print("  1. Aplicar as atualizações")
    print("  2. Cancelar")
    if input("Escolha uma opção: ").strip() != "1":
        print("\nAplicação cancelada.")
        return False
    return run_command(["scripts/notion_csv.py", "--apply"])
