/* ==========================================================================
   ROUTER - Manhwateca Rose Edition
   ========================================================================== */

import { ui } from './app.js';

// Metadados das páginas (extraído do seu código original)
const pageMeta = {
  flows: {
    eyebrow: "FLUXOS",
    title: "Execute o processo guiado",
    subtitle: "Fluxo operacional da Manhwateca.",
  },
  overview: {
    eyebrow: "DASHBOARD",
    title: "Visão geral",
    subtitle: "Acompanhe a biblioteca e as integrações.",
  },
  library: {
    eyebrow: "ACERVO E CURADORIA",
    title: "Biblioteca",
    subtitle: "Consulte capítulos, leitura e dados editoriais.",
  },
  organization: {
    eyebrow: "ARQUIVOS LOCAIS",
    title: "Organização",
    subtitle: "Revise e aplique padrões com segurança.",
  },
  mangaupdates: {
    eyebrow: "ENRIQUECIMENTO",
    title: "MangaUpdates",
    subtitle: "Localize IDs e valide correspondências.",
  },
  notion: {
    eyebrow: "INTEGRAÇÃO",
    title: "Notion",
    subtitle: "Simule lotes e atualize metadados.",
  },
  automation: {
    eyebrow: "PROCESSAMENTO",
    title: "Automação",
    subtitle: "Execute o fluxo completo e acompanhe tarefas.",
  },
  settings: {
    eyebrow: "AMBIENTE",
    title: "Configurações",
    subtitle: "Verifique requisitos e suporte técnico.",
  },
};

/**
 * Navega para uma página específica
 */
export async function navigateTo(pageName, updateHash = true) {
  const page = pageMeta[pageName] ? pageName : "overview";
  const container = document.getElementById("page-content");
  
  // 1. Feedback visual de carregamento
  container.style.opacity = "0.5";

  try {
    // 2. Busca o fragmento HTML
    const response = await fetch(`/views/${page}.html`);
    if (!response.ok) throw new Error(`Página ${page} não encontrada.`);
    const html = await response.text();

    // 3. Injeta o conteúdo
    container.innerHTML = html;

    // 4. Atualiza a Topbar via utilitário do app.js
    const meta = pageMeta[page];
    ui.updateTopbar(meta.eyebrow, meta.title, meta.subtitle);
    ui.toggleRefreshAction(page === "overview");

    // 5. Atualiza classes ativas no menu
    document.querySelectorAll("[data-page]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.page === page);
    });

    // 6. Gerencia o Histórico do Browser
    if (updateHash) {
      window.location.hash = page;
    }

    // 7. Inicializa o JS específico da página (se houver)
    // Procuramos por um arquivo em js/modules/[page].js que tenha uma função init()
    try {
      const module = await import(`./modules/${page}.js`);
      if (module.init) module.init();
    } catch (err) {
      console.warn(`⚠️ Nenhum módulo JS encontrado ou erro ao carregar para: ${page}`);
    }

  } catch (error) {
    console.error("Erro na navegação:", error);
    container.innerHTML = `<div class="empty">Erro ao carregar a página: ${error.message}</div>`;
  } finally {
    container.style.opacity = "1";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

/**
 * Configura o roteador inicial
 */
export function initRouter() {
  // Escuta mudanças na URL (botões voltar/avançar do browser)
  window.addEventListener("hashchange", () => {
    const page = window.location.hash.replace("#", "");
    navigateTo(page, false);
  });

  // Carrega a página inicial
  const initialPage = window.location.hash.replace("#", "") || "flows";
  navigateTo(initialPage);
}