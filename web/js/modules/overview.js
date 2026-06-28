/* ==========================================================================
   DASHBOARD (OVERVIEW) MODULE
   ========================================================================== */

// Seletores de elementos (serão preenchidos no init)
let grid, pendingList;

/**
 * Helper: Escapa HTML para segurança
 */
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[char]);
}

/**
 * Helper: Gera o HTML de um card de status
 */
function renderStatusCard(title, detail, available, label) {
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

/**
 * Carrega o status geral do sistema
 */
async function loadStatus() {
  if (!grid) return;
  grid.innerHTML = '<article class="status-card loading">Consultando o ambiente...</article>';
  
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    const catalogSourceInfo = data.catalog.source || {};
    const catalogDetail = catalogSourceInfo.detail
      ? ` Fonte: ${catalogSourceInfo.label} (${catalogSourceInfo.detail}).`
      : ` Fonte: ${catalogSourceInfo.label || "local"}.`;

    grid.innerHTML = [
      renderStatusCard(
        "Catálogo local",
        `${data.catalog.count} obra(s) catalogadas.${catalogDetail}`,
        data.catalog.available,
        catalogSourceInfo.kind === "postgresql" ? "Banco ativo" : undefined
      ),
      renderStatusCard(
        "Biblioteca no Drive",
        data.library.configured
          ? "O diretório configurado está acessível para leitura e organização."
          : "Configure MANGA_ROOT no arquivo .env.",
        data.library.available
      ),
      renderStatusCard(
        "MangaUpdates",
        data.mangaupdates.cache_available
          ? "Dados externos enriquecidos estão disponíveis."
          : "Faltam dados externos no catálogo.",
        data.mangaupdates.cache_available
      ),
      renderStatusCard(
        "Notion",
        data.notion.configured
          ? "Credenciais disponíveis para sincronização."
          : "Configure token e database no .env.",
        data.notion.configured,
        data.notion.configured ? "Configurado" : "Não configurado"
      ),
    ].join("");
  } catch (error) {
    grid.innerHTML = renderStatusCard("Falha no status", error.message, false, "Erro");
  }
}

/**
 * Carrega a lista de pendências acionáveis
 */
async function loadPendingActions() {
  if (!pendingList) return;
  pendingList.innerHTML = '<article class="pending-card loading">Calculando pendências...</article>';

  try {
    const response = await fetch("/api/pending", { cache: "no-store" });
    const payload = await response.json();

    if (!payload.items.length) {
      pendingList.innerHTML = `
        <article class="pending-card success">
          <strong>Tudo em dia</strong>
          <span>${escapeHtml(payload.empty_message || "Nenhuma pendência encontrada.")}</span>
        </article>
      `;
      return;
    }

    pendingList.innerHTML = payload.items.map(item => `
      <button type="button"
              class="pending-card ${escapeHtml(item.severity || "info")}"
              data-action="${escapeHtml(item.action || "")}"
              data-page="${escapeHtml(item.page || "")}"
              data-panel="${escapeHtml(item.panel || "")}">
        <span class="pending-kind">${escapeHtml(item.kind || "Ação")}</span>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail)}</span>
        <em>${item.action ? "Executar próxima etapa" : "Abrir seção"}</em>
      </button>
    `).join("");
  } catch (error) {
    pendingList.innerHTML = `<p class="empty">Erro ao carregar pendências: ${error.message}</p>`;
  }
}

/**
 * Função de inicialização chamada pelo Router
 */
export function init() {
  grid = document.getElementById("statusGrid");
  pendingList = document.getElementById("pendingList");

  // Carrega os dados iniciais
  loadStatus();
  loadPendingActions();

  // Escuta o evento de refresh disparado pelo app.js
  window.addEventListener('dash:refresh', () => {
    loadStatus();
    loadPendingActions();
  }, { once: false });

  // Delegação de evento para os cards de pendência
  pendingList?.addEventListener("click", (e) => {
    const card = e.target.closest(".pending-card");
    if (!card) return;

    const { action, page, panel } = card.dataset;
    
    // Se tiver uma página alvo, usa o roteador para navegar
    if (page) {
      import('../router.js').then(router => {
        router.navigateTo(page);
        // Lógica opcional para abrir painel específico pode ser adicionada aqui
      });
    }
  });
}