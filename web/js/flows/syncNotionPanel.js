import { escapeHtml } from "../utils/html.js";

const NEXT_ACTION_LABELS = {
  none: "Nenhuma ação necessária",
  apply: "Aplicar alterações técnicas",
  review_duplicates: "Revisar páginas duplicadas",
  review_missing: "Revisar páginas ausentes",
  review_blockers: "Revisar bloqueios",
  retry: "Tentar novamente",
};

const BLOCKER_LABELS = {
  api_error: "Erro de comunicação",
  duplicate_page: "Página duplicada",
  missing_page: "Página ausente",
  stale_notion_page: "Página alterada no Notion",
  unsafe_property: "Propriedade não autorizada",
  local_persistence_error: "Erro ao persistir estado local",
};

export function renderSyncNotionPanel(input = {}) {
  const context = normalizeContext(input);
  const state = officialState(context);
  const showCandidatePicker = state.showCandidatePicker !== false;
  const actionDisabled = state.actionDisabled || (
    showCandidatePicker && !context.running && context.journeyWorkIds.length === 0
  );
  return `
    <section class="sync-notion-panel sync-notion-panel--${escapeHtml(state.tone)}">
      <details class="flow-section-details" open>
        ${mainHeader()}
        <div class="flow-section-body sync-notion-stage-body ${showCandidatePicker ? "" : "sync-notion-stage-body--detail-only"}">
          ${showCandidatePicker ? candidatePicker(context) : ""}
          <section class="sync-notion-detail-panel">
            ${showCandidatePicker ? selectedCandidateDetail() : ""}
            ${state.showHeader === false ? "" : header(state)}
            ${state.note ? note(state.note) : ""}
            ${state.metrics.length ? verificationPanel(state) : ""}
            ${state.showNextAction === false && state.showActionButton === false ? "" : nextAction(state, actionDisabled)}
            ${state.blockers.length ? blockersList(state.blockers) : state.clearMessage ? note(state.clearMessage) : ""}
          </section>
        </div>
      </details>
    </section>
  `;
}

function mainHeader() {
  const description = "Reflete no Notion as alterações realizadas durante o Workflow.";
  return `
    <summary class="flow-section-summary sync-notion-main-header">
      <span class="eyebrow">Jornada operacional</span>
      <span class="sync-notion-title-row">
        <h2>${headingTooltip("Sincronizar Notion", description)}</h2>
      </span>
    </summary>
  `;
}

function normalizeContext(input) {
  if (
    input
    && (
      Object.prototype.hasOwnProperty.call(input, "stageResult")
      || Object.prototype.hasOwnProperty.call(input, "stageStatus")
      || Object.prototype.hasOwnProperty.call(input, "legacyMetadata")
    )
  ) {
    return {
      stageResult: input.stageResult || null,
      stageStatus: input.stageStatus || input.stageResult?.status || "waiting",
      legacyMetadata: input.legacyMetadata || {},
      candidates: input.legacyMetadata?.candidates || { items: [], summary: {} },
      candidateStatus: input.candidateStatus || input.legacyMetadata?.candidates?.filter || "default",
      journeyWorkIds: Array.isArray(input.journeyWorkIds) ? input.journeyWorkIds : [],
      hiddenWorkIds: Array.isArray(input.hiddenWorkIds) ? input.hiddenWorkIds : [],
      running: input.stageStatus === "running",
    };
  }
  return {
    stageResult: null,
    stageStatus: "waiting",
    legacyMetadata: input || {},
    candidates: input?.candidates || { items: [], summary: {} },
    candidateStatus: input?.candidates?.filter || "default",
    journeyWorkIds: [],
    hiddenWorkIds: [],
    running: false,
  };
}

function officialState(context) {
  const result = context.stageResult || {};
  const metrics = result.metrics || {};
  const status = result.status || context.stageStatus || "waiting";
  const messages = officialMessages(result);
  const message = result.note || messages[0] || "";
  const hasOfficialResult = hasOfficialMetrics(metrics) || isTerminal(status);

  if (status === "running") {
    return {
      title: "Sincronização em andamento",
      lead: "Validando obras e comparando dados com o Notion.",
      tone: "info",
      note: "Aguarde a conclusão para ver as métricas oficiais.",
      metrics: [],
      blockers: [],
      nextAction: "Etapa em processamento",
      showNextAction: true,
      showCandidatePicker: false,
      actionLabel: "Sincronizando...",
      actionDisabled: true,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (!hasOfficialResult && status === "waiting") {
    return {
      title: "Esta etapa ainda não foi executada nesta jornada.",
      lead: "Abrir esta tela não inicia a sincronização. Use o botão abaixo para executar a etapa manualmente.",
      tone: "info",
      note: "",
      metrics: [],
      blockers: [],
      nextAction: "Sincronizar quando estiver pronta",
      showNextAction: true,
      showHeader: false,
      showCandidatePicker: true,
      actionLabel: "Sincronizar com o Notion",
      actionDisabled: context.journeyWorkIds.length === 0,
      clearMessage: "",
      hasOfficialResult: false,
    };
  }

  if (isUnavailable(metrics, messages)) {
    return {
      title: "Integração com o Notion indisponível.",
      lead: message || "Verifique a configuração do Notion antes de tentar novamente.",
      tone: "bad",
      note: "",
      metrics: errorMetrics(metrics),
      blockers: blockers(metrics),
      nextAction: "Verificar configuração",
      showNextAction: true,
      showCandidatePicker: false,
      actionLabel: "Tentar novamente",
      actionDisabled: false,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (metrics.status === "blocked" || hasBlockedWarning(result)) {
    return {
      title: "Sincronização pausada por bloqueios.",
      lead: message || "Resolva os bloqueios antes de tentar sincronizar novamente.",
      tone: "warning",
      note: "",
      metrics: blockedMetrics(result, metrics),
      blockers: blockers(metrics),
      nextAction: nextActionLabel(metrics.next_action),
      showNextAction: true,
      showCandidatePicker: false,
      actionLabel: "Tentar novamente",
      actionDisabled: false,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (metrics.status === "error" && metrics.partial) {
    return {
      title: "Sincronização interrompida parcialmente.",
      lead: message || "Parte do lote já foi aplicada no Notion antes da interrupção.",
      tone: "warning",
      note: "Revise o erro antes de executar novamente para evitar inconsistências.",
      metrics: partialMetrics(metrics),
      blockers: blockers(metrics),
      nextAction: nextActionLabel(metrics.next_action || "retry"),
      showNextAction: true,
      showCandidatePicker: false,
      actionLabel: "Tentar novamente",
      actionDisabled: false,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (status === "failed" || metrics.status === "error") {
    return {
      title: "Não foi possível concluir a sincronização.",
      lead: message || "A execução oficial falhou antes de concluir a etapa.",
      tone: "bad",
      note: "",
      metrics: errorMetrics(metrics),
      blockers: blockers(metrics),
      nextAction: nextActionLabel(metrics.next_action || "retry"),
      showNextAction: true,
      showCandidatePicker: isScopeSelectionError(metrics, messages),
      actionLabel: "Tentar novamente",
      actionDisabled: false,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (metrics.status === "synced") {
    const checkedCount = Number(
      metrics.checked_count
      || Number(metrics.applied_count || 0) + Number(metrics.remote_matches_local_count || metrics.unchanged_count || 0)
    );
    return {
      title: "Sincronização oficial concluída.",
      lead: Number(metrics.applied_count || 0) > 0
        ? "As alterações técnicas foram aplicadas pelo fluxo oficial."
        : `Verificação concluída: ${checkedCount || 0} obra(s) equivalentes ao Notion.`,
      tone: "ok",
      note: "",
      metrics: syncedMetrics(metrics),
      blockers: blockers(metrics),
      nextAction: nextActionLabel(metrics.next_action || "none"),
      showNextAction: nextActionLabel(metrics.next_action || "none") !== NEXT_ACTION_LABELS.none,
      showHeader: false,
      showCandidatePicker: true,
      showActionButton: true,
      actionLabel: "Selecione obras",
      actionDisabled: context.journeyWorkIds.length === 0,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  return {
    title: "Estado oficial do Notion indisponível.",
    lead: message || "Ainda não há resultado estruturado para esta etapa.",
    tone: "info",
    note: "",
    metrics: [],
    blockers: [],
    nextAction: "Executar a etapa manualmente",
    showNextAction: true,
    showCandidatePicker: true,
    actionLabel: "Sincronizar com o Notion",
    actionDisabled: context.journeyWorkIds.length === 0,
    clearMessage: "",
    hasOfficialResult,
  };
}

function isScopeSelectionError(metrics, messages) {
  if (metrics.scope_missing) return true;
  return (messages || []).some(message =>
    /selecione ao menos uma obra/i.test(String(message || ""))
  );
}

function header(state) {
  return `
    <header class="sync-notion-header">
      <span class="sync-notion-status-dot" aria-hidden="true"></span>
      <div>
        <h3>${escapeHtml(state.title)}</h3>
        <p>${escapeHtml(state.lead)}</p>
      </div>
    </header>
  `;
}

function candidatePicker(context) {
  const candidates = context.candidates || { items: [], summary: {} };
  const activeFilter = context.candidateStatus || candidates.filter || "default";
  const hideSessionSynced = activeFilter === "default";
  const items = hideSessionSynced
    ? visibleCandidateItems(candidates.items, context.hiddenWorkIds)
    : (Array.isArray(candidates.items) ? candidates.items : []);
  const summary = candidates.summary || {};
  const journeyCount = context.journeyWorkIds.length;
  const resultByWorkId = latestResultByWorkId(context.stageResult?.metrics?.results);
  const sessionWorkIds = new Set((context.hiddenWorkIds || []).map(Number));
  const pageSize = 5;
  const page = 1;
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  return `
    <section class="sync-notion-candidates" data-notion-sync-candidates data-notion-sync-page="${page}" data-notion-sync-page-size="${pageSize}">
      <header class="sync-notion-queue-header">
        <h3>${headingTooltip("Fila de sincronização", "Obras pendentes de verificação ou atualização no Notion.")}</h3>
      </header>
      <div class="sync-notion-candidate-summary">
        ${candidateSummary(summary)}
      </div>
      <div class="sync-notion-candidate-tools">
        <label>
          <span>Buscar obra</span>
          <input type="search" placeholder="Nome, ID local ou MangaUpdates" data-notion-sync-search>
        </label>
      </div>
      <div class="sync-notion-selection-head">
        <label class="sync-notion-page-size sync-notion-page-size--filter">
          <span>Mostrar</span>
          <select data-notion-sync-status-filter>
            ${candidateFilterOptions(activeFilter)}
          </select>
        </label>
        <label class="sync-notion-page-size sync-notion-page-size--size">
          <span>Itens</span>
          <select data-notion-sync-page-size-select>
            ${[5, 10].map(size => `<option value="${size}" ${size === pageSize ? "selected" : ""}>${size}</option>`).join("")}
          </select>
        </label>
        <label class="sync-notion-select-all">
          <input type="checkbox" data-notion-sync-select-all>
          ${headingTooltip("Selecionar visíveis", inheritedScopeMessage(journeyCount))}
        </label>
      </div>
      <div class="sync-notion-candidate-list">
        ${items.length ? items.map((item, index) => candidateItem(item, index, {
          result: resultByWorkId.get(Number(item.workId)),
          sessionDone: sessionWorkIds.has(Number(item.workId)),
        })).join("") : emptyCandidates()}
      </div>
      <div class="sync-notion-candidate-footer">
        <span></span>
        ${notionSyncPager(page, pages)}
      </div>
    </section>
  `;
}

function headingTooltip(label, text) {
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(text)}">${escapeHtml(label)}</span>`;
}

function latestResultByWorkId(results) {
  const entries = new Map();
  if (!Array.isArray(results)) return entries;
  for (const result of results) {
    const workId = Number(result?.work_id || result?.workId);
    if (Number.isFinite(workId) && workId > 0) entries.set(workId, result);
  }
  return entries;
}

function selectedCandidateDetail() {
  return `
    <section class="sync-notion-selected-detail" data-notion-sync-detail>
      <div class="sync-notion-detail-topline">
        <div>
          <span class="eyebrow">Obra selecionada</span>
          <h3 data-notion-sync-detail-title>Nenhuma obra selecionada</h3>
        </div>
        <span class="sync-notion-detail-status" data-notion-sync-detail-status hidden></span>
      </div>
      <div class="sync-notion-detail-grid">
        <article>
          <span>ID MangaUpdates</span>
          <strong data-notion-sync-detail-work-code>Não informado</strong>
        </article>
        <article>
          <span>Página no Notion</span>
          <strong data-notion-sync-detail-page>Não associada</strong>
        </article>
        <article>
          <span>Última sincronização</span>
          <strong data-notion-sync-detail-synced>Não informada</strong>
        </article>
      </div>
      <div class="sync-notion-cover-note-row">
        <div class="sync-notion-cover" data-notion-sync-detail-cover role="button" tabindex="0" aria-expanded="false" aria-label="Ampliar capa">
          <span>Sem capa</span>
        </div>
        <article class="sync-notion-planner-note">
          <strong data-notion-sync-note-title>O que acontecerá</strong>
          <p data-notion-sync-note-text>O planner oficial localizará a página correspondente no Notion, comparará os dados técnicos e só aplicará alterações quando encontrar diferenças.</p>
        </article>
      </div>
      <div class="sync-notion-completion-note" data-notion-sync-completion hidden>
        <strong>Verificação concluída</strong>
        <span>Esta obra foi removida da fila da sessão. Selecione outro item para continuar.</span>
      </div>
    </section>
  `;
}

function candidateFilterOptions(activeFilter) {
  const options = [
    ["error", "Com erro"],
    ["default", "Fila padrão"],
    ["never_synced", "Nunca sincronizadas"],
    ["pending", "Pendentes"],
    ["synced", "Sincronizadas"],
    ["all", "Todas"],
  ];
  return options.map(([value, label]) =>
    `<option value="${escapeHtml(value)}" ${value === activeFilter ? "selected" : ""}>${escapeHtml(label)}</option>`
  ).join("");
}

function filterDescription(activeFilter) {
  if (activeFilter === "synced") {
    return "Obras já sincronizadas ficam disponíveis apenas nesta visão explícita.";
  }
  if (activeFilter === "all") {
    return "Mostra todas as obras elegíveis do PostgreSQL para consulta manual.";
  }
  if (activeFilter === "never_synced") {
    return "Mostra obras com ID MangaUpdates que ainda não têm confirmação local de sync Notion.";
  }
  if (activeFilter === "error") {
    return "Mostra obras com erro registrado na última tentativa de sincronização.";
  }
  if (activeFilter === "pending") {
    return "Mostra obras marcadas localmente como pendentes de sincronização.";
  }
  return "Fila operacional: obras nunca sincronizadas, pendentes ou com erro.";
}

function visibleCandidateItems(items, hiddenWorkIds) {
  const hidden = new Set((hiddenWorkIds || []).map(Number));
  return (Array.isArray(items) ? items : [])
    .filter(item => !hidden.has(Number(item.workId)));
}

function candidateSummary(summary) {
  const pending = Number(summary.neverSynced || 0) + Number(summary.pending || 0);
  return [
    ["Pendentes", pending],
    ["Sincronizadas", summary.synced || 0],
    ["Erros", summary.error || 0],
  ].map(([label, value]) => `
    <span>
      <strong>${escapeHtml(String(value))}</strong>
      <small>${escapeHtml(label)}</small>
    </span>
  `).join("");
}

function candidateItem(item, index, options = {}) {
  const workId = item.workId || "";
  const title = item.title || "Obra sem título";
  const status = item.displayStatus || "Estado local não informado";
  const listStatus = compactCandidateStatus(item, status);
  const pageLabel = item.notionPageId ? "Associada" : "Não associada";
  const resultStatus = String(options.result?.status || "").trim();
  const resultMessage = String(options.result?.message || options.result?.reason || options.result?.error || "").trim();
  const syncedLabel = item.notionLastSyncedAt
    ? formatTimestamp(item.notionLastSyncedAt)
    : (item.notionSyncStatus === "synced" || resultStatus === "remote_matches_local" ? "Equivalência confirmada" : "Nunca sincronizada");
  const selectable = item.selectable !== false;
  const search = [
    title,
    item.workCode || "",
    String(workId || ""),
  ].join(" ").toLocaleLowerCase("pt-BR");
  return `
    <label class="sync-notion-candidate ${selectable ? "" : "is-disabled"}" data-notion-sync-candidate data-notion-sync-index="${index}" data-notion-sync-search-text="${escapeHtml(search)}" data-notion-sync-title="${escapeHtml(title)}" data-notion-sync-status="${escapeHtml(status)}" data-notion-sync-raw-status="${escapeHtml(item.notionSyncStatus || "")}" data-notion-sync-result-status="${escapeHtml(resultStatus)}" data-notion-sync-result-message="${escapeHtml(resultMessage)}" data-notion-sync-session-done="${options.sessionDone ? "true" : "false"}" data-notion-sync-work-code="${escapeHtml(item.workCode || "")}" data-notion-sync-page-label="${escapeHtml(pageLabel)}" data-notion-sync-synced-label="${escapeHtml(syncedLabel)}" data-notion-sync-cover-url="${escapeHtml(item.coverUrl || "")}" ${index >= 5 ? "hidden" : ""}>
      <input type="checkbox" data-notion-sync-choice data-notion-sync-work-id="${escapeHtml(String(workId))}" ${selectable ? "" : "disabled"}>
      <span>
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(listStatus)} · ID ${escapeHtml(String(workId || "--"))}</small>
      </span>
    </label>
  `;
}

function compactCandidateStatus(item, fallback) {
  const status = String(item?.notionSyncStatus || "").trim();
  if (status === "synced") return "Sincronizada";
  if (status === "pending") return "Pendente";
  if (status === "error") return "Erro";
  if (status === "conflict") return "Precisa de revisão";
  if (status === "ignored") return "Ignorada";
  return fallback;
}

function notionSyncPager(page, pages) {
  const nextPage = Math.min(page + 1, pages);
  return `
    <nav class="sync-notion-pager" data-notion-sync-pager aria-label="Paginação de obras para sincronização">
      <button class="flow-page-link" type="button" data-notion-sync-page-action="prev" ${page <= 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>
      <button class="flow-page-link active" type="button" data-notion-sync-page-number="${page}">${page}</button>
      <button class="flow-page-link" type="button" data-notion-sync-page-number="${nextPage}" ${page >= pages ? "hidden" : ""}>${nextPage}</button>
      <button class="flow-page-link" type="button" data-notion-sync-page-action="next" ${page >= pages ? "disabled" : ""} aria-label="Próxima página">›</button>
    </nav>
  `;
}

function inheritedScopeMessage(count) {
  return count === 1
    ? "Se nenhuma obra for selecionada, esta etapa usará a obra da jornada atual."
    : "Se nenhuma obra for selecionada, esta etapa usará as obras da jornada atual.";
}

function emptyCandidates() {
  return `
    <div class="flow-panel-note sync-notion-empty-candidates">
      Nenhuma obra elegível encontrada no PostgreSQL.
    </div>
  `;
}

function verificationPanel(state) {
  return `
    <section class="sync-notion-verification">
      <header>
        <strong>Última verificação da etapa</strong>
        ${state.checkedAt ? `<span>${escapeHtml(state.checkedAt)}</span>` : ""}
      </header>
      ${metricsGrid(state.metrics)}
    </section>
  `;
}

function metricsGrid(items) {
  return `
    <div class="flow-subgrid sync-notion-metrics">
      ${items.map(item => metric(item.label, item.value)).join("")}
    </div>
  `;
}

function syncedMetrics(metrics) {
  const applied = Number(metrics.applied_count || metrics.updated_count || 0);
  const remoteMatches = Number(metrics.remote_matches_local_count || metrics.unchanged_count || 0);
  return [
    { label: "Obras verificadas", value: Number(metrics.checked_count || applied + remoteMatches) },
    { label: "Alterações aplicadas", value: applied },
    { label: "Equivalentes ao Notion", value: remoteMatches },
    { label: "Falhas", value: metrics.failed_count || 0 },
  ];
}

function blockedMetrics(result, metrics) {
  return [
    { label: "Bloqueios", value: metrics.blocker_count || result.skipped || 0 },
    { label: "Ausentes", value: metrics.missing_count || 0 },
    { label: "Duplicadas", value: metrics.duplicate_count || 0 },
  ];
}

function partialMetrics(metrics) {
  return [
    { label: "Aplicadas", value: metrics.applied_count || 0 },
    { label: "Com falha", value: metrics.failed_count || 0 },
    { label: "Sem alteração", value: metrics.unchanged_count || 0 },
  ];
}

function errorMetrics(metrics) {
  return [
    { label: "Falhas", value: metrics.failed_count || 1 },
    { label: "Aplicadas", value: metrics.applied_count || 0 },
  ];
}

function nextAction(state, disabled = false) {
  return `
    <article class="sync-notion-next-action">
      <div>
        <strong>Próxima ação</strong>
        <span data-notion-sync-next-label>${escapeHtml(state.nextAction)}</span>
        <p data-notion-sync-next-helper></p>
      </div>
      ${state.showActionButton === false ? "" : `
        <button class="primary-action" type="button" data-flow-run-stage data-notion-sync-action ${disabled ? "disabled" : ""}>
          ${escapeHtml(state.actionLabel)}
        </button>
      `}
    </article>
  `;
}

function legacySection(metadata, hasOfficialResult) {
  if (hasOfficialResult) return "";
  if (!metadata?.sync && !metadata?.updated_at && !metadata?.summary) return "";
  const summary = metadata.summary || {};
  const title = "Última simulação legada";
  return `
    <details class="sync-notion-legacy">
      <summary>${escapeHtml(title)}</summary>
      <p>Este relatório salvo não representa a execução oficial atual.</p>
      <div class="sync-notion-legacy-meta">
        <span>Data: ${escapeHtml(formatTimestamp(metadata.updated_at))}</span>
        <span>Modo: ${escapeHtml(metadata.mode || "não informado")}</span>
      </div>
      <div class="sync-notion-legacy-summary">
        ${legacyMetric("Atualizações", summary.updates)}
        ${legacyMetric("Sem alteração", summary.unchanged)}
        ${legacyMetric("Ausentes", summary.missing)}
        ${legacyMetric("Duplicadas", summary.duplicates)}
      </div>
    </details>
  `;
}

function legacyMetric(label, value) {
  return `<span>${escapeHtml(label)}: ${escapeHtml(String(Number(value || 0)))}</span>`;
}

function metric(label, value) {
  return `
    <article class="flow-metric-card">
      <strong>${escapeHtml(String(Number(value || 0)))}</strong>
      <span>${escapeHtml(label)}</span>
    </article>
  `;
}

function note(text) {
  return `
    <div class="flow-panel-note sync-notion-clear">
      ${escapeHtml(text)}
    </div>
  `;
}

function blockersList(items) {
  return `
    <div class="sync-notion-blockers">
      <h4>O que impede a sincronização</h4>
      <div class="sync-notion-blocker-list">
        ${items.map(blockerItem).join("")}
      </div>
    </div>
  `;
}

function blockerItem(blocker) {
  const title = blocker.work_title || blocker.message || "Item sem identificação";
  const detail = [
    blockerLabel(blocker.code),
    blocker.work_id ? `ID ${blocker.work_id}` : "",
    blocker.message && blocker.message !== title ? blocker.message : "",
  ].filter(Boolean).join(" · ");
  const action = blocker.code === "missing_page" && blocker.work_id
    ? `<button class="secondary-action" type="button" data-notion-create-page data-notion-create-work-id="${escapeHtml(String(blocker.work_id))}">Criar página no Notion</button>`
    : "";
  return `
    <article class="sync-notion-blocker">
      <div>
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
      ${action}
    </article>
  `;
}

function blockers(metrics) {
  return Array.isArray(metrics.blockers) ? metrics.blockers : [];
}

function hasOfficialMetrics(metrics) {
  return Boolean(metrics && Object.keys(metrics).length);
}

function isTerminal(status) {
  return ["completed", "completed_with_warnings", "failed", "cancelled"].includes(status);
}

function hasBlockedWarning(result) {
  return officialMessages(result).some(message =>
    String(message || "").includes("Sincronização pausada")
  );
}

function isUnavailable(metrics, messages) {
  const text = [
    metrics.message,
    metrics.error,
    ...(messages || []),
  ].filter(Boolean).join(" ");
  return /notion indisponível/i.test(text);
}

function officialMessages(result) {
  return [
    ...(result.messages || []),
    ...(result.warnings || []),
    ...(result.errors || []),
  ].map(messageText).filter(Boolean);
}

function messageText(item) {
  if (!item) return "";
  if (typeof item === "string") return item;
  return item.message || item.detail || item.reason || item.code || "";
}

function nextActionLabel(action) {
  return NEXT_ACTION_LABELS[action] || NEXT_ACTION_LABELS.review_blockers;
}

function blockerLabel(code) {
  return BLOCKER_LABELS[code] || "Bloqueio identificado";
}

function formatTimestamp(value) {
  if (!value) return "não disponível";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
