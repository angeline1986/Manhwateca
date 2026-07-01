# 02 — Tela: Correspondências Pendentes

## 1. Objetivo Funcional — User Story

Como usuária, quero revisar candidatos retornados pelo MangaUpdates para escolher o ID correto ou informar um ID manual, evitando gravações incorretas.

- Exibe obras com candidatos ambíguos.
- Mostra confiança de cada candidato.
- Permite selecionar candidato, informar ID manual ou ignorar temporariamente.
- Prepara decisões para aplicação posterior.

## 2. Mapeamento de Dados — Data Schema

### KPIs

```ts
export interface CorrespondenciasPendentesKpis {
  pendingReview: number;
  ambiguous: number;
  lowConfidence: number;
  manualIdRequired: number;
  selectedButNotApplied: number;
}
```

```sql
SELECT
  COUNT(*) FILTER (WHERE decision_status = 'PENDING_REVIEW') AS pending_review,
  COUNT(*) FILTER (WHERE candidates_count > 1) AS ambiguous,
  COUNT(*) FILTER (WHERE match_confidence < 85) AS low_confidence,
  COUNT(*) FILTER (WHERE decision_status = 'MANUAL_ID_REQUIRED') AS manual_id_required,
  COUNT(*) FILTER (WHERE selected_candidate_id IS NOT NULL AND applied_at IS NULL) AS selected_but_not_applied
FROM mangaupdates_decision_queue;
```

### Tabela Principal

```ts
export interface PendingDecisionRow {
  queueId: string;
  mangaId: string;
  localTitle: string;
  normalizedTitle: string;
  candidates: MangaUpdatesCandidate[];
  selectedCandidateId: string | null;
  manualMangaupdatesId: string | null;
  decisionStatus: "PENDING_REVIEW" | "MANUAL_ID_REQUIRED" | "IGNORED";
  confidence: number | null;
  reason: "AMBIGUOUS" | "LOW_CONFIDENCE" | "NO_RESULT" | "ALIAS_DETECTED";
  updatedAt: string;
}

export interface MangaUpdatesCandidate {
  id: string;
  title: string;
  url: string;
  confidence: number;
  isRecommended: boolean;
}
```

## 3. Arquitetura de API — Endpoints

| Método | Rota | Descrição | Carga |
|---|---|---|---|
| GET | `/api/mangaupdates/review` | Lista fila de revisão | Paginado |
| POST | `/api/mangaupdates/decisions` | Salva decisão temporária | Síncrono |
| POST | `/api/mangaupdates/decisions/ignore` | Ignora item temporariamente | Síncrono |

```ts
export interface ReviewQueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  reason?: "AMBIGUOUS" | "LOW_CONFIDENCE" | "NO_RESULT" | "ALIAS_DETECTED";
  onlyUndecided?: boolean;
}
```

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "queueId": "dq_001",
        "mangaId": "manga_001",
        "localTitle": "Exemplo de título A",
        "reason": "AMBIGUOUS",
        "candidates": [
          { "id": "123", "title": "Example Title A", "confidence": 87, "isRecommended": true }
        ]
      }
    ]
  }
}
```

## 4. Regras de Negócio e Lógica de Processamento

### Critério de Entrada

```sql
WHERE decision_status IN ('PENDING_REVIEW', 'MANUAL_ID_REQUIRED')
   OR selected_candidate_id IS NOT NULL AND applied_at IS NULL
```

### Regras

- Candidato único com confiança alta pode ser recomendado, mas ainda deve ser validado se a tela exigir revisão.
- ID manual deve validar formato e existência antes da aplicação definitiva.
- Decisão salva aqui não grava diretamente `mangaupdates_id` na tabela principal.
- Item ignorado não deve sumir definitivamente; deve poder ser reaberto.

```sql
ORDER BY
  CASE
    WHEN reason = 'AMBIGUOUS' THEN 1
    WHEN reason = 'LOW_CONFIDENCE' THEN 2
    WHEN reason = 'ALIAS_DETECTED' THEN 3
    WHEN reason = 'NO_RESULT' THEN 4
    ELSE 9
  END,
  confidence ASC NULLS FIRST,
  updated_at DESC;
```

## 5. Comportamento de Componentes e Gatilhos

| Componente | Tipo | Efeito |
|---|---|---|
| Selecionar candidato | Síncrono | Atualiza decisão temporária |
| Informar ID manual | Síncrono | Salva ID manual na fila |
| Marcar decisão | Síncrono | Define item como pronto para aplicar |
| Ignorar por enquanto | Síncrono | Mantém rastreio, mas remove da prioridade |

## 6. Estados da Interface e Edge Cases

- Empty: “Não há correspondências pendentes.”
- Duplicidade de ID selecionado: mostrar alerta antes de aplicar.
- ID manual inválido: bloquear salvamento.
- Candidato removido da API: manter registro local e sinalizar.
- Lista grande: paginação obrigatória.
