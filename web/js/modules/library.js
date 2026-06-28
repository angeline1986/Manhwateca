import { api } from '../core/api.js';
import { state } from '../core/state.js';

// Elementos da UI
let catalogList, editorialList, catalogSearch, editorialSearch, editorialFilters;

/**
 * Renderiza o Catálogo Técnico (Tabela)
 */
function renderCatalogTable(items) {
  if (!catalogList) return;
  
  catalogList.innerHTML = items.length ? items.map((manga, index) => {
    const issues = [...(manga.count_issues || []), ...(manga.unparsed_files || [])];
    const detailsId = `catalog-issue-${index}`;
    
    return `
      <tr>
        <td>
          <strong>${manga.nome}</strong>
          ${manga.alias?.length ? `<small>${manga.alias.join(", ")}</small>` : ""}
        </td>
        <td>${manga.ultimo_lido || "-"}</td>
        <td>${manga.main_caps || "0"}</td>
        <td>${manga.tamanho || "-"}</td>
        <td>${manga.chapters_found || "0"}</td>
        <td>
          ${issues.length 
            ? `<button class="issue-button" data-target="${detailsId}">Ver ${issues.length} alerta(s)</button>`
            : '<span class="state ok">OK</span>'}
        </td>
      </tr>
    `;
  }).join("") : '<tr><td colspan="6" class="empty">Nenhuma obra encontrada.</td></tr>';
}

/**
 * Renderiza os Cards de Curadoria
 */
function renderEditorialList(filter = "all") {
  const query = editorialSearch.value.toLowerCase();
  
  const filtered = state.editorialWorks.filter(work => {
    const matchesSearch = work.Nome.toLowerCase().includes(query) || work.Alias?.toLowerCase().includes(query);
    if (!matchesSearch) return false;

    if (filter === "reading") return work.Status === "Lendo";
    if (filter === "without-id") return !work["ID da obra"];
    if (filter === "new-chapters") return Number(work["Último capítulo disponível"]) > Number(work["Último lido"]);
    return true;
  });

  editorialList.innerHTML = filtered.map(work => `
    <details class="editorial-work">
      <summary>
        <span><strong>${work.Nome}</strong> <small>${work.Alias || ""}</small></span>
        <span>${work.Status}</span>
      </summary>
      <form class="editorial-form" data-name="${work.Nome}">
        <label>Status<input name="Status" value="${work.Status}"></label>
        <label>Nota<input name="Nota" value="${work.Nota}"></label>
        <label class="wide">Alias<input name="Alias" value="${work.Alias || ""}"></label>
        <button type="submit" class="primary-action">Salvar Localmente</button>
      </form>
    </details>
  `).join("");
}

/**
 * Inicialização do Módulo
 */
export async function init() {
  catalogList = document.getElementById("catalogList");
  editorialList = document.getElementById("editorialList");
  catalogSearch = document.getElementById("catalogSearch");
  editorialSearch = document.getElementById("editorialSearch");
  editorialFilters = document.getElementById("editorialFilters");

  // Carrega Dados do Catálogo
  const catalogData = await api.getCatalog();
  state.catalog = catalogData.mangas;
  renderCatalogTable(state.catalog);

  // Carrega Dados Editoriais
  const editorialData = await api.getEditorial();
  state.editorialWorks = editorialData.works;
  renderEditorialList();

  // Listeners de Busca
  catalogSearch?.addEventListener("input", () => {
    const query = catalogSearch.value.toLowerCase();
    const filtered = state.catalog.filter(m => m.nome.toLowerCase().includes(query));
    renderCatalogTable(filtered);
  });

  editorialSearch?.addEventListener("input", () => renderEditorialList());

  // Listeners de Filtros
  editorialFilters?.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    editorialFilters.querySelectorAll("button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    renderEditorialList(btn.dataset.filter);
  });

  // Listener de Salvamento
  editorialList?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const name = form.dataset.name;
    const changes = Object.fromEntries(new FormData(form));
    
    const res = await api.updateEditorial(name, changes);
    if (res.ok) {
        document.getElementById("editorialFeedback").textContent = "Alterações salvas!";
    }
  });
}