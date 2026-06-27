# Dashboard — Especificação Funcional

## 01 - Visão Geral

---

# Objetivo do Documento

Este documento define a visão funcional do módulo **Dashboard** da Manhwateca.

Seu propósito é especificar o comportamento esperado da tela, seus limites de responsabilidade e sua interação com os demais módulos da aplicação.

Esta documentação complementa as User Stories do Dashboard, descrevendo **como a interface deve funcionar**, e não apenas **o que ela deve entregar**.

O documento deve servir como referência oficial para:

* desenvolvimento Front-end;
* desenvolvimento Back-end;
* arquitetura da aplicação;
* testes funcionais;
* evolução futura da interface.

---

# Objetivo do Dashboard

O Dashboard é a página inicial da Manhwateca.

Sua principal responsabilidade é fornecer uma visão consolidada do estado da biblioteca e orientar o usuário sobre qual ação deve ser executada em seguida.

Ao acessar a aplicação, o usuário deve conseguir responder rapidamente às seguintes perguntas:

* A biblioteca está saudável?
* Existe alguma pendência importante?
* Em qual etapa do workflow estou?
* Posso continuar trabalhando?
* Qual é a próxima ação recomendada?

O Dashboard não substitui os demais módulos da aplicação.

Seu papel é atuar como um **centro de comando**, concentrando informações estratégicas e direcionando o usuário para a funcionalidade adequada.

---

# Papel dentro da Arquitetura

A Manhwateca é organizada em quatro módulos principais.

| Módulo        | Responsabilidade                    |
| ------------- | ----------------------------------- |
| Dashboard     | Informar e orientar                 |
| Biblioteca    | Consultar e editar obras            |
| Fluxos        | Executar processos operacionais     |
| Configurações | Administrar o ambiente da aplicação |

O Dashboard representa o ponto inicial de utilização da aplicação.

Toda navegação operacional deve partir dele.

---

# Responsabilidades

O Dashboard é responsável por:

* consolidar informações provenientes de diferentes módulos;
* apresentar indicadores resumidos;
* identificar pendências relevantes;
* recomendar a próxima ação do usuário;
* resumir o estado do Workflow;
* apresentar o estado das integrações;
* fornecer atalhos para os módulos especializados;
* permitir atualização manual das informações.

---

# Fora do Escopo

O Dashboard **não deve**:

* organizar arquivos;
* catalogar biblioteca;
* consultar MangaUpdates;
* resolver IDs;
* atualizar metadados;
* sincronizar Notion;
* editar obras;
* alterar configurações;
* executar processos demorados.

Essas responsabilidades pertencem aos módulos especializados.

---

# Princípios Funcionais

Toda implementação do Dashboard deve respeitar os seguintes princípios.

## Orientação

O Dashboard deve orientar o usuário.

Nunca deve exigir que ele descubra sozinho qual etapa executar.

---

## Simplicidade

A interface deve apresentar apenas informações necessárias para tomada de decisão.

Informações técnicas detalhadas pertencem aos módulos especializados.

---

## Consistência

Todos os componentes devem utilizar a mesma linguagem visual e os mesmos conceitos utilizados em toda a aplicação.

Exemplos:

* Pendência
* Próximo Passo
* Workflow
* Biblioteca
* Integrações

Não utilizar sinônimos diferentes para representar o mesmo conceito.

---

## Não duplicação

O Dashboard não deve reproduzir funcionalidades completas existentes em Biblioteca, Fluxos ou Configurações.

Sempre que uma interação exigir maior profundidade, a navegação deve ser encaminhada ao módulo responsável.

---

# Relação com as User Stories

Esta especificação funcional implementa as seguintes User Stories.

| User Story | Tema                       |
| ---------- | -------------------------- |
| US-001     | Estado geral da biblioteca |
| US-002     | Próximo passo recomendado  |
| US-003     | Métricas operacionais      |
| US-004     | Pendências críticas        |
| US-005     | Ações rápidas              |
| US-006     | Resumo do Workflow         |
| US-007     | Estado das integrações     |
| US-008     | Atualização do Dashboard   |
| US-009     | Navegação entre módulos    |

As regras de negócio permanecem documentadas nas respectivas User Stories.

Este documento descreve exclusivamente o comportamento funcional da interface.

---

# Componentes da Página

O Dashboard é composto pelos seguintes componentes.

| Ordem | Componente                |
| ----- | ------------------------- |
| 1     | Cabeçalho                 |
| 2     | Próximo Passo Recomendado |
| 3     | Cards de Métricas         |
| 4     | Painel de Pendências      |
| 5     | Estado das Integrações    |
| 6     | Resumo do Workflow        |
| 7     | Ações Rápidas             |

Cada componente possui documentação própria nesta pasta.

---

# Fluxo de Dados

O Dashboard não deve consultar diretamente diferentes serviços.

Toda informação exibida deve ser obtida através de uma API agregadora.

```text
Dashboard
        │
        ▼
GET /api/dashboard
        │
        ▼
Backend
        │
 ├── PostgreSQL
 ├── Workflow
 ├── Biblioteca
 ├── MangaUpdates
 └── Notion
```

Essa arquitetura reduz o número de chamadas HTTP e garante consistência entre os componentes da interface.

---

# Estados Globais

A página deve considerar os seguintes estados.

| Estado     | Descrição                                                        |
| ---------- | ---------------------------------------------------------------- |
| Loading    | Informações estão sendo carregadas                               |
| Ready      | Dashboard carregado normalmente                                  |
| Partial    | Parte das informações está indisponível                          |
| Refreshing | Atualização manual em andamento                                  |
| Empty      | Não existem dados suficientes para exibição                      |
| Error      | Não foi possível carregar o Dashboard                            |
| Blocked    | Existe um bloqueio crítico que impede a continuidade do workflow |

Todos os componentes devem responder adequadamente a esses estados.

---

# Navegação

O Dashboard é responsável apenas por iniciar navegações.

Os destinos permitidos são:

* Biblioteca
* Fluxos
* Configurações

Nenhum componente do Dashboard deve abrir páginas internas diretamente.

Sempre que possível, a navegação deve preservar contexto.

Exemplo:

```text
Dashboard
      ↓
Fluxos
      ↓
Etapa Resolver IDs
```

---

# Fonte de Verdade

Cada informação apresentada deve possuir uma única origem.

| Informação    | Fonte                         |
| ------------- | ----------------------------- |
| Workflow      | Módulo Fluxos                 |
| Obras         | PostgreSQL                    |
| Integrações   | Backend                       |
| Pendências    | Workflow                      |
| Próximo Passo | Motor de decisão do Dashboard |

O Dashboard não deve recalcular informações que já foram produzidas por outros módulos.

---

# Critérios Gerais de Qualidade

A implementação desta tela deve atender aos seguintes critérios.

* O carregamento deve ser rápido.
* A interface deve permanecer utilizável mesmo diante de falhas parciais.
* Os componentes devem ser independentes entre si.
* A ausência de uma informação não deve impedir a renderização das demais.
* A navegação deve ser intuitiva.
* O Dashboard deve permanecer livre de funcionalidades operacionais.
* A linguagem utilizada deve ser compreensível por usuários não técnicos.

---

# Relação entre os Documentos

Esta pasta organiza a especificação funcional por componente.

Cada documento descreve detalhadamente um aspecto da interface.

| Documento                  | Conteúdo                     |
| -------------------------- | ---------------------------- |
| 01-visao-geral.md          | Visão funcional do Dashboard |
| 02-layout-geral.md         | Estrutura visual da página   |
| 03-cabecalho.md            | Cabeçalho superior           |
| 04-proximo-passo.md        | Card principal do Dashboard  |
| 05-metricas.md             | Cards de indicadores         |
| 06-pendencias.md           | Painel de pendências         |
| 07-workflow.md             | Resumo do Workflow           |
| 08-integracoes.md          | Estado das integrações       |
| 09-acoes-rapidas.md        | Área de atalhos              |
| 10-atualizacao.md          | Atualização manual           |
| 11-navegacao.md            | Regras de navegação          |
| 12-estados-da-interface.md | Estados visuais da página    |
| 13-mensagens.md            | Catálogo de mensagens        |

---

# Critérios de Aceite

Esta documentação será considerada atendida quando:

* definir claramente o papel do Dashboard;
* estabelecer seus limites de responsabilidade;
* identificar todos os componentes principais da página;
* explicar a relação entre Dashboard e os demais módulos;
* documentar a origem dos dados exibidos;
* servir como base para implementação da interface sem necessidade de interpretações adicionais.
