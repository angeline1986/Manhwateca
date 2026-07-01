import { getJson } from "./client.js";

export function getNotionStatus() {
  return getJson("/api/notion/status");
}

export function getMetadataStatus() {
  return getJson("/api/notion/metadata");
}
