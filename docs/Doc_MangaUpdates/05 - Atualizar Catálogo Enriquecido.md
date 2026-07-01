# 05 — Tela: Atualizar Catálogo Enriquecido

## 1. Objetivo Funcional — User Story

Como usuária, quero recalcular o catálogo enriquecido depois de consultar os detalhes do MangaUpdates, para refletir metadados, capítulos, status e aliases seguros.

- Recalcula dados derivados dos detalhes.
- Atualiza pendências.
- Gera catálogo enriquecido.
- Executa reconciliação segura de aliases locais.
- Permite pré-visualizar mudanças antes de aplicar.

## 2. Mapeamento de Dados — Data Schema

### KPIs

```ts
export interface CatalogoEnriquecidoKpis {
  readyToRefresh: boolean;
  detailsSynced: number;
  aliasesSuggested: number;
  aliasesSafeToApply: number;
  pendingRecalculation: number;
}
```

```sql
SELECT
  COUNT(*) FILTER (WHERE details_status = 'SYNCED') AS details_synced,
  COUNT(*) FILTER (WHERE alias_status = 'SUGGESTED') AS aliases_suggested,
  COUNT(*) FILTER (WHERE alias_status = 'SAFE_TO_APPLY') AS aliases_safe_to_apply,
  COUNT(*) FILTER (WHERE catalog_needs_refresh = TRUE) AS pending_recalculation
FROM mangas;
```

### Tabela Principal

```ts
export interface CatalogRefreshRow {
  mangaId: string;
  localTitle: string;
  mangaupdatesId: string | null;
  detailsStatus: string;
  aliasSuggestion: string | null;
  aliasConfidence: number | null;
  catalogNeedsRefresh: boolean;
  expectedChanges: CatalogExpectedChange[];
}

export interface CatalogExpectedChange {
  field: string;
  before: string | number | null;
  after: string | number | null;
  confidence?: number;
}
```

## 3. Arquitetura de API — Endpoints

| Método | Rota | Descrição | Carga |
|---|---|---|---|
| GET | `/api/mangaupdates/catalog/preview` | Prévia das mudanças | Paginado |
| POST | `/api/mangaupdates/catalog/refresh` | Atualiza catálogo | Job assíncrono |
| POST | `/api/mangaupdates/aliases/apply-safe` | Aplica aliases seguros | Job assíncrono |

```ts
export interface CatalogRefreshRequest {
  applyAliases?: boolean;
  dryRun?: boolean;
  onlySafeMatches?: boolean;
}
```

## 4. Regras de Negócio e Lógica de Processamento

### Critério de Entrada

```sql
WHERE details_status = 'SYNCED'
   OR catalog_needs_refresh = TRUE
   OR alias_status IN ('SUGGESTED', 'SAFE_TO_APPLY')
```

### Regras

- Alias só pode ser gravado automaticamente quando `aliasConfidence >= 95`.
- Se houver mais de uma obra compatível, bloquear alias automático.
- Atualização do catálogo deve gerar log.
- Dry-run deve mostrar mudanças sem gravar.

```sql
ORDER BY
  CASE
    WHEN alias_status = 'SAFE_TO_APPLY' THEN 1
    WHEN catalog_needs_refresh = TRUE THEN 2
    WHEN alias_status = 'SUGGESTED' THEN 3
    ELSE 9
  END,
  alias_confidence DESC NULLS LAST,
  updated_at DESC;
```

## 5. Comportamento de Componentes e Gatilhos

| Componente | Tipo | Efeito |
|---|---|---|
| Atualizar catálogo enriquecido | Assíncrono/job | Recalcula dados derivados |
| Pré-visualizar mudanças | Síncrono | Retorna diff sem gravar |
| Aplicar aliases seguros | Assíncrono/job | Grava aliases com alta confiança |

## 6. Estados da Interface e Edge Cases

- Empty: “Catálogo já está atualizado.”
- Alias ambíguo: nunca aplicar automaticamente.
- Detalhe ausente: item fica fora do refresh.
- Falha parcial: manter log por obra.
- Escalabilidade: usar paginação e job em lote.
