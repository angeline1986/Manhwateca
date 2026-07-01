export function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const menuToggle = document.getElementById("menuToggle");

  function closeSidebar() {
    sidebar?.classList.remove("open");
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

  setSidebarCollapsed(
    localStorage.getItem("manhwateca-sidebar-collapsed") === "true"
  );

  return { closeSidebar, setSidebarCollapsed };
}
