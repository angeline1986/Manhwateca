import { escapeHtml } from "../utils/html.js";

export function decisionsTab(_review, selectedDecisions = {}) {
  const decisions = Object.values(selectedDecisions);
  if (!decisions.length) return emptyState();
  const blocked = validationBlocks(decisions);
  const ready = decisions.length - blocked.length;
  const canApply = ready > 0 && !blocked.length;
  const selected = canApply ? ready : 0;
  const description = "Escolha quais decisões prontas serão gravadas no PostgreSQL.";
  return `
    <article class="flow-apply-panel ${canApply ? "ready" : "blocked"}">
      <details class="flow-section-details" open>
        ${applySummary(description)}
        <div class="flow-section-body flow-apply-body">
          <section class="flow-apply-summary-row">
            <div class="flow-apply-hero" aria-label="Resumo da aplicação">
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
          </section>
          <div class="flow-apply-list-head">
            <strong>Decisões prontas</strong>
            <span>
              <a href="#" data-flow-select-all-decisions>Selecionar todos</a>
              <b>·</b>
              <a href="#" data-flow-clear-decisions>Limpar seleção</a>
            </span>
          </div>
          <section class="flow-apply-checklist" aria-label="Decisões prontas">
            ${decisions.map(decisionItem).join("")}
          </section>
          <p class="flow-apply-helper" data-flow-apply-helper>Você pode desmarcar obras que não deseja aplicar neste lote.</p>
          <footer class="flow-apply-actions">
            <button class="secondary-action btn" type="button" data-flow-subtab="pendencias">
              Voltar para revisão
            </button>
            <button class="primary-action btn" type="button" data-flow-apply-decisions ${canApply ? "" : "disabled"}>
              ${canApply ? `Aplicar ${ready} ${plural(ready, "decisão", "decisões")}` : "Selecione decisões"}
            </button>
          </footer>
        </div>
      </details>
    </article>
  `;
}

function emptyState() {
  const description = "Escolha quais decisões prontas serão gravadas no PostgreSQL.";
  return `
    <article class="flow-apply-panel empty">
      <details class="flow-section-details" open>
        ${applySummary(description)}
        <div class="flow-section-body flow-apply-body">
          <div class="flow-apply-hero">
            <strong>Nenhuma decisão pronta</strong>
            <span>Volte para a revisão antes de gravar.</span>
          </div>
          <footer class="flow-apply-actions">
            <button class="primary-action btn" type="button" data-flow-subtab="pendencias">
              Voltar para revisão
            </button>
          </footer>
        </div>
      </details>
    </article>
  `;
}

function applySummary(description) {
  return `
    <summary class="flow-section-summary">
      <span class="eyebrow">Confirmação</span>
      <h2>${headingTooltip("Aplicar decisões", description)}</h2>
    </summary>
  `;
}

function headingTooltip(label, text) {
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(text)}">${escapeHtml(label)}</span>`;
}

function decisionItem(decision) {
  const title = decision.Nome || "Obra sem título";
  const origin = decision.Origem || "Candidato selecionado";
  const id = decision.ID || "--";
  const ready = isReadyDecision(decision);
  const queueId = decision.queueId || decision.Nome || title;
  return `
    <label class="flow-apply-item ${ready ? "ready" : "blocked"}">
      <input type="checkbox" data-flow-apply-choice="${escapeHtml(queueId)}" ${ready ? "checked" : "disabled"}>
      <span class="flow-apply-item-icon" aria-hidden="true">${ready ? "✓" : "!"}</span>
      <div class="flow-apply-item-copy">
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(decisionDescription(decision, id, origin))}</small>
      </div>
      <em>${ready ? "Pronto" : "Bloqueado"}</em>
    </label>
  `;
}

function validationBlocks(decisions) {
  return decisions.filter(decision => !isReadyDecision(decision));
}

function isReadyDecision(decision) {
  return decision?.Tipo === "sem_correspondencia" || Boolean(Number(decision.ID));
}

function decisionDescription(decision, id, origin) {
  if (decision?.Tipo === "sem_correspondencia") return "Sem correspondência · revisão manual";
  return `ID ${String(id)} · ${originLabel(origin)}`;
}

function originLabel(origin) {
  const normalized = String(origin).toLowerCase();
  if (normalized.includes("manual")) return "manual";
  if (normalized.includes("atual")) return "ID atual";
  return "candidato";
}

function plural(count, singular, pluralText) {
  return count === 1 ? singular : pluralText;
}

function statusIcon(ok) {
  return ok ? "✓" : "!";
}

function backIcon() {
  return `
    <svg class="btn-icon btn-icon-filled" viewBox="0 0 640 640" aria-hidden="true">
      <path d="M320 128C263.2 128 212.1 152.7 176.9 192L224 192C241.7 192 256 206.3 256 224C256 241.7 241.7 256 224 256L96 256C78.3 256 64 241.7 64 224L64 96C64 78.3 78.3 64 96 64C113.7 64 128 78.3 128 96L128 150.7C174.9 97.6 243.5 64 320 64C461.4 64 576 178.6 576 320C576 461.4 461.4 576 320 576C233 576 156.1 532.6 109.9 466.3C99.8 451.8 103.3 431.9 117.8 421.7C132.3 411.5 152.2 415.1 162.4 429.6C197.2 479.4 254.8 511.9 320 511.9C426 511.9 512 425.9 512 319.9C512 213.9 426 128 320 128z"/>
    </svg>
  `;
}
