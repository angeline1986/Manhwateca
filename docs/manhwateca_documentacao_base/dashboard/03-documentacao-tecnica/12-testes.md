# Dashboard — Documentação Técnica

## 12 - Testes

---

# Objetivo

Este documento define a estratégia oficial de testes do módulo **Dashboard** da Manhwateca.

O Dashboard é um módulo de agregação de dados que depende de múltiplos serviços internos e integrações externas. Sua qualidade depende da validação de três aspectos principais:

* corretude da agregação de dados;
* estabilidade da interface;
* resiliência diante de falhas.

A estratégia apresentada neste documento busca garantir que alterações futuras possam ser realizadas com segurança, reduzindo regressões e aumentando a confiabilidade do sistema.

---

# Objetivos dos Testes

Os testes do Dashboard devem garantir que:

* o `DashboardViewModel` seja construído corretamente;
* os componentes renderizem corretamente todos os estados;
* a navegação funcione conforme especificado;
* falhas em serviços externos não interrompam a interface;
* consultas SQL retornem os resultados esperados;
* alterações futuras não provoquem regressões.

---

# Pirâmide de Testes

A estratégia do projeto segue a pirâmide clássica.

```text
                E2E

        Integração

      Unitários
```

Distribuição recomendada:

| Tipo       | Percentual |
| ---------- | ---------: |
| Unitários  |        70% |
| Integração |        20% |
| End-to-End |        10% |

---

# Organização dos Testes

Estrutura sugerida:

```text
tests/

├── unit/
│   ├── repositories/
│   ├── services/
│   ├── aggregation/
│   └── viewmodels/
│
├── integration/
│   ├── api/
│   ├── database/
│   └── integrations/
│
├── frontend/
│   ├── components/
│   ├── navigation/
│   └── accessibility/
│
└── e2e/
```

---

# Testes Unitários

Os testes unitários devem validar componentes isolados.

## Repositories

Validar:

* consultas SQL;
* tratamento de resultados vazios;
* tratamento de erros do banco.

Exemplo:

```python
def test_count_missing_ids():
    ...
```

---

## Services

Cada serviço deve ser testado isoladamente.

Exemplo:

```python
def test_metrics_service_returns_counts():
    ...
```

Validar:

* regras de agregação;
* ordenação;
* cálculos;
* transformação de DTOs.

---

## DashboardAggregationService

Este é o componente mais importante.

Testes obrigatórios:

* todos os serviços respondem corretamente;
* um serviço falha;
* múltiplos serviços falham;
* resposta completa;
* resposta parcial.

Exemplo:

```python
def test_build_dashboard_view_model():
    ...
```

---

# Mocking

Integrações externas devem ser simuladas.

Nunca depender de:

* MangaUpdates real;
* Notion real;
* Google Drive real.

Utilizar mocks ou fakes.

Exemplo:

```python
mock_notion.status = "healthy"
```

---

# Testes de Contrato

Validar o JSON produzido pela API.

Endpoint:

```http
GET /api/dashboard
```

Verificar:

* estrutura;
* nomes dos campos;
* tipos;
* obrigatoriedade.

Exemplo:

```python
assert response["metrics"]["libraryCount"] == 347
```

---

# Testes de Banco de Dados

Validar:

* consultas SQL;
* índices utilizados;
* consistência das agregações.

Exemplo:

```sql
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM manga;
```

Objetivo:

* identificar consultas lentas;
* detectar full table scans.

---

# Testes de Integração

Os testes de integração validam a comunicação entre componentes.

Fluxo:

```text
Controller

↓

AggregationService

↓

Repositories

↓

PostgreSQL
```

Devem utilizar banco de testes isolado.

---

# Testes das Integrações Externas

Validar cenários como:

## MangaUpdates indisponível

Resultado esperado:

* Dashboard funcional;
* integração em erro.

---

## Notion indisponível

Resultado esperado:

* sincronização indisponível;
* demais componentes preservados.

---

## PostgreSQL indisponível

Resultado esperado:

* resposta HTTP adequada;
* log estruturado.

---

# Testes do Frontend

Cada componente deve ser testado isoladamente.

## Header

Validar:

* renderização;
* botão Recarregar;
* data da última atualização.

---

## NextActionCard

Testar:

* loading;
* success;
* empty;
* error.

---

## MetricsGrid

Validar:

* renderização dos quatro cards;
* valores zero;
* números elevados.

---

## PendingActionsPanel

Validar:

* lista vazia;
* múltiplas pendências;
* ordenação recebida do backend.

---

## WorkflowPanel

Validar todos os estados:

* pending;
* running;
* completed;
* blocked;
* error.

---

## IntegrationsPanel

Validar:

* healthy;
* warning;
* error;
* unknown.

---

# Testes de Estados

Todos os estados definidos em `06-estados.md` devem possuir cobertura.

Tabela mínima:

| Componente    | Loading | Success | Empty | Error |
| ------------- | ------- | ------- | ----- | ----- |
| Header        | ✅       | ✅       | —     | ✅     |
| NextAction    | ✅       | ✅       | ✅     | ✅     |
| Metrics       | ✅       | ✅       | —     | —     |
| Pendências    | ✅       | ✅       | ✅     | ✅     |
| Workflow      | ✅       | ✅       | —     | ✅     |
| Integrações   | ✅       | ✅       | —     | ✅     |
| Ações Rápidas | ✅       | ✅       | —     | —     |

---

# Testes de Navegação

Validar:

* clique na ação recomendada;
* clique nas pendências;
* clique nas ações rápidas;
* retorno ao Dashboard;
* atualização após retorno.

---

# Testes de Acessibilidade

Executar:

* Lighthouse;
* axe DevTools;
* navegação por teclado;
* VoiceOver ou NVDA.

Validar:

* foco;
* landmarks;
* contraste;
* ARIA;
* leitura correta.

---

# Testes End-to-End

Fluxo completo.

```text
Abrir Dashboard

↓

Consultar Próxima Ação

↓

Abrir Fluxos

↓

Executar atividade

↓

Voltar

↓

Atualizar Dashboard

↓

Validar Workflow
```

Esse fluxo representa o principal caso de uso da aplicação.

---

# Testes de Performance

Executar:

* benchmark da API;
* benchmark das consultas;
* tempo de renderização;
* tempo de refresh.

Metas:

| Métrica | Valor    |
| ------- | -------- |
| API     | ≤ 300 ms |
| Refresh | ≤ 500 ms |
| Render  | ≤ 100 ms |

---

# Cobertura

Metas mínimas.

| Camada             | Cobertura |
| ------------------ | --------- |
| Services           | ≥ 95%     |
| Repositories       | ≥ 90%     |
| AggregationService | 100%      |
| Controllers        | ≥ 90%     |
| Frontend           | ≥ 85%     |

Cobertura não substitui qualidade dos testes.

---

# Testes de Regressão

Sempre executar antes do merge:

* Dashboard completo;
* Workflow;
* Integrações;
* Navegação;
* Atualização;
* API.

---

# CI/CD

Pipeline recomendado:

```text
Lint

↓

Testes Unitários

↓

Testes Integração

↓

Testes Frontend

↓

Testes E2E

↓

Build

↓

Deploy
```

O deploy só deve ocorrer após aprovação de todas as etapas.

---

# Dados de Teste

Criar massa de dados previsível.

Exemplo:

* 100 obras;
* 8 obras sem ID;
* 23 novos capítulos;
* 14 sincronizações pendentes.

Esses valores devem permanecer estáveis para facilitar comparações.

---

# Anti-patterns

São proibidos:

* testes dependentes da internet;
* testes compartilhando banco de produção;
* mocks excessivos que escondam erros reais;
* testes dependentes de ordem de execução;
* asserts genéricos.

---

# Checklist

| Item                      | Obrigatório |
| ------------------------- | ----------- |
| Testes unitários          | ✅           |
| Testes de integração      | ✅           |
| Testes E2E                | ✅           |
| Testes de acessibilidade  | ✅           |
| Testes de performance     | ✅           |
| Cobertura mínima atingida | ✅           |
| Pipeline CI validado      | ✅           |

---

# Relação com outros documentos

| Documento            | Conteúdo relacionado             |
| -------------------- | -------------------------------- |
| 03-api-dashboard.md  | Contratos validados pelos testes |
| 05-componentes.md    | Componentes cobertos             |
| 06-estados.md        | Estados obrigatórios             |
| 10-performance.md    | Benchmarks                       |
| 11-acessibilidade.md | Testes de acessibilidade         |

---

# Conclusão

A estratégia de testes do Dashboard combina validações unitárias, integração, interface, acessibilidade, desempenho e testes end-to-end para garantir alta confiabilidade do módulo. O foco principal deve permanecer no `DashboardAggregationService`, responsável por consolidar informações de diversos domínios, e na estabilidade do contrato da API, que serve como base para toda a camada de apresentação.
