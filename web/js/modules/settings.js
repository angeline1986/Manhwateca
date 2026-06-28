export async function init() {
  const diagGrid = document.getElementById("diagnosticGrid");
  const refreshBtn = document.getElementById("refreshDiagnostics");

  async function runDiagnostics() {
    diagGrid.innerHTML = "Carregando...";
    const res = await fetch("/api/diagnostics");
    const data = await res.json();

    diagGrid.innerHTML = data.checks.map(check => `
      <article class="diagnostic-item ${check.ok ? 'ok' : 'warn'}">
        <strong>${check.name}</strong>
        <span>${check.detail}</span>
      </article>
    `).join("");
  }

  refreshBtn?.addEventListener("click", runDiagnostics);
  runDiagnostics();
}