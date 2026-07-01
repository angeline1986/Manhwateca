# 03 — Tela: Aplicar Decisões

## 1. Objetivo Funcional — User Story

Como usuária, quero aplicar no PostgreSQL as decisões revisadas, para transformar escolhas temporárias em IDs confirmados no catálogo principal.

- Lista decisões prontas para gravação.
- Valida duplicidade antes de aplicar.
- Grava `mangaupdates_id` na obra.
- Registra log/auditoria.
- Remove ou marca itens da fila como aplicados.

## 2. Mapeamento de Dados — Data Schema

### KPIs

```ts
export interface AplicarDecisoesKpis {
  readyToApply: number;
  blockedByDuplicate: number;
  blockedByInvalidId: number;
  appliedToday: number;
}
```

```sql
SELECT
  COUNT(*) FILTER (WHERE selected_mangaupdates_id IS NOT NULL AND applied_at IS NULL) AS ready_to_apply,
  COUNT(*) FILTER (WHERE has_duplicate = TRUE) AS blocked_by_duplicate,
  COUNT(*) FILTER (WHERE is_valid_id = FALSE) AS blocked_by_invalid_id,
  COUNT(*) FILTER (WHERE applied_at::date = CURRENT_DATE) AS applied_today
FROM mangaupdates_decision_queue;
```

### Tabela Principal

```ts
export interface ApplyDecisionRow {
  queueId: string;
  mangaId: string;
  localTitle: string;
  selectedMangaupdatesId: string;
  selectedTitle: string | null;
  source: "candidate" | "manual";
  validationStatus: "READY" | "DUPLICATE" | "INVALID_ID" | "STALE";
  expectedResult: "SAVE_WORK_CODE" | "BLOCKED";
}
```

## 3. Arquitetura de API — Endpoints

| Método | Rota | Descrição | Carga |
|---|---|---|---|
| GET | `/api/mangaupdates/decisions/ready` | Lista decisões prontas | Paginado |
| POST | `/api/mangaupdates/decisions/validate` | Valida lote antes de aplicar | Síncrono |
| POST | `/api/mangaupdates/decisions/apply` | Aplica decisões | Job assíncrono |

```ts
export interface ApplyDecisionsRequest {
  queueIds: string[];
  dryRun?: boolean;
}

export interface ApplyDecisionsResponse {
  jobId: string;
  accepted: number;
  blocked: number;
}
```

```json
{
  "success": true,
  "data": {
    "jobId": "job_apply_001",
    "accepted": 10,
    "blocked": 1
  }
}
```

## 4. Regras de Negócio e Lógica de Processamento

### Critério de Entrada

```sql
WHERE selected_mangaupdates_id IS NOT NULL
  AND applied_at IS NULL
```

### Regras

- Não aplicar decisão com ID duplicado em outra obra ativa.
- Não aplicar decisão sem validação.
- Aplicação deve ser transacional por item.
- Falha em um item não deve cancelar todo o lote.

```sql
ORDER BY
  CASE
    WHEN validation_status = 'DUPLICATE' THEN 1
    WHEN validation_status = 'INVALID_ID' THEN 2
    WHEN validation_status = 'READY' THEN 3
    ELSE 9
  END,
  updated_at ASC;
```

## 5. Comportamento de Componentes e Gatilhos

| Componente | Tipo | Efeito |
|---|---|---|
| Aplicar decisões selecionadas | Assíncrono/job | Atualiza tabela principal |
| Voltar para revisão | Síncrono | Navega para fila de revisão |
| Validar antes de aplicar | Síncrono | Detecta duplicidades e stale data |

## 6. Estados da Interface e Edge Cases

- Empty: “Nenhuma decisão pronta para aplicar.”
- Duplicidade: bloquear item e apontar obra conflitante.
- Stale data: decisão feita sobre candidato desatualizado.
- Falha parcial: exibir itens aplicados e itens bloqueados.
- Timeout do job: manter status consultável em `/api/jobs/{jobId}`.
