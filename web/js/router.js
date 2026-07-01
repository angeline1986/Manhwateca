import { pageMeta } from "./state/appState.js";

export function initRouter(options = {}) {
  const {
    defaultPage = "flows",
    onPageChange,
  } = options;

  function showPage(pageName, updateHash = true) {
    const page = pageMeta[pageName] ? pageName : "overview";
    const topbar = document.getElementById("topbar");
    topbar.classList.toggle("overview", page === "overview");
    topbar.classList.toggle("flows", page === "flows");
    document.getElementById("refresh").hidden = page !== "overview";
    document.querySelectorAll(".page").forEach(section =>
      section.classList.toggle("active", section.id === `page-${page}`)
    );
    document.querySelectorAll("[data-page]").forEach(button =>
      button.classList.toggle("active", button.dataset.page === page)
    );
    document.getElementById("pageEyebrow").textContent = pageMeta[page].eyebrow;
    document.getElementById("pageTitle").textContent = pageMeta[page].title;
    document.getElementById("pageSubtitle").textContent = pageMeta[page].subtitle;
    if (updateHash) history.replaceState(null, "", `#${page}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (onPageChange) onPageChange(page);
  }

  document.querySelectorAll("[data-page]").forEach(button =>
    button.addEventListener("click", () => showPage(button.dataset.page))
  );

  showPage(location.hash.replace("#", "") || defaultPage, false);

  return { showPage };
}
