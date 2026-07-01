export function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const menuToggle = document.getElementById("menuToggle");
  const backButton = document.getElementById("backButton");
  const menuLabel = document.getElementById("menuLabel");

  function closeSidebar() {
    sidebar?.classList.remove("open");
  }

  function setContext(enabled) {
    sidebar?.classList.toggle("context", enabled);
    if (menuLabel) menuLabel.textContent = enabled ? "Fluxo operacional" : "Menu principal";
  }

  function selectFlowSubtab(subtab) {
    setContext(true);
    document.querySelector('[data-page="flows"]')?.click();
    document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
      button.classList.toggle("active", button.dataset.sidebarFlowSubtab === subtab)
    );
    setTimeout(() =>
      document.querySelector(`#flowsCurrentActions [data-flow-subtab="${subtab}"]`)?.click()
    );
  }

  function setSidebarCollapsed(collapsed) {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    if (sidebarToggle) {
      sidebarToggle.textContent = collapsed ? "›" : "‹";
      sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
      sidebarToggle.setAttribute(
        "aria-label",
        collapsed ? "Expandir menu lateral" : "Recolher menu lateral"
      );
    }
    localStorage.setItem("manhwateca-sidebar-collapsed", String(collapsed));
  }

  menuToggle?.addEventListener("click", () =>
    sidebar?.classList.toggle("open")
  );

  sidebarToggle?.addEventListener("click", () =>
    setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed"))
  );

  backButton?.addEventListener("click", () => setContext(false));
  document.querySelector('[data-page="flows"]')?.addEventListener("click", () =>
    setContext(true)
  );
  document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
    button.addEventListener("click", () => selectFlowSubtab(button.dataset.sidebarFlowSubtab))
  );
  document.addEventListener("click", event => {
    const subtab = event.target.closest("[data-flow-subtab]");
    if (!subtab) return;
    document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
      button.classList.toggle("active", button.dataset.sidebarFlowSubtab === subtab.dataset.flowSubtab)
    );
  });

  setSidebarCollapsed(
    localStorage.getItem("manhwateca-sidebar-collapsed") === "true"
  );

  return { closeSidebar, setSidebarCollapsed };
}
