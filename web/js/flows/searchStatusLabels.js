export function statusLabel(status) {
  return {
    WITHOUT_ID: "Sem ID confirmado",
    READY_TO_SEARCH: "Não pesquisada",
    CANDIDATES_FOUND: "Revisão",
    PENDING_REVIEW: "Revisão",
    MANUAL_ID_REQUIRED: "Sem correspondência",
    ERROR: "Falha",
  }[status] || status || "Revisão";
}

export function statusTone(status) {
  if (status === "ERROR" || status === "MANUAL_ID_REQUIRED") return "bad";
  if (status === "CANDIDATES_FOUND" || status === "PENDING_REVIEW") return "amb";
  return "info";
}

export function resultLabel(item) {
  if (item?.decisionStatus === "READY_TO_SEARCH") return "—";
  if (item?.decisionStatus === "ERROR") return "Falha na consulta";
  const arrayCount = Array.isArray(item?.candidates) ? item.candidates.length : null;
  const explicitCount = Number.isFinite(Number(item?.candidateCount))
    ? Number(item.candidateCount)
    : Number.isFinite(Number(item?.candidatesCount))
      ? Number(item.candidatesCount)
      : arrayCount;
  if (explicitCount !== null && Number.isFinite(explicitCount)) {
    return `${explicitCount} encontrado${explicitCount === 1 ? "" : "s"}`;
  }
  return {
    WITHOUT_ID: "—",
    CANDIDATES_FOUND: "Disponíveis para revisão",
    PENDING_REVIEW: "Disponíveis para revisão",
    MANUAL_ID_REQUIRED: "0 encontrados",
  }[item?.decisionStatus] || "Aguardando";
}

export function actionLabel(action) {
  return {
    SEARCH_API: "Executar busca",
    NORMALIZE_TITLE: "Ajustar título",
    REVIEW_CANDIDATES: "Revisar candidatos",
    MANUAL_SEARCH: "Ajustar busca",
    RETRY_FAILED: "Repetir tentativa",
  }[action] || action || "Executar busca";
}
