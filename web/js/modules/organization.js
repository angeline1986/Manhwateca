import { api } from '../core/api.js';
import { notifications } from '../ui/notifications.js';

export async function init() {
  const catalogList = document.getElementById("catalogPendingList");
  
  // 1. Injeta botões de ação
  const actionGrid = document.getElementById("actionGrid");
  const actions = [
    { id: "organization_preview", label: "Preview Organização", confirm: false },
    { id: "apply_organization", label: "Aplicar Movimentação", confirm: true },
    { id: "rename_preview", label: "Preview Renomeação", confirm: false },
    { id: "apply_renaming", label: "Aplicar Nomes", confirm: true }
  ];

  actionGrid.innerHTML = actions.map(act => `
    <button class="action-button ${act.confirm ? 'destructive' : ''}" data-action="${act.id}" data-confirm="${act.confirm}">
      <strong>${act.label}</strong>
      <span>Executar tarefa técnica</span>
    </button>
  `).join("");

  // 2. Lógica de Catalogação Individual (Event Delegation)
  catalogList?.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-catalog-one]");
    if (!btn) return;
    
    const name = btn.dataset.catalogOne;
    btn.disabled = true;
    btn.textContent = "Processando...";

    try {
      const res = await fetch("/api/catalog/catalog-one", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
      });
      if (res.ok) {
        btn.textContent = "OK!";
        btn.closest(".catalog-pending-row").classList.add("catalog-pending-row-done");
      }
    } catch (err) {
      notifications.showTaskToast("Erro", "Falha ao catalogar obra.", "failed");
      btn.disabled = false;
    }
  });

  // 3. Listener para botões do grid
  actionGrid.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    if (btn.dataset.confirm === "true") {
      const ok = await notifications.confirm("Atenção", "Esta ação alterará arquivos físicos.");
      if (!ok) return;
    }
    api.startTask(btn.dataset.action, "APLICAR");
  });
}