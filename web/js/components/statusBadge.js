import { escapeHtml } from "../utils/html.js";

export function statusBadge(label, status = "pending") {
  return `<span class="state ${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

