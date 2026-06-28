import { api } from '../core/api.js';
import { notifications } from '../ui/notifications.js';

let actionGrid;

/**
 * Renderiza o status visual da sincronização com o Notion
 */
function updateSyncIndicator(data) {
  const indicator = document.getElementById("notionSyncStatus");
  const title = document.getElementById("notionStatusTitle");
  const detail = document.getElementById("notionStatusDetail");
  
  if (!data || !indicator) return;

  indicator.className = "notion-sync-status " + (data.available ? "ok" : "warning");
  
  if (data.pending?.length > 0) {
    title.textContent = `${data.pending.length} obras pendentes para importação`;
    detail.textContent = "Clique para revisar o lote antes de enviar ao Notion.";
  } else {
    title.textContent = "Sincronização em dia";
    detail.textContent = "Todas as obras catalogadas já possuem página no Notion.";
  }
}

/**
 * Carrega os dados de status do Notion
 */
async function loadNotionStatus() {
  try {
    const data = await api.getStatus(); // Usando a rota de status global que contém info do Notion
    const notion = data.notion;
    
    // Atualiza Listas de conferência
    const listPending = document.querySelector("#listPending ul");
    if (listPending) {
      listPending.innerHTML = notion.pending_items?.map(item => `<li>${item}</li>`).join("") || "<li>Nenhuma</li>";
    }

    updateSyncIndicator(notion);
  } catch (err) {
    console.error("Erro ao carregar status do Notion:", err);
  }
}

/**
 * Executa uma tarefa do Notion com confirmação
 */
async function handleNotionAction(actionId, requiresConfirmation) {
  if (requiresConfirmation) {
    const confirmed = await notifications.confirm(
      "Confirmar Sincronização",
      "Esta ação enviará dados diretamente para a sua database no Notion. Deseja continuar?"
    );
    if (!confirmed) return;
  }

  try {
    notifications.showTaskToast("Notion", "Iniciando comunicação...", "running");
    const res = await api.startTask(actionId, "APLICAR");
    
    if (res.id) {
      notifications.showTaskToast("Sucesso", "Tarefa enviada para a fila de processamento.");
    }
  } catch (err) {
    notifications.showTaskToast("Erro", "Falha ao iniciar sincronização.", "failed");
  }
}

/**
 * Inicialização do Módulo
 */
export async function init() {
  actionGrid = document.getElementById("notionActionGrid");

  // Define os botões de ação manualmente ou via API
  const actions = [
    { id: "notion_simulate_batch", label: "Simular Lote", desc: "Verifica o que precisa ser criado.", confirm: false },
    { id: "notion_apply_batch", label: "Importar Lote", desc: "Cria até 25 páginas novas.", confirm: true },
    { id: "notion_csv_preview", label: "Simular Metadados", desc: "Compara campos do banco com o Notion.", confirm: false },
    { id: "notion_csv_apply", label: "Aplicar Metadados", desc: "Atualiza notas, status e IDs.", confirm: true }
  ];

  if (actionGrid) {
    actionGrid.innerHTML = actions.map(act => `
      <button class="action-button ${act.confirm ? 'destructive' : ''}" data-action="${act.id}" data-confirm="${act.confirm}">
        <strong>${act.label}</strong>
        <span>${act.desc}</span>
      </button>
    `).join("");

    actionGrid.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      handleNotionAction(btn.dataset.action, btn.dataset.confirm === "true");
    });
  }

  loadNotionStatus();
}