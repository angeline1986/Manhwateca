import { getJson } from "./client.js";

export function getNotionStatus() {
  return getJson("/api/notion/status");
}

export function getMetadataStatus() {
  return getJson("/api/notion/metadata");
}

export function getSyncCandidates(status = "default") {
  return getJson(`/api/notion/sync-candidates?status=${encodeURIComponent(status)}`);
}
