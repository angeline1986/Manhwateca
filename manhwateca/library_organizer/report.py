import html
import unicodedata
from pathlib import Path

from manhwateca.library_organizer.grouping import GROUPS
from manhwateca.library_organizer.planning import determine_status
from manhwateca.reporting.files import write_report


def generate_report(
    plan,
    conflicts,
    duplicates,
    empty_legacy_folders,
    report_path,
    dry_run,
):
    correct = [item for item in plan if item["is_correct"]]
    pending = [item for item in plan if not item["is_correct"]]
    conflict_names = {
        item["name"]
        for conflict in conflicts
        for item in conflict.get("items", [])
    }
    duplicate_names = {
        entry["original"]
        for duplicate in duplicates
        for entry in duplicate.get("entries", [])
    }
    rows = [
        _pending_row(
            item,
            determine_status(item, conflicts, duplicates),
            _library_root(plan),
        )
        for item in sorted(pending, key=lambda entry: entry["name"].casefold())
    ]
    correct_groups = _correct_groups(correct)
    document = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manhwateca - Organização de Pastas</title>
<style>{_styles()}</style>
</head>
<body>
<header class="hero">
  <div>
    <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
    <h1>Organização de pastas</h1>
    <p>{len(plan)} obras detectadas · {len(correct)} já estão corretas.</p>
  </div>
  <span class="mode">Simulação: {"ON" if dry_run else "OFF"}</span>
</header>
<main>
  <section class="summary">
    {_metric("Pastas a mover", len(pending), "move")}
    {_metric("Conflitos", len(conflicts), "conflict")}
    {_metric("Duplicados", len(duplicates), "duplicate")}
  </section>
  <section class="panel">
    <div class="panel-head">
      <div>
        <span class="eyebrow">REVISÃO NECESSÁRIA</span>
        <h2>O que será alterado</h2>
        <p>Revise origem e destino antes de aplicar a organização.</p>
      </div>
      <input id="search" type="search" placeholder="Buscar obra ou caminho">
    </div>
    <nav class="filters" aria-label="Filtros">
      <button class="active" data-filter="move">A mover ({len(pending)})</button>
      <button data-filter="conflict">Conflitos ({len(conflict_names)})</button>
      <button data-filter="duplicate">Duplicados ({len(duplicate_names)})</button>
      <button data-filter="all">Todas as pendências</button>
    </nav>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Obra</th><th>Pasta atual</th><th>Destino</th><th>Motivo</th><th>Situação</th></tr></thead>
        <tbody id="pendingRows">
          {''.join(rows) if rows else '<tr class="empty-row"><td colspan="5">Nenhuma pasta precisa ser movida.</td></tr>'}
        </tbody>
      </table>
    </div>
    <p class="empty-filter" id="emptyFilter" hidden>Nenhum item corresponde ao filtro.</p>
  </section>
  {_warning_section(conflicts, duplicates, empty_legacy_folders)}
  <details class="panel correct-panel">
    <summary>
      <div><span class="eyebrow">INVENTÁRIO</span><h2>Obras já organizadas</h2></div>
      <span>{len(correct)} obras</span>
    </summary>
    <div class="correct-groups">{correct_groups}</div>
  </details>
</main>
<script>{_script()}</script>
</body>
</html>"""
    write_report(report_path, document)


def _metric(label, value, tone):
    return (
        f'<article class="metric {tone}"><strong>{value}</strong>'
        f"<span>{label}</span></article>"
    )


def _library_root(plan):
    if not plan:
        return None
    destination = plan[0]["destination"]
    return destination.parents[1]


def _display_path(path, root):
    if root is None:
        return str(path)
    try:
        relative = path.relative_to(root)
    except ValueError:
        return str(path)
    return str(Path(root.name) / relative)


def _formatted_path(path, root):
    display_path = Path(_display_path(path, root))
    parent = str(display_path.parent)
    prefix = f"{html.escape(parent)}/" if parent != "." else ""
    folder = html.escape(display_path.name)
    return f'{prefix}<strong class="work-folder">{folder}</strong>'


def _pending_row(item, status, root):
    current = item.get("current_group") or item["source"].parent.name
    target = item["group"]
    reason = _change_reason(item, current, target)
    kind = {
        "Conflito": "conflict",
        "Duplicado suspeito": "duplicate",
    }.get(status, "move")
    search = " ".join((
        item["name"],
        _display_path(item["source"], root),
        _display_path(item["destination"], root),
        status,
    )).casefold()
    return f"""<tr data-kind="{kind}" data-search="{html.escape(search, quote=True)}">
<td><strong>{html.escape(item["name"])}</strong></td>
<td><span class="group">{html.escape(current)}</span><small>{_formatted_path(item["source"], root)}</small></td>
<td><span class="group">{html.escape(target)}</span><small>{_formatted_path(item["destination"], root)}</small></td>
<td>{html.escape(reason)}</td>
<td><span class="status {kind}">{html.escape(status)}</span></td>
</tr>"""


def _change_reason(item, current, target):
    if current != target:
        return f"Mover do grupo {current} para {target}"
    source_name = item["source"].name
    destination_name = item["destination"].name
    if source_name.casefold() == destination_name.casefold():
        return "Ajustar maiúsculas e minúsculas"
    if unicodedata.normalize("NFC", source_name) == unicodedata.normalize(
        "NFC",
        destination_name,
    ):
        return "Normalizar acentuação Unicode"
    return "Padronizar nome ou localização"


def _correct_groups(items):
    groups = {}
    for item in items:
        groups.setdefault(item["group"], []).append(item["name"])
    if not groups:
        return "<p>Nenhuma obra já organizada.</p>"
    return "".join(
        f"""<details>
<summary><strong>{html.escape(group)}</strong><span>{len(names)} obras</span></summary>
<ul>{''.join(f'<li>{html.escape(name)}</li>' for name in sorted(names, key=str.casefold))}</ul>
</details>"""
        for group in GROUPS
        if (names := groups.get(group))
    )


def _warning_section(conflicts, duplicates, empty_folders):
    if not (conflicts or duplicates or empty_folders):
        return ""
    items = []
    if conflicts:
        items.append(f"<li><strong>{len(conflicts)} conflito(s):</strong> a aplicação será bloqueada até a revisão.</li>")
    if duplicates:
        items.append(f"<li><strong>{len(duplicates)} duplicidade(s):</strong> confirme se são obras diferentes.</li>")
    if empty_folders:
        paths = ", ".join(html.escape(str(path)) for path in empty_folders)
        items.append(f"<li><strong>Pastas vazias:</strong> {paths}</li>")
    return f"""<section class="panel warnings"><span class="eyebrow">ATENÇÃO</span>
<h2>Itens que impedem ou exigem revisão</h2><ul>{''.join(items)}</ul></section>"""


def _styles():
    return """
:root{--rose:#a94d6b;--rose-soft:#fff5f7;--border:#eadde1;--text:#3f3438;--muted:#75686d;--bg:#faf8f9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.hero,main{width:min(1180px,calc(100% - 36px));margin:auto}.hero{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:38px 0 24px}
h1,h2,p{margin-top:0}h1{margin-bottom:4px;font-size:34px}h2{margin-bottom:6px}.eyebrow{color:var(--rose);font-size:11px;font-weight:900;letter-spacing:.16em}
.hero p,.panel-head p{margin-bottom:0;color:var(--muted)}.mode{padding:8px 13px;border-radius:999px;background:#f4e4e4;color:var(--rose);font-weight:800;white-space:nowrap}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px}.metric{padding:20px;border:1px solid var(--border);border-radius:16px;background:#fff}
.metric strong,.metric span{display:block}.metric strong{font-size:30px;color:var(--rose)}.metric span{color:var(--muted);font-weight:700}
.panel{margin-bottom:18px;padding:26px;border:1px solid var(--border);border-radius:18px;background:#fff;box-shadow:0 14px 40px rgba(90,55,68,.06)}
.panel-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-end}.panel-head input{width:min(340px,100%);padding:11px 13px;border:1px solid #d9c9cf;border-radius:10px;font:inherit}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0 14px}.filters button{padding:8px 12px;border:1px solid var(--border);border-radius:999px;background:#fff;color:var(--muted);font-weight:800;cursor:pointer}
.filters button.active{border-color:var(--rose);background:var(--rose);color:#fff}.table-wrap{overflow:auto;border:1px solid var(--border);border-radius:13px}
table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}th{background:#f8f3f5;color:var(--muted);font-size:11px;letter-spacing:.08em;text-transform:uppercase}
tbody tr:last-child td{border-bottom:0}td small{display:block;max-width:330px;margin-top:4px;color:var(--muted);word-break:break-word}.work-folder{color:var(--text);font-weight:900}.group{font-weight:800}.status{display:inline-block;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:900;white-space:nowrap}
.status.move{color:#8d4960;background:#f4e4e4}.status.conflict{color:#a03232;background:#fde8e8}.status.duplicate{color:#976414;background:#fff0d5}
.empty-row td,.empty-filter{padding:25px;text-align:center;color:var(--muted)}.correct-panel>summary{display:flex;justify-content:space-between;align-items:center;cursor:pointer;list-style:none}.correct-panel>summary::-webkit-details-marker{display:none}
.correct-panel>summary>span{color:var(--muted);font-weight:800}.correct-groups{display:grid;gap:8px;margin-top:20px}.correct-groups details{border:1px solid var(--border);border-radius:11px}
.correct-groups summary{display:flex;justify-content:space-between;padding:12px 14px;cursor:pointer}.correct-groups summary span{color:var(--muted);font-size:13px}.correct-groups ul{columns:3;margin:0;padding:4px 34px 16px}.correct-groups li{margin:5px 0}
.warnings{border-color:#edc98c;background:#fffbf2}.warnings ul{margin-bottom:0;padding-left:22px}
@media(max-width:800px){.hero,.panel-head{align-items:flex-start;flex-direction:column}.summary{grid-template-columns:1fr}.panel-head input{width:100%}.correct-groups ul{columns:1}}
"""


def _script():
    return """
const rows=[...document.querySelectorAll('#pendingRows tr[data-kind]')];
const buttons=[...document.querySelectorAll('[data-filter]')];
const search=document.getElementById('search');
const empty=document.getElementById('emptyFilter');
let filter='move';
function applyFilters(){
  const query=search.value.toLocaleLowerCase('pt-BR').trim();
  let visible=0;
  rows.forEach(row=>{
    const kindMatch=filter==='all'||row.dataset.kind===filter;
    const searchMatch=row.dataset.search.includes(query);
    row.hidden=!(kindMatch&&searchMatch);
    if(!row.hidden)visible++;
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
