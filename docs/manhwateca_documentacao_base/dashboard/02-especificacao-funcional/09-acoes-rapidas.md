# Dashboard — Especificação Funcional

## 09 - Ações Rápidas

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do componente **Ações Rápidas**, responsável por oferecer atalhos para os principais módulos da Manhwateca.

As Ações Rápidas têm como objetivo reduzir a quantidade de navegação necessária para iniciar tarefas frequentes, mantendo o Dashboard como ponto central de acesso da aplicação.

Esta documentação implementa a **US-005 — Acessar ações rápidas**.

---

# Objetivo do Componente

O componente deve permitir que o usuário acesse rapidamente as principais funcionalidades da Manhwateca sem precisar navegar pelo menu lateral.

As Ações Rápidas **não executam operações diretamente**. Elas apenas direcionam o usuário para o módulo responsável.

---

# User Story Relacionada

| ID     | Título                |
| ------ | --------------------- |
| US-005 | Acessar ações rápidas |

---

# Conceito

Uma Ação Rápida representa um atalho para uma funcionalidade frequentemente utilizada.

Ela deve reduzir o número de cliques necessários para iniciar uma atividade, sem duplicar funcionalidades já existentes em outros módulos.

---

# Estrutura Visual

```text
┌──────────────────────────────────────────────┐
│ Ações Rápidas                                │
│                                              │
│ [📚 Biblioteca]                              │
│ [⚙ Fluxos]                                  │
│ [🔄 Atualizar Dashboard]                     │
│ [🛠 Configurações]                           │
└──────────────────────────────────────────────┘
```

Cada ação deve ser apresentada como um botão ou card clicável.

---

# Ações Disponíveis

O Dashboard disponibiliza quatro ações rápidas.

| Ordem | Ação                | Destino               |
| ----- | ------------------- | --------------------- |
| 1     | Biblioteca          | Página Biblioteca     |
| 2     | Fluxos              | Página Fluxos         |
| 3     | Atualizar Dashboard | Atualização dos dados |
| 4     | Configurações       | Página Configurações  |

A lista deve permanecer fixa.

---

# Biblioteca

## Objetivo

Permitir acesso imediato ao catálogo da biblioteca.

Destino:

```text
Biblioteca
```

Esta ação não abre uma obra específica.

---

# Fluxos

## Objetivo

Permitir acesso ao módulo responsável pela execução do Workflow.

Destino:

```text
Fluxos
```

Quando existir um próximo passo recomendado, o módulo Fluxos deverá ser aberto diretamente na etapa correspondente.

---

# Atualizar Dashboard

## Objetivo

Atualizar as informações exibidas na página.

Esta ação executa o mesmo comportamento documentado em:

```text
10-atualizacao.md
```

Ela não executa tarefas do Workflow.

---

# Configurações

## Objetivo

Permitir acesso rápido ao ambiente de configuração da aplicação.

Destino:

```text
Configurações
```

Utilizado principalmente quando houver problemas de infraestrutura ou necessidade de alterar parâmetros da aplicação.

---

# Fonte de Dados

As Ações Rápidas são componentes fixos da interface.

Elas não dependem de informações provenientes da API.

Apenas seu estado (habilitado ou desabilitado) poderá variar conforme o contexto da aplicação.

---

# Estados do Componente

## Ready

Todas as ações estão disponíveis.

---

## Disabled

Uma ação permanece visível, porém desabilitada.

Exemplo:

```text
Fluxos indisponível
```

---

## Loading

Durante o carregamento inicial do Dashboard.

Os botões permanecem desabilitados até que a página esteja pronta.

---

# Navegação

| Ação                | Destino                 |
| ------------------- | ----------------------- |
| Biblioteca          | Biblioteca              |
| Fluxos              | Fluxos                  |
| Atualizar Dashboard | Atualiza a página atual |
| Configurações       | Configurações           |

A navegação deve utilizar exclusivamente o roteador interno da aplicação.

---

# Regras Funcionais

## RF-001

As Ações Rápidas nunca executam processos operacionais diretamente.

---

## RF-002

Toda ação deve possuir um destino claramente definido.

---

## RF-003

A ação **Atualizar Dashboard** é a única exceção, permanecendo na própria página.

---

## RF-004

Quando o módulo de destino estiver indisponível, a ação deve permanecer visível, porém desabilitada.

---

## RF-005

As Ações Rápidas não substituem o menu lateral.

Elas representam apenas atalhos para funcionalidades frequentemente utilizadas.

---

## RF-006

A ordem das ações deve permanecer constante para preservar a memória espacial do usuário.

---

## RF-007

Os ícones utilizados devem representar claramente a funcionalidade correspondente.

---

## RF-008

Sempre que possível, o contexto da navegação deve ser preservado.

Exemplo:

Ao selecionar **Fluxos**, o usuário poderá ser direcionado para a etapa recomendada pelo Dashboard.

---

# Responsividade

## Desktop

As ações podem ser apresentadas em uma única linha ou em uma grade.

---

## Tablet

Os botões podem ser distribuídos em duas linhas.

---

## Mobile

Cada ação ocupa toda a largura disponível.

A ordem permanece inalterada.

---

# Acessibilidade

O componente deve:

* permitir navegação por teclado;
* possuir área de clique adequada;
* apresentar rótulos textuais claros;
* fornecer indicação visual de foco;
* não depender exclusivamente de ícones para transmitir significado.

---

# Dependências

O componente depende de:

* Sistema de Navegação;
* Componente de Atualização (`10-atualizacao.md`).

As demais ações apenas encaminham o usuário para os módulos Biblioteca, Fluxos ou Configurações.

---

# Critérios de Aceite

O componente será considerado conforme esta especificação quando:

* apresentar exatamente quatro ações rápidas;
* manter ordem fixa dos atalhos;
* permitir acesso direto aos módulos principais da aplicação;
* utilizar o roteador interno para navegação;
* suportar os estados Ready, Loading e Disabled;
* não executar processos operacionais diretamente;
* manter consistência visual com os demais componentes do Dashboard.
