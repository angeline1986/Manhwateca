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
      ${mainHeader()}
      ${state.showHeader === false ? "" : header(state)}
      ${showCandidatePicker ? candidatePicker(context) : ""}
      ${state.note ? note(state.note) : ""}
      ${state.metrics.length ? metricsGrid(state.metrics) : ""}
      ${state.showNextAction === false ? "" : nextAction(state)}
      ${state.blockers.length ? blockersList(state.blockers) : state.clearMessage ? note(state.clearMessage) : ""}
      ${state.showActionButton === false ? "" : actionButton(state.actionLabel, actionDisabled)}
      ${legacySection(context.legacyMetadata, state.hasOfficialResult)}
    </section>
  `;
}

function mainHeader() {
  const description = "Reflete no Notion as alterações realizadas durante o Workflow.";
  return `
    <header class="sync-notion-main-header">
      <span class="eyebrow">Jornada operacional</span>
      <h2>${headingTooltip("Sincronizar Notion", description)}</h2>
    </header>
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
      note: "As obras verificadas foram removidas desta fila da sessão. Selecione um novo lote para continuar.",
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
  const pageSize = 5;
  const page = 1;
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  return `
    <section class="sync-notion-candidates" data-notion-sync-candidates data-notion-sync-page="${page}" data-notion-sync-page-size="${pageSize}">
      <div class="sync-notion-candidate-header">
        <span data-notion-sync-selected>0 selecionadas</span>
      </div>
      <div class="sync-notion-candidate-tools">
        <label>
          <span>Buscar obra</span>
          <input type="search" placeholder="Digite título ou ID" data-notion-sync-search>
        </label>
        <div class="sync-notion-candidate-summary">
          ${candidateSummary(summary)}
        </div>
      </div>
      <div class="sync-notion-selection-head">
        <label class="sync-notion-select-all">
          <input type="checkbox" data-notion-sync-select-all>
          Selecionar todas visíveis
        </label>
        <label class="sync-notion-page-size">
          <span>Mostrar</span>
          <select data-notion-sync-status-filter>
            ${candidateFilterOptions(activeFilter)}
          </select>
        </label>
        <label class="sync-notion-page-size">
          <span>Itens por página</span>
          <select data-notion-sync-page-size-select>
            ${[5, 10].map(size => `<option value="${size}" ${size === pageSize ? "selected" : ""}>${size}</option>`).join("")}
          </select>
        </label>
      </div>
      <div class="sync-notion-candidate-list">
        ${items.length ? items.map(candidateItem).join("") : emptyCandidates()}
      </div>
      <div class="sync-notion-candidate-footer">
        ${journeyCount ? inheritedScope(context, items) : "<span></span>"}
        ${notionSyncPager(page, pages)}
      </div>
    </section>
  `;
}

function headingTooltip(label, text) {
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(text)}">${escapeHtml(label)}</span>`;
}

function candidateFilterOptions(activeFilter) {
  const options = [
    ["default", "Pendentes"],
    ["never_synced", "Nunca sincronizadas"],
    ["error", "Com erro"],
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
  return "Fila operacional: obras ainda não sincronizadas, pendentes ou com erro.";
}

function visibleCandidateItems(items, hiddenWorkIds) {
  const hidden = new Set((hiddenWorkIds || []).map(Number));
  return (Array.isArray(items) ? items : [])
    .filter(item => !hidden.has(Number(item.workId)));
}

function candidateSummary(summary) {
  return [
    `Total: ${summary.total || 0}`,
    `Nunca sincronizadas: ${summary.neverSynced || 0}`,
    `Sincronizadas: ${summary.synced || 0}`,
    `Erro: ${summary.error || 0}`,
    `Revisão: ${summary.conflict || 0}`,
  ].map(item => `<span>${escapeHtml(item)}</span>`).join("");
}

function candidateItem(item, index) {
  const workId = item.workId || "";
  const title = item.title || "Obra sem título";
  const status = item.displayStatus || "Estado local não informado";
  const selectable = item.selectable !== false;
  const search = [
    title,
    item.workCode || "",
    String(workId || ""),
  ].join(" ").toLocaleLowerCase("pt-BR");
  return `
    <label class="sync-notion-candidate ${selectable ? "" : "is-disabled"}" data-notion-sync-candidate data-notion-sync-index="${index}" data-notion-sync-search-text="${escapeHtml(search)}" ${index >= 5 ? "hidden" : ""}>
      <input type="checkbox" data-notion-sync-choice data-notion-sync-work-id="${escapeHtml(String(workId))}" ${selectable ? "" : "disabled"}>
      <span>
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(status)} · ID ${escapeHtml(String(workId || "--"))} · MangaUpdates ${escapeHtml(item.workCode || "--")}</small>
      </span>
    </label>
  `;
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

function inheritedScope(context, items) {
  const works = journeyWorks(context.journeyWorkIds, items);
  const count = works.length;
  const message = count === 1
    ? "Se nenhuma obra for selecionada, esta etapa usará a obra da jornada atual."
    : "Se nenhuma obra for selecionada, esta etapa usará as obras da jornada atual.";
  return `
    <details class="sync-notion-inherited-scope">
      <summary>
        <span>${escapeHtml(message)}</span>
        <span class="sync-notion-inherited-arrow" aria-hidden="true">▸</span>
      </summary>
      <div class="sync-notion-inherited-list">
        ${works.map(work => `
          <span>${escapeHtml(work.title)} · ID ${escapeHtml(String(work.workId))}</span>
        `).join("")}
      </div>
    </details>
  `;
}

function journeyWorks(workIds, items) {
  const byId = new Map(items.map(item => [Number(item.workId), item]));
  return workIds
    .map(workId => {
      const numericId = Number(workId);
      const item = byId.get(numericId);
      return {
        workId: numericId,
        title: item?.title || "Obra da jornada",
      };
    })
    .filter(work => Number.isFinite(work.workId) && work.workId > 0);
}

function emptyCandidates() {
  return `
    <div class="flow-panel-note sync-notion-empty-candidates">
      Nenhuma obra elegível encontrada no PostgreSQL.
    </div>
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

function nextAction(state) {
  return `
    <article class="sync-notion-next-action">
      <strong>Próxima ação</strong>
      <span>${escapeHtml(state.nextAction)}</span>
    </article>
  `;
}

function actionButton(label, disabled = false) {
  return `
    <div class="sync-notion-actions">
      <button class="primary-action" type="button" data-flow-run-stage ${disabled ? "disabled" : ""}>
        ${escapeHtml(label)}
      </button>
    </div>
  `;
}

function legacySection(metadata, hasOfficialResult) {
  if (hasOfficialResult) return "";
  if (!metadata?.sync && !metadata?.updated_at && !metadata?.summary) return "";
  const summary = metadata.summary || {};
  const title = "Última simulação legada";
  return `
    <aside class="sync-notion-legacy">
      <h4>${escapeHtml(title)}</h4>
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
    </aside>
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
