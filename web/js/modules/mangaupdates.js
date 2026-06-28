import { api } from '../core/api.js';
import { notifications } from '../ui/notifications.js';

let reviewItems = [];
const decisions = new Map(); // Guarda as escolhas do usuário temporariamente

/**
 * Helper para renderizar card de candidato
 */
function renderCandidate(workName, candidate) {
  const isSelected = decisions.get(workName)?.ID === candidate.id;
  return `
    <article class="candidate-card ${isSelected ? 'selected' : ''}">
      <div>
        <strong>${candidate.titulo}</strong>
        <span class="score">${Number(candidate.pontuacao).toFixed(2)}</span>
      </div>
      <small>ID ${candidate.id} · ${candidate.ano || '?'}</small>
      <p>${candidate.descricao || 'Sem descrição.'}</p>
      <div class="candidate-actions">
        <a href="${candidate.url}" target="_blank">Ver Ficha</a>
        <button type="button" class="compact" 
                data-select-work="${workName}" 
                data-id="${candidate.id}" 
                data-title="${candidate.titulo}">Selecionar</button>
      </div>
    </article>
  `;
}

/**
 * Renderiza a lista de obras que precisam de revisão
 */
function renderReviewList(items) {
  const list = document.getElementById("idReviewList");
  const query = document.getElementById("reviewSearch")?.value.toLowerCase() || "";
  
  const filtered = items.filter(item => item.nome.toLowerCase().includes(query));

  list.innerHTML = filtered.map(item => `
    <div class="review-work">
      <div class="review-work-header">
        <h3>${item.nome}</h3>
        <span>${item.candidates.length} candidatos encontrados</span>
      </div>
      <div class="candidate-grid">
        ${item.candidates.map(c => renderCandidate(item.nome, c)).join("")}
      </div>
      <div class="manual-decision">
        <label>ID Manual:</label>
        <input type="number" placeholder="Ex: 12345" id="manual-${item.nome_decisao}">
        <button type="button" data-manual-work="${item.nome}">Usar este ID</button>
      </div>
    </div>
  `).join("") || '<p class="empty">Nenhuma obra pendente de revisão.</p>';
}

/**
 * Carrega Status do Cache
 */
async function loadCacheStatus() {
  const data = await api.getStatus();
  const summary = document.getElementById("mangaCacheSummary");
  if (!summary) return;

  const s = data.mangaupdates || {};
  summary.innerHTML = `
    <article><strong>${s.confirmed_ids || 0}</strong><span>IDs Confirmados</span></article>
    <article><strong>${s.cached_ids || 0}</strong><span>Com Cache</span></article>
    <article><strong>${s.calls_needed || 0}</strong><span>Chamadas Pendentes</span></article>
  `;
}

/**
 * Inicialização do Módulo
 */
export async function init() {
  const list = document.getElementById("idReviewList");
  const applyBtn = document.getElementById("applyDecisions");

  // 1. Carrega dados iniciais
  loadCacheStatus();
  const reviewData = await fetch("/api/mangaupdates/review").then(res => res.json());
  reviewItems = reviewData.items || [];
  renderReviewList(reviewItems);
  
  if (reviewItems.length > 0) applyBtn.hidden = false;

  // 2. Listener para seleção de candidatos (Event Delegation)
  list?.addEventListener("click", (e) => {
    const btnSelect = e.target.closest("[data-select-work]");
    const btnManual = e.target.closest("[data-manual-work]");

    if (btnSelect) {
      const { selectWork, id, title } = btnSelect.dataset;
      decisions.set(selectWork, { Nome: selectWork, ID: Number(id), "Nome encontrado": title });
      renderReviewList(reviewItems);
    }

    if (btnManual) {
      const workName = btnManual.dataset.manualWork;
      const input = document.getElementById(`manual-${workName.replace(/\s+/g, '')}`);
      if (input?.value) {
        decisions.set(workName, { Nome: workName, ID: Number(input.value), "Nome encontrado": "Manual" });
        renderReviewList(reviewItems);
      }
    }
  });

  // 3. Aplicar decisões ao banco
  applyBtn?.addEventListener("click", async () => {
    if (decisions.size === 0) return alert("Selecione ao menos uma decisão.");
    
    const confirmed = await notifications.confirm("Confirmar IDs", `Você está prestes a vincular ${decisions.size} obras.`);
    if (!confirmed) return;

    const res = await fetch("/api/mangaupdates/decisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decisions: Array.from(decisions.values()) })
    });

    if (res.ok) {
      notifications.showTaskToast("MangaUpdates", "IDs vinculados com sucesso!");
      decisions.clear();
      init(); // Recarrega o módulo
    }
  });
}