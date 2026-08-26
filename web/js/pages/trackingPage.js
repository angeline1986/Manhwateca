import {
  checkReleaseWork,
  checkReleases,
  getReleaseSubscriptions,
  getReleases,
  updateReleaseFavorite,
} from "../api/releasesApi.js";
import { getTasks } from "../api/tasksApi.js";
import { escapeHtml } from "../utils/html.js";

const DAY_OPTIONS = [1, 7, 15, 30, 45, 60];

export function initTrackingPage(elements) {
  let days = 15;
  let subscriptions = [];
  let releases = [];
  let selectedMangaId = null;
  let history = [];
  let historyExpanded = false;

  renderHeader();

  async function loadTracking() {
    await loadSubscriptions();
    await loadReleases();
    renderWorks();
    await loadSelectedHistory();
  }

  async function loadSubscriptions() {
    const { response, payload } = await getReleaseSubscriptions();
    if (!response.ok) throw new Error(payload?.error || "Não foi possível carregar obras.");
    subscriptions = Array.isArray(payload.items) ? payload.items : [];
    if (!selectedMangaId && subscriptions.length) selectedMangaId = subscriptions[0].manga_id;
    renderHeader();
  }

  async function loadReleases() {
    const search = elements.releaseSearch?.value || "";
    const unseen = Boolean(elements.unseenOnly?.checked);
    const { response, payload } = await getReleases({
      days,
      search,
      unseen_only: unseen ? "true" : "",
      per_page: 100,
    });
    if (!response.ok) throw new Error(payload?.error || "Não foi possível carregar lançamentos.");
    releases = Array.isArray(payload.items) ? payload.items : [];
    renderReleaseSummary(payload);
    renderReleaseTable();
    renderWorks();
  }

  function renderHeader() {
    const favorites = subscriptions.filter(item => item.favorite).length;
    const monitored = subscriptions.filter(isMonitored);
    elements.worksCount.textContent = String(monitored.length);
    elements.favoriteCount.textContent = String(favorites);
    if (elements.topbarMeta) {
      elements.topbarMeta.innerHTML = `
        <article class="status-minimalist tracking-topbar-meta">
          <span>Última verificação</span>
          <strong>${escapeHtml(latestCheckedAt(monitored))}</strong>
          <small>${monitored.length} obras monitoradas</small>
        </article>
      `;
    }
  }

  function renderReleaseSummary(payload) {
    elements.windowLabel.textContent = days === 1 ? "Hoje" : `Últimos ${days} dias`;
    elements.releaseCount.textContent = `${payload.total || 0} capítulos encontrados`;
    elements.updatedCount.textContent = String(updatedFavorites().size);
  }

  function renderReleaseTable() {
    const favoriteIds = favoriteMangaIds();
    const onlyFavorites = Boolean(elements.favoritesOnly?.checked);
    const items = onlyFavorites
      ? releases.filter(item => favoriteIds.has(Number(item.manga_id)))
      : releases;
    if (!items.length) {
      elements.releaseList.innerHTML = '<tr><td colspan="5">Nenhum capítulo encontrado nesta janela.</td></tr>';
      return;
    }
    elements.releaseList.innerHTML = items.map(item => `
      <tr>
        <td>${escapeHtml(item.title || "")}</td>
        <td>${escapeHtml(item.chapter || "")}</td>
        <td>${escapeHtml(dateOnly(item.release_date))}</td>
        <td>${escapeHtml(item.release_group || "-")}</td>
        <td><span class="state ${item.viewed_at ? "ok" : "warn"}">${escapeHtml(item.status)}</span></td>
      </tr>
    `).join("");
  }

  function renderWorks() {
    renderHeader();
    const items = filteredWorks();
    if (!items.some(item => item.manga_id === selectedMangaId)) {
      selectedMangaId = items[0]?.manga_id || subscriptions[0]?.manga_id || null;
    }
    elements.workList.innerHTML = items.length ? items.map(item => `
      <article class="tracking-work-item ${item.manga_id === selectedMangaId ? "active" : ""}"
               data-tracking-work="${escapeHtml(item.manga_id)}"
               tabindex="0">
        <span>${starButton(item)}</span>
        <strong>${escapeHtml(item.title || "Obra sem título")}</strong>
      </article>
    `).join("") : '<div class="organization-empty-list">Nenhuma obra nesta seleção.</div>';
    renderDetail();
  }

  function renderDetail() {
    const item = subscriptions.find(work => work.manga_id === selectedMangaId);
    if (!item) {
      elements.detail.innerHTML = `
        <div class="organization-empty-detail">
          <span class="eyebrow">OBRA SELECIONADA</span>
          <h2>Nenhuma obra selecionada</h2>
          <p>Selecione uma obra monitorada para ver detalhes.</p>
        </div>
      `;
      return;
    }
    elements.detail.innerHTML = `
      <div class="tracking-detail-top">
        <div>
          <span class="eyebrow">OBRA SELECIONADA</span>
          <h2>${escapeHtml(item.title || "Obra sem título")}</h2>
        </div>
        ${starButton(item, "detail")}
      </div>
      <div class="tracking-detail-grid">
        <article><span>ÚLTIMO LANÇAMENTO</span><strong>${escapeHtml(latestReleaseLabel(item))}</strong></article>
        <article><span>ÚLTIMA VERIFICAÇÃO</span><strong>${escapeHtml(dateTime(item.last_checked_at, "Sem registro"))}</strong></article>
        <article><span>STATUS</span><strong>${item.monitored ? "Monitorada" : "Pausada"}</strong></article>
      </div>
      <section class="tracking-history">
        <h3>HISTÓRICO DE LANÇAMENTOS</h3>
        ${renderHistory(item)}
      </section>
      <section class="organization-action-bar">
        <div class="organization-action-copy">
          <small>PRÓXIMA AÇÃO</small>
          <strong>Verificar atualizações desta obra</strong>
          <p>Consulte agora se existem novos lançamentos.</p>
        </div>
        <div class="organization-actions">
          <button type="button" class="primary-action" data-tracking-check-work="${escapeHtml(item.manga_id)}">Verificar agora</button>
        </div>
      </section>
    `;
  }

  function renderHistory(item) {
    const rows = history.filter(row => Number(row.manga_id) === Number(item.manga_id));
    if (!rows.length) return '<p class="tracking-empty">Nenhum lançamento recente encontrado para esta obra.</p>';
    const visibleRows = historyExpanded ? rows : rows.slice(0, 5);
    const hiddenCount = Math.max(0, rows.length - visibleRows.length);
    return `
      <div class="tracking-history-list">
        ${visibleRows.map(row => `
          <article>
            <strong>Cap. ${escapeHtml(row.chapter || "-")}</strong>
            <span>${escapeHtml(dateOnly(row.release_date))}</span>
            <em>${escapeHtml(row.status || "")}</em>
          </article>
        `).join("")}
      </div>
      ${rows.length > 5 ? `
        <div class="tracking-history-actions">
          <button type="button" class="secondary-action tracking-history-toggle" data-tracking-history-toggle>
            ${historyExpanded ? "Ver menos" : `Ver mais (${hiddenCount})`}
          </button>
        </div>
      ` : ""}
    `;
  }

  async function loadSelectedHistory() {
    if (!selectedMangaId) return;
    const { response, payload } = await getReleases({ manga_id: selectedMangaId, days: 365, per_page: 20 });
    if (!response.ok) return;
    history = [
      ...history.filter(row => Number(row.manga_id) !== Number(selectedMangaId)),
      ...((payload.items || []).map(row => ({ ...row, manga_id: selectedMangaId }))),
    ];
    renderDetail();
  }

  async function toggleFavorite(mangaId) {
    const item = subscriptions.find(work => Number(work.manga_id) === Number(mangaId));
    if (!item) return;
    const next = !item.favorite;
    const { response, payload } = await updateReleaseFavorite({ manga_id: mangaId, favorite: next });
    if (!response.ok) throw new Error(payload?.error || "Não foi possível atualizar favorita.");
    item.favorite = Boolean(payload.favorite);
    renderReleaseTable();
    renderWorks();
  }

  async function checkAll() {
    elements.checkAll.disabled = true;
    elements.checkAll.textContent = "Verificando...";
    try {
      const { payload } = await checkReleases();
      await waitForTask(payload?.id);
      await loadTracking();
    } finally {
      elements.checkAll.disabled = false;
      elements.checkAll.textContent = "Verificar agora";
    }
  }

  async function checkWork(mangaId, button) {
    button.disabled = true;
    button.textContent = "Verificando...";
    try {
      const { payload } = await checkReleaseWork(mangaId);
      await waitForTask(payload?.id);
      await loadSubscriptions();
      await loadSelectedHistory();
      await loadReleases();
    } finally {
      button.disabled = false;
      button.textContent = "Verificar agora";
    }
  }

  function filteredWorks() {
    const query = (elements.workSearch?.value || "").trim().toLocaleLowerCase("pt-BR");
    const filter = elements.workFilter?.value || "all";
    return subscriptions.filter(isMonitored).filter(item => {
      if (filter === "favorites" && !item.favorite) return false;
      if (filter === "not-favorites" && item.favorite) return false;
      return !query || String(item.title || "").toLocaleLowerCase("pt-BR").includes(query);
    });
  }

  function favoriteMangaIds() {
    return new Set(subscriptions.filter(item => item.favorite).map(item => Number(item.manga_id)));
  }

  function isMonitored(item) {
    if (hasField(item, "monitored")) return Boolean(item.monitored);
    if (hasField(item, "enabled")) return Boolean(item.enabled);
    return item.explicit_enabled !== false;
  }

  function hasField(item, field) {
    return Object.prototype.hasOwnProperty.call(item, field);
  }

  function latestCheckedAt(items) {
    const latest = items
      .map(item => item.last_checked_at)
      .filter(Boolean)
      .sort((left, right) => new Date(right).getTime() - new Date(left).getTime())[0];
    return dateTime(latest, "Sem registro");
  }

  function updatedFavorites() {
    const favoriteIds = favoriteMangaIds();
    return new Set(releases.filter(item => favoriteIds.has(Number(item.manga_id))).map(item => Number(item.manga_id)));
  }

  function starButton(item, scope = "list") {
    return `
      <button type="button"
              class="tracking-star"
              data-tracking-favorite="${escapeHtml(item.manga_id)}"
              data-tracking-star-scope="${escapeHtml(scope)}"
              aria-label="${item.favorite ? "Remover favorita" : "Marcar favorita"}">
        ${item.favorite ? "★" : "☆"}
      </button>
    `;
  }

  elements.daysSlider?.addEventListener("input", () => {
    days = DAY_OPTIONS[Number(elements.daysSlider.value)] || 15;
    loadReleases();
  });
  elements.releaseSearch?.addEventListener("input", () => loadReleases());
  elements.favoritesOnly?.addEventListener("change", renderReleaseTable);
  elements.unseenOnly?.addEventListener("change", () => loadReleases());
  elements.workSearch?.addEventListener("input", renderWorks);
  elements.workFilter?.addEventListener("change", renderWorks);
  elements.checkAll?.addEventListener("click", checkAll);
  elements.workList?.addEventListener("click", event => {
    const favorite = event.target.closest("[data-tracking-favorite]");
    if (favorite) {
      event.stopPropagation();
      toggleFavorite(favorite.dataset.trackingFavorite);
      return;
    }
    const item = event.target.closest("[data-tracking-work]");
    if (!item) return;
    selectedMangaId = Number(item.dataset.trackingWork);
    historyExpanded = false;
    renderWorks();
    loadSelectedHistory();
  });
  elements.detail?.addEventListener("click", event => {
    const historyToggle = event.target.closest("[data-tracking-history-toggle]");
    if (historyToggle) {
      historyExpanded = !historyExpanded;
      renderDetail();
      return;
    }
    const favorite = event.target.closest("[data-tracking-favorite]");
    if (favorite) {
      toggleFavorite(favorite.dataset.trackingFavorite);
      return;
    }
    const check = event.target.closest("[data-tracking-check-work]");
    if (check) checkWork(Number(check.dataset.trackingCheckWork), check);
  });

  return { loadTracking };
}

async function waitForTask(taskId) {
  if (!taskId) return null;
  const maxAttempts = 600;
  for (let index = 0; index < maxAttempts; index += 1) {
    const { response, payload } = await getTasks();
    if (!response.ok) {
      throw new Error(payload?.error || "Não foi possível acompanhar a verificação.");
    }
    const task = (payload.tasks || []).find(item => item.id === taskId);
    if (task && !["queued", "running"].includes(task.status)) {
      if (task.status === "failed") {
        throw new Error(task.error || task.error_message || "A verificação falhou.");
      }
      return task;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error("A verificação continua em andamento após 10 minutos. Atualize a página para consultar o status.");
}

function latestReleaseLabel(item) {
  if (!item.latest_release_chapter && !item.latest_release_date) return "Sem lançamento registrado";
  const chapter = item.latest_release_chapter ? `cap ${item.latest_release_chapter}` : "capítulo não informado";
  const date = dateOnly(item.latest_release_date);
  return `${chapter} · ${date}`;
}

function dateOnly(value) {
  return value ? String(value).slice(0, 10).split("-").reverse().join("/") : "-";
}

function dateTime(value, fallback = "-") {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}
