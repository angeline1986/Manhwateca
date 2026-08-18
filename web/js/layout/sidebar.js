export function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const menuToggle = document.getElementById("menuToggle");
  const backButton = document.getElementById("backButton");
  const menuLabel = document.getElementById("menuLabel");
  const organizationPageButton = document.querySelector('[data-page="organization-v2"]');
  let openingOrganizationSubtab = false;

  function closeSidebar() {
    sidebar?.classList.remove("open");
  }

  function setContext(context) {
    const enabled = Boolean(context);
    sidebar?.classList.toggle("context", enabled);
    sidebar?.classList.toggle("flow-context", context === "flows");
    sidebar?.classList.toggle("organization-context", context === "organization");
    if (menuLabel) {
      if (context === "flows") menuLabel.textContent = "Fluxo operacional";
      else if (context === "organization") menuLabel.textContent = "Organização";
      else menuLabel.textContent = "Menu principal";
    }
  }

  function markOrganizationSubtab(subtab) {
    document.querySelectorAll("[data-sidebar-organization-subtab]").forEach(button =>
      button.classList.toggle(
        "active",
        button.dataset.sidebarOrganizationSubtab === subtab
      )
    );
  }

  function emitOrganizationSubtab(subtab) {
    window.dispatchEvent(new CustomEvent(
      "manhwateca:organization-subtab",
      { detail: { subtab } }
    ));
  }

  function selectFlowSubtab(subtab) {
    setContext("flows");
    document.querySelector('[data-page="flows"]')?.click();
    document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
      button.classList.toggle("active", button.dataset.sidebarFlowSubtab === subtab)
    );
    window.dispatchEvent(new CustomEvent("manhwateca:flow-subtab", { detail: { subtab } }));
  }

  function selectOrganizationSubtab(subtab) {
    setContext("organization");
    markOrganizationSubtab(subtab);
    openingOrganizationSubtab = true;
    organizationPageButton?.click();
    openingOrganizationSubtab = false;
    emitOrganizationSubtab(subtab);
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

  backButton?.addEventListener("click", () => setContext(null));

  document.querySelector('[data-page="flows"]')?.addEventListener("click", () =>
    setContext("flows")
  );

  organizationPageButton?.addEventListener("click", () => {
    setContext("organization");
    if (openingOrganizationSubtab) return;

    const subtab = "track_library";
    markOrganizationSubtab(subtab);
    queueMicrotask(() => emitOrganizationSubtab(subtab));
  });

  document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
    button.addEventListener("click", () =>
      selectFlowSubtab(button.dataset.sidebarFlowSubtab)
    )
  );

  document.querySelectorAll("[data-sidebar-organization-subtab]").forEach(button =>
    button.addEventListener("click", () =>
      selectOrganizationSubtab(button.dataset.sidebarOrganizationSubtab)
    )
  );

  document.addEventListener("click", event => {
    const subtab = event.target.closest("[data-flow-subtab]");
    if (!subtab) return;
    document.querySelectorAll("[data-sidebar-flow-subtab]").forEach(button =>
      button.classList.toggle(
        "active",
        button.dataset.sidebarFlowSubtab === subtab.dataset.flowSubtab
      )
    );
  });

  setSidebarCollapsed(
    localStorage.getItem("manhwateca-sidebar-collapsed") === "true"
  );

  return { closeSidebar, setSidebarCollapsed };
}
