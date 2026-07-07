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
  const fields = FIELDS.length;
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
            ${impactMetric("Campos previstos", String(selected * fields), "metadata-fields-count")}
            ${impactMetric("Não selecionadas", "0", "metadata-not-selected")}
            ${impactMetric("Tempo estimado", estimateTime(selected))}
          </div>
        </div>
      </section>

      <section class="metadata-fields">
        <div class="metadata-fields-head">
          <h3>Campos que serão atualizados</h3>
          <small>Somente metadados. IDs e decisões permanecem intactos.</small>
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

        <div class="metadata-list">
          ${works.length ? works.map(work => metadataItem(work, fields)).join("") : emptyState()}
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
    .filter(item => item.mangaupdatesId)
    .slice(0, 25);
}

function metadataItem(work, fields) {
  const title = work.localTitle || "Obra sem título";
  const id = work.mangaupdatesId || "sem ID";
  return `
    <label class="metadata-item">
      <input class="metadata-item-checkbox" type="checkbox" checked data-metadata-choice data-metadata-fields="${fields}">
      <div class="metadata-item-content">
        <strong class="metadata-item-title">${escapeHtml(title)}</strong>
        <span class="metadata-item-meta">ID ${escapeHtml(String(id))} · atualizar ${fields} campos</span>
      </div>
      <span class="metadata-badge">Pronta</span>
    </label>
  `;
}

function impactMetric(label, value, attr) {
  const data = attr ? ` data-${attr}` : "";
  return `<div><span>${escapeHtml(label)}</span><b${data}>${escapeHtml(value)}</b></div>`;
}

function emptyState() {
  return `
    <div class="metadata-empty">
      Nenhuma obra com ID confirmado disponível para sincronização.
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
