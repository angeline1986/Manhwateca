import json
from datetime import datetime


def write_csv_status(summary, applied, path):
    payload = {
        "atualizado_em": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "modo": "APLICAÇÃO" if applied else "SIMULAÇÃO",
        "resumo": {
            "atualizacoes": summary["updated"],
            "sem_alteracao": len(summary.get("unchanged", [])),
            "ausentes": len(summary["missing"]),
            "duplicadas": len(summary["duplicates"]),
        },
        "atualizacoes": summary.get("updates", []),
        "sem_alteracao": summary.get("unchanged", []),
        "ausentes": summary["missing"],
        "duplicadas": summary["duplicates"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return payload
