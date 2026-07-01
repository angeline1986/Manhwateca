import { getActions } from "../api/tasksApi.js";
import { escapeHtml } from "../utils/html.js";

export function initActionsPage({ elements, startTask }) {
  async function loadActions() {
    const actionHelp = {
      organization_preview: ["Analisa a organização alfabética das pastas.", "Gera um preview sem mover pastas."],
      rename_preview: ["Analisa nomes de capítulos, capas e títulos.", "Gera um preview sem renomear arquivos."],
      chapter_audit: ["Verifica capítulos e arquivos que precisam de conferência.", "Gera um relatório sem alterar a biblioteca."],
      catalog_scan: ["Lê novamente todas as pastas e capítulos.", "Atualiza o catálogo no PostgreSQL."],
      apply_organization: ["Move as obras para os grupos alfabéticos corretos.", "Altera as pastas após confirmação."],
      apply_renaming: ["Padroniza os nomes de capítulos, capas e títulos fora do padrão.", "Renomeia os arquivos após confirmação."],
      run_tests: ["Verifica automaticamente as regras principais do sistema.", "Mostra os resultados no histórico."],
      mangaupdates_search: ["Pesquisa obras ainda sem ID confirmado.", "Registra candidatos e decisões no PostgreSQL."],
      mangaupdates_refresh: ["Completa candidatos sem link ou descrição.", "Atualiza dados de revisão no PostgreSQL."],
      mangaupdates_details: ["Consulta detalhes dos IDs confirmados.", "Atualiza URL, capa e metadados no PostgreSQL."],
      mangaupdates_force_refresh: ["Reconsulta IDs confirmados mesmo com dados salvos.", "Use somente quando quiser atualizar dados antigos."],
      mangaupdates_csv: ["Usa os dados já salvos, sem consultar a API.", "Atualiza o CSV preservando campos manuais."],
      notion_simulate_batch: ["Compara o catálogo com as páginas do Notion.", "Mostra o próximo lote sem alterar o Notion."],
      notion_apply_batch: ["Cria as próximas páginas ausentes.", "Publica até 25 obras após confirmação."],
      notion_update_existing: ["Envia novas contagens para páginas existentes.", "Atualiza o Notion sem criar páginas."],
      notion_csv_preview: ["Compara a fonte enriquecida com as páginas existentes.", "Simula as alterações sem escrever no Notion."],
      notion_csv_apply: ["Envia metadados enriquecidos para páginas existentes.", "Atualiza páginas após confirmação."],
    };
    const { payload: actions } = await getActions();
    const renderActionButton = (id, action, options = {}) => {
      const fallback = actionHelp[id] || ["Ação disponível no sistema.", "O resultado aparecerá no histórico."];
      const label = options.label || action.label || id;
      const classes = [
        "action-button",
        action.requires_confirmation ? "destructive" : "",
        options.compact ? "compact" : "",
      ].filter(Boolean).join(" ");
      return `
        <button class="${classes}"
                type="button" data-action="${id}"
                data-confirmation="${action.requires_confirmation}">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(action.description || fallback[0])}</span>
          <small>${escapeHtml(action.result || fallback[1])}</small>
        </button>
      `;
    };
    const render = entries => entries.map(([id, action]) =>
      renderActionButton(id, action)
    ).join("");
    const renderGroupedAction = ({ title, description, previewId, applyId }) => {
      const preview = actions[previewId];
      const apply = actions[applyId];
      if (!preview || !apply) return "";
      return `
        <article class="action-card">
          <div>
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(description)}</p>
          </div>
          <div class="action-card-options" aria-label="Ações de ${escapeHtml(title)}">
            ${renderActionButton(previewId, preview, { label: "Preview", compact: true })}
            ${renderActionButton(applyId, apply, { label: "Aplicar", compact: true })}
          </div>
        </article>
      `;
    };
    const entries = Object.entries(actions);
    const organizationIds = new Set(["chapter_audit", "catalog_scan"]);
    const notionIds = new Set([
      "notion_simulate_batch", "notion_apply_batch", "notion_update_existing",
      "notion_csv_preview", "notion_csv_apply",
    ]);
    elements.actionGrid.innerHTML = [
      renderGroupedAction({
        title: "Organização de Pastas",
        description: "Analisa e move pastas para os grupos alfabéticos corretos.",
        previewId: "organization_preview",
        applyId: "apply_organization",
      }),
      renderGroupedAction({
        title: "Padronização",
        description: "Analisa e renomeia capítulos, capas e títulos fora do padrão.",
        previewId: "rename_preview",
        applyId: "apply_renaming",
      }),
      render(entries.filter(([id]) => organizationIds.has(id))),
    ].join("");
    elements.mangaActionGrid.innerHTML = render(entries.filter(([id, action]) =>
      action.group === "mangaupdates" && id !== "mangaupdates_csv"
    ));
    elements.notionActionGrid.innerHTML = render(entries.filter(([id]) => notionIds.has(id)));
    elements.supportActionGrid.innerHTML = render(entries.filter(([id]) => id === "run_tests"));
  }

  function handleActionClick(event) {
    const button = event.target.closest("[data-action]");
    if (button) {
      startTask(button.dataset.action, button.dataset.confirmation === "true");
    }
  }

  [elements.actionGrid, elements.mangaActionGrid, elements.notionActionGrid, elements.supportActionGrid]
    .forEach(container => container.addEventListener("click", handleActionClick));

  elements.quickGuide?.addEventListener("click", event => {
    const action = event.target.closest("[data-action]");
    if (action) handleActionClick(event);
  });

  return { handleActionClick, loadActions };
}
