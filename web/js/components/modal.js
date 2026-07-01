export function openModal(dialog) {
  if (dialog?.showModal) dialog.showModal();
}

export function closeModal(dialog) {
  if (dialog?.close) dialog.close();
}

