import { selectCandidate, selectCurrentId, selectManualId, selectNoMatch } from "./flowDecisionHandlers.js";

export function handleDecisionWorkspaceClick(event, context) {
  const target = event.target;
  const mode = target.closest("[data-flow-workspace-mode]");
  if (mode) { context.setWorkspaceMode?.(mode.dataset.flowWorkspaceMode); return true; }
  const tab = target.closest("[data-flow-review-tab]");
  if (tab) { context.setReviewDetailTab?.(tab.dataset.flowReviewTab); return true; }
  if (target.closest("[data-flow-next-review]")) { context.nextReview?.(); return true; }
  if (target.closest("[data-flow-batch-open]")) { context.openBatch?.(); return true; }
  if (target.closest("[data-flow-batch-close]")) { context.closeBatch?.(); return true; }
  if (target.closest("[data-flow-batch-check]")) { context.checkBatch?.(); return true; }
  if (target.closest("[data-flow-batch-apply]")) { context.applyBatch?.(); return true; }
  if (target.closest("[data-flow-correction-open]")) { context.openCorrection?.(); return true; }
  if (target.closest("[data-flow-correction-close]")) { context.closeCorrection?.(); return true; }
  const edit = target.closest("[data-flow-edit-review]");
  if (edit) { context.editReview?.(edit.dataset.flowEditReview); return true; }
  const remove = target.closest("[data-flow-remove-review]");
  if (remove) { context.removeReview?.(remove.dataset.flowRemoveReview); return true; }
  const copy = target.closest("[data-flow-copy-title]");
  if (copy) {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(copy.dataset.flowCopyTitle || "")
        .then(() => context.setFeedback?.("Título copiado.", "success"))
        .catch(() => context.setFeedback?.("Não foi possível copiar o título.", "error"));
    } else context.setFeedback?.("Cópia indisponível neste navegador.", "error");
    return true;
  }
  const save = target.closest("[data-flow-save-review]");
  if (save) { context.saveCurrentReviewDecision(save.dataset.flowSaveReview); return true; }
  const review = target.closest("[data-flow-review-work]");
  if (review) {
    context.setActiveReviewKey(review.dataset.flowReviewWork);
    context.renderWorkflow();
    return true;
  }
  const candidate = target.closest("[data-flow-select-id]");
  if (candidate) {
    const decisions = selectCandidate(context.getSelectedDecisions(), candidate);
    context.validateAndSetReviewDecision?.(decisions, candidate.dataset.flowWork);
    return true;
  }
  const manual = target.closest("[data-flow-manual-work]");
  if (manual) {
    const result = selectManualId(context.getSelectedDecisions(), manual, context.area);
    if (result.error) {
      const field = manual.closest(".decision-workspace-field, .flow-manual-row");
      const feedback = field?.querySelector("[data-flow-manual-feedback]");
      if (feedback) {
        feedback.textContent = result.error;
        feedback.className = "flow-manual-feedback error";
      }
      field?.querySelector("[data-flow-manual-id]")?.setAttribute("aria-invalid", "true");
    } else context.validateAndSetReviewDecision?.(result.selectedDecisions, manual.dataset.flowManualWork);
    return true;
  }
  const currentId = target.closest("[data-flow-confirm-current-id]");
  if (currentId) {
    const result = selectCurrentId(context.getSelectedDecisions(), currentId);
    if (result.error) context.setFeedback(result.error, "error");
    else context.validateAndSetReviewDecision?.(result.selectedDecisions, currentId.dataset.flowWork);
    return true;
  }
  const noMatch = target.closest("[data-flow-no-match]");
  if (noMatch) {
    context.setReviewManualDraft?.(noMatch.dataset.flowWork, "");
    context.setSelectedDecisions(selectNoMatch(context.getSelectedDecisions(), noMatch));
    context.renderWorkflow();
    return true;
  }
  const ignore = target.closest("[data-flow-ignore-review]");
  if (ignore) { context.ignoreCurrentReview?.(ignore.dataset.flowWork); return true; }
  return false;
}

export function handleDecisionWorkspaceChange(event, context) {
  if (!event.target.matches("[data-flow-batch-choice]")) return false;
  context.setBatchChoice?.(event.target.dataset.flowBatchChoice, event.target.checked);
  return true;
}
