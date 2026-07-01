import { getTasks, startTaskAction } from "../api/tasksApi.js";
import { escapeHtml } from "../utils/html.js";
import { initTaskToast } from "./taskToast.js";

export function initTaskRunner({ elements, callbacks, showPage, getNotionUncataloged }) {
  let taskTimer;
  let lastCatalogTask;
  let lastMangaUpdatesTask;
  let lastNotionTask;
  let lastMetadataTask;
  const taskToast = initTaskToast({ elements, taskNextStep, taskCompletionSummary });

  function confirmTask(action) {
    const notionWrite = [
      "notion_apply_batch",
      "notion_update_existing",
      "notion_csv_apply",
    ].includes(action);
    const externalRefresh = action === "mangaupdates_force_refresh";
    const massCatalog = action === "catalog_scan";
    elements.confirmationTitle.textContent = massCatalog
      ? "Confirmar Catalogação em Massa"
      : externalRefresh
      ? "Confirmar consultas externas"
      : notionWrite
      ? "Confirmar alteração no Notion"
      : "Confirmar alteração na biblioteca";
    elements.confirmationText.textContent = massCatalog
      ? `Você está prestes a registrar ${getNotionUncataloged()} nova(s) obra(s) no banco de dados. Deseja prosseguir?`
      : externalRefresh
      ? "Esta ação reconsulta o MangaUpdates mesmo quando já existe cache. Deseja continuar?"
      : notionWrite
      ? "Esta ação enviará alterações ao Notion. Deseja continuar?"
      : "Esta ação alterará arquivos ou pastas da biblioteca. Deseja continuar?";
    elements.confirmationDialog.showModal();
    return new Promise(resolve => {
      elements.confirmationDialog.addEventListener("close", () => {
        resolve(elements.confirmationDialog.returnValue === "confirm");
      }, { once: true });
    });
  }

  async function startTask(action, requiresConfirmation) {
    let confirmation = null;
    let parameters = {};
    if (requiresConfirmation) {
      if (!await confirmTask(action)) return;
      confirmation = "APLICAR";
    }
    if (action === "mangaupdates_search") {
      const initials = window.prompt(
        "Letras iniciais (ex.: A, ABC ou 0-9). Deixe vazio para todas."
      );
      if (initials === null) return;
      parameters = { initials };
    }
    const { response, payload } = await startTaskAction(action, {
      confirmation,
      parameters,
    });
    if (!response.ok) {
      window.alert(payload.error || "Não foi possível iniciar a tarefa.");
      return;
    }
    document.getElementById("taskToastTitle").textContent = payload.label;
    document.getElementById("taskToastText").textContent =
      "Preparando a execução...";
    elements.taskToast.dataset.taskId = payload.id;
    elements.taskToast.className = "task-toast running";
    elements.taskProgress.setAttribute("aria-label", "Tarefa em andamento");
    elements.taskResultLink.hidden = true;
    elements.viewTaskProgress.hidden = false;
    elements.viewTaskProgress.textContent = "Ver andamento";
    elements.taskToast.hidden = false;
    await loadTasks();
  }

  function renderTask(task) {
    const running = ["queued", "running"].includes(task.status);
    const next = taskNextStep(task);
    const reports = (task.reports || []).map(path => `
      <a href="/reports/${path.replace(/^reports\//, "")}" target="_blank">
        Abrir ${path.split("/").pop()}
      </a>
    `).join("");
    const messages = (task.messages || []).join("\n");
    const metrics = renderTaskMetrics(task);
    return `
      <article class="task-item" data-task-id="${escapeHtml(task.id)}">
        <div class="task-head">
          <strong>${task.label}</strong>
          <span class="state ${task.status === "completed" ? "ok" : "warn"}">
            ${task.status}
          </span>
        </div>
        <p>${task.started_at || task.created_at}${task.finished_at ? ` → ${task.finished_at}` : ""}</p>
        ${metrics}
        ${next ? `
          <div class="task-next-step">
            <strong>Próximo passo</strong>
            <span>${escapeHtml(next.text)}</span>
            <button type="button"
                    data-next-page="${escapeHtml(next.page)}"
                    data-next-panel="${escapeHtml(next.panel || "")}">
              ${escapeHtml(next.label)}
            </button>
          </div>
        ` : ""}
        ${reports ? `<div class="task-links">${reports}</div>` : ""}
        ${messages ? `<pre>${escapeHtml(messages)}</pre>` : ""}
        ${running ? "<p>Executando em segundo plano...</p>" : ""}
      </article>
    `;
  }

  function renderTaskMetrics(task) {
    const chips = [];
    if (typeof task.duration_seconds === "number") {
      chips.push(`Duração: ${task.duration_seconds.toFixed(2)}s`);
    }
    const notion = task.metrics?.notion || {};
    if (typeof notion.created === "number") chips.push(`Criadas: ${notion.created}`);
    if (typeof notion.updated === "number") chips.push(`Atualizadas: ${notion.updated}`);
    if (typeof notion.unchanged === "number") chips.push(`Sem alteração: ${notion.unchanged}`);
    if (typeof notion.missing === "number") chips.push(`Ausentes: ${notion.missing}`);
    const external = task.metrics?.external_calls || {};
    if (typeof external.notion_writes === "number") {
      chips.push(`Escritas Notion: ${external.notion_writes}`);
    }
    if (typeof external.mangaupdates === "number") {
      chips.push(`Chamadas MangaUpdates: ${external.mangaupdates}`);
    }
    const mangaupdates = task.metrics?.mangaupdates || {};
    if (typeof mangaupdates.actionable_review === "number") {
      chips.push(`A revisar na tela: ${mangaupdates.actionable_review}`);
    }
    if (typeof mangaupdates.not_found === "number") {
      chips.push(`Não encontradas: ${mangaupdates.not_found}`);
    }
    const items = task.metrics?.items || {};
    if (items.created?.length) chips.push(`Obras criadas: ${items.created.length}`);
    if (items.updated?.length) chips.push(`Obras atualizadas: ${items.updated.length}`);
    if (items.missing?.length) chips.push(`Obras ausentes: ${items.missing.length}`);
    if (items.duplicates?.length) chips.push(`Duplicadas: ${items.duplicates.length}`);
    if (items.errors?.length) chips.push(`Erros: ${items.errors.length}`);
    return chips.length
      ? `<div class="task-metrics">${chips.map(item => `<span>${escapeHtml(item)}</span>`).join("")}</div>`
      : "";
  }

  function taskNextStep(task) {
    if (task.status !== "completed") return null;
    const manga = task.metrics?.mangaupdates || {};
    const notion = task.metrics?.notion || {};
    const items = task.metrics?.items || {};

    if (["mangaupdates_search", "mangaupdates_refresh"].includes(task.action)) {
      const actionableReview = manga.actionable_review ?? manga.review ?? 0;
      if (actionableReview > 0) {
        return {
          label: "Revisar IDs pendentes",
          page: "mangaupdates",
          panel: "idReviewPanel",
          text: `${actionableReview} correspondência(s) aparecem na seção de revisão e precisam de decisão antes de consultar detalhes na API.`,
        };
      }
      if ((manga.pending || 0) > 0) {
        return {
          label: "Buscar próximo lote",
          page: "mangaupdates",
          panel: "mangaActionsPanel",
          text: `${manga.pending} obra(s) ainda não foram pesquisadas. Execute somente “Buscar próximo lote de IDs”.`,
        };
      }
      if ((manga.not_found || 0) > 0) {
        return {
          label: "Pesquisar manualmente",
          page: "mangaupdates",
          panel: "apiSearchPanel",
          text: `${manga.not_found} obra(s) já foram pesquisadas e não tiveram candidato útil. Use a pesquisa avulsa ou ajuste nomes de busca.`,
        };
      }
    }

    if (task.action === "mangaupdates_details") {
      if ((manga.pending || 0) > 0) {
        return {
          label: "Consultar próximo lote",
          page: "mangaupdates",
          panel: "mangaActionsPanel",
          text: `${manga.pending} ID(s) confirmado(s) ainda aguardam detalhes da API.`,
        };
      }
      return {
        label: "Ver banco atualizado",
        page: "mangaupdates",
        panel: "mangaActionsPanel",
        text: "Os detalhes consultados já foram salvos no banco quando PostgreSQL está ativo.",
      };
    }

    if (task.action === "mangaupdates_csv" && (manga.pending || 0) > 0) {
      return {
        label: "Consultar detalhes",
        page: "mangaupdates",
        panel: "mangaActionsPanel",
        text: `${manga.pending} obra(s) confirmadas ainda precisam de detalhes antes de entrar no CSV.`,
      };
    }

    if (task.action === "catalog_scan") {
      return {
        label: "Ver pendências de catálogo",
        page: "organization",
        panel: "organizationCatalogPendingPanel",
        text: "Confira quais pastas do Drive ainda não aparecem no PostgreSQL.",
      };
    }

    if (task.action === "notion_simulate_batch" && (notion.pending || 0) > 0) {
      return {
        label: "Importar lote",
        page: "notion",
        panel: "notionActionsPanel",
        text: `${notion.pending} página(s) ainda precisam ser criadas. Aplique somente após revisar a simulação.`,
      };
    }

    if (task.action === "notion_apply_batch") {
      if ((notion.pending || 0) > 0) {
        return {
          label: "Importar próximo lote",
          page: "notion",
          panel: "notionActionsPanel",
          text: `${notion.pending} página(s) continuam pendentes para o próximo lote.`,
        };
      }
      return {
        label: "Simular metadados",
        page: "notion",
        panel: "notionActionsPanel",
        text: "O catálogo foi importado. Agora simule a atualização dos metadados a partir do banco.",
      };
    }

    if (task.action === "notion_csv_preview") {
      if ((notion.updated || 0) > 0 || (notion.missing || 0) > 0 || (notion.duplicates || 0) > 0) {
        return {
          label: "Revisar metadados",
          page: "notion",
          panel: "metadataPanel",
          text: "Revise ausentes, duplicadas e alterações antes de aplicar os metadados.",
        };
      }
    }

    if (task.action === "notion_csv_apply" && items.missing?.length) {
      return {
        label: "Ver ausentes",
        page: "notion",
        panel: "metadataPanel",
        text: `${items.missing.length} obra(s) do CSV não foram encontradas no Notion.`,
      };
    }

    return null;
  }

  function goToNextStep(page, panel) {
    showPage(page || "overview");
    window.setTimeout(() => {
      const target = panel ? document.getElementById(panel) : null;
      if (target?.tagName === "DETAILS") target.open = true;
      (target || document.getElementById(`page-${page}`) || document.body).scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      elements.taskToast.hidden = true;
    }, 120);
  }

  async function loadTasks() {
    const { payload: data } = await getTasks();
    if (elements.taskList) {
      elements.taskList.innerHTML = data.tasks.length
        ? data.tasks.map(renderTask).join("")
        : '<p class="empty">Nenhuma tarefa executada.</p>';
    }
    taskToast.updateTaskToast(data.tasks);
    const hasRunning = data.tasks.some(task => ["queued", "running"].includes(task.status));
    const catalogTask = data.tasks.find(task =>
      task.action === "catalog_scan" && task.status === "completed"
    );
    if (catalogTask && catalogTask.id !== lastCatalogTask) {
      lastCatalogTask = catalogTask.id;
      await Promise.all([
        callbacks.loadCatalog(),
        callbacks.loadStatus(),
        callbacks.loadNotionStatus(),
        callbacks.loadPendingActions(),
      ]);
    }
    const mangaUpdatesTask = data.tasks.find(task =>
      task.group === "mangaupdates" && task.status === "completed"
    );
    if (mangaUpdatesTask && mangaUpdatesTask.id !== lastMangaUpdatesTask) {
      lastMangaUpdatesTask = mangaUpdatesTask.id;
      await Promise.all([
        callbacks.loadIdReview(),
        callbacks.loadPendingActions(),
        callbacks.loadMangaUpdatesStatus(),
      ]);
    }
    const notionTask = data.tasks.find(task =>
      task.group === "notion" && !["queued", "running"].includes(task.status)
    );
    if (notionTask && notionTask.id !== lastNotionTask) {
      lastNotionTask = notionTask.id;
      await Promise.all([callbacks.loadNotionStatus(), callbacks.loadPendingActions()]);
    }
    const metadataTask = data.tasks.find(task =>
      ["notion_csv_preview", "notion_csv_apply"].includes(task.action)
      && !["queued", "running"].includes(task.status)
    );
    if (metadataTask && metadataTask.id !== lastMetadataTask) {
      lastMetadataTask = metadataTask.id;
      await Promise.all([callbacks.loadMetadataStatus(), callbacks.loadPendingActions()]);
    }
    clearTimeout(taskTimer);
    if (hasRunning) {
      taskTimer = setTimeout(loadTasks, 1000);
    }
  }

  function taskCompletionSummary(task) {
    const parts = [];
    const mangaupdates = task.metrics?.mangaupdates || {};
    if (typeof mangaupdates.processed === "number") parts.push(`Processadas: ${mangaupdates.processed}`);
    if (typeof mangaupdates.details === "number") parts.push(`Detalhes consultados: ${mangaupdates.details}`);
    if (typeof mangaupdates.review === "number") parts.push(`Para revisar: ${mangaupdates.review}`);
    if (typeof mangaupdates.actionable_review === "number") parts.push(`A revisar na tela: ${mangaupdates.actionable_review}`);
    if (typeof mangaupdates.pending === "number") parts.push(`Pendentes: ${mangaupdates.pending}`);
    if (typeof mangaupdates.not_found === "number") parts.push(`Não encontradas: ${mangaupdates.not_found}`);

    const notion = task.metrics?.notion || {};
    if (typeof notion.created === "number") parts.push(`Criadas: ${notion.created}`);
    if (typeof notion.updated === "number") parts.push(`Atualizadas: ${notion.updated}`);
    if (typeof notion.unchanged === "number") parts.push(`Sem alteração: ${notion.unchanged}`);
    if (typeof notion.pending === "number") parts.push(`Restantes: ${notion.pending}`);
    if (typeof notion.missing === "number") parts.push(`Ausentes: ${notion.missing}`);
    if (typeof notion.duplicates === "number") parts.push(`Duplicadas: ${notion.duplicates}`);

    const items = task.metrics?.items || {};
    if (items.missing?.length) parts.push(`Obras ausentes: ${items.missing.length}`);
    if (items.errors?.length) parts.push(`Erros: ${items.errors.length}`);

    return parts.length
      ? `Tarefa concluída. ${parts.join(" · ")}.`
      : "Tarefa concluída com sucesso.";
  }

  elements.viewTaskProgress?.addEventListener("click", () => {
    if (elements.viewTaskProgress.dataset.nextPage) {
      goToNextStep(
        elements.viewTaskProgress.dataset.nextPage,
        elements.viewTaskProgress.dataset.nextPanel
      );
      return;
    }
    showPage("automation");
    window.setTimeout(() => {
      if (!elements.taskList) return;
      const task = elements.taskList.querySelector(
        `[data-task-id="${CSS.escape(elements.taskToast.dataset.taskId || "")}"]`
      );
      (task || document.getElementById("taskHistory"))?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      if (task) {
        task.classList.add("task-highlight");
        window.setTimeout(() => task.classList.remove("task-highlight"), 1800);
      }
      elements.taskToast.hidden = true;
    }, 120);
  });

  if (elements.taskList) {
    elements.taskList.addEventListener("click", event => {
      const button = event.target.closest("[data-next-page]");
      if (!button) return;
      goToNextStep(button.dataset.nextPage, button.dataset.nextPanel);
    });
  }

  return { startTask, loadTasks, goToNextStep };
}
