# Dashboard — Documentação Técnica

## 01 - Visão Geral

---

# Objetivo

Este documento define o escopo técnico do módulo **Dashboard**, suas responsabilidades arquiteturais, objetivos de engenharia, requisitos não funcionais e limites de implementação.

O Dashboard é o principal ponto de entrada da Manhwateca e possui função exclusivamente **orquestradora**. Seu objetivo é consolidar informações provenientes de múltiplos domínios da aplicação e apresentá-las de forma consistente ao usuário.

Este documento deve ser utilizado como referência antes da implementação de qualquer funcionalidade relacionada ao Dashboard.

---

# Papel do Dashboard na Arquitetura

Dentro da arquitetura da Manhwateca, o Dashboard representa a camada de apresentação consolidada.

Ele não implementa regras de negócio específicas nem executa operações sobre a biblioteca.

Sua responsabilidade consiste em:

* consultar informações produzidas por outros módulos;
* consolidar indicadores;
* apresentar o estado geral do sistema;
* orientar a navegação do usuário;
* informar o próximo passo do Workflow.

Em termos arquiteturais:

```text
                    Biblioteca
                         │
                         │
                    Repositories
                         │
                         ▼
                   Domain Services
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
 Workflow Service  Metrics Service  Integration Service
         │               │                │
         └───────────────┼────────────────┘
                         ▼
              Dashboard Aggregation Service
                         ▼
                 Dashboard ViewModel
                         ▼
                  Dashboard API
                         ▼
                   Frontend HTML
```

Todo o Dashboard deve consumir exclusivamente o **Dashboard Aggregation Service**, nunca múltiplos serviços diretamente.

---

# Objetivos de Engenharia

O Dashboard foi projetado para atender aos seguintes objetivos.

## Objetivo 1 — Centralização

Toda informação operacional relevante deve estar disponível em uma única tela.

O usuário nunca deverá navegar por diversos módulos apenas para descobrir o estado da biblioteca.

---

## Objetivo 2 — Baixo Acoplamento

O Dashboard não conhece detalhes internos de:

* PostgreSQL
* MangaUpdates
* Notion
* Biblioteca
* Workflow

Esses detalhes pertencem aos respectivos serviços.

---

## Objetivo 3 — Alta Coesão

Todos os componentes do Dashboard representam o mesmo contexto de negócio:

**Estado atual da biblioteca.**

Nenhum componente deve possuir responsabilidades externas a esse contexto.

---

## Objetivo 4 — Independência Visual

Cada componente deve ser renderizado de forma independente.

Falhas em um componente não devem impedir a renderização dos demais.

---

## Objetivo 5 — Escalabilidade

Novos cards ou painéis poderão ser adicionados futuramente sem alterar os componentes existentes.

---

# Responsabilidades

O Dashboard possui responsabilidades bem definidas.

## Deve

* Consolidar dados.
* Exibir métricas.
* Exibir pendências.
* Exibir integrações.
* Exibir progresso do Workflow.
* Exibir próxima ação.
* Navegar entre módulos.
* Atualizar informações.

---

## Não deve

* Executar catalogação.
* Resolver IDs.
* Atualizar metadados.
* Sincronizar Notion.
* Alterar registros do banco.
* Consultar APIs diretamente.
* Executar regras complexas de negócio.

Essas responsabilidades pertencem aos respectivos módulos especializados.

---

# Stack Tecnológica

## Backend

| Tecnologia         | Finalidade          |
| ------------------ | ------------------- |
| Python             | Linguagem principal |
| PostgreSQL         | Persistência        |
| psycopg            | Driver PostgreSQL   |
| dotenv             | Configuração        |
| Repository Pattern | Persistência        |
| Service Layer      | Regras de negócio   |

---

## Frontend

| Tecnologia                  | Finalidade    |
| --------------------------- | ------------- |
| HTML5                       | Estrutura     |
| CSS3                        | Estilos       |
| JavaScript ES6              | Comportamento |
| Fetch API                   | Comunicação   |
| Tailwind (quando aplicável) | Layout        |

---

## Integrações

| Serviço                   | Objetivo      |
| ------------------------- | ------------- |
| PostgreSQL                | Dados locais  |
| MangaUpdates              | Metadados     |
| Google Drive / Biblioteca | Arquivos      |
| Notion                    | Sincronização |

---

# Arquitetura Lógica

O Dashboard deve ser dividido em quatro camadas.

```text
Frontend

↓

Dashboard Controller

↓

Dashboard Aggregation Service

↓

Repositories + External Services
```

Cada camada possui responsabilidades específicas.

---

## Frontend

Responsável apenas por:

* renderização;
* eventos;
* atualização visual;
* navegação.

Não contém regras de negócio.

---

## Controller

Responsável por:

* receber requisições;
* validar parâmetros;
* chamar o Aggregation Service;
* serializar respostas.

Não realiza consultas SQL.

---

## Dashboard Aggregation Service

É o componente mais importante do módulo.

Responsabilidades:

* consultar todos os serviços necessários;
* consolidar informações;
* construir o ViewModel;
* definir a próxima ação;
* normalizar respostas.

Nenhum componente do Frontend deve consumir diretamente outros serviços.

---

## Repositories

Responsáveis exclusivamente pelo acesso aos dados.

Cada Repository possui apenas operações de persistência.

Nunca implementam regras de negócio.

---

# Dependências

O Dashboard depende dos seguintes módulos.

| Módulo        | Tipo        |
| ------------- | ----------- |
| Biblioteca    | Obrigatória |
| Workflow      | Obrigatória |
| PostgreSQL    | Obrigatória |
| Integrações   | Obrigatória |
| Configurações | Obrigatória |
| Notion        | Opcional    |
| MangaUpdates  | Opcional    |

Integrações opcionais nunca devem impedir o carregamento do Dashboard.

---

# Dependências proibidas

O Dashboard não deve depender diretamente de:

* SQL inline na camada Web;
* chamadas HTTP dentro da UI;
* lógica de negócio implementada em JavaScript;
* acesso direto ao banco.

Toda comunicação deve passar pelo Backend.

---

# Modelo de Comunicação

Toda comunicação segue o fluxo abaixo.

```text
Browser

↓

GET /dashboard

↓

Dashboard Controller

↓

Dashboard Service

↓

Repositories

↓

PostgreSQL

↓

Dashboard ViewModel

↓

JSON

↓

Frontend
```

Esse fluxo deve permanecer único e consistente.

---

# Requisitos Não Funcionais

## Tempo de resposta

Meta:

```
< 300 ms
```

para leitura do Dashboard em ambiente local.

---

## Consistência

Todos os componentes devem representar o mesmo instante lógico.

Não é permitido que:

* Métricas sejam antigas;
* Workflow seja novo.

Todas as informações devem ser geradas na mesma atualização.

---

## Disponibilidade

Falhas parciais devem degradar apenas o componente afetado.

Exemplo:

```
Notion indisponível

↓

Painel Integrações

↓

Dashboard continua funcional
```

---

## Observabilidade

Todas as falhas devem gerar logs estruturados.

Exemplo:

```json
{
  "module": "dashboard",
  "component": "integration_service",
  "severity": "warning",
  "message": "Notion unavailable"
}
```

---

# Escalabilidade

A arquitetura deve permitir adicionar novos painéis.

Exemplo:

```
Dashboard

├── Métricas
├── Workflow
├── Pendências
├── Integrações
├── Próximo Passo
└── Estatísticas de Leitura (futuro)
```

Sem necessidade de alterar os componentes existentes.

---

# Princípios de Projeto

A implementação deve seguir:

* SOLID
* DRY
* KISS
* Repository Pattern
* Service Layer
* Composition over Inheritance
* Fail Fast
* Fail Safe para integrações externas

---

# Critérios de Qualidade

O Dashboard somente será considerado pronto quando:

* todos os componentes forem independentes;
* não houver lógica de negócio na UI;
* existir apenas um Aggregation Service;
* todas as respostas forem serializadas por ViewModels;
* todas as integrações puderem falhar isoladamente;
* todos os componentes possuírem estados de Loading, Success, Empty e Error;
* o tempo médio de carregamento atender às metas estabelecidas.

---

# Relação com os demais documentos

Este documento apresenta apenas a visão arquitetural.

Os detalhes estão distribuídos da seguinte forma:

| Documento             | Conteúdo                                           |
| --------------------- | -------------------------------------------------- |
| 02-arquitetura.md     | Organização das camadas, padrões e fluxo de dados  |
| 03-api-dashboard.md   | Contratos JSON entre Backend e Frontend            |
| 04-modelo-de-dados.md | Estrutura do PostgreSQL e consultas                |
| 05-componentes.md     | Especificação técnica dos componentes da interface |
| 06-estados.md         | Máquina de estados da UI                           |
| 08-atualizacao.md     | Estratégia de atualização e invalidação de cache   |

---

# Conclusão

O Dashboard é um módulo de **orquestração e apresentação**, cuja responsabilidade é consolidar informações de diferentes domínios da aplicação em uma visão única e consistente.

Sua arquitetura privilegia baixo acoplamento, alta coesão, separação clara de responsabilidades e tolerância a falhas parciais, garantindo que o sistema permaneça utilizável mesmo diante da indisponibilidade de integrações externas.
