import { getJson } from "../api/client.js";
import { checkReleases, getReleases, getReleasesSummary, markViewed } from "../api/releasesApi.js";
import { escapeHtml } from "../utils/html.js";

function card(title, detail, available, label) {
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

function pendingKindLabel(kind) {
  return {
    catalog: "Catálogo",
    csv: "CSV",
    mangaupdates: "MangaUpdates",
    notion: "Notion",
  }[kind] || "Ação";
}

export function initOverviewPage(elements) {
  let releasePeriod = "today";

  function setPendingLists(html) {
    if (elements.pendingList) elements.pendingList.innerHTML = html;
    if (elements.organizationPendingList) {
      elements.organizationPendingList.innerHTML = html;
    }
  }

  async function loadPendingActions() {
    const { response, payload } = await getJson("/api/pending");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!payload.items.length) {
      setPendingLists(`
        <article class="pending-card success">
          <strong>Tudo em dia</strong>
          <span>${escapeHtml(payload.empty_message || "Nenhuma pendência acionável encontrada.")}</span>
        </article>
      `);
      return;
    }
    setPendingLists(payload.items.map(item => `
      <button type="button"
              class="pending-card ${escapeHtml(item.severity || "info")}"
              ${item.action ? `data-action="${escapeHtml(item.action)}"` : ""}
              ${item.page ? `data-pending-page="${escapeHtml(item.page)}"` : ""}
              ${item.panel ? `data-pending-panel="${escapeHtml(item.panel)}"` : ""}>
        <span class="pending-kind">${escapeHtml(pendingKindLabel(item.kind))}</span>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail)}</span>
        <em>${escapeHtml(item.action ? "Executar próxima etapa" : "Abrir seção")}</em>
      </button>
    `).join(""));
  }

  async function loadStatus() {
    elements.grid.innerHTML = '<article class="status-card loading">Consultando o ambiente...</article>';
    setPendingLists('<article class="pending-card loading">Calculando pendências...</article>');
    elements.refreshButton.disabled = true;
    try {
      const { response, payload: data } = await getJson("/api/status");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const catalogSourceInfo = data.catalog.source || {};
      const catalogSourceLabel = catalogSourceInfo.label || "fonte local";
      const catalogDetail = catalogSourceInfo.detail
        ? ` Fonte: ${catalogSourceLabel} (${catalogSourceInfo.detail}).`
        : ` Fonte: ${catalogSourceLabel}.`;
      const fallbackDetail = catalogSourceInfo.fallback_reason
        ? ` Usando fallback porque: ${catalogSourceInfo.fallback_reason}`
        : "";
      elements.grid.innerHTML = [
        card(
          "Catálogo local",
          `${data.catalog.count} obra(s) catalogadas.${catalogDetail}${fallbackDetail}`,
          data.catalog.available,
          catalogSourceInfo.kind === "postgresql" ? "Banco ativo" : undefined
        ),
        card(
          "Biblioteca no Drive",
          data.library.configured
            ? "O diretório configurado está acessível para leitura e organização."
            : "Configure MANGA_ROOT no arquivo .env para localizar os arquivos.",
          data.library.available
        ),
        card(
          "MangaUpdates",
          data.mangaupdates.cache_available && data.mangaupdates.csv_available
            ? "Dados externos enriquecidos estão disponíveis."
            : "Ainda faltam dados externos enriquecidos no catálogo.",
          data.mangaupdates.cache_available && data.mangaupdates.csv_available
        ),
        card(
          "Notion",
          data.notion.configured
            ? "Credenciais disponíveis para simular e aplicar sincronizações."
            : "Configure token e database no .env antes de sincronizar.",
          data.notion.configured,
          data.notion.configured ? "Configurado" : "Não configurado"
        ),
      ].join("");
      await loadPendingActions();
      await loadReleaseDashboard();
    } catch (error) {
      elements.grid.innerHTML = card(
        "Falha ao consultar status",
        error.message,
        false,
        "Servidor indisponível"
      );
      setPendingLists(`
        <article class="pending-card warning">
          <strong>Não foi possível calcular pendências</strong>
          <span>${escapeHtml(error.message)}</span>
        </article>
      `);
    } finally {
      elements.refreshButton.disabled = false;
    }
  }

  async function loadReleaseDashboard() {
    if (!elements.releaseCards) return;
    elements.releaseCards.innerHTML = '<article class="release-card loading">Carregando lançamentos...</article>';
    elements.releaseFeedback.textContent = "";
    try {
      const { response, payload } = await getReleasesSummary();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      elements.releaseCards.innerHTML = ["month", "week", "today"].map(period => releaseCard(period, payload)).join("");
      setMonitorStatus(payload.last_monitor_run, null, payload.monitoring);
      elements.releaseFeedback.textContent = releaseWarningMessage(payload.warning);
      setReleasePeriod(releasePeriod, false);
    } catch (error) {
      elements.releaseCards.innerHTML = ["month", "week", "today"]
        .map(period => releaseCard(period, fallbackSummary()))
        .join("");
      setMonitorStatus(null);
      setReleasePeriod(releasePeriod, false);
      elements.releaseFeedback.textContent = releaseErrorMessage(error);
      return;
    }
    await loadReleaseList();
  }

  async function loadReleaseList() {
    if (!elements.releaseList) return;
    elements.releaseList.innerHTML = '<tr><td colspan="5">Carregando capítulos...</td></tr>';
    const search = elements.releaseSearch?.value || "";
    const unseen = Boolean(elements.releaseUnseenOnly?.checked);
    try {
      const { response, payload } = await getReleases({
        period: releasePeriod,
        search,
        unseen_only: unseen ? "true" : "",
        per_page: 20,
      });
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      if (payload.warning) {
        elements.releaseFeedback.textContent = releaseWarningMessage(payload.warning);
      }
      if (!payload.items.length) {
        elements.releaseList.innerHTML = `<tr><td colspan="5">Nenhum capítulo disponível ${periodLabel(releasePeriod).toLowerCase()}.</td></tr>`;
        return;
      }
      elements.releaseList.innerHTML = payload.items.map(item => `
        <tr>
          <td>${escapeHtml(item.title || "")}</td>
          <td>${escapeHtml(item.chapter || "")}</td>
          <td>${escapeHtml(dateOnly(item.release_date))}</td>
          <td>${escapeHtml(item.release_group || "-")}</td>
          <td><span class="state ${item.viewed_at ? "ok" : "warn"}">${escapeHtml(item.status)}</span></td>
        </tr>
      `).join("");
    } catch (error) {
      elements.releaseList.innerHTML = `<tr><td colspan="5">${escapeHtml(releaseErrorMessage(error))}</td></tr>`;
    }
  }

  function setReleasePeriod(period, reload = true) {
    releasePeriod = period;
    document.querySelectorAll("[data-release-period]").forEach(button => {
      button.classList.toggle("active", button.dataset.releasePeriod === period);
    });
    document.querySelectorAll("[data-release-card]").forEach(button => {
      button.classList.toggle("active", button.dataset.releaseCard === period);
    });
    if (reload) loadReleaseList();
  }

  function setMonitorStatus(run, overrideStatus = null, monitoring = null) {
    if (elements.releaseMonitorStatus) {
      elements.releaseMonitorStatus.textContent = monitorRunLabel(run, overrideStatus, monitoring);
    }
  }

  async function loadDiagnostics() {
    elements.refreshDiagnostics.disabled = true;
    try {
      const { payload: data } = await getJson("/api/diagnostics");
      elements.diagnosticGrid.innerHTML = data.checks.map(check => `
        <article class="diagnostic-item ${check.ok ? "ok" : "warn"}">
          <strong>${escapeHtml(check.name)}</strong>
          <span>${escapeHtml(check.detail)}</span>
        </article>
      `).join("");
    } finally {
      elements.refreshDiagnostics.disabled = false;
    }
  }

  elements.refreshButton?.addEventListener("click", loadStatus);
  elements.refreshDiagnostics?.addEventListener("click", loadDiagnostics);
  elements.releaseCards?.addEventListener("click", event => {
    const button = event.target.closest("[data-release-card]");
    if (button) setReleasePeriod(button.dataset.releaseCard);
  });
  document.querySelectorAll("[data-release-period]").forEach(button => {
    button.addEventListener("click", () => setReleasePeriod(button.dataset.releasePeriod));
  });
  elements.releaseSearch?.addEventListener("input", () => loadReleaseList());
  elements.releaseUnseenOnly?.addEventListener("change", () => loadReleaseList());
  elements.releaseList?.addEventListener("click", async event => {
    const button = event.target.closest("[data-release-viewed]");
    if (!button) return;
    button.disabled = true;
    await markViewed({ release_id: button.dataset.releaseViewed });
    await loadReleaseDashboard();
  });
  elements.releaseCheckNow?.addEventListener("click", async () => {
    elements.releaseCheckNow.disabled = true;
    setMonitorStatus(null, "running");
    elements.releaseFeedback.textContent = "";
    try {
      const { payload } = await checkReleases();
      if (payload.id) {
        await waitForReleaseTask(payload.id);
      }
      await loadReleaseDashboard();
    } catch (error) {
      elements.releaseFeedback.textContent = releaseErrorMessage(error);
    } finally {
      elements.releaseCheckNow.disabled = false;
    }
  });

  return { loadStatus, loadDiagnostics, loadPendingActions };
}

function releaseCard(period, payload) {
  const data = payload[period] || {};
  const chapterCount = Number(data.chapter_count ?? data.release_count ?? 0);
  return `
    <button type="button" class="release-card ${period === "today" ? "active" : ""}" data-release-card="${period}">
      <strong>${cardTitle(period)}</strong>
      <span class="release-card-count">${chapterLabel(chapterCount)}</span>
      <small>${periodDateLabel(period, data)}</small>
    </button>
  `;
}

function fallbackSummary() {
  return {
    today: { chapter_count: 0, release_count: 0 },
    week: { chapter_count: 0, release_count: 0 },
    month: { chapter_count: 0, release_count: 0 },
    last_monitor_run: null,
  };
}

function releaseErrorMessage(error) {
  const message = error?.message || "";
  if (error?.response?.status === 404) {
    return "A rota de lançamentos não foi encontrada no servidor da Manhwateca.";
  }
  if (error?.response?.status >= 500) {
    return "O servidor da Manhwateca não conseguiu carregar os lançamentos agora.";
  }
  if (message.includes("JSON inválido") || message.includes("resposta vazia")) {
    return message;
  }
  if (message.includes("servidor da Manhwateca")) {
    return message;
  }
  return "Não foi possível carregar os lançamentos agora.";
}

function releaseWarningMessage(warning) {
  if (!warning) return "";
  if (String(warning).includes("tabelas do monitor")) {
    return "O monitor ainda não foi inicializado no banco de dados. Aplique as migrations para começar a registrar lançamentos.";
  }
  return String(warning);
}

function cardTitle(period) {
  return {
    month: "Capítulos disponíveis no mês",
    week: "Capítulos disponíveis na semana",
    today: "Capítulos disponíveis hoje",
  }[period];
}

function periodLabel(period) {
  return { month: "este mês", week: "esta semana", today: "hoje" }[period];
}

function dateOnly(value) {
  return value ? String(value).slice(0, 10).split("-").reverse().join("/") : "-";
}

function dateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function monitorRunLabel(run, overrideStatus = null, monitoring = null) {
  if (overrideStatus === "running") return "Verificação em andamento...";
  const suffix = monitoringLabel(monitoring);
  if (!run) return joinMonitorParts("Monitor ainda não executado", suffix);
  const when = run.finished_at || run.started_at;
  const label = when ? `Última verificação: ${dateTime(when)}` : "Última verificação registrada";
  if (!run.status || run.status === "success") return joinMonitorParts(label, suffix);
  return joinMonitorParts(`${label}. Status: ${statusLabel(run.status)}`, suffix);
}

function statusLabel(status) {
  return {
    failed: "falha",
    partial_success: "sucesso parcial",
    running: "em execução",
  }[status] || status;
}

function monitoringLabel(monitoring) {
  const count = Number(monitoring?.monitored_count ?? 0);
  if (!count) return "";
  return `${count} ${count === 1 ? "obra monitorada" : "obras monitoradas"}`;
}

function joinMonitorParts(...parts) {
  return parts.filter(Boolean).join(" · ");
}

async function waitForReleaseTask(taskId) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const { response, payload } = await getJson(`/api/tasks/${taskId}`);
    if (!response.ok) break;
    if (!["queued", "running"].includes(payload.status)) return payload;
    await delay(1000);
  }
  return null;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function chapterLabel(count) {
  return `${count} ${count === 1 ? "capítulo" : "capítulos"}`;
}

function periodDateLabel(period, data) {
  if (!data.start_date) return "-";
  if (period === "today") return dateOnly(data.start_date);
  return `${dateOnly(data.start_date)} a ${dateOnly(data.end_date)}`;
}
