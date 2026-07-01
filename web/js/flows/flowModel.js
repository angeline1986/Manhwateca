import {
  ACTIVE_FLOW_STEP_SET,
  FLOW_STAGE_GROUPS,
} from "./flowConstants.js";

export function normalizeFlowsPayload(payload) {
  const execution = payload?.data?.execution;
  if (!execution) {
    return {
      steps: FLOW_STAGE_GROUPS.map(group => ({ id: group.id, label: group.title })),
      run: { status: "idle", results: {} },
    };
  }
  const results = {};
  for (const stage of execution.stages || []) {
    const messages = [
      ...(stage.messages || []).map(item => item.message),
      ...((stage.result?.warnings || []).map(item => item.message)),
      ...((stage.result?.errors || []).map(item => item.message)),
    ].filter(Boolean);
    results[stage.id] = {
      status: stage.status,
      metrics: stage.result?.metrics || {},
      messages,
      note: messages[0],
    };
  }
  return {
    steps: (execution.definitions || [])
      .filter(definition => ACTIVE_FLOW_STEP_SET.has(definition.id))
      .map(definition => ({ id: definition.id, label: definition.name })),
    run: {
      status: execution.status,
      current: execution.currentStage,
      started_at: execution.startedAt,
      finished_at: execution.finishedAt,
      results,
      notification: execution.errors?.[0]?.message
        || execution.warnings?.[0]?.message
        || null,
    },
  };
}

export function flowStageStatus(group, run) {
  const results = run.results || {};
  const statuses = group.steps.map(step => results[step]?.status).filter(Boolean);
  if (group.steps.includes(run.current)) return "running";
  if (statuses.includes("failed")) return "failed";
  if (statuses.includes("cancelled")) return "cancelled";
  if (statuses.includes("completed_with_warnings")) return "completed_with_warnings";
  if (group.steps.every(step => results[step]?.status === "completed")) {
    return "completed";
  }
  return "waiting";
}

export function visibleFlowStatuses(run) {
  const statuses = {};
  let previousComplete = true;
  for (const group of FLOW_STAGE_GROUPS) {
    const rawStatus = flowStageStatus(group, run);
    statuses[group.id] = previousComplete ? rawStatus : "waiting";
    previousComplete = ["completed", "completed_with_warnings"].includes(statuses[group.id]);
  }
  return statuses;
}

export function currentFlowStage(run, visibleStatuses = visibleFlowStatuses(run)) {
  const activeCurrent = FLOW_STAGE_GROUPS.find(group =>
    group.steps.includes(run.current)
  );
  if (activeCurrent && visibleStatuses[activeCurrent.id] !== "waiting") {
    return activeCurrent;
  }
  const warning = FLOW_STAGE_GROUPS.find(group =>
    visibleStatuses[group.id] === "completed_with_warnings"
  );
  if (warning) return warning;
  return FLOW_STAGE_GROUPS.find(group =>
    !["completed", "completed_with_warnings"].includes(visibleStatuses[group.id])
  ) || FLOW_STAGE_GROUPS[FLOW_STAGE_GROUPS.length - 1];
}

export function withOptimisticStage(data, stageId) {
  const current = data || { run: { status: "idle", results: {} }, steps: [] };
  return {
    ...current,
    run: {
      ...(current.run || {}),
      status: "running",
      current: stageId,
      results: {
        ...(current.run?.results || {}),
        [stageId]: {
          ...(current.run?.results?.[stageId] || {}),
          status: "running",
          note: "Solicitação enviada ao backend.",
          messages: ["Solicitação enviada ao backend."],
        },
      },
    },
  };
}
