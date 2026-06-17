const grid = document.getElementById("statusGrid");
const refreshButton = document.getElementById("refresh");
const pendingList = document.getElementById("pendingList");
const diagnosticGrid = document.getElementById("diagnosticGrid");
const refreshDiagnostics = document.getElementById("refreshDiagnostics");
const actionGrid = document.getElementById("actionGrid");
const mangaActionGrid = document.getElementById("mangaActionGrid");
const notionActionGrid = document.getElementById("notionActionGrid");
const supportActionGrid = document.getElementById("supportActionGrid");
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
const apiSearchForm = document.getElementById("apiSearchForm");
const apiSearchQuery = document.getElementById("apiSearchQuery");
const apiSearchFeedback = document.getElementById("apiSearchFeedback");
const apiSearchResults = document.getElementById("apiSearchResults");
const notionSummary = document.getElementById("notionSummary");
const notionMeta = document.getElementById("notionMeta");
const notionLists = document.getElementById("notionLists");
const notionSyncStatus = document.getElementById("notionSyncStatus");
const notionCatalogPanel = document.getElementById("notionCatalogPanel");
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
const taskToast = document.getElementById("taskToast");
const viewTaskProgress = document.getElementById("viewTaskProgress");
const taskProgress = document.getElementById("taskProgress");
const taskResultLink = document.getElementById("taskResultLink");
const confirmationDialog = document.getElementById("confirmationDialog");
const confirmationTitle = document.getElementById("confirmationTitle");
const confirmationText = document.getElementById("confirmationText");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
let taskTimer;
let notionUncataloged = 0;
let notionStatusStale = false;
let catalog = [];
let lastCatalogTask;
let lastMangaUpdatesTask;
let lastNotionTask;
let lastMetadataTask;
let reviewItems = [];
let apiSearchItems = [];
const decisions = new Map();
let editorialWorks = [];
let editorialOptions = {};
let editorialFilter = "all";
let workflowState;
let workflowTimer;

const pageMeta = {
  overview: {
    eyebrow: "MANHWATECA WORKSPACE",
    title: "Organize os arquivos e mantenha o Notion atualizado.",
    subtitle: "Esta tela mostra se o catálogo local, a biblioteca no Drive, os dados do MangaUpdates e a conexão com o Notion estão disponíveis para executar as próximas etapas.",
  },
  library: {
    eyebrow: "ACERVO E CURADORIA",
    title: "Biblioteca",
    subtitle: "Consulte capítulos, leitura e dados editoriais.",
  },
  organization: {
    eyebrow: "ARQUIVOS LOCAIS",
    title: "Organização",
    subtitle: "Revise e aplique padrões com segurança.",
  },
  mangaupdates: {
    eyebrow: "ENRIQUECIMENTO",
    title: "MangaUpdates",
    subtitle: "Localize IDs e valide correspondências.",
  },
  notion: {
    eyebrow: "INTEGRAÇÃO",
    title: "Notion",
    subtitle: "Simule lotes e atualize metadados.",
  },
  automation: {
    eyebrow: "PROCESSAMENTO",
    title: "Automação",
    subtitle: "Execute o fluxo completo e acompanhe tarefas.",
  },
  settings: {
    eyebrow: "AMBIENTE",
    title: "Configurações",
    subtitle: "Verifique requisitos e suporte técnico.",
  },
};

function showPage(pageName, updateHash = true) {
  const page = pageMeta[pageName] ? pageName : "overview";
  document.getElementById("topbar").classList.toggle("overview", page === "overview");
  document.getElementById("refresh").hidden = page !== "overview";
  document.querySelectorAll(".page").forEach(section =>
    section.classList.toggle("active", section.id === `page-${page}`)
  );
  document.querySelectorAll("[data-page]").forEach(button =>
    button.classList.toggle("active", button.dataset.page === page)
  );
  document.getElementById("pageEyebrow").textContent = pageMeta[page].eyebrow;
  document.getElementById("pageTitle").textContent = pageMeta[page].title;
  document.getElementById("pageSubtitle").textContent = pageMeta[page].subtitle;
  document.getElementById("sidebar").classList.remove("open");
  if (updateHash) history.replaceState(null, "", `#${page}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-page]").forEach(button =>
  button.addEventListener("click", () => showPage(button.dataset.page))
);
document.getElementById("menuToggle").addEventListener("click", () =>
  sidebar.classList.toggle("open")
);

function setSidebarCollapsed(collapsed) {
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  sidebarToggle.textContent = collapsed ? "›" : "‹";
  sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
  sidebarToggle.setAttribute(
    "aria-label", collapsed ? "Expandir menu lateral" : "Recolher menu lateral"
  );
  localStorage.setItem("manhwateca-sidebar-collapsed", String(collapsed));
}

sidebarToggle.addEventListener("click", () =>
  setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed"))
);

setSidebarCollapsed(
  localStorage.getItem("manhwateca-sidebar-collapsed") === "true"
);

showPage(location.hash.replace("#", "") || "overview", false);

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
  pendingList.innerHTML = '<article class="pending-card loading">Calculando pendências...</article>';
  refreshButton.disabled = true;
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    grid.innerHTML = [
      card(
        "Catálogo local",
        `${data.catalog.count} obra(s) catalogadas. É atualizado ao executar “Catalogar biblioteca”.`,
        data.catalog.available
      ),
      card(
        "Biblioteca no Drive",
        data.library.configured
          ? "O diretório configurado está acessível para leitura e organização."
          : "Configure MANGA_ROOT no arquivo .env para localizar os arquivos.",
        data.library.available
      ),
      card(
        "MangaUpdates",
        data.mangaupdates.cache_available && data.mangaupdates.csv_available
          ? "Cache de detalhes e CSV enriquecido estão disponíveis."
          : "Ainda faltam o cache de detalhes ou o CSV enriquecido.",
        data.mangaupdates.cache_available && data.mangaupdates.csv_available
      ),
      card(
        "Notion",
        data.notion.configured
          ? "Credenciais disponíveis para simular e aplicar sincronizações."
          : "Configure token e database no .env antes de sincronizar.",
        data.notion.configured,
        data.notion.configured ? "Configurado" : "Não configurado"
      ),
    ].join("");
    await loadPendingActions();
  } catch (error) {
    grid.innerHTML = card(
      "Falha ao consultar status",
      error.message,
      false,
      "Servidor indisponível"
    );
    pendingList.innerHTML = `
      <article class="pending-card warning">
        <strong>Não foi possível calcular pendências</strong>
        <span>${escapeHtml(error.message)}</span>
      </article>
    `;
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadStatus);

async function loadPendingActions() {
  const response = await fetch("/api/pending", { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  if (!payload.items.length) {
    pendingList.innerHTML = `
      <article class="pending-card success">
        <strong>Tudo em dia</strong>
        <span>${escapeHtml(payload.empty_message || "Nenhuma pendência acionável encontrada.")}</span>
      </article>
    `;
    return;
  }
  pendingList.innerHTML = payload.items.map(item => `
    <button type="button"
            class="pending-card ${escapeHtml(item.severity || "info")}"
            ${item.action ? `data-action="${escapeHtml(item.action)}"` : ""}
            ${item.page ? `data-pending-page="${escapeHtml(item.page)}"` : ""}>
      <span class="pending-kind">${escapeHtml(pendingKindLabel(item.kind))}</span>
      <strong>${escapeHtml(item.title)}</strong>
      <span>${escapeHtml(item.detail)}</span>
      <em>${escapeHtml(item.action ? "Executar próxima etapa" : "Abrir seção")}</em>
    </button>
  `).join("");
}

function pendingKindLabel(kind) {
  return {
    catalog: "Catálogo",
    csv: "CSV",
    mangaupdates: "MangaUpdates",
    notion: "Notion",
  }[kind] || "Ação";
}

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
  const actionHelp = {
    organization_preview: ["Analisa a organização alfabética das pastas.", "Gera um preview sem mover pastas."],
    rename_preview: ["Analisa nomes de capítulos, capas e títulos.", "Gera um preview sem renomear arquivos."],
    chapter_audit: ["Verifica capítulos e arquivos que precisam de conferência.", "Gera um relatório sem alterar a biblioteca."],
    catalog_scan: ["Lê novamente todas as pastas e capítulos.", "Atualiza o catálogo local data/mangas.json."],
    apply_organization: ["Move as obras para os grupos alfabéticos corretos.", "Altera as pastas após confirmação."],
    apply_renaming: ["Padroniza os nomes de capítulos e capas.", "Renomeia os arquivos após confirmação."],
    run_tests: ["Verifica automaticamente as regras principais do sistema.", "Mostra os resultados no histórico."],
    mangaupdates_search: ["Pesquisa obras ainda sem ID confirmado.", "Atualiza buscaIds.json com candidatos."],
    mangaupdates_refresh: ["Completa candidatos sem link ou descrição.", "Atualiza os candidatos já pesquisados."],
    mangaupdates_details: ["Consulta detalhes dos IDs confirmados.", "Atualiza o cache local do MangaUpdates."],
    mangaupdates_csv: ["Usa os dados já salvos, sem consultar a API.", "Atualiza o CSV preservando campos manuais."],
    notion_simulate_batch: ["Compara o catálogo com as páginas do Notion.", "Mostra o próximo lote sem alterar o Notion."],
    notion_apply_batch: ["Cria as próximas páginas ausentes.", "Publica até 25 obras após confirmação."],
    notion_update_existing: ["Envia novas contagens para páginas existentes.", "Atualiza o Notion sem criar páginas."],
    notion_csv_preview: ["Compara o CSV com as páginas existentes.", "Simula as alterações sem escrever no Notion."],
    notion_csv_apply: ["Envia os metadados enriquecidos do CSV.", "Atualiza páginas após confirmação."],
  };
  const response = await fetch("/api/actions", { cache: "no-store" });
  const actions = await response.json();
  const render = entries => entries.map(([id, action]) => {
    const fallback = actionHelp[id] || ["Ação disponível no sistema.", "O resultado aparecerá no histórico."];
    return `
    <button class="action-button ${action.requires_confirmation ? "destructive" : ""}"
            type="button" data-action="${id}"
            data-confirmation="${action.requires_confirmation}">
      <strong>${escapeHtml(action.label || id)}</strong>
      <span>${escapeHtml(action.description || fallback[0])}</span>
      <small>${escapeHtml(action.result || fallback[1])}</small>
    </button>
  `;
  }).join("");
  const entries = Object.entries(actions);
  const organizationIds = new Set([
    "organization_preview", "rename_preview", "chapter_audit",
    "catalog_scan", "apply_organization", "apply_renaming",
  ]);
  const notionIds = new Set([
    "notion_simulate_batch", "notion_apply_batch", "notion_update_existing",
    "notion_csv_preview", "notion_csv_apply",
  ]);
  actionGrid.innerHTML = render(entries.filter(([id]) => organizationIds.has(id)));
  mangaActionGrid.innerHTML = render(entries.filter(([, action]) =>
    action.group === "mangaupdates"
  ));
  notionActionGrid.innerHTML = render(entries.filter(([id]) => notionIds.has(id)));
  supportActionGrid.innerHTML = render(entries.filter(([id]) => id === "run_tests"));
}

function confirmTask(action) {
  const notionWrite = [
    "notion_apply_batch",
    "notion_update_existing",
    "notion_csv_apply",
  ].includes(action);
  confirmationTitle.textContent = notionWrite
    ? "Confirmar alteração no Notion"
    : "Confirmar alteração na biblioteca";
  confirmationText.textContent = notionWrite
    ? "Esta ação enviará alterações ao Notion. Deseja continuar?"
    : "Esta ação alterará arquivos ou pastas da biblioteca. Deseja continuar?";
  confirmationDialog.showModal();
  return new Promise(resolve => {
    confirmationDialog.addEventListener("close", () => {
      resolve(confirmationDialog.returnValue === "confirm");
    }, { once: true });
  });
}

async function startTask(action, requiresConfirmation) {
  let confirmation = null;
  let parameters = {};
  if (requiresConfirmation) {
    if (!await confirmTask(action)) return;
    confirmation = "APLICAR";
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
  document.getElementById("taskToastTitle").textContent = payload.label;
  document.getElementById("taskToastText").textContent =
    "Preparando a execução...";
  taskToast.dataset.taskId = payload.id;
  taskToast.className = "task-toast running";
  taskProgress.setAttribute("aria-label", "Tarefa em andamento");
  taskResultLink.hidden = true;
  viewTaskProgress.hidden = false;
  viewTaskProgress.textContent = "Ver andamento";
  taskToast.hidden = false;
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
    <article class="task-item" data-task-id="${escapeHtml(task.id)}">
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

viewTaskProgress.addEventListener("click", () => {
  showPage("automation");
  window.setTimeout(() => {
    const task = taskList.querySelector(
      `[data-task-id="${CSS.escape(taskToast.dataset.taskId || "")}"]`
    );
    (task || document.getElementById("taskHistory")).scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
    if (task) {
      task.classList.add("task-highlight");
      window.setTimeout(() => task.classList.remove("task-highlight"), 1800);
    }
    taskToast.hidden = true;
  }, 120);
});

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
  updateTaskToast(data.tasks);
  const hasRunning = data.tasks.some(task => ["queued", "running"].includes(task.status));
  const catalogTask = data.tasks.find(task =>
    task.action === "catalog_scan" && task.status === "completed"
  );
  if (catalogTask && catalogTask.id !== lastCatalogTask) {
    lastCatalogTask = catalogTask.id;
    await Promise.all([
      loadCatalog(),
      loadStatus(),
      loadNotionStatus(),
      loadPendingActions(),
    ]);
  }
  const mangaUpdatesTask = data.tasks.find(task =>
    task.group === "mangaupdates" && task.status === "completed"
  );
  if (mangaUpdatesTask && mangaUpdatesTask.id !== lastMangaUpdatesTask) {
    lastMangaUpdatesTask = mangaUpdatesTask.id;
    await Promise.all([loadIdReview(), loadPendingActions()]);
  }
  const notionTask = data.tasks.find(task =>
    task.group === "notion" && !["queued", "running"].includes(task.status)
  );
  if (notionTask && notionTask.id !== lastNotionTask) {
    lastNotionTask = notionTask.id;
    await Promise.all([loadNotionStatus(), loadPendingActions()]);
  }
  const metadataTask = data.tasks.find(task =>
    ["notion_csv_preview", "notion_csv_apply"].includes(task.action)
    && !["queued", "running"].includes(task.status)
  );
  if (metadataTask && metadataTask.id !== lastMetadataTask) {
    lastMetadataTask = metadataTask.id;
    await Promise.all([loadMetadataStatus(), loadPendingActions()]);
  }
  clearTimeout(taskTimer);
  taskTimer = setTimeout(loadTasks, hasRunning ? 1000 : 5000);
}

function updateTaskToast(tasks) {
  if (taskToast.hidden || !taskToast.dataset.taskId) return;
  const task = tasks.find(item => item.id === taskToast.dataset.taskId);
  if (!task) return;
  const text = document.getElementById("taskToastText");
  if (["queued", "running"].includes(task.status)) {
    taskToast.className = "task-toast running";
    text.textContent = task.status === "queued"
      ? "Aguardando o início da tarefa..."
      : "Executando. O resultado aparecerá assim que estiver pronto.";
    return;
  }
  const completed = task.status === "completed";
  taskToast.className = `task-toast ${completed ? "completed" : "failed"}`;
  taskProgress.setAttribute(
    "aria-label",
    completed ? "Tarefa concluída" : "Tarefa encerrada com erro"
  );
  text.textContent = completed
    ? "Tarefa concluída com sucesso."
    : "A tarefa não foi concluída. Consulte o resultado para entender o motivo.";
  const report = (task.reports || [])[0];
  if (completed && report) {
    taskResultLink.href = `/reports/${report.replace(/^reports\//, "")}`;
    taskResultLink.hidden = false;
    viewTaskProgress.hidden = true;
  } else {
    taskResultLink.hidden = true;
    viewTaskProgress.hidden = false;
    viewTaskProgress.textContent = "Ver resultado";
  }
}

function summaryCard(label, value) {
  return `<article><strong>${value}</strong><span>${label}</span></article>`;
}

function renderCatalog(items) {
  catalogList.innerHTML = items.length ? items.map((manga, index) => {
    const issues = [...(manga.count_issues || []), ...(manga.unparsed_files || [])];
    const aliases = (manga.alias || []).join(", ");
    const detailsId = `catalog-issue-${index}`;
    return `
      <tr>
        <td><strong>${escapeHtml(manga.nome || "")}</strong>
          ${aliases ? `<small>${escapeHtml(aliases)}</small>` : ""}</td>
        <td>${manga.ultimo_lido}</td>
        <td>${manga.main_caps}</td>
        <td>${escapeHtml(manga.tamanho)}</td>
        <td>${manga.chapters_found}</td>
        <td>${issues.length
          ? `<button class="issue-button" type="button"
               data-issue-target="${detailsId}" aria-expanded="false">
               Ver ${issues.length} alerta(s)
             </button>`
          : '<span class="state ok">OK</span>'}</td>
      </tr>
      ${issues.length ? `
        <tr class="issue-details" id="${detailsId}" hidden>
          <td colspan="6">
            <div>
              <strong>Como decidir o que fazer em ${escapeHtml(manga.nome)}:</strong>
              <div class="issue-guidance">
                ${issues.map(issue => explainIssue(issue)).join("")}
              </div>
              <button type="button" data-action="chapter_audit">
                Identificar arquivos envolvidos
              </button>
              <a href="/reports/audits/chapter_audit.html" target="_blank">
                Consultar última auditoria
              </a>
            </div>
          </td>
        </tr>` : ""}
    `;
  }).join("") : '<tr><td colspan="6" class="empty">Nenhuma obra encontrada.</td></tr>';
}

function explainIssue(issue) {
  const guidance = {
    "lacunas": [
      "Intervalos entre capítulos",
      "Se você apagou capítulos já lidos, nenhuma correção é necessária. Caso contrário, confira se há arquivos ausentes."
    ],
    "sobreposições": [
      "Capítulos repetidos em mais de um arquivo",
      "Compare os intervalos indicados na auditoria. Mantenha ambos se forem versões diferentes; caso contrário, remova o duplicado."
    ],
    "MangaUpdates divergente": [
      "Contagem local diferente do MangaUpdates",
      "Confira se a obra está atualizada na fonte. Se o Drive estiver correto, mantenha o catálogo local; não é necessário renomear arquivos."
    ],
    "somente side stories": [
      "A pasta contém apenas histórias extras",
      "Mantenha assim se a obra principal já foi lida ou removida. Revise apenas se capítulos principais deveriam estar presentes."
    ],
  };
  if (guidance[issue]) {
    return `<article><strong>${guidance[issue][0]}</strong><p>${guidance[issue][1]}</p></article>`;
  }
  if (String(issue).toLowerCase().endsWith(".pdf")) {
    return `<article><strong>Nome de arquivo não reconhecido</strong>
      <p>Revise <code>${escapeHtml(issue)}</code>. Padronize o nome somente se o capítulo ou intervalo não estiver claro.</p>
    </article>`;
  }
  return `<article><strong>${escapeHtml(issue)}</strong>
    <p>Abra a auditoria para identificar os arquivos envolvidos antes de alterar a biblioteca.</p>
  </article>`;
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
    const libraryTotal = Number.isFinite(data.summary.library)
      ? data.summary.library
      : data.summary.catalog;
    const currentCatalogTotal = Number.isFinite(data.summary.current_catalog)
      ? data.summary.current_catalog
      : data.summary.catalog;
    const uncatalogedTotal = Number.isFinite(data.summary.uncataloged)
      ? data.summary.uncataloged
      : Math.max(0, libraryTotal - data.summary.catalog);
    data.summary.library = libraryTotal;
    data.summary.current_catalog = currentCatalogTotal;
    data.summary.uncataloged = uncatalogedTotal;
    data.uncataloged = Array.isArray(data.uncataloged) ? data.uncataloged : [];
    notionSummary.innerHTML = [
      summaryCard("Biblioteca no Drive", data.summary.library),
      summaryCard("Catálogo", data.summary.current_catalog),
      summaryCard("Importadas", data.summary.imported),
      summaryCard("Pendentes", data.summary.pending),
      summaryCard("Não catalogadas", data.summary.uncataloged),
    ].join("");
    notionMeta.innerHTML = data.available
      ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
         <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>`
      : `<span>${escapeHtml(data.error || "Execute uma simulação para gerar o status.")}</span>`;
    notionLists.innerHTML = [
      notionList("Último lote", data.current_batch),
      notionList("Não catalogadas", data.uncataloged, "warning"),
      notionList("Pendentes", data.pending, "warning"),
      notionList("Duplicadas", data.duplicates, "danger"),
    ].join("");
    renderNotionSyncStatus(data);
  } finally {
    refreshNotion.disabled = false;
  }
}

function renderNotionSyncStatus(data) {
  const pending = data.summary.pending;
  const uncataloged = data.summary.uncataloged;
  notionUncataloged = uncataloged;
  notionStatusStale = Boolean(data.stale);
  updateNotionActionAvailability();
  const title = notionSyncStatus.querySelector("strong");
  const detail = notionSyncStatus.querySelector("small");
  notionSyncStatus.classList.remove("ok", "warning", "unavailable");
  if (!data.available) {
    notionSyncStatus.classList.add("unavailable");
    title.textContent = "Situação das importações ainda não verificada";
    detail.textContent = "Execute “Simular próximo lote” para comparar o catálogo com o Notion.";
    return;
  }
  if (uncataloged > 0) {
    notionSyncStatus.classList.add("warning");
    title.textContent = `${uncataloged} obra${uncataloged === 1 ? "" : "s"} do Drive ainda não ${uncataloged === 1 ? "foi catalogada" : "foram catalogadas"}`;
    detail.textContent = "Execute “Catalogar biblioteca”. Depois simule o próximo lote do Notion.";
    return;
  }
  if (data.stale) {
    notionSyncStatus.classList.add("warning");
    title.textContent = "O catálogo mudou desde a última verificação do Notion";
    detail.textContent = `O último status avaliou ${data.summary.catalog} obras; o catálogo atual possui ${data.summary.current_catalog}. Execute “Simular próximo lote”.`;
    return;
  }
  if (pending > 0) {
    notionSyncStatus.classList.add("warning");
    title.textContent = `${pending} obra${pending === 1 ? "" : "s"} ainda não ${pending === 1 ? "foi incluída" : "foram incluídas"} no Notion`;
    detail.textContent = String(data.mode || "").includes("SIMULAÇÃO")
      ? "A simulação apenas identificou as páginas. Execute “Importar próximo lote” e confirme a operação."
      : `Status da última verificação: ${data.updated_at || "data não informada"}.`;
    return;
  }
  notionSyncStatus.classList.add("ok");
  title.textContent = "Todas as obras catalogadas estão no Notion";
  detail.textContent = `Nenhuma inclusão pendente na última verificação${data.updated_at ? ` de ${data.updated_at}` : ""}.`;
}

function updateNotionActionAvailability() {
  ["notion_simulate_batch", "notion_apply_batch"].forEach(action => {
    const button = notionActionGrid.querySelector(`[data-action="${action}"]`);
    if (!button) return;
    const blockedByCatalog = notionUncataloged > 0;
    const blockedByStaleStatus =
      action === "notion_apply_batch" && notionStatusStale;
    button.disabled = blockedByCatalog || blockedByStaleStatus;
    button.title = blockedByCatalog
      ? "Catalogue as obras novas antes de sincronizar com o Notion."
      : blockedByStaleStatus
        ? "Simule o próximo lote antes de importar novas páginas."
        : "";
  });
}

notionSyncStatus.addEventListener("click", () => {
  if (notionUncataloged > 0) {
    showPage("organization");
    window.setTimeout(() => {
      const catalogButton = actionGrid.querySelector('[data-action="catalog_scan"]');
      catalogButton?.scrollIntoView({ behavior: "smooth", block: "center" });
      catalogButton?.classList.add("task-highlight");
      window.setTimeout(
        () => catalogButton?.classList.remove("task-highlight"),
        1800,
      );
    }, 120);
  } else {
    notionCatalogPanel.open = true;
    notionCatalogPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

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
      summaryCard("Sem alteração", data.summary.unchanged),
      summaryCard("Ausentes", data.summary.missing),
      summaryCard("Duplicadas", data.summary.duplicates),
      summaryCard("CSV disponível", data.csv_available ? "Sim" : "Não"),
    ].join("");
    metadataMeta.innerHTML = data.available
      ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
         <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>
         ${renderSyncStateSummary(data.sync_state)}`
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

function renderSyncStateSummary(state) {
  if (!state || !state.available) {
    return "";
  }
  const synced = state.statuses?.sincronizado || 0;
  const pending = state.statuses?.pendente || 0;
  return `<span>Estado: ${synced}/${state.total} sincronizadas${
    pending ? `, ${pending} pendente(s)` : ""
  }</span>`;
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
  const statusLabels = {
    pending: "Aguardando",
    running: "Executando",
    completed: "Concluída",
    failed: "Falhou",
    manual: "Ação manual",
    interrupted: "Interrompida",
  };
  const checked = run.selected?.includes(step.id) ?? true;
  return `
    <article class="workflow-step ${status}">
      <label>
        <input type="checkbox" value="${step.id}" ${checked ? "checked" : ""}
          ${run.status === "running" ? "disabled" : ""}>
        <span><strong>${escapeHtml(step.label)}</strong>
          ${step.manual ? "<small>Etapa manual</small>" : ""}</span>
      </label>
      <span class="workflow-status">${escapeHtml(statusLabels[status] || status)}</span>
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
      : data.run.status === "running"
        ? "Fluxo em execução."
        : ["failed", "interrupted"].includes(data.run.status)
          ? "O fluxo foi interrompido. Consulte a etapa destacada."
          : "Nenhum fluxo iniciado. Selecione as etapas e clique em Executar."
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

apiSearchForm.addEventListener("submit", async event => {
  event.preventDefault();
  const query = apiSearchQuery.value.trim();
  if (query.length < 2) return;
  const submit = apiSearchForm.querySelector("button");
  submit.disabled = true;
  apiSearchFeedback.textContent = "Consultando o MangaUpdates...";
  apiSearchResults.innerHTML = "";
  try {
    const response = await fetch("/api/mangaupdates/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const payload = await response.json();
    if (!response.ok) {
      apiSearchFeedback.textContent = response.status === 404
        ? "O servidor local precisa ser reiniciado para habilitar esta pesquisa."
        : (payload.error || "Não foi possível pesquisar.");
      return;
    }
    apiSearchFeedback.textContent = payload.results.length
      ? `${payload.results.length} resultado(s) encontrado(s).`
      : "Nenhuma obra encontrada.";
    apiSearchItems = payload.results;
    apiSearchResults.innerHTML = payload.results.map((item, index) => `
      <details class="api-result" ${index === 0 ? "open" : ""}>
        <summary>
          <strong>${escapeHtml(item.title)}</strong>
          <strong class="api-result-id">ID ${escapeHtml(item.series_id)}</strong>
        </summary>
        <div class="api-result-content">
          <p data-api-description="${index}">${escapeHtml(item.description || "Descrição não disponível.")}</p>
          <div class="api-result-actions">
            ${item.url ? `<a class="result-action" href="${escapeHtml(item.url)}"
              target="_blank" rel="noopener noreferrer" title="Detalhes"
              aria-label="Abrir detalhes no MangaUpdates">
              <span class="result-action-icon details-icon" aria-hidden="true"></span>
            </a>` : ""}
            ${item.description ? `<button type="button"
              class="result-action text-button" data-translate-result="${index}"
              title="Traduzir descrição" aria-label="Traduzir descrição">
              <span class="result-action-icon translation-icon" aria-hidden="true"></span>
            </button>` : ""}
          </div>
        </div>
      </details>
    `).join("");
  } catch {
    apiSearchFeedback.textContent = "Não foi possível conectar ao servidor local.";
  } finally {
    submit.disabled = false;
  }
});

apiSearchResults.addEventListener("click", async event => {
  const button = event.target.closest("[data-translate-result]");
  if (!button) return;
  const index = Number(button.dataset.translateResult);
  const item = apiSearchItems[index];
  const paragraph = apiSearchResults.querySelector(
    `[data-api-description="${index}"]`
  );
  if (!item || !paragraph) return;
  if (button.dataset.translated === "true") {
    paragraph.textContent = item.description;
    button.title = "Traduzir descrição";
    button.setAttribute("aria-label", "Traduzir descrição");
    button.dataset.translated = "false";
    button.classList.remove("translated");
    return;
  }
  button.disabled = true;
  button.title = "Traduzindo...";
  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: item.description }),
    });
    const payload = await response.json();
    if (!response.ok) {
      button.title = "Tentar traduzir novamente";
      apiSearchFeedback.textContent = payload.error || "Não foi possível traduzir.";
      return;
    }
    paragraph.textContent = payload.translation;
    button.title = "Ver texto original";
    button.setAttribute("aria-label", "Ver texto original");
    button.dataset.translated = "true";
    button.classList.add("translated");
    apiSearchFeedback.textContent = "Descrição traduzida para português.";
  } catch {
    button.title = "Tentar traduzir novamente";
    apiSearchFeedback.textContent = "Não foi possível conectar ao servidor local.";
  } finally {
    button.disabled = false;
  }
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
    summaryCard("Conferências necessárias", data.summary.review),
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

function handleActionClick(event) {
  const button = event.target.closest("[data-action]");
  if (button) {
    startTask(button.dataset.action, button.dataset.confirmation === "true");
  }
}

[actionGrid, mangaActionGrid, notionActionGrid, supportActionGrid]
  .forEach(container => container.addEventListener("click", handleActionClick));

document.querySelector(".quick-guide").addEventListener("click", event => {
  const action = event.target.closest("[data-action]");
  if (action) handleActionClick(event);
});

pendingList.addEventListener("click", event => {
  const card = event.target.closest(".pending-card");
  if (!card || !pendingList.contains(card)) return;
  const action = card.dataset.action;
  if (action) {
    startTask(action, pendingRequiresConfirmation(action));
    return;
  }
  if (card.dataset.pendingPage) showPage(card.dataset.pendingPage);
});

function pendingRequiresConfirmation(action) {
  return [
    "apply_organization",
    "apply_renaming",
    "notion_apply_batch",
    "notion_update_existing",
    "notion_csv_apply",
  ].includes(action);
}

catalogList.addEventListener("click", event => {
  const issueButton = event.target.closest("[data-issue-target]");
  if (issueButton) {
    const details = document.getElementById(issueButton.dataset.issueTarget);
    details.hidden = !details.hidden;
    issueButton.setAttribute("aria-expanded", String(!details.hidden));
    issueButton.textContent = details.hidden
      ? issueButton.textContent.replace("Ocultar", "Ver")
      : issueButton.textContent.replace("Ver", "Ocultar");
    return;
  }
  const action = event.target.closest("[data-action]");
  if (action) handleActionClick(event);
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
