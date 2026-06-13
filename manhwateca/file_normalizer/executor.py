import unicodedata
import uuid
from pathlib import Path


def apply_plan(plan, conflicts, dry_run=True):
    if dry_run:
        return True
    conflicted_paths = {
        item["old_path"]
        for conflict in conflicts
        for item in conflict["files"]
    }
    if conflicts:
        print("Conflitos encontrados. Os arquivos envolvidos serão ignorados.")

    errors = []
    for mangas in plan.values():
        for files in mangas.values():
            for item in files:
                _rename_item(item, conflicted_paths, errors)

    if errors or conflicts:
        print()
        print(f"Arquivos pendentes por conflito: {len(conflicted_paths)}")
        print(f"Arquivos pendentes por erro: {len(errors)}")
        return False
    return True


def _rename_item(item, conflicted_paths, errors):
    old_path = Path(item["old_path"])
    new_path = Path(item["new_path"])
    if item["old_path"] in conflicted_paths:
        print(f"[PULAR] Conflito: {old_path}")
        return
    if not old_path.exists():
        return
    try:
        if _equivalent_name(old_path.name) == _equivalent_name(new_path.name):
            temporary = old_path.with_name(
                f"manhwateca-temp-{uuid.uuid4().hex}{old_path.suffix}"
            )
            old_path.rename(temporary)
            temporary.rename(new_path)
        elif not new_path.exists():
            old_path.rename(new_path)
    except OSError as error:
        errors.append((old_path, error))
        print(f"[ERRO] Não foi possível renomear: {old_path}")
        print(f"       {error}")


def _equivalent_name(name):
    return unicodedata.normalize("NFC", name).casefold()
