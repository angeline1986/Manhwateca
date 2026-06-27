# Dashboard — Documentação Técnica

## 04 - Modelo de Dados

---

# Objetivo

Este documento descreve o modelo de dados utilizado pelo Dashboard da Manhwateca, incluindo:

* entidades consultadas;
* tabelas PostgreSQL;
* relacionamentos;
* índices recomendados;
* consultas SQL utilizadas para agregação;
* estratégias de otimização;
* construção do `DashboardViewModel`.

O Dashboard **não possui tabelas próprias**. Ele é um módulo de leitura que consolida informações provenientes de diferentes domínios da aplicação.

---

# Visão Geral

O Dashboard consome dados de múltiplos repositórios.

```text
                 Dashboard

                      │

      ┌───────────────┼────────────────┐

      ▼               ▼                ▼

  Biblioteca      Workflow        Integrações

      │               │                │

      └───────────────┼────────────────┘

                      ▼

                 PostgreSQL
```

Nenhum dado é persistido pelo Dashboard.

---

# Fontes de Dados

| Origem              | Responsabilidade                |
| ------------------- | ------------------------------- |
| PostgreSQL          | Dados principais da biblioteca  |
| Sistema de Arquivos | Estado da biblioteca local      |
| MangaUpdates        | Disponibilidade de atualizações |
| Notion              | Estado da sincronização         |

A consulta ao PostgreSQL deve ser considerada a fonte de verdade para todas as métricas locais.

---

# Entidades Consultadas

O Dashboard consulta informações derivadas das seguintes entidades de domínio:

```text
Library

Manga

Chapter

Workflow

SyncJob

IntegrationStatus
```

Essas entidades pertencem a outros módulos e não devem ser modificadas pelo Dashboard.

---

# Modelo Conceitual

```text
Library
    │
    ├──────── Manga
    │             │
    │             ├──────── Chapter
    │             │
    │             └──────── Metadata
    │
    ├──────── WorkflowState
    │
    ├──────── SyncQueue
    │
    └──────── IntegrationStatus
```

---

# Exemplo de Estrutura Relacional

## Tabela `manga`

| Campo           | Tipo      | Observação       |
| --------------- | --------- | ---------------- |
| id              | bigint    | PK               |
| title           | text      | Nome da obra     |
| mangaupdates_id | bigint    | Nullable         |
| status          | text      | Enum             |
| created_at      | timestamp | Cadastro         |
| updated_at      | timestamp | Última alteração |

---

## Índices recomendados

```sql
CREATE INDEX idx_manga_status
ON manga(status);

CREATE INDEX idx_manga_mangaupdates_id
ON manga(mangaupdates_id);
```

---

# Tabela `chapter`

| Campo          | Tipo      |
| -------------- | --------- |
| id             | bigint    |
| manga_id       | bigint    |
| chapter_number | numeric   |
| is_new         | boolean   |
| created_at     | timestamp |

---

## Índices

```sql
CREATE INDEX idx_chapter_new
ON chapter(is_new);

CREATE INDEX idx_chapter_manga
ON chapter(manga_id);
```

---

# Tabela `workflow_state`

| Campo           | Tipo      |
| --------------- | --------- |
| id              | bigint    |
| current_step    | integer   |
| completed_steps | integer   |
| status          | text      |
| updated_at      | timestamp |

---

# Tabela `sync_queue`

| Campo       | Tipo      |
| ----------- | --------- |
| id          | bigint    |
| entity_type | text      |
| entity_id   | bigint    |
| synced      | boolean   |
| created_at  | timestamp |

---

# Tabela `integration_status`

| Campo       | Tipo      |
| ----------- | --------- |
| id          | bigint    |
| integration | text      |
| status      | text      |
| message     | text      |
| checked_at  | timestamp |

---

# Consultas SQL

## Total de obras

```sql
SELECT COUNT(*)
FROM manga;
```

---

## Obras sem ID

```sql
SELECT COUNT(*)
FROM manga
WHERE mangaupdates_id IS NULL;
```

---

## Obras com novos capítulos

```sql
SELECT COUNT(DISTINCT manga_id)
FROM chapter
WHERE is_new = TRUE;
```

A utilização de `DISTINCT` evita contabilizar múltiplos capítulos da mesma obra.

---

## Pendências de sincronização

```sql
SELECT COUNT(*)
FROM sync_queue
WHERE synced = FALSE;
```

---

## Etapa atual do Workflow

```sql
SELECT
    current_step,
    completed_steps,
    status
FROM workflow_state
ORDER BY updated_at DESC
LIMIT 1;
```

---

## Estado das integrações

```sql
SELECT
    integration,
    status,
    message
FROM integration_status;
```

---

# Consulta Consolidada

Embora as consultas possam ser executadas individualmente pelos respectivos repositórios, recomenda-se que a consolidação ocorra na camada de serviço.

Exemplo em pseudocódigo:

```python
metrics = MetricsRepository.load()
workflow = WorkflowRepository.load()
sync = SyncRepository.load()
integrations = IntegrationRepository.load()

return DashboardViewModel(
    metrics=metrics,
    workflow=workflow,
    integrations=integrations,
    sync=sync
)
```

A responsabilidade pela agregação pertence ao `DashboardAggregationService`, nunca aos repositórios.

---

# Estratégia de Agregação

Cada repositório deve executar apenas consultas relacionadas ao seu domínio.

```text
MangaRepository

↓

count_library()

count_missing_ids()

count_new_chapters()

──────────────

WorkflowRepository

↓

load_state()

──────────────

SyncRepository

↓

count_pending_sync()

──────────────

IntegrationRepository

↓

load_status()
```

O Aggregation Service consolida os resultados em um único ViewModel.

---

# Regras de Performance

As consultas utilizadas pelo Dashboard devem obedecer às seguintes regras:

* utilizar índices apropriados;
* evitar `SELECT *`;
* evitar `JOIN` desnecessários;
* utilizar agregações (`COUNT`, `SUM`, `EXISTS`) sempre que possível;
* evitar carregar entidades completas quando apenas métricas forem necessárias.

---

# Estratégia de Cache

As consultas do Dashboard são predominantemente de leitura.

Pode-se utilizar cache em memória para reduzir a carga do banco.

Recomendações:

| Informação  | TTL sugerido |
| ----------- | ------------ |
| Métricas    | 30 segundos  |
| Workflow    | 10 segundos  |
| Integrações | 15 segundos  |
| Pendências  | 15 segundos  |

O cache deve ser invalidado sempre que uma operação do Workflow for concluída.

---

# Consistência

Todas as consultas utilizadas para construir o Dashboard devem representar o mesmo instante lógico.

Para isso:

* executar todas as leituras dentro da mesma transação de leitura, quando aplicável;
* evitar leituras parciais durante atualizações concorrentes;
* construir o ViewModel apenas após a obtenção de todos os resultados.

---

# ViewModel Derivado

O resultado final da agregação deve possuir a seguinte estrutura lógica:

```text
DashboardViewModel

├── generatedAt
├── metrics
│     ├── libraryCount
│     ├── newChapters
│     ├── missingIds
│     └── pendingNotionSync
│
├── workflow
│
├── pendingActions
│
├── integrations
│
└── nextAction
```

Nenhuma consulta SQL deve conhecer essa estrutura.

---

# Responsabilidades

| Camada     | Responsabilidade     |
| ---------- | -------------------- |
| Repository | Executar SQL         |
| Service    | Agregar dados        |
| Controller | Serializar resposta  |
| Frontend   | Renderizar ViewModel |

---

# Anti-patterns

As seguintes práticas são proibidas:

* executar SQL diretamente no Controller;
* executar SQL no JavaScript;
* reutilizar entidades do ORM como resposta da API;
* executar consultas duplicadas para o mesmo indicador;
* construir métricas diretamente na interface.

---

# Relação com os demais documentos

| Documento           | Conteúdo relacionado                     |
| ------------------- | ---------------------------------------- |
| 02-arquitetura.md   | Organização das camadas e fluxo de dados |
| 03-api-dashboard.md | Estrutura do ViewModel consumido pela UI |
| 05-componentes.md   | Consumo das métricas por componente      |
| 08-atualizacao.md   | Estratégias de invalidação do cache      |

---

# Conclusão

O Dashboard deve ser tratado como um **módulo de leitura e agregação**. Todas as consultas ao PostgreSQL devem permanecer encapsuladas em repositórios especializados, enquanto a consolidação das informações ocorre exclusivamente no `DashboardAggregationService`.

Essa separação reduz o acoplamento, facilita testes, melhora a performance das consultas e garante que o contrato da API permaneça estável mesmo diante de mudanças no modelo relacional.
