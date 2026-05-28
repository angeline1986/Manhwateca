import os
import re
import html
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
from utils import clean_manga_name, normalize_first_letter


load_dotenv()

MANGA_ROOT = Path(os.getenv("MANGA_ROOT", "")).expanduser()

DRY_RUN = True

REPORT_PATH = Path("reports/rename_preview.html")

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

CHAPTER_EXTENSIONS = {
    ".pdf",
    ".cbz",
}


def get_group(name):
    first = normalize_first_letter(name)

    for group, letters in GROUPS.items():
        if first in letters:
            return group

    return "0-9"


def normalize_chapter_name(filename):
    path = Path(filename)
    stem = path.stem
    suffix = path.suffix

    new_stem = stem

    new_stem = re.sub(r"cap[ií]tulo", "cap", new_stem, flags=re.IGNORECASE)
    new_stem = re.sub(r"\bcaps?\b", "cap", new_stem, flags=re.IGNORECASE)

    new_stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)\s*(?:=|_|ao|a|–|—)\s*(\d+(?:\.\d+)?)",
        r"cap \1-\2",
        new_stem,
        flags=re.IGNORECASE,
    )

    new_stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)",
        r"cap \1-\2",
        new_stem,
        flags=re.IGNORECASE,
    )

    new_stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)",
        r"cap \1",
        new_stem,
        flags=re.IGNORECASE,
    )

    new_stem = re.sub(r"\s+", " ", new_stem).strip()

    return f"{new_stem}{suffix}"


def build_plan():
    plan = defaultdict(lambda: defaultdict(list))

    for file in MANGA_ROOT.rglob("*"):
        if not file.is_file():
            continue

        if file.suffix.lower() not in CHAPTER_EXTENSIONS:
            continue

        manga_folder = file.parent
        manga_name = clean_manga_name(manga_folder.name)
        group = get_group(manga_name)

        new_file_name = normalize_chapter_name(file.name)

        if new_file_name == file.name:
            continue

        plan[group][manga_name].append({
            "old_name": file.name,
            "new_name": new_file_name,
            "old_path": str(file),
            "new_path": str(file.with_name(new_file_name)),
        })

    return plan


def generate_html(plan):
    total_files = sum(
        len(files)
        for mangas in plan.values()
        for files in mangas.values()
    )
    total_mangas = sum(len(mangas) for mangas in plan.values())
    total_groups = sum(1 for mangas in plan.values() if mangas)
    dry_run_label = "ON" if DRY_RUN else "OFF"

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "<title>Manhwateca - Preview de Renomeação</title>",
        "<style>",
        """
        :root {
            --bg: #f6f8fa;
            --panel: #ffffff;
            --panel-soft: #f9fafb;
            --border: #d8dee4;
            --border-soft: #eaeef2;
            --text: #1f2328;
            --muted: #59636e;
            --muted-soft: #818b98;
            --blue: #0969da;
            --old: #b91c1c;
            --new: #15803d;
            --shadow: 0 16px 40px rgba(31, 35, 40, 0.08);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: Inter, SF Pro Display, Segoe UI, sans-serif;
            margin: 0;
            background: var(--bg);
            color: var(--text);
        }

        .topbar {
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--border);
            background: rgba(246, 248, 250, 0.94);
            backdrop-filter: blur(16px);
        }

        .topbar-inner,
        .page {
            max-width: 1800px;
            margin: auto;
            padding-left: 28px;
            padding-right: 28px;
        }

        .topbar-inner {
            padding-top: 20px;
            padding-bottom: 18px;
        }

        .brand-row {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 16px;
        }

        .brand {
            min-width: 220px;
        }

        h1 {
            margin: 0;
            font-size: 28px;
            line-height: 1.1;
            letter-spacing: 0;
        }

        .subtitle {
            margin-top: 4px;
            color: var(--muted);
            font-size: 14px;
            font-weight: 500;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(128px, 1fr));
            gap: 12px;
            flex: 1;
        }

        .summary-card {
            min-height: 76px;
            padding: 14px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04);
        }

        .summary-label {
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .summary-value {
            margin-top: 8px;
            font-size: 26px;
            line-height: 1;
            font-weight: 800;
        }

        .toolbar {
            display: grid;
            grid-template-columns: minmax(260px, 1fr) auto;
            gap: 12px;
            align-items: center;
        }

        .search {
            width: 100%;
            height: 44px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--panel);
            color: var(--text);
            font: inherit;
            font-size: 15px;
            outline: none;
            padding: 0 14px;
        }

        .search:focus {
            border-color: var(--blue);
            box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.14);
        }

        .actions {
            display: flex;
            gap: 8px;
            justify-content: flex-end;
        }

        button {
            height: 40px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--panel);
            color: var(--text);
            cursor: pointer;
            font: inherit;
            font-size: 14px;
            font-weight: 700;
            padding: 0 14px;
        }

        button:hover {
            background: var(--panel-soft);
            border-color: #afb8c1;
        }

        .page {
            padding-top: 24px;
            padding-bottom: 44px;
        }

        .live-count {
            margin-bottom: 16px;
            color: var(--muted);
            font-size: 14px;
            font-weight: 600;
        }

        .groups-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .group-card {
            min-width: 0;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: var(--shadow);
        }

        .group-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px 18px 14px;
            border-bottom: 1px solid var(--border-soft);
        }

        .group-title {
            font-size: 30px;
            line-height: 1;
            font-weight: 850;
        }

        .group-stats {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            min-height: 28px;
            border: 1px solid var(--border-soft);
            border-radius: 999px;
            background: var(--panel-soft);
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
            padding: 4px 10px;
            white-space: nowrap;
        }

        .manga-list {
            padding: 8px;
        }

        .manga {
            border: 1px solid transparent;
            border-radius: 8px;
        }

        .manga + .manga {
            margin-top: 4px;
        }

        .manga[open] {
            border-color: var(--border-soft);
            background: #fcfcfd;
        }

        .manga summary {
            display: grid;
            grid-template-columns: 18px minmax(0, 1fr) auto;
            gap: 8px;
            align-items: center;
            min-height: 44px;
            padding: 8px 10px;
            border-radius: 8px;
            cursor: pointer;
            color: var(--text);
            font-size: 14px;
            font-weight: 700;
            list-style: none;
        }

        .manga summary::-webkit-details-marker {
            display: none;
        }

        .chevron {
            color: var(--muted-soft);
            font-size: 12px;
            transition: transform 0.16s ease;
        }

        .manga[open] .chevron {
            transform: rotate(90deg);
        }

        .manga-title {
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .manga-count {
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
        }

        .table-wrap {
            overflow-x: auto;
            padding: 0 10px 12px 36px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            border: 1px solid var(--border-soft);
            border-radius: 8px;
            overflow: hidden;
            background: var(--panel);
            font-size: 13px;
        }

        th, td {
            border-bottom: 1px solid var(--border-soft);
            padding: 10px 12px;
            text-align: left;
            vertical-align: middle;
            overflow-wrap: anywhere;
        }

        th {
            background: var(--panel-soft);
            color: var(--muted);
            font-size: 12px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        tbody tr:last-child td {
            border-bottom: 0;
        }

        .old {
            color: #b91c1c;
        }

        .new {
            color: #15803d;
            font-weight: 600;
        }

        .empty {
            color: var(--muted-soft);
            padding: 18px;
            font-size: 14px;
        }

        .no-results {
            display: none;
            border: 1px dashed var(--border);
            border-radius: 8px;
            background: var(--panel);
            color: var(--muted);
            padding: 26px;
            text-align: center;
            font-weight: 700;
        }

        @media (max-width: 1100px) {
            .brand-row {
                display: block;
            }

            .brand {
                margin-bottom: 14px;
            }

            .summary-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .groups-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 720px) {
            .topbar-inner,
            .page {
                padding-left: 16px;
                padding-right: 16px;
            }

            .toolbar {
                grid-template-columns: 1fr;
            }

            .actions {
                justify-content: stretch;
            }

            .actions button {
                flex: 1;
            }

            .summary-grid {
                grid-template-columns: 1fr;
            }

            .group-header {
                align-items: flex-start;
                flex-direction: column;
            }

            .group-stats {
                justify-content: flex-start;
            }

            .table-wrap {
                padding-left: 10px;
            }
        }
        """,
        "</style>",
        "</head>",
        "<body>",
        "<header class='topbar'>",
        "<div class='topbar-inner'>",
        "<div class='brand-row'>",
        "<div class='brand'>",
        "<h1>Manhwateca</h1>",
        "<div class='subtitle'>Preview de Renomeação</div>",
        "</div>",
        "<div class='summary-grid' aria-label='Resumo'>",
        "<div class='summary-card'><div class='summary-label'>Obras</div>"
        f"<div class='summary-value'>{total_mangas}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Arquivos</div>"
        f"<div class='summary-value'>{total_files}</div></div>",
        "<div class='summary-card'><div class='summary-label'>Grupos</div>"
        f"<div class='summary-value'>{total_groups}</div></div>",
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
        f"<div class='live-count' id='liveCount'>{total_mangas} obras • {total_files} alterações</div>",
        "<div class='groups-grid' id='groupsGrid'>",
    ]

    for group in GROUPS:
        mangas = plan.get(group, {})
        group_file_count = sum(len(files) for files in mangas.values())

        html_parts.append(
            "<section class='group-card' "
            f"data-group='{html.escape(group)}' "
            f"data-total-mangas='{len(mangas)}' "
            f"data-total-files='{group_file_count}'>"
        )
        html_parts.append("<div class='group-header'>")
        html_parts.append(f"<div class='group-title'>{html.escape(group)}</div>")
        html_parts.append("<div class='group-stats'>")
        html_parts.append(
            f"<span class='pill'><span class='group-manga-count'>{len(mangas)}</span> obras</span>"
        )
        html_parts.append(
            f"<span class='pill'><span class='group-file-count'>{group_file_count}</span> alterações</span>"
        )
        html_parts.append("</div>")
        html_parts.append("</div>")

        if not mangas:
            html_parts.append("<div class='empty'>Nenhuma alteração.</div>")
        else:
            html_parts.append("<div class='manga-list'>")

        for manga_name in sorted(mangas.keys(), key=str.lower):
            files = mangas[manga_name]
            search_text = " ".join(
                [manga_name]
                + [item["old_name"] for item in files]
                + [item["new_name"] for item in files]
            ).lower()

            html_parts.append(
                "<details class='manga' "
                f"data-search='{html.escape(search_text, quote=True)}' "
                f"data-total-files='{len(files)}'>"
            )
            html_parts.append(
                "<summary>"
                "<span class='chevron'>▶</span>"
                f"<span class='manga-title'>{html.escape(manga_name)}</span>"
                f"<span class='manga-count'>(<span class='manga-file-count'>{len(files)}</span>)</span>"
                "</summary>"
            )

            html_parts.append("<div class='table-wrap'>")
            html_parts.append("<table>")
            html_parts.append("<thead>")
            html_parts.append("<tr><th>Antes</th><th>Depois</th></tr>")
            html_parts.append("</thead>")
            html_parts.append("<tbody>")

            for item in sorted(files, key=lambda x: x["old_name"].lower()):
                row_search = f"{manga_name} {item['old_name']} {item['new_name']}".lower()
                html_parts.append(
                    f"<tr data-search='{html.escape(row_search, quote=True)}'>"
                )
                html_parts.append(f"<td class='old'>{html.escape(item['old_name'])}</td>")
                html_parts.append(f"<td class='new'>{html.escape(item['new_name'])}</td>")
                html_parts.append("</tr>")

            html_parts.append("</tbody>")
            html_parts.append("</table>")
            html_parts.append("</div>")
            html_parts.append("</details>")

        if mangas:
            html_parts.append("</div>")

        html_parts.append("</section>")

    html_parts.append("</div>")
    html_parts.append("<div class='no-results' id='noResults'>Nenhuma alteração encontrada para a busca.</div>")
    html_parts.append("</main>")
    html_parts.append(
        """
        <script>
        const searchInput = document.getElementById('search');
        const liveCount = document.getElementById('liveCount');
        const noResults = document.getElementById('noResults');
        const groups = Array.from(document.querySelectorAll('.group-card'));
        const mangas = Array.from(document.querySelectorAll('.manga'));

        function setAll(open) {
            mangas.forEach((manga) => {
                if (manga.style.display !== 'none') {
                    manga.open = open;
                }
            });
        }

        function plural(value, singular, pluralText) {
            return value === 1 ? singular : pluralText;
        }

        function applyFilter() {
            const query = searchInput.value.trim().toLowerCase();
            let visibleMangas = 0;
            let visibleFiles = 0;

            groups.forEach((group) => {
                let groupMangas = 0;
                let groupFiles = 0;

                group.querySelectorAll('.manga').forEach((manga) => {
                    const mangaMatches = !query || manga.dataset.search.includes(query);
                    let mangaFiles = 0;

                    manga.querySelectorAll('tbody tr').forEach((row) => {
                        const rowMatches = !query || row.dataset.search.includes(query);
                        row.style.display = rowMatches ? '' : 'none';
                        if (rowMatches) {
                            mangaFiles += 1;
                        }
                    });

                    const showManga = mangaMatches && mangaFiles > 0;
                    manga.style.display = showManga ? '' : 'none';

                    if (showManga) {
                        groupMangas += 1;
                        groupFiles += mangaFiles;
                        manga.querySelector('.manga-file-count').textContent = mangaFiles;
                    }
                });

                group.style.display = groupMangas > 0 || (!query && Number(group.dataset.totalFiles) === 0) ? '' : 'none';
                group.querySelector('.group-manga-count').textContent = groupMangas;
                group.querySelector('.group-file-count').textContent = groupFiles;

                visibleMangas += groupMangas;
                visibleFiles += groupFiles;
            });

            liveCount.textContent = `${visibleMangas} ${plural(visibleMangas, 'obra', 'obras')} • ${visibleFiles} ${plural(visibleFiles, 'alteração', 'alterações')}`;
            noResults.style.display = visibleFiles === 0 && query ? 'block' : 'none';
        }

        document.getElementById('expandAll').addEventListener('click', () => setAll(true));
        document.getElementById('collapseAll').addEventListener('click', () => setAll(false));
        searchInput.addEventListener('input', applyFilter);
        applyFilter();
        </script>
        """
    )
    html_parts.append("</body>")
    html_parts.append("</html>")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(html_parts), encoding="utf-8")


def apply_plan(plan):
    if DRY_RUN:
        return

    for mangas in plan.values():
        for files in mangas.values():
            for item in files:
                old_path = Path(item["old_path"])
                new_path = Path(item["new_path"])

                if new_path.exists():
                    continue

                old_path.rename(new_path)


def main():
    if not MANGA_ROOT.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {MANGA_ROOT}")

    plan = build_plan()

    generate_html(plan)
    apply_plan(plan)

    print(f"Preview gerado em: {REPORT_PATH}")


if __name__ == "__main__":
    main()
