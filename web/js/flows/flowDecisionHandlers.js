import {
  applyMangaUpdatesDecisions,
  validateMangaUpdatesDecisions,
} from "../api/mangaupdatesApi.js";

export async function applySelectedDecisions(selectedDecisions, callbacks, queueIds = []) {
  const selectedIds = new Set(queueIds);
  const decisions = Object.values(selectedDecisions).filter(decision =>
    selectedIds.has(decision.queueId || decision.Nome)
  );
  if (!selectedIds.size) {
    callbacks.setFeedback("Selecione ao menos uma decisão.", "error");
    return selectedDecisions;
  }
  const validation = await validateMangaUpdatesDecisions({ queueIds });
  if (!validation.response.ok || !validation.payload.valid) {
    callbacks.setFeedback(callbacks.errorMessage(validation.payload), "error");
    return selectedDecisions;
  }
  const { response, payload } = await applyMangaUpdatesDecisions({ queueIds, dryRun: false });
  callbacks.setFeedback(
    response.ok ? `${payload.accepted} decisão(ões) aplicada(s).` : callbacks.errorMessage(payload),
    response.ok ? "success" : "error",
  );
  if (response.ok) await callbacks.reload();
  return response.ok ? remainingDecisions(selectedDecisions, selectedIds) : selectedDecisions;
}

export function selectCandidate(selectedDecisions, button) {
  return {
    ...selectedDecisions,
    [button.dataset.flowWork]: {
      queueId: button.dataset.flowWork,
      Nome: button.dataset.flowLocalTitle || button.dataset.flowWork,
      ID: Number(button.dataset.flowSelectId),
      "Nome encontrado": button.dataset.flowTitle,
      Origem: "Candidato selecionado",
    },
  };
}

export function selectManualId(selectedDecisions, button, area) {
  const key = button.dataset.flowManualWork;
  const input = area.querySelector(`[data-flow-manual-id="${CSS.escape(key)}"]`);
  const value = Number(input?.value || 0);
  if (!value) return { selectedDecisions, error: "Informe um ID manual válido." };
  return {
    selectedDecisions: {
      ...selectedDecisions,
      [key]: {
        queueId: key,
        Nome: button.dataset.flowLocalTitle || key,
        ID: value,
        "Nome encontrado": `ID ${value}`,
        Origem: "ID informado manualmente",
      },
    },
  };
}

function remainingDecisions(selectedDecisions, appliedIds) {
  return Object.fromEntries(
    Object.entries(selectedDecisions).filter(([, decision]) =>
      !appliedIds.has(decision.queueId || decision.Nome)
    )
  );
}
