import html
from pathlib import Path

COMMON_CSS = """
* {
    box-sizing: border-box;
}

.manga summary::-webkit-details-marker {
    display: none;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

th,
td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border-soft);
}

th {
    font-weight: 600;
    color: var(--muted);
    background: var(--border-soft);
}

tbody tr:last-child td {
    border-bottom: 0;
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
        column-count: 1;
    }
}

@media (max-width: 720px) {
    .topbar-inner,
    .page {
        padding-left: 16px;
        padding-right: 16px;
    }

    .toolbar {
        flex-direction: column;
    }

    .actions {
        width: 100%;
    }

    .actions button {
        flex: 1;
    }
}
"""

COMMON_JS = """
const searchInput = document.getElementById('search');
const expandAllButton = document.getElementById('expandAll');
const collapseAllButton = document.getElementById('collapseAll');

function setAll(open) {
    document.querySelectorAll('.manga').forEach((el) => {
        el.open = open;
    });
}

expandAllButton.addEventListener('click', () => setAll(true));
collapseAllButton.addEventListener('click', () => setAll(false));
"""


def render_summary_cards(cards):
    html_parts = ["<div class='summary-grid' aria-label='Resumo'>"]

    for card in cards:
        html_parts.append(
            "<div class='summary-card'><div class='summary-label'>{label}</div>"
            "<div class='summary-value'>{value}</div></div>".format(
                label=html.escape(str(card['label'])),
                value=html.escape(str(card['value'])),
            )
        )

    html_parts.append("</div>")
    return "\n".join(html_parts)


def build_html_page(title, subtitle, summary_cards_html, page_body_html, extra_css="", extra_js=""):
    return "\n".join([
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"<title>{html.escape(str(title))}</title>",
        "<style>",
        COMMON_CSS,
        extra_css,
        "</style>",
        "</head>",
        "<body>",
        "<header class='topbar'>",
        "<div class='topbar-inner'>",
        "<div class='brand-row'>",
        "<div class='brand'>",
        f"<h1>{html.escape(str(title))}</h1>",
        f"<div class='subtitle'>{html.escape(str(subtitle))}</div>",
        "</div>",
        summary_cards_html,
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
        page_body_html,
        "</main>",
        "<script>",
        COMMON_JS,
        extra_js,
        "</script>",
        "</body>",
        "</html>",
    ])


def write_report(report_path, html_text):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html_text, encoding='utf-8')
