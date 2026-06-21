import html
import json
from pathlib import Path


from manhwateca.mangaupdates_service.review.data import (
    consolidate_review_items as _consolidate_review_items,
    count_confirmed_without_details as _count_confirmed_without_details,
    load_json_object,
    normalize_title,
)
from manhwateca.mangaupdates_service.review.decisions import (
    backup_path,
    import_decisions as _import_decisions,
    load_decisions,
    load_items as _load_items,
)
from manhwateca.mangaupdates_service.review.parser import build_parser
from manhwateca.mangaupdates_service.review.rendering import (
    render_candidate,
    score_class,
)
from manhwateca.mangaupdates_service.review.service import (
    generate_report as _generate_report,
    run_cli,
)


IDS_FILE = Path("reports/integrations/buscaIds.json")
REPORT_FILE = Path("reports/audits/mangaupdates_id_review.html")
DEFAULT_DECISIONS_FILE = Path(
    "reports/integrations/mangaupdates_id_decisions.json"
)
CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
METADATA_FILE = Path("config/catalog_metadata.json")
CACHE_FILE = Path("data/mangaupdates.json")


def load_items(path=IDS_FILE):
    return _load_items(path)


def import_decisions(decisions_path, ids_path=IDS_FILE, decision_repository=None):
    return _import_decisions(
        decisions_path,
        ids_path,
        decision_repository=decision_repository,
    )


def count_confirmed_without_details(items, cache_path=CACHE_FILE):
    return _count_confirmed_without_details(items, cache_path)


def consolidate_review_items(items, csv_path=None, metadata_path=METADATA_FILE):
    return _consolidate_review_items(items, csv_path, metadata_path)


def render_report(items, csv_path=None, metadata_path=METADATA_FILE):
    review_items = consolidate_review_items(
        items,
        csv_path=csv_path,
        metadata_path=metadata_path,
    )
    confirmed_items = [
        item for item in items
        if item.get("Status") in {
            "Confirmado automaticamente",
            "Confirmado manualmente",
        } and item.get("ID")
    ]
    confirmed = sum(
        item.get("Status") in {
            "Confirmado automaticamente",
            "Confirmado manualmente",
        }
        for item in items
    )
    cards = []
    for item in review_items:
        candidates = [
            candidate for candidate in item.get("IDs", [])
            if float(candidate.get("pontuacao") or 0) > 0.70
        ]
        decision_name = str(item.get("Nome decisão") or item.get("Nome", ""))
        related_names = [
            str(name) for name in item.get("Nomes relacionados", [])
            if name and str(name) != str(item.get("Nome"))
        ]
        related_text = (
            "<div class='related-names'>Também catalogada como: "
            + html.escape(" | ".join(related_names))
            + "</div>"
            if related_names else ""
        )
        candidates_html = "".join(
            render_candidate(candidate, suggested=index == 0)
            for index, candidate in enumerate(candidates)
        )
        search = html.escape(
            " ".join(
                [str(item.get("Nome", ""))]
                + [str(candidate.get("titulo", "")) for candidate in candidates]
            ).casefold(),
            quote=True,
        )
        cards.append(f"""
        <details class="work" data-category="review"
          data-decision-name="{html.escape(decision_name, quote=True)}"
          data-search="{search}">
          <summary>
            <span>
              <span class="work-title">{html.escape(str(item.get("Nome", "")))}</span>
              <span class="candidate-count">{len(candidates)} candidatos</span>
            </span>
            <span class="status" data-status>Revisar</span>
          </summary>
          <div class="work-body">
            <p class="guidance">Compare título, tipo, ano e sinopse. Abra a ficha
            externa quando precisar confirmar personagens ou capa. A lista
            mostra somente candidatos com score acima de 0,70 e prioriza
            títulos classificados como Yaoi ou Shounen Ai.</p>
            {related_text}
            <div class="candidate-grid">{candidates_html or
              "<div class='no-candidates'>Nenhum candidato atingiu o score mínimo.</div>"}</div>
            <div class="manual-id">
              <div>
                <strong>Nenhuma das opções?</strong>
                <span>Informe o ID correto da obra no MangaUpdates.</span>
              </div>
              <div class="manual-id-action">
                <input type="number" min="1" step="1"
                  class="manual-id-input" placeholder="Ex.: 53840259364">
                <button type="button" class="manual-id-button">
                  Usar este ID
                </button>
              </div>
            </div>
          </div>
        </details>
        """)

    for item in confirmed_items:
        confirmation = str(item.get("Status"))
        status_label = (
            "Aplicado"
            if confirmation == "Confirmado manualmente"
            else "Confirmado"
        )
        cards.append(f"""
        <details class="work applied-work"
          data-category="confirmed"
          data-search="{html.escape(str(item.get("Nome", "")).casefold(), quote=True)}">
          <summary>
            <span>
              <span class="work-title">{html.escape(str(item.get("Nome", "")))}</span>
              <span class="candidate-count">ID {html.escape(str(item.get("ID")))}</span>
            </span>
            <span class="status applied">{status_label}</span>
          </summary>
          <div class="work-body">
            <p class="guidance">Decisão importada no buscaIds.json.</p>
            <div class="flow-files">
              Nome encontrado: {html.escape(str(item.get("Nome encontrado", "")))}<br>
              Status: {html.escape(confirmation)}
            </div>
          </div>
        </details>
        """)

    data = json.dumps(
        [{
            "name": item.get("Nome decisão") or item.get("Nome", ""),
        } for item in review_items],
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Revisão de IDs MangaUpdates</title>
<style>
:root {{ --ink:#27303f; --muted:#788496; --line:#e5e9ee; --blue:#3976d2;
--blue-soft:#edf5ff; --green:#267a55; --amber:#a96613; --paper:#fff; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--ink); background:#f7f8fa;
font:15px/1.55 Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.page {{ max-width:1240px; margin:auto; padding:42px 28px 70px; }}
.hero {{ display:flex; justify-content:space-between; gap:24px; align-items:end;
margin-bottom:26px; }}
h1 {{ margin:0 0 5px; font-size:30px; letter-spacing:-.03em; }}
.subtitle,.muted {{ color:var(--muted); }}
.summary {{ display:flex; gap:10px; flex-wrap:wrap; }}
.pill {{ padding:8px 12px; border:1px solid var(--line); border-radius:9px;
background:var(--paper); box-shadow:0 5px 18px rgba(31,41,55,.04);
color:var(--ink); cursor:pointer; font:inherit; }}
.pill:hover {{ border-color:#b9c7d8; transform:translateY(-1px); }}
.pill.active {{ color:#235da8; border-color:#9fc1ec; background:var(--blue-soft);
box-shadow:0 5px 18px rgba(57,118,210,.12); }}
.toolbar {{ position:sticky; top:0; z-index:5; display:flex; gap:12px;
padding:14px; margin-bottom:18px; border:1px solid var(--line); border-radius:12px;
background:rgba(255,255,255,.94); box-shadow:0 8px 26px rgba(31,41,55,.06);
backdrop-filter:blur(10px); }}
input {{ flex:1; min-width:180px; padding:11px 13px; border:1px solid #d8dee6;
border-radius:8px; font:inherit; }}
button,.external {{ border:0; border-radius:7px; padding:9px 12px; font:600 13px inherit;
cursor:pointer; text-decoration:none; }}
.export {{ color:#fff; background:var(--green); }}
.secondary {{ color:var(--ink); background:#eef1f4; }}
.work {{ margin-bottom:12px; border:1px solid var(--line); border-radius:11px;
background:var(--paper); box-shadow:0 7px 22px rgba(31,41,55,.045); overflow:hidden; }}
summary {{ display:flex; justify-content:space-between; align-items:center; gap:15px;
padding:18px 20px; cursor:pointer; list-style:none; }}
summary::-webkit-details-marker {{ display:none; }}
.work-title {{ font-size:17px; font-weight:700; }}
.candidate-count {{ margin-left:9px; color:var(--muted); font-size:13px; }}
.status {{ padding:4px 10px; border-radius:999px; color:var(--amber); background:#fff5df;
font-size:12px; font-weight:700; }}
.status.selected {{ color:var(--green); background:#e8f7ef; }}
.status.applied {{ color:#315f91; background:#eaf3ff; }}
.work-body {{ padding:0 20px 20px; border-top:1px solid var(--line); }}
.guidance {{ color:var(--muted); }}
.related-names {{ margin:-2px 0 14px; padding:8px 10px; color:#536174;
background:#f3f6f9; border-radius:7px; font-size:13px; }}
.candidate-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
.no-candidates {{ grid-column:1/-1; padding:18px; color:var(--muted);
border:1px dashed #ccd4de; border-radius:9px; text-align:center; }}
.manual-id {{ display:flex; justify-content:space-between; align-items:center; gap:18px;
margin-top:16px; padding:16px; border:1px solid #dce4ed; border-radius:9px;
background:#f8fafc; }}
.manual-id span {{ display:block; color:var(--muted); font-size:13px; }}
.manual-id-action {{ display:flex; gap:8px; }}
.manual-id-input {{ width:190px; min-width:0; }}
.manual-id-button {{ color:#fff; background:#586b84; white-space:nowrap; }}
.candidate {{ padding:16px; border:1px solid var(--line); border-radius:9px; background:#fff; }}
.candidate.suggested {{ border-color:#bdd7f6; background:var(--blue-soft); }}
.candidate.selected {{ outline:2px solid #62a67f; background:#f1fbf5; }}
.candidate-head,.candidate-actions {{ display:flex; justify-content:space-between; gap:12px;
align-items:center; }}
.position {{ margin-right:7px; color:var(--muted); }}
.suggested-label {{ margin-left:8px; color:var(--blue); font-size:11px; font-weight:700; }}
.score {{ min-width:48px; padding:4px 8px; text-align:center; border-radius:7px; font-weight:800; }}
.score-high {{ color:#24704e; background:#e5f6ec; }}
.score-medium {{ color:#996114; background:#fff2d8; }}
.score-low {{ color:#77808d; background:#eef0f3; }}
.metadata {{ display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; color:var(--muted);
font-size:12px; }}
.metadata span {{ padding:3px 7px; background:#f2f4f6; border-radius:5px; }}
.description {{ color:#4b5666; display:-webkit-box; -webkit-line-clamp:4;
-webkit-box-orient:vertical; overflow:hidden; }}
.external {{ color:var(--blue); background:#edf4fd; }}
.select-button {{ color:#fff; background:var(--blue); }}
.empty {{ padding:35px; text-align:center; border:1px solid var(--line); border-radius:12px;
background:#fff; }}
@media(max-width:800px) {{ .hero,.toolbar {{ align-items:stretch; flex-direction:column; }}
.candidate-grid {{ grid-template-columns:1fr; }}
.manual-id,.manual-id-action {{ align-items:stretch; flex-direction:column; }}
.manual-id-input {{ width:100%; }} }}
</style>
</head>
<body>
<main class="page">
  <header class="hero">
    <div><h1>Revisão de IDs MangaUpdates</h1>
    <div class="subtitle">Compare os candidatos antes de vinculá-los à biblioteca.</div></div>
    <div class="summary">
      <button type="button" class="pill active" data-filter="review"
        aria-pressed="true"><strong>{len(review_items)}</strong> para revisar</button>
      <button type="button" class="pill" data-filter="confirmed"
        aria-pressed="false"><strong>{confirmed}</strong> IDs confirmados</button>
      <button type="button" class="pill" data-filter="selected"
        aria-pressed="false"><strong id="selectedCount">0</strong> decisões tomadas</button>
    </div>
  </header>
  <div class="toolbar">
    <input id="search" type="search" placeholder="Buscar obra ou candidato...">
    <button class="secondary" id="expandAll">Expandir tudo</button>
    <button class="secondary" id="collapseAll">Recolher tudo</button>
    <button class="export" id="export">Exportar decisões</button>
  </div>
  <section id="works">{"".join(cards) if cards else '<div class="empty">Nenhuma obra aguardando revisão.</div>'}</section>
</main>
<script>
const works = {data};
const decisions = JSON.parse(localStorage.getItem("manhwateca-id-decisions") || "{{}}");
const reviewNames = new Set(works.map((work) => work.name));
let activeFilter = "review";
Object.keys(decisions).forEach((name) => {{
  if (!reviewNames.has(name)) delete decisions[name];
}});
function applyFilters() {{
  const query = document.getElementById("search").value.trim()
    .toLocaleLowerCase("pt-BR");
  document.querySelectorAll(".work").forEach((work) => {{
    const name = work.dataset.decisionName ||
      work.querySelector(".work-title").textContent;
    const categoryMatch = activeFilter === "selected"
      ? Boolean(decisions[name])
      : work.dataset.category === activeFilter;
    work.hidden = !categoryMatch || !work.dataset.search.includes(query);
  }});
}}
function refresh() {{
  document.querySelectorAll(".work:not(.applied-work)").forEach((work) => {{
    const name = work.dataset.decisionName ||
      work.querySelector(".work-title").textContent;
    const selected = decisions[name];
    work.querySelectorAll(".candidate").forEach((card) => {{
      card.classList.toggle("selected", card.querySelector(".select-button").dataset.id === String(selected?.id));
    }});
    const status = work.querySelector("[data-status]");
    status.textContent = selected ? "Selecionado" : "Revisar";
    status.classList.toggle("selected", Boolean(selected));
  }});
  document.getElementById("selectedCount").textContent = Object.keys(decisions).length;
  localStorage.setItem("manhwateca-id-decisions", JSON.stringify(decisions));
  applyFilters();
}}
document.querySelectorAll(".select-button").forEach((button) => button.addEventListener("click", () => {{
  const work = button.closest(".work");
  const name = work.dataset.decisionName ||
    work.querySelector(".work-title").textContent;
  decisions[name] = {{ id:Number(button.dataset.id), title:button.dataset.title }};
  refresh();
}}));
document.querySelectorAll(".manual-id-button").forEach((button) =>
  button.addEventListener("click", () => {{
    const work = button.closest(".work");
    const input = work.querySelector(".manual-id-input");
    const id = Number(input.value);
    if (!Number.isInteger(id) || id <= 0) {{
      input.focus();
      return alert("Informe um ID numérico válido.");
    }}
    const name = work.dataset.decisionName ||
      work.querySelector(".work-title").textContent;
    decisions[name] = {{
      id,
      title:`ID ${{id}}`,
      source:"ID informado manualmente"
    }};
    refresh();
  }}));
document.getElementById("search").addEventListener("input", (event) => {{
  applyFilters();
}});
document.querySelectorAll("[data-filter]").forEach((button) =>
  button.addEventListener("click", () => {{
    activeFilter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => {{
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", String(active));
    }});
    applyFilters();
  }}));
document.getElementById("expandAll").addEventListener("click", () =>
  document.querySelectorAll(".work:not([hidden])").forEach((work) => work.open = true));
document.getElementById("collapseAll").addEventListener("click", () =>
  document.querySelectorAll(".work").forEach((work) => work.open = false));
document.getElementById("export").addEventListener("click", () => {{
  const payload = Object.entries(decisions).map(([Nome, choice]) => ({{
    Nome, ID:choice.id, "Nome encontrado":choice.title,
    Origem:choice.source || "Candidato exibido"
  }}));
  if (!payload.length) return alert("Selecione pelo menos um candidato.");
  const blob = new Blob([JSON.stringify(payload, null, 2) + "\\n"], {{type:"application/json"}});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "mangaupdates_id_decisions.json";
  link.click();
  URL.revokeObjectURL(link.href);
}});
refresh();
</script>
</body>
</html>"""


def generate_report(
    ids_path=IDS_FILE,
    report_path=REPORT_FILE,
    csv_path=CSV_FILE,
):
    return _generate_report(
        ids_path,
        report_path,
        csv_path,
        load_items=load_items,
        consolidate_items=consolidate_review_items,
        render_report=render_report,
    )


def main():
    args = build_parser(IDS_FILE).parse_args()
    run_cli(args, {
        "import_decisions": import_decisions,
        "count_pending_details": count_confirmed_without_details,
        "load_items": load_items,
        "generate_report": generate_report,
    })


if __name__ == "__main__":
    main()
