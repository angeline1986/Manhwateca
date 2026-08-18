import { getJson, postJson } from "./client.js";

export function getCatalog() {
  return getJson("/api/catalog");
}

export function getStructureReview() {
  return getJson("/api/organization/structure-review");
}

export function getFolderOrganizationReview() {
  return getJson("/api/organization/folder-review");
}

export function getNamingReview() {
  return getJson("/api/organization/naming-review");
}

export function reconcileAliases() {
  return postJson("/api/catalog/reconcile-aliases");
}

export function catalogOne(payload) {
  return postJson("/api/catalog/catalog-one", payload);
}

export function getChapterReview() {
  return getJson("/api/organization/chapter-review");
}

export function getOrganizationPendingReview() {
  return getJson("/api/organization/pending-review");
}

export function createOrganizationDecision(payload) {
  return postJson("/api/organization/decision", payload);
}

export function resolveOrganizationDecision(payload) {
  return postJson("/api/organization/decision/resolve", payload);
}

export function getTaskHistory() {
  return getJson("/api/tasks");
}
