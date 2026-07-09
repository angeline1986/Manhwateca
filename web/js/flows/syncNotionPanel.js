import { escapeHtml } from "../utils/html.js";

const STATE_COPY = {
  synced: {
    title: "Tudo sincronizado",
    tone: "ok",
    lead: "Nenhuma ação necessária no momento.",
  },
  paused: {
    title: "Alterações detectadas",
    tone: "info",
    lead: "Existem alterações identificadas para acompanhamento. A aplicação automática ainda não está ativa neste fluxo.",
  },
  blocked: {
    title: "Sincronização pausada",
    tone: "warning",
    lead: "Resolva os itens abaixo antes de continuar.",
  },
  error: {
    title: "Erro ao verificar Notion",
    tone: "bad",
    lead: "Não foi possível verificar o estado. Tente novamente.",
  },
};

const EVIDENCE_COPY = {
  legacy_report: {
    title: "Estado do Notion não validado no fluxo oficial",
    tone: "warning",
    lead: "A informação disponível vem de um relatório legado salvo.",
    note: "A sincronização real ainda não foi verificada nesta etapa.",
    nextAction: "Validar pelo fluxo oficial",
  },
  local_postgresql: {
    title: "Estado local sem pendências",
    tone: "info",
    lead: "Este estado foi calculado a partir do PostgreSQL local.",
    note: "Ele não representa uma validação real do Notion.",
  },
  notion_live_check: {
    title: "Notion verificado",
    tone: "ok",
    lead: "O estado foi verificado diretamente no Notion em modo somente leitura.",
  },
  notion_apply_result: {
    title: "Sincronização aplicada",
    tone: "ok",
    lead: "A última execução registrou aplicação real no Notion.",
  },
  unavailable: {
    title: "Estado do Notion indisponível",
    tone: "info",
    lead: "Ainda não há uma verificação estruturada para esta etapa.",
  },
};

const NEXT_ACTION_LABELS = {
  none: "Nenhuma ação necessária",
  apply: "Acompanhar alterações detectadas",
  review_duplicates: "Revisar páginas duplicadas",
  review_missing: "Revisar páginas ausentes",
  review_blockers: "Revisar bloqueios",
  retry: "Verificar novamente",
};

const BLOCKER_LABELS = {
  api_error: "Erro de comunicação",
  duplicate_page: "Página duplicada",
  missing_page: "Página ausente",
};

export function renderSyncNotionPanel(metadata) {
  const sync = metadata?.sync;
  if (!sync) return unavailablePanel();
  const copy = panelCopy(sync);
  const blockers = Array.isArray(sync.blockers) ? sync.blockers : [];
  return `
    <section class="sync-notion-panel sync-notion-panel--${escapeHtml(copy.tone)}">
      <header class="sync-notion-header">
        <span class="sync-notion-status-dot" aria-hidden="true"></span>
        <div>
          <h3>${escapeHtml(copy.title)}</h3>
          <p>${escapeHtml(copy.lead)}</p>
        </div>
      </header>
      ${copy.note ? evidenceNote(copy.note) : ""}
      <div class="flow-subgrid sync-notion-metrics">
        ${metric("Atualizações", sync.updated_count)}
        ${metric("Sem alteração", sync.unchanged_count)}
        ${metric("Ausentes", sync.missing_count)}
        ${metric("Duplicadas", sync.duplicate_count)}
      </div>
      <article class="sync-notion-next-action">
        <strong>Próxima ação</strong>
        <span>${escapeHtml(copy.nextAction || nextActionLabel(sync.next_action))}</span>
      </article>
      ${blockers.length ? blockersList(blockers) : noBlockers()}
      <footer class="sync-notion-footer">
        Última verificação: ${escapeHtml(formatTimestamp(metadata.updated_at))}
      </footer>
    </section>
  `;
}

function panelCopy(sync) {
  if (sync.evidence && EVIDENCE_COPY[sync.evidence]) {
    return EVIDENCE_COPY[sync.evidence];
  }
  return STATE_COPY[sync.status] || EVIDENCE_COPY.unavailable;
}

function unavailablePanel() {
  return `
    <section class="sync-notion-panel sync-notion-panel--info">
      <header class="sync-notion-header">
        <span class="sync-notion-status-dot" aria-hidden="true"></span>
        <div>
          <h3>Estado do Notion indisponível</h3>
          <p>Ainda não há uma verificação estruturada para esta etapa.</p>
        </div>
      </header>
      <article class="sync-notion-next-action">
        <strong>Próxima ação</strong>
        <span>Atualize o estado quando houver uma nova verificação disponível.</span>
      </article>
    </section>
  `;
}

function metric(label, value) {
  return `
    <article class="flow-metric-card">
      <strong>${escapeHtml(String(Number(value || 0)))}</strong>
      <span>${escapeHtml(label)}</span>
    </article>
  `;
}

function evidenceNote(text) {
  return `
    <div class="flow-panel-note sync-notion-clear">
      ${escapeHtml(text)}
    </div>
  `;
}

function blockersList(blockers) {
  return `
    <div class="sync-notion-blockers">
      <h4>O que impede a sincronização</h4>
      <div class="sync-notion-blocker-list">
        ${blockers.map(blockerItem).join("")}
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

function noBlockers() {
  return `
    <div class="flow-panel-note sync-notion-clear">
      Nenhum bloqueio identificado na última verificação.
    </div>
  `;
}

function nextActionLabel(action) {
  return NEXT_ACTION_LABELS[action] || NEXT_ACTION_LABELS.review_blockers;
}

function blockerLabel(code) {
  return BLOCKER_LABELS[code] || "Bloqueio identificado";
}

function formatTimestamp(value) {
  if (!value) return "não disponível";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
