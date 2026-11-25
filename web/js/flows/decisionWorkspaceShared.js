export const keyOf = item => item.queueId || item.nome_decisao || item.localTitle || item.nome || "obra";
export const titleOf = item => item.localTitle || item.nome || item.searchedTitle || "Obra sem título";
export const idOf = decision => decision?.Tipo === "sem_correspondencia" ? "" : String(decision?.ID || "");
export const normalize = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");

export function rankedCandidates(candidates) {
  const unique = new Map();
  for (const candidate of candidates) {
    const score = Number(candidate.confidence ?? candidate.pontuacao ?? 0);
    if (score <= 0.64) continue;
    const key = String(candidate.id || candidate.title || candidate.titulo || "");
    if (!key) continue;
    if (!unique.has(key) || score > Number(unique.get(key).confidence ?? unique.get(key).pontuacao ?? 0)) unique.set(key, candidate);
  }
  return [...unique.values()].sort((a, b) => Number(b.confidence ?? b.pontuacao ?? 0) - Number(a.confidence ?? a.pontuacao ?? 0)).slice(0, 5);
}

export function aliasesText(item) {
  const aliases = item.alternativeTitles || item.aliases || item.alias || [];
  if (Array.isArray(aliases) && aliases.length) return aliases.join(", ");
  return typeof aliases === "string" && aliases.trim() ? aliases : "Não informado";
}

export function originLabel(decision) {
  if (decision?.Tipo === "sem_correspondencia") return "Revisão manual";
  const origin = String(decision?.Origem || "").toLowerCase();
  if (origin.includes("manual")) return "ID manual";
  if (origin.includes("atual")) return "ID atual";
  return "Candidato selecionado";
}
