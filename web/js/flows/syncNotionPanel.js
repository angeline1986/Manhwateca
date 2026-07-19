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
  const actionDisabled = state.actionDisabled || (
    !context.running && context.journeyWorkIds.length === 0
  );
  return `
    <section class="sync-notion-panel sync-notion-panel--${escapeHtml(state.tone)}">
      ${header(state)}
      ${candidatePicker(context)}
      ${state.note ? note(state.note) : ""}
      ${state.metrics.length ? metricsGrid(state.metrics) : ""}
      ${nextAction(state)}
      ${state.blockers.length ? blockersList(state.blockers) : state.clearMessage ? note(state.clearMessage) : ""}
      ${actionButton(state.actionLabel, actionDisabled)}
      ${legacySection(context.legacyMetadata, state.hasOfficialResult)}
    </section>
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
      journeyWorkIds: Array.isArray(input.journeyWorkIds) ? input.journeyWorkIds : [],
      running: input.stageStatus === "running",
    };
  }
  return {
    stageResult: null,
    stageStatus: "waiting",
    legacyMetadata: input || {},
    candidates: input?.candidates || { items: [], summary: {} },
    journeyWorkIds: [],
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
      actionLabel: "Tentar novamente",
      actionDisabled: false,
      clearMessage: "",
      hasOfficialResult,
    };
  }

  if (metrics.status === "synced") {
    return {
      title: "Sincronização oficial concluída.",
      lead: Number(metrics.applied_count || 0) > 0
        ? "As alterações técnicas foram aplicadas pelo fluxo oficial."
        : "Nenhuma alteração técnica era necessária no Notion.",
      tone: "ok",
      note: "Origem: Fluxo oficial.",
      metrics: syncedMetrics(metrics),
      blockers: blockers(metrics),
      nextAction: nextActionLabel(metrics.next_action || "none"),
      actionLabel: "Sincronizar novamente",
      actionDisabled: false,
      clearMessage: blockers(metrics).length ? "" : "Nenhum bloqueio identificado na execução oficial.",
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
    actionLabel: "Sincronizar com o Notion",
    actionDisabled: context.journeyWorkIds.length === 0,
    clearMessage: "",
    hasOfficialResult,
  };
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
  const items = Array.isArray(candidates.items) ? candidates.items : [];
  const summary = candidates.summary || {};
  const journeyCount = context.journeyWorkIds.length;
  return `
    <section class="sync-notion-candidates" data-notion-sync-candidates>
      <div class="sync-notion-candidate-header">
        <div>
          <h4>Selecionar obras para sincronização</h4>
          <p>Escolha obras elegíveis do PostgreSQL. O planner oficial decide se há diferenças no Notion.</p>
        </div>
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
      ${journeyCount ? `
        <div class="flow-panel-note sync-notion-inherited-scope">
          ${escapeHtml(`${journeyCount} obra(s) processada(s) nesta jornada podem ser usadas se nenhuma seleção manual for feita.`)}
        </div>
      ` : ""}
      <div class="sync-notion-candidate-list">
        ${items.length ? items.map(candidateItem).join("") : emptyCandidates()}
      </div>
    </section>
  `;
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

function candidateItem(item) {
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
    <label class="sync-notion-candidate ${selectable ? "" : "is-disabled"}" data-notion-sync-candidate data-notion-sync-search-text="${escapeHtml(search)}">
      <input type="checkbox" data-notion-sync-choice data-notion-sync-work-id="${escapeHtml(String(workId))}" ${selectable ? "" : "disabled"}>
      <span>
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(status)} · ID ${escapeHtml(String(workId || "--"))} · MangaUpdates ${escapeHtml(item.workCode || "--")}</small>
      </span>
    </label>
  `;
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
  return [
    { label: "Atualizações", value: metrics.applied_count || metrics.updated_count || 0 },
    { label: "Sem alteração", value: metrics.unchanged_count || 0 },
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
  if (!metadata?.sync && !metadata?.updated_at && !metadata?.summary) return "";
  const summary = metadata.summary || {};
  const title = hasOfficialResult ? "Última simulação legada" : "Última simulação legada";
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
  return `
    <article class="sync-notion-blocker">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
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
