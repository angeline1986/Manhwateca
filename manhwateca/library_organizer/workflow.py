import html
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv


from manhwateca.library_organizer.discovery import (
    find_empty_legacy_folders as _find_empty_legacy_folders,
    find_manga_folders as _find_manga_folders,
    is_manga_folder as _is_manga_folder,
)
from manhwateca.library_organizer.grouping import (
    GROUPS,
    get_current_group as _get_current_group,
    get_group,
    is_group_folder,
    is_legacy_container,
)
from manhwateca.library_organizer.execution import (
    apply_plan as _apply_plan,
    write_history as _write_history,
)
from manhwateca.library_organizer.planning import (
    build_plan as _build_plan,
    detect_conflicts,
    determine_status,
)
from manhwateca.library_organizer.parser import parse_args
from manhwateca.reporting.files import write_report
from manhwateca.shared.duplicates import detect_duplicates_organize
from manhwateca.shared.paths import get_required_path_env


load_dotenv()

MANGA_ROOT = get_required_path_env("MANGA_ROOT")

DRY_RUN = True

REPORT_PATH = Path("reports/audits/organize_preview.html")
HISTORY_PATH = Path("reports/logs/organize_history.jsonl")


def is_manga_folder(path):
    return _is_manga_folder(path, is_group_folder, is_legacy_container)


def find_empty_legacy_folders(root):
    return _find_empty_legacy_folders(root, is_legacy_container)


def find_manga_folders(root):
    return _find_manga_folders(root, is_group_folder, is_manga_folder)


def build_plan(manga_folders):
    return _build_plan(
        manga_folders,
        MANGA_ROOT,
        get_group,
        get_current_group,
    )


def get_current_group(path):
    return _get_current_group(path, MANGA_ROOT)


def generate_html(plan, conflicts, duplicates, empty_legacy_folders=None):
    empty_legacy_folders = empty_legacy_folders or []
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
            reason = conflict.get('reason', 'destino_duplicado')
            if reason == 'destino_existente':
                reason_label = 'Destino já existe'
            elif reason == 'destino_duplicado':
                reason_label = 'Destino duplicado no plano'
            elif reason == 'both':
                reason_label = 'Destino já existe + Destino duplicado'
            else:
                reason_label = reason

            html_parts.append("<div class='duplicate-item'>")
            html_parts.append(f"<div class='duplicate-name'>Destino: {html.escape(conflict['destination'])}</div>")
            html_parts.append(f"<div class='duplicate-name' style='font-weight:600;color:#b91c1c;'>Motivo: {html.escape(reason_label)}</div>")
            html_parts.append("<div class='duplicate-entries'>")
            for item in conflict['items']:
                html_parts.append(
                    f"• {html.escape(item['name'])} — {html.escape(str(item['source']))}" 
                )
                html_parts.append("<br>")
            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</section>")

    if empty_legacy_folders:
        html_parts.append(
            "<section class='duplicates-section' "
            "style='border-color:#fcd34d;background:#fffbeb;'>"
        )
        html_parts.append(
            "<h2 class='duplicates-title'>Pastas vazias para revisão manual</h2>"
        )
        html_parts.append(
            "<div class='duplicate-item'><div class='duplicate-entries'>"
            "Estas pastas não são tratadas como obras nem movidas automaticamente:<br><br>"
        )
        for path in empty_legacy_folders:
            html_parts.append(f"• {html.escape(str(path))}<br>")
        html_parts.append("</div></div></section>")

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

    write_report(REPORT_PATH, "\n".join(html_parts))


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


def write_history(source, destination, status, error=None):
    return _write_history(
        source,
        destination,
        status,
        HISTORY_PATH,
        error,
    )


def apply_plan(plan, conflicts, duplicates):
    return _apply_plan(
        plan,
        conflicts,
        duplicates,
        dry_run=DRY_RUN,
        history_writer=write_history,
    )


def organize(apply=False):
    global DRY_RUN
    DRY_RUN = not apply

    if not MANGA_ROOT.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {MANGA_ROOT}")

    manga_folders = find_manga_folders(MANGA_ROOT)
    empty_legacy_folders = find_empty_legacy_folders(MANGA_ROOT)

    if not manga_folders:
        media_files = sum(
            1
            for path in MANGA_ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pdf", ".cbz"}
        )
        raise RuntimeError(
            "Nenhuma obra foi detectada. "
            f"Foram encontrados {media_files} arquivos PDF/CBZ em {MANGA_ROOT}. "
            "Verifique se os nomes contêm 'cap', 'capítulo' ou 'side story'."
        )

    plan = build_plan(manga_folders)
    conflicts = detect_conflicts(plan)
    duplicates = detect_duplicates_organize(plan)

    total_detected = len(plan)
    total_correct = sum(1 for item in plan if item["is_correct"])
    total_to_move = total_detected - total_correct

    generate_html(plan, conflicts, duplicates, empty_legacy_folders)
    applied = apply_plan(plan, conflicts, duplicates)

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
    print(f"Pastas vazias para revisão manual: {len(empty_legacy_folders)}")
    print()

    if conflicts:
        print("Atenção: existem conflitos. Revise o HTML antes de aplicar alterações.")
        print("\nConflitos detectados:")

        # Print "Destino já existe" conflicts first
        for conflict in conflicts:
            if conflict.get('reason') == 'destino_existente' or conflict.get('reason') == 'both':
                print("[Destino já existe]")
                print("Destino:")
                print(conflict['destination'])
                print("\nOrigem:")
                for item in conflict['items']:
                    print(item['source'])
                print("\n" + "-"*40 + "\n")

        # Print "Destino duplicado" conflicts
        for conflict in conflicts:
            if conflict.get('reason') == 'destino_duplicado' or conflict.get('reason') == 'both':
                print("[Destino duplicado]")
                print("Destino:")
                print(conflict['destination'])
                print("\nOrigem 1:")
                for i, item in enumerate(conflict['items'], start=1):
                    print(f"Origem {i}: {item['source']}")
                print("\n" + "-"*40 + "\n")

    if duplicates:
        print("Duplicados detectados:")
        for dup in duplicates:
            print(f"- {dup['normalized']}: {[entry['original'] for entry in dup['entries']]}" )
        print()

    if empty_legacy_folders:
        print("Pastas vazias ignoradas pela organização automática:")
        for path in empty_legacy_folders:
            print(f"- {path}")
        print()

    return applied
