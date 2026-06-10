import html
import json
from pathlib import Path

from report_utils import build_html_page, render_summary_cards, write_report


DATA_FILE = Path("data/mangas.json")
REPORT_FILE = Path("reports/chapter_audit.html")


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
    external_differences = [
        manga
        for manga in mangas
        if manga.get("mangaupdates_latest_chapter") is not None
        and manga.get("main_caps", 0) != manga["mangaupdates_latest_chapter"]
    ]
    cards = render_summary_cards([
        {"label": "Obras", "value": len(mangas)},
        {"label": "Revisar", "value": len(review)},
        {"label": "Divergências externas", "value": len(external_differences)},
        {"label": "Sem lacunas", "value": len(mangas) - len(review)},
    ])

    rows = []
    for manga in mangas:
        status = audit_status(manga)
        issues = ", ".join(manga.get("count_issues", [])) or "Nenhuma"
        missing = ", ".join(manga.get("missing_ranges", [])) or "-"
        unparsed = "<br>".join(
            html.escape(name) for name in manga.get("unparsed_files", [])
        ) or "-"
        external = manga.get("mangaupdates_latest_chapter")
        external_text = str(external) if external is not None else "-"
        source_url = manga.get("mangaupdates_url")
        if source_url:
            external_text = (
                f"<a href='{html.escape(source_url)}' target='_blank' "
                f"rel='noreferrer'>{external_text}</a>"
            )
        rows.append(
            "<tr class='manga' data-search='{search}'>"
            "<td>{name}</td><td>{status}</td><td>{last}</td><td>{found}</td>"
            "<td>{side}</td><td>{missing}</td><td>{external}</td>"
            "<td>{issues}</td><td>{unparsed}</td></tr>".format(
                search=html.escape(manga["nome"].casefold()),
                name=html.escape(manga["nome"]),
                status=html.escape(status),
                last=manga.get("main_caps", 0),
                found=manga.get("chapters_found", 0),
                side=manga.get("side_stories_found", 0),
                missing=html.escape(missing),
                external=external_text,
                issues=html.escape(issues),
                unparsed=unparsed,
            )
        )

    body = "\n".join([
        "<div class='table-wrap'><table>",
        "<thead><tr><th>Obra</th><th>Status</th><th>Último local</th>"
        "<th>Encontrados</th><th>Side stories</th><th>Lacunas</th>"
        "<th>MangaUpdates</th><th>Problemas</th>"
        "<th>Não interpretados</th></tr></thead>",
        "<tbody>",
        *rows,
        "</tbody></table></div>",
    ])
    extra_css = """
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
    extra_js = """
searchInput.addEventListener('input', () => {
    const query = searchInput.value.trim().toLocaleLowerCase();
    document.querySelectorAll('tbody .manga').forEach((row) => {
        row.hidden = !row.dataset.search.includes(query);
    });
});
"""
    return build_html_page(
        "Auditoria de Capítulos",
        "Compara contagem local, lacunas e referência do MangaUpdates.",
        cards,
        body,
        extra_css,
        extra_js,
    )


def main():
    mangas = load_mangas()
    write_report(REPORT_FILE, render_report(mangas))
    print(f"Relatório gerado: {REPORT_FILE}")


if __name__ == "__main__":
    main()
