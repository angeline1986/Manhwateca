import { catalogOne, getCatalog, getNamingReview, getStructureReview, reconcileAliases } from "../api/libraryApi.js";
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
  let organizationCheckedKeys = new Set();
  let organizationWorkspace = null;
  let trackCatalogSnapshot = null;
  let trackCatalogLoading = false;
  let trackCatalogError = "";
  let structureReviewSnapshot = null;
  let structureReviewLoading = false;
  let structureReviewError = "";
  let namingReviewSnapshot = null;
  let namingReviewLoading = false;
  let namingReviewError = "";
  const organizationViewState = new Map();

  const organizationPage = document.getElementById("page-organization");
  const legacyPanels = organizationPage
    ? [...organizationPage.children].filter(child => child.classList?.contains("panel"))
    : [];

  const subtabConfig = {
    review_structure: {
      title: "Revisar estrutura",
      subtitle: "As informações detalhadas da divergência estão no painel à direita.",
      listTitle: "Fila de estrutura",
      listSubtitle: "Obras identificadas no snapshot.",
      filterOptions: ["Todas", "Divergências", "Duplicatas", "OK"],
      status: "Prévia local",
    },
    standardize_names: {
      title: "Padronizar nomes",
      subtitle: "Revise os nomes identificados e confirme as sugestões necessárias.",
      listTitle: "Fila de nomenclatura",
      listSubtitle: "Arquivos e pastas que podem ter seus nomes padronizados.",
      filterOptions: ["Todas", "Sugeridos", "Revisar", "Manter"],
      status: "Prévia local",
    },
    organize_folders: {
      title: "Organizar pastas",
      subtitle: "Revise origem e destino antes de qualquer movimentação.",
      listTitle: "Fila de organização",
      listSubtitle: "Arquivos e pastas com movimentação proposta.",
      filterOptions: ["Todas", "Movimentos", "Conflitos", "Manter"],
      status: "Prévia local",
    },
    validate_chapters: {
      title: "Validar capítulos",
      subtitle: "Verifique lacunas e duplicidades na sequência de capítulos das obras.",
      listTitle: "Fila de capítulos",
      listSubtitle: "Obras com sequência válida, lacunas ou duplicidades.",
      filterOptions: ["Todas", "Inconsistências", "Lacunas", "Duplicados"],
      status: "Prévia local",
    },
    review_pending: {
      title: "Revisar pendências",
      subtitle: "Resolva os casos que não puderam ser tratados automaticamente.",
      listTitle: "Fila de revisão",
      listSubtitle: "Casos que não puderam ser resolvidos automaticamente.",
      filterOptions: ["Todas", "Corrigir", "Decidir", "Revisar"],
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
      const items = Array.isArray(structureReviewSnapshot?.items)
        ? structureReviewSnapshot.items
        : [];

      return items.map(item => {
        const category = item.category || "ok";
        const filter = category === "duplicate"
          ? "Duplicatas"
          : (category === "divergence" ? "Divergências" : "OK");
        const currentPaths = Array.isArray(item.current_paths)
          ? item.current_paths.join("\n")
          : "";
        const suggested = item.expected_path || "Manter estrutura atual";
        const needsPreview = item.action === "preview";

        return {
          id: item.id,
          title: item.title,
          badge: item.badge,
          badgeKind: category === "ok" ? "ok" : "warning",
          filter,
          group: item.expected_group || item.current_group || "#",
          meta: [
            ["Estrutura atual", item.current_structure || "—"],
            ["Estrutura esperada", item.expected_structure || "—"],
            ["Arquivos", String(item.files ?? 0)],
          ],
          notice: [
            item.issue_title || "Divergência identificada",
            item.issue_description || "",
          ],
          boxes: [
            ["Estrutura atual", currentPaths || "Nenhum caminho informado."],
            ["Estrutura sugerida", suggested],
          ],
          action: needsPreview ? {
            label: "Analisar estrutura",
            description: (
              "O planner identificou a divergência. Gere o preview completo "
              + "antes de tomar qualquer decisão."
            ),
            secondary: null,
            primary: "Gerar preview",
            task: "organization_preview",
            confirmation: false,
          } : {
            label: "Nenhuma ação estrutural",
            description: item.movement_required
              ? "Sem conflito estrutural. A movimentação, se necessária, será tratada em Organizar pastas."
              : "A estrutura atual não requer correção.",
            secondary: null,
            primary: null,
            task: "",
            confirmation: false,
          },
        };
      });
    }

    if (subtab === "standardize_names") {
      const items = Array.isArray(namingReviewSnapshot?.items) ? namingReviewSnapshot.items : [];
      return items.map(item => ({
        id: item.id,
        title: item.title,
        group: item.group || "#",
        badge: item.badge,
        badgeKind: item.category === "review" ? "warning" : "ok",
        filter: item.category === "review" ? "Revisar" : "Sugeridos",
        meta: [
          ["Tipo", item.kind === "cover" ? "Capa" : "Capítulo"],
          ["Obra", item.work || "—"],
          ["Grupo", item.group || "—"],
        ],
        notice: [item.category === "review" ? "Revisão necessária" : "Nome sugerido", item.reason || ""],
        boxes: [["Antes", item.old_name || "—"], ["Depois", item.new_name || "—"]],
        action: {
          label: item.category === "review" ? "Revisar sugestão" : "Confirmar renomeação",
          description: "A alteração permanece em prévia até a etapa Aplicar organização.",
          secondary: null,
          primary: "Gerar preview",
          task: "rename_preview",
          confirmation: false,
        },
      }));
    }

    if (subtab === "review_pending") {
      return getPendingItems().map(item => ({
        ...item,
        badge: "Decisão necessária",
        badgeKind: "warning",
        filter: item.action ? "Corrigir" : "Decidir",
        meta: [
          ["Problema", item.kind || "Pendência"],
          ["Origem", item.title || "Revisão"],
          ["Impacto", item.action ? "Requer tratamento" : "Decisão manual"],
        ],
        notice: [
          "Sem decisão segura",
          item.detail || "O sistema não conseguiu determinar sozinho o tratamento adequado para esta pendência.",
        ],
        boxes: [
          ["Opção 1", "Ignorar a pendência e continuar."],
          ["Opção 2", "Corrigir a origem antes da aplicação."],
        ],
        action: {
          label: "Registrar decisão",
          description: "Escolha como esta pendência deve ser tratada.",
          secondary: "Ignorar",
          primary: "Sinalizar correção",
          task: "",
          confirmation: false,
          sourceElement: item.sourceElement,
        },
      }));
    }

    const definitions = {
      organize_folders: {
        id: "organize_folders",
        title: "Boredom_01.cbz",
        badge: "Movimento seguro",
        badgeKind: "ok",
        filter: "Movimentos",
        meta: [
          ["Origem", "/Downloads"],
          ["Destino", "/Biblioteca/Boredom"],
          ["Conflitos", "0"],
        ],
        notice: [
          "Movimentação proposta",
          "O arquivo será movido para a pasta principal da obra.",
        ],
        boxes: [
          ["Antes", "Downloads/\n└── Boredom_01.cbz"],
          ["Depois", "Biblioteca/Boredom/\n└── Boredom_01.cbz"],
        ],
        action: {
          label: "Confirmar movimentação",
          description: "O arquivo só será movido na aplicação final.",
          secondary: "Ignorar",
          primary: "Aprovar",
          task: "organization_preview",
          confirmation: false,
        },
      },
      validate_chapters: {
        id: "validate_chapters",
        title: "Romance in Romance",
        badge: "Lacuna encontrada",
        badgeKind: "warning",
        filter: "Lacunas",
        meta: [
          ["Capítulos", "38"],
          ["Lacunas", "1"],
          ["Duplicados", "0"],
        ],
        notice: [
          "Capítulo ausente",
          "Não foi encontrado um arquivo correspondente ao capítulo 012.",
        ],
        boxes: [
          ["Sequência", "001–011, 013–038"],
          ["Ação sugerida", "Ignorar a lacuna ou corrigir a origem antes da aplicação."],
        ],
        action: {
          label: "Decidir tratamento",
          description: "A lacuna não pode ser resolvida automaticamente.",
          secondary: "Ignorar",
          primary: "Sinalizar correção",
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
      return [
        [String(items.filter(item => item.filter === "Divergências").length), "DIVERGÊNCIAS"],
        [String(items.filter(item => item.filter === "Duplicatas").length), "DUPLICATAS"],
        [String(items.filter(item => item.filter === "OK").length), "OK"],
      ];
    }

    if (subtab === "standardize_names") {
      const suggested = items.filter(item => item.filter === "Sugeridos").length;
      const review = items.filter(item => item.filter === "Revisar").length;
      return [[String(suggested), "SUGERIDOS"], [String(review), "REVISAR"], [String(review), "BLOQUEIOS"]];
    }

    if (subtab === "organize_folders") {
      return [["1", "MOVER"], ["0", "REVISAR"], ["0", "MANTER"]];
    }

    if (subtab === "validate_chapters") {
      return [["42", "DIVERGÊNCIAS"], ["7", "LACUNAS"], ["6", "DUPLICADOS"]];
    }

    if (subtab === "review_pending") {
      const corrigir = items.filter(item => item.filter === "Corrigir").length;
      const decidir = items.filter(item => item.filter === "Decidir").length;
      const revisar = Math.max(0, items.length - corrigir - decidir);
      return [
        [String(corrigir), "CORRIGIR", "O problema está identificado e sabemos que a origem precisa de correção."],
        [String(decidir), "DECIDIR", "Existem alternativas e o usuário precisa escolher o tratamento."],
        [String(revisar), "REVISAR", "O sistema não conseguiu chegar a uma conclusão suficiente para recomendar uma decisão."],
      ];
    }

    return [];
  }

  function organizationStateFor(subtab) {
    if (!organizationViewState.has(subtab)) {
      organizationViewState.set(subtab, {
        search: "",
        filter: "Todas",
        quantity: 5,
        group: "Todas",
      });
    }
    return organizationViewState.get(subtab);
  }

  function filteredOrganizationItems(items, state) {
    const search = String(state.search || "").trim().toLocaleLowerCase("pt-BR");
    return items
      .filter(item =>
        !search || String(item.title || "").toLocaleLowerCase("pt-BR").includes(search)
      )
      .filter(item => state.filter === "Todas" || item.filter === state.filter)
      .filter(item => state.group === "Todas" || String(item.group || "#") === state.group);
  }

  async function loadStructureReview() {
    if (structureReviewLoading) return;
    structureReviewLoading = true;
    structureReviewError = "";
    if (organizationSubtab === "review_structure") renderOrganizationSubtab();

    try {
      const { response, payload } = await getStructureReview();
      if (!response.ok) {
        throw new Error(payload?.error || "Não foi possível analisar a estrutura.");
      }
      structureReviewSnapshot = payload;
    } catch (error) {
      structureReviewError = error?.message || "Não foi possível analisar a estrutura.";
    } finally {
      structureReviewLoading = false;
      if (organizationSubtab === "review_structure") renderOrganizationSubtab();
    }
  }

  async function loadNamingReview() {
    if (namingReviewLoading) return;
    namingReviewLoading = true;
    namingReviewError = "";
    if (organizationSubtab === "standardize_names") renderOrganizationSubtab();
    try {
      const { response, payload } = await getNamingReview();
      if (!response.ok) throw new Error(payload?.error || "Não foi possível analisar os nomes.");
      namingReviewSnapshot = payload;
    } catch (error) {
      namingReviewError = error?.message || "Não foi possível analisar os nomes.";
    } finally {
      namingReviewLoading = false;
      if (organizationSubtab === "standardize_names") renderOrganizationSubtab();
    }
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
    const viewState = organizationStateFor(organizationSubtab);
    const filtered = filteredOrganizationItems(items, viewState);
    const visible = filtered.slice(0, viewState.quantity);

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
            ${kpis.map(([value, label, tooltip]) => `
              <article class="organization-kpi ${tooltip ? "has-tooltip" : ""}"
                       ${tooltip ? 'tabindex="0"' : ""}>
                <strong>${escapeHtml(value)}</strong>
                <span>${escapeHtml(label)}${tooltip ? ' <b class="organization-info" aria-hidden="true">ⓘ</b>' : ""}</span>
                ${tooltip ? `<em class="organization-tooltip" role="tooltip"><b>${escapeHtml(label)}</b>${escapeHtml(tooltip)}</em>` : ""}
              </article>
            `).join("")}
          </div>
          <div class="organization-search-row">
            <input type="search"
                   data-organization-search
                   value="${escapeHtml(viewState.search)}"
                   placeholder="BUSCAR POR NOME..."
                   aria-label="Buscar por nome">
            ${(organizationSubtab === "review_structure" || organizationSubtab === "standardize_names") ? `
              <select data-organization-group aria-label="Filtrar por grupo alfabético">
                ${["Todas", ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ".split(""), "0–9", "#"].map(group => `
                  <option value="${group}" ${group === viewState.group ? "selected" : ""}>${group === "Todas" ? "GRUPO: TODAS" : `GRUPO: ${group}`}</option>
                `).join("")}
              </select>` : ""}
          </div>
          <div class="organization-filter-row">
            <select data-organization-filter aria-label="Filtrar itens">
              ${config.filterOptions.map(option => `
                <option value="${escapeHtml(option)}" ${option === viewState.filter ? "selected" : ""}>
                  ${escapeHtml(option.toUpperCase())}
                </option>
              `).join("")}
            </select>
            <select data-organization-quantity aria-label="Quantidade de itens">
              <option value="5" ${viewState.quantity === 5 ? "selected" : ""}>5</option>
              <option value="10" ${viewState.quantity === 10 ? "selected" : ""}>10</option>
            </select>
            <label class="organization-select-visible" title="Selecionar visíveis">
              <input type="checkbox" data-organization-select-all aria-label="Selecionar visíveis">
            </label>
          </div>
          <div class="organization-item-list" data-organization-list>
            ${renderOrganizationItems(visible)}
          </div>
        </aside>
        <section class="organization-detail-panel" data-organization-detail>
          ${structureReviewLoading && organizationSubtab === "review_structure" && !structureReviewSnapshot
            ? `<div class="organization-empty-detail"><span class="eyebrow">ANÁLISE</span><h2>Analisando estrutura...</h2><p>Consultando o planner da biblioteca.</p></div>`
            : structureReviewError && organizationSubtab === "review_structure" && !structureReviewSnapshot
              ? `<div class="organization-empty-detail"><span class="eyebrow">ANÁLISE</span><h2>Não foi possível analisar</h2><p>${escapeHtml(structureReviewError)}</p></div>`
              : namingReviewLoading && organizationSubtab === "standardize_names" && !namingReviewSnapshot
                ? `<div class="organization-empty-detail"><span class="eyebrow">ANÁLISE</span><h2>Analisando nomes...</h2><p>Consultando o normalizador existente.</p></div>`
                : namingReviewError && organizationSubtab === "standardize_names" && !namingReviewSnapshot
                  ? `<div class="organization-empty-detail"><span class="eyebrow">ANÁLISE</span><h2>Não foi possível analisar</h2><p>${escapeHtml(namingReviewError)}</p></div>`
                  : renderOrganizationDetail(selected)}
        </section>
      </div>
    `;
  }

  function organizationItemKey(item) {
    return String(item?.id || item?.title || "");
  }

  function renderOrganizationItems(items) {
    if (!items.length) {
      return '<div class="organization-empty-list">Nenhum item nesta etapa.</div>';
    }

    const selectedItem = getListData(organizationSubtab)[selectedIndex] || null;
    const selectedKey = organizationItemKey(selectedItem);

    return items.map(item => {
      const key = organizationItemKey(item);
      const active = key === selectedKey;
      const checked = organizationCheckedKeys.has(key);

      return `
        <article class="organization-list-item ${checked ? "selected" : ""}"
                 data-organization-key="${escapeHtml(key)}"
                 ${active ? 'aria-current="true"' : ""}>
          <input type="checkbox"
                 data-organization-item-checkbox
                 data-organization-key="${escapeHtml(key)}"
                 ${checked ? "checked" : ""}
                 aria-label="Selecionar ${escapeHtml(item.title)}">
          <h4>${escapeHtml(item.title)}</h4>
        </article>
      `;
    }).join("");
  }

  function formatStructureTree(value) {
    const paths = String(value || "").split("\n").map(path => path.trim()).filter(Boolean);
    if (!paths.length) return "—";
    return paths.map(path => {
      const parts = path.split(/[\\/]+/).filter(Boolean);
      return parts.map((part, index) => `${index ? "    ".repeat(index - 1) + "└── " : ""}${part}${index < parts.length - 1 ? "/" : "/"}`).join("\n");
    }).join("\n\n");
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
          <article class="organization-detail-box"><h3>${escapeHtml(label)}</h3><p class="${organizationSubtab === "review_structure" ? "organization-tree" : ""}">${organizationSubtab === "review_structure" ? escapeHtml(formatStructureTree(value)) : escapeHtml(value)}</p></article>
        `).join("")}
      </div>
      <section class="organization-action-bar">
        <div class="organization-action-copy">
          <small>PRÓXIMA AÇÃO</small>
          <strong>${escapeHtml(item.action?.label || "Continuar revisão")}</strong>
          <p>${escapeHtml(item.action?.description || "")}</p>
        </div>
        <div class="organization-actions">
          ${item.action?.secondary
            ? `<button type="button" class="secondary-action" data-organization-secondary>${escapeHtml(item.action.secondary)}</button>`
            : ""}
          ${item.action?.primary
            ? `<button type="button" class="primary-action" data-organization-primary>${escapeHtml(item.action.primary)}</button>`
            : ""}
        </div>
      </section>
    `;
  }

  function catalogSnapshotMetrics(data) {
    const summary = data?.summary || {};
    const changes = data?.changes || {};
    return {
      works: Number(summary.total || 0),
      chapters: Number(summary.main_caps || 0),
      review: Number(summary.review || 0),
      unparsed: Number(summary.unparsed || 0),
      added: Array.isArray(changes.new) ? changes.new.length : 0,
      updated: Array.isArray(changes.updated) ? changes.updated.length : 0,
      removed: Array.isArray(changes.removed) ? changes.removed.length : 0,
      source: data?.source?.label || "Catálogo local",
      sourceDetail: data?.source?.detail || "",
    };
  }

  async function loadTrackLibrarySnapshot() {
    if (trackCatalogLoading) return;
    trackCatalogLoading = true;
    trackCatalogError = "";
    if (organizationSubtab === "track_library") renderTrackLibrary();

    try {
      const { response, payload } = await getCatalog();
      if (!response.ok) {
        throw new Error(payload?.error || "Não foi possível carregar o snapshot da biblioteca.");
      }
      trackCatalogSnapshot = payload;
    } catch (error) {
      trackCatalogError = error?.message || "Não foi possível carregar o snapshot da biblioteca.";
    } finally {
      trackCatalogLoading = false;
      if (organizationSubtab === "track_library") renderTrackLibrary();
    }
  }

  function renderTrackLibrary() {
    const workspace = ensureOrganizationWorkspace();
    if (!workspace) return;

    const config = {
      title: "Rastrear biblioteca",
      subtitle: "Localize obras, pastas e capítulos antes de qualquer análise.",
      status: trackCatalogLoading ? "Atualizando" : "Somente leitura",
    };
    updateTopbar(config);
    setOrganizationMode(true);

    if (trackCatalogLoading && !trackCatalogSnapshot) {
      workspace.innerHTML = `
        <header class="organization-workspace-head">
          <div>
            <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
            <h2>Rastrear biblioteca</h2>
            <p>Leia o estado atual da biblioteca sem mover ou renomear arquivos.</p>
          </div>
          <span class="organization-stage-status">Atualizando</span>
        </header>
        <section class="organization-full-content organization-track-content">
          <div class="organization-track-state">
            <strong>Carregando snapshot atual...</strong>
            <p>Consultando o catálogo já mantido pela Manhwateca.</p>
          </div>
        </section>
      `;
      return;
    }

    if (trackCatalogError && !trackCatalogSnapshot) {
      workspace.innerHTML = `
        <header class="organization-workspace-head">
          <div>
            <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
            <h2>Rastrear biblioteca</h2>
            <p>Leia o estado atual da biblioteca sem mover ou renomear arquivos.</p>
          </div>
          <span class="organization-stage-status">Indisponível</span>
        </header>
        <section class="organization-full-content organization-track-content">
          <div class="organization-track-state error">
            <strong>Não foi possível carregar o snapshot.</strong>
            <p>${escapeHtml(trackCatalogError)}</p>
            <button type="button" class="secondary-action" data-organization-track-refresh>Tentar novamente</button>
          </div>
        </section>
      `;
      return;
    }

    const metrics = catalogSnapshotMetrics(trackCatalogSnapshot);
    const hasSnapshot = Boolean(trackCatalogSnapshot);
    const changeTotal = metrics.added + metrics.updated + metrics.removed;

    workspace.innerHTML = `
      <header class="organization-workspace-head">
        <div>
          <span class="eyebrow">ORGANIZAÇÃO LOCAL</span>
          <h2>Rastrear biblioteca</h2>
          <p>Leia o estado atual da biblioteca sem mover ou renomear arquivos.</p>
        </div>
        <span class="organization-stage-status">${trackCatalogLoading ? "Atualizando" : "Somente leitura"}</span>
      </header>

      <section class="organization-full-content organization-track-content">
        <p class="organization-full-lead">
          O rastreamento reutiliza o catálogo atual da Manhwateca. Uma nova leitura atualiza o PostgreSQL e os indicadores da Biblioteca.
        </p>

        <section class="organization-progress-card">
          <div class="organization-progress-head">
            <div>
              <strong>${hasSnapshot ? "Snapshot concluído" : "Snapshot não carregado"}</strong>
              <small title="${escapeHtml(metrics.sourceDetail)}">Fonte: ${escapeHtml(metrics.source)}</small>
            </div>
            <span>${hasSnapshot ? "100%" : "—"}</span>
          </div>

          <div class="organization-progress" aria-label="Estado do snapshot">
            <div class="organization-progress-bar" style="width:${hasSnapshot ? "100%" : "0%"}"></div>
          </div>

          <div class="organization-timeline">
            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div>
                <b>Obras catalogadas</b>
                <small>${metrics.works} obra(s) disponíveis no catálogo atual.</small>
              </div>
              <span class="organization-step-status">${metrics.works}</span>
            </div>

            <div class="organization-step">
              <span class="organization-step-marker">✓</span>
              <div>
                <b>Capítulos indexados</b>
                <small>${metrics.chapters} capítulo(s) contabilizados no snapshot atual.</small>
              </div>
              <span class="organization-step-status">${metrics.chapters}</span>
            </div>

            <div class="organization-step">
              <span class="organization-step-marker">${metrics.review ? "!" : "✓"}</span>
              <div>
                <b>Conferências necessárias</b>
                <small>${metrics.review
                  ? `${metrics.review} obra(s) possuem ocorrências que precisam de revisão.`
                  : "Nenhuma conferência foi indicada pelo catálogo atual."}</small>
              </div>
              <span class="organization-step-status ${metrics.review ? "neutral" : ""}">${metrics.review}</span>
            </div>

            <div class="organization-step">
              <span class="organization-step-marker">${metrics.unparsed ? "!" : "✓"}</span>
              <div>
                <b>Arquivos não interpretados</b>
                <small>${metrics.unparsed
                  ? `${metrics.unparsed} arquivo(s) não foram interpretados pelo catálogo.`
                  : "Nenhum arquivo não interpretado foi informado."}</small>
              </div>
              <span class="organization-step-status ${metrics.unparsed ? "neutral" : ""}">${metrics.unparsed}</span>
            </div>
          </div>
        </section>

        <div class="organization-track-changes">
          <span>Última catalogação</span>
          <strong>${changeTotal
            ? `${metrics.added} nova(s) · ${metrics.updated} alterada(s) · ${metrics.removed} removida(s)`
            : "Nenhuma mudança registrada"}</strong>
        </div>

        <section class="organization-full-action">
          <div class="organization-action-copy">
            <small>PRÓXIMA AÇÃO</small>
            <strong>${hasSnapshot ? "Usar o snapshot concluído" : "Rastrear biblioteca"}</strong>
            <p>${hasSnapshot
              ? "Avance para revisar a estrutura identificada ou execute uma nova leitura da biblioteca."
              : "Execute uma leitura para atualizar o catálogo antes de continuar."}</p>
          </div>

          <div class="organization-actions">
            <button type="button"
                    class="secondary-action"
                    data-organization-task="catalog_scan"
                    data-confirmation="true"
                    ${trackCatalogLoading ? "disabled" : ""}>
              ${trackCatalogLoading ? "Rastreando..." : "Rastrear novamente"}
            </button>
            <button type="button"
                    class="primary-action"
                    data-organization-go="review_structure"
                    ${hasSnapshot ? "" : "disabled"}>
              Usar snapshot
            </button>
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
          <p>Revise o impacto das alterações antes da confirmação final.</p>
        </div>
        <span class="organization-stage-status">Pronto para aplicar</span>
      </header>

      <section class="organization-full-content organization-apply-content">
        <p class="organization-full-lead">Última conferência antes de renomear e mover itens.</p>

        <div class="organization-summary-grid">
          <article class="organization-apply-summary success">
            <h3>24 mudanças prontas</h3>
            <p class="organization-ready-lines">✓ 18 renomeações<br>✓ 6 movimentos<br>✓ Nenhum conflito bloqueante</p>
          </article>

          <article class="organization-apply-summary">
            <h3>Impacto da aplicação</h3>
            <p>Destino: Biblioteca local<br>Modo: aplicação com log<br>Rollback: disponível</p>
          </article>
        </div>

        <section class="organization-checklist">
          <div class="organization-check">
            <span class="organization-step-marker">✓</span>
            <div>
              <b>Renomear capítulos</b>
              <small>18 arquivos serão padronizados.</small>
            </div>
            <span class="organization-step-status">Pronto</span>
          </div>

          <div class="organization-check">
            <span class="organization-step-marker">✓</span>
            <div>
              <b>Mover pastas</b>
              <small>6 itens serão reorganizados.</small>
            </div>
            <span class="organization-step-status">Pronto</span>
          </div>
        </section>

        <section class="organization-full-action">
          <div class="organization-action-copy">
            <small>PRÓXIMA AÇÃO</small>
            <strong>Aplicar organização</strong>
            <p>A operação será registrada e poderá ser revertida.</p>
          </div>

          <div class="organization-actions">
            <button type="button" class="secondary-action" data-organization-go="review_pending">Voltar às pendências</button>
            <button type="button" class="primary-action" data-organization-task="apply_organization" data-confirmation="true">Aplicar organização</button>
          </div>
        </section>
      </section>
    `;
  }

  function handleOrganizationClick(event) {
    if (event.target.closest("[data-organization-track-refresh]")) {
      loadTrackLibrarySnapshot();
      return;
    }
    const itemCheckbox = event.target.closest("[data-organization-item-checkbox]");
    if (itemCheckbox) {
      const key = itemCheckbox.dataset.organizationKey || "";
      if (itemCheckbox.checked) organizationCheckedKeys.add(key);
      else organizationCheckedKeys.delete(key);
      itemCheckbox.closest(".organization-list-item")?.classList.toggle("selected", itemCheckbox.checked);
      return;
    }

    const item = event.target.closest("[data-organization-key]");
    if (item) {
      const key = item.dataset.organizationKey || "";
      const allItems = getListData(organizationSubtab);
      const nextIndex = allItems.findIndex(candidate => organizationItemKey(candidate) === key);
      if (nextIndex >= 0) selectedIndex = nextIndex;
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

    const state = organizationStateFor(organizationSubtab);
    state.search = workspace.querySelector("[data-organization-search]")?.value || "";
    state.quantity = Number.parseInt(
      workspace.querySelector("[data-organization-quantity]")?.value || "5",
      10
    );
    state.filter = workspace.querySelector("[data-organization-filter]")?.value || "Todas";
    state.group = workspace.querySelector("[data-organization-group]")?.value || "Todas";

    const visible = filteredOrganizationItems(
      getListData(organizationSubtab),
      state
    ).slice(0, state.quantity);

    const list = workspace.querySelector("[data-organization-list]");
    if (list) list.innerHTML = renderOrganizationItems(visible);

    if (event.target.matches("[data-organization-select-all]")) {
      list?.querySelectorAll("[data-organization-item-checkbox]").forEach(input => {
        input.checked = event.target.checked;
        const key = input.dataset.organizationKey || "";
        if (input.checked) organizationCheckedKeys.add(key);
        else organizationCheckedKeys.delete(key);
        input.closest(".organization-list-item")?.classList.toggle("selected", input.checked);
      });
    }
  }

  function setSubtab(subtab) {
    organizationSubtab = subtab;
    selectedIndex = 0;
    organizationCheckedKeys = new Set();
    if (subtab === "track_library") {
      renderTrackLibrary();
      loadTrackLibrarySnapshot();
      return;
    }
    if (subtab === "apply_organization") {
      renderApplyOrganization();
      return;
    }
    if (subtab === "review_structure") {
      renderOrganizationSubtab();
      if (!structureReviewSnapshot) loadStructureReview();
      return;
    }
    if (subtab === "standardize_names") {
      renderOrganizationSubtab();
      if (!namingReviewSnapshot) loadNamingReview();
      return;
    }
    if (subtabConfig[subtab]) {
      renderOrganizationSubtab();
      return;
    }
    setOrganizationMode(false);
    restoreTopbar();
  }


  window.addEventListener("manhwateca:catalog-loaded", event => {
    if (!event.detail?.data) return;
    trackCatalogSnapshot = event.detail.data;
    trackCatalogError = "";
    trackCatalogLoading = false;
    if (organizationSubtab === "track_library") renderTrackLibrary();
    if (organizationSubtab === "review_structure") renderOrganizationSubtab();
  });

  window.addEventListener("manhwateca:organization-subtab", event => {
    setSubtab(event.detail?.subtab || "track_library");
  });

  if (location.hash === "#organization-v2" && !organizationSubtab) {
    const active = document.querySelector("[data-sidebar-organization-subtab].active");
    setSubtab(active?.dataset.sidebarOrganizationSubtab || "track_library");
  }

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
