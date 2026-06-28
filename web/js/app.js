/* ==========================================================================
   APP ENTRY POINT - Manhwateca Rose Edition
   ========================================================================== */

import { initRouter, navigateTo } from './router.js';
import { setupSidebar } from './ui/sidebar.js';

// Elementos Globais
const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const refreshButton = document.getElementById("refresh");

/**
 * Inicialização Global
 */
async function init() {
  console.log("🚀 Manhwateca Workspace: Iniciando módulos...");

  // 1. Configura a Sidebar (Toggle, Persistência de estado)
  setupSidebar();

  // 2. Configura o Botão de Menu Mobile
  menuToggle?.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  // 3. Configura os links de navegação
  document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => {
      const page = button.dataset.page;
      navigateTo(page);
    });
  });

  // 4. Inicializa o Roteador (Carrega a página inicial baseada no Hash)
  initRouter();

  // 5. Configura o botão de Refresh da Dashboard (se houver lógica global)
  refreshButton?.addEventListener("click", () => {
    // Dispara um evento customizado que a página de Overview pode escutar
    window.dispatchEvent(new CustomEvent('dash:refresh'));
  });
  
  console.log("✅ Sistema pronto.");
}

// Inicia a aplicação quando o DOM estiver pronto
document.addEventListener("DOMContentLoaded", init);

/**
 * Utilitários Globais
 * Podem ser acessados por outros módulos se necessário
 */
export const ui = {
  // Exemplo: Mostrar/Esconder o botão de refresh da topbar
  toggleRefreshAction(show) {
    if (refreshButton) refreshButton.hidden = !show;
  },
  
  // Atualiza as informações da Topbar
  updateTopbar(eyebrow, title, subtitle) {
    document.getElementById("pageEyebrow").textContent = eyebrow;
    document.getElementById("pageTitle").textContent = title;
    document.getElementById("pageSubtitle").textContent = subtitle;
  }
};