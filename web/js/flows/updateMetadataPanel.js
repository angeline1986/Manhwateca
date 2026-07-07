import { escapeHtml } from "../utils/html.js";

const FIELDS = [
  "Títulos alternativos",
  "Autores",
  "Gêneros",
  "Status",
  "País",
  "Sinopse",
  "Tags",
  "Capa",
];

export function renderUpdateMetadataPanel(metadata = {}) {
  const works = readyWorks(metadata);
  const selected = works.length;
  const fields = works.reduce((total, work) => total + changedFields(work).length, 0);
  return `
    <section class="metadata-card">
      <header class="metadata-header">
        <span class="eyebrow">Confirmação</span>
        <h2>Atualizar metadados</h2>
        <p>Confirme quais obras terão dados oficiais atualizados. Esta etapa não altera decisões nem troca IDs.</p>
      </header>

      <section class="metadata-confirm-row">
        <div class="metadata-hero">
          <strong>${selectedLabel(works.length, "obra pronta", "obras prontas")}</strong>
          <p>
            <span data-metadata-selected>${selectedLabel(selected, "selecionada para sincronizar", "selecionadas para sincronizar")}</span><br>
            ✓ IDs confirmados<br>
            ✓ Nenhum conflito
          </p>
        </div>
        <div class="metadata-impact">
          <h3>Impacto da sincronização</h3>
          <div class="metadata-impact-grid">
            ${impactMetric("Fonte", "MangaUpdates")}
            ${impactMetric("Campos previstos", String(fields), "metadata-fields-count")}
            ${impactMetric("Não selecionadas", "0", "metadata-not-selected")}
            ${impactMetric("Tempo estimado", estimateTime(selected))}
          </div>
        </div>
      </section>

      <section class="metadata-fields">
        <div class="metadata-fields-head">
          <h3>Campos avaliados na sincronização</h3>
          <small>Ao expandir uma obra, aparecem apenas campos com alteração real.</small>
        </div>
        <div class="metadata-fields-grid">
          ${FIELDS.map(field => `<span class="metadata-field-chip">${escapeHtml(field)}</span>`).join("")}
        </div>
      </section>

      <section class="metadata-selection">
        <div class="metadata-selection-head">
          <label class="metadata-select-all">
            <input type="checkbox" data-metadata-select-all ${works.length ? "checked" : ""}>
            Selecionar todas
          </label>
          <span>${selectedLabel(works.length, "obra pronta", "obras prontas")}</span>
        </div>

        <div class="metadata-list" data-metadata-list>
          ${works.length ? works.map((work, index) => metadataItem(work, index)).join("") : emptyState()}
        </div>
      </section>

      <div class="metadata-notice">
        A sincronização consulta dados oficiais e registra log. Nenhuma obra sem ID confirmado será alterada.
      </div>

      <footer class="metadata-actions">
        <button class="metadata-button-secondary" type="button" data-flow-subtab="decisoes">← Aplicar decisões</button>
        <button class="metadata-button-primary" type="button" data-flow-run-stage data-metadata-run ${works.length ? "" : "disabled"}>
          ${works.length ? `Sincronizar ${selectedLabel(selected, "obra", "obras")}` : "Selecione obras"}
        </button>
      </footer>
    </section>
  `;
}

function readyWorks(metadata) {
  return (metadata.items || [])
    .filter(item => item.mangaupdatesId && changedFields(item).length > 0)
    .slice(0, 25);
}

function metadataItem(work, index) {
  const title = work.localTitle || "Obra sem título";
  const id = work.mangaupdatesId || "sem ID";
  const changes = changedFields(work);
  const count = changes.length;
  const itemId = `metadata-item-${index}`;
  return `
    <article class="metadata-item" data-metadata-expandable aria-expanded="false">
      <div class="metadata-item-header" role="button" tabindex="0" aria-controls="${itemId}">
        <input class="metadata-item-checkbox" type="checkbox" checked data-metadata-choice data-metadata-fields="${count}" aria-label="Selecionar ${escapeHtml(title)} para sincronização">
        <div class="metadata-item-content">
          <strong class="metadata-item-title">${escapeHtml(title)}</strong>
          <span class="metadata-item-meta">ID ${escapeHtml(String(id))} · ${selectedLabel(count, "campo alterado", "campos alterados")}</span>
        </div>
        <span class="metadata-badge">Pronta</span>
        <span class="metadata-item-arrow" aria-hidden="true">▸</span>
      </div>
      <div class="metadata-item-details" id="${itemId}">
        ${changes.map(changeBlock).join("")}
      </div>
    </article>
  `;
}

function changedFields(work) {
  const rawChanges = (
    work.metadataChanges
    || work.changes
    || work.previewChanges
    || work.diff
    || []
  );
  if (Array.isArray(rawChanges) && rawChanges.length) {
    return rawChanges
      .map(normalizeChange)
      .filter(change => change.field && hasVisibleChange(change));
  }
  const changed = work.changedFields || work.fieldsChanged || [];
  if (Array.isArray(changed) && changed.length) {
    return changed
      .map(field => ({ field, current: "", next: "" }))
      .filter(change => change.field);
  }
  return [];
}

function normalizeChange(change) {
  if (typeof change === "string") {
    return { field: change, current: "", next: "" };
  }
  return {
    field: change.field || change.name || change.label || "",
    current: change.current ?? change.before ?? change.from ?? "",
    next: change.next ?? change.after ?? change.to ?? "",
  };
}

function hasVisibleChange(change) {
  return stringifyValue(change.current) !== stringifyValue(change.next);
}

function changeBlock(change) {
  const current = stringifyValue(change.current);
  const next = stringifyValue(change.next);
  return `
    <section class="metadata-change">
      <strong>${escapeHtml(change.field)}</strong>
      ${current ? `<p class="metadata-change-value">${escapeHtml(current)}</p><span class="metadata-change-arrow">↓</span>` : ""}
      ${next ? `<p class="metadata-change-value metadata-change-next">${escapeHtml(next)}</p>` : '<p class="metadata-change-value metadata-change-next">Será atualizado com o valor oficial.</p>'}
    </section>
  `;
}

function stringifyValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join("\n");
  if (value === null || value === undefined) return "";
  return String(value);
}

function impactMetric(label, value, attr) {
  const data = attr ? ` data-${attr}` : "";
  return `<div><span>${escapeHtml(label)}</span><b${data}>${escapeHtml(value)}</b></div>`;
}

function emptyState() {
  return `
    <div class="metadata-empty">
      <strong>Nenhuma alteração de metadados encontrada.</strong>
      <span>Execute a comparação/sincronização prévia antes de atualizar.</span>
    </div>
  `;
}

function selectedLabel(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function estimateTime(count) {
  if (!count) return "~0s";
  return `~${Math.max(10, count * 18)}s`;
}
