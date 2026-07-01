# 01 — Tela: Buscar IDs

## 1. Objetivo Funcional — User Story

Como usuária, quero localizar candidatos no MangaUpdates para obras que ainda não possuem ID confirmado, para iniciar o enriquecimento de dados sem alterar o catálogo de forma definitiva.

- Mostra obras sem `mangaupdates_id`.
- Permite executar busca na API externa.
- Classifica resultados em: candidatos encontrados, sem resultado e erro.
- Alimenta a fila de revisão quando o match não é seguro.

## 2. Mapeamento de Dados — Data Schema

### KPIs

```ts
export interface BuscarIdsKpis {
  withoutId: number;
  readyToSearch: number;
  candidatesFound: number;
  noResult: number;
  apiErrors: number;
}
```

```sql
SELECT
  COUNT(*) FILTER (WHERE mangaupdates_id IS NULL) AS without_id,
  COUNT(*) FILTER (WHERE decision_status = 'READY_TO_SEARCH') AS ready_to_search,
  COUNT(*) FILTER (WHERE decision_status = 'CANDIDATES_FOUND') AS candidates_found,
  COUNT(*) FILTER (WHERE decision_status = 'MANUAL_ID_REQUIRED') AS no_result,
  COUNT(*) FILTER (WHERE decision_status = 'ERROR') AS api_errors
FROM mangas;
```

### Tabela Principal

```ts
export interface BuscarIdsRow {
  id: string;
  localTitle: string;
  normalizedTitle: string;
  alternativeTitles: string[];
  folderPath: string | null;
  decisionStatus: "WITHOUT_ID" | "READY_TO_SEARCH" | "CANDIDATES_FOUND" | "MANUAL_ID_REQUIRED" | "ERROR";
  lastSearchAt: string | null;
  candidatesCount: number;
  nextAction: "SEARCH_API" | "NORMALIZE_TITLE" | "REVIEW_CANDIDATES" | "MANUAL_SEARCH";
}
```

### Enums Recomendados

```ts
export enum BuscarIdsAction {
  SEARCH_AND_ENRICH = "SEARCH_AND_ENRICH",
  FILTER_WITHOUT_ID = "FILTER_WITHOUT_ID",
  RETRY_FAILED = "RETRY_FAILED"
}
```

## 3. Arquitetura de API — Endpoints

| Método | Rota | Descrição | Carga |
|---|---|---|---|
| GET | `/api/mangaupdates/works?status=WITHOUT_ID` | Lista obras sem ID | Paginado |
| POST | `/api/mangaupdates/search` | Inicia busca em lote | Job assíncrono |
| GET | `/api/jobs/{jobId}` | Consulta progresso do job | Polling |

```ts
export interface BuscarIdsQueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  onlyFailed?: boolean;
  sort?: "title" | "updatedAt" | "lastSearchAt";
}
```

```json
{
  "success": true,
  "data": {
    "kpis": {
      "withoutId": 18,
      "readyToSearch": 18,
      "candidatesFound": 12,
      "noResult": 6,
      "apiErrors": 0
    },
    "items": [
      {
        "id": "manga_001",
        "localTitle": "Exemplo de título A",
        "decisionStatus": "READY_TO_SEARCH",
        "candidatesCount": 0,
        "nextAction": "SEARCH_API"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "total": 18
    }
  }
}
```

## 4. Regras de Negócio e Lógica de Processamento

### Critério de Entrada

```sql
WHERE mangaupdates_id IS NULL
```

### Regras

- Obra sem ID entra como `WITHOUT_ID`.
- Se estiver elegível para busca, vira `READY_TO_SEARCH`.
- Se a API retornar candidatos, vira `CANDIDATES_FOUND`.
- Se houver mais de um candidato ou baixa confiança, vira `PENDING_REVIEW`.
- Se não houver resultado, vira `MANUAL_ID_REQUIRED`.

```sql
ORDER BY
  CASE
    WHEN decision_status = 'ERROR' THEN 1
    WHEN decision_status = 'MANUAL_ID_REQUIRED' THEN 2
    WHEN decision_status = 'READY_TO_SEARCH' THEN 3
    ELSE 9
  END,
  last_search_at ASC NULLS FIRST,
  local_title ASC;
```

## 5. Comportamento de Componentes e Gatilhos

| Componente | Tipo | Efeito |
|---|---|---|
| Buscar e enriquecer dados | Assíncrono/job | Consulta API e grava candidatos |
| Ver somente obras sem ID | Síncrono | Aplica filtro local/API |
| Retry de falhas | Assíncrono/job | Reprocessa apenas itens com erro |

## 6. Estados da Interface e Edge Cases

- Loading: skeleton nos KPIs e tabela.
- Empty: “Nenhuma obra sem ID encontrada.”
- 403: bloquear busca e exibir erro de permissão.
- 429: pausar job por rate limit.
- 503: manter itens como `ERROR` e permitir retry.
- Timeout: registrar tentativa e continuar lote.
