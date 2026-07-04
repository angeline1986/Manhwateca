import {
  applySelectedDecisions,
  selectCandidate,
  selectManualId,
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
  if (event.target.closest("[data-flow-run-stage], [data-flow-start]")) {
    context.runCurrentFlowStage();
  }
}

export function handleFlowsChange(event, area) {
  if (event.target.matches("[data-flow-apply-choice]")) updateApplySummary(area);
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

function selectedLabel(selected) {
  if (!selected) return "Nenhuma decisão selecionada";
  return `${selected} ${selected === 1 ? "selecionada" : "selecionadas"} para aplicar`;
}

function helperLabel(selected) {
  if (!selected) return "Selecione ao menos uma decisão para aplicar.";
  if (selected === 1) return "1 decisão será aplicada. As demais continuarão prontas para aplicar depois.";
  return "Você pode desmarcar obras que não deseja aplicar neste lote.";
}
