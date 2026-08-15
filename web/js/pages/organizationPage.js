import { catalogOne, reconcileAliases } from "../api/libraryApi.js";
import { escapeHtml } from "../utils/html.js";

export function initOrganizationPage({
  elements,
  getNotionUncataloged,
  loadCatalog,
  loadNotionStatus,
  loadPendingActions,
  startTask,
}) {
  let catalogPendingItems = [];
  let catalogPendingPage = 1;
  const catalogPendingPageSize = 8;
  let organizationSubtab = null;
  let selectedIndex = 0;
  let organizationWorkspace = null;

  const organizationPage = document.getElementById("page-organization");
  const legacyPanels = organizationPage
    ? [...organizationPage.children].filter(child => child.classList?.contains("panel"))
    : [];

  const subtabConfig = {
    review_structure: {
      title: "Revisar estrutura",
      subtitle: "As informações detalhadas da divergência estão no painel à direita.",
      listTitle: "Fila de estrutura",
      listSubtitle: "Obras identificadas na biblioteca local que exigem conferência.",
      filterOptions: ["Todas", "Pendentes"],
      status: "Prévia local",
    },
    standardize_names: {
      title: "Padronizar nomes",
      subtitle: "Revise nomes atuais e a proposta antes de qualquer renomeação física.",
      listTitle: "Fila de nomenclatura",
      listSubtitle: "Itens de padronização disponíveis para revisão.",
      filterOptions: ["Todas", "Preview"],
      status: "Prévia local",
    },
    organize_folders: {
      title: "Organizar pastas",
      subtitle: "Compare origem e destino antes de mover qualquer pasta.",
      listTitle: "Fila de organização",
      listSubtitle: "Movimentações disponíveis para conferência.",
      filterOptions: ["Todas", "Preview"],
      status: "Prévia local",
    },
    validate_chapters: {
      title: "Validar capítulos",
      subtitle: "Confira a auditoria de capítulos antes de continuar.",
      listTitle: "Fila de capítulos",
      listSubtitle: "Auditorias e verificações disponíveis para revisão local.",
      filterOptions: ["Todas", "Auditoria"],
      status: "Prévia local",
    },
    review_pending: {
      title: "Revisar pendências",
      subtitle: "Resolva somente os casos que ainda exigem execução ou decisão.",
      listTitle: "Fila de revisão",
      listSubtitle: "Pendências acionáveis já calculadas pelo sistema.",
      filterOptions: ["Todas", "Com ação", "Abrir seção"],
      status: "Decisão manual",
    },
  };

  function renderCatalogPending(data) {
    if (!elements.organizationCatalogPendingList) return;
    catalogPendingItems = Array.isArray(data.uncataloged) ? data.uncataloged : [];
    catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
    renderCatalogPendingPage();
    if (organizationSubtab === "review_structure") renderOrganizationSubtab();
  }

  function clampCatalogPendingPage(page) {
    const totalPages = Math.max(1, Math.ceil(catalogPendingItems.length / catalogPendingPageSize));
    return Math.min(Math.max(1, page || 1), totalPages);
  }

  function renderCatalogPendingPage() {
    const items = catalogPendingItems;
    if (elements.catalogPendingCount) {
      elements.catalogPendingCount.textContent = `${items.length} pendente${items.length === 1 ? "" : "s"}`;
    }
    if (elements.catalogAllPending) {
      elements.catalogAllPending.disabled = !items.length;
    }
    if (elements.catalogPendingMeta) {
      const now = new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      });
      elements.catalogPendingMeta.textContent = `Sincronizado pela última vez às ${now}.`;
    }
    if (!items.length) {
      elements.organizationCatalogPendingList.innerHTML = '<p class="empty">Nenhuma obra fora do catálogo.</p>';
      return;
    }
    catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
    const totalPages = Math.max(1, Math.ceil(items.length / catalogPendingPageSize));
    const start = (catalogPendingPage - 1) * catalogPendingPageSize;
    const pageItems = items.slice(start, start + catalogPendingPageSize);
    elements.organizationCatalogPendingList.innerHTML = `
      <div class="catalog-pending-row catalog-pending-head">
        <span>Nome da pasta no Drive</span>
        <span>Ações</span>
      </div>
      ${pageItems.map(item => `
        <div class="catalog-pending-row">
          <strong>${escapeHtml(item)}</strong>
          <span class="catalog-pending-action">
            <button type="button" data-catalog-one="${escapeHtml(item)}">Catalogar</button>
            <small aria-live="polite"></small>
          </span>
        </div>
      `).join("")}
      <div class="catalog-pending-footer">
        <span>Mostrando ${start + 1}-${Math.min(start + catalogPendingPageSize, items.length)} de ${items.length}</span>
        <span class="catalog-pending-pages">
          ${renderCatalogPendingPagination(totalPages)}
        </span>
      </div>
    `;
  }

  function renderCatalogPendingPagination(totalPages) {
    const pages = new Set([1, totalPages, catalogPendingPage]);
    if (catalogPendingPage > 1) pages.add(catalogPendingPage - 1);
    if (catalogPendingPage < totalPages) pages.add(catalogPendingPage + 1);
    const ordered = [...pages].sort((a, b) => a - b);
    const controls = [
      `<button type="button" class="page-arrow" data-catalog-page="prev" ${catalogPendingPage === 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>`,
    ];
    let previous = 0;
    for (const page of ordered) {
      if (page - previous > 1) controls.push('<span class="page-ellipsis">...</span>');
      controls.push(
        page === catalogPendingPage
          ? `<strong>${page}</strong>`
          : `<button type="button" data-catalog-page="${page}">${page}</button>`
      );
      previous = page;
    }
    controls.push(
      `<button type="button" class="page-arrow" data-catalog-page="next" ${catalogPendingPage === totalPages ? "disabled" : ""} aria-label="Próxima página">›</button>`
    );
    return controls.join("");
  }

  function ensureOrganizationWorkspace() {
    if (organizationWorkspace || !organizationPage) return organizationWorkspace;
    organizationWorkspace = document.createElement("section");
    organizationWorkspace.className = "panel organization-workspace";
    organizationWorkspace.hidden = true;
    organizationPage.prepend(organizationWorkspace);
    organizationWorkspace.addEventListener("click", handleOrganizationClick);
    organizationWorkspace.addEventListener("input", handleOrganizationFilterChange);
    organizationWorkspace.addEventListener("change", handleOrganizationFilterChange);
    return organizationWorkspace;
  }

  function setOrganizationMode(enabled) {
    const workspace = ensureOrganizationWorkspace();
    if (!workspace) return;
    workspace.hidden = !enabled;
    legacyPanels.forEach(panel => {
      panel.hidden = enabled;
    });
  }

  function ensureTopbarStatus() {
    const topbar = document.getElementById("topbar");
    if (!topbar) return null;
    let badge = topbar.querySelector(".organization-topbar-status");
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "organization-topbar-status";
      topbar.append(badge);
    }
    return badge;
  }

  function updateTopbar(config) {
    const eyebrow = document.getElementById("pageEyebrow");
    const title = document.getElementById("pageTitle");
    const subtitle = document.getElementById("pageSubtitle");
    const status = ensureTopbarStatus();
    if (eyebrow) eyebrow.textContent = `ORGANIZAÇÃO / ${config.title.toUpperCase()}`;
    if (title) title.textContent = "Organizar biblioteca local";
    if (subtitle) subtitle.textContent = config.subtitle;
    if (status) {
      status.textContent = config.status || "Prévia local";
      status.hidden = false;
    }
  }

  function restoreTopbar() {
    const eyebrow = document.getElementById("pageEyebrow");
    const title = document.getElementById("pageTitle");
    const subtitle = document.getElementById("pageSubtitle");
    const status = document.querySelector(".organization-topbar-status");
    if (eyebrow) eyebrow.textContent = "ARQUIVOS LOCAIS";
    if (title) title.textContent = "Organização";
    if (subtitle) subtitle.textContent = "Revise e aplique padrões com segurança.";
    if (status) status.hidden = true;
  }

  function getPendingItems() {
    const list = document.getElementById("organizationPendingList");
    if (!list) return [];
    return [...list.querySelectorAll(".pending-card")]
      .filter(card => !card.classList.contains("loading"))
      .map((card, index) => ({
        id: `pending-${index}`,
        title: card.querySelector("strong")?.textContent?.trim() || "Pendência",
        kind: card.querySelector(".pending-kind")?.textContent?.trim() || "Ação",
        detail: [...card.querySelectorAll("span")]
          .map(span => span.textContent.trim())
          .find(text => text && text !== card.querySelector(".pending-kind")?.textContent?.trim()) || "",
        action: card.dataset.action || "",
        pendingPage: card.dataset.pendingPage || "",
        pendingPanel: card.dataset.pendingPanel || "",
        sourceElement: card,
      }));
  }

  function getListData(subtab) {
    if (subtab === "review_structure") {
      return catalogPendingItems.map((name, index) => ({
        id: `structure-${index}`,
        title: name,
        badge: "Revisão necessária",
        badgeKind: "warning",
        filter: "Pendentes",
        meta: [
          ["Status", "Divergente"],
          ["Origem", "Biblioteca local"],
          ["Estrutura", "Fora do catálogo"],
          ["Tipo", "Pasta"],
          ["Modo", "Prévia local"],
        ],
        notice: [
          "Divergência identificada",
          "Esta pasta foi detectada na biblioteca local e ainda não está representada no catálogo atual.",
        ],
        boxes: [
          ["Pasta detectada", name],
          ["Próximo passo", "Gerar a prévia de organização para conferir a estrutura antes de qualquer movimentação."],
        ],
        action: {
          label: "Conferir estrutura",
          description: "Analise a organização sem mover pastas.",
          secondary: "Ignorar por enquanto",
          primary: "Gerar preview",
          task: "organization_preview",
          confirmation: false,
        },
      }));
    }

    if (subtab === "review_pending") {
      return getPendingItems().map(item => ({
        ...item,
        badge: item.action ? "Ação disponível" : "Decisão necessária",
        badgeKind: item.action ? "ok" : "warning",
        filter: item.action ? "Com ação" : "Abrir seção",
        meta: [
          ["Status", "Pendente"],
          ["Tipo", item.kind],
          ["Tratamento", item.action ? "Executar" : "Revisar"],
          ["Origem", "Pendências"],
          ["Modo", "Manual"],
        ],
        notice: ["Pendência identificada", item.detail || "Este item ainda exige uma ação ou decisão."],
        boxes: [
          ["Item", item.title],
          ["Tratamento", item.action ? "Executar a próxima etapa indicada pelo sistema." : "Abrir a seção relacionada para revisar o caso."],
        ],
        action: {
          label: item.action ? "Executar próxima etapa" : "Revisar pendência",
          description: item.detail || "Continue pelo fluxo indicado.",
          secondary: "Agora não",
          primary: item.action ? "Executar" : "Abrir seção",
          task: item.action,
          confirmation: ["apply_organization", "apply_renaming", "catalog_scan"].includes(item.action),
          sourceElement: item.sourceElement,
        },
      }));
    }

    const definitions = {
      standardize_names: {
        id: "standardize_names",
        title: "Padronização de nomes",
        badge: "Prévia local",
        badgeKind: "ok",
        filter: "Preview",
        meta: [
          ["Status", "Aguardando preview"],
          ["Escopo", "Nomes"],
          ["Conteúdo", "Capítulos e capas"],
          ["Modo", "Prévia local"],
          ["Aplicação", "Com confirmação"],
        ],
        notice: ["Padronização de nomes", "Analisa capítulos, capas e títulos fora do padrão antes de qualquer renomeação."],
        boxes: [
          ["Antes", "Nomes atuais da biblioteca local"],
          ["Depois", "Sugestões apresentadas pelo preview de padronização"],
        ],
        action: {
          label: "Gerar prévia de nomes",
          description: "Nenhum arquivo é renomeado durante a prévia.",
          secondary: "Agora não",
          primary: "Gerar preview",
          task: "rename_preview",
          confirmation: false,
        },
      },
      organize_folders: {
        id: "organize_folders",
        title: "Organização de pastas",
        badge: "Prévia local",
        badgeKind: "ok",
        filter: "Preview",
        meta: [
          ["Status", "Aguardando preview"],
          ["Escopo", "Pastas"],
          ["Organização", "Alfabética"],
          ["Modo", "Prévia local"],
          ["Aplicação", "Com confirmação"],
        ],
        notice: ["Movimentação proposta", "A prévia mostra a organização alfabética antes de qualquer movimentação física."],
        boxes: [
          ["Origem", "Estrutura atual da biblioteca"],
          ["Destino", "Grupos alfabéticos calculados pelo preview"],
        ],
        action: {
          label: "Gerar prévia de pastas",
          description: "Nenhuma pasta é movida durante a prévia.",
          secondary: "Agora não",
          primary: "Gerar preview",
          task: "organization_preview",
          confirmation: false,
        },
      },
      validate_chapters: {
        id: "validate_chapters",
        title: "Auditoria de capítulos",
        badge: "Auditoria local",
        badgeKind: "ok",
        filter: "Auditoria",
        meta: [
          ["Status", "Pronta para executar"],
          ["Escopo", "Capítulos"],
          ["Inclui", "Arquivos"],
          ["Modo", "Auditoria"],
          ["Alteração física", "Não"],
        ],
        notice: ["Validação de capítulos", "Verifica divergências de capítulos e arquivos que precisam de conferência."],
        boxes: [
          ["Verificação", "Capítulos e arquivos não interpretados"],
          ["Resultado", "Relatório local para revisão"],
        ],
        action: {
          label: "Executar auditoria",
          description: "Gere o relatório sem alterar a biblioteca.",
          secondary: "Agora não",
          primary: "Executar auditoria",
          task: "chapter_audit",
          confirmation: false,
        },
      },
    };
    const item = definitions[subtab];
    return item ? [item] : [];
  }

  function getKpis(subtab, items) {
    if (subtab === "review_structure") {
      return [[String(items.length), "PENDENTES"], ["LOCAL", "ORIGEM"], ["PREVIEW", "MODO"]];
    }
    if (subtab === "review_pending") {
      const actionCount = items.filter(item => item.action?.task).length;
      return [[String(items.length), "PENDENTES"], [String(actionCount), "COM AÇÃO"], [String(Math.max(0, items.length - actionCount)), "REVISAR"]];
    }
    if (subtab === "standardize_names") return [["1", "ETAPA"], ["PREVIEW", "MODO"], ["LOCAL", "ESCOPO"]];
    if (subtab === "organize_folders") return [["1", "ETAPA"], ["PREVIEW", "MODO"], ["PASTAS", "ESCOPO"]];
    return [["1", "AUDITORIA"], ["LOCAL", "ESCOPO"], ["0", "ALTERAÇÕES"]];
  }

  function renderOrganizationSubtab() {
    const config = subtabConfig[organizationSubtab];
    if (!config) return;
    const workspace = ensureOrganizationWorkspace();
    if (!workspace) return;
    updateTopbar(config);
    setOrganizationMode(true);

    const items = getListData(organizationSubtab);
    selectedIndex = Math.min(selectedIndex, Math.max(0, items.length - 1));
    const selected = items[selectedIndex] || null;
    const kpis = getKpis(organizationSubtab, items);

    workspace.innerHTML = `
      <header class="organization-workspace-head">
        <div>
          <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
          <h2>${escapeHtml(config.title)}</h2>
          <p>${escapeHtml(config.subtitle)}</p>
        </div>
        <span class="organization-stage-status">${escapeHtml(config.status || "Prévia local")}</span>
      </header>
      <div class="organization-split">
        <aside class="organization-list-panel">
          <h3>${escapeHtml(config.listTitle)}</h3>
          <p class="organization-list-subtitle">${escapeHtml(config.listSubtitle)}</p>
          <div class="organization-kpis">
            ${kpis.map(([value, label]) => `
              <article class="organization-kpi"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></article>
            `).join("")}
          </div>
          <div class="organization-search-row">
            <input type="search" data-organization-search placeholder="BUSCAR POR NOME..." aria-label="Buscar por nome">
          </div>
          <div class="organization-filter-row">
            <select data-organization-filter aria-label="Filtrar itens">
              ${config.filterOptions.map(option => `<option value="${escapeHtml(option)}">${escapeHtml(option.toUpperCase())}</option>`).join("")}
            </select>
            <select data-organization-quantity aria-label="Quantidade de itens">
              <option value="5" selected>5</option>
              <option value="10">10</option>
            </select>
            <label class="organization-select-visible" title="Selecionar visíveis">
              <input type="checkbox" data-organization-select-all aria-label="Selecionar visíveis">
            </label>
          </div>
          <div class="organization-item-list" data-organization-list>
            ${renderOrganizationItems(items.slice(0, 5))}
          </div>
        </aside>
        <section class="organization-detail-panel" data-organization-detail>
          ${renderOrganizationDetail(selected)}
        </section>
      </div>
    `;
  }

  function renderOrganizationItems(items) {
    if (!items.length) {
      return '<div class="organization-empty-list">Nenhum item nesta etapa.</div>';
    }
    return items.map((item, index) => `
      <article class="organization-list-item ${index === selectedIndex ? "active" : ""}" data-organization-index="${index}">
        <input type="checkbox" aria-label="Selecionar ${escapeHtml(item.title)}">
        <h4>${escapeHtml(item.title)}</h4>
      </article>
    `).join("");
  }

  function renderOrganizationDetail(item) {
    if (!item) {
      return `
        <div class="organization-empty-detail">
          <span class="eyebrow">ITEM SELECIONADO</span>
          <h2>Nenhum item nesta etapa</h2>
          <p>Execute ou atualize o fluxo correspondente para alimentar esta etapa.</p>
        </div>
      `;
    }
    return `
      <div class="organization-detail-top">
        <div>
          <span class="eyebrow">ITEM SELECIONADO</span>
          <h2>${escapeHtml(item.title)}</h2>
        </div>
        <span class="organization-badge ${item.badgeKind || ""}">${escapeHtml(item.badge || "Revisão")}</span>
      </div>
      <div class="organization-meta-grid">
        ${(item.meta || []).map(([label, value]) => `
          <article class="organization-meta"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>
        `).join("")}
      </div>
      <section class="organization-notice">
        <h3>${escapeHtml(item.notice?.[0] || "Informação")}</h3>
        <p>${escapeHtml(item.notice?.[1] || "")}</p>
      </section>
      <div class="organization-detail-boxes">
        ${(item.boxes || []).map(([label, value]) => `
          <article class="organization-detail-box"><h3>${escapeHtml(label)}</h3><p>${escapeHtml(value)}</p></article>
        `).join("")}
      </div>
      <section class="organization-action-bar">
        <div class="organization-action-copy">
          <small>PRÓXIMA AÇÃO</small>
          <strong>${escapeHtml(item.action?.label || "Continuar revisão")}</strong>
          <p>${escapeHtml(item.action?.description || "")}</p>
        </div>
        <div class="organization-actions">
          <button type="button" class="secondary-action" data-organization-secondary>${escapeHtml(item.action?.secondary || "Voltar")}</button>
          <button type="button" class="primary-action" data-organization-primary>${escapeHtml(item.action?.primary || "Continuar")}</button>
        </div>
      </section>
    `;
  }

  function renderTrackLibrary() {
    const workspace = ensureOrganizationWorkspace();
    if (!workspace) return;
    const config = {
      title: "Rastrear biblioteca",
      subtitle: "Localize obras, pastas e capítulos antes de qualquer análise.",
      status: "Somente leitura",
    };
    updateTopbar(config);
    setOrganizationMode(true);
    workspace.innerHTML = `
      <header class="organization-workspace-head">
        <div>
          <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
          <h2>Rastrear biblioteca</h2>
          <p>Escolha uma origem para revisar o conteúdo identificado.</p>
        </div>
        <span class="organization-stage-status">Somente leitura</span>
      </header>
      <section class="organization-full-content organization-track-content">
        <p class="organization-full-lead">Rastreamento das pastas e criação de um snapshot sem mover ou renomear arquivos.</p>

        <section class="organization-progress-card">
          <div class="organization-progress-head">
            <strong>Snapshot local</strong>
            <span>${catalogPendingItems.length ? "Disponível" : "Pronto para atualizar"}</span>
          </div>
          <div class="organization-progress"><div class="organization-progress-bar"></div></div>
          <div class="organization-timeline">
            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div><b>Pastas lidas</b><small>A biblioteca local foi disponibilizada para revisão.</small></div>
              <span class="organization-step-status">OK</span>
            </div>
            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div><b>Obras agrupadas</b><small>As próximas etapas usam os dados já carregados pelo catálogo.</small></div>
              <span class="organization-step-status">OK</span>
            </div>
            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div><b>Pendências identificadas</b><small>${catalogPendingItems.length} pasta(s) fora do catálogo aguardando revisão.</small></div>
              <span class="organization-step-status">${catalogPendingItems.length}</span>
            </div>
            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div><b>Snapshot disponível</b><small>Revisar estrutura pode usar esta fotografia da biblioteca.</small></div>
              <span class="organization-step-status neutral">Snapshot</span>
            </div>
          </div>
        </section>

        <section class="organization-full-action">
          <div class="organization-action-copy">
            <small>PRÓXIMA AÇÃO</small>
            <strong>Usar o snapshot disponível</strong>
            <p>Você pode rastrear novamente ou avançar para revisar a estrutura identificada.</p>
          </div>
          <div class="organization-actions">
            <button type="button" class="secondary-action" data-organization-task="catalog_scan" data-confirmation="true">Rastrear novamente</button>
            <button type="button" class="primary-action" data-organization-go="review_structure">Usar snapshot</button>
          </div>
        </section>
      </section>
    `;
  }

  function renderApplyOrganization() {
    const workspace = ensureOrganizationWorkspace();
    if (!workspace) return;
    const config = {
      title: "Aplicar organização",
      subtitle: "Confirme as alterações revisadas antes de alterar arquivos e pastas.",
      status: "Pronto para aplicar",
    };
    updateTopbar(config);
    setOrganizationMode(true);
    workspace.innerHTML = `
      <header class="organization-workspace-head">
        <div>
          <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
          <h2>Aplicar organização</h2>
          <p>Revise o impacto antes da confirmação final.</p>
        </div>
        <span class="organization-stage-status">Pronto para aplicar</span>
      </header>
      <section class="organization-full-content organization-apply-content">
        <p class="organization-full-lead">Última conferência antes de renomear e mover itens.</p>

        <div class="organization-summary-grid">
          <article class="organization-apply-summary success">
            <h3>Mudanças revisadas</h3>
            <p>Organização de pastas e padronização de nomes continuam protegidas por confirmação explícita.</p>
          </article>
          <article class="organization-apply-summary">
            <h3>Impacto da aplicação</h3>
            <p>Destino: biblioteca local<br>Modo: aplicação confirmada<br>Operações: pastas e nomes</p>
          </article>
        </div>

        <section class="organization-checklist">
          <div class="organization-check">
            <span class="organization-step-marker">✓</span>
            <div><b>Organizar pastas</b><small>Move obras para os grupos alfabéticos calculados pelo preview.</small></div>
            <span class="organization-step-status">Pronto</span>
          </div>
          <div class="organization-check">
            <span class="organization-step-marker">✓</span>
            <div><b>Padronizar nomes</b><small>Aplica as renomeações aprovadas para capítulos, capas e títulos.</small></div>
            <span class="organization-step-status">Pronto</span>
          </div>
        </section>

        <section class="organization-full-action">
          <div class="organization-action-copy">
            <small>PRÓXIMA AÇÃO</small>
            <strong>Aplicar organização</strong>
            <p>Escolha a operação física somente depois de revisar as prévias correspondentes.</p>
          </div>
          <div class="organization-actions">
            <button type="button" class="secondary-action" data-organization-task="apply_renaming" data-confirmation="true">Aplicar nomes</button>
            <button type="button" class="primary-action" data-organization-task="apply_organization" data-confirmation="true">Aplicar organização</button>
          </div>
        </section>
      </section>
    `;
  }

  function handleOrganizationClick(event) {
    const item = event.target.closest("[data-organization-index]");
    if (item) {
      selectedIndex = Number.parseInt(item.dataset.organizationIndex, 10) || 0;
      renderOrganizationSubtab();
      return;
    }
    const goButton = event.target.closest("[data-organization-go]");
    if (goButton) {
      const target = goButton.dataset.organizationGo;
      const sidebarButton = document.querySelector(`[data-sidebar-organization-subtab="${target}"]`);
      if (sidebarButton) sidebarButton.click();
      else setSubtab(target);
      return;
    }
    const taskButton = event.target.closest("[data-organization-task]");
    if (taskButton) {
      startTask(taskButton.dataset.organizationTask, taskButton.dataset.confirmation === "true");
      return;
    }
    if (event.target.closest("[data-organization-secondary]")) return;
    const primary = event.target.closest("[data-organization-primary]");
    if (!primary) return;
    const selected = getListData(organizationSubtab)[selectedIndex];
    if (!selected?.action) return;
    if (selected.action.task) {
      startTask(selected.action.task, Boolean(selected.action.confirmation));
    } else if (selected.action.sourceElement) {
      selected.action.sourceElement.click();
    }
  }

  function handleOrganizationFilterChange(event) {
    const workspace = ensureOrganizationWorkspace();
    if (!workspace || !subtabConfig[organizationSubtab]) return;
    const search = workspace.querySelector("[data-organization-search]")?.value?.trim().toLowerCase() || "";
    const quantity = Number.parseInt(workspace.querySelector("[data-organization-quantity]")?.value || "5", 10);
    const activeFilter = workspace.querySelector("[data-organization-filter]")?.value || "Todas";
    const allItems = getListData(organizationSubtab);
    const filtered = allItems
      .filter(item => item.title.toLowerCase().includes(search))
      .filter(item => activeFilter === "Todas" || item.filter === activeFilter)
      .slice(0, quantity);
    const list = workspace.querySelector("[data-organization-list]");
    if (list) list.innerHTML = renderOrganizationItems(filtered);
    if (event.target.matches("[data-organization-select-all]")) {
      list?.querySelectorAll('input[type="checkbox"]').forEach(input => {
        input.checked = event.target.checked;
      });
    }
  }

  function setSubtab(subtab) {
    organizationSubtab = subtab;
    selectedIndex = 0;
    if (subtab === "track_library") {
      renderTrackLibrary();
      return;
    }
    if (subtab === "apply_organization") {
      renderApplyOrganization();
      return;
    }
    if (subtabConfig[subtab]) {
      renderOrganizationSubtab();
      return;
    }
    setOrganizationMode(false);
    restoreTopbar();
  }

  window.addEventListener("manhwateca:organization-subtab", event => {
    setSubtab(event.detail?.subtab || "track_library");
  });

  elements.catalogAllPending?.addEventListener("click", () => {
    if (!getNotionUncataloged()) return;
    startTask("catalog_scan", true);
  });

  elements.refreshCatalogPending?.addEventListener("click", async () => {
    elements.refreshCatalogPending.disabled = true;
    elements.refreshCatalogPending.classList.add("spinning");
    try {
      await reconcileAliases();
      await Promise.all([loadNotionStatus(), loadPendingActions()]);
    } finally {
      elements.refreshCatalogPending.disabled = false;
      elements.refreshCatalogPending.classList.remove("spinning");
    }
  });

  if (elements.organizationCatalogPendingList) {
    elements.organizationCatalogPendingList.addEventListener("click", async event => {
      const pageButton = event.target.closest("[data-catalog-page]");
      if (pageButton) {
        const target = pageButton.dataset.catalogPage;
        if (target === "next") catalogPendingPage += 1;
        else if (target === "prev") catalogPendingPage -= 1;
        else catalogPendingPage = Number.parseInt(target, 10) || catalogPendingPage;
        catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
        renderCatalogPendingPage();
        return;
      }
      const button = event.target.closest("[data-catalog-one]");
      if (!button) return;
      const name = button.dataset.catalogOne;
      const row = button.closest(".catalog-pending-row");
      const feedback = button.parentElement?.querySelector("small");
      button.disabled = true;
      button.textContent = "Catalogando...";
      if (feedback) {
        feedback.textContent = "Salvando no PostgreSQL...";
        feedback.className = "";
      }
      try {
        const { response, payload } = await catalogOne({ name });
        if (!response.ok) {
          if (feedback) {
            feedback.textContent = payload.error || "Não foi possível catalogar.";
            feedback.className = "error";
          } else {
            window.alert(payload.error || "Não foi possível catalogar a obra.");
          }
          button.disabled = false;
          button.textContent = "Tentar novamente";
          return;
        }
        if (feedback) {
          feedback.textContent = "Catalogada.";
          feedback.className = "success";
        }
        button.textContent = "Catalogada";
        catalogPendingItems = catalogPendingItems.filter(item => item !== name);
        if (row) row.classList.add("catalog-pending-row-done");
        window.setTimeout(() => {
          catalogPendingPage = clampCatalogPendingPage(catalogPendingPage);
          renderCatalogPendingPage();
        }, 650);
        await Promise.all([loadCatalog(), loadNotionStatus(), loadPendingActions()]);
      } finally {
        if (button.textContent !== "Catalogada" && button.textContent !== "Tentar novamente") {
          button.disabled = false;
          button.textContent = "Catalogar";
        }
      }
    });
  }

  return { renderCatalogPending };
}
