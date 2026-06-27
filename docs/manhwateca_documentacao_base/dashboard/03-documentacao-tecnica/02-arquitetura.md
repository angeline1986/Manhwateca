# Dashboard — Documentação Técnica

## 02 - Arquitetura

---

# Objetivo

Este documento descreve a arquitetura do módulo **Dashboard**, os padrões de projeto adotados, a separação de responsabilidades entre as camadas da aplicação e o fluxo completo de dados, desde a persistência até a renderização da interface.

O objetivo é garantir uma implementação previsível, de baixo acoplamento e alta manutenibilidade.

---

# Visão Geral da Arquitetura

O Dashboard deve atuar exclusivamente como um **módulo agregador**.

Ele não executa regras de negócio específicas de outros domínios, nem consulta diretamente APIs externas ou o banco de dados.

Toda a informação apresentada na interface deve ser produzida por um único serviço de agregação.

```text
                    ┌──────────────────────┐
                    │      Frontend        │
                    │  HTML / CSS / JS     │
                    └──────────┬───────────┘
                               │
                               ▼
                    Dashboard Controller
                               │
                               ▼
                Dashboard Aggregation Service
                               │
      ┌────────────┬───────────┼──────────────┬────────────┐
      ▼            ▼           ▼              ▼
 MetricsSvc   WorkflowSvc  PendingSvc  IntegrationSvc
      │            │           │              │
      └────────────┴───────────┼──────────────┘
                               ▼
                        Repository Layer
                               │
      ┌────────────┬───────────┼──────────────┬────────────┐
      ▼            ▼           ▼              ▼
 PostgreSQL   Biblioteca   MangaUpdates    Notion
```

---

# Arquitetura em Camadas

O Dashboard segue uma arquitetura em camadas (Layered Architecture).

## Camada de Apresentação

Responsável exclusivamente pela renderização da interface.

Responsabilidades:

* renderizar componentes;
* disparar eventos;
* consumir a API;
* atualizar a interface.

Não pode:

* executar SQL;
* implementar regras de negócio;
* chamar APIs externas.

---

## Camada de Controller

Responsável por receber requisições HTTP.

Fluxo típico:

```text
HTTP Request

↓

Validação

↓

Dashboard Service

↓

Serialização

↓

HTTP Response
```

Responsabilidades:

* validar entrada;
* chamar Services;
* retornar JSON.

---

## Camada de Serviços

É onde toda a lógica de consolidação acontece.

O Dashboard utiliza um serviço principal.

```text
DashboardAggregationService
```

Esse serviço orquestra todos os demais.

Ele nunca consulta diretamente o banco.

---

## Camada de Persistência

Implementada através de **Repositories**.

Cada Repository possui responsabilidade única.

Exemplo:

```text
MangaRepository

↓

SELECT ...

↓

Objeto Python
```

Repositories nunca:

* chamam APIs;
* conhecem HTML;
* retornam JSON.

---

# Padrões de Projeto

## Repository Pattern

Toda consulta ao PostgreSQL deve ocorrer através de Repositories.

Exemplo:

```python
class MangaRepository:

    def count_all(self):
        ...

    def count_missing_ids(self):
        ...

    def count_new_chapters(self):
        ...
```

Benefícios:

* isolamento do banco;
* facilidade para testes;
* reutilização.

---

## Service Layer

Cada domínio possui um Service especializado.

Exemplo:

```text
WorkflowService

↓

calcula etapa atual
```

O Dashboard nunca implementa essa lógica.

---

## Aggregator Pattern

O Dashboard utiliza um **Aggregator Service**.

Esse padrão evita que o Frontend consulte múltiplos endpoints.

Exemplo:

```text
Frontend

↓

GET /dashboard

↓

DashboardAggregationService

↓

20 consultas

↓

1 resposta JSON
```

---

## ViewModel Pattern

A API nunca retorna entidades do banco.

Ela retorna ViewModels.

Exemplo:

```json
{
  "metrics": {},
  "workflow": {},
  "integrations": {}
}
```

Isso desacopla completamente UI e persistência.

---

## Dependency Injection

Todos os Services devem receber seus Repositories por injeção.

Exemplo:

```python
class DashboardAggregationService:

    def __init__(
        self,
        metrics_service,
        workflow_service,
        pending_service
    ):
        ...
```

Nunca instanciar dependências dentro do Service.

---

# Fluxo de Dados

Fluxo completo de leitura.

```text
Browser

↓

GET /dashboard

↓

Dashboard Controller

↓

DashboardAggregationService

↓

WorkflowService

↓

WorkflowRepository

↓

PostgreSQL

↓

Workflow DTO

↓

Dashboard ViewModel

↓

JSON

↓

Frontend

↓

Renderização
```

Todos os componentes seguem esse fluxo.

---

# Construção do ViewModel

O Dashboard deve produzir apenas um objeto.

Exemplo:

```text
DashboardViewModel

├── metrics
├── nextAction
├── workflow
├── pendingActions
├── integrations
└── lastUpdated
```

Cada componente da UI consome apenas sua seção.

---

# Sequência de Construção

O Aggregation Service deve seguir a ordem abaixo.

```text
1.
Carregar métricas

↓

2.
Carregar Workflow

↓

3.
Carregar pendências

↓

4.
Carregar integrações

↓

5.
Calcular próxima ação

↓

6.
Montar ViewModel

↓

7.
Retornar JSON
```

Essa sequência evita dependências circulares.

---

# Responsabilidades dos Serviços

## MetricsService

Responsável por:

* contar obras;
* contar IDs;
* contar capítulos novos;
* contar sincronizações.

---

## WorkflowService

Responsável por:

* etapa atual;
* progresso;
* bloqueios.

---

## PendingService

Responsável por:

* gerar pendências;
* calcular prioridades;
* ordenar lista.

---

## IntegrationService

Responsável por:

* validar PostgreSQL;
* validar Biblioteca;
* validar MangaUpdates;
* validar Notion.

---

## DashboardAggregationService

Responsável por:

* orquestrar todos os serviços;
* construir ViewModel;
* calcular próxima ação.

Não deve conter SQL.

---

# Dependências Permitidas

```text
Controller

↓

Aggregation Service

↓

Domain Services

↓

Repositories

↓

PostgreSQL
```

---

# Dependências Proibidas

Nunca permitir:

```text
Frontend

↓

SQL
```

Nem:

```text
Controller

↓

SELECT
```

Nem:

```text
JavaScript

↓

Business Rules
```

---

# Estratégia para Falhas

Cada serviço deve falhar isoladamente.

Exemplo:

```text
Notion indisponível

↓

IntegrationService

↓

status = ERROR

↓

Dashboard continua funcionando
```

Não interromper toda a construção do ViewModel.

---

# Ordem de Inicialização

```text
Repositories

↓

Services

↓

Aggregation Service

↓

Controller

↓

Frontend
```

Nunca inverter essa ordem.

---

# Escalabilidade

Novos componentes devem exigir apenas:

1. novo Service (quando necessário);
2. novo DTO;
3. novo trecho do ViewModel;
4. novo componente Frontend.

Nenhum componente existente deve precisar ser alterado.

---

# Diagrama de Dependências

```text
Dashboard Controller
        │
        ▼
DashboardAggregationService
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
Metrics Workflow Integration
 │        │              │
 ▼        ▼              ▼
Repositories
        │
        ▼
PostgreSQL
```

---

# Regras Arquiteturais

A implementação deve obedecer obrigatoriamente às seguintes regras:

* Controllers nunca executam SQL.
* Repositories nunca retornam JSON.
* Services nunca conhecem HTML.
* Frontend nunca implementa regras de negócio.
* O Dashboard possui apenas um ponto de agregação de dados.
* Toda resposta da API deve ser produzida a partir de um ViewModel.
* Cada camada conhece apenas a camada imediatamente inferior.

Essas restrições garantem baixo acoplamento, alta coesão e facilitam testes, evolução e manutenção do módulo.
