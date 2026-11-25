import { escapeHtml } from "../utils/html.js";
import { keyOf, titleOf, normalize } from "./decisionWorkspaceShared.js";
import { reviewQueue, reviewDetail } from "./decisionWorkspaceReview.js";
import { confirmedQueue, confirmedDetail, correctionDialog } from "./decisionWorkspaceCorrection.js";
import { batchDialog } from "./decisionWorkspaceBatch.js";


export function decisionWorkspaceTab(review, decisions = {}, activeKey = "", options = {}) {
  const items = [...(review?.items || [])].sort((a, b) => titleOf(a).localeCompare(titleOf(b), "pt-BR", { sensitivity: "base" }));
  const saved = new Set(options.savedKeys || []);
  const ignored = new Set(options.ignoredReviewKeys || []);
  const mode = options.workspaceMode === "confirmed" ? "confirmed" : "review";
  const pending = items.filter(item => !saved.has(keyOf(item)) && !ignored.has(keyOf(item)));
  const prepared = items.filter(item => saved.has(keyOf(item)));
  const queue = [...pending, ...prepared];
  const search = mode === "review" ? options.searchQuery || "" : options.idCorrection?.search || "";
  const visible = mode === "review"
    ? queue.filter(item => normalize(titleOf(item)).includes(normalize(search)))
    : options.idCorrection?.candidates || [];
  const current = mode === "review" ? visible.find(item => keyOf(item) === activeKey) || visible[0] : null;
  const confirmed = options.idCorrection || {};
  const readyDecisions = Object.fromEntries(Object.entries(decisions).filter(([key]) => saved.has(key)));
  const preparedCount = Object.keys(readyDecisions).length;
  return `
    <section class="decision-workspace" aria-label="Central de decisões">
      <div class="decision-workspace-grid">
        <aside class="decision-workspace-rail" aria-label="Fila de obras">
          <div class="decision-workspace-rail-head">
            <h3>${mode === "review" ? "Fila de revisão" : "Obras confirmadas"}</h3>
            <p>${mode === "review" ? `${pending.length} pendentes · ${preparedCount} prontas para o lote` : "Busque uma obra para corrigir o ID."}</p>
            <div class="decision-workspace-modes" role="group" aria-label="Modo de trabalho">
              <button type="button" data-flow-workspace-mode="review" aria-pressed="${mode === "review"}" class="decision-workspace-control ${mode === "review" ? "active" : ""}">Pendências</button>
              <button type="button" data-flow-workspace-mode="confirmed" aria-pressed="${mode === "confirmed"}" class="decision-workspace-control ${mode === "confirmed" ? "active" : ""}">IDs confirmados</button>
            </div>
            <input type="search" class="decision-workspace-search" placeholder="Buscar obra..." aria-label="Buscar obra" ${mode === "review" ? `data-flow-review-search value="${escapeHtml(search)}"` : `data-confirmed-id-search value="${escapeHtml(search)}"`}>
          </div>
          <div class="decision-workspace-list">
            ${mode === "review" ? reviewQueue(visible, current, saved, decisions) : confirmedQueue(visible, confirmed)}
          </div>
          <div class="decision-workspace-rail-foot">${mode === "review" ? "Decisões preparadas ficam no fim da fila." : "Correções de vínculo não entram no lote de revisão."}</div>
        </aside>
        <div class="decision-workspace-detail">
          ${mode === "review" ? reviewDetail(current, decisions, saved, options) : confirmedDetail(confirmed)}
        </div>
      </div>
      <footer class="decision-workspace-footer">
        <span><strong>${preparedCount} ${preparedCount === 1 ? "decisão preparada" : "decisões preparadas"}</strong> <b>·</b> ${pending.length} ${pending.length === 1 ? "pendente" : "pendentes"} <b>·</b> Gravação somente após confirmação</span>
        <button type="button" class="primary-action" data-flow-batch-open ${preparedCount ? "" : "disabled"}>Conferir lote (${preparedCount})</button>
      </footer>
    </section>
    ${batchDialog(readyDecisions, pending.length, options)}
    ${correctionDialog(confirmed)}
  `;
}
