# 00 — MangaUpdates: Visão Geral do Módulo

## 1. Objetivo Funcional — User Story

Como usuária da Manhwateca, quero centralizar em uma única área o fluxo de identificação, revisão e enriquecimento de obras via MangaUpdates para:

- descobrir IDs externos de obras cadastradas localmente;
- revisar correspondências ambíguas antes de gravar qualquer dado definitivo;
- confirmar IDs no PostgreSQL com rastreabilidade;
- consultar metadados externos somente para IDs já confirmados;
- recalcular o catálogo enriquecido sem misturar etapas manuais e automáticas.

## 2. Fluxo Macro

```text
MangaUpdates
├── 01 - Buscar IDs
├── 02 - Correspondências Pendentes
├── 03 - Aplicar Decisões
├── 04 - Consultar Detalhes dos IDs
└── 05 - Atualizar Catálogo Enriquecido
```

## 3. Máquina de Estados Recomendada

```text
WITHOUT_ID
  → READY_TO_SEARCH
  → CANDIDATES_FOUND
  → PENDING_REVIEW
  → CONFIRMED
  → DETAILS_PENDING
  → DETAILS_SYNCED
  → CATALOG_READY
```

## 4. Mapeamento de Dados Compartilhado — Data Schema

```ts
export interface MangaUpdatesWorkItem {
  id: string;
  localTitle: string;
  normalizedTitle: string;
  alternativeTitles: string[];
  folderPath: string | null;
  mangaupdatesId: string | null;
  mangaupdatesUrl: string | null;
  decisionStatus: DecisionStatus;
  detailsStatus: DetailsStatus;
  matchConfidence: number | null;
  candidatesCount: number;
  latestChapter: number | null;
  detailsSyncedAt: string | null;
  lastSearchAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export enum DecisionStatus {
  WITHOUT_ID = "WITHOUT_ID",
  READY_TO_SEARCH = "READY_TO_SEARCH",
  CANDIDATES_FOUND = "CANDIDATES_FOUND",
  PENDING_REVIEW = "PENDING_REVIEW",
  MANUAL_ID_REQUIRED = "MANUAL_ID_REQUIRED",
  CONFIRMED = "CONFIRMED",
  IGNORED = "IGNORED",
  ERROR = "ERROR"
}

export enum DetailsStatus {
  NOT_REQUIRED = "NOT_REQUIRED",
  PENDING = "PENDING",
  SYNCED = "SYNCED",
  API_ERROR = "API_ERROR",
  TIMEOUT = "TIMEOUT"
}
```

```sql
SELECT
  m.id,
  m.title AS local_title,
  m.normalized_title,
  m.alternative_titles,
  m.folder_path,
  m.mangaupdates_id,
  m.mangaupdates_url,
  m.decision_status,
  m.details_status,
  m.match_confidence,
  m.latest_mangaupdates_chapter,
  m.details_synced_at,
  m.last_search_at,
  m.created_at,
  m.updated_at
FROM mangas m;
```

## 5. Endpoints Compartilhados

| Método | Rota | Uso |
|---|---|---|
| GET | `/api/mangaupdates/status` | KPIs gerais do módulo |
| GET | `/api/mangaupdates/works` | Listagem paginada por status |
| GET | `/api/mangaupdates/review` | Fila de revisão |
| POST | `/api/mangaupdates/search` | Job de busca de IDs |
| POST | `/api/mangaupdates/decisions` | Salvar decisão temporária |
| POST | `/api/mangaupdates/decisions/apply` | Aplicar decisões no PostgreSQL |
| POST | `/api/mangaupdates/details/sync` | Consultar detalhes na API |
| POST | `/api/mangaupdates/catalog/refresh` | Recalcular catálogo enriquecido |

## 6. Regras Gerais de Segurança

- Nunca gravar `mangaupdates_id` automaticamente quando houver ambiguidade.
- Nunca gravar alias local se houver mais de uma obra possível.
- Toda decisão aplicada deve gerar log.
- Toda chamada externa deve ter timeout e retry controlado.
- Jobs em lote devem permitir falha parcial sem perder o progresso.

## 7. Ordenação Global Recomendada

```sql
ORDER BY
  CASE
    WHEN decision_status = 'PENDING_REVIEW' THEN 1
    WHEN decision_status = 'MANUAL_ID_REQUIRED' THEN 2
    WHEN decision_status = 'CANDIDATES_FOUND' THEN 3
    WHEN details_status = 'PENDING' THEN 4
    WHEN decision_status = 'WITHOUT_ID' THEN 5
    ELSE 9
  END,
  match_confidence ASC NULLS LAST,
  updated_at DESC,
  local_title ASC;
```
