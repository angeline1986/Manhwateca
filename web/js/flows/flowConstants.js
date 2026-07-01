export const FLOW_STAGE_GROUPS = [
  {
    id: "resolve_ids",
    order: 1,
    title: "Resolver IDs",
    description: "Busca candidatos e confirma IDs oficiais no MangaUpdates.",
    steps: ["resolve_ids"],
  },
  {
    id: "update_metadata",
    order: 2,
    title: "Atualizar metadados",
    description: "Consulta detalhes oficiais e prepara dados enriquecidos.",
    steps: ["update_metadata"],
  },
  {
    id: "sync_notion",
    order: 3,
    title: "Sincronizar Notion",
    description: "Reflete no Notion as alterações realizadas durante o Workflow.",
    steps: ["sync_notion"],
  },
];

export const RESOLVE_ID_STEPS = [
  {
    id: "buscar",
    title: "Buscar candidatos",
    description: "Consulta o MangaUpdates para obras sem ID oficial.",
  },
  {
    id: "pendencias",
    title: "Revisar pendências",
    description: "Valida candidatos ambíguos ou informa IDs manualmente.",
  },
  {
    id: "decisoes",
    title: "Aplicar decisões",
    description: "Grava as decisões revisadas no banco de dados.",
  },
];

export const ACTIVE_FLOW_STEPS = FLOW_STAGE_GROUPS.flatMap(group => group.steps);
export const ACTIVE_FLOW_STEP_SET = new Set(ACTIVE_FLOW_STEPS);

export const FLOW_STATUS_LABELS = {
  waiting: "Aguardando",
  validating: "Validando",
  running: "Processando",
  completed: "Concluída",
  completed_with_warnings: "Concluída com alertas",
  skipped: "Ignorada",
  failed: "Falhou",
  cancelled: "Cancelada",
};
