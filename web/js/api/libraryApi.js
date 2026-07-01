import { getJson, postJson } from "./client.js";

export function getCatalog() {
  return getJson("/api/catalog");
}

export function reconcileAliases() {
  return postJson("/api/catalog/reconcile-aliases");
}

export function catalogOne(payload) {
  return postJson("/api/catalog/catalog-one", payload);
}
