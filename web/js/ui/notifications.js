/* ==========================================================================
   NOTIFICATIONS UI - Controla Toasts e Feedbacks de Tarefas
   ========================================================================== */

const toast = document.getElementById("taskToast");
const toastTitle = document.getElementById("taskToastTitle");
const toastText = document.getElementById("taskToastText");
const toastLink = document.getElementById("taskResultLink");
const viewProgressBtn = document.getElementById("viewTaskProgress");

export const notifications = {
  /**
   * Atualiza ou mostra o Toast de tarefa
   * @param {Object} task Objeto da tarefa vindo da API
   */
  updateTaskToast(task) {
    if (!task) return;

    toast.hidden = false;
    toast.dataset.taskId = task.id;
    toastTitle.textContent = task.label || "Processando...";
    
    const isRunning = ["queued", "running"].includes(task.status);
    toast.className = `task-toast ${task.status}`;

    if (isRunning) {
      toastText.textContent = task.status === "queued" 
        ? "Na fila de espera..." 
        : "Executando agora...";
      toastLink.hidden = true;
      viewProgressBtn.hidden = false;
    } else {
      const success = task.status === "completed";
      toastText.textContent = success ? "Tarefa concluída!" : "Falha na execução.";
      
      // Se tiver relatório, mostra o link
      if (task.reports && task.reports.length > 0) {
        toastLink.href = `/reports/${task.reports[0].replace(/^reports\//, "")}`;
        toastLink.hidden = false;
        viewProgressBtn.hidden = true;
      }
    }
  },

  hideToast() {
    toast.hidden = true;
  }
};