#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()

def replace_once(path, old, new, label):
    file = ROOT / path
    if not file.exists():
        raise RuntimeError(f"{label}: arquivo não encontrado: {path}")
    text = file.read_text(encoding="utf-8")
    if new in text:
        print(f"[OK] {label}: ajuste já aplicado.")
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: trecho esperado encontrado {count} vez(es) em {path}. "
            "Patch interrompido para não alterar código inesperado."
        )
    file.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[OK] {label}: {path}")

def append_once(path, marker, block, label):
    file = ROOT / path
    if not file.exists():
        raise RuntimeError(f"{label}: arquivo não encontrado: {path}")
    text = file.read_text(encoding="utf-8")
    if marker in text:
        print(f"[OK] {label}: ajuste já aplicado.")
        return
    file.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")
    print(f"[OK] {label}: {path}")

replace_once(
    "web/js/pages/trackingPage.js",
    '''  let selectedMangaId = null;
  let history = [];
''',
    '''  let selectedMangaId = null;
  let history = [];
  let historyExpanded = false;
''',
    "estado do histórico",
)

replace_once(
    "web/js/pages/trackingPage.js",
    '''  function renderHistory(item) {
    const rows = history.filter(row => Number(row.manga_id) === Number(item.manga_id));
    if (!rows.length) return '<p class="tracking-empty">Nenhum lançamento recente encontrado para esta obra.</p>';
    return `
      <div class="tracking-history-list">
        ${rows.map(row => `
          <article>
            <strong>Cap. ${escapeHtml(row.chapter || "-")}</strong>
            <span>${escapeHtml(dateOnly(row.release_date))}</span>
            <em>${escapeHtml(row.status || "")}</em>
          </article>
        `).join("")}
      </div>
    `;
  }
''',
    '''  function renderHistory(item) {
    const rows = history.filter(row => Number(row.manga_id) === Number(item.manga_id));
    if (!rows.length) return '<p class="tracking-empty">Nenhum lançamento recente encontrado para esta obra.</p>';
    const visibleRows = historyExpanded ? rows : rows.slice(0, 5);
    const hiddenCount = Math.max(0, rows.length - visibleRows.length);
    return `
      <div class="tracking-history-list">
        ${visibleRows.map(row => `
          <article>
            <strong>Cap. ${escapeHtml(row.chapter || "-")}</strong>
            <span>${escapeHtml(dateOnly(row.release_date))}</span>
            <em>${escapeHtml(row.status || "")}</em>
          </article>
        `).join("")}
      </div>
      ${rows.length > 5 ? `
        <div class="tracking-history-actions">
          <button type="button" class="secondary-action tracking-history-toggle" data-tracking-history-toggle>
            ${historyExpanded ? "Ver menos" : `Ver mais (${hiddenCount})`}
          </button>
        </div>
      ` : ""}
    `;
  }
''',
    "histórico compacto",
)

replace_once(
    "web/js/pages/trackingPage.js",
    '''    selectedMangaId = Number(item.dataset.trackingWork);
    renderWorks();
    loadSelectedHistory();
''',
    '''    selectedMangaId = Number(item.dataset.trackingWork);
    historyExpanded = false;
    renderWorks();
    loadSelectedHistory();
''',
    "reset de expansão ao trocar obra",
)

replace_once(
    "web/js/pages/trackingPage.js",
    '''  elements.detail?.addEventListener("click", event => {
    const favorite = event.target.closest("[data-tracking-favorite]");
''',
    '''  elements.detail?.addEventListener("click", event => {
    const historyToggle = event.target.closest("[data-tracking-history-toggle]");
    if (historyToggle) {
      historyExpanded = !historyExpanded;
      renderDetail();
      return;
    }
    const favorite = event.target.closest("[data-tracking-favorite]");
''',
    "toggle de histórico",
)

replace_once(
    "web/js/pages/trackingPage.js",
    '''async function waitForTask(taskId) {
  if (!taskId) return;
  for (let index = 0; index < 30; index += 1) {
    const { payload } = await getTasks();
    const task = (payload.tasks || []).find(item => item.id === taskId);
    if (task && !["queued", "running"].includes(task.status)) return;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}
''',
    '''async function waitForTask(taskId) {
  if (!taskId) return null;
  const maxAttempts = 600;
  for (let index = 0; index < maxAttempts; index += 1) {
    const { response, payload } = await getTasks();
    if (!response.ok) {
      throw new Error(payload?.error || "Não foi possível acompanhar a verificação.");
    }
    const task = (payload.tasks || []).find(item => item.id === taskId);
    if (task && !["queued", "running"].includes(task.status)) {
      if (task.status === "failed") {
        throw new Error(task.error || task.error_message || "A verificação falhou.");
      }
      return task;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error("A verificação continua em andamento após 10 minutos. Atualize a página para consultar o status.");
}
''',
    "polling de task",
)

append_once(
    "web/css/pages/releases.css",
    "/* tracking follow-up: compact queue + collapsible history */",
    '''
/* tracking follow-up: compact queue + collapsible history */
.tracking-work-list {
  align-content: start;
}

.tracking-history-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.tracking-history-toggle {
  min-width: 112px;
}
''',
    "CSS da fila/histórico",
)

test_path = ROOT / "tests/test_tracking_followup_regressions.py"
test_path.parent.mkdir(parents=True, exist_ok=True)
test_path.write_text(r'''from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_tracking_task_wait_no_longer_stops_after_30_seconds():
    page = read("web/js/pages/trackingPage.js")
    wait = page.split("async function waitForTask", 1)[1].split(
        "function latestReleaseLabel", 1
    )[0]
    assert "const maxAttempts = 600" in wait
    assert "index < maxAttempts" in wait
    assert "throw new Error" in wait
    assert "index < 30" not in wait


def test_tracking_history_is_compact_and_expandable():
    page = read("web/js/pages/trackingPage.js")
    assert "let historyExpanded = false" in page
    assert "rows.slice(0, 5)" in page
    assert 'data-tracking-history-toggle' in page
    assert '"Ver menos"' in page
    assert "`Ver mais (${hiddenCount})`" in page


def test_tracking_work_queue_does_not_stretch_with_long_history():
    css = read("web/css/pages/releases.css")
    assert "/* tracking follow-up: compact queue + collapsible history */" in css
    block = css.split("/* tracking follow-up: compact queue + collapsible history */", 1)[1]
    assert ".tracking-work-list" in block
    assert "align-content: start" in block
''', encoding="utf-8")
print("[OK] teste adicionado: tests/test_tracking_followup_regressions.py")

print("\nPatch aplicado com sucesso.")
print("Arquivos alterados:")
print("  web/js/pages/trackingPage.js")
print("  web/css/pages/releases.css")
print("  tests/test_tracking_followup_regressions.py")
