import { escapeHtml } from "../utils/html.js";

export function emptyState(message, className = "loading") {
  return `<span class="${escapeHtml(className)}">${escapeHtml(message)}</span>`;
}

