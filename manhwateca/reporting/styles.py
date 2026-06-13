COMMON_CSS = """
* { box-sizing: border-box; }
.manga summary::-webkit-details-marker { display: none; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border-soft);
}
th { font-weight: 600; color: var(--muted); background: var(--border-soft); }
tbody tr:last-child td { border-bottom: 0; }
@media (max-width: 1100px) {
    .brand-row { display: block; }
    .brand { margin-bottom: 14px; }
    .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .groups-grid { column-count: 1; }
}
@media (max-width: 720px) {
    .topbar-inner, .page { padding-left: 16px; padding-right: 16px; }
    .toolbar { flex-direction: column; }
    .actions { width: 100%; }
    .actions button { flex: 1; }
}
"""


COMMON_JS = """
const searchInput = document.getElementById('search');
const expandAllButton = document.getElementById('expandAll');
const collapseAllButton = document.getElementById('collapseAll');
function setAll(open) {
    document.querySelectorAll('.manga').forEach((el) => { el.open = open; });
}
expandAllButton.addEventListener('click', () => setAll(true));
collapseAllButton.addEventListener('click', () => setAll(false));
"""
