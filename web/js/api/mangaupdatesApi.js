import { getJson, postJson } from "./client.js";

export function getReviewItems() {
  return getJson("/api/mangaupdates/review");
}

export function getMangaUpdatesStatus() {
  return getJson("/api/mangaupdates/status");
}

export function getMangaUpdatesWorks(params = {}) {
  const query = new URLSearchParams(params);
  return getJson(`/api/mangaupdates/works?${query.toString()}`);
}

export function getConfirmedMangaUpdatesIdCandidates(params = {}) {
  const query = new URLSearchParams(params);
  return getJson(`/api/mangaupdates/confirmed-id/candidates?${query.toString()}`);
}

export function searchMangaUpdates(payload) {
  return postJson("/api/mangaupdates/search", payload);
}

export function previewConfirmedMangaUpdatesIdCorrection(payload) {
  return postJson("/api/mangaupdates/confirmed-id/preview", payload);
}

export function applyConfirmedMangaUpdatesIdCorrection(payload) {
  return postJson("/api/mangaupdates/confirmed-id/apply", payload);
}

export function translateText(payload) {
  return postJson("/api/translate", payload);
}

export function applyMangaUpdatesDecisions(payload) {
  return postJson("/api/mangaupdates/decisions/apply", payload);
}

export function validateMangaUpdatesDecisions(payload) {
  return postJson("/api/mangaupdates/decisions/validate", payload);
}
