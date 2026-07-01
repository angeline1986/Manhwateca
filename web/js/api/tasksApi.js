import { getJson, postJson } from "./client.js";

export function getActions() {
  return getJson("/api/actions");
}

export function getTasks() {
  return getJson("/api/tasks");
}

export function startTaskAction(action, payload = {}) {
  return postJson(`/api/tasks/${action}`, payload);
}
