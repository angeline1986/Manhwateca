/* ==========================================================================
   SIDEBAR UI COMPONENT
   ========================================================================== */

/**
 * Altera o estado do menu entre expandido e recolhido (Desktop)
 * @param {boolean} collapsed 
 */
function setSidebarCollapsed(collapsed) {
  const sidebarToggle = document.getElementById("sidebarToggle");
  
  // Aplica a classe ao body para que o CSS (sidebar.css) reaja
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  
  if (sidebarToggle) {
    // Atualiza o ícone visual
    sidebarToggle.textContent = collapsed ? "›" : "‹";
    
    // Atualiza atributos de acessibilidade
    sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
    sidebarToggle.setAttribute(
      "aria-label", 
      collapsed ? "Expandir menu lateral" : "Recolher menu lateral"
    );
  }
  
  // Persiste a escolha do usuário
  localStorage.setItem("manhwateca-sidebar-collapsed", String(collapsed));
}

/**
 * Inicializa os ouvintes de evento e recupera o estado salvo
 */
export function setupSidebar() {
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");

  // 1. Evento de clique para o Toggle (Desktop)
  sidebarToggle?.addEventListener("click", () => {
    const isCurrentlyCollapsed = document.body.classList.contains("sidebar-collapsed");
    setSidebarCollapsed(!isCurrentlyCollapsed);
  });

  // 2. Recupera estado do localStorage ao carregar
  const savedState = localStorage.getItem("manhwateca-sidebar-collapsed") === "true";
  setSidebarCollapsed(savedState);

  // 3. Fecha o menu mobile automaticamente ao clicar em um link
  // (Opcional, melhora a UX em telas pequenas)
  sidebar?.addEventListener("click", (event) => {
    if (event.target.closest(".nav-link") && window.innerWidth <= 820) {
      sidebar.classList.remove("open");
    }
  });
}