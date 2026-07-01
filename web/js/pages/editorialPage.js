import { getEditorial, saveEditorial, saveReviewNote } from "../api/editorialApi.js";
import { summaryCard } from "../components/summaryCard.js";
import { escapeHtml } from "../utils/html.js";

export function initEditorialPage({ elements, onSaved }) {
  let editorialWorks = [];
  let editorialOptions = {};
  let editorialFilter = "all";

  function optionTags(values, selected) {
    return values.map(value =>
      `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>
        ${escapeHtml(value || "Não informado")}</option>`
    ).join("");
  }

  function editorialCard(work) {
    return `
      <details class="editorial-work">
        <summary>
          <span><strong>${escapeHtml(work.Nome)}</strong>
            <small>${escapeHtml(work.Alias || "Sem alias")}</small></span>
          <span>${escapeHtml(work.Status)} · ${escapeHtml(work.Tamanho)}</span>
        </summary>
        <form class="editorial-form" data-work="${escapeHtml(work.Nome)}">
          <label>Status<select name="Status">
            ${optionTags(editorialOptions.Status, work.Status)}</select></label>
          <label>Nota<select name="Nota">
            ${optionTags(editorialOptions.Nota, work.Nota)}</select></label>
          <label>Interesse<input name="Interesse" value="${escapeHtml(work.Interesse)}"></label>
          <label>Picância<select name="Picância">
            ${optionTags(editorialOptions.Picância, work.Picância)}</select></label>
          <label>Último lido<input name="Último lido" type="number" min="0"
            value="${escapeHtml(work["Último lido"])}"></label>
          <label>Alias<input name="Alias" value="${escapeHtml(work.Alias)}"></label>
          <label class="wide">Temática<input name="Temática"
            value="${escapeHtml(work.Temática)}" placeholder="Drama | Romance"></label>
          <label class="wide">Universo<input name="Universo"
            value="${escapeHtml(work.Universo)}" placeholder="Omegaverse | Fantasia"></label>
          <div class="editorial-context">
            Disponível: ${escapeHtml(work["Último capítulo disponível"])}
            · Encontrados: ${escapeHtml(work["Capítulos encontrados"])}
            · ID: ${escapeHtml(work["ID da obra"] || "pendente")}
          </div>
          <button type="submit">Salvar dados locais</button>
        </form>
      </details>
    `;
  }

  function matchesEditorialFilter(work) {
    const last = Number(work["Último lido"] || 0);
    const available = Number(work["Último capítulo disponível"] || 0);
    const rules = {
      all: true,
      reading: work.Status === "Lendo",
      "without-id": !work["ID da obra"],
      incomplete: !work.Interesse || !work.Picância,
      "new-chapters": available > last,
      audit: work["Status da contagem"] !== "OK",
    };
    return rules[editorialFilter];
  }

  function renderEditorial() {
    const query = elements.editorialSearch.value.toLocaleLowerCase("pt-BR").trim();
    const filtered = editorialWorks.filter(work =>
      matchesEditorialFilter(work)
      && [work.Nome, work.Alias].some(value =>
        String(value).toLocaleLowerCase("pt-BR").includes(query))
    );
    elements.editorialList.innerHTML = filtered.length
      ? filtered.map(editorialCard).join("")
      : '<p class="empty">Nenhuma obra corresponde ao filtro.</p>';
  }

  async function loadEditorial() {
    const { payload: data } = await getEditorial();
    editorialWorks = data.works;
    editorialOptions = data.options;
    elements.editorialSummary.innerHTML = [
      summaryCard("Obras", data.summary.total),
      summaryCard("Em leitura", data.summary.reading),
      summaryCard("Sem ID", data.summary.without_id),
      summaryCard("Metadados incompletos", data.summary.incomplete),
      summaryCard("Com capítulos disponíveis", data.summary.new_chapters),
      summaryCard("Em auditoria", data.summary.audit),
    ].join("");
    renderEditorial();
  }

  elements.editorialFilters.addEventListener("click", event => {
    const button = event.target.closest("[data-editorial-filter]");
    if (!button) return;
    editorialFilter = button.dataset.editorialFilter;
    elements.editorialFilters.querySelectorAll("button").forEach(item =>
      item.classList.toggle("active", item === button)
    );
    renderEditorial();
  });

  elements.editorialSearch.addEventListener("input", renderEditorial);

  elements.editorialList.addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.target;
    const changes = Object.fromEntries(new FormData(form).entries());
    const { response, payload } = await saveEditorial({
      name: form.dataset.work,
      changes,
    });
    elements.editorialFeedback.textContent = response.ok
      ? `${form.dataset.work}: dados salvos localmente.`
      : (payload.error || "Não foi possível salvar.");
    if (response.ok) {
      await loadEditorial();
      if (onSaved) await onSaved();
    }
  });

  elements.reviewForm.addEventListener("submit", async event => {
    event.preventDefault();
    const note = elements.reviewNote.value.trim();
    if (!note) return;
    const { response, payload } = await saveReviewNote({ note });
    elements.reviewFeedback.textContent = response.ok
      ? "Observação registrada."
      : (payload.error || "Não foi possível salvar.");
    if (response.ok) elements.reviewNote.value = "";
  });

  return { loadEditorial };
}
