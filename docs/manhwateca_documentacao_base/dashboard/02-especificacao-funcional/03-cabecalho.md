## 03 - Cabeçalho

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do cabeçalho do Dashboard da Manhwateca.

O cabeçalho representa o primeiro componente do Workspace e tem como objetivo identificar claramente o contexto da página, fornecer informações gerais ao usuário e disponibilizar ações globais relacionadas ao Dashboard.

---

# Objetivo do Componente

O Cabeçalho deve permitir que o usuário:

* identifique rapidamente a página atual;
* compreenda o propósito do Dashboard;
* saiba quando as informações foram atualizadas pela última vez;
* atualize manualmente os dados exibidos.

O componente não possui responsabilidades operacionais.

---

# User Stories Relacionadas

| User Story | Relação                            |
| ---------- | ---------------------------------- |
| US-001     | Identificação do Dashboard         |
| US-008     | Atualização manual das informações |
| US-009     | Navegação global da aplicação      |

---

# Estrutura do Componente

O Cabeçalho é composto pelos seguintes elementos.

```text
┌────────────────────────────────────────────────────────────┐
│ DASHBOARD                                                  │
│ Centro de comando da biblioteca                            │
│                                                            │
│ Última atualização: Hoje às 20:35        [ Recarregar ]    │
└────────────────────────────────────────────────────────────┘
```

---

# Componentes Internos

## Eyebrow

Texto pequeno utilizado para identificação do módulo.

Valor padrão:

```text
Dashboard
```

Função:

* identificar o módulo ativo;
* manter consistência com as demais páginas.

---

## Título

Título principal da página.

Valor padrão:

```text
Centro de Comando
```

ou

```text
Dashboard
```

(conforme definido pelo Design System)

O título deve permanecer constante.

---

## Descrição

Texto curto explicando a finalidade da página.

Exemplo:

```text
Acompanhe a saúde da biblioteca,
as pendências e o progresso do Workflow.
```

A descrição não deve ultrapassar duas linhas.

---

## Última Atualização

Exibe quando o Dashboard foi atualizado pela última vez.

Exemplo:

```text
Última atualização:
Hoje às 20:35
```

ou

```text
26/06/2026 20:35
```

A informação deve ser obtida do backend.

---

## Botão Recarregar

Texto padrão:

```text
Recarregar
```

Responsabilidade:

Solicitar uma nova atualização das informações do Dashboard.

O comportamento completo deste botão está documentado em:

```text
10-atualizacao.md
```

---

# Organização Visual

Os elementos devem seguir a seguinte disposição.

```text
Eyebrow

↓

Título

↓

Descrição

↓

Última atualização            Botão Recarregar
```

O botão deve permanecer alinhado à direita.

As informações textuais permanecem alinhadas à esquerda.

---

# Fonte de Dados

O componente consome:

```http
GET /api/dashboard
```

Campos utilizados:

```json
{
  "last_updated_at": "2026-06-26T20:35:00-03:00"
}
```

Os demais textos são fixos e fazem parte da interface.

---

# Estados do Componente

## Loading

Enquanto o Dashboard estiver carregando.

Comportamento:

* título visível;
* descrição visível;
* data substituída por skeleton;
* botão desabilitado.

---

## Ready

Estado padrão.

Todos os elementos são exibidos normalmente.

---

## Refreshing

Durante uma atualização manual.

Comportamento esperado:

* botão apresenta indicador de carregamento;
* botão permanece desabilitado;
* demais elementos continuam visíveis.

---

## Error

Caso não seja possível atualizar os dados.

Comportamento:

* manter a última data conhecida;
* apresentar mensagem de erro discreta;
* reabilitar o botão.

---

# Eventos

## EVT-001

Evento:

Selecionar **Recarregar**.

Resultado esperado:

Solicitar nova atualização do Dashboard.

---

## EVT-002

Conclusão da atualização.

Resultado esperado:

Atualizar o campo "Última atualização".

---

## EVT-003

Falha durante atualização.

Resultado esperado:

Manter informações existentes.

Exibir mensagem apropriada.

---

# Regras Funcionais

## RF-001

O Cabeçalho deve estar sempre visível no topo do Workspace.

---

## RF-002

O botão Recarregar nunca deve executar operações operacionais.

Ele apenas solicita nova leitura das informações.

---

## RF-003

A data exibida representa a última atualização conhecida do Dashboard.

Não corresponde necessariamente ao horário da última sincronização com serviços externos.

---

## RF-004

O botão Recarregar não pode ser acionado novamente enquanto uma atualização estiver em andamento.

---

## RF-005

Falhas na atualização não devem remover as informações já exibidas.

---

## RF-006

O Cabeçalho não deve variar conforme o estado do Workflow.

Seu conteúdo permanece estável durante toda a utilização da aplicação.

---

# Responsividade

## Desktop

Título e descrição alinhados à esquerda.

Botão Recarregar alinhado à direita.

---

## Tablet

O botão pode ocupar linha própria caso não exista espaço suficiente.

---

## Mobile

Todos os elementos devem ser empilhados verticalmente.

Ordem:

1. Eyebrow
2. Título
3. Descrição
4. Última atualização
5. Botão Recarregar

---

# Acessibilidade

O componente deve atender aos seguintes critérios:

* utilizar apenas um título principal (`h1`) na página;
* permitir navegação por teclado;
* fornecer texto alternativo para o botão quando necessário;
* possuir contraste adequado entre texto e fundo;
* indicar visualmente quando o botão estiver desabilitado.

---

# Dependências

O Cabeçalho depende diretamente de:

* Dashboard API (data da última atualização);
* Componente de atualização manual (`10-atualizacao.md`).

Não possui dependência funcional dos módulos Biblioteca, Fluxos ou Configurações.

---

# Critérios de Aceite

O componente será considerado conforme esta especificação quando:

* identificar claramente o Dashboard;
* apresentar título e descrição da página;
* exibir a data da última atualização;
* disponibilizar o botão Recarregar;
* manter comportamento consistente em todos os estados da interface;
* permanecer funcional em diferentes resoluções;
* delegar toda a lógica de atualização ao componente documentado em `10-atualizacao.md`.
