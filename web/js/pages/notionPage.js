import { getMetadataStatus, getNotionStatus } from "../api/notionApi.js";
import { summaryCard } from "../components/summaryCard.js";
import { escapeHtml } from "../utils/html.js";

export function initNotionPage({ elements, showPage, onCatalogPendingData }) {
  let notionUncataloged = 0;
  let notionStatusStale = false;

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
    elements.refreshNotion.disabled = true;
    try {
      const { payload: data } = await getNotionStatus();
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
      elements.notionSummary.innerHTML = [
        summaryCard("Biblioteca no Drive", data.summary.library),
        summaryCard("Catálogo", data.summary.current_catalog),
        summaryCard("Importadas", data.summary.imported),
        summaryCard("Pendentes", data.summary.pending),
        summaryCard("Não catalogadas", data.summary.uncataloged),
      ].join("");
      elements.notionMeta.innerHTML = data.available
        ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
           <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>`
        : `<span>${escapeHtml(data.error || "Execute uma simulação para gerar o status.")}</span>`;
      elements.notionLists.innerHTML = [
        notionList("Último lote", data.current_batch),
        notionList("Não catalogadas", data.uncataloged, "warning"),
        notionList("Pendentes", data.pending, "warning"),
        notionList("Duplicadas", data.duplicates, "danger"),
      ].join("");
      if (onCatalogPendingData) onCatalogPendingData(data);
      renderNotionSyncStatus(data);
    } finally {
      elements.refreshNotion.disabled = false;
    }
  }

  function renderNotionSyncStatus(data) {
    const pending = data.summary.pending;
    const uncataloged = data.summary.uncataloged;
    notionUncataloged = uncataloged;
    notionStatusStale = Boolean(data.stale);
    updateNotionActionAvailability();
    const title = elements.notionSyncStatus.querySelector("strong");
    const detail = elements.notionSyncStatus.querySelector("small");
    elements.notionSyncStatus.classList.remove("ok", "warning", "unavailable");
    if (!data.available) {
      elements.notionSyncStatus.classList.add("unavailable");
      title.textContent = "Situação das importações ainda não verificada";
      detail.textContent = "Execute “Simular próximo lote” para comparar o catálogo com o Notion.";
      return;
    }
    if (uncataloged > 0) {
      elements.notionSyncStatus.classList.add("warning");
      title.textContent = `${uncataloged} obra${uncataloged === 1 ? "" : "s"} do Drive ainda não ${uncataloged === 1 ? "foi catalogada" : "foram catalogadas"}`;
      detail.textContent = "Execute “Catalogar biblioteca”. Depois simule o próximo lote do Notion.";
      return;
    }
    if (data.stale) {
      elements.notionSyncStatus.classList.add("warning");
      title.textContent = "O catálogo mudou desde a última verificação do Notion";
      detail.textContent = `O último status avaliou ${data.summary.catalog} obras; o catálogo atual possui ${data.summary.current_catalog}. Execute “Simular próximo lote”.`;
      return;
    }
    if (pending > 0) {
      elements.notionSyncStatus.classList.add("warning");
      title.textContent = `${pending} obra${pending === 1 ? "" : "s"} ainda não ${pending === 1 ? "foi incluída" : "foram incluídas"} no Notion`;
      detail.textContent = String(data.mode || "").includes("SIMULAÇÃO")
        ? "A simulação apenas identificou as páginas. Execute “Importar próximo lote” e confirme a operação."
        : `Status da última verificação: ${data.updated_at || "data não informada"}.`;
      return;
    }
    elements.notionSyncStatus.classList.add("ok");
    title.textContent = "Todas as obras catalogadas estão no Notion";
    detail.textContent = `Nenhuma inclusão pendente na última verificação${data.updated_at ? ` de ${data.updated_at}` : ""}.`;
  }

  function updateNotionActionAvailability() {
    ["notion_simulate_batch", "notion_apply_batch"].forEach(action => {
      const button = elements.notionActionGrid.querySelector(`[data-action="${action}"]`);
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

  function renderMetadataUpdates(updates) {
    elements.metadataUpdates.innerHTML = updates.length ? `
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
    elements.refreshMetadata.disabled = true;
    try {
      const { payload: data } = await getMetadataStatus();
      elements.metadataSummary.innerHTML = [
        summaryCard("Atualizações", data.summary.updates),
        summaryCard("Sem alteração", data.summary.unchanged),
        summaryCard("Ausentes", data.summary.missing),
        summaryCard("Duplicadas", data.summary.duplicates),
        summaryCard("CSV disponível", data.csv_available ? "Sim" : "Não"),
      ].join("");
      elements.metadataMeta.innerHTML = data.available
        ? `<strong>${escapeHtml(data.mode || "Status")}</strong>
           <span>Atualizado em ${escapeHtml(data.updated_at || "-")}</span>
           ${renderSyncStateSummary(data.sync_state)}`
        : `<span>${escapeHtml(data.error || "Execute a simulação dos metadados.")}</span>`;
      renderMetadataUpdates(data.updates);
      elements.metadataAlerts.innerHTML = [
        notionList("Ausentes no Notion", data.missing, "warning"),
        notionList("Duplicadas", data.duplicates, "danger"),
      ].join("");
    } finally {
      elements.refreshMetadata.disabled = false;
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

  elements.notionSyncStatus.addEventListener("click", () => {
    if (notionUncataloged > 0) {
      showPage("organization");
      window.setTimeout(() => {
        const catalogButton = elements.actionGrid.querySelector('[data-action="catalog_scan"]');
        catalogButton?.scrollIntoView({ behavior: "smooth", block: "center" });
        catalogButton?.classList.add("task-highlight");
        window.setTimeout(
          () => catalogButton?.classList.remove("task-highlight"),
          1800,
        );
      }, 120);
    } else {
      elements.notionCatalogPanel.open = true;
      elements.notionCatalogPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  elements.refreshNotion.addEventListener("click", loadNotionStatus);
  elements.refreshMetadata.addEventListener("click", loadMetadataStatus);

  return {
    getNotionUncataloged: () => notionUncataloged,
    loadMetadataStatus,
    loadNotionStatus,
  };
}
