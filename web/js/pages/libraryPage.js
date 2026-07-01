import { getCatalog } from "../api/libraryApi.js";
import { summaryCard } from "../components/summaryCard.js";
import { escapeHtml } from "../utils/html.js";

export function initLibraryPage({ elements, onAction }) {
  let catalog = [];

  function renderCatalog(items) {
    elements.catalogList.innerHTML = items.length ? items.map((manga, index) => {
      const issues = [...(manga.count_issues || []), ...(manga.unparsed_files || [])];
      const aliases = (manga.alias || []).join(", ");
      const detailsId = `catalog-issue-${index}`;
      return `
        <tr>
          <td><strong>${escapeHtml(manga.nome || "")}</strong>
            ${aliases ? `<small>${escapeHtml(aliases)}</small>` : ""}</td>
          <td>${manga.ultimo_lido}</td>
          <td>${manga.main_caps}</td>
          <td>${escapeHtml(manga.tamanho)}</td>
          <td>${manga.chapters_found}</td>
          <td>${issues.length
            ? `<button class="issue-button" type="button"
                 data-issue-target="${detailsId}" aria-expanded="false">
                 Ver ${issues.length} alerta(s)
               </button>`
            : '<span class="state ok">OK</span>'}</td>
        </tr>
        ${issues.length ? `
          <tr class="issue-details" id="${detailsId}" hidden>
            <td colspan="6">
              <div>
                <strong>Como decidir o que fazer em ${escapeHtml(manga.nome)}:</strong>
                <div class="issue-guidance">
                  ${issues.map(issue => explainIssue(issue)).join("")}
                </div>
                <button type="button" data-action="chapter_audit">
                  Identificar arquivos envolvidos
                </button>
                <a href="/reports/audits/chapter_audit.html" target="_blank">
                  Consultar última auditoria
                </a>
              </div>
            </td>
          </tr>` : ""}
      `;
    }).join("") : '<tr><td colspan="6" class="empty">Nenhuma obra encontrada.</td></tr>';
  }

  function explainIssue(issue) {
    const guidance = {
      "lacunas": [
        "Intervalos entre capítulos",
        "Se você apagou capítulos já lidos, nenhuma correção é necessária. Caso contrário, confira se há arquivos ausentes."
      ],
      "sobreposições": [
        "Capítulos repetidos em mais de um arquivo",
        "Compare os intervalos indicados na auditoria. Mantenha ambos se forem versões diferentes; caso contrário, remova o duplicado."
      ],
      "MangaUpdates divergente": [
        "Contagem local diferente do MangaUpdates",
        "Confira se a obra está atualizada na fonte. Se o Drive estiver correto, mantenha o catálogo local; não é necessário renomear arquivos."
      ],
      "somente side stories": [
        "A pasta contém apenas histórias extras",
        "Mantenha assim se a obra principal já foi lida ou removida. Revise apenas se capítulos principais deveriam estar presentes."
      ],
    };
    if (guidance[issue]) {
      return `<article><strong>${guidance[issue][0]}</strong><p>${guidance[issue][1]}</p></article>`;
    }
    if (String(issue).toLowerCase().endsWith(".pdf")) {
      return `<article><strong>Nome de arquivo não reconhecido</strong>
        <p>Revise <code>${escapeHtml(issue)}</code>. Padronize o nome somente se o capítulo ou intervalo não estiver claro.</p>
      </article>`;
    }
    return `<article><strong>${escapeHtml(issue)}</strong>
      <p>Abra a auditoria para identificar os arquivos envolvidos antes de alterar a biblioteca.</p>
    </article>`;
  }

  function renderChanges(changes) {
    const total = changes.new.length + changes.updated.length + changes.removed.length;
    if (!total) {
      elements.catalogChanges.innerHTML = "<p>Nenhuma mudança registrada na última catalogação.</p>";
      return;
    }
    elements.catalogChanges.innerHTML = `
      <strong>Última catalogação:</strong>
      <span>${changes.new.length} nova(s)</span>
      <span>${changes.updated.length} alterada(s)</span>
      <span>${changes.removed.length} removida(s)</span>
    `;
  }

  async function loadCatalog() {
    const { payload: data } = await getCatalog();
    catalog = data.mangas;
    if (elements.catalogSource) {
      elements.catalogSource.textContent = data.source?.label
        ? `Fonte: ${data.source.label}`
        : "";
      elements.catalogSource.title = data.source?.detail || "";
    }
    elements.catalogSummary.innerHTML = [
      summaryCard("Obras", data.summary.total),
      summaryCard("Último cap. disponível", data.summary.main_caps),
      summaryCard("Side stories", data.summary.side_stories),
      summaryCard("Conferências necessárias", data.summary.review),
      summaryCard("Arquivos não lidos", data.summary.unparsed),
    ].join("");
    renderChanges(data.changes);
    renderCatalog(catalog);
  }

  elements.catalogSearch.addEventListener("input", () => {
    const query = elements.catalogSearch.value.toLocaleLowerCase("pt-BR").trim();
    renderCatalog(catalog.filter(manga =>
      [manga.nome, ...(manga.alias || [])]
        .some(value => String(value).toLocaleLowerCase("pt-BR").includes(query))
    ));
  });

  elements.catalogList.addEventListener("click", event => {
    const issueButton = event.target.closest("[data-issue-target]");
    if (issueButton) {
      const details = document.getElementById(issueButton.dataset.issueTarget);
      details.hidden = !details.hidden;
      issueButton.setAttribute("aria-expanded", String(!details.hidden));
      issueButton.textContent = details.hidden
        ? issueButton.textContent.replace("Ocultar", "Ver")
        : issueButton.textContent.replace("Ver", "Ocultar");
      return;
    }
    const action = event.target.closest("[data-action]");
    if (action && onAction) onAction(event);
  });

  return { loadCatalog };
}
