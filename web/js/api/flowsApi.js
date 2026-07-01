import { getJson, postJson } from "./client.js";

export async function getFlowStatus() {
  return getJson("/api/flows/status");
}

export async function getFlowIntegrations() {
  return getJson("/api/flows/integrations");
}

export async function getFlowHistory() {
  return getJson("/api/flows/history");
}

export async function getFlowsState() {
  const [status, integrations, history] = await Promise.all([
    getFlowStatus(),
    getFlowIntegrations(),
    getFlowHistory(),
  ]);
  return {
    status: status.payload,
    integrations: integrations.payload,
    history: history.payload,
  };
}

export function startWorkflow(payload) {
  return postJson("/api/flows/start", payload);
}

export function runFlowStage(stageId) {
  return postJson(`/api/flows/stages/${stageId}/run`);
}

export function cancelWorkflowRun() {
  return postJson("/api/flows/cancel");
}
