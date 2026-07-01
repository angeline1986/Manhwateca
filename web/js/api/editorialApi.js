import { getJson, postJson } from "./client.js";

export function getEditorial() {
  return getJson("/api/editorial");
}

export function saveEditorial(payload) {
  return postJson("/api/editorial", payload);
}

export function saveReviewNote(payload) {
  return postJson("/api/review-notes", payload);
}
