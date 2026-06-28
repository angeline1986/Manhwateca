/* ==========================================================================
   CORE API - Central de Requisições
   ========================================================================== */

export const api = {
  // Busca status geral (Dashboard)
  async getStatus() {
    const res = await fetch("/api/status", { cache: "no-store" });
    return res.json();
  },

  // Busca pendências
  async getPending() {
    const res = await fetch("/api/pending", { cache: "no-store" });
    return res.json();
  },

  // Inicia uma tarefa (Task) técnica
  async startTask(action, confirmation = null, parameters = {}) {
    const res = await fetch(`/api/tasks/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmation, parameters })
    });
    return res.json();
  },

  // Busca lista de tarefas recentes (Histórico)
  async getTasks() {
    const res = await fetch("/api/tasks", { cache: "no-store" });
    return res.json();
  },

  // --- Módulo de Fluxos (Workflow) ---
  flows: {
    async getStatus() {
      const res = await fetch("/api/flows/status", { cache: "no-store" });
      return res.json();
    },
    async start(selected = [], resume = false) {
      const res = await fetch("/api/flows/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected, resume })
      });
      return res.json();
    },
    async cancel() {
      const res = await fetch("/api/flows/cancel", { 
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      return res.json();
    }
  },

  // --- Outras rotas conforme necessário ---
  async getCatalog() {
    const res = await fetch("/api/catalog", { cache: "no-store" });
    return res.json();
  },

  async getEditorial() {
    const res = await fetch("/api/editorial", { cache: "no-store" });
    return res.json();
  },

  async updateEditorial(name, changes) {
    const res = await fetch("/api/editorial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, changes })
    });
    return res.json();
  }
};