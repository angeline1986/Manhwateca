# Dashboard — Especificação Funcional

## 04 - Próximo Passo Recomendado

---

# Objetivo do Documento

Este documento especifica funcionalmente o componente **Próximo Passo Recomendado**, responsável por orientar o usuário sobre qual atividade deve ser executada em seguida.

O componente representa o elemento de maior destaque do Dashboard e atua como principal mecanismo de orientação da Manhwateca.

Sua implementação está relacionada à **US-002 — Receber a próxima ação recomendada**.

---

# Objetivo do Componente

O componente deve reduzir a necessidade de decisão do usuário.

Ao abrir a aplicação, o usuário não deve precisar analisar todas as métricas para descobrir qual atividade executar.

O sistema deve determinar automaticamente a ação prioritária e apresentá-la de forma clara.

---

# Responsabilidades

O componente é responsável por:

* identificar a próxima etapa do Workflow;
* apresentar o motivo da recomendação;
* explicar o impacto da ação;
* direcionar o usuário para a página Fluxos;
* atualizar automaticamente quando o Dashboard for atualizado.

---

# Fora do Escopo

Este componente não deve:

* executar nenhuma etapa do Workflow;
* iniciar sincronizações;
* alterar dados;
* recalcular o Workflow localmente;
* permitir editar recomendações.

Toda a lógica pertence ao backend.

---

# User Story Relacionada

| ID     | Título                             |
| ------ | ---------------------------------- |
| US-002 | Receber a próxima ação recomendada |

---

# Estrutura Visual

O componente é composto pelos seguintes elementos.

```text
┌──────────────────────────────────────────────┐
│ PRÓXIMO PASSO RECOMENDADO                    │
│                                              │
│ Resolver 8 obras sem ID                      │
│                                              │
│ Existem obras catalogadas que ainda precisam │
│ de identificação no MangaUpdates.            │
│                                              │
│ [Continuar fluxo]   [Ver pendências]         │
└──────────────────────────────────────────────┘
```

---

# Componentes Internos

## Badge

Exibe a categoria da informação.

Valor padrão:

```text
Próximo Passo Recomendado
```

---

## Título

Representa a ação recomendada.

Exemplos:

* Resolver 8 obras sem ID
* Atualizar metadados
* Sincronizar Notion
* Organizar biblioteca

O título deve utilizar verbo no infinitivo.

---

## Descrição

Explica por que aquela ação foi escolhida.

A descrição deve:

* possuir linguagem simples;
* evitar termos técnicos;
* informar o impacto da ação.

Exemplo:

```text
Existem obras catalogadas que ainda não possuem
identificação confirmada.
```

---

## Botão Principal

Texto padrão:

```text
Continuar fluxo
```

Responsabilidade:

Abrir a página **Fluxos** diretamente na etapa recomendada.

---

## Botão Secundário

Texto padrão:

```text
Ver pendências
```

Responsabilidade:

Abrir o painel correspondente dentro da página Fluxos.

---

# Fonte de Dados

O componente deve consumir apenas informações provenientes do endpoint:

```http
GET /api/dashboard
```

Estrutura esperada:

```json
recommended_next_step
{
  "title": "...",
  "description": "...",
  "step_id": "...",
  "step_label": "...",
  "primary_action": {},
  "secondary_action": {}
}
```

O componente nunca deve montar essas informações localmente.

---

# Regras Funcionais

## RF-001

O Dashboard deve apresentar apenas **uma recomendação principal**.

---

## RF-002

A recomendação deve respeitar a ordem oficial do Workflow.

---

## RF-003

Uma etapa bloqueada nunca pode ser recomendada.

---

## RF-004

Caso exista uma falha crítica de ambiente, ela possui prioridade sobre qualquer etapa operacional.

---

## RF-005

Caso exista uma tarefa em execução, nenhuma nova recomendação deve ser apresentada.

---

## RF-006

Toda recomendação deve possuir uma justificativa.

---

## RF-007

Toda recomendação deve possuir um destino de navegação.

---

## RF-008

O componente não deve desaparecer quando não houver recomendações.

Nesse cenário deve apresentar um estado específico.

---

# Matriz de Priorização

| Condição                   | Recomendação          |
| -------------------------- | --------------------- |
| Biblioteca não configurada | Configurar biblioteca |
| Organização pendente       | Organizar biblioteca  |
| Catálogo desatualizado     | Catalogar arquivos    |
| Obras sem ID               | Resolver IDs          |
| Metadados pendentes        | Atualizar metadados   |
| Sincronização pendente     | Sincronizar Notion    |
| Workflow concluído         | Nenhuma ação pendente |
| Ambiente indisponível      | Corrigir ambiente     |

---

# Estados do Componente

## Loading

Enquanto o Dashboard estiver carregando.

Elementos:

* skeleton do título;
* skeleton da descrição;
* skeleton dos botões.

---

## Ready

Estado padrão.

Exibe normalmente a recomendação.

---

## Empty

Quando não existir nenhuma atividade pendente.

Exemplo:

```text
Nenhuma ação pendente.

Sua biblioteca está totalmente atualizada.
```

O botão principal deve ser ocultado.

---

## Refreshing

Durante a atualização manual do Dashboard.

O componente permanece visível utilizando os dados anteriores até o término da atualização.

---

## Error

Caso o backend não consiga calcular a recomendação.

Mensagem sugerida:

```text
Não foi possível determinar a próxima ação.
```

O usuário ainda poderá utilizar os demais componentes da página.

---

## Blocked

Existe uma falha crítica de infraestrutura.

Exemplo:

```text
Banco de dados indisponível.

Corrija o ambiente antes de continuar.
```

O botão principal deve abrir **Configurações**.

---

# Navegação

| Ação            | Destino                       |
| --------------- | ----------------------------- |
| Continuar fluxo | Fluxos → etapa recomendada    |
| Ver pendências  | Fluxos → painel de pendências |

A navegação deve preservar o contexto da recomendação.

---

# Mensagens

## MSG-DASH-001

```text
Resolver 8 obras sem ID.
```

---

## MSG-DASH-002

```text
Atualizar metadados das obras.
```

---

## MSG-DASH-003

```text
Sincronizar alterações com o Notion.
```

---

## MSG-DASH-004

```text
Nenhuma ação pendente.
```

---

## MSG-DASH-005

```text
Não foi possível determinar a próxima ação.
```

---

# Casos de Erro

| Situação             | Comportamento Esperado                        |
| -------------------- | --------------------------------------------- |
| API indisponível     | Exibir estado Error                           |
| Workflow inexistente | Exibir estado Empty                           |
| Ambiente bloqueado   | Exibir estado Blocked                         |
| Dados incompletos    | Exibir mensagem genérica sem quebrar o layout |

---

# Critérios de Aceite

* Deve existir apenas um componente "Próximo Passo Recomendado".
* Toda recomendação deve possuir título, descrição e ação.
* A recomendação deve ser obtida exclusivamente pelo backend.
* O componente nunca deve executar tarefas automaticamente.
* O botão principal deve abrir a etapa correspondente na página Fluxos.
* O componente deve suportar os estados Loading, Ready, Empty, Refreshing, Error e Blocked.
* O layout deve permanecer estável independentemente do conteúdo exibido.

---

# Dependências

Este componente depende diretamente de:

* Workflow;
* API agregadora do Dashboard;
* Sistema de navegação;
* Módulo Fluxos.

Não possui dependência direta da Biblioteca ou do Notion, consumindo apenas os dados consolidados fornecidos pelo backend.
