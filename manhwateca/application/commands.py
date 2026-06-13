import subprocess
import sys


MANGAUPDATES_ID_COMMAND = [
    "scripts/mangaupdates.py",
    "--fill-ids",
    "reports/integrations/buscaIds.json",
    "--delay",
    "3",
    "--limit",
    "10",
]
MANGAUPDATES_REFRESH_CANDIDATES_COMMAND = [
    "scripts/mangaupdates.py",
    "--refresh-incomplete-candidates",
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


def run_command(arguments, project_root):
    command = [sys.executable, *arguments]
    print(f"\nExecutando: {' '.join(arguments)}\n")
    result = subprocess.run(command, cwd=project_root, check=False)
    if result.returncode == 0:
        print("\n[OK] Operação concluída.")
    else:
        print(f"\n[ERRO] Operação encerrada com código {result.returncode}.")
    return result.returncode == 0
