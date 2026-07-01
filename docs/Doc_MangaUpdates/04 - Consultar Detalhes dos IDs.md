# 04 — Tela: Consultar Detalhes dos IDs

## 1. Objetivo Funcional — User Story

Como usuária, quero consultar os detalhes completos do MangaUpdates para obras com ID confirmado, para enriquecer o catálogo com metadados externos.

- Lista obras com ID confirmado.
- Identifica quais ainda não têm detalhes sincronizados.
- Executa consulta em lote na API externa.
- Registra falhas e permite retry.

## 2. Mapeamento de Dados — Data Schema

### KPIs

```ts
export interface ConsultarDetalhesKpis {
  confirmedIds: number;
  pendingDetails: number;
  syncedDetails: number;
  apiErrors: number;
  syncProgressPercent: number;
}
```

```sql
SELECT
  COUNT(*) FILTER (WHERE mangaupdates_id IS NOT NULL) AS confirmed_ids,
  COUNT(*) FILTER (WHERE mangaupdates_id IS NOT NULL AND details_synced_at IS NULL) AS pending_details,
  COUNT(*) FILTER (WHERE details_status = 'SYNCED') AS synced_details,
  COUNT(*) FILTER (WHERE details_status IN ('API_ERROR', 'TIMEOUT')) AS api_errors
FROM mangas;
```

### Tabela Principal

```ts
export interface DetailsSyncRow {
  mangaId: string;
  localTitle: string;
  mangaupdatesId: string;
  detailsStatus: "PENDING" | "SYNCED" | "API_ERROR" | "TIMEOUT";
  latestChapter: number | null;
  genres: string[];
  status: string | null;
  lastAttemptAt: string | null;
  detailsSyncedAt: string | null;
  errorMessage: string | null;
}
```

## 3. Arquitetura de API — Endpoints

| Método | Rota | Descrição | Carga |
|---|---|---|---|
| GET | `/api/mangaupdates/details/status` | KPIs de sincronização | Total |
| GET | `/api/mangaupdates/details/pending` | Obras aguardando detalhes | Paginado |
| POST | `/api/mangaupdates/details/sync` | Inicia consulta em lote | Job assíncrono |
| POST | `/api/mangaupdates/details/retry` | Reprocessa falhas | Job assíncrono |

```ts
export interface DetailsSyncQueryParams {
  page?: number;
  pageSize?: number;
  status?: "PENDING" | "SYNCED" | "API_ERROR" | "TIMEOUT";
  search?: string;
}
```

## 4. Regras de Negócio e Lógica de Processamento

### Critério de Entrada

```sql
WHERE mangaupdates_id IS NOT NULL
```

### Regras

- Detalhes só podem ser consultados para IDs confirmados.
- API externa deve ter timeout.
- Dados existentes só devem ser sobrescritos se a resposta for válida.
- Erros devem ser persistidos com mensagem e timestamp.

```sql
ORDER BY
  CASE
    WHEN details_status = 'API_ERROR' THEN 1
    WHEN details_status = 'TIMEOUT' THEN 2
    WHEN details_status = 'PENDING' THEN 3
    WHEN details_status = 'SYNCED' THEN 4
    ELSE 9
  END,
  last_attempt_at ASC NULLS FIRST,
  local_title ASC;
```

## 5. Comportamento de Componentes e Gatilhos

| Componente | Tipo | Efeito |
|---|---|---|
| Consultar detalhes agora | Assíncrono/job | Busca dados completos na API |
| Ver erros da API | Síncrono | Filtra itens com erro |
| Retry | Assíncrono/job | Reprocessa falhas |

## 6. Estados da Interface e Edge Cases

- Empty: “Todos os IDs confirmados já possuem detalhes.”
- 403: chave/limite de API inválido.
- 429: rate limit; aplicar backoff.
- 503: serviço externo indisponível.
- Timeout: marcar item como `TIMEOUT`.
- Resposta incompleta: manter detalhes antigos e registrar alerta.
