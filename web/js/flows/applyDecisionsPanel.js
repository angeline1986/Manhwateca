import { escapeHtml } from "../utils/html.js";

export function decisionsTab(_review, selectedDecisions = {}) {
  const decisions = Object.values(selectedDecisions);
  if (!decisions.length) return emptyState();
  const blocked = validationBlocks(decisions);
  const ready = decisions.length - blocked.length;
  const canApply = ready > 0 && !blocked.length;
  const selected = canApply ? ready : 0;
  return `
    <section class="flow-apply-panel ${canApply ? "ready" : "blocked"}">
      <div class="flow-apply-overview">
        <div class="flow-apply-summary" aria-label="Resumo da aplicação">
          <strong>${ready} ${plural(ready, "obra pronta", "obras prontas")}</strong>
          <span data-flow-apply-selected>${selected} ${plural(selected, "selecionada", "selecionadas")} para aplicar</span>
          <span>${statusIcon(canApply)} ${blocked.length ? `${blocked.length} ${plural(blocked.length, "conflito encontrado", "conflitos encontrados")}` : "Nenhum conflito"}</span>
          <span>${statusIcon(canApply)} ${canApply ? "IDs validados" : "Revise os bloqueios antes de gravar"}</span>
        </div>
        <div class="flow-apply-impact" aria-label="Impacto da aplicação">
          <h4>Impacto da aplicação</h4>
          <div class="flow-apply-impact-grid">
            <div><span>Destino</span><strong>PostgreSQL</strong></div>
            <div><span>Serão gravados</span><strong><b data-flow-impact-ids>${selected}</b> ID</strong></div>
            <div><span>Não aplicadas</span><strong data-flow-impact-skipped>${ready - selected}</strong></div>
            <div><span>Origem</span><strong>Revisão manual</strong></div>
          </div>
        </div>
      </div>
      <div class="flow-apply-list-head">
        <strong>Decisões prontas</strong>
        <span>
          <button type="button" data-flow-select-all-decisions>Selecionar todos</button>
          <b>·</b>
          <button type="button" data-flow-clear-decisions>Limpar seleção</button>
        </span>
      </div>
      <div class="flow-apply-checklist" aria-label="Decisões prontas">
        ${decisions.map(decisionItem).join("")}
      </div>
      <footer class="flow-apply-footer">
        <button class="secondary-action" type="button" data-flow-subtab="pendencias">Voltar para revisão</button>
        <button class="primary-action" type="button" data-flow-apply-decisions ${canApply ? "" : "disabled"}>
          ${canApply ? `Aplicar ${ready} ${plural(ready, "decisão", "decisões")}` : "Selecione decisões"}
        </button>
      </footer>
    </section>
  `;
}

function emptyState() {
  return `
    <section class="flow-apply-panel empty">
      <div class="flow-apply-summary">
        <strong>Nenhuma decisão pronta</strong>
        <span>Volte para a revisão antes de gravar.</span>
      </div>
      <footer class="flow-apply-footer">
        <button class="primary-action" type="button" data-flow-subtab="pendencias">Voltar para Revisar pendências</button>
      </footer>
    </section>
  `;
}

function decisionItem(decision) {
  const title = decision.Nome || "Obra sem título";
  const origin = decision.Origem || "Candidato selecionado";
  const id = decision.ID || "--";
  const ready = Boolean(Number(decision.ID));
  const queueId = decision.queueId || decision.Nome || title;
  return `
    <label class="flow-apply-item ${ready ? "ready" : "blocked"}">
      <input type="checkbox" data-flow-apply-choice="${escapeHtml(queueId)}" ${ready ? "checked" : "disabled"}>
      <span class="flow-apply-item-icon" aria-hidden="true">${ready ? "✓" : "!"}</span>
      <div class="flow-apply-item-copy">
        <strong>${escapeHtml(title)}</strong>
        <small>ID ${escapeHtml(String(id))} · ${escapeHtml(originLabel(origin))}</small>
      </div>
      <em>${ready ? "Pronto" : "Bloqueado"}</em>
    </label>
  `;
}

function validationBlocks(decisions) {
  return decisions.filter(decision => !Number(decision.ID));
}

function originLabel(origin) {
  return String(origin).toLowerCase().includes("manual")
    ? "manual"
    : "candidato";
}

function plural(count, singular, pluralText) {
  return count === 1 ? singular : pluralText;
}

function statusIcon(ok) {
  return ok ? "✓" : "!";
}
