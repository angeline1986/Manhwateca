import argparse
import csv
import json
from pathlib import Path


CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
OUTPUT_FILE = Path("config/catalog_metadata.json")


def load_updates(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def load_current_names(path=CSV_FILE):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [row["Nome"] for row in csv.DictReader(file)]


def build_metadata(current_names, updates):
    if len(current_names) != len(updates):
        raise ValueError(
            f"Quantidade divergente: CSV possui {len(current_names)} obras "
            f"e atualização possui {len(updates)}."
        )

    metadata = {}
    for current_name, update in zip(current_names, updates):
        metadata[current_name] = {
            "nome_oficial": update["Nome (Oficial)"].strip(),
            "alias": update["Alias (Português)"].strip(),
            "interesse": update["Interesse"].strip(),
        }
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Importa nomes oficiais, aliases e interesse."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    metadata = build_metadata(load_current_names(), load_updates(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Metadados importados: {len(metadata)}")
    print(f"Arquivo gerado: {args.output}")


if __name__ == "__main__":
    main()
