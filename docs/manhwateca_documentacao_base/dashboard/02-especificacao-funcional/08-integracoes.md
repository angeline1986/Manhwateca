# Dashboard — Especificação Funcional

## 08 - Estado das Integrações

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do componente **Estado das Integrações**, responsável por apresentar um resumo da saúde dos serviços e recursos necessários para o funcionamento da Manhwateca.

O componente permite identificar rapidamente problemas de infraestrutura antes da execução do Workflow.

Esta documentação implementa a **US-007 — Consultar o estado das integrações**.

---

# Objetivo do Componente

O painel de Integrações deve:

* informar se o ambiente está operacional;
* identificar rapidamente problemas de infraestrutura;
* distinguir falhas operacionais de falhas de configuração;
* direcionar o usuário para Configurações quando necessário.

O componente possui finalidade exclusivamente informativa.

---

# User Story Relacionada

| ID     | Título                             |
| ------ | ---------------------------------- |
| US-007 | Consultar o estado das integrações |

---

# Integrações Monitoradas

O Dashboard monitora as seguintes integrações.

| Integração   | Finalidade                        |
| ------------ | --------------------------------- |
| PostgreSQL   | Armazenamento do catálogo local   |
| Biblioteca   | Acesso aos arquivos da biblioteca |
| MangaUpdates | Consulta de metadados das obras   |
| Notion       | Sincronização da biblioteca       |

Novas integrações deverão ser documentadas neste arquivo antes de serem incorporadas ao Dashboard.

---

# Estrutura Visual

```text
┌──────────────────────────────────────────────┐
│ Estado das Integrações                       │
│                                              │
│ 🟢 PostgreSQL        Operacional             │
│ 🟢 Biblioteca        Diretório acessível     │
│ 🟡 MangaUpdates      Resposta lenta          │
│ 🔴 Notion            Token inválido          │
└──────────────────────────────────────────────┘
```

Cada integração deve ocupar apenas uma linha.

---

# Estrutura da Integração

Cada item deve conter:

* nome da integração;
* indicador visual;
* descrição resumida do estado.

Não devem ser exibidas mensagens técnicas ou exceções da aplicação.

---

# Fonte de Dados

O componente deve consumir exclusivamente:

```http
GET /api/dashboard
```

Estrutura esperada:

```json
{
  "integrations": [
    {
      "id": "postgresql",
      "name": "PostgreSQL",
      "status": "ok",
      "description": "Banco conectado."
    }
  ]
}
```

O Dashboard não deve realizar verificações diretamente nos serviços.

---

# Estados Possíveis

Cada integração pode assumir um dos seguintes estados.

| Estado         | Significado                |
| -------------- | -------------------------- |
| ok             | Operacional                |
| warn           | Operacional com restrições |
| error          | Indisponível               |
| not_configured | Ainda não configurada      |

---

# Regras Funcionais

## RF-001

Cada integração deve possuir exatamente um estado.

---

## RF-002

O Dashboard não deve realizar autenticação nem validação detalhada das integrações.

---

## RF-003

Mensagens técnicas devem permanecer restritas ao módulo Configurações.

---

## RF-004

A indisponibilidade de uma integração não impede a renderização das demais.

---

## RF-005

Sempre que possível, deve ser apresentada uma orientação simples ao usuário.

Exemplo:

```text
Token do Notion inválido.

Verifique a configuração da integração.
```

---

## RF-006

Integrações indisponíveis não devem ocultar outras informações do Dashboard.

---

## RF-007

Problemas críticos de infraestrutura possuem prioridade sobre informações meramente informativas.

---

# Navegação

Quando uma integração apresentar estado **error** ou **not_configured**, o componente deve permitir navegação para Configurações.

| Integração   | Destino                        |
| ------------ | ------------------------------ |
| PostgreSQL   | Configurações → Banco de Dados |
| Biblioteca   | Configurações → Biblioteca     |
| MangaUpdates | Configurações → Integrações    |
| Notion       | Configurações → Integrações    |

O Dashboard não deve oferecer ações de correção.

---

# Estados do Componente

## Loading

As integrações devem ser apresentadas como skeleton.

---

## Ready

Todas as integrações são exibidas normalmente.

---

## Partial

Quando apenas parte das integrações puder ser consultada.

As integrações disponíveis permanecem visíveis.

---

## Error

Quando nenhuma informação puder ser obtida.

Mensagem:

```text
Não foi possível consultar o estado das integrações.
```

---

# Atualização

As informações devem ser atualizadas:

* durante o carregamento inicial;
* após atualização manual do Dashboard;
* após alterações realizadas em Configurações.

---

# Responsividade

## Desktop

Lista vertical.

---

## Tablet

Mantém a mesma estrutura.

---

## Mobile

Cada integração ocupa uma linha completa.

O texto pode quebrar em múltiplas linhas quando necessário.

---

# Acessibilidade

O componente deve:

* utilizar texto e ícones para indicar estado;
* não depender exclusivamente de cores;
* permitir leitura por tecnologias assistivas;
* manter contraste adequado entre texto e fundo.

---

# Dependências

O componente depende de:

* Dashboard API;
* Configurações.

O Dashboard apenas apresenta o estado resumido das integrações.

Toda configuração, autenticação, teste detalhado e diagnóstico pertencem exclusivamente ao módulo Configurações.

---

# Critérios de Aceite

O componente será considerado conforme esta especificação quando:

* apresentar todas as integrações monitoradas;
* indicar corretamente o estado de cada integração;
* utilizar informações fornecidas pela API agregadora;
* suportar os estados Loading, Ready, Partial e Error;
* direcionar o usuário para Configurações quando necessário;
* não realizar verificações diretas nos serviços monitorados;
* manter linguagem compreensível para usuários não técnicos.
