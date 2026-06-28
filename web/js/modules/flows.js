import { api } from '../core/api.js';
import { state } from '../core/state.js';

let updateTimer;
const FLOW_STATUS_LABELS = {
  waiting: "Aguardando",
  running: "Processando",
  completed: "Concluída",
  failed: "Falhou",
  manual: "Requer Ação",
};

/**
 * Renderiza a lista de etapas (Stages)
 */
function renderStageList(execution) {
  const list = document.getElementById("flowsStageList");
  if (!list || !execution) return;

  const stages = execution.stages || [];
  list.innerHTML = stages.map((stage, index) => {
    const isCurrent = execution.currentStage === stage.id;
    const status = stage.status || 'waiting';
    
    return `
      <article class="flow-stage ${status} ${isCurrent ? 'current' : ''}">
        <span class="flow-stage-marker">${status === 'completed' ? '✓' : index + 1}</span>
        <div>
          <h3>${stage.name}</h3>
          <p>${stage.description || 'Etapa do processo.'}</p>
        </div>
        <span class="flow-stage-status">${FLOW_STATUS_LABELS[status] || status}</span>
      </article>
    `;
  }).join("");
}

/**
 * Atualiza o progresso e o cabeçalho
 */
function updateProgress(execution) {
  const summary = document.getElementById("flowsSummary");
  const progress = document.getElementById("flowsProgress");
  if (!execution || !summary) return;

  const total = execution.stages?.length || 0;
  const completed = execution.stages?.filter(s => s.status === 'completed').length || 0;
  const percent = Math.round((completed / total) * 100);

  summary.innerHTML = `<span class="flow-chip">${completed} de ${total} etapas concluídas</span>`;
  progress.innerHTML = `
    <span><b>${percent}%</b> concluído</span>
    <div class="flow-progress-bar"><span style="width:${percent}%"></span></div>
  `;
}

/**
 * Consulta o servidor e atualiza a tela
 */
async function refreshWorkflowStatus() {
  try {
    const data = await api.flows.getStatus();
    const execution = data?.data?.execution;
    
    if (execution) {
      state.workflowState = execution;
      renderStageList(execution);
      updateProgress(execution);
      
      document.getElementById("flowsCurrentTitle").textContent = 
        execution.currentStage ? `Etapa: ${execution.currentStage}` : "Pronto para iniciar";
    }

    // Se estiver rodando, agenda próxima atualização em 2 segundos
    if (execution?.status === 'running') {
      updateTimer = setTimeout(refreshWorkflowStatus, 2000);
    }
  } catch (err) {
    console.error("Erro ao atualizar fluxos:", err);
  }
}

/**
 * Inicialização do Módulo
 */
export async function init() {
  const startBtn = document.getElementById("flowsStartWorkflow");

  // Limpa timers anteriores para evitar duplicidade
  if (updateTimer) clearTimeout(updateTimer);

  // Carregamento inicial
  refreshWorkflowStatus();

  // Listener para iniciar Workflow
  startBtn?.addEventListener("click", async () => {
    startBtn.disabled = true;
    try {
      const res = await api.flows.start();
      if (res.ok) {
        document.getElementById("flowsFeedback").textContent = "Workflow iniciado!";
        refreshWorkflowStatus();
      }
    } catch (err) {
      document.getElementById("flowsFeedback").textContent = "Erro ao iniciar.";
    } finally {
      startBtn.disabled = false;
    }
  });
}