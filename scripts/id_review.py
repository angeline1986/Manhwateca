import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path


IDS_FILE = Path("reports/integrations/buscaIds.json")
REPORT_FILE = Path("reports/audits/mangaupdates_id_review.html")
DEFAULT_DECISIONS_FILE = Path(
    "reports/integrations/mangaupdates_id_decisions.json"
)


def load_items(path=IDS_FILE):
    with path.open(encoding="utf-8") as file:
        items = json.load(file)
    if not isinstance(items, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return items


def load_decisions(path):
    with path.open(encoding="utf-8") as file:
        decisions = json.load(file)
    if not isinstance(decisions, list):
        raise ValueError(
            f"Formato inválido em {path}: era esperada uma lista de decisões."
        )
    return decisions


def backup_path(path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.stem}.backup-{timestamp}{path.suffix}")


def import_decisions(decisions_path, ids_path=IDS_FILE):
    items = load_items(ids_path)
    decisions = load_decisions(decisions_path)
    by_name = {}
    duplicate_names = set()
    for position, item in enumerate(items):
        name = str(item.get("Nome") or "").strip()
        if name in by_name:
            duplicate_names.add(name)
        by_name[name] = position

    applied = []
    rejected = []
    seen = set()
    for decision in decisions:
        if not isinstance(decision, dict):
            rejected.append("Decisão inválida: era esperado um objeto.")
            continue
        name = str(decision.get("Nome") or "").strip()
        series_id = decision.get("ID")
        selected_title = str(decision.get("Nome encontrado") or "").strip()
        if not name or series_id in (None, ""):
            rejected.append("Decisão sem Nome ou ID.")
            continue
        if name in seen:
            rejected.append(f"{name}: decisão duplicada no arquivo.")
            continue
        seen.add(name)
        if name in duplicate_names:
            rejected.append(f"{name}: nome duplicado no buscaIds.json.")
            continue
        position = by_name.get(name)
        if position is None:
            rejected.append(f"{name}: obra não encontrada no buscaIds.json.")
            continue

        item = items[position]
        candidates = item.get("IDs") or []
        candidate = next(
            (
                candidate
                for candidate in candidates
                if str(candidate.get("id")) == str(series_id)
            ),
            None,
        )
        if candidate is None:
            rejected.append(
                f"{name}: ID {series_id} não pertence aos candidatos exibidos."
            )
            continue
        candidate_title = str(candidate.get("titulo") or "").strip()
        if selected_title and selected_title != candidate_title:
            rejected.append(
                f"{name}: título selecionado não corresponde ao candidato."
            )
            continue

        item["Status"] = "Confirmado manualmente"
        item["ID"] = candidate["id"]
        item["Nome encontrado"] = candidate_title
        item.pop("IDs", None)
        applied.append(name)

    backup = None
    if applied:
        backup = backup_path(ids_path)
        shutil.copy2(ids_path, backup)
        temporary = ids_path.with_suffix(f"{ids_path.suffix}.tmp")
        temporary.write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(ids_path)
    return applied, rejected, backup


def score_class(score):
    if score >= 0.9:
        return "score-high"
    if score >= 0.7:
        return "score-medium"
    return "score-low"


def render_candidate(candidate, suggested=False):
    series_id = str(candidate.get("id", ""))
    title = html.escape(str(candidate.get("titulo") or "Sem título"))
    url = html.escape(str(candidate.get("url") or ""), quote=True)
    description = html.escape(str(candidate.get("descricao") or "Sem descrição."))
    score = float(candidate.get("pontuacao") or 0)
    row_class = "candidate suggested" if suggested else "candidate"
    link = (
        f"<a class='external' href='{url}' target='_blank' rel='noopener'>"
        "Abrir ficha ↗</a>"
        if url
        else "<span class='muted'>Sem link</span>"
    )
    return f"""
    <article class="{row_class}">
      <div class="candidate-head">
        <div>
          <span class="position">#{candidate.get("posicao", "-")}</span>
          <strong>{title}</strong>
          {"<span class='suggested-label'>Melhor resultado</span>" if suggested else ""}
        </div>
        <span class="score {score_class(score)}">{score:.2f}</span>
      </div>
      <div class="metadata">
        <span>{html.escape(str(candidate.get("tipo") or "Tipo desconhecido"))}</span>
        <span>{html.escape(str(candidate.get("ano") or "Ano desconhecido"))}</span>
        <span>ID {series_id}</span>
      </div>
      <p class="description">{description}</p>
      <div class="candidate-actions">
        {link}
        <button type="button" class="select-button"
          data-id="{html.escape(series_id, quote=True)}"
          data-title="{html.escape(str(candidate.get("titulo") or ""), quote=True)}">
          Selecionar este ID
        </button>
      </div>
    </article>
    """


def render_report(items):
    review_items = [
        item for item in items
        if item.get("Status") == "Revisar" and item.get("IDs")
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
        candidates = item.get("IDs", [])
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
        <details class="work" data-search="{search}">
          <summary>
            <span>
              <span class="work-title">{html.escape(str(item.get("Nome", "")))}</span>
              <span class="candidate-count">{len(candidates)} candidatos</span>
            </span>
            <span class="status" data-status>Revisar</span>
          </summary>
          <div class="work-body">
            <p class="guidance">Compare título, tipo, ano e sinopse. Abra a ficha
            externa quando precisar confirmar personagens ou capa.</p>
            <div class="candidate-grid">{candidates_html}</div>
          </div>
        </details>
        """)

    data = json.dumps(
        [{"name": item.get("Nome", "")} for item in review_items],
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
background:var(--paper); box-shadow:0 5px 18px rgba(31,41,55,.04); }}
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
.work-body {{ padding:0 20px 20px; border-top:1px solid var(--line); }}
.guidance {{ color:var(--muted); }}
.candidate-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
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
.candidate-grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main class="page">
  <header class="hero">
    <div><h1>Revisão de IDs MangaUpdates</h1>
    <div class="subtitle">Compare os candidatos antes de vinculá-los à biblioteca.</div></div>
    <div class="summary"><span class="pill"><strong>{len(review_items)}</strong> para revisar</span>
    <span class="pill"><strong>{confirmed}</strong> IDs confirmados</span>
    <span class="pill"><strong id="selectedCount">0</strong> decisões tomadas</span></div>
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
function refresh() {{
  document.querySelectorAll(".work").forEach((work) => {{
    const name = work.querySelector(".work-title").textContent;
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
}}
document.querySelectorAll(".select-button").forEach((button) => button.addEventListener("click", () => {{
  const work = button.closest(".work");
  const name = work.querySelector(".work-title").textContent;
  decisions[name] = {{ id:Number(button.dataset.id), title:button.dataset.title }};
  refresh();
}}));
document.getElementById("search").addEventListener("input", (event) => {{
  const query = event.target.value.trim().toLocaleLowerCase("pt-BR");
  document.querySelectorAll(".work").forEach((work) => {{
    work.hidden = !work.dataset.search.includes(query);
  }});
}});
document.getElementById("expandAll").addEventListener("click", () =>
  document.querySelectorAll(".work:not([hidden])").forEach((work) => work.open = true));
document.getElementById("collapseAll").addEventListener("click", () =>
  document.querySelectorAll(".work").forEach((work) => work.open = false));
document.getElementById("export").addEventListener("click", () => {{
  const payload = Object.entries(decisions).map(([Nome, choice]) => ({{
    Nome, ID:choice.id, "Nome encontrado":choice.title
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


def generate_report(ids_path=IDS_FILE, report_path=REPORT_FILE):
    items = load_items(ids_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(items), encoding="utf-8")
    review_count = sum(
        bool(item.get("Status") == "Revisar" and item.get("IDs"))
        for item in items
    )
    print(f"Relatório gerado: {report_path}")
    print(f"Obras aguardando revisão: {review_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Gera o relatório ou importa decisões de IDs."
    )
    parser.add_argument(
        "--import-decisions",
        type=Path,
        help="Importa o JSON exportado pela página de revisão.",
    )
    parser.add_argument(
        "--ids-file",
        type=Path,
        default=IDS_FILE,
        help="Arquivo buscaIds.json que será lido ou atualizado.",
    )
    args = parser.parse_args()

    if args.import_decisions:
        applied, rejected, backup = import_decisions(
            args.import_decisions,
            ids_path=args.ids_file,
        )
        print(f"Decisões aplicadas: {len(applied)}")
        for name in applied:
            print(f"- {name}")
        print(f"Decisões rejeitadas: {len(rejected)}")
        for reason in rejected:
            print(f"- {reason}")
        if backup:
            print(f"Backup criado: {backup}")
        return

    generate_report(ids_path=args.ids_file)


if __name__ == "__main__":
    main()
