import {
  applyMangaUpdatesDecisions,
  getMangaUpdatesStatus,
  getReviewItems,
  searchMangaUpdates,
  translateText,
} from "../api/mangaupdatesApi.js";
import { summaryCard } from "../components/summaryCard.js";
import { escapeHtml } from "../utils/html.js";

export function initMangaUpdatesPage({ elements, onDecisionsApplied }) {
  let reviewItems = [];
  let apiSearchItems = [];
  const decisions = new Map();

  function candidateCard(item, candidate) {
    const selected = decisions.get(item.nome_decisao)?.ID === candidate.id;
    return `
      <article class="candidate-card ${selected ? "selected" : ""}">
        <div><strong>${escapeHtml(candidate.titulo || "")}</strong>
          <span class="score">${Number(candidate.pontuacao || 0).toFixed(2)}</span></div>
        <small>${escapeHtml(candidate.tipo || "Tipo não informado")} ·
          ${escapeHtml(candidate.ano || "Ano não informado")} · ID ${candidate.id}</small>
        <p>${escapeHtml(candidate.descricao || "Sem descrição.")}</p>
        <div class="candidate-actions">
          ${candidate.url ? `<a href="${escapeHtml(candidate.url)}" target="_blank">Abrir ficha</a>` : ""}
          <button type="button" data-select-id="${candidate.id}"
            data-work="${escapeHtml(item.nome_decisao)}"
            data-title="${escapeHtml(candidate.titulo || "")}">Selecionar</button>
        </div>
      </article>
    `;
  }

  function reviewMarkup(items) {
    return items.length ? items.map(item => `
      <details class="review-work">
        <summary><strong>${escapeHtml(item.nome)}</strong>
          <span>${item.candidates.length} candidato(s)</span></summary>
        <div class="candidate-grid">
          ${item.candidates.map(candidate => candidateCard(item, candidate)).join("")
            || '<p class="empty">Nenhum candidato acima de 0,70.</p>'}
        </div>
        <div class="manual-decision">
          <label>ID manual</label>
          <input type="number" min="1" data-manual-id="${escapeHtml(item.nome_decisao)}">
          <button type="button" data-manual-work="${escapeHtml(item.nome_decisao)}">
            Usar ID
          </button>
        </div>
      </details>
    `).join("") : '<p class="empty">Nenhuma obra aguardando revisão.</p>';
  }

  function renderReview(items) {
    const html = reviewMarkup(items);
    elements.idReviewList.innerHTML = html;
    if (elements.organizationIdReviewList) {
      elements.organizationIdReviewList.innerHTML = html;
    }
  }

  function renderReviewSummary(summary) {
    const html = [
      summaryCard("Registros", summary.total),
      summaryCard("A revisar", summary.review),
      summaryCard("IDs confirmados", summary.confirmed),
      summaryCard("Ainda não pesquisados", summary.pending),
    ].join("");
    elements.reviewSummary.innerHTML = html;
    if (elements.organizationReviewSummary) {
      elements.organizationReviewSummary.innerHTML = html;
    }
  }

  async function loadIdReview() {
    const { payload: data } = await getReviewItems();
    reviewItems = data.items;
    renderReviewSummary(data.summary);
    renderReview(reviewItems);
    const warning = data.warning || "";
    elements.decisionFeedback.textContent = warning;
    elements.applyDecisionsButton.hidden = !reviewItems.length;
    if (elements.organizationDecisionFeedback) {
      elements.organizationDecisionFeedback.textContent = warning;
    }
    if (elements.organizationApplyDecisionsButton) {
      elements.organizationApplyDecisionsButton.hidden = !reviewItems.length;
    }
  }

  function cacheList(title, items, emptyText) {
    const entries = (items || []).map(item =>
      `<li><strong>${escapeHtml(item.name || item.title || "")}</strong>
        <small>ID ${escapeHtml(item.id || "")}</small></li>`
    ).join("");
    return `<article class="notion-list">
      <strong>${escapeHtml(title)}</strong>
      ${entries ? `<ul>${entries}</ul>` : `<p>${escapeHtml(emptyText)}</p>`}
    </article>`;
  }

  async function loadMangaUpdatesStatus() {
    const { payload } = await getMangaUpdatesStatus();
    const summary = payload.summary || {};
    elements.mangaCacheSummary.innerHTML = [
      summaryCard("IDs confirmados", summary.confirmed_ids || 0),
      summaryCard("Com cache", summary.cached_ids || 0),
      summaryCard("Chamadas necessárias", summary.calls_needed || 0),
      summaryCard(`Próximo lote (${summary.batch_size || 10})`, summary.next_batch || 0),
      summaryCard("Forçar atualização", summary.force_refresh_calls || 0),
    ].join("");
    elements.mangaCacheLists.innerHTML = [
      cacheList("Próximas chamadas", payload.next_batch, "Nenhuma chamada necessária."),
      cacheList("Forçar atualização", payload.force_refresh_batch, "Nenhum ID confirmado."),
      `<article class="notion-list">
        <strong>Política do cache</strong>
        <p>Cache válido por ${escapeHtml(summary.ttl_days || 30)} dias.
        A opção normal consulta apenas ausentes ou expirados.</p>
      </article>`,
    ].join("");
  }

  function handleReviewDecisionClick(event, list, feedback) {
    const selected = event.target.closest("[data-select-id]");
    const manual = event.target.closest("[data-manual-work]");
    if (selected) {
      decisions.set(selected.dataset.work, {
        Nome: selected.dataset.work,
        ID: Number(selected.dataset.selectId),
        "Nome encontrado": selected.dataset.title,
        Origem: "Candidato selecionado",
      });
      renderReview(reviewItems);
    }
    if (manual) {
      const input = list.querySelector(
        `[data-manual-id="${CSS.escape(manual.dataset.manualWork)}"]`
      );
      if (!input.value) return;
      decisions.set(manual.dataset.manualWork, {
        Nome: manual.dataset.manualWork,
        ID: Number(input.value),
        "Nome encontrado": `ID ${input.value}`,
        Origem: "ID informado manualmente",
      });
      feedback.textContent = "ID manual incluído nas decisões.";
    }
  }

  function filterReviewFromInput(input) {
    const query = input.value.toLocaleLowerCase("pt-BR").trim();
    renderReview(reviewItems.filter(item =>
      item.nome.toLocaleLowerCase("pt-BR").includes(query)
    ));
  }

  async function submitReviewDecisions(feedback) {
    if (!decisions.size) {
      feedback.textContent = "Selecione ao menos uma decisão.";
      return;
    }
    const { response, payload } = await applyMangaUpdatesDecisions({
      decisions: [...decisions.values()],
    });
    feedback.textContent = response.ok
      ? `${payload.applied.length} decisão(ões) aplicada(s).`
      : (payload.rejected || [payload.error]).join(" ");
    if (response.ok) {
      decisions.clear();
      await loadIdReview();
      if (onDecisionsApplied) await onDecisionsApplied();
    }
  }

  elements.refreshMangaUpdatesStatus.addEventListener("click", loadMangaUpdatesStatus);

  elements.idReviewList.addEventListener("click", event =>
    handleReviewDecisionClick(event, elements.idReviewList, elements.decisionFeedback)
  );

  if (elements.organizationIdReviewList) {
    elements.organizationIdReviewList.addEventListener("click", event =>
      handleReviewDecisionClick(
        event,
        elements.organizationIdReviewList,
        elements.organizationDecisionFeedback
      )
    );
  }

  elements.reviewSearch.addEventListener("input", () =>
    filterReviewFromInput(elements.reviewSearch)
  );

  if (elements.organizationReviewSearch) {
    elements.organizationReviewSearch.addEventListener("input", () =>
      filterReviewFromInput(elements.organizationReviewSearch)
    );
  }

  elements.apiSearchForm.addEventListener("submit", async event => {
    event.preventDefault();
    const query = elements.apiSearchQuery.value.trim();
    if (query.length < 2) return;
    const submit = elements.apiSearchForm.querySelector("button");
    submit.disabled = true;
    elements.apiSearchFeedback.textContent = "Consultando o MangaUpdates...";
    elements.apiSearchResults.innerHTML = "";
    try {
      const { response, payload } = await searchMangaUpdates({ query });
      if (!response.ok) {
        elements.apiSearchFeedback.textContent = response.status === 404
          ? "O servidor local precisa ser reiniciado para habilitar esta pesquisa."
          : (payload.error || "Não foi possível pesquisar.");
        return;
      }
      elements.apiSearchFeedback.textContent = payload.results.length
        ? `${payload.results.length} resultado(s) encontrado(s).`
        : "Nenhuma obra encontrada.";
      apiSearchItems = payload.results;
      elements.apiSearchResults.innerHTML = payload.results.map((item, index) => `
        <details class="api-result" ${index === 0 ? "open" : ""}>
          <summary>
            <strong>${escapeHtml(item.title)}</strong>
            <strong class="api-result-id">ID ${escapeHtml(item.series_id)}</strong>
          </summary>
          <div class="api-result-content">
            <p data-api-description="${index}">${escapeHtml(item.description || "Descrição não disponível.")}</p>
            <div class="api-result-actions">
              ${item.url ? `<a class="result-action" href="${escapeHtml(item.url)}"
                target="_blank" rel="noopener noreferrer" title="Detalhes"
                aria-label="Abrir detalhes no MangaUpdates">
                <span class="result-action-icon details-icon" aria-hidden="true"></span>
              </a>` : ""}
              ${item.description ? `<button type="button"
                class="result-action text-button" data-translate-result="${index}"
                title="Traduzir descrição" aria-label="Traduzir descrição">
                <span class="result-action-icon translation-icon" aria-hidden="true"></span>
              </button>` : ""}
            </div>
          </div>
        </details>
      `).join("");
    } catch {
      elements.apiSearchFeedback.textContent = "Não foi possível conectar ao servidor local.";
    } finally {
      submit.disabled = false;
    }
  });

  elements.apiSearchResults.addEventListener("click", async event => {
    const button = event.target.closest("[data-translate-result]");
    if (!button) return;
    const index = Number(button.dataset.translateResult);
    const item = apiSearchItems[index];
    const paragraph = elements.apiSearchResults.querySelector(
      `[data-api-description="${index}"]`
    );
    if (!item || !paragraph) return;
    if (button.dataset.translated === "true") {
      paragraph.textContent = item.description;
      button.title = "Traduzir descrição";
      button.setAttribute("aria-label", "Traduzir descrição");
      button.dataset.translated = "false";
      button.classList.remove("translated");
      return;
    }
    button.disabled = true;
    button.title = "Traduzindo...";
    try {
      const { response, payload } = await translateText({ text: item.description });
      if (!response.ok) {
        button.title = "Tentar traduzir novamente";
        elements.apiSearchFeedback.textContent = payload.error || "Não foi possível traduzir.";
        return;
      }
      paragraph.textContent = payload.translation;
      button.title = "Ver texto original";
      button.setAttribute("aria-label", "Ver texto original");
      button.dataset.translated = "true";
      button.classList.add("translated");
      elements.apiSearchFeedback.textContent = "Descrição traduzida para português.";
    } catch {
      button.title = "Tentar traduzir novamente";
      elements.apiSearchFeedback.textContent = "Não foi possível conectar ao servidor local.";
    } finally {
      button.disabled = false;
    }
  });

  elements.applyDecisionsButton.addEventListener("click", () =>
    submitReviewDecisions(elements.decisionFeedback)
  );

  if (elements.organizationApplyDecisionsButton) {
    elements.organizationApplyDecisionsButton.addEventListener("click", () =>
      submitReviewDecisions(elements.organizationDecisionFeedback)
    );
  }

  return { loadIdReview, loadMangaUpdatesStatus };
}
