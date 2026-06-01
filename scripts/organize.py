import os
import re
import shutil
import html
import unicodedata
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from utils import clean_manga_name, normalize_first_letter, scan_chapters, detect_duplicates_organize


load_dotenv()

MANGA_ROOT = Path(os.getenv("MANGA_ROOT", "")).expanduser()

DRY_RUN = True

REPORT_PATH = Path("reports/organize_preview.html")


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

        is_correct = manga_folder == destination

        plan.append({
            "name": clean_name,
            "source": manga_folder,
            "destination": destination,
            "group": group,
            "current_group": get_current_group(manga_folder),
            "exists": destination.exists(),
            "is_correct": is_correct,
            "main_caps": chapter_data["main_caps"],
            "side_caps": chapter_data["side_caps"],
            "total_caps": chapter_data["total_caps"],
        })

    return plan


def detect_conflicts(plan):
    conflicts = []
    destination_map = defaultdict(list)

    for item in plan:
        dest_str = str(item["destination"])
        destination_map[dest_str].append(item)

    for dest_str, items in destination_map.items():
        if len(items) > 1:
            conflicts.append({
                "destination": dest_str,
                "items": items,
            })

    return conflicts


def determine_status(item, conflicts, duplicates):
    if item["is_correct"]:
        return "Já está correto"

    if any(item in conflict["items"] for conflict in conflicts):
        return "Conflito"

    if any(item["name"] in [e["original"] for e in dup["entries"]] for dup in duplicates):
        return "Duplicado suspeito"

    return "Será movido"


def get_current_group(path):
    current = path.parent
    candidate = None

    while current != current.parent and current != MANGA_ROOT:
        if current.name in GROUPS:
            return current.name

        if re.match(r"^\d{2}[_-]", current.name) or re.match(r"^\d{2}$", current.name):
            return current.name

        if candidate is None:
            candidate = current.name

        current = current.parent

    return candidate or path.parent.name or "Desconhecido"


def generate_html(plan, conflicts, duplicates):
    total_detected = len(plan)
    total_correct = sum(1 for item in plan if item["is_correct"])
    total_to_move = total_detected - total_correct
    total_conflicts = len(conflicts)
    total_duplicates = len(duplicates)
    dry_run_label = "ON" if DRY_RUN else "OFF"

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "<title>Manhwateca - Preview de Organização de Pastas</title>",
        "<style>",
        ":root {",
        "--bg: #f5f7fa;",
        "--panel: #ffffff;",
        "--border: #e2e8f0;",
        "--border-soft: #f1f5f9;",
        "--text: #1e293b;",
        "--muted: #64748b;",
        "--muted-soft: #94a3b8;",
        "--shadow: 0 1px 3px rgba(0,0,0,0.1);",
        "}",
        "* { margin: 0; padding: 0; box-sizing: border-box; }",
        "body {",
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;",
        "background: var(--bg);",
        "color: var(--text);",
        "line-height: 1.5;",
        "}",
        ".topbar {",
        "background: var(--panel);",
        "border-bottom: 1px solid var(--border);",
        "position: sticky;",
        "top: 0;",
        "z-index: 100;",
        "}",
        ".topbar-inner {",
        "max-width: 1400px;",
        "margin: 0 auto;",
        "padding: 20px 24px;",
        "}",
        ".brand-row {",
        "display: flex;",
        "align-items: center;",
        "gap: 24px;",
        "margin-bottom: 16px;",
        "}",
        ".brand h1 {",
        "font-size: 24px;",
        "font-weight: 800;",
        "color: var(--text);",
        "}",
        ".subtitle {",
        "margin-top: 4px;",
        "color: var(--muted);",
        "font-size: 14px;",
        "font-weight: 500;",
        "}",
        ".summary-grid {",
        "display: grid;",
        "grid-template-columns: repeat(6, minmax(110px, 1fr));",
        "gap: 12px;",
        "flex: 1;",
        "}",
        ".summary-card {",
        "min-height: 76px;",
        "padding: 14px 16px;",
        "border: 1px solid var(--border);",
        "border-radius: 8px;",
        "background: var(--panel);",
        "}",
        ".summary-label {",
        "font-size: 12px;",
        "font-weight: 600;",
        "color: var(--muted);",
        "text-transform: uppercase;",
        "letter-spacing: 0.5px;",
        "}",
        ".summary-value {",
        "font-size: 28px;",
        "font-weight: 800;",
        "color: var(--text);",
        "margin-top: 4px;",
        "}",
        ".toolbar {",
        "display: flex;",
        "gap: 12px;",
        "align-items: center;",
        "}",
        ".search {",
        "flex: 1;",
        "padding: 10px 14px;",
        "border: 1px solid var(--border);",
        "border-radius: 8px;",
        "font-size: 14px;",
        "background: var(--panel);",
        "}",
        ".actions {",
        "display: flex;",
        "gap: 8px;",
        "}",
        ".actions button {",
        "padding: 10px 16px;",
        "border: 1px solid var(--border);",
        "border-radius: 8px;",
        "background: var(--panel);",
        "font-size: 13px;",
        "font-weight: 600;",
        "cursor: pointer;",
        "}",
        ".actions button:hover {",
        "background: var(--border-soft);",
        "}",
        ".page {",
        "max-width: 1400px;",
        "margin: 0 auto;",
        "padding: 24px;",
        "}",
        ".groups-grid {",
        "column-count: 2;",
        "column-gap: 20px;",
        "}",
        ".group-card {",
        "break-inside: avoid;",
        "display: inline-block;",
        "width: 100%;",
        "margin-bottom: 20px;",
        "overflow: hidden;",
        "border: 1px solid var(--border);",
        "border-radius: 8px;",
        "background: var(--panel);",
        "box-shadow: var(--shadow);",
        "}",
        ".group-header {",
        "display: flex;",
        "align-items: center;",
        "justify-content: space-between;",
        "padding: 16px 18px;",
        "border-bottom: 1px solid var(--border-soft);",
        "background: var(--panel);",
        "}",
        ".group-title {",
        "font-size: 18px;",
        "font-weight: 700;",
        "color: var(--text);",
        "}",
        ".group-stats {",
        "display: flex;",
        "gap: 8px;",
        "}",
        ".pill {",
        "padding: 4px 10px;",
        "border-radius: 12px;",
        "background: var(--border-soft);",
        "color: var(--muted);",
        "font-size: 12px;",
        "font-weight: 600;",
        "}",
        ".manga-list {",
        "padding: 12px;",
        "}",
        ".manga {",
        "border: 1px solid var(--border-soft);",
        "border-radius: 8px;",
        "margin-bottom: 4px;",
        "background: var(--panel);",
        "}",
        ".manga summary {",
        "display: flex;",
        "align-items: center;",
        "gap: 8px;",
        "min-height: 44px;",
        "padding: 8px 10px;",
        "border-radius: 8px;",
        "cursor: pointer;",
        "color: var(--text);",
        "font-size: 14px;",
        "font-weight: 700;",
        "list-style: none;",
        "flex-wrap: wrap;",
        "}",
        ".manga summary::-webkit-details-marker {",
        "display: none;",
        "}",
        ".chevron {",
        "color: var(--muted-soft);",
        "font-size: 12px;",
        "transition: transform 0.16s ease;",
        "}",
        ".manga[open] .chevron {",
        "transform: rotate(90deg);",
        "}",
        ".manga-title {",
        "flex: 1;",
        "}",
        ".manga-count {",
        "color: var(--muted);",
        "font-size: 13px;",
        "}",
        ".status-badge {",
        "display: inline-block;",
        "padding: 2px 8px;",
        "margin-left: 8px;",
        "border-radius: 4px;",
        "font-size: 11px;",
        "font-weight: 700;",
        "}",
        ".status-ok {",
        "background: #dcfce7;",
        "color: #166534;",
        "}",
        ".status-move {",
        "background: #dbeafe;",
        "color: #1e40af;",
        "}",
        ".status-conflict {",
        "background: #fef2f2;",
        "color: #dc2626;",
        "}",
        ".status-duplicate {",
        "background: #fffbeb;",
        "color: #b45309;",
        "}",
        ".table-wrap {",
        "padding: 12px;",
        "}",
        "table {",
        "width: 100%;",
        "border-collapse: collapse;",
        "font-size: 13px;",
        "}",
        "th, td {",
        "padding: 8px 10px;",
        "text-align: left;",
        "border-bottom: 1px solid var(--border-soft);",
        "}",
        "th {",
        "font-weight: 600;",
        "color: var(--muted);",
        "background: var(--border-soft);",
        "}",
        "td {",
        "color: var(--text);",
        "}",
        ".duplicates-section {",
        "margin-bottom: 24px;",
        "padding: 20px;",
        "border: 2px solid #f59e0b;",
        "border-radius: 8px;",
        "background: #fffbeb;",
        "}",
        ".duplicates-title {",
        "margin: 0 0 16px 0;",
        "font-size: 18px;",
        "font-weight: 700;",
        "color: #b45309;",
        "}",
        ".duplicate-item {",
        "padding: 12px;",
        "margin-bottom: 8px;",
        "border: 1px solid #fcd34d;",
        "border-radius: 6px;",
        "background: #fff;",
        "}",
        ".duplicate-item:last-child {",
        "margin-bottom: 0;",
        "}",
        ".duplicate-name {",
        "font-weight: 600;",
        "color: #92400e;",
        "}",
        ".duplicate-entries {",
        "margin-top: 8px;",
        "font-size: 13px;",
        "color: #78350f;",
        "}",
        "@media (max-width: 1100px) {",
        ".brand-row {",
        "display: block;",
        "}",
        ".brand {",
        "margin-bottom: 14px;",
        "}",
        ".summary-grid {",
        "grid-template-columns: repeat(2, minmax(0, 1fr));",
        "}",
        ".groups-grid {",
        "column-count: 1;",
        "}",
        "}",
        "@media (max-width: 720px) {",
        ".topbar-inner,",
        ".page {",
        "padding-left: 16px;",
        "padding-right: 16px;",
        "}",
        ".toolbar {",
        "flex-direction: column;",
        "}",
        ".actions {",
        "width: 100%;",
        "}",
        ".actions button {",
        "flex: 1;",
        "}",
        "}",
        "</style>",
        "</head>",
        "<body>",
        "<header class='topbar'>",
        "<div class='topbar-inner'>",
        "<div class='brand-row'>",
        "<div class='brand'>",
        "<h1>Manhwateca</h1>",
        "<div class='subtitle'>Preview de Organização de Pastas</div>",
        "</div>",
        "<div class='summary-grid' aria-label='Resumo'>",
        "<div class='summary-card'><div class='summary-label'>Obras Detectadas</div>"
        f"<div class='summary-value'>{total_detected}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Já Corretas</div>"
        f"<div class='summary-value'>{total_correct}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Pastas a Mover</div>"
        f"<div class='summary-value'>{total_to_move}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Conflitos</div>"
        f"<div class='summary-value'>{total_conflicts}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Duplicados</div>"
        f"<div class='summary-value'>{total_duplicates}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Modo Simulação</div>"
        f"<div class='summary-value'>{dry_run_label}</div></div>",
        "</div>",
        "</div>",
        "<div class='toolbar'>",
        "<input class='search' id='search' type='search' placeholder='Buscar obra...' autocomplete='off'>",
        "<div class='actions'>",
        "<button type='button' id='expandAll'>Expandir Tudo</button>",
        "<button type='button' id='collapseAll'>Recolher Tudo</button>",
        "</div>",
        "</div>",
        "</div>",
        "</header>",
        "<main class='page'>",
    ]

    if duplicates:
        html_parts.append("<section class='duplicates-section'>")
        html_parts.append("<h2 class='duplicates-title'>⚠️ Possíveis Duplicados Detectados</h2>")

        for dup in duplicates:
            html_parts.append("<div class='duplicate-item'>")
            html_parts.append(f"<div class='duplicate-name'>{html.escape(dup['normalized'])}</div>")
            html_parts.append("<div class='duplicate-entries'>")

            for entry in dup['entries']:
                html_parts.append(
                    f"• {html.escape(entry['original'])} (grupo: {html.escape(entry['group'])})<br>"
                )

            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</section>")

    if conflicts:
        html_parts.append("<section class='duplicates-section' style='border-color:#fca5a5;background:#fff1f2;'>")
        html_parts.append("<h2 class='duplicates-title'>🚨 Conflitos Detectados</h2>")

        for conflict in conflicts:
            html_parts.append("<div class='duplicate-item'>")
            html_parts.append(f"<div class='duplicate-name'>Destino: {html.escape(conflict['destination'])}</div>")
            html_parts.append("<div class='duplicate-entries'>")
            for item in conflict['items']:
                html_parts.append(
                    f"• {html.escape(item['name'])} — {html.escape(str(item['source']))}" 
                )
                html_parts.append("<br>")
            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</section>")

    html_parts.append("<div class='groups-grid' id='groupsGrid'>")

    for group in GROUPS:
        group_items = [item for item in plan if item["group"] == group]
        group_conflicts = sum(1 for c in conflicts if any(item["group"] == group for item in c["items"]))
        group_duplicates = sum(1 for d in duplicates for e in d["entries"] if e["group"] == group)

        html_parts.append(
            "<section class='group-card' "
            f"data-group='{html.escape(group)}'>"
        )
        html_parts.append("<div class='group-header'>")
        html_parts.append(f"<div class='group-title'>{html.escape(group)}</div>")
        html_parts.append("<div class='group-stats'>")
        html_parts.append(
            f"<span class='pill'><span class='group-manga-count'>{len(group_items)}</span> obras</span>"
        )
        to_move = sum(1 for item in group_items if not item["is_correct"])
        html_parts.append(
            f"<span class='pill'><span class='group-move-count'>{to_move}</span> a mover</span>"
        )
        if group_conflicts > 0:
            html_parts.append(
                f"<span class='pill' style='background:#fef2f2;color:#dc2626;border-color:#fecaca;'>{group_conflicts} conflitos</span>"
            )
        if group_duplicates > 0:
            html_parts.append(
                f"<span class='pill' style='background:#fffbeb;color:#b45309;border-color:#fcd34d;'>{group_duplicates} duplicados</span>"
            )
        html_parts.append("</div>")
        html_parts.append("</div>")

        if not group_items:
            html_parts.append("<div class='manga-list'>Nenhuma obra.</div>")
        else:
            html_parts.append("<div class='manga-list'>")

        for item in sorted(group_items, key=lambda x: x["name"].lower()):
            status = determine_status(item, conflicts, duplicates)
            search_text = " ".join([
                item["source"].name,
                item["name"],
                str(item["source"]),
                str(item["destination"]),
                item["group"],
            ]).lower()

            status_class_map = {
                "Já está correto": "status-ok",
                "Será movido": "status-move",
                "Conflito": "status-conflict",
                "Duplicado suspeito": "status-duplicate",
            }
            status_class = status_class_map.get(status, "status-move")

            current_group = item.get("current_group", get_current_group(item["source"]))

            html_parts.append(
                "<details class='manga' "
                f"data-search='{html.escape(search_text, quote=True)}'>"
            )
            html_parts.append(
                "<summary>"
                "<span class='chevron'>▶</span>"
                f"<span class='manga-title'>{html.escape(item['name'])}</span>"
                f"<span class='status-badge {status_class}'>{html.escape(status)}</span>"
                "</summary>"
            )

            html_parts.append("<div class='table-wrap'>")
            html_parts.append("<table>")
            html_parts.append("<tbody>")

            html_parts.append(f"<tr><th>Pasta atual</th><td>{html.escape(item['source'].name)}</td></tr>")
            html_parts.append(f"<tr><th>Nome limpo</th><td>{html.escape(item['name'])}</td></tr>")
            html_parts.append(f"<tr><th>Grupo atual</th><td>{html.escape(current_group)}</td></tr>")
            html_parts.append(f"<tr><th>Grupo destino</th><td>{html.escape(item['group'])}</td></tr>")
            html_parts.append(f"<tr><th>Caminho atual</th><td>{html.escape(str(item['source']))}</td></tr>")
            html_parts.append(f"<tr><th>Caminho destino</th><td>{html.escape(str(item['destination']))}</td></tr>")
            html_parts.append(f"<tr><th>Main caps</th><td>{item['main_caps']}</td></tr>")
            html_parts.append(f"<tr><th>Side caps</th><td>{item['side_caps']}</td></tr>")
            html_parts.append(f"<tr><th>Total caps</th><td>{item['total_caps']}</td></tr>")

            html_parts.append("</tbody>")
            html_parts.append("</table>")
            html_parts.append("</div>")
            html_parts.append("</details>")

        if group_items:
            html_parts.append("</div>")

        html_parts.append("</section>")

    html_parts.append("</div>")
    html_parts.append("</main>")
    html_parts.append(
        """
        <script>
        const searchInput = document.getElementById('search');
        const groupsGrid = document.getElementById('groupsGrid');
        const groupCards = groupsGrid.querySelectorAll('.group-card');

        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            let visibleCount = 0;

            groupCards.forEach(card => {
                const items = card.querySelectorAll('.manga');
                let hasVisibleItem = false;

                items.forEach(item => {
                    const searchText = item.getAttribute('data-search');
                    if (searchText.includes(query)) {
                        item.style.display = '';
                        hasVisibleItem = true;
                    } else {
                        item.style.display = 'none';
                    }
                });

                if (hasVisibleItem || query === '') {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });

        document.getElementById('expandAll').addEventListener('click', function() {
            document.querySelectorAll('.manga').forEach(el => el.open = true);
        });

        document.getElementById('collapseAll').addEventListener('click', function() {
            document.querySelectorAll('.manga').forEach(el => el.open = false);
        });
        </script>
        """
    )
    html_parts.append("</body>")
    html_parts.append("</html>")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(html_parts), encoding="utf-8")


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


def apply_plan(plan, conflicts):
    if DRY_RUN:
        return

    if conflicts:
        print("Conflitos encontrados. Nenhuma pasta foi movida.")
        return

    for item in plan:
        if item["exists"]:
            continue

        if item["is_correct"]:
            continue

        item["destination"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(item["source"]), str(item["destination"]))


def organize():
    if not MANGA_ROOT:
        raise ValueError("MANGA_ROOT não foi definido no .env")

    if not MANGA_ROOT.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {MANGA_ROOT}")

    manga_folders = find_manga_folders(MANGA_ROOT)
    plan = build_plan(manga_folders)
    conflicts = detect_conflicts(plan)
    duplicates = detect_duplicates_organize(plan)

    total_detected = len(plan)
    total_correct = sum(1 for item in plan if item["is_correct"])
    total_to_move = total_detected - total_correct

    generate_html(plan, conflicts, duplicates)
    apply_plan(plan, conflicts)

    print(f"Pasta raiz: {MANGA_ROOT}")
    print(f"Modo simulação: {DRY_RUN}")
    print()
    print(f"Relatório gerado: {REPORT_PATH}")
    print()
    print("Resumo:")
    print(f"Obras detectadas: {total_detected}")
    print(f"Já corretas: {total_correct}")
    print(f"Pastas a mover: {total_to_move}")
    print(f"Grupos: {len(GROUPS)}")
    print(f"Conflitos: {len(conflicts)}")
    print(f"Possíveis duplicados: {len(duplicates)}")
    print()

    if conflicts:
        print("Atenção: existem conflitos. Revise o HTML antes de aplicar alterações.")
        print("\nConflitos detectados:")
        for conflict in conflicts:
            print(f"- destino: {conflict['destination']}")
            for item in conflict['items']:
                print(f"  origem: {item['source']}")
            print()

    if duplicates:
        print("Duplicados detectados:")
        for dup in duplicates:
            print(f"- {dup['normalized']}: {[entry['original'] for entry in dup['entries']]}" )
        print()


if __name__ == "__main__":
    organize()