import { validateMangaUpdatesDecisions } from "../api/mangaupdatesApi.js";
import { applySelectedDecisions } from "./flowDecisionHandlers.js";

export function createDecisionWorkspaceController(deps) {
  const state = {
    workspaceMode: "review",
    reviewDetailTab: "manual",
    manualDrafts: {},
    reviewChoiceFeedback: {},
    reviewValidationPending: false,
    batchOpen: false,
    batchSelectedKeys: new Set(),
    batchValidation: null,
    batchChecking: false,
    correctionOpen: false,
  };
  const render = () => deps.render();
  const ready = () => Object.fromEntries(Object.entries(deps.getDecisions())
    .filter(([key]) => deps.getSavedKeys().has(key)));
  const selectionKey = () => [...state.batchSelectedKeys].sort().join("|");
  const selectedDecisions = () => Object.entries(ready())
    .filter(([key]) => state.batchSelectedKeys.has(key)).map(([, decision]) => decision);

  function snapshot() {
    return { ...state, batchSelectedKeys: [...state.batchSelectedKeys] };
  }

  function setMode(value) {
    state.workspaceMode = value === "confirmed" ? "confirmed" : "review";
    state.reviewDetailTab = "manual";
    render();
  }

  function setTab(value) {
    state.reviewDetailTab = value;
    render();
  }

  function setManualDraft(key, value) {
    state.manualDrafts[key] = value;
    delete state.reviewChoiceFeedback[key];
  }

  async function selectDecision(nextDecisions, key) {
    const decision = nextDecisions[key];
    if (!decision || state.reviewValidationPending) return;
    state.reviewValidationPending = true;
    state.reviewChoiceFeedback[key] = { message: "Conferindo o ID no catálogo...", tone: "" };
    render();
    try {
      const { response, payload } = await validateMangaUpdatesDecisions({ decisions: [decision] });
      if (!response.ok || !payload.valid) {
        state.reviewChoiceFeedback[key] = {
          message: payload?.blocks?.[0]?.reason || deps.errorMessage(payload), tone: "error",
        };
      } else {
        deps.setDecisions(nextDecisions);
        if (decision.Origem !== "ID informado manualmente") delete state.manualDrafts[key];
        deps.getSavedKeys().delete(key);
        resetBatchValidation();
        state.reviewChoiceFeedback[key] = {
          message: "ID disponível no catálogo. Prepare a decisão para incluí-la no lote.", tone: "success",
        };
      }
    } catch (error) {
      state.reviewChoiceFeedback[key] = {
        message: `Falha ao conferir ID: ${error.message || "erro desconhecido"}.`, tone: "error",
      };
    } finally {
      state.reviewValidationPending = false;
      render();
    }
  }

  function openBatch() {
    const keys = Object.keys(ready());
    if (!keys.length) return;
    state.batchSelectedKeys = new Set(keys);
    resetBatchValidation();
    state.batchOpen = true;
    render();
  }

  function closeBatch() {
    state.batchOpen = false;
    render();
  }

  function setBatchChoice(key, checked) {
    if (checked) state.batchSelectedKeys.add(key);
    else state.batchSelectedKeys.delete(key);
    resetBatchValidation();
    render();
  }

  async function checkBatch() {
    const decisions = selectedDecisions();
    if (!decisions.length || state.batchChecking) return;
    state.batchChecking = true;
    resetBatchValidation();
    render();
    try {
      const { response, payload } = await validateMangaUpdatesDecisions({ decisions });
      state.batchValidation = {
        valid: response.ok && payload.valid === true,
        message: response.ok && payload.valid
          ? `${decisions.length} ${decisions.length === 1 ? "decisão conferida" : "decisões conferidas"} no catálogo local. A existência dos IDs no MangaUpdates não foi verificada.`
          : payload?.blocks?.map(block => `${block.name}: ${block.reason}`).join(" ") || deps.errorMessage(payload),
        selectionKey: selectionKey(),
      };
    } catch (error) {
      state.batchValidation = {
        valid: false, message: `Falha ao conferir lote: ${error.message || "erro desconhecido"}.`,
        selectionKey: selectionKey(),
      };
    } finally {
      state.batchChecking = false;
      render();
    }
  }

  async function applyBatch() {
    if (!state.batchValidation?.valid || state.batchValidation.selectionKey !== selectionKey() || state.batchChecking) return;
    state.batchChecking = true;
    render();
    let applyError = "";
    try {
      const prepared = ready();
      const remainingPrepared = await applySelectedDecisions(prepared, {
        errorMessage: deps.errorMessage,
        reload: deps.reload,
        setFeedback: (message, tone) => {
          deps.setFeedback(message, tone);
          if (tone === "error" || tone === "warning") applyError = message;
        },
      }, [...state.batchSelectedKeys]);
      if (remainingPrepared !== prepared) {
        const remaining = { ...deps.getDecisions() };
        Object.keys(prepared).filter(key => !(key in remainingPrepared))
          .forEach(key => { delete remaining[key]; });
        state.batchOpen = false;
        deps.afterApply(remaining);
      } else if (!applyError) applyError = "Nenhuma decisão foi aplicada. Confira o lote novamente.";
    } catch (error) {
      applyError = `Falha ao aplicar lote: ${error.message || "erro desconhecido"}.`;
      deps.setFeedback(applyError, "error");
    } finally {
      state.batchChecking = false;
      if (applyError) state.batchValidation = { valid: false, message: applyError, selectionKey: selectionKey() };
      render();
    }
  }

  function openCorrection() {
    if (!deps.getConfirmedCorrection().preview?.can_apply) return;
    state.correctionOpen = true;
    render();
  }

  function closeCorrection() {
    state.correctionOpen = false;
    render();
  }

  function resetBatchValidation() { state.batchValidation = null; }

  function pruneApplied(remaining) {
    state.batchSelectedKeys = new Set([...state.batchSelectedKeys].filter(key => key in remaining));
    resetBatchValidation();
  }

  return {
    state, snapshot, setMode, setTab, setManualDraft, selectDecision,
    openBatch, closeBatch, setBatchChoice, checkBatch, applyBatch,
    openCorrection, closeCorrection, resetBatchValidation, pruneApplied,
  };
}
