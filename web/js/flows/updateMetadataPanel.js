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
  
  // Calcula o total de campos pendentes somando o tamanho do array pendingMetadata de cada obra
  const totalPendingFields = works.reduce((total, work) => {
    return total + (work.pendingMetadata ? work.pendingMetadata.length : 0);
  }, 0);

  return `
    <section class="metadata-card">
      <header class="metadata-header">
        <span class="eyebrow">Confirmação</span>
        <h2>Atualizar metadados</h2>
        <p>Confirme quais obras terão dados oficiais atualizados. Esta etapa utiliza o ID confirmado para buscar informações completas.</p>
      </header>

      <section class="metadata-confirm-row">
        <div class="metadata-hero">
          <strong>${selectedLabel(works.length, "obra pronta", "obras prontas")}</strong>
          <p>
            <span data-metadata-selected>${selectedLabel(selected, "selecionada para sincronizar", "selecionadas para sincronizar")}</span><br>
            ✓ IDs confirmados<br>
            ✓ Metadados pendentes identificados
          </p>
        </div>
        <div class="metadata-impact">
          <h3>Impacto da sincronização</h3>
          <div class="metadata-impact-grid">
            ${impactMetric("Fonte", "MangaUpdates")}
            ${impactMetric("Campos pendentes", String(totalPendingFields), "metadata-fields-count")}
            ${impactMetric("Não selecionadas", "0", "metadata-not-selected")}
            ${impactMetric("Tempo estimado", estimateTime(selected))}
          </div>
        </div>
      </section>

      <section class="metadata-fields">
        <div class="metadata-fields-head">
          <h3>Campos avaliados na sincronização</h3>
          <small>Ao expandir uma obra, aparecem os campos que serão preenchidos ou atualizados.</small>
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
        A sincronização consulta os dados oficiais via API e atualiza os registros locais.
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
  // A regra agora é: tem que ter ID do MangaUpdates e ter pelo menos um metadado pendente
  return (metadata.items || [])
    .filter(item => item.mangaupdatesId && item.pendingMetadata && item.pendingMetadata.length > 0)
    .slice(0, 25);
}

function metadataItem(work, index) {
  const title = work.localTitle || "Obra sem título";
  const id = work.mangaupdatesId || "sem ID";
  const pending = work.pendingMetadata || [];
  const count = pending.length;
  const itemId = `metadata-item-${index}`;

  return `
    <article class="metadata-item" data-metadata-expandable aria-expanded="false">
      <div class="metadata-item-header" role="button" tabindex="0" aria-controls="${itemId}">
        <input class="metadata-item-checkbox" type="checkbox" checked data-metadata-choice data-metadata-work-id="${escapeHtml(String(work.mangaId || work.id || ""))}" data-metadata-fields="${count}" aria-label="Selecionar ${escapeHtml(title)}">
        <div class="metadata-item-content">
          <strong class="metadata-item-title">${escapeHtml(title)}</strong>
          <span class="metadata-item-meta">ID ${escapeHtml(String(id))} · ${selectedLabel(count, "campo pendente", "campos pendentes")}</span>
        </div>
        <span class="metadata-badge">Pronta</span>
        <span class="metadata-item-arrow" aria-hidden="true">▸</span>
      </div>
      <div class="metadata-item-details" id="${itemId}">
        ${pending.map(field => pendingBlock(field)).join("")}
      </div>
    </article>
  `;
}

/**
 * Renderiza o bloco de informação de um campo pendente.
 */
function pendingBlock(fieldKey) {
  const mapping = {
    'cover': { label: 'Capa', detail: 'A imagem será buscada no MangaUpdates e salva localmente.' },
    'mangaupdatesUrl': { label: 'URL MangaUpdates', detail: 'O link oficial será gerado com base no ID confirmado.' }
  };

  const info = mapping[fieldKey] || { label: fieldKey, detail: 'Este campo será atualizado com os dados oficiais.' };

  return `
    <section class="metadata-change">
      <strong>${escapeHtml(info.label)}</strong>
      <p class="metadata-change-value metadata-change-next">${escapeHtml(info.detail)}</p>
    </section>
  `;
}

function impactMetric(label, value, attr) {
  const data = attr ? ` data-${attr}` : "";
  return `<div><span>${escapeHtml(label)}</span><b${data}>${escapeHtml(value)}</b></div>`;
}

function emptyState() {
  return `
    <div class="metadata-empty">
      <strong>Nenhuma obra com metadados pendentes encontrada.</strong>
      <span>Obras sem ID confirmado ou que já possuem capa e URL não aparecem aqui.</span>
    </div>
  `;
}

function selectedLabel(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function estimateTime(count) {
  if (!count) return "~0s";
  // Estimativa baseada em 1.5s por obra para buscar metadados
  return `~${Math.max(5, count * 2)}s`;
}
