import { escapeHtml } from "../utils/html.js";

export function confirmedQueue(items, state) {
  if (state.candidatesLoading) return '<p class="decision-workspace-empty">Buscando obras...</p>';
  if (state.candidatesError) return `<p class="decision-workspace-empty error">${escapeHtml(state.candidatesError)}</p>`;
  if (!items.length) return `<p class="decision-workspace-empty">${state.search ? "Nenhuma obra encontrada." : "Busque uma obra já vinculada pelo título ou ID."}</p>`;
  return items.map(item => `<button type="button" class="decision-workspace-control decision-workspace-item ${Number(state.selectedWork?.id) === Number(item.id) ? "active" : ""}" data-confirmed-id-select-work="${escapeHtml(String(item.id))}" ${Number(state.selectedWork?.id) === Number(item.id) ? 'aria-current="true"' : ""}>
    <span><strong>${escapeHtml(item.title || "Obra sem título")}</strong><em class="neutral">Vinculada</em></span><small>ID ${escapeHtml(String(item.current_work_code || "--"))}</small>
  </button>`).join("");
}

export function confirmedDetail(state) {
  const work = state.selectedWork;
  const preview = state.preview;
  return `<header class="decision-workspace-detail-head"><div><span class="eyebrow">Vínculo confirmado</span><h3>${escapeHtml(work?.title || "Nenhuma obra selecionada")}</h3><p>${work ? "Confira o vínculo atual antes de propor outro ID." : "Busque e selecione uma obra na lista."}</p></div>${work ? `<button type="button" class="secondary-action" data-flow-copy-title="${escapeHtml(work.title)}">Copiar título</button>` : ""}</header>
    <nav class="decision-workspace-tabs"><span class="active">Corrigir vínculo</span></nav>
    <div class="decision-workspace-detail-body">
      <div class="decision-workspace-info"><article><span>Obra local</span><strong>${escapeHtml(work?.title || "Não selecionada")}</strong></article><article><span>ID MangaUpdates atual</span><strong>${escapeHtml(String(work?.current_work_code || "Não informado"))}</strong></article></div>
      <div class="decision-workspace-notice warning"><strong>Atenção ao alterar o ID</strong><p>A correção troca apenas o vínculo e invalida metadados derivados do ID antigo. Atualize os metadados depois.</p></div>
      <div class="decision-workspace-field"><label for="flowWorkspaceCorrectionId">Novo ID MangaUpdates</label><div><input id="flowWorkspaceCorrectionId" type="text" inputmode="numeric" placeholder="Informe o novo ID" data-confirmed-id-new value="${escapeHtml(state.newWorkCode || "")}" ${work ? "" : "disabled"}><button type="button" class="primary-action" data-confirmed-id-preview ${work && !state.loading ? "" : "disabled"}>${state.loading ? "Validando..." : "Verificar ID"}</button></div><small>Esta verificação consulta o vínculo local e o MangaUpdates.</small></div>
      ${state.error ? `<div class="decision-workspace-notice error"><p>${escapeHtml(state.error)}</p></div>` : ""}
      ${preview ? correctionPreview(preview) : ""}
    </div>
    <footer class="decision-workspace-detail-foot"><span>Correções de vínculo são aplicadas separadamente do lote de pendências.</span><div><button type="button" class="primary-action" data-flow-correction-open ${preview?.can_apply ? "" : "disabled"}>Confirmar correção</button></div></footer>`;
}

function correctionPreview(preview) {
  return `<div class="decision-workspace-preview ${preview.can_apply ? "ready" : "blocked"}"><strong>${preview.can_apply ? "Novo vínculo validado" : "Correção bloqueada"}</strong><div class="decision-workspace-info"><article><span>Vínculo atual</span><strong>${escapeHtml(preview.current?.title || preview.current?.work_code || "Não disponível")}</strong></article><article><span>Novo vínculo</span><strong>${escapeHtml(preview.proposed?.title || preview.proposed?.work_code || "Não disponível")}</strong></article></div>${(preview.blockers || []).map(blocker => `<p>${escapeHtml(blocker.message || "Correção bloqueada.")}${blocker.existing_title ? ` Vinculado a ${escapeHtml(blocker.existing_title)}.` : ""}</p>`).join("")}</div>`;
}

export function correctionDialog(state) {
  const work = state.selectedWork;
  const preview = state.preview;
  return `<dialog class="decision-workspace-dialog" data-flow-correction-dialog aria-labelledby="decisionCorrectionTitle"><header><div><span class="eyebrow">Corrigir ID confirmado</span><h2 id="decisionCorrectionTitle">Confirmar correção</h2><p>Confira o ID atual e o novo vínculo antes de gravar.</p></div><button type="button" class="decision-workspace-control decision-workspace-close" data-flow-correction-close aria-label="Fechar">×</button></header><div class="decision-workspace-dialog-body"><div class="decision-workspace-info"><article><span>Obra</span><strong>${escapeHtml(work?.title || "--")}</strong></article><article><span>ID atual → novo ID</span><strong>${escapeHtml(String(work?.current_work_code || "--"))} → ${escapeHtml(String(preview?.proposed?.work_code || "--"))}</strong></article></div><div class="decision-workspace-notice warning"><p>Os metadados derivados do ID anterior serão invalidados e deverão ser reconstruídos em Atualizar metadados.</p></div></div><footer><button type="button" class="secondary-action" data-flow-correction-close>Cancelar</button><button type="button" class="primary-action" data-confirmed-id-apply ${preview?.can_apply ? "" : "disabled"}>Aplicar correção</button></footer></dialog>`;
}
