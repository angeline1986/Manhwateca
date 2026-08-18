import { getJson, postJson } from "./client.js";

export function getCatalog() {
  return getJson("/api/catalog");
}

export function getStructureReview() {
  return getJson("/api/organization/structure-review");
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
