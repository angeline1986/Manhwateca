import { escapeHtml } from "../utils/html.js";
import { keyOf, titleOf, idOf, rankedCandidates, aliasesText, originLabel } from "./decisionWorkspaceShared.js";

export function reviewQueue(items, current, saved, decisions) {
  if (!items.length) return '<p class="decision-workspace-empty">Nenhuma obra encontrada.</p>';
  return items.map(item => {
    const key = keyOf(item);
    const prepared = saved.has(key);
    const conflict = item.reason === "EXTERNAL_ID_ALREADY_ASSIGNED";
    const status = prepared ? "Preparada" : conflict ? "Conflito" : item.candidates?.length ? "Revisar" : "Sem ID";
    const tone = prepared ? "ready" : conflict ? "warning" : "neutral";
    const description = prepared
      ? decisions[key]?.Tipo === "sem_correspondencia" ? "Sem correspondência" : `ID ${idOf(decisions[key])} · ${originLabel(decisions[key])}`
      : conflict ? "ID sugerido já pertence a outra obra" : item.candidates?.length ? `${item.candidates.length} candidatos encontrados` : "Nenhum candidato confiável";
    return `<button type="button" class="decision-workspace-control decision-workspace-item ${current && keyOf(current) === key ? "active" : ""}" data-flow-review-work="${escapeHtml(key)}" ${current && keyOf(current) === key ? 'aria-current="true"' : ""}>
      <span><strong>${escapeHtml(titleOf(item))}</strong><em class="${tone}">${status}</em></span><small>${escapeHtml(description)}</small>
    </button>`;
  }).join("");
}

export function reviewDetail(item, decisions, saved, options) {
  if (!item) return '<div class="decision-workspace-placeholder"><h3>Nenhuma pendência selecionada</h3><p>Use a busca ou confira o lote preparado.</p></div>';
  const key = keyOf(item);
  const title = titleOf(item);
  const decision = decisions[key];
  const prepared = saved.has(key);
  const tab = ["manual", "suggestions", "context"].includes(options.reviewDetailTab) ? options.reviewDetailTab : "manual";
  const candidates = rankedCandidates(item.candidates || []);
  const alias = aliasesText(item);
  const conflict = item.reason === "EXTERNAL_ID_ALREADY_ASSIGNED" ? item.conflict || {} : null;
  const feedback = options.reviewChoiceFeedback?.[key];
  const manualDraft = options.manualDrafts?.[key] ?? (decision?.Origem === "ID informado manualmente" ? String(decision.ID) : "");
  return `<header class="decision-workspace-detail-head"><div><span class="eyebrow">${prepared ? "Decisão preparada" : "Obra em análise"}</span><h3>${escapeHtml(title)}</h3><p>${prepared ? "Esta decisão está no lote e pode ser editada antes da gravação." : "Revise a obra e prepare uma decisão para o lote."}</p></div><button type="button" class="secondary-action" data-flow-copy-title="${escapeHtml(title)}">Copiar título</button></header>
    ${prepared ? preparedDetail(decision, key) : `
      <nav class="decision-workspace-tabs" aria-label="Detalhes da revisão">
        ${[["manual", "Inserir ID manual"], ["suggestions", `Sugestões (${candidates.length})`], ["context", "Contexto da busca"]].map(([value, label]) => `<button type="button" data-flow-review-tab="${value}" class="decision-workspace-control ${tab === value ? "active" : ""}" aria-current="${tab === value ? "page" : "false"}">${label}</button>`).join("")}
      </nav>
      <div class="decision-workspace-detail-body">
        <div class="decision-workspace-info"><article><span>Título normalizado</span><strong>${escapeHtml(item.normalizedTitle || item.searchedTitle || title)}</strong></article><article><span>Aliases locais</span><strong>${escapeHtml(alias)}</strong></article></div>
        ${conflict ? `<div class="decision-workspace-notice warning"><strong>ID sugerido já associado</strong><p>ID ${escapeHtml(String(conflict.candidateExternalId || "--"))} pertence a ${escapeHtml(conflict.existingTitle || "outra obra")}. Escolha outro ID ou marque sem correspondência.</p></div>` : ""}
        ${feedback && tab !== "manual" ? `<div class="decision-workspace-notice ${feedback.tone === "error" ? "error" : feedback.tone === "success" ? "success" : "info"}" role="status"><p>${escapeHtml(feedback.message)}</p></div>` : ""}
        ${tab === "manual" ? `<div class="decision-workspace-field"><label for="flowWorkspaceManualId">ID MangaUpdates da obra</label><div><input id="flowWorkspaceManualId" type="text" inputmode="numeric" placeholder="Ex.: 98765" data-flow-manual-id="${escapeHtml(key)}" value="${escapeHtml(manualDraft)}" ${options.reviewValidationPending ? "disabled" : ""}><button type="button" class="primary-action" data-flow-manual-work="${escapeHtml(key)}" data-flow-local-title="${escapeHtml(title)}" ${options.reviewValidationPending ? "disabled" : ""}>Selecionar ID</button></div><small>O ID será conferido contra vínculos do catálogo. A existência na API externa não é verificada aqui.</small><p class="flow-manual-feedback ${feedback?.tone || ""}" data-flow-manual-feedback role="status" aria-live="polite">${escapeHtml(feedback?.message || "")}</p></div>` : ""}
        ${tab === "suggestions" ? candidatesList(candidates, item, key, title, options.reviewValidationPending) : ""}
        ${tab === "context" ? reviewContext(item) : ""}
        ${decision ? `<div class="decision-workspace-selected"><strong>${decision.Tipo === "sem_correspondencia" ? "Sem correspondência selecionado" : `ID ${escapeHtml(idOf(decision))} selecionado`}</strong><p>Prepare a decisão para incluí-la no lote. Nenhum dado foi gravado ainda.</p></div>` : ""}
      </div>
      <footer class="decision-workspace-detail-foot"><button type="button" class="decision-workspace-control decision-workspace-link danger" data-flow-ignore-review data-flow-work="${escapeHtml(key)}">Ignorar por enquanto</button><div><button type="button" class="secondary-action" data-flow-no-match data-flow-work="${escapeHtml(key)}" data-flow-local-title="${escapeHtml(title)}">Sem correspondência</button><button type="button" class="secondary-action" data-flow-next-review>Próxima pendência</button><button type="button" class="primary-action" data-flow-save-review="${escapeHtml(key)}" ${decision ? "" : "disabled"}>Preparar decisão</button></div></footer>
    `}`;
}

function candidatesList(candidates, item, key, title, loading) {
  if (!candidates.length) return '<p class="decision-workspace-empty">Nenhuma sugestão confiável. Informe um ID manualmente.</p>';
  const blockedId = item.reason === "EXTERNAL_ID_ALREADY_ASSIGNED" ? String(item.conflict?.candidateExternalId || "") : "";
  return `<div class="decision-workspace-candidates">${candidates.map(candidate => {
    const blocked = blockedId && String(candidate.id) === blockedId;
    return `<article class="decision-workspace-candidate ${blocked ? "blocked" : ""}"><div><strong>${escapeHtml(candidate.title || candidate.titulo || "Sem título")}</strong><small>ID ${escapeHtml(String(candidate.id || "--"))} · ${Math.round(Number(candidate.confidence ?? candidate.pontuacao ?? 0) * 100)}% de correspondência${blocked ? " · Já vinculado" : ""}</small></div><button type="button" class="secondary-action" data-flow-select-id="${escapeHtml(String(candidate.id || ""))}" data-flow-work="${escapeHtml(key)}" data-flow-local-title="${escapeHtml(title)}" data-flow-title="${escapeHtml(candidate.title || candidate.titulo || "")}" ${blocked || loading ? "disabled" : ""}>${blocked ? "Indisponível" : "Selecionar"}</button></article>`;
  }).join("")}</div>`;
}

function reviewContext(item) {
  const reason = {
    EXTERNAL_ID_ALREADY_ASSIGNED: "O ID encontrado já está vinculado a outra obra.",
    NO_CANDIDATES: "A busca não encontrou candidatos seguros.",
    AMBIGUOUS: "A busca retornou candidatos ambíguos.",
  }[item.reason] || item.reasonLabel || "A busca requer uma decisão manual.";
  return `<div class="decision-workspace-context"><strong>Motivo da revisão</strong><p>${escapeHtml(reason)}</p>${item.searchedTitle ? `<small>Título usado na busca: ${escapeHtml(item.searchedTitle)}</small>` : ""}</div>`;
}

function preparedDetail(decision, key) {
  return `<div class="decision-workspace-detail-body"><div class="decision-workspace-selected"><strong>${decision?.Tipo === "sem_correspondencia" ? "Sem correspondência" : `ID ${escapeHtml(idOf(decision))}`}</strong><p>${escapeHtml(originLabel(decision))}. A gravação ainda não aconteceu.</p></div><div class="decision-workspace-notice info"><p>Você pode conferir e aplicar parte do lote sem concluir toda a fila.</p></div></div><footer class="decision-workspace-detail-foot"><button type="button" class="decision-workspace-control decision-workspace-link danger" data-flow-remove-review="${escapeHtml(key)}">Retirar do lote</button><div><button type="button" class="secondary-action" data-flow-edit-review="${escapeHtml(key)}">Editar decisão</button><button type="button" class="primary-action" data-flow-batch-open>Conferir lote</button></div></footer>`;
}
