# Dashboard — Documentação Técnica

## 10 - Performance

---

# Objetivo

Este documento estabelece os requisitos de desempenho do Dashboard da Manhwateca, as metas de performance, as estratégias de otimização e os critérios técnicos que devem ser seguidos durante a implementação.

O Dashboard é uma tela de leitura intensiva (read-heavy), acessada com frequência e utilizada como ponto de entrada da aplicação. Por esse motivo, sua arquitetura deve privilegiar baixa latência, consultas eficientes e renderização rápida.

Os objetivos principais são:

* minimizar o tempo de carregamento;
* reduzir consultas redundantes;
* evitar gargalos de renderização;
* otimizar o acesso ao PostgreSQL;
* manter a experiência do usuário consistente mesmo com grandes bibliotecas.

---

# Metas de Performance

As metas abaixo devem ser utilizadas como referência para validação da implementação.

| Indicador                        | Meta     |
| -------------------------------- | -------- |
| Tempo de resposta da API         | ≤ 300 ms |
| Tempo de agregação (Backend)     | ≤ 200 ms |
| Tempo de renderização (Frontend) | ≤ 100 ms |
| Tempo total Dashboard → Render   | ≤ 500 ms |
| Atualização manual (Refresh)     | ≤ 500 ms |
| Taxa de erro                     | < 1%     |

Esses valores consideram uma instalação local utilizando PostgreSQL.

---

# Indicadores Web (Core Web Vitals)

Embora a aplicação seja local, recomenda-se observar os principais indicadores do navegador.

| Métrica                         | Meta     |
| ------------------------------- | -------- |
| LCP (Largest Contentful Paint)  | < 2,5 s  |
| INP (Interaction to Next Paint) | < 200 ms |
| CLS (Cumulative Layout Shift)   | < 0,1    |
| TTFB (Time to First Byte)       | < 200 ms |

Esses indicadores garantem uma interface responsiva e estável.

---

# Pipeline de Carregamento

O fluxo completo de carregamento deve seguir a sequência abaixo.

```text
Usuário

↓

GET /api/dashboard

↓

Dashboard Controller

↓

DashboardAggregationService

↓

Repositories

↓

PostgreSQL

↓

DashboardViewModel

↓

JSON

↓

Frontend

↓

Renderização
```

Cada etapa deve possuir métricas próprias de monitoramento.

---

# Estratégia de Consultas

O Dashboard deve executar apenas consultas de leitura.

As consultas devem privilegiar:

* `COUNT`;
* `EXISTS`;
* agregações;
* índices.

Evitar:

* carregamento de entidades completas;
* consultas repetidas;
* múltiplos `JOIN` quando não forem necessários.

---

# Consultas Recomendadas

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

---

## Pendências de sincronização

```sql
SELECT COUNT(*)
FROM sync_queue
WHERE synced = FALSE;
```

Todas essas consultas possuem custo reduzido quando os índices apropriados estão presentes.

---

# Índices Obrigatórios

## Manga

```sql
CREATE INDEX idx_manga_mangaupdates
ON manga(mangaupdates_id);
```

---

## Chapter

```sql
CREATE INDEX idx_chapter_new
ON chapter(is_new);

CREATE INDEX idx_chapter_manga
ON chapter(manga_id);
```

---

## Sync Queue

```sql
CREATE INDEX idx_sync_pending
ON sync_queue(synced);
```

---

## Workflow

```sql
CREATE INDEX idx_workflow_updated
ON workflow_state(updated_at DESC);
```

Esses índices reduzem significativamente o custo das consultas utilizadas pelo Dashboard.

---

# Evitando N+1 Queries

O Dashboard nunca deve executar consultas por item.

Exemplo incorreto:

```text
Para cada obra

↓

SELECT ...
```

Resultado:

```text
1 + N consultas
```

Exemplo correto:

```text
1 consulta agregada

↓

COUNT

↓

Resposta
```

Sempre preferir agregações no banco.

---

# Agregação no Banco vs Aplicação

Sempre que possível, o PostgreSQL deve realizar os cálculos.

Exemplo correto:

```sql
SELECT COUNT(*)
FROM manga;
```

Evitar:

```python
len(repository.find_all())
```

Transferir milhares de registros apenas para contar elementos aumenta consumo de memória e tempo de processamento.

---

# Estratégia de Cache

Cada serviço pode manter cache próprio.

| Serviço            | TTL  |
| ------------------ | ---- |
| MetricsService     | 30 s |
| WorkflowService    | 10 s |
| PendingService     | 15 s |
| IntegrationService | 15 s |

O DashboardAggregationService não deve armazenar cache.

---

# Invalidação

O cache deve ser invalidado quando ocorrer:

* organização da biblioteca;
* catalogação;
* resolução de IDs;
* atualização de metadados;
* sincronização com Notion;
* alteração de configurações.

Nunca utilizar apenas expiração temporal quando houver eventos claros de invalidação.

---

# Paralelismo

Os serviços independentes podem ser executados em paralelo.

Fluxo recomendado:

```text
                 DashboardAggregationService

                          │

        ┌─────────────────┼─────────────────┐

        ▼                 ▼                 ▼

 MetricsService   WorkflowService   IntegrationService

        ▼                 ▼                 ▼

             Aguardar conclusão de todos

                          ▼

                Construir DashboardViewModel
```

O paralelismo reduz significativamente o tempo de agregação.

---

# Serialização

A serialização do ViewModel deve ocorrer apenas uma vez.

Fluxo:

```text
Objetos

↓

DashboardViewModel

↓

JSON

↓

HTTP Response
```

Evitar múltiplas conversões intermediárias.

---

# Otimização do Frontend

O Frontend deve:

* realizar apenas uma chamada HTTP;
* renderizar componentes a partir do ViewModel;
* evitar manipulação excessiva do DOM;
* reutilizar elementos quando possível.

Nunca executar cálculos pesados em JavaScript.

---

# Atualização da Interface

Durante o refresh:

* manter o conteúdo anterior visível;
* substituir o ViewModel apenas após sucesso;
* evitar reconstrução completa do DOM quando não necessária.

Isso reduz flickering e melhora a percepção de desempenho.

---

# Lazy Loading

O Dashboard não deve utilizar lazy loading para seus componentes principais.

Todos os componentes são críticos para a compreensão do estado da aplicação.

O lazy loading pode ser utilizado futuramente para módulos secundários ou gráficos históricos.

---

# Monitoramento

Cada atualização deve registrar:

```json
{
  "operation": "dashboard.refresh",
  "duration_ms": 182,
  "database_ms": 97,
  "serialization_ms": 8,
  "render_ms": 61
}
```

Essas métricas permitem identificar gargalos específicos.

---

# Gargalos Comuns

| Sintoma         | Possível causa                      |
| --------------- | ----------------------------------- |
| API lenta       | Consultas sem índice                |
| Refresh lento   | Cache não utilizado                 |
| Interface lenta | Manipulação excessiva do DOM        |
| CPU elevada     | Agregações realizadas na aplicação  |
| Memória elevada | Carregamento de entidades completas |

---

# Estratégias de Escalabilidade

Para bibliotecas com milhares de obras:

* manter consultas agregadas;
* utilizar índices específicos;
* evitar consultas por registro;
* utilizar paginação apenas nos módulos que listam dados (não no Dashboard);
* manter o ViewModel compacto.

O tamanho do JSON do Dashboard deve permanecer pequeno e previsível.

---

# Anti-patterns

As seguintes práticas são proibidas:

* `SELECT *` quando apenas contagens forem necessárias;
* consultas N+1;
* múltiplas chamadas HTTP para montar o Dashboard;
* lógica de agregação no Frontend;
* cache global compartilhado entre módulos;
* atualização individual de componentes.

---

# Checklist de Performance

| Item                       | Obrigatório |
| -------------------------- | ----------- |
| Apenas um endpoint HTTP    | ✅           |
| Consultas agregadas        | ✅           |
| Índices criados            | ✅           |
| Sem N+1 Queries            | ✅           |
| Cache especializado        | ✅           |
| Atualização atômica        | ✅           |
| Paralelismo entre serviços | ✅           |
| Logs de performance        | ✅           |

---

# Relação com outros documentos

| Documento                 | Conteúdo relacionado         |
| ------------------------- | ---------------------------- |
| 04-modelo-de-dados.md     | Consultas SQL e índices      |
| 08-atualizacao.md         | Estratégia de refresh        |
| 09-tratamento-de-erros.md | Timeouts e retries           |
| 12-testes.md              | Testes de carga e desempenho |

---

# Conclusão

O desempenho do Dashboard depende diretamente da combinação entre uma arquitetura desacoplada, consultas SQL eficientes, agregação centralizada, caches especializados e renderização otimizada. O objetivo é garantir que o usuário obtenha uma visão completa do estado da biblioteca em poucos centenas de milissegundos, mesmo em cenários com grande volume de dados, mantendo consistência, previsibilidade e baixo consumo de recursos.
