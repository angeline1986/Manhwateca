import tempfile
import unittest
from pathlib import Path

from manhwateca.reporting import (
    build_html_page,
    render_summary_cards,
    write_report,
)


class ReportingTests(unittest.TestCase):
    def test_summary_cards_escape_content(self):
        rendered = render_summary_cards([
            {"label": "<Obras>", "value": "1 & 2"},
        ])

        self.assertIn("&lt;Obras&gt;", rendered)
        self.assertIn("1 &amp; 2", rendered)

    def test_page_keeps_domain_body_and_escapes_heading(self):
        rendered = build_html_page(
            "Título & teste",
            "Subtítulo",
            "<div>Resumo</div>",
            "<section id='domain'>Conteúdo</section>",
        )

        self.assertIn("<title>Título &amp; teste</title>", rendered)
        self.assertIn("<section id='domain'>Conteúdo</section>", rendered)

    def test_write_report_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audits" / "report.html"

            write_report(path, "<html></html>")

            self.assertEqual("<html></html>", path.read_text(encoding="utf-8"))
