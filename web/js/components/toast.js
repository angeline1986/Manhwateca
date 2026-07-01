export function showToast(element, message) {
  if (!element) return;
  element.textContent = message || "";
  element.hidden = !message;
}

