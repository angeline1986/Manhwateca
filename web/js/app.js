const grid = document.getElementById("statusGrid");
const refreshButton = document.getElementById("refresh");
const diagnosticGrid = document.getElementById("diagnosticGrid");
const refreshDiagnostics = document.getElementById("refreshDiagnostics");
const actionGrid = document.getElementById("actionGrid");
const taskList = document.getElementById("taskList");
const reviewForm = document.getElementById("reviewForm");
const reviewNote = document.getElementById("reviewNote");
const reviewFeedback = document.getElementById("reviewFeedback");
const catalogSummary = document.getElementById("catalogSummary");
const catalogChanges = document.getElementById("catalogChanges");
const catalogList = document.getElementById("catalogList");
const catalogSearch = document.getElementById("catalogSearch");
const reviewSummary = document.getElementById("reviewSummary");
const idReviewList = document.getElementById("idReviewList");
const reviewSearch = document.getElementById("reviewSearch");
const applyDecisionsButton = document.getElementById("applyDecisions");
const decisionFeedback = document.getElementById("decisionFeedback");
const notionSummary = document.getElementById("notionSummary");
const notionMeta = document.getElementById("notionMeta");
const notionLists = document.getElementById("notionLists");
const refreshNotion = document.getElementById("refreshNotion");
const metadataSummary = document.getElementById("metadataSummary");
const metadataMeta = document.getElementById("metadataMeta");
const metadataUpdates = document.getElementById("metadataUpdates");
const metadataAlerts = document.getElementById("metadataAlerts");
const refreshMetadata = document.getElementById("refreshMetadata");
const editorialSummary = document.getElementById("editorialSummary");
const editorialFilters = document.getElementById("editorialFilters");
const editorialList = document.getElementById("editorialList");
const editorialSearch = document.getElementById("editorialSearch");
const editorialFeedback = document.getElementById("editorialFeedback");
const workflowSteps = document.getElementById("workflowSteps");
const workflowNotice = document.getElementById("workflowNotice");
const workflowFeedback = document.getElementById("workflowFeedback");
const startWorkflow = document.getElementById("startWorkflow");
const resumeWorkflow = document.getElementById("resumeWorkflow");
let taskTimer;
let catalog = [];
let lastCatalogTask;
let lastMangaUpdatesTask;
let lastNotionTask;
let lastMetadataTask;
let reviewItems = [];
const decisions = new Map();
let editorialWorks = [];
let editorialOptions = {};
let editorialFilter = "all";
let workflowState;
let workflowTimer;

function card(title, detail, available, label) {
  return `
    <article class="status-card">
      <h3>${title}</h3>
      <p>${detail}</p>
      <span class="state ${available ? "ok" : "warn"}">
        ${label || (available ? "Disponível" : "Requer atenção")}
      </span>
    </article>
  `;
}

async function loadStatus() {
  grid.innerHTML = '<article class="status-card loading">Consultando o ambiente...</article>';
  refreshButton.disabled = true;
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    grid.innerHTML = [
      card(
        "Catálogo local",
        `${data.catalog.count} obra(s) em ${data.catalog.path}.`,
        data.catalog.available
      ),
      card(
        "Biblioteca no Drive",
        data.library.configured
          ? "A variável MANGA_ROOT está configurada."
          : "Configure MANGA_ROOT no arquivo .env.",
        data.library.available
      ),
      card(
        "MangaUpdates",
        "Cache externo e CSV de integração.",
        data.mangaupdates.cache_available && data.mangaupdates.csv_available
      ),
      card(
        "Notion",
        "Token e banco necessários para sincronizações futuras.",
        data.notion.configured,
        data.notion.configured ? "Configurado" : "Não configurado"
      ),
    ].join("");
  } catch (error) {
    grid.innerHTML = card(
      "Falha ao consultar status",
      error.message,
      false,
      "Servidor indisponível"
    );
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadStatus);

async function loadDiagnostics() {
  refreshDiagnostics.disabled = true;
  try {
    const response = await fetch("/api/diagnostics", { cache: "no-store" });
    const data = await response.json();
    diagnosticGrid.innerHTML = data.checks.map(check => `
      <article class="diagnostic-item ${check.ok ? "ok" : "warn"}">
        <strong>${escapeHtml(check.name)}</strong>
        <span>${escapeHtml(check.detail)}</span>
      </article>
    `).join("");
  } finally {
    refreshDiagnostics.disabled = false;
  }
}

refreshDiagnostics.addEventListener("click", loadDiagnostics);

async function loadActions() {
  const response = await fetch("/api/actions");
  const actions = await response.json();
  actionGrid.innerHTML = Object.entries(actions).map(([id, action]) => `
    <button class="action-button ${action.requires_confirmation ? "destructive" : ""}"
            type="button" data-action="${id}"
            data-confirmation="${action.requires_confirmation}">
      ${action.label}
    </button>
  `).join("");
}

async function startTask(action, requiresConfirmation) {
  let confirmation = null;
  let parameters = {};
  if (requiresConfirmation) {
    confirmation = window.prompt(
      "Esta ação altera arquivos da biblioteca. Digite APLICAR para confirmar."
    );
    if (confirmation !== "APLICAR") return;
  }
  if (action === "mangaupdates_search") {
    const initials = window.prompt(
      "Letras iniciais (ex.: A, ABC ou 0-9). Deixe vazio para todas."
    );
    if (initials === null) return;
    parameters = { initials };
  }
  const response = await fetch(`/api/tasks/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmation, parameters })
  });
  const payload = await response.json();
  if (!response.ok) {
    window.alert(payload.error || "Não foi possível iniciar a tarefa.");
    return;
  }
  await loadTasks();
}

function renderTask(task) {
  const running = ["queued", "running"].includes(task.status);
  const reports = (task.reports || []).map(path => `
    <a href="/reports/${path.replace(/^reports\//, "")}" target="_blank">
      Abrir ${path.split("/").pop()}
    </a>
  `).join("");
  const messages = (task.messages || []).join("\n");
  return `
    <article class="task-item">
      <div class="task-head">
        <strong>${task.label}</strong>
        <span class="state ${task.status === "completed" ? "ok" : "warn"}">
          ${task.status}
        </span>
      </div>
      <p>${task.started_at || task.created_at}${task.finished_at ? ` → ${task.finished_at}` : ""}</p>
      ${reports ? `<div class="task-links">${reports}</div>` : ""}
      ${messages ? `<pre>${escapeHtml(messages)}</pre>` : ""}
      ${running ? "<p>Executando em segundo plano...</p>" : ""}
    </article>
  `;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[character]);
}

async function loadTasks() {
  const response = await fetch("/api/tasks", { cache: "no-store" });
  const data = await response.json();
  taskList.innerHTML = data.tasks.length
    ? data.tasks.map(renderTask).join("")
    : '<p class="empty">Nenhuma tarefa executada.</p>';
  const hasRunning = data.tasks.some(task => ["queued", "running"].includes(task.status));
  const catalogTask = data.tasks.find(task =>
    task.action === "catalog_scan" && task.status === "completed"
  );
  if (catalogTask && catalogTask.id !== lastCatalogTask) {
    lastCatalogTask = catalogTask.id;
    await loadCatalog();
  }
  const mangaUpdatesTask = data.tasks.find(task =>
    task.group === "mangaupdates" && task.status === "completed"
  );
  if (mangaUpdatesTask && mangaUpdatesTask.id !== lastMangaUpdatesTask) {
    lastMangaUpdatesTask = mangaUpdatesTask.id;
    await loadIdReview();
  }
  const notionTask = data.tasks.find(task =>
    task.group === "notion" && !["queued", "running"].includes(task.status)
  );
  if (notionTask && notionTask.id !== lastNotionTask) {
    lastNotionTask = notionTask.id;
    await loadNotionStatus();
  }
  const metadataTask = data.tasks.find(task =>
    ["notion_csv_preview", "notion_csv_apply"].includes(task.action)
    && !["queued", "running"].includes(task.status)
  );
  if (metadataTask && metadataTask.id !== lastMetadataTask) {
    lastMetadataTask = metadataTask.id;
    await loadMetadataStatus();
  }
  clearTimeout(taskTimer);
  taskTimer = setTimeout(loadTasks, hasRunning ? 1000 : 5000);
}

function summaryCard(label, value) {
  return `<article><strong>${value}</strong><span>${label}</span></article>`;
}

function renderCatalog(items) {
  catalogList.innerHTML = items.length ? items.map(manga => {
    const issues = [...(manga.count_issues || []), ...(manga.unparsed_files || [])];
    const aliases = (manga.alias || []).join(", ");
    return `
      <tr>
        <td><strong>${escapeHtml(manga.nome || "")}</strong>
          ${aliases ? `<small>${escapeHtml(aliases)}</small>` : ""}</td>
        <td>${manga.ultimo_lido}</td>
        <td>${manga.proximo_a_ler}</td>
        <td>${manga.main_caps}</td>
        <td>${escapeHtml(manga.tamanho)}</td>
        <td>${manga.chapters_found}</td>
        <td>${manga.side_stories_found}</td>
        <td><span class="state ${issues.length ? "warn" : "ok"}"
          title="${escapeHtml(issues.join(" | "))}">
          ${issues.length ? `${issues.length} alerta(s)` : "OK"}
        </span></td>
      </tr>
    `;
  }).join("") : '<tr><td colspan="8" class="empty">Nenhuma obra encontrada.</td></tr>';
}

function renderChanges(changes) {
  const total = changes.new.length + changes.updated.length + changes.removed.length;
  if (!total) {
    catalogChanges.innerHTML = "<p>Nenhuma mudança registrada na última catalogação.</p>";
    return;
  }
  catalogChanges.innerHTML = `
    <strong>Última catalogação:</strong>
    <span>${changes.new.length} nova(s)</span>
    <span>${changes.updated.length} alterada(s)</span>
    <span>${changes.removed.length} removida(s)</span>
  `;
}

function candidateCard(item, candidate) {
  const selected = decisions.get(item.nome_decisao)?.ID === candidate.id;
  return `
    <article class="candidate-card ${selected ? "selected" : ""}">
      <div><strong>${escapeHtml(candidate.titulo || "")}</strong>
        <span class="score">${Number(candidate.pontuacao || 0).toFixed(2)}</span></div>
      <small>${escapeHtml(candidate.tipo || "Tipo não informado")} ·
        ${escapeHtml(candidate.ano || "Ano não informado")} · ID ${candidate.id}</small>
      <p>${escapeHtml(candidate.descricao || "Sem descrição.")}</p>
      <div class="candidate-actions">
        ${candidate.url ? `<a href="${escapeHtml(candidate.url)}" target="_blank">Abrir ficha</a>` : ""}
        <button type="button" data-select-id="${candidate.id}"
          data-work="${escapeHtml(item.nome_decisao)}"
          data-title="${escapeHtml(candidate.titulo || "")}">Selecionar</button>
      </div>
    </article>
  `;
}

function renderReview(items) {
  idReviewList.innerHTML = items.length ? items.map(item => `
    <details class="review-work">
      <summary><strong>${escapeHtml(item.nome)}</strong>
        <span>${item.candidates.length} candidato(s)</span></summary>
      <div class="candidate-grid">
        ${item.candidates.map(candidate => candidateCard(item, candidate)).join("")
          || '<p class="empty">Nenhum candidato acima de 0,70.</p>'}
      </div>
      <div class="manual-decision">
        <label>ID manual</label>
        <input type="number" min="1" data-manual-id="${escapeHtml(item.nome_decisao)}">
        <button type="button" data-manual-work="${escapeHtml(item.nome_decisao)}">
          Usar ID
        </button>
      </div>
    </details>
  `).join("") : '<p class="empty">Nenhuma obra aguardando revisão no CSV.</p>';
}

async function loadIdReview() {
  const response = await fetch("/api/mangaupdates/review", { cache: "no-store" });
  const data = await response.json();
  reviewItems = data.items;
  reviewSummary.innerHTML = [
    summaryCard("Registros", data.summary.total),
    summaryCard("A revisar", data.summary.review),
    summaryCard("IDs confirmados", data.summary.confirmed),
    summaryCard("Ainda não pesquisados", data.summary.pending),
  ].join("");
  renderReview(reviewItems);
}

function notionList(title, items, tone = "") {
  return `
    <article class="notion-list ${tone}">
      <strong>${title}</strong>
      ${items.length
        ? `<ul>${items.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
        : '<p>Nenhuma obra.</p>'}
    </article>
  `;
}

async function loadNotionStatus() {
  refreshNotion.disabled = true;
  try {
    const response = await fetch("/api/notion/status", { cache: "no-store" });
    const data = await response.json();
    notionSummary.innerHTML = [
      summaryCard("Catálogo", data.summary.catalog),
      summaryCard("Importadas", data.summary.imported),
      summaryCard("No último lote", data.summary.current_batch),
      summaryCard("Pendentes", data.summary.pending),
      summaryCard("Duplicadas", data.summary.duplicates),
    ].join("");
    notionMeta.innerHTML = data.available
      ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
         <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>`
      : `<span>${escapeHtml(data.error || "Execute uma simulação para gerar o status.")}</span>`;
    notionLists.innerHTML = [
      notionList("Último lote", data.current_batch),
      notionList("Pendentes", data.pending, "warning"),
      notionList("Duplicadas", data.duplicates, "danger"),
    ].join("");
  } finally {
    refreshNotion.disabled = false;
  }
}

refreshNotion.addEventListener("click", loadNotionStatus);

function renderMetadataUpdates(updates) {
  metadataUpdates.innerHTML = updates.length ? `
    <h3>Páginas atualizáveis</h3>
    <div class="metadata-table-wrap">
      <table class="catalog-table">
        <thead><tr><th>Obra</th><th>Propriedades</th></tr></thead>
        <tbody>${updates.map(item => `
          <tr><td><strong>${escapeHtml(item.name)}</strong></td>
          <td class="property-tags">${item.properties.map(property =>
            `<span>${escapeHtml(property)}</span>`).join("")}</td></tr>
        `).join("")}</tbody>
      </table>
    </div>
  ` : '<p class="empty">Execute a simulação para listar as atualizações.</p>';
}

async function loadMetadataStatus() {
  refreshMetadata.disabled = true;
  try {
    const response = await fetch("/api/notion/metadata", { cache: "no-store" });
    const data = await response.json();
    metadataSummary.innerHTML = [
      summaryCard("Atualizações", data.summary.updates),
      summaryCard("Ausentes", data.summary.missing),
      summaryCard("Duplicadas", data.summary.duplicates),
      summaryCard("CSV disponível", data.csv_available ? "Sim" : "Não"),
    ].join("");
    metadataMeta.innerHTML = data.available
      ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
         <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>`
      : `<span>${escapeHtml(data.error || "Execute a simulação dos metadados.")}</span>`;
    renderMetadataUpdates(data.updates);
    metadataAlerts.innerHTML = [
      notionList("Ausentes no Notion", data.missing, "warning"),
      notionList("Duplicadas", data.duplicates, "danger"),
    ].join("");
  } finally {
    refreshMetadata.disabled = false;
  }
}

refreshMetadata.addEventListener("click", loadMetadataStatus);

function optionTags(values, selected) {
  return values.map(value =>
    `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>
      ${escapeHtml(value || "Não informado")}</option>`
  ).join("");
}

function editorialCard(work) {
  return `
    <details class="editorial-work">
      <summary>
        <span><strong>${escapeHtml(work.Nome)}</strong>
          <small>${escapeHtml(work.Alias || "Sem alias")}</small></span>
        <span>${escapeHtml(work.Status)} · ${escapeHtml(work.Tamanho)}</span>
      </summary>
      <form class="editorial-form" data-work="${escapeHtml(work.Nome)}">
        <label>Status<select name="Status">
          ${optionTags(editorialOptions.Status, work.Status)}</select></label>
        <label>Nota<select name="Nota">
          ${optionTags(editorialOptions.Nota, work.Nota)}</select></label>
        <label>Interesse<input name="Interesse" value="${escapeHtml(work.Interesse)}"></label>
        <label>Picância<select name="Picância">
          ${optionTags(editorialOptions.Picância, work.Picância)}</select></label>
        <label>Último lido<input name="Último lido" type="number" min="0"
          value="${escapeHtml(work["Último lido"])}"></label>
        <label>Alias<input name="Alias" value="${escapeHtml(work.Alias)}"></label>
        <label class="wide">Temática<input name="Temática"
          value="${escapeHtml(work.Temática)}" placeholder="Drama | Romance"></label>
        <label class="wide">Universo<input name="Universo"
          value="${escapeHtml(work.Universo)}" placeholder="Omegaverse | Fantasia"></label>
        <div class="editorial-context">
          Disponível: ${escapeHtml(work["Último capítulo disponível"])}
          · Encontrados: ${escapeHtml(work["Capítulos encontrados"])}
          · ID: ${escapeHtml(work["ID da obra"] || "pendente")}
        </div>
        <button type="submit">Salvar dados locais</button>
      </form>
    </details>
  `;
}

function matchesEditorialFilter(work) {
  const last = Number(work["Último lido"] || 0);
  const available = Number(work["Último capítulo disponível"] || 0);
  const rules = {
    all: true,
    reading: work.Status === "Lendo",
    "without-id": !work["ID da obra"],
    incomplete: !work.Interesse || !work.Picância,
    "new-chapters": available > last,
    audit: work["Status da contagem"] !== "OK",
  };
  return rules[editorialFilter];
}

function renderEditorial() {
  const query = editorialSearch.value.toLocaleLowerCase("pt-BR").trim();
  const filtered = editorialWorks.filter(work =>
    matchesEditorialFilter(work)
    && [work.Nome, work.Alias].some(value =>
      String(value).toLocaleLowerCase("pt-BR").includes(query))
  );
  editorialList.innerHTML = filtered.length
    ? filtered.map(editorialCard).join("")
    : '<p class="empty">Nenhuma obra corresponde ao filtro.</p>';
}

async function loadEditorial() {
  const response = await fetch("/api/editorial", { cache: "no-store" });
  const data = await response.json();
  editorialWorks = data.works;
  editorialOptions = data.options;
  editorialSummary.innerHTML = [
    summaryCard("Obras", data.summary.total),
    summaryCard("Em leitura", data.summary.reading),
    summaryCard("Sem ID", data.summary.without_id),
    summaryCard("Metadados incompletos", data.summary.incomplete),
    summaryCard("Com capítulos disponíveis", data.summary.new_chapters),
    summaryCard("Em auditoria", data.summary.audit),
  ].join("");
  renderEditorial();
}

editorialFilters.addEventListener("click", event => {
  const button = event.target.closest("[data-editorial-filter]");
  if (!button) return;
  editorialFilter = button.dataset.editorialFilter;
  editorialFilters.querySelectorAll("button").forEach(item =>
    item.classList.toggle("active", item === button)
  );
  renderEditorial();
});

editorialSearch.addEventListener("input", renderEditorial);

editorialList.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.target;
  const changes = Object.fromEntries(new FormData(form).entries());
  const response = await fetch("/api/editorial", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: form.dataset.work, changes })
  });
  const payload = await response.json();
  editorialFeedback.textContent = response.ok
    ? `${form.dataset.work}: dados salvos localmente.`
    : (payload.error || "Não foi possível salvar.");
  if (response.ok) await Promise.all([loadEditorial(), loadCatalog()]);
});

function workflowStep(step, run) {
  const result = run.results?.[step.id];
  const status = result?.status || "pending";
  const checked = run.selected?.includes(step.id) ?? true;
  return `
    <article class="workflow-step ${status}">
      <label>
        <input type="checkbox" value="${step.id}" ${checked ? "checked" : ""}
          ${run.status === "running" ? "disabled" : ""}>
        <span><strong>${escapeHtml(step.label)}</strong>
          ${step.manual ? "<small>Etapa manual</small>" : ""}</span>
      </label>
      <span class="workflow-status">${escapeHtml(status)}</span>
      ${result?.note ? `<p>${escapeHtml(result.note)}</p>` : ""}
      ${result?.messages?.length
        ? `<details><summary>Mensagens</summary><pre>${escapeHtml(result.messages.join("\n"))}</pre></details>`
        : ""}
      ${status === "manual"
        ? `<button type="button" data-complete-manual="${step.id}">
             Concluí esta etapa e quero continuar
           </button>`
        : ""}
    </article>
  `;
}

function renderWorkflow(data) {
  workflowState = data;
  workflowSteps.innerHTML = data.steps.map(step =>
    workflowStep(step, data.run)
  ).join("");
  workflowNotice.textContent = data.run.notification || (
    data.run.status === "completed"
      ? "Fluxo concluído."
      : `Situação: ${data.run.status || "idle"}`
  );
  startWorkflow.disabled = data.run.status === "running";
  resumeWorkflow.hidden = !["failed", "interrupted"].includes(data.run.status);
}

async function loadWorkflow() {
  const response = await fetch("/api/workflow", { cache: "no-store" });
  const data = await response.json();
  renderWorkflow(data);
  clearTimeout(workflowTimer);
  workflowTimer = setTimeout(
    loadWorkflow, data.run.status === "running" ? 1000 : 5000
  );
}

async function runWorkflow(resume = false) {
  const selected = [...workflowSteps.querySelectorAll(
    'input[type="checkbox"]:checked'
  )].map(input => input.value);
  const response = await fetch("/api/workflow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected, resume })
  });
  const payload = await response.json();
  workflowFeedback.textContent = response.ok
    ? "Fluxo iniciado."
    : (payload.error || "Não foi possível iniciar.");
  if (response.ok) renderWorkflow(payload);
}

startWorkflow.addEventListener("click", () => runWorkflow(false));
resumeWorkflow.addEventListener("click", () => runWorkflow(true));
workflowSteps.addEventListener("click", async event => {
  const button = event.target.closest("[data-complete-manual]");
  if (!button) return;
  const response = await fetch("/api/workflow/continue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step: button.dataset.completeManual })
  });
  const payload = await response.json();
  workflowFeedback.textContent = response.ok
    ? "Etapa confirmada. Fluxo retomado."
    : (payload.error || "Não foi possível retomar.");
  if (response.ok) renderWorkflow(payload);
});

idReviewList.addEventListener("click", event => {
  const selected = event.target.closest("[data-select-id]");
  const manual = event.target.closest("[data-manual-work]");
  if (selected) {
    decisions.set(selected.dataset.work, {
      Nome: selected.dataset.work,
      ID: Number(selected.dataset.selectId),
      "Nome encontrado": selected.dataset.title,
      Origem: "Candidato selecionado",
    });
    renderReview(reviewItems);
  }
  if (manual) {
    const input = idReviewList.querySelector(
      `[data-manual-id="${CSS.escape(manual.dataset.manualWork)}"]`
    );
    if (!input.value) return;
    decisions.set(manual.dataset.manualWork, {
      Nome: manual.dataset.manualWork,
      ID: Number(input.value),
      "Nome encontrado": `ID ${input.value}`,
      Origem: "ID informado manualmente",
    });
    decisionFeedback.textContent = "ID manual incluído nas decisões.";
  }
});

reviewSearch.addEventListener("input", () => {
  const query = reviewSearch.value.toLocaleLowerCase("pt-BR").trim();
  renderReview(reviewItems.filter(item =>
    item.nome.toLocaleLowerCase("pt-BR").includes(query)
  ));
});

applyDecisionsButton.addEventListener("click", async () => {
  if (!decisions.size) {
    decisionFeedback.textContent = "Selecione ao menos uma decisão.";
    return;
  }
  const response = await fetch("/api/mangaupdates/decisions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decisions: [...decisions.values()] })
  });
  const payload = await response.json();
  decisionFeedback.textContent = response.ok
    ? `${payload.applied.length} decisão(ões) aplicada(s).`
    : (payload.rejected || [payload.error]).join(" ");
  if (response.ok) {
    decisions.clear();
    await loadIdReview();
  }
});

async function loadCatalog() {
  const response = await fetch("/api/catalog", { cache: "no-store" });
  const data = await response.json();
  catalog = data.mangas;
  catalogSummary.innerHTML = [
    summaryCard("Obras", data.summary.total),
    summaryCard("Último cap. disponível", data.summary.main_caps),
    summaryCard("Side stories", data.summary.side_stories),
    summaryCard("Precisam de revisão", data.summary.review),
    summaryCard("Arquivos não lidos", data.summary.unparsed),
  ].join("");
  renderChanges(data.changes);
  renderCatalog(catalog);
}

catalogSearch.addEventListener("input", () => {
  const query = catalogSearch.value.toLocaleLowerCase("pt-BR").trim();
  renderCatalog(catalog.filter(manga =>
    [manga.nome, ...(manga.alias || [])]
      .some(value => String(value).toLocaleLowerCase("pt-BR").includes(query))
  ));
});

actionGrid.addEventListener("click", event => {
  const button = event.target.closest("[data-action]");
  if (button) {
    startTask(button.dataset.action, button.dataset.confirmation === "true");
  }
});

reviewForm.addEventListener("submit", async event => {
  event.preventDefault();
  const note = reviewNote.value.trim();
  if (!note) return;
  const response = await fetch("/api/review-notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note })
  });
  const payload = await response.json();
  reviewFeedback.textContent = response.ok
    ? "Observação registrada."
    : (payload.error || "Não foi possível salvar.");
  if (response.ok) reviewNote.value = "";
});

Promise.all([
  loadStatus(), loadDiagnostics(), loadActions(), loadCatalog(),
  loadIdReview(), loadTasks()
  , loadNotionStatus(), loadMetadataStatus(), loadEditorial(), loadWorkflow()
]);
