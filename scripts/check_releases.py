#!/usr/bin/env python3
from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from manhwateca.release_monitor.service import ReleaseMonitorService


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    result = ReleaseMonitorService().run()
    print(f"Status: {result.status}")
    print(f"Execução: {result.run_id}")
    print(f"Páginas consultadas: {result.pages_requested}")
    print(f"Releases recebidas: {result.releases_received}")
    print(f"Releases parseadas: {result.releases_parsed}")
    print(f"Releases no período: {result.releases_in_period}")
    print(f"Com metadata de série: {result.releases_with_series_metadata}")
    print(f"Sem metadata de série: {result.releases_missing_series_metadata}")
    print(f"Inválidas: {result.releases_invalid}")
    print(f"Correspondentes às obras monitoradas: {result.releases_matched}")
    print(f"Inseridas: {result.releases_inserted}")
    print(f"Já conhecidas: {result.releases_already_known}")
    print(f"Sem correspondência: {result.releases_unmatched}")
    if result.error_message:
        print(f"Erro: {result.error_message}")
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
