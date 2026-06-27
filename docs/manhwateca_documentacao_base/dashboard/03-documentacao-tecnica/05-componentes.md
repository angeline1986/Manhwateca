# Dashboard — Documentação Técnica

## 05 - Componentes

---

# Objetivo

Este documento especifica tecnicamente todos os componentes que compõem a interface do Dashboard.

Para cada componente são definidos:

* responsabilidade;
* origem dos dados;
* contrato esperado;
* propriedades (Props);
* estados suportados;
* eventos;
* comportamento esperado;
* dependências.

Este documento serve como referência para implementação Front-end e integração com o `DashboardViewModel`.

---

# Hierarquia da Interface

O Dashboard é composto pelos seguintes componentes.

```text
DashboardPage
│
├── Header
│
├── NextActionCard
│
├── MetricsGrid
│   ├── MetricCard
│   ├── MetricCard
│   ├── MetricCard
│   └── MetricCard
│
├── PendingActionsPanel
│
├── IntegrationsPanel
│
├── WorkflowPanel
│
└── QuickActionsPanel
```

Todos os componentes são independentes.

---

# DashboardPage

## Responsabilidade

Container principal da página.

Responsável por:

* solicitar o DashboardViewModel;
* distribuir dados aos componentes filhos;
* controlar atualização global;
* controlar estados globais da página.

---

## Props

| Nome      | Tipo               |
| --------- | ------------------ |
| dashboard | DashboardViewModel |

---

## Eventos

| Evento    | Ação                |
| --------- | ------------------- |
| onLoad    | Buscar Dashboard    |
| onRefresh | Atualizar Dashboard |

---

## Dependências

```text
DashboardController

↓

DashboardViewModel
```

---

# Header

## Responsabilidade

Exibir informações gerais da página.

Contém:

* título;
* subtítulo;
* última atualização;
* botão Recarregar.

---

## Props

| Nome        | Tipo     |
| ----------- | -------- |
| title       | string   |
| subtitle    | string   |
| lastUpdated | datetime |

---

## Eventos

| Evento           | Resultado           |
| ---------------- | ------------------- |
| Click Recarregar | Atualizar Dashboard |

---

## Estados

* loading
* success
* error

---

# NextActionCard

## Responsabilidade

Apresentar a ação prioritária definida pelo sistema.

É o principal componente do Dashboard.

---

## Props

| Campo       | Tipo   |
| ----------- | ------ |
| title       | string |
| description | string |
| priority    | string |
| action      | string |
| buttonLabel | string |

---

## Exemplo

```json
{
  "title": "Resolver IDs",
  "description": "Existem 8 obras sem identificação.",
  "priority": "high",
  "action": "/fluxos#resolver-ids"
}
```

---

## Estados

* loading
* success
* empty
* error

---

## Eventos

| Evento      | Resultado |
| ----------- | --------- |
| Click botão | Navegação |

---

# MetricsGrid

## Responsabilidade

Agrupar os quatro indicadores do Dashboard.

Não contém lógica.

Distribui dados para quatro MetricCards.

---

## Props

```text
metrics
```

---

## Componentes Filhos

* LibraryMetricCard
* ChaptersMetricCard
* MissingIdsMetricCard
* PendingSyncMetricCard

---

# MetricCard

## Responsabilidade

Renderizar um único indicador.

---

## Props

| Nome  | Tipo    |
| ----- | ------- |
| title | string  |
| value | integer |
| icon  | string  |
| color | string  |

---

## Exemplo

```json
{
    "title":"Novos capítulos",
    "value":23,
    "icon":"book",
    "color":"green"
}
```

---

## Estados

* loading
* success
* empty

Nunca possui estado de erro individual.

---

# PendingActionsPanel

## Responsabilidade

Exibir pendências ordenadas.

---

## Props

```text
pendingActions[]
```

---

## Estrutura

Cada item possui:

```json
{
    "title":"",
    "description":"",
    "severity":"",
    "action":""
}
```

---

## Ordenação

Sempre realizada pelo Backend.

Jamais ordenar no Frontend.

---

## Eventos

| Evento      | Resultado |
| ----------- | --------- |
| Click item  | Navegação |
| Click botão | Navegação |

---

## Estados

* loading
* success
* empty
* error

---

# IntegrationStatusItem

Representa uma única integração.

---

## Props

| Campo   | Tipo   |
| ------- | ------ |
| label   | string |
| status  | string |
| message | string |

---

## Status

```text
healthy

warning

error

unknown
```

---

# IntegrationsPanel

## Responsabilidade

Agrupar todas as integrações.

---

## Props

```text
integrations[]
```

---

## Estados

* loading
* success
* error

---

# WorkflowPanel

## Responsabilidade

Exibir o progresso do Workflow.

---

## Props

```json
{
    "progress":60,
    "steps":[]
}
```

---

## WorkflowStep

Cada etapa possui:

```json
{
    "id":"resolve_ids",
    "status":"running"
}
```

---

## Estados possíveis

* pending

* running

* completed

* blocked

* error

---

# QuickActionsPanel

## Responsabilidade

Renderizar atalhos de navegação.

---

## Props

```text
quickActions[]
```

---

## Estrutura

```json
{
    "label":"Biblioteca",
    "route":"/biblioteca"
}
```

---

## Eventos

| Evento | Resultado |
| ------ | --------- |
| Click  | Navegação |

---

# Responsabilidade do Frontend

O Frontend nunca deve:

* calcular métricas;
* ordenar listas;
* decidir prioridades;
* montar Workflow;
* validar integrações.

Sua responsabilidade é apenas renderizar.

---

# Responsabilidade do Backend

O Backend deve entregar todos os componentes prontos para renderização.

Exemplo:

```text
DashboardAggregationService

↓

DashboardViewModel

↓

Frontend
```

Nunca delegar lógica para JavaScript.

---

# Comunicação entre Componentes

A comunicação ocorre exclusivamente através do `DashboardPage`.

```text
DashboardPage

├── Header

├── NextAction

├── Metrics

├── PendingActions

├── Workflow

├── Integrations

└── QuickActions
```

Componentes irmãos nunca compartilham estado diretamente.

---

# Estados Compartilhados

Apenas o DashboardPage mantém estado global.

```text
DashboardState

↓

DashboardViewModel
```

Todos os demais componentes recebem dados por propriedades.

---

# Regras de Renderização

* Componentes devem ser renderizados independentemente.
* Erro em um painel não deve impedir os demais.
* Nenhum componente deve executar requisições HTTP próprias.
* Nenhum componente deve acessar diretamente o banco.
* Todos os componentes devem ser determinísticos: mesmas Props → mesma renderização.

---

# Extensibilidade

Novos componentes devem seguir o mesmo padrão:

```text
ViewModel

↓

Props

↓

Renderização
```

Sem alterar componentes existentes.

---

# Checklist de Componentes

| Componente          | Loading | Empty | Error | Eventos   |
| ------------------- | ------- | ----- | ----- | --------- |
| Header              | ✅       | —     | ✅     | Refresh   |
| NextActionCard      | ✅       | ✅     | ✅     | Navegação |
| MetricsGrid         | ✅       | —     | —     | —         |
| PendingActionsPanel | ✅       | ✅     | ✅     | Navegação |
| IntegrationsPanel   | ✅       | —     | ✅     | —         |
| WorkflowPanel       | ✅       | —     | ✅     | —         |
| QuickActionsPanel   | ✅       | —     | —     | Navegação |

---

# Relação com outros documentos

| Documento            | Conteúdo relacionado                              |
| -------------------- | ------------------------------------------------- |
| 03-api-dashboard.md  | Origem das Props e contratos JSON                 |
| 06-estados.md        | Máquina de estados dos componentes                |
| 07-navegacao.md      | Fluxo de navegação acionado pelos eventos         |
| 11-acessibilidade.md | Requisitos de acessibilidade para cada componente |

---

# Conclusão

A interface do Dashboard é composta por componentes independentes, orientados por propriedades derivadas do `DashboardViewModel`. Cada componente possui responsabilidade única, estados bem definidos e comportamento determinístico, permitindo evolução incremental, testes isolados e baixo acoplamento entre apresentação e lógica de negócio.
