# Dashboard — Especificação Funcional

## 06 - Pendências Acionáveis

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do painel **Pendências Acionáveis** do Dashboard da Manhwateca.

Seu objetivo é consolidar todas as pendências relevantes da aplicação em um único local, permitindo que o usuário identifique rapidamente quais atividades exigem atenção e navegue diretamente para o módulo responsável pela resolução.

Esta documentação implementa a **US-004 — Consultar pendências críticas**.

---

# Objetivo do Componente

O painel de Pendências Acionáveis deve:

* destacar apenas situações que exigem intervenção do usuário;
* priorizar pendências bloqueantes;
* reduzir o tempo gasto procurando problemas em diferentes módulos;
* direcionar o usuário para a etapa correta do Workflow.

O painel não executa nenhuma ação corretiva.

---

# User Story Relacionada

| ID     | Título                        |
| ------ | ----------------------------- |
| US-004 | Consultar pendências críticas |

---

# Estrutura Visual

```text
┌──────────────────────────────────────────────────────┐
│ Pendências Acionáveis                                │
│                                                      │
│ 🔴 8 obras sem ID confirmado                         │
│ Resolver antes de atualizar metadados.               │
│                                      [Abrir Fluxos]  │
│──────────────────────────────────────────────────────│
│ 🟡 14 alterações aguardando sincronização            │
│ Existem alterações pendentes no Notion.              │
│                                      [Abrir Fluxos]  │
└──────────────────────────────────────────────────────┘
```

Cada pendência deve ser apresentada como um item independente.

---

# Estrutura de uma Pendência

Cada item deve conter obrigatoriamente:

* indicador visual de severidade;
* título;
* descrição;
* botão de navegação.

Opcionalmente poderá apresentar:

* quantidade de ocorrências;
* categoria;
* data da identificação.

---

# Fonte de Dados

As pendências devem ser obtidas exclusivamente através da API agregadora.

```http
GET /api/dashboard
```

Estrutura esperada:

```json
{
  "pending": [
    {
      "id": "without_id",
      "title": "8 obras sem ID confirmado",
      "description": "Resolva antes de atualizar metadados.",
      "severity": "danger",
      "target_page": "flows",
      "target_step": "resolve_ids"
    }
  ]
}
```

O Dashboard não deve gerar pendências localmente.

---

# Severidades

As pendências devem utilizar quatro níveis de severidade.

| Severidade | Uso                             |
| ---------- | ------------------------------- |
| danger     | Bloqueios ou ações obrigatórias |
| warn       | Atenção necessária              |
| info       | Informações relevantes          |
| ok         | Não utilizado para pendências   |

---

# Ordenação

As pendências devem ser exibidas obedecendo a seguinte prioridade:

1. Bloqueios de infraestrutura;
2. Etapas obrigatórias do Workflow;
3. Pendências de sincronização;
4. Informações complementares.

Dentro da mesma severidade, a ordenação deve seguir a sequência oficial do Workflow.

---

# Agrupamento

As pendências devem representar categorias de problemas.

Exemplo correto:

```text
8 obras sem ID confirmado
```

Exemplo incorreto:

```text
Payback
Semantic Error
The Pizza Delivery Man
...
```

O detalhamento individual pertence ao módulo **Fluxos**.

---

# Estados do Componente

## Loading

Enquanto as informações são carregadas.

O painel deve apresentar skeletons para cada item.

---

## Ready

Estado padrão.

Todas as pendências são apresentadas normalmente.

---

## Empty

Quando não existirem pendências.

Exemplo:

```text
✔ Nenhuma pendência encontrada.

Sua biblioteca está pronta para uso.
```

O painel permanece visível.

---

## Partial

Quando apenas parte das pendências puder ser obtida.

As pendências disponíveis permanecem visíveis.

Uma mensagem discreta informa que algumas informações não puderam ser carregadas.

---

## Error

Quando não for possível obter nenhuma pendência.

O painel permanece renderizado.

Mensagem sugerida:

```text
Não foi possível consultar as pendências.
```

---

# Navegação

Cada pendência possui um único destino.

| Tipo de Pendência    | Destino                       |
| -------------------- | ----------------------------- |
| Organizar biblioteca | Fluxos → Organizar Biblioteca |
| Catalogar arquivos   | Fluxos → Catalogar Arquivos   |
| Resolver IDs         | Fluxos → Resolver IDs         |
| Atualizar metadados  | Fluxos → Atualizar Metadados  |
| Sincronizar Notion   | Fluxos → Sincronizar Notion   |
| Problema de ambiente | Configurações                 |

A navegação é responsabilidade do Dashboard.

A resolução da pendência ocorre exclusivamente no módulo de destino.

---

# Regras Funcionais

## RF-001

Somente pendências acionáveis devem ser exibidas.

---

## RF-002

Pendências informativas não pertencem a este painel.

---

## RF-003

Cada categoria de problema deve aparecer apenas uma vez.

---

## RF-004

Pendências resolvidas deixam de ser exibidas automaticamente após a atualização do Dashboard.

---

## RF-005

O painel nunca deve listar obras individualmente.

---

## RF-006

Toda pendência deve possuir um destino de navegação.

---

## RF-007

Pendências críticas possuem prioridade absoluta sobre qualquer outra informação do painel.

---

## RF-008

O painel não deve permitir edição, confirmação ou resolução direta das pendências.

---

# Atualização

As pendências devem ser atualizadas:

* durante o carregamento inicial;
* após atualização manual do Dashboard;
* após conclusão de processos executados em Fluxos.

---

# Responsividade

## Desktop

Lista completa ocupando a coluna esquerda do Grid Principal.

---

## Tablet

Mantém uma coluna dedicada sempre que houver espaço disponível.

---

## Mobile

O painel ocupa toda a largura disponível.

Cada pendência é apresentada verticalmente.

---

# Acessibilidade

O componente deve:

* utilizar indicadores visuais e textuais de severidade;
* permitir navegação por teclado;
* apresentar foco visível nos botões;
* não depender exclusivamente de cores para indicar prioridade.

---

# Dependências

O painel depende de:

* Dashboard API;
* Workflow;
* Sistema de Navegação.

Não possui dependência direta da Biblioteca ou do Notion.

---

# Critérios de Aceite

O painel será considerado conforme esta especificação quando:

* apresentar apenas pendências que exijam ação do usuário;
* agrupar ocorrências por categoria;
* ordenar os itens pela prioridade definida;
* permitir navegação para o módulo responsável;
* suportar os estados Loading, Ready, Empty, Partial e Error;
* manter sua posição no layout mesmo quando não houver pendências;
* não executar nenhuma ação corretiva diretamente pelo Dashboard.
