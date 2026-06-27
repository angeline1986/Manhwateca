# Dashboard — Documentação Técnica

## README

---

# Objetivo

Este diretório contém toda a documentação técnica necessária para implementação, manutenção e evolução do módulo **Dashboard** da Manhwateca.

O objetivo desta documentação é permitir que qualquer desenvolvedor consiga implementar o Dashboard de forma consistente, sem depender de conhecimento implícito ou consultas constantes ao código-fonte.

Esta documentação complementa os documentos de **User Stories**, **Especificação Funcional** e **Manual do Usuário**, concentrando-se exclusivamente nos aspectos de arquitetura, engenharia de software, contratos de dados e decisões técnicas.

---

# Público-alvo

Esta documentação destina-se a:

* Desenvolvedores Back-end
* Desenvolvedores Front-end
* Arquitetos de Software
* Tech Leads
* QA Engineers
* DevOps
* Contribuidores do projeto

Não é destinada ao usuário final.

---

# Escopo

Esta documentação descreve exclusivamente o módulo **Dashboard**.

São abordados:

* arquitetura do módulo;
* contratos entre Backend e Frontend;
* fluxo de dados;
* estrutura de componentes;
* estados da interface;
* estratégias de atualização;
* tratamento de falhas;
* otimizações;
* testes;
* critérios de implementação;
* critérios de revisão de código.

Não faz parte deste documento:

* documentação do módulo Fluxos;
* documentação do Banco de Dados completo;
* documentação da API do MangaUpdates;
* documentação da API do Notion.

Esses assuntos possuem documentação própria.

---

# Organização da documentação

A documentação foi dividida em módulos independentes.

Cada documento possui um único objetivo técnico.

```text
03-documentacao-tecnica/

README.md

01-visao-geral.md
02-arquitetura.md
03-api-dashboard.md
04-modelo-de-dados.md
05-componentes.md
06-estados.md
07-navegacao.md
08-atualizacao.md
09-tratamento-de-erros.md
10-performance.md
11-acessibilidade.md
12-testes.md
13-checklist-de-implementacao.md
14-checklist-code-review.md
```

Essa organização evita documentos excessivamente longos e facilita futuras evoluções.

---

# Ordem recomendada de leitura

Embora cada documento seja autossuficiente, recomenda-se seguir a seguinte sequência.

| Ordem | Documento                  | Objetivo                                              |
| ----- | -------------------------- | ----------------------------------------------------- |
| 01    | Visão Geral                | Entender o escopo técnico do Dashboard.               |
| 02    | Arquitetura                | Conhecer a estrutura da aplicação e o fluxo de dados. |
| 03    | API Dashboard              | Entender os contratos entre Backend e Frontend.       |
| 04    | Modelo de Dados            | Conhecer tabelas, consultas e agregações.             |
| 05    | Componentes                | Estrutura técnica da interface.                       |
| 06    | Estados                    | Máquina de estados da UI.                             |
| 07    | Navegação                  | Fluxo entre módulos.                                  |
| 08    | Atualização                | Estratégia de refresh e invalidação de cache.         |
| 09    | Tratamento de Erros        | Estratégias de tolerância a falhas.                   |
| 10    | Performance                | Metas e otimizações.                                  |
| 11    | Acessibilidade             | Requisitos de UX e ARIA.                              |
| 12    | Testes                     | Estratégia de qualidade.                              |
| 13    | Checklist de Implementação | Guia para desenvolvimento.                            |
| 14    | Checklist de Code Review   | Critérios de aprovação antes do merge.                |

---

# Relação com as demais documentações

Esta documentação faz parte da documentação oficial do Dashboard.

```text
Dashboard

├── 01 User Stories
│
├── 02 Especificação Funcional
│
├── 03 Documentação Técnica
│
└── 04 Manual do Usuário
```

Cada conjunto responde a uma pergunta diferente.

| Documento               | Pergunta respondida               |
| ----------------------- | --------------------------------- |
| User Stories            | O que deve ser construído?        |
| Especificação Funcional | Como o sistema deve se comportar? |
| Documentação Técnica    | Como implementar?                 |
| Manual do Usuário       | Como utilizar?                    |

---

# Dependências entre documentos

A documentação técnica pressupõe que os seguintes documentos já tenham sido definidos:

* User Stories
* Regras de Negócio
* Especificação Funcional

As decisões técnicas descritas aqui não substituem regras de negócio.

Quando houver conflito entre uma decisão técnica e uma regra funcional, prevalece a documentação funcional.

---

# Filosofia de arquitetura

O Dashboard foi concebido como um **módulo de orquestração**, e não como um executor de operações.

Sua responsabilidade é:

* consolidar dados provenientes de diferentes serviços;
* apresentar indicadores de forma consistente;
* orientar o usuário sobre a próxima ação;
* fornecer uma visão unificada do estado da biblioteca.

Ele **não** deve executar diretamente operações de negócio, como catalogação, resolução de IDs ou sincronizações. Essas responsabilidades pertencem aos módulos especializados.

Essa separação segue o princípio da **Single Responsibility Principle (SRP)** e reduz o acoplamento entre a camada de apresentação e a lógica de negócio.

---

# Princípios arquiteturais adotados

A implementação do Dashboard deve seguir os seguintes princípios:

* Separação clara entre UI, Serviços e Persistência.
* Repositórios responsáveis exclusivamente pelo acesso aos dados.
* Serviços responsáveis pela consolidação e regras de negócio.
* Componentes de interface desacoplados das fontes de dados.
* Atualizações idempotentes.
* Falhas isoladas por integração.
* Baixo acoplamento entre módulos.
* Alta coesão interna dos componentes.

---

# Convenções utilizadas

Ao longo da documentação serão utilizados alguns padrões.

## Diagramas

Fluxos serão representados utilizando diagramas ASCII.

Exemplo:

```text
Repository
        ↓
Service
        ↓
ViewModel
        ↓
Dashboard API
        ↓
Frontend
```

---

## JSON

Todos os contratos utilizarão JSON estruturado.

Exemplo:

```json
{
  "metrics": {},
  "workflow": {},
  "integrations": {}
}
```

---

## SQL

Consultas serão apresentadas utilizando sintaxe PostgreSQL.

Sempre que possível, serão privilegiadas consultas de leitura, agregações e exemplos otimizados.

---

## Pseudocódigo

Algoritmos serão apresentados em pseudocódigo quando sua implementação não depender da linguagem utilizada.

---

# Convenções de nomenclatura

| Elemento         | Convenção           |
| ---------------- | ------------------- |
| Classes          | PascalCase          |
| Métodos          | snake_case (Python) |
| Endpoints        | kebab-case          |
| JSON             | camelCase           |
| Constantes       | UPPER_SNAKE_CASE    |
| Componentes HTML | kebab-case          |

---

# Premissas técnicas

Esta documentação assume que o projeto utiliza:

* Python como linguagem principal;
* PostgreSQL como banco de dados;
* Backend baseado em Services e Repositories;
* Frontend HTML/CSS/JavaScript;
* API REST interna para comunicação entre UI e Backend;
* Integrações com MangaUpdates e Notion.

Caso alguma dessas premissas seja alterada, a documentação deverá ser revisada.

---

# Objetivos desta documentação

Ao concluir todos os documentos desta pasta, um desenvolvedor deverá ser capaz de:

* compreender a arquitetura do Dashboard;
* implementar novos componentes;
* modificar componentes existentes;
* criar novos contratos de API;
* otimizar consultas SQL;
* tratar falhas de integração;
* implementar testes automatizados;
* revisar Pull Requests utilizando critérios padronizados.

---

# Histórico de versões

| Versão | Alteração                                               |
| ------ | ------------------------------------------------------- |
| 1.0    | Estrutura inicial da documentação técnica do Dashboard. |

---

# Próximos documentos

O próximo documento desta sequência é **01-visao-geral.md**.

Ele apresenta:

* objetivos técnicos;
* limites arquiteturais;
* responsabilidades do módulo;
* stack tecnológica;
* dependências;
* requisitos não funcionais;
* princípios de engenharia adotados pelo Dashboard.
