import {
  applySelectedDecisions,
  selectCandidate,
  selectCurrentId,
  selectManualId,
  selectNoMatch,
} from "./flowDecisionHandlers.js";

export function handleFlowsClick(event, context) {
  if (event.target.closest("[data-flow-select-all-decisions]")) {
    event.preventDefault();
    setDecisionChecks(context.area, true);
    return updateApplySummary(context.area);
  }
  if (event.target.closest("[data-flow-clear-decisions]")) {
    event.preventDefault();
    setDecisionChecks(context.area, false);
    return updateApplySummary(context.area);
  }
  const subtab = event.target.closest("[data-flow-subtab]");
  if (subtab) return context.setActiveSubtab(subtab.dataset.flowSubtab);
  if (event.target.closest("[data-flow-review-again]")) {
    context.reviewAgain();
    return;
  }
  if (event.target.closest("[data-flow-save-review]")) {
    context.saveCurrentReviewDecision();
    return;
  }
  const worksPageAction = event.target.closest("[data-flow-works-page]");
  if (worksPageAction) {
    context.setWorksPage(Number(worksPageAction.dataset.flowWorksPage || 1));
    context.loadWorkflow();
    return;
  }
  const selectedCandidate = event.target.closest("[data-flow-select-id]");
  if (selectedCandidate) {
    context.setSelectedDecisions(selectCandidate(
      context.getSelectedDecisions(),
      selectedCandidate,
    ));
    context.setFeedback("Decisão marcada para aplicação.", "info");
    context.renderWorkflow();
    return;
  }
  const reviewWork = event.target.closest("[data-flow-review-work]");
  if (reviewWork) {
    context.setActiveReviewKey(reviewWork.dataset.flowReviewWork);
    context.renderWorkflow();
    return;
  }
  const manualDecision = event.target.closest("[data-flow-manual-work]");
  if (manualDecision) {
    const result = selectManualId(
      context.getSelectedDecisions(),
      manualDecision,
      context.area,
    );
    if (result.error) context.setFeedback(result.error, "error");
    else {
      context.setSelectedDecisions(result.selectedDecisions);
      context.setFeedback("ID manual marcado para aplicação.", "info");
      context.renderWorkflow();
    }
    return;
  }
  const currentIdDecision = event.target.closest("[data-flow-confirm-current-id]");
  if (currentIdDecision) {
    const result = selectCurrentId(
      context.getSelectedDecisions(),
      currentIdDecision,
    );
    if (result.error) context.setFeedback(result.error, "error");
    else {
      context.setSelectedDecisions(result.selectedDecisions);
      context.setFeedback("ID atual marcado para confirmação.", "info");
      context.renderWorkflow();
    }
    return;
  }
  const noMatchDecision = event.target.closest("[data-flow-no-match]");
  if (noMatchDecision) {
    context.setSelectedDecisions(selectNoMatch(
      context.getSelectedDecisions(),
      noMatchDecision,
    ));
    context.setFeedback("Sem correspondência marcado para aplicação.", "info");
    context.renderWorkflow();
    return;
  }
  const ignoreDecision = event.target.closest("[data-flow-ignore-review]");
  if (ignoreDecision) {
    context.ignoreCurrentReview?.(ignoreDecision.dataset.flowWork);
    return;
  }
  if (event.target.closest("[data-flow-apply-decisions]")) {
    const queueIds = checkedDecisionIds(context.area);
    applySelectedDecisions(context.readyDecisions(), {
      errorMessage: context.errorMessage,
      reload: context.loadWorkflow,
      setFeedback: context.setFeedback,
    }, queueIds).then(updated => context.afterApply(updated));
    return;
  }
  if (event.target.closest("[data-page]")) {
    context.showPage(event.target.closest("[data-page]").dataset.page);
    return;
  }
  if (event.target.closest("[data-flow-cancel]")) return context.cancelWorkflow();
  if (event.target.closest("[data-flow-refresh]")) return context.loadWorkflow();
  if (event.target.closest("[data-confirmed-id-preview]")) {
    event.preventDefault();
    context.previewConfirmedIdCorrection?.();
    return;
  }
  const confirmedIdCandidate = event.target.closest("[data-confirmed-id-select-work]");
  if (confirmedIdCandidate) {
    event.preventDefault();
    context.selectConfirmedIdCorrectionWork?.(Number(confirmedIdCandidate.dataset.confirmedIdSelectWork));
    return;
  }
  const confirmedIdPageButton = event.target.closest("[data-confirmed-id-page-action], [data-confirmed-id-page-number]");
  if (confirmedIdPageButton) {
    event.preventDefault();
    const current = Number(context.confirmedIdCorrection?.page || 1);
    const action = confirmedIdPageButton.dataset.confirmedIdPageAction;
    const requested = Number(confirmedIdPageButton.dataset.confirmedIdPageNumber);
    let next = current;
    if (action === "prev") next -= 1;
    else if (action === "next") next += 1;
    else if (Number.isFinite(requested)) next = requested;
    context.setConfirmedIdCorrectionPage?.(next);
    return;
  }
  if (event.target.closest("[data-confirmed-id-apply]")) {
    event.preventDefault();
    context.applyConfirmedIdCorrection?.();
    return;
  }
  const createNotionPage = event.target.closest("[data-notion-create-page]");
  if (createNotionPage) {
    event.preventDefault();
    context.createMissingNotionPage?.(Number(createNotionPage.dataset.notionCreateWorkId));
    return;
  }
  const notionSyncPageButton = event.target.closest("[data-notion-sync-page-action], [data-notion-sync-page-number]");
  if (notionSyncPageButton) {
    event.preventDefault();
    updateNotionSyncPage(context.area, notionSyncPageButton);
    return;
  }
  const metadataPageButton = event.target.closest("[data-metadata-page-action], [data-metadata-page-number]");
  if (metadataPageButton) {
    event.preventDefault();
    updateMetadataPage(context.area, metadataPageButton);
    return;
  }
  const metadataCard = event.target.closest("[data-metadata-expandable]");
  if (metadataCard) {
    toggleMetadataDetails(event, metadataCard, context.area);
    return;
  }
  if (event.target.closest("[data-flow-run-stage], [data-flow-start]")) {
    context.runCurrentFlowStage();
  }
}

export function handleFlowsChange(event, area, context = {}) {
  if (event.target.matches("[data-flow-apply-choice]")) updateApplySummary(area);
  if (event.target.matches("[data-metadata-select-all]")) {
    setMetadataChecks(area, event.target.checked);
    updateMetadataSummary(area);
  }
  if (event.target.matches("[data-metadata-choice]")) updateMetadataSummary(area);
  if (event.target.matches("[data-notion-sync-select-all]")) {
    setNotionSyncChecks(area, event.target.checked);
    updateNotionSyncSummary(area);
  }
  if (event.target.matches("[data-notion-sync-choice]")) updateNotionSyncSummary(area);
  if (event.target.matches("[data-notion-sync-status-filter]")) {
    context.setNotionSyncCandidateStatus?.(event.target.value || "default");
  }
  if (event.target.matches("[data-notion-sync-page-size-select]")) {
    const card = area.querySelector("[data-notion-sync-candidates]");
    if (card) {
      card.dataset.notionSyncPage = "1";
      card.dataset.notionSyncPageSize = event.target.value || "5";
    }
    applyNotionSyncPagination(area);
    updateNotionSyncSummary(area);
  }
  if (event.target.matches("[data-metadata-page-size-select]")) {
    const card = area.querySelector("[data-metadata-page]");
    if (card) {
      card.dataset.metadataPage = "1";
      card.dataset.metadataPageSize = event.target.value || "5";
    }
    applyMetadataPagination(area);
    updateMetadataSummary(area);
  }
}

export function handleFlowsInput(event, area, context = {}) {
  if (event.target.matches("[data-flow-review-search]")) {
    context.setReviewSearchQuery?.(event.target.value || "");
  }
  if (event.target.matches("[data-notion-sync-search]")) {
    filterNotionSyncCandidates(area, event.target.value || "");
    updateNotionSyncSummary(area);
  }
  if (event.target.matches("[data-confirmed-id-search]")) {
    context.searchConfirmedIdCorrectionWorks?.(event.target.value || "");
  }
  if (event.target.matches("[data-confirmed-id-new]")) {
    context.setConfirmedIdCorrectionNewWorkCode?.(event.target.value || "");
  }
}

function checkedDecisionIds(area) {
  return [...area.querySelectorAll("[data-flow-apply-choice]:checked")]
    .map(input => input.dataset.flowApplyChoice)
    .filter(Boolean);
}

function setDecisionChecks(area, checked) {
  area.querySelectorAll("[data-flow-apply-choice]:not(:disabled)")
    .forEach(input => { input.checked = checked; });
}

function updateApplySummary(area) {
  const choices = [...area.querySelectorAll("[data-flow-apply-choice]:not(:disabled)")];
  const selected = choices.filter(input => input.checked).length;
  const selectedText = area.querySelector("[data-flow-apply-selected]");
  const helper = area.querySelector("[data-flow-apply-helper]");
  const button = area.querySelector("[data-flow-apply-decisions]");
  const impactIds = area.querySelector("[data-flow-impact-ids]");
  const skipped = area.querySelector("[data-flow-impact-skipped]");
  if (selectedText) selectedText.textContent = selectedLabel(selected);
  if (impactIds) impactIds.textContent = String(selected);
  if (skipped) skipped.textContent = String(choices.length - selected);
  if (helper) helper.textContent = helperLabel(selected);
  if (!button) return;
  button.disabled = selected === 0;
  button.textContent = selected
    ? `Aplicar ${selected} ${selected === 1 ? "decisão" : "decisões"}`
    : "Selecione decisões";
}

function setMetadataChecks(area, checked) {
  visibleMetadataChoices(area)
    .forEach(input => { input.checked = checked; });
}

function updateMetadataSummary(area) {
  const choices = [...area.querySelectorAll("[data-metadata-choice]")];
  const visibleChoices = visibleMetadataChoices(area);
  const selected = choices.filter(input => input.checked).length;
  const fields = choices
    .filter(input => input.checked)
    .reduce((total, input) => total + Number(input.dataset.metadataFields || 0), 0);
  const selectAll = area.querySelector("[data-metadata-select-all]");
  const selectedText = area.querySelector("[data-metadata-selected]");
  const fieldsText = area.querySelector("[data-metadata-fields-count]");
  const skippedText = area.querySelector("[data-metadata-not-selected]");
  const estimatedTime = area.querySelector("[data-metadata-estimated-time]");
  const button = area.querySelector("[data-metadata-run]");
  if (selectAll) {
    const visibleSelected = visibleChoices.filter(input => input.checked).length;
    selectAll.checked = Boolean(visibleChoices.length && visibleSelected === visibleChoices.length);
    selectAll.indeterminate = visibleSelected > 0 && visibleSelected < visibleChoices.length;
  }
  if (selectedText) {
    selectedText.textContent = `${selected} ${selected === 1 ? "selecionada" : "selecionadas"}`;
  }
  if (fieldsText) fieldsText.textContent = String(fields);
  if (skippedText) skippedText.textContent = String(choices.length - selected);
  if (estimatedTime) estimatedTime.textContent = estimateMetadataTime(selected);
  if (!button) return;
  button.disabled = selected === 0;
  button.textContent = selected
    ? `Sincronizar ${selected} ${selected === 1 ? "obra" : "obras"}`
    : "Selecione obras";
}

function updateMetadataPage(area, button) {
  const card = area.querySelector("[data-metadata-page]");
  if (!card) return;
  const current = Number(card.dataset.metadataPage || 1);
  const pageSize = Number(card.dataset.metadataPageSize || 5);
  const total = area.querySelectorAll("[data-metadata-choice]").length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const action = button.dataset.metadataPageAction;
  const requested = Number(button.dataset.metadataPageNumber);
  let next = current;
  if (action === "prev") next -= 1;
  else if (action === "next") next += 1;
  else if (Number.isFinite(requested)) next = requested;
  card.dataset.metadataPage = String(Math.min(Math.max(next, 1), pages));
  applyMetadataPagination(area);
  updateMetadataSummary(area);
}

function applyMetadataPagination(area) {
  const card = area.querySelector("[data-metadata-page]");
  if (!card) return;
  const page = Number(card.dataset.metadataPage || 1);
  const pageSize = Number(card.dataset.metadataPageSize || 5);
  const items = [...area.querySelectorAll("[data-metadata-index]")];
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(Math.max(page, 1), pages);
  card.dataset.metadataPage = String(safePage);
  const start = (safePage - 1) * pageSize;
  const end = start + pageSize;
  items.forEach((item, index) => {
    item.hidden = index < start || index >= end;
  });
  renderMetadataPager(area, safePage, pages);
}

function renderMetadataPager(area, page, pages) {
  const pager = area.querySelector("[data-metadata-pager]");
  if (!pager) return;
  const nextPage = Math.min(page + 1, pages);
  pager.innerHTML = `
    <button class="flow-page-link" type="button" data-metadata-page-action="prev" ${page <= 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>
    <button class="flow-page-link active" type="button" data-metadata-page-number="${page}">${page}</button>
    <button class="flow-page-link" type="button" data-metadata-page-number="${nextPage}" ${page >= pages ? "hidden" : ""}>${nextPage}</button>
    <button class="flow-page-link" type="button" data-metadata-page-action="next" ${page >= pages ? "disabled" : ""} aria-label="Próxima página">›</button>
  `;
}

function visibleMetadataChoices(area) {
  return [...area.querySelectorAll("[data-metadata-choice]")]
    .filter(input => !input.closest("[data-metadata-index]")?.hidden);
}

function setNotionSyncChecks(area, checked) {
  visibleNotionSyncChoices(area)
    .forEach(input => { input.checked = checked; });
}

function updateNotionSyncSummary(area) {
  const choices = [...area.querySelectorAll("[data-notion-sync-choice]:not(:disabled)")];
  const visibleChoices = visibleNotionSyncChoices(area);
  const selected = choices.filter(input => input.checked).length;
  const selectAll = area.querySelector("[data-notion-sync-select-all]");
  const selectedText = area.querySelector("[data-notion-sync-selected]");
  const button = area.querySelector("[data-flow-run-stage]");
  if (selectAll) {
    const visibleSelected = visibleChoices.filter(input => input.checked).length;
    selectAll.checked = Boolean(visibleChoices.length && visibleSelected === visibleChoices.length);
    selectAll.indeterminate = visibleSelected > 0 && visibleSelected < visibleChoices.length;
    selectAll.disabled = visibleChoices.length === 0;
  }
  if (selectedText) {
    selectedText.textContent = `${selected} ${selected === 1 ? "selecionada" : "selecionadas"}`;
  }
  if (button) {
    const hasInheritedScope = Boolean(area.querySelector(".sync-notion-inherited-scope"));
    button.disabled = selected === 0 && !hasInheritedScope;
    button.textContent = selected
      ? (selected === 1 ? "Sincronizar esta obra" : `Sincronizar ${selected} obras`)
      : (hasInheritedScope ? "Sincronizar escopo da jornada" : "Selecione obras");
  }
  updateNotionSyncFocusedCandidate(area);
  return visibleChoices;
}

function filterNotionSyncCandidates(area, value) {
  const query = String(value || "").trim().toLocaleLowerCase("pt-BR");
  area.querySelectorAll("[data-notion-sync-candidate]").forEach(item => {
    const text = item.dataset.notionSyncSearchText || "";
    item.dataset.notionSyncFiltered = Boolean(query) && !text.includes(query) ? "true" : "false";
  });
  const card = area.querySelector("[data-notion-sync-candidates]");
  if (card) card.dataset.notionSyncPage = "1";
  applyNotionSyncPagination(area);
  updateNotionSyncResults(area);
}

function updateNotionSyncPage(area, button) {
  const card = area.querySelector("[data-notion-sync-candidates]");
  if (!card) return;
  const current = Number(card.dataset.notionSyncPage || 1);
  const pageSize = Number(card.dataset.notionSyncPageSize || 5);
  const total = filteredNotionSyncItems(area).length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const action = button.dataset.notionSyncPageAction;
  const requested = Number(button.dataset.notionSyncPageNumber);
  let next = current;
  if (action === "prev") next -= 1;
  else if (action === "next") next += 1;
  else if (Number.isFinite(requested)) next = requested;
  card.dataset.notionSyncPage = String(Math.min(Math.max(next, 1), pages));
  applyNotionSyncPagination(area);
  updateNotionSyncSummary(area);
}

function applyNotionSyncPagination(area) {
  const card = area.querySelector("[data-notion-sync-candidates]");
  if (!card) return;
  const page = Number(card.dataset.notionSyncPage || 1);
  const pageSize = Number(card.dataset.notionSyncPageSize || 5);
  const items = filteredNotionSyncItems(area);
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(Math.max(page, 1), pages);
  card.dataset.notionSyncPage = String(safePage);
  const start = (safePage - 1) * pageSize;
  const end = start + pageSize;
  area.querySelectorAll("[data-notion-sync-candidate]").forEach(item => {
    item.hidden = true;
  });
  items.forEach((item, index) => {
    item.hidden = index < start || index >= end;
  });
  renderNotionSyncPager(area, safePage, pages);
  updateNotionSyncResults(area);
}

function renderNotionSyncPager(area, page, pages) {
  const pager = area.querySelector("[data-notion-sync-pager]");
  if (!pager) return;
  const nextPage = Math.min(page + 1, pages);
  pager.innerHTML = `
    <button class="flow-page-link" type="button" data-notion-sync-page-action="prev" ${page <= 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>
    <button class="flow-page-link active" type="button" data-notion-sync-page-number="${page}">${page}</button>
    <button class="flow-page-link" type="button" data-notion-sync-page-number="${nextPage}" ${page >= pages ? "hidden" : ""}>${nextPage}</button>
    <button class="flow-page-link" type="button" data-notion-sync-page-action="next" ${page >= pages ? "disabled" : ""} aria-label="Próxima página">›</button>
  `;
}

function filteredNotionSyncItems(area) {
  return [...area.querySelectorAll("[data-notion-sync-candidate]")]
    .filter(item => item.dataset.notionSyncFiltered !== "true");
}

function visibleNotionSyncChoices(area) {
  return [...area.querySelectorAll("[data-notion-sync-choice]:not(:disabled)")]
    .filter(input => !input.closest("[data-notion-sync-candidate]")?.hidden);
}

function updateNotionSyncResults(area) {
  const results = area.querySelector("[data-notion-sync-results]");
  if (!results) return;
  const count = filteredNotionSyncItems(area).length;
  results.textContent = `${count} ${count === 1 ? "resultado" : "resultados"}`;
}

function updateNotionSyncFocusedCandidate(area) {
  const checked = [...area.querySelectorAll("[data-notion-sync-choice]:checked")];
  const focused = checked[0]?.closest("[data-notion-sync-candidate]") || null;
  area.querySelectorAll("[data-notion-sync-candidate].is-selected")
    .forEach(item => item.classList.remove("is-selected"));
  if (focused) focused.classList.add("is-selected");

  const title = area.querySelector("[data-notion-sync-detail-title]");
  const status = area.querySelector("[data-notion-sync-detail-status]");
  const workCode = area.querySelector("[data-notion-sync-detail-work-code]");
  const page = area.querySelector("[data-notion-sync-detail-page]");
  const synced = area.querySelector("[data-notion-sync-detail-synced]");
  const cover = area.querySelector("[data-notion-sync-detail-cover]");
  if (!title || !workCode || !page || !synced) return;

  if (!focused) {
    title.textContent = "Nenhuma obra selecionada";
    workCode.textContent = "Não informado";
    page.textContent = "Não associada";
    synced.textContent = "Não informada";
    setNotionSyncCover(cover, "");
    if (status) {
      status.textContent = "";
      status.hidden = true;
    }
    return;
  }

  title.textContent = focused.dataset.notionSyncTitle || "Obra sem título";
  workCode.textContent = focused.dataset.notionSyncWorkCode || "Não informado";
  page.textContent = focused.dataset.notionSyncPageLabel || "Não associada";
  synced.textContent = focused.dataset.notionSyncSyncedLabel || "Não informada";
  setNotionSyncCover(cover, focused.dataset.notionSyncCoverUrl || "");
  if (status) {
    status.textContent = focused.dataset.notionSyncStatus || "Estado local não informado";
    status.hidden = false;
  }
}

function setNotionSyncCover(target, url) {
  if (!target) return;
  const source = String(url || "").trim();
  if (!source) {
    target.replaceChildren(document.createElement("span"));
    target.firstElementChild.textContent = "Sem capa";
    target.classList.add("is-empty");
    return;
  }
  const image = document.createElement("img");
  image.src = source;
  image.alt = "";
  target.replaceChildren(image);
  target.classList.remove("is-empty");
}

function estimateMetadataTime(selected) {
  if (!selected) return "~0s";
  const seconds = selected * 2;
  if (seconds < 60) return `~${seconds}s`;
  return `~${Math.ceil(seconds / 60)}min`;
}

function toggleMetadataDetails(event, card, area) {
  if (event.target.closest("input, button, a")) return;
  const expanded = card.getAttribute("aria-expanded") === "true";
  area.querySelectorAll("[data-metadata-expandable][aria-expanded='true']")
    .forEach(item => {
      if (item !== card) setMetadataExpanded(item, false);
    });
  setMetadataExpanded(card, !expanded);
}

function setMetadataExpanded(card, expanded) {
  card.setAttribute("aria-expanded", expanded ? "true" : "false");
  const arrow = card.querySelector(".metadata-item-arrow");
  if (arrow) arrow.textContent = expanded ? "▾" : "▸";
}

function selectedLabel(selected) {
  if (!selected) return "Nenhuma decisão selecionada";
  return `${selected} ${selected === 1 ? "selecionada" : "selecionadas"} para aplicar`;
}

function helperLabel(selected) {
  if (!selected) return "Selecione ao menos uma decisão para aplicar.";
  if (selected === 1) return "1 decisão será aplicada. As demais continuarão prontas para aplicar depois.";
  return "Você pode desmarcar obras que não deseja aplicar neste lote.";
}
