import json
import shutil
import unicodedata
import uuid
from datetime import datetime


def write_history(
    source,
    destination,
    status,
    history_path,
    error=None,
):
    history_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(source),
        "destination": str(destination),
        "status": status,
    }
    if error:
        entry["error"] = str(error)

    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def apply_plan(
    plan,
    conflicts,
    duplicates,
    dry_run,
    history_writer,
):
    if dry_run:
        return True
    if conflicts or duplicates:
        print("Conflitos ou duplicados encontrados. Nenhuma pasta foi movida.")
        return False

    pending = [
        item
        for item in plan
        if not item["is_correct"] and not item["exists"]
    ]
    missing_sources = [
        item for item in pending if not item["source"].exists()
    ]
    if missing_sources:
        print("Origens ausentes. Nenhuma nova pasta foi movida:")
        for item in missing_sources:
            print(f"- {item['source']}")
        print("Gere uma nova prévia antes de tentar novamente.")
        return False

    pending.sort(
        key=lambda item: len(item["source"].parts),
        reverse=True,
    )
    for item in pending:
        if not item["source"].exists():
            print(f"[PULAR] Origem já movimentada: {item['source']}")
            history_writer(
                item["source"],
                item["destination"],
                "origem_ausente",
            )
            continue

        item["destination"].parent.mkdir(parents=True, exist_ok=True)
        try:
            _move_item(item)
        except Exception as error:
            history_writer(
                item["source"],
                item["destination"],
                "erro",
                error,
            )
            raise
        else:
            history_writer(
                item["source"],
                item["destination"],
                "movido",
            )
    return True


def _move_item(item):
    source = item["source"]
    destination = item["destination"]
    source_equivalent = unicodedata.normalize(
        "NFC",
        source.name,
    ).casefold()
    destination_equivalent = unicodedata.normalize(
        "NFC",
        destination.name,
    ).casefold()

    if (
        source.parent == destination.parent
        and source_equivalent == destination_equivalent
    ):
        temporary = source.with_name(f"manhwateca-temp-{uuid.uuid4().hex}")
        source.rename(temporary)
        temporary.rename(destination)
    else:
        shutil.move(str(source), str(destination))
