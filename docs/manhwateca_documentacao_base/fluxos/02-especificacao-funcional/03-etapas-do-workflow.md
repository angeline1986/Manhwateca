# Etapas do Workflow

> Documento: **03-etapas-do-workflow.md**

---

# Objetivo

Este documento especifica o comportamento funcional das cinco etapas que compõem o Workflow operacional da Manhwateca.

Cada etapa possui um objetivo específico, critérios para início e conclusão, dependências, estados de execução e resultados esperados. Em conjunto, elas formam um fluxo contínuo que transforma uma biblioteca local em um catálogo atualizado e sincronizado.

---

# Visão Geral do Workflow

O Workflow é composto pelas seguintes etapas:

```text
① Organizar Biblioteca
        │
        ▼
② Catalogar Obras
        │
        ▼
③ Resolver IDs
        │
        ▼
④ Atualizar Metadados
        │
        ▼
⑤ Sincronizar Notion
```

O usuário pode executar o Workflow completo ou iniciar uma etapa específica quando permitido pelas regras de negócio.

---

# Ordem de Execução

A sequência lógica do Workflow é fixa.

| Ordem | Etapa                | Dependência              |
| ----: | -------------------- | ------------------------ |
|     1 | Organizar Biblioteca | Nenhuma                  |
|     2 | Catalogar Obras      | Organização              |
|     3 | Resolver IDs         | Catalogação              |
|     4 | Atualizar Metadados  | Resolução de IDs         |
|     5 | Sincronizar Notion   | Atualização de Metadados |

A interface nunca deve permitir reordenar essas etapas.

---

# Etapa 1 — Organizar Biblioteca

## Finalidade

Preparar a biblioteca para processamento.

## Ações executadas

* localizar diretórios;
* validar estrutura;
* identificar novas obras;
* atualizar índice interno;
* registrar inconsistências.

## Critérios para início

* biblioteca configurada;
* diretório acessível.

## Critérios para conclusão

* varredura finalizada;
* índice atualizado;
* inconsistências registradas.

## Próxima etapa

Catalogar Obras.

---

# Etapa 2 — Catalogar Obras

## Finalidade

Transformar diretórios válidos em registros persistidos no banco de dados.

## Ações executadas

* criar novos registros;
* atualizar registros existentes;
* validar dados mínimos;
* identificar duplicidades.

## Critérios para início

* organização concluída.

## Critérios para conclusão

* todas as obras catalogadas;
* registros atualizados;
* pendências identificadas.

## Próxima etapa

Resolver IDs.

---

# Etapa 3 — Resolver IDs

## Finalidade

Associar cada obra ao seu identificador oficial no MangaUpdates.

## Ações executadas

* pesquisar candidatos;
* validar correspondências;
* confirmar associações;
* registrar obras não localizadas.

## Critérios para início

* obra catalogada.

## Critérios para conclusão

* todos os IDs possíveis resolvidos;
* pendências registradas.

## Próxima etapa

Atualizar Metadados.

---

# Etapa 4 — Atualizar Metadados

## Finalidade

Atualizar automaticamente as informações oficiais das obras.

## Ações executadas

* consultar MangaUpdates;
* atualizar títulos;
* atualizar autores;
* atualizar gêneros;
* atualizar status;
* atualizar capítulos;
* registrar data da sincronização.

## Critérios para início

* obra com `mangaupdates_id`.

## Critérios para conclusão

* metadados atualizados;
* histórico registrado.

## Próxima etapa

Sincronizar Notion.

---

# Etapa 5 — Sincronizar Notion

## Finalidade

Refletir no Notion todas as alterações realizadas durante o Workflow.

## Ações executadas

* criar páginas;
* atualizar páginas existentes;
* sincronizar propriedades;
* registrar falhas;
* consolidar resultados.

## Critérios para início

* metadados atualizados.

## Critérios para conclusão

* sincronização encerrada;
* resumo disponível.

---

# Fluxo de Transição

Ao concluir uma etapa, o sistema deve executar automaticamente a transição para a próxima.

```text
Concluída

↓

Persistir resultados

↓

Atualizar progresso

↓

Atualizar interface

↓

Iniciar próxima etapa
```

Não deve existir intervenção manual entre etapas durante a execução automática.

---

# Execução Individual

A interface deve permitir a execução isolada de determinadas etapas.

Exemplos:

* executar novamente a Resolução de IDs;
* atualizar apenas os Metadados;
* sincronizar novamente o Notion.

Ao iniciar uma etapa individual, o sistema deverá validar todas as dependências antes da execução.

---

# Estados das Etapas

Cada etapa pode assumir um dos seguintes estados:

| Estado                | Descrição                        |
| --------------------- | -------------------------------- |
| Aguardando            | Ainda não iniciada               |
| Em execução           | Processamento ativo              |
| Concluída             | Finalizada com sucesso           |
| Concluída com alertas | Finalizada, porém com pendências |
| Falhou                | Interrompida por erro            |
| Cancelada             | Interrompida pelo usuário        |

Os estados devem ser representados de forma consistente em toda a interface.

---

# Progresso

Cada etapa deve possuir progresso próprio.

Informações mínimas:

* percentual;
* quantidade processada;
* total esperado;
* tempo decorrido.

Exemplo:

```text
Resolver IDs

██████████░░░░░░

68%

341 de 503 obras
```

---

# Dependências Funcionais

Antes de iniciar qualquer etapa, o sistema deve validar:

| Validação               | Obrigatória  |
| ----------------------- | ------------ |
| PostgreSQL disponível   | Sim          |
| Biblioteca acessível    | Etapa 1      |
| MangaUpdates disponível | Etapas 3 e 4 |
| Notion disponível       | Etapa 5      |

Caso alguma dependência esteja indisponível, apenas a etapa correspondente deve ser afetada.

---

# Interrupção do Workflow

O usuário pode cancelar a execução.

Ao cancelar:

* finalizar a operação corrente de forma segura;
* persistir resultados já produzidos;
* registrar histórico parcial;
* atualizar o estado da interface.

Operações já concluídas não devem ser revertidas.

---

# Finalização

Ao término da última etapa, o sistema deve:

* consolidar estatísticas;
* atualizar Dashboard;
* atualizar histórico;
* atualizar indicadores;
* liberar recursos temporários;
* apresentar resumo da execução.

---

# Relação com outros documentos

| Documento                        | Conteúdo relacionado                |
| -------------------------------- | ----------------------------------- |
| 02-interface-e-layout.md         | Organização visual do Workflow      |
| 04-processamento-e-validacoes.md | Regras de execução e validações     |
| 05-integracoes.md                | Dependências externas               |
| 06-estados-e-mensagens.md        | Estados visuais e mensagens         |
| 07-regras-de-navegacao.md        | Navegação durante e após o Workflow |

---

# Conclusão

As cinco etapas do Workflow constituem o processo operacional central da Manhwateca. Cada uma possui responsabilidades, dependências e critérios de conclusão bem definidos, permitindo que o sistema execute o processamento da biblioteca de forma incremental, previsível e rastreável. A transição automática entre etapas, aliada à possibilidade de reprocessamentos individuais, garante flexibilidade sem comprometer a consistência dos dados.
