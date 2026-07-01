import { getJson } from "../api/client.js";
import { escapeHtml } from "../utils/html.js";

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

function pendingKindLabel(kind) {
  return {
    catalog: "Catálogo",
    csv: "CSV",
    mangaupdates: "MangaUpdates",
    notion: "Notion",
  }[kind] || "Ação";
}

export function initOverviewPage(elements) {
  function setPendingLists(html) {
    if (elements.pendingList) elements.pendingList.innerHTML = html;
    if (elements.organizationPendingList) {
      elements.organizationPendingList.innerHTML = html;
    }
  }

  async function loadPendingActions() {
    const { response, payload } = await getJson("/api/pending");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!payload.items.length) {
      setPendingLists(`
        <article class="pending-card success">
          <strong>Tudo em dia</strong>
          <span>${escapeHtml(payload.empty_message || "Nenhuma pendência acionável encontrada.")}</span>
        </article>
      `);
      return;
    }
    setPendingLists(payload.items.map(item => `
      <button type="button"
              class="pending-card ${escapeHtml(item.severity || "info")}"
              ${item.action ? `data-action="${escapeHtml(item.action)}"` : ""}
              ${item.page ? `data-pending-page="${escapeHtml(item.page)}"` : ""}
              ${item.panel ? `data-pending-panel="${escapeHtml(item.panel)}"` : ""}>
        <span class="pending-kind">${escapeHtml(pendingKindLabel(item.kind))}</span>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail)}</span>
        <em>${escapeHtml(item.action ? "Executar próxima etapa" : "Abrir seção")}</em>
      </button>
    `).join(""));
  }

  async function loadStatus() {
    elements.grid.innerHTML = '<article class="status-card loading">Consultando o ambiente...</article>';
    setPendingLists('<article class="pending-card loading">Calculando pendências...</article>');
    elements.refreshButton.disabled = true;
    try {
      const { response, payload: data } = await getJson("/api/status");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const catalogSourceInfo = data.catalog.source || {};
      const catalogSourceLabel = catalogSourceInfo.label || "fonte local";
      const catalogDetail = catalogSourceInfo.detail
        ? ` Fonte: ${catalogSourceLabel} (${catalogSourceInfo.detail}).`
        : ` Fonte: ${catalogSourceLabel}.`;
      const fallbackDetail = catalogSourceInfo.fallback_reason
        ? ` Usando fallback porque: ${catalogSourceInfo.fallback_reason}`
        : "";
      elements.grid.innerHTML = [
        card(
          "Catálogo local",
          `${data.catalog.count} obra(s) catalogadas.${catalogDetail}${fallbackDetail}`,
          data.catalog.available,
          catalogSourceInfo.kind === "postgresql" ? "Banco ativo" : undefined
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
            ? "Dados externos enriquecidos estão disponíveis."
            : "Ainda faltam dados externos enriquecidos no catálogo.",
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
      elements.grid.innerHTML = card(
        "Falha ao consultar status",
        error.message,
        false,
        "Servidor indisponível"
      );
      setPendingLists(`
        <article class="pending-card warning">
          <strong>Não foi possível calcular pendências</strong>
          <span>${escapeHtml(error.message)}</span>
        </article>
      `);
    } finally {
      elements.refreshButton.disabled = false;
    }
  }

  async function loadDiagnostics() {
    elements.refreshDiagnostics.disabled = true;
    try {
      const { payload: data } = await getJson("/api/diagnostics");
      elements.diagnosticGrid.innerHTML = data.checks.map(check => `
        <article class="diagnostic-item ${check.ok ? "ok" : "warn"}">
          <strong>${escapeHtml(check.name)}</strong>
          <span>${escapeHtml(check.detail)}</span>
        </article>
      `).join("");
    } finally {
      elements.refreshDiagnostics.disabled = false;
    }
  }

  elements.refreshButton?.addEventListener("click", loadStatus);
  elements.refreshDiagnostics?.addEventListener("click", loadDiagnostics);

  return { loadStatus, loadDiagnostics, loadPendingActions };
}
