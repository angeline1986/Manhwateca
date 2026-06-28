/* ==========================================================================
   CORE STATE - Estado Global da Aplicação
   ========================================================================== */

export const state = {
  catalog: [],
  reviewItems: [],
  editorialWorks: [],
  workflowState: null,
  lastTasks: [],
  
  // Helpers para busca no estado
  getCatalogItem(name) {
    return this.catalog.find(m => m.nome === name);
  }
};