import os
import shutil
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from utils import clean_manga_name, normalize_first_letter, scan_chapters


load_dotenv()

MANGA_ROOT = Path(os.getenv("MANGA_ROOT", "")).expanduser()

DRY_RUN = True


GROUPS = {
    "0-9": "0123456789",

    "A": "A",
    "BC": "BC",
    "DE": "DE",
    "FG": "FG",
    "HIJ": "HIJ",
    "KLM": "KLM",
    "NO": "NO",

    "PQR": "PQR",
    "ST": "ST",
    "UVW": "UVW",
    "XYZ": "XYZ",
}


def get_group(folder_name):
    first = normalize_first_letter(folder_name)

    for group_name, letters in GROUPS.items():
        if first in letters:
            return group_name

    return "0-9"


def is_group_folder(folder_name):
    return folder_name in GROUPS


def is_manga_folder(path):
    chapter_data = scan_chapters(path)
    return chapter_data["chapter_files"] > 0 or chapter_data["side_files"] > 0


def find_manga_folders(root):
    manga_folders = []

    for path in root.rglob("*"):
        if not path.is_dir():
            continue

        if is_group_folder(path.name):
            continue

        if is_manga_folder(path):
            manga_folders.append(path)

    return manga_folders


def build_plan(manga_folders):
    plan = []

    for manga_folder in manga_folders:
        clean_name = clean_manga_name(manga_folder.name)
        group = get_group(clean_name)
        destination = MANGA_ROOT / group / clean_name
        chapter_data = scan_chapters(manga_folder)

        if manga_folder == destination:
            continue

        plan.append({
            "name": clean_name,
            "source": manga_folder,
            "destination": destination,
            "group": group,
            "exists": destination.exists(),
            "main_caps": chapter_data["main_caps"],
            "side_caps": chapter_data["side_caps"],
            "total_caps": chapter_data["total_caps"],
        })

    return plan


def print_moves(plan):
    print("Plano de movimentação:")
    print()

    if not plan:
        print("Nenhuma pasta precisa ser movida.")
        print()
        return

    for item in plan:
        if item["exists"]:
            print("[PULAR] Já existe destino:")
            print(f"  {item['destination']}")
            print()
            continue

        print("[MOVER]")
        print(f"  de:   {item['source']}")
        print(f"  para: {item['destination']}")
        print(f"  caps: main={item['main_caps']} | side={item['side_caps']} | total={item['total_caps']}")
        print()


def print_tree_preview(plan):
    tree = defaultdict(list)

    for item in plan:
        tree[item["group"]].append(item)

    print("Prévia da nova estrutura:")
    print()

    for group in GROUPS:
        print(f"{group}/")

        items = sorted(tree[group], key=lambda item: item["name"].lower())

        if not items:
            print("  —")

        for item in items:
            print(
                f"  {item['name']} "
                f"(main: {item['main_caps']}, side: {item['side_caps']}, total: {item['total_caps']})"
            )

        print()


def print_summary(plan):
    summary = defaultdict(int)

    for item in plan:
        summary[item["group"]] += 1

    print("Resumo:")
    print()

    total = 0

    for group in GROUPS:
        count = summary[group]
        total += count
        print(f"{group}: {count}")

    print()
    print(f"Total a mover: {total}")
    print(f"Modo simulação: {DRY_RUN}")
    print()


def create_group_folders():
    for group in GROUPS:
        target = MANGA_ROOT / group

        if target.exists():
            continue

        print(f"[CRIAR] {target}")

        if not DRY_RUN:
            target.mkdir(parents=True, exist_ok=True)


def apply_plan(plan):
    if DRY_RUN:
        return

    for item in plan:
        if item["exists"]:
            continue

        item["destination"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(item["source"]), str(item["destination"]))


def organize():
    if not MANGA_ROOT:
        raise ValueError("MANGA_ROOT não foi definido no .env")

    if not MANGA_ROOT.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {MANGA_ROOT}")

    print(f"Pasta raiz: {MANGA_ROOT}")
    print()

    manga_folders = find_manga_folders(MANGA_ROOT)
    plan = build_plan(manga_folders)

    print(f"{len(manga_folders)} pastas de mangá encontradas.")
    print()

    create_group_folders()
    print()

    print_moves(plan)
    print_tree_preview(plan)
    print_summary(plan)

    apply_plan(plan)


if __name__ == "__main__":
    organize()