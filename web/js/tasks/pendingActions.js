export function pendingRequiresConfirmation(action) {
  return [
    "apply_organization",
    "apply_renaming",
    "notion_apply_batch",
    "notion_update_existing",
    "notion_csv_apply",
    "catalog_scan",
  ].includes(action);
}

export function initPendingActions({ lists, organizationPendingList, startTask, goToNextStep }) {
  function handlePendingClick(event) {
    const list = event.currentTarget;
    const card = event.target.closest(".pending-card");
    if (!card || !list.contains(card)) return;
    const action = card.dataset.action;
    if (action) {
      startTask(action, pendingRequiresConfirmation(action));
      return;
    }
    if (card.dataset.pendingPage) {
      if (
        list === organizationPendingList
        && card.dataset.pendingPanel === "idReviewPanel"
      ) {
        goToNextStep("organization", "organizationIdReviewPanel");
        return;
      }
      goToNextStep(card.dataset.pendingPage, card.dataset.pendingPanel || "");
    }
  }

  lists
    .filter(Boolean)
    .forEach(list => list.addEventListener("click", handlePendingClick));

  return { handlePendingClick };
}
