import json
import shutil
from datetime import datetime


def backup_editorial_files(project_root, paths):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir = project_root / "reports/backups/editorial" / timestamp
    saved = []
    for path in paths:
        if not path.is_file():
            continue
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / path.name
        shutil.copy2(path, target)
        saved.append(str(target.relative_to(project_root)))
    return saved


def log_editorial_change(project_root, name, changes, backups):
    path = project_root / "reports/logs/editorial_changes.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "obra": name,
        "campos": sorted(changes),
        "backups": backups,
    }
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
