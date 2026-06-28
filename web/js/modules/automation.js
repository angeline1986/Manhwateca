import { api } from '../core/api.js';

export async function init() {
  const taskList = document.getElementById("taskList");

  async function refreshTasks() {
    const data = await api.getTasks();
    if (!data.tasks?.length) return;

    taskList.innerHTML = data.tasks.map(task => `
      <article class="task-item">
        <div class="task-head">
          <strong>${task.label}</strong>
          <span class="state ${task.status === 'completed' ? 'ok' : 'warn'}">${task.status}</span>
        </div>
        <p>Início: ${task.started_at || '?'}</p>
        ${task.messages?.length ? `<pre>${task.messages.join("\n")}</pre>` : ""}
      </article>
    `).join("");
  }

  refreshTasks();
  // Polling para atualizar o histórico a cada 5 segundos nesta página
  const interval = setInterval(refreshTasks, 5000);
  
  // Limpa o interval quando o usuário sair da página
  window.addEventListener('hashchange', () => clearInterval(interval), { once: true });
}