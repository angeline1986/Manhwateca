# Dashboard — Especificação Funcional

## 07 - Resumo do Workflow

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do componente **Resumo do Workflow**, responsável por apresentar ao usuário uma visão simplificada do progresso do fluxo operacional da Manhwateca.

O componente permite identificar rapidamente quais etapas já foram concluídas, qual etapa está em andamento e quais atividades ainda permanecem pendentes.

Esta documentação implementa a **US-006 — Acompanhar o progresso do Workflow**.

---

# Objetivo do Componente

O Resumo do Workflow deve:

* apresentar o estado atual do processo operacional;
* permitir que o usuário compreenda rapidamente em qual etapa se encontra;
* reforçar a sequência oficial do Workflow;
* servir como apoio visual ao componente **Próximo Passo Recomendado**.

O componente possui finalidade exclusivamente informativa.

---

# User Story Relacionada

| ID     | Título                             |
| ------ | ---------------------------------- |
| US-006 | Acompanhar o progresso do Workflow |

---

# Workflow Oficial

O Workflow da Manhwateca é composto por cinco etapas fixas.

| Ordem | Etapa                |
| ----- | -------------------- |
| 1     | Organizar Biblioteca |
| 2     | Catalogar Arquivos   |
| 3     | Resolver IDs         |
| 4     | Atualizar Metadados  |
| 5     | Sincronizar Notion   |

A ordem é obrigatória e não pode ser alterada pela interface.

---

# Estrutura Visual

```text
┌──────────────────────────────────────────┐
│ Workflow                                 │
│                                          │
│ ✔ Organizar Biblioteca                   │
│ ✔ Catalogar Arquivos                     │
│ ► Resolver IDs                           │
│ ○ Atualizar Metadados                    │
│ ○ Sincronizar Notion                     │
└──────────────────────────────────────────┘
```

Cada etapa representa apenas o estado geral do processo.

O componente não exibe detalhes internos das tarefas.

---

# Estrutura da Etapa

Cada etapa deve apresentar:

* número da etapa;
* nome;
* estado atual;
* indicador visual.

Opcionalmente poderá apresentar uma descrição curta.

---

# Estados das Etapas

Cada etapa pode assumir apenas um dos seguintes estados.

| Estado       | Descrição                                    |
| ------------ | -------------------------------------------- |
| Não iniciada | Ainda não foi executada                      |
| Atual        | Próxima etapa a ser executada                |
| Em execução  | Processo atualmente em andamento             |
| Concluída    | Etapa finalizada com sucesso                 |
| Erro         | Última execução terminou com falha           |
| Bloqueada    | Não pode ser executada devido a dependências |

Esses estados são mutuamente exclusivos.

---

# Fonte de Dados

O componente deve consumir exclusivamente:

```http
GET /api/dashboard
```

Estrutura esperada:

```json
{
  "workflow": {
    "current_step": "resolve_ids",
    "steps": [
      {
        "id": "organize_library",
        "number": 1,
        "title": "Organizar Biblioteca",
        "status": "done"
      }
    ]
  }
}
```

O Dashboard não deve calcular o progresso do Workflow.

---

# Regras Funcionais

## RF-001

A sequência oficial do Workflow é fixa.

---

## RF-002

Somente uma etapa pode possuir o estado **Atual**.

---

## RF-003

Etapas concluídas permanecem visíveis.

---

## RF-004

Uma etapa bloqueada impede a execução das etapas seguintes.

---

## RF-005

O componente não permite alterar o estado das etapas.

---

## RF-006

Toda informação exibida deve refletir exatamente o estado informado pelo módulo Fluxos.

---

## RF-007

O componente não substitui a página Fluxos.

Ele apresenta apenas um resumo visual.

---

## RF-008

Ao selecionar uma etapa (quando essa interação existir), o Dashboard deve navegar para a etapa correspondente no módulo Fluxos.

---

# Estados do Componente

## Loading

O componente apresenta skeleton para todas as etapas.

---

## Ready

As etapas são exibidas normalmente.

---

## Empty

Quando o Workflow ainda não foi iniciado.

Exemplo:

```text
Workflow não iniciado.

A primeira etapa será "Organizar Biblioteca".
```

---

## Error

Caso não seja possível obter o estado do Workflow.

Mensagem:

```text
Não foi possível consultar o Workflow.
```

---

## Blocked

Quando existir um bloqueio crítico.

O componente deve destacar visualmente a etapa bloqueada.

---

# Navegação

Quando permitido pela interface, cada etapa pode direcionar o usuário para a página Fluxos.

| Etapa                | Destino                       |
| -------------------- | ----------------------------- |
| Organizar Biblioteca | Fluxos → Organizar Biblioteca |
| Catalogar Arquivos   | Fluxos → Catalogar Arquivos   |
| Resolver IDs         | Fluxos → Resolver IDs         |
| Atualizar Metadados  | Fluxos → Atualizar Metadados  |
| Sincronizar Notion   | Fluxos → Sincronizar Notion   |

A navegação não altera o estado do Workflow.

---

# Atualização

O Resumo do Workflow deve ser atualizado:

* durante o carregamento inicial;
* após atualização manual do Dashboard;
* após conclusão de qualquer etapa executada na página Fluxos.

---

# Responsividade

## Desktop

As etapas são exibidas em uma lista vertical.

---

## Tablet

Mantém a mesma estrutura.

---

## Mobile

A lista permanece vertical.

A ordem das etapas nunca deve ser alterada.

---

# Acessibilidade

O componente deve:

* permitir navegação por teclado;
* identificar claramente a etapa atual;
* não depender exclusivamente de cores para indicar estados;
* fornecer descrições compreensíveis para tecnologias assistivas.

---

# Dependências

O componente depende de:

* Dashboard API;
* Módulo Fluxos.

O estado apresentado pelo Dashboard deve refletir exatamente o estado mantido pelo módulo Fluxos, que é a única fonte de verdade para o Workflow.

---

# Critérios de Aceite

O componente será considerado conforme esta especificação quando:

* apresentar as cinco etapas oficiais do Workflow;
* manter a ordem fixa das etapas;
* indicar corretamente o estado de cada etapa;
* utilizar exclusivamente informações fornecidas pela API agregadora;
* suportar os estados Loading, Ready, Empty, Error e Blocked;
* permitir navegação para a página Fluxos quando aplicável;
* atuar apenas como resumo visual, sem executar ou modificar processos operacionais.
