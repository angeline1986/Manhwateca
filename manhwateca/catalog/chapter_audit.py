import html
import json
from pathlib import Path

from manhwateca.reporting import (
    build_html_page,
    render_summary_cards,
    write_report,
)


DATA_FILE = Path("data/mangas.json")
REPORT_FILE = Path("reports/audits/chapter_audit.html")


def load_mangas(path=DATA_FILE):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def audit_status(manga):
    external = manga.get("mangaupdates_latest_chapter")
    local = manga.get("main_caps", 0)
    if external is not None and local != external:
        return "Divergência externa"
    return manga.get("count_status", "Revisar")


def render_report(mangas):
    review = [manga for manga in mangas if audit_status(manga) != "OK"]
    external = [
        manga for manga in mangas
        if manga.get("mangaupdates_latest_chapter") is not None
        and manga.get("main_caps", 0) != manga["mangaupdates_latest_chapter"]
    ]
    cards = render_summary_cards([
        {"label": "Obras", "value": len(mangas)},
        {"label": "Revisar", "value": len(review)},
        {"label": "Divergências externas", "value": len(external)},
        {"label": "Sem lacunas", "value": len(mangas) - len(review)},
    ])
    rows = "\n".join(_render_row(manga) for manga in mangas)
    body = (
        "<div class='table-wrap'><table><thead><tr><th>Obra</th>"
        "<th>Status</th><th>Último local</th><th>Encontrados</th>"
        "<th>Side stories</th><th>Lacunas</th><th>MangaUpdates</th>"
        "<th>Problemas</th><th>Não interpretados</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )
    return build_html_page(
        "Auditoria de Capítulos",
        "Compara contagem local, lacunas e referência do MangaUpdates.",
        cards,
        body,
        EXTRA_CSS,
        EXTRA_JS,
    )


def _render_row(manga):
    status = audit_status(manga)
    issues = ", ".join(manga.get("count_issues", [])) or "Nenhuma"
    missing = ", ".join(manga.get("missing_ranges", [])) or "-"
    unparsed = "<br>".join(
        html.escape(name) for name in manga.get("unparsed_files", [])
    ) or "-"
    external = manga.get("mangaupdates_latest_chapter")
    external_text = str(external) if external is not None else "-"
    if manga.get("mangaupdates_url"):
        url = html.escape(manga["mangaupdates_url"], quote=True)
        external_text = (
            f"<a href='{url}' target='_blank' rel='noreferrer'>"
            f"{external_text}</a>"
        )
    values = [
        html.escape(manga["nome"]),
        html.escape(status),
        str(manga.get("main_caps", 0)),
        str(manga.get("chapters_found", 0)),
        str(manga.get("side_stories_found", 0)),
        html.escape(missing),
        external_text,
        html.escape(issues),
        unparsed,
    ]
    cells = "".join(f"<td>{value}</td>" for value in values)
    search = html.escape(manga["nome"].casefold(), quote=True)
    return f"<tr class='manga' data-search='{search}'>{cells}</tr>"


def main():
    write_report(REPORT_FILE, render_report(load_mangas()))
    print(f"Relatório gerado: {REPORT_FILE}")


EXTRA_CSS = """
body { margin: 0; font-family: system-ui, sans-serif; background: #f7f8fa; color: #20242a; }
.topbar { background: white; border-bottom: 1px solid #dfe3e8; }
.topbar-inner, .page { max-width: 1600px; margin: auto; padding: 24px; }
.brand-row, .toolbar { display: flex; gap: 20px; justify-content: space-between; align-items: center; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; }
.summary-card, .table-wrap { background: white; border: 1px solid #dfe3e8; border-radius: 10px; }
.summary-card { padding: 12px; }
.summary-label { color: #68707b; font-size: 12px; }
.summary-value { font-size: 24px; font-weight: 700; }
.toolbar { margin-top: 18px; }
.search { width: 100%; padding: 10px 12px; border: 1px solid #cbd1d8; border-radius: 8px; }
.actions { display: none; }
.table-wrap { overflow: auto; }
a { color: #1463d6; }
"""

EXTRA_JS = """
searchInput.addEventListener('input', () => {
    const query = searchInput.value.trim().toLocaleLowerCase();
    document.querySelectorAll('tbody .manga').forEach((row) => {
        row.hidden = !row.dataset.search.includes(query);
    });
});
"""
