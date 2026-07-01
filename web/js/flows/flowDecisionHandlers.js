import { applyMangaUpdatesDecisions } from "../api/mangaupdatesApi.js";

export async function applySelectedDecisions(selectedDecisions, callbacks) {
  const decisions = Object.values(selectedDecisions);
  if (!decisions.length) {
    callbacks.setFeedback("Selecione ao menos uma decisão.", "error");
    return selectedDecisions;
  }
  const { response, payload } = await applyMangaUpdatesDecisions({ decisions });
  callbacks.setFeedback(
    response.ok ? `${payload.applied.length} decisão(ões) aplicada(s).` : callbacks.errorMessage(payload),
    response.ok ? "success" : "error",
  );
  if (response.ok) await callbacks.reload();
  return response.ok ? {} : selectedDecisions;
}

export function selectCandidate(selectedDecisions, button) {
  return {
    ...selectedDecisions,
    [button.dataset.flowWork]: {
      Nome: button.dataset.flowWork,
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
        Nome: key,
        ID: value,
        "Nome encontrado": `ID ${value}`,
        Origem: "ID informado manualmente",
      },
    },
  };
}
