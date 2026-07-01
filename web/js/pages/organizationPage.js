import { catalogOne, reconcileAliases } from "../api/libraryApi.js";
import { escapeHtml } from "../utils/html.js";

export function initOrganizationPage({
  elements,
  getNotionUncataloged,
  loadCatalog,
  loadNotionStatus,
  loadPendingActions,
  startTask,
}) {
  let catalogPendingItems = [];
  let catalogPendingPage = 1;
  const catalogPendingPageSize = 8;

  function renderCatalogPending(data) {
    if (!elements.organizationCatalogPendingList) return;
    catalogPendingItems = Array.isArray(data.uncataloged) ? data.uncataloged : [];
    catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
    renderCatalogPendingPage();
  }

  function clampCatalogPendingPage(page) {
    const totalPages = Math.max(1, Math.ceil(catalogPendingItems.length / catalogPendingPageSize));
    return Math.min(Math.max(1, page || 1), totalPages);
  }

  function renderCatalogPendingPage() {
    const items = catalogPendingItems;
    if (elements.catalogPendingCount) {
      elements.catalogPendingCount.textContent = `${items.length} pendente${items.length === 1 ? "" : "s"}`;
    }
    if (elements.catalogAllPending) {
      elements.catalogAllPending.disabled = !items.length;
    }
    if (elements.catalogPendingMeta) {
      const now = new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      });
      elements.catalogPendingMeta.textContent = `Sincronizado pela última vez às ${now}.`;
    }
    if (!items.length) {
      elements.organizationCatalogPendingList.innerHTML = '<p class="empty">Nenhuma obra fora do catálogo.</p>';
      return;
    }
    catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
    const totalPages = Math.max(1, Math.ceil(items.length / catalogPendingPageSize));
    const start = (catalogPendingPage - 1) * catalogPendingPageSize;
    const pageItems = items.slice(start, start + catalogPendingPageSize);
    elements.organizationCatalogPendingList.innerHTML = `
      <div class="catalog-pending-row catalog-pending-head">
        <span>Nome da pasta no Drive</span>
        <span>Ações</span>
      </div>
      ${pageItems.map(item => `
        <div class="catalog-pending-row">
          <strong>${escapeHtml(item)}</strong>
          <span class="catalog-pending-action">
            <button type="button" data-catalog-one="${escapeHtml(item)}">Catalogar</button>
            <small aria-live="polite"></small>
          </span>
        </div>
      `).join("")}
      <div class="catalog-pending-footer">
        <span>Mostrando ${start + 1}-${Math.min(start + catalogPendingPageSize, items.length)} de ${items.length}</span>
        <span class="catalog-pending-pages">
          ${renderCatalogPendingPagination(totalPages)}
        </span>
      </div>
    `;
  }

  function renderCatalogPendingPagination(totalPages) {
    const pages = new Set([1, totalPages, catalogPendingPage]);
    if (catalogPendingPage > 1) pages.add(catalogPendingPage - 1);
    if (catalogPendingPage < totalPages) pages.add(catalogPendingPage + 1);
    const ordered = [...pages].sort((a, b) => a - b);
    const controls = [
      `<button type="button" class="page-arrow" data-catalog-page="prev" ${catalogPendingPage === 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>`,
    ];
    let previous = 0;
    for (const page of ordered) {
      if (page - previous > 1) {
        controls.push('<span class="page-ellipsis">...</span>');
      }
      controls.push(
        page === catalogPendingPage
          ? `<strong>${page}</strong>`
          : `<button type="button" data-catalog-page="${page}">${page}</button>`
      );
      previous = page;
    }
    controls.push(
      `<button type="button" class="page-arrow" data-catalog-page="next" ${catalogPendingPage === totalPages ? "disabled" : ""} aria-label="Próxima página">›</button>`
    );
    return controls.join("");
  }

  elements.catalogAllPending?.addEventListener("click", () => {
    if (!getNotionUncataloged()) return;
    startTask("catalog_scan", true);
  });

  elements.refreshCatalogPending?.addEventListener("click", async () => {
    elements.refreshCatalogPending.disabled = true;
    elements.refreshCatalogPending.classList.add("spinning");
    try {
      await reconcileAliases();
      await Promise.all([loadNotionStatus(), loadPendingActions()]);
    } finally {
      elements.refreshCatalogPending.disabled = false;
      elements.refreshCatalogPending.classList.remove("spinning");
    }
  });

  if (elements.organizationCatalogPendingList) {
    elements.organizationCatalogPendingList.addEventListener("click", async event => {
      const pageButton = event.target.closest("[data-catalog-page]");
      if (pageButton) {
        const target = pageButton.dataset.catalogPage;
        if (target === "next") {
          catalogPendingPage += 1;
        } else if (target === "prev") {
          catalogPendingPage -= 1;
        } else {
          catalogPendingPage = Number.parseInt(target, 10) || catalogPendingPage;
        }
        catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
        renderCatalogPendingPage();
        return;
      }

      const button = event.target.closest("[data-catalog-one]");
      if (!button) return;
      const name = button.dataset.catalogOne;
      const row = button.closest(".catalog-pending-row");
      const feedback = button.parentElement?.querySelector("small");
      button.disabled = true;
      button.textContent = "Catalogando...";
      if (feedback) {
        feedback.textContent = "Salvando no PostgreSQL...";
        feedback.className = "";
      }
      try {
        const { response, payload } = await catalogOne({ name });
        if (!response.ok) {
          if (feedback) {
            feedback.textContent = payload.error || "Não foi possível catalogar.";
            feedback.className = "error";
          } else {
            window.alert(payload.error || "Não foi possível catalogar a obra.");
          }
          button.disabled = false;
          button.textContent = "Tentar novamente";
          return;
        }
        if (feedback) {
          feedback.textContent = "Catalogada.";
          feedback.className = "success";
        }
        button.textContent = "Catalogada";
        catalogPendingItems = catalogPendingItems.filter(item => item !== name);
        if (row) row.classList.add("catalog-pending-row-done");
        window.setTimeout(() => {
          catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
          renderCatalogPendingPage();
        }, 650);
        await Promise.all([loadCatalog(), loadNotionStatus(), loadPendingActions()]);
      } finally {
        if (button.textContent !== "Catalogada" && button.textContent !== "Tentar novamente") {
          button.disabled = false;
          button.textContent = "Catalogar";
        }
      }
    });
  }

  return { renderCatalogPending };
}
