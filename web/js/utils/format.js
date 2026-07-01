export function formatDateTime(value, fallback = "Sem data") {
  if (!value) return fallback;
  return new Date(value).toLocaleString("pt-BR");
}

export function formatNumber(value) {
  return Number(value || 0).toLocaleString("pt-BR");
}

