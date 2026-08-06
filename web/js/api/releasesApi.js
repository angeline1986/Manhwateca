import { getJson, postJson } from "./client.js";

export function getReleasesSummary() {
  return getJson("/api/dashboard/releases-summary");
}

export function getReleases(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  return getJson(`/api/releases?${query.toString()}`);
}

export function checkReleases() {
  return postJson("/api/releases/check");
}

export function markViewed(payload) {
  return postJson("/api/releases/mark-viewed", payload);
}
