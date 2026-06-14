import html

from manhwateca.file_normalizer.grouping import GROUPS
from manhwateca.reporting.files import write_report


def generate_report(plan, conflicts, duplicates, report_path, dry_run):
    changes = _flatten_changes(plan, conflicts)
    work_count = len({item["work"] for item in changes})
    cover_count = sum(item["kind"] == "cover" for item in changes)
    conflict_count = sum(item["conflict"] for item in changes)

    document = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manhwateca - Padronização de Arquivos</title>
<style>{_styles()}</style>
</head>
<body>
<header class="hero">
  <div>
    <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
    <h1>Padronização de arquivos</h1>
    <p>{len(changes)} nomes serão ajustados em {work_count} obras.</p>
  </div>
  <span class="mode">Simulação: {"ON" if dry_run else "OFF"}</span>
</header>
<main>
  <section class="summary">
    {_metric("Arquivos a renomear", len(changes))}
    {_metric("Obras afetadas", work_count)}
    {_metric("Capas", cover_count)}
    {_metric("Conflitos", len(conflicts))}
    {_metric("Duplicados", len(duplicates))}
  </section>
  <section class="panel">
    <div class="panel-head">
      <div>
        <span class="eyebrow">REVISÃO NECESSÁRIA</span>
        <h2>O que será renomeado</h2>
        <p>Compare os nomes antes e depois. Esta prévia não altera arquivos.</p>
      </div>
      <input id="search" type="search" placeholder="Buscar obra ou arquivo">
    </div>
    <nav class="filters" aria-label="Filtros">
      <button class="active" data-filter="all">Todas ({len(changes)})</button>
      <button data-filter="chapter">Capítulos ({len(changes) - cover_count})</button>
      <button data-filter="cover">Capas ({cover_count})</button>
      <button data-filter="conflict">Conflitos ({conflict_count})</button>
    </nav>
    <div class="works" id="works">
      {_work_sections(changes)}
    </div>
    <p class="empty-filter" id="emptyFilter" hidden>Nenhuma alteração corresponde ao filtro.</p>
  </section>
  {_warning_section(conflicts, duplicates)}
</main>
<script>{_script()}</script>
</body>
</html>"""
    write_report(report_path, document)


def _flatten_changes(plan, conflicts):
    conflict_keys = {
        (conflict["manga"], conflict["conflict_name"])
        for conflict in conflicts
    }
    changes = []
    for group in GROUPS:
        for work, files in plan.get(group, {}).items():
            for item in files:
                changes.append({
                    "group": group,
                    "work": work,
                    "old": item["old_name"],
                    "new": item["new_name"],
                    "kind": item.get("kind", "chapter"),
                    "conflict": (work, item["new_name"]) in conflict_keys,
                })
    return sorted(
        changes,
        key=lambda item: (
            list(GROUPS).index(item["group"]),
            item["work"].casefold(),
            item["old"].casefold(),
        ),
    )


def _metric(label, value):
    return (
        f'<article class="metric"><strong>{value}</strong>'
        f"<span>{label}</span></article>"
    )


def _work_sections(changes):
    if not changes:
        return '<p class="empty-filter">Nenhum arquivo precisa ser renomeado.</p>'
    grouped = {}
    for item in changes:
        grouped.setdefault((item["group"], item["work"]), []).append(item)
    sections = []
    for (group, work), items in grouped.items():
        search = " ".join(
            [work, group]
            + [item["old"] for item in items]
            + [item["new"] for item in items]
        ).casefold()
        kinds = " ".join(sorted({item["kind"] for item in items}))
        if any(item["conflict"] for item in items):
            kinds += " conflict"
        rows = "".join(_change_row(item) for item in items)
        sections.append(
            f"""<details class="work" data-search="{html.escape(search, quote=True)}"
 data-kinds="{html.escape(kinds, quote=True)}">
<summary>
  <span><small>{html.escape(group)}</small><strong>{html.escape(work)}</strong></span>
  <span class="count">{len(items)} alteração{"ões" if len(items) != 1 else ""}</span>
</summary>
<div class="table-wrap"><table>
<thead><tr><th>Antes</th><th>Depois</th><th>Tipo</th><th>Situação</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</details>"""
        )
    return "".join(sections)


def _change_row(item):
    kind_label = "Capa" if item["kind"] == "cover" else "Capítulo"
    status = "Conflito" if item["conflict"] else "Será renomeado"
    status_class = "conflict" if item["conflict"] else "change"
    search = f'{item["work"]} {item["old"]} {item["new"]}'.casefold()
    return f"""<tr data-kind="{item["kind"]}" data-conflict="{str(item["conflict"]).lower()}"
 data-search="{html.escape(search, quote=True)}">
<td class="old">{html.escape(item["old"])}</td>
<td class="new">{html.escape(item["new"])}</td>
<td>{kind_label}</td>
<td><span class="status {status_class}">{status}</span></td>
</tr>"""


def _warning_section(conflicts, duplicates):
    if not (conflicts or duplicates):
        return ""
    messages = []
    if conflicts:
        messages.append(
            f"<li><strong>{len(conflicts)} conflito(s):</strong> "
            "a aplicação fica bloqueada até a correção.</li>"
        )
    if duplicates:
        messages.append(
            f"<li><strong>{len(duplicates)} possível(is) duplicado(s):</strong> "
            "confirme se são obras diferentes.</li>"
        )
    return (
        '<section class="panel warnings"><span class="eyebrow">ATENÇÃO</span>'
        "<h2>Itens que exigem revisão</h2>"
        f"<ul>{''.join(messages)}</ul></section>"
    )


def _styles():
    return """
:root{--rose:#a94d6b;--border:#eadde1;--text:#3f3438;--muted:#75686d;--bg:#faf8f9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.hero,main{width:min(1180px,calc(100% - 36px));margin:auto}.hero{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:38px 0 24px}
h1,h2,p{margin-top:0}h1{margin-bottom:4px;font-size:34px}h2{margin-bottom:6px}.eyebrow{color:var(--rose);font-size:11px;font-weight:900;letter-spacing:.16em}
.hero p,.panel-head p{margin-bottom:0;color:var(--muted)}.mode{padding:8px 13px;border-radius:999px;background:#f4e4e4;color:var(--rose);font-weight:800;white-space:nowrap}
.summary{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:18px}.metric{padding:18px;border:1px solid var(--border);border-radius:15px;background:#fff}
.metric strong,.metric span{display:block}.metric strong{font-size:28px;color:var(--rose)}.metric span{color:var(--muted);font-weight:700}
.panel{margin-bottom:18px;padding:26px;border:1px solid var(--border);border-radius:18px;background:#fff;box-shadow:0 14px 40px rgba(90,55,68,.06)}
.panel-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-end}.panel-head input{width:min(340px,100%);padding:11px 13px;border:1px solid #d9c9cf;border-radius:10px;font:inherit}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0 14px}.filters button{padding:8px 12px;border:1px solid var(--border);border-radius:999px;background:#fff;color:var(--muted);font-weight:800;cursor:pointer}
.filters button.active{border-color:var(--rose);background:var(--rose);color:#fff}.works{display:grid;gap:10px}.work{border:1px solid var(--border);border-radius:13px;overflow:hidden}
.work>summary{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:15px 17px;cursor:pointer;list-style:none}.work>summary::-webkit-details-marker{display:none}
.work>summary span:first-child{display:flex;align-items:center;gap:12px}.work>summary small{min-width:34px;color:var(--rose);font-size:11px;font-weight:900}.work>summary strong{font-size:16px}.count{color:var(--muted);font-size:13px;font-weight:800}
.table-wrap{overflow:auto;border-top:1px solid var(--border)}table{width:100%;border-collapse:collapse}th,td{padding:12px 15px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{background:#f8f3f5;color:var(--muted);font-size:11px;letter-spacing:.08em;text-transform:uppercase}tbody tr:last-child td{border-bottom:0}.old{color:#a13e3e}.new{color:#397246;font-weight:800}
.status{display:inline-block;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:900;white-space:nowrap}.status.change{color:#8d4960;background:#f4e4e4}.status.conflict{color:#a03232;background:#fde8e8}
.empty-filter{padding:24px;text-align:center;color:var(--muted)}.warnings{border-color:#edc98c;background:#fffbf2}.warnings ul{margin-bottom:0;padding-left:22px}
@media(max-width:800px){.hero,.panel-head{align-items:flex-start;flex-direction:column}.summary{grid-template-columns:1fr 1fr}.panel-head input{width:100%}}
"""


def _script():
    return """
const works=[...document.querySelectorAll('.work')];
const buttons=[...document.querySelectorAll('[data-filter]')];
const search=document.getElementById('search');
const empty=document.getElementById('emptyFilter');
let filter='all';
function applyFilters(){
  const query=search.value.toLocaleLowerCase('pt-BR').trim();
  let visible=0;
  works.forEach(work=>{
    let rows=0;
    work.querySelectorAll('tbody tr').forEach(row=>{
      const kindMatch=filter==='all'||row.dataset.kind===filter||
        (filter==='conflict'&&row.dataset.conflict==='true');
      const searchMatch=!query||row.dataset.search.includes(query)||
        work.dataset.search.includes(query);
      row.hidden=!(kindMatch&&searchMatch);
      if(!row.hidden)rows++;
    });
    work.hidden=rows===0;
    if(!work.hidden)visible++;
  });
  empty.hidden=visible!==0;
}
buttons.forEach(button=>button.addEventListener('click',()=>{
  filter=button.dataset.filter;
  buttons.forEach(item=>item.classList.toggle('active',item===button));
  applyFilters();
}));
search.addEventListener('input',applyFilters);
applyFilters();
"""
