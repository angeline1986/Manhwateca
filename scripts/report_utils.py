import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.reporting import (
    build_html_page,
    render_summary_cards,
    write_report,
)
from manhwateca.reporting.styles import COMMON_CSS, COMMON_JS


__all__ = [
    "COMMON_CSS",
    "COMMON_JS",
    "build_html_page",
    "render_summary_cards",
    "write_report",
]
