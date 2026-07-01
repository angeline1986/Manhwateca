export function initTaskToast({ elements, taskNextStep, taskCompletionSummary }) {
  function updateTaskToast(tasks) {
    if (elements.taskToast.hidden || !elements.taskToast.dataset.taskId) return;
    const task = tasks.find(item => item.id === elements.taskToast.dataset.taskId);
    if (!task) return;
    const text = document.getElementById("taskToastText");
    if (["queued", "running"].includes(task.status)) {
      elements.taskToast.className = "task-toast running";
      text.textContent = task.status === "queued"
        ? "Aguardando o início da tarefa..."
        : "Executando. O resultado aparecerá assim que estiver pronto.";
      return;
    }
    const completed = task.status === "completed";
    elements.taskToast.className = `task-toast ${completed ? "completed" : "failed"}`;
    elements.taskProgress.setAttribute(
      "aria-label",
      completed ? "Tarefa concluída" : "Tarefa encerrada com erro"
    );
    text.textContent = completed
      ? taskCompletionSummary(task)
      : "A tarefa não foi concluída. Consulte o resultado para entender o motivo.";
    const next = completed ? taskNextStep(task) : null;
    const report = (task.reports || [])[0];
    if (next) {
      elements.taskResultLink.hidden = true;
      elements.viewTaskProgress.hidden = false;
      elements.viewTaskProgress.textContent = next.label;
      elements.viewTaskProgress.dataset.nextPage = next.page;
      elements.viewTaskProgress.dataset.nextPanel = next.panel || "";
    } else if (completed && report) {
      elements.taskResultLink.href = `/reports/${report.replace(/^reports\//, "")}`;
      elements.taskResultLink.hidden = false;
      elements.viewTaskProgress.hidden = true;
      delete elements.viewTaskProgress.dataset.nextPage;
      delete elements.viewTaskProgress.dataset.nextPanel;
    } else {
      elements.taskResultLink.hidden = true;
      elements.viewTaskProgress.hidden = false;
      elements.viewTaskProgress.textContent = "Ver resultado";
      delete elements.viewTaskProgress.dataset.nextPage;
      delete elements.viewTaskProgress.dataset.nextPanel;
    }
  }

  return { updateTaskToast };
}
