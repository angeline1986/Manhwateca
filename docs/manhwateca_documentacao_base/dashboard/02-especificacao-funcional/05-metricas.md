## 05 - Métricas Operacionais

---

# Objetivo do Documento

Este documento especifica o comportamento funcional dos **Cards de Métricas** exibidos no Dashboard da Manhwateca.

As métricas fornecem uma visão resumida do estado da biblioteca e permitem que o usuário compreenda rapidamente a situação atual da coleção.

Esta documentação está diretamente relacionada à **US-003 — Visualizar métricas operacionais**.

---

# Objetivo do Componente

Os Cards de Métricas têm como objetivo apresentar indicadores consolidados da biblioteca, permitindo uma avaliação rápida da situação geral do sistema.

As métricas possuem caráter exclusivamente informativo.

Elas não executam ações nem permitem edição direta dos dados.

---

# User Story Relacionada

| ID     | Título                           |
| ------ | -------------------------------- |
| US-003 | Visualizar métricas operacionais |

---

# Métricas Disponíveis

O Dashboard apresenta quatro métricas principais.

| Ordem | Métrica              | Objetivo                                  |
| ----- | -------------------- | ----------------------------------------- |
| 1     | Total de Obras       | Quantidade total de obras cadastradas     |
| 2     | Novos Capítulos      | Obras com novos capítulos detectados      |
| 3     | Obras sem ID         | Obras que ainda precisam de identificação |
| 4     | Pendências do Notion | Alterações aguardando sincronização       |

A quantidade de métricas é fixa.

---

# Estrutura Visual

Cada métrica deve ser apresentada em um card independente.

```text id="w3sl2m"
┌────────────────────────────┐
│ Total de Obras             │
│                            │
│            347             │
│                            │
│ Obras catalogadas          │
└────────────────────────────┘
```

Todos os cards devem possuir dimensões semelhantes.

---

# Organização dos Cards

Os cards devem ser apresentados na seguinte ordem:

```text id="ag2hnn"
┌─────────┬─────────┬─────────┬─────────┐
│ Obras   │ Novos   │ Sem ID  │ Notion  │
└─────────┴─────────┴─────────┴─────────┘
```

A ordem não deve variar.

---

# Especificação das Métricas

## Total de Obras

### Objetivo

Informar a quantidade total de obras cadastradas na biblioteca.

### Fonte

Catálogo local (PostgreSQL).

### Exemplo

```text id="wv4nnk"
347
Obras catalogadas
```

---

## Novos Capítulos

### Objetivo

Informar quantas obras possuem novos capítulos detectados desde a última atualização.

### Fonte

Resultado consolidado do Workflow.

### Exemplo

```text id="c9e64o"
23
Novos capítulos
```

---

## Obras sem ID

### Objetivo

Informar quantas obras ainda precisam ser identificadas antes da atualização dos metadados.

### Fonte

Workflow / Catálogo.

### Exemplo

```text id="ijglx6"
8
Sem ID
```

---

## Pendências do Notion

### Objetivo

Informar quantas alterações aguardam sincronização.

### Fonte

Processo de sincronização.

### Exemplo

```text id="rjgjts"
14
Pendentes
```

---

# Fonte de Dados

Todas as métricas devem ser obtidas através do endpoint agregador.

```http id="9xlb6y"
GET /api/dashboard
```

Estrutura esperada:

```json id="9qudme"
{
  "metrics": {
    "total_works": 347,
    "new_chapters": 23,
    "without_id": 8,
    "notion_pending": 14
  }
}
```

O Dashboard não deve calcular métricas localmente.

---

# Estados do Componente

## Loading

Enquanto os dados estiverem sendo carregados.

Cada card deve exibir um skeleton.

---

## Ready

Estado padrão.

Todos os indicadores são apresentados normalmente.

---

## Empty

Caso não existam obras cadastradas.

Exemplo:

```text id="bx91zk"
0

Obras catalogadas
```

Não deve ser exibida mensagem de erro.

---

## Partial

Caso alguma métrica esteja indisponível.

Exemplo:

```text id="8x3fze"
Dados indisponíveis
```

Os demais cards permanecem funcionando normalmente.

---

## Error

Caso não seja possível obter nenhuma métrica.

Todos os cards devem permanecer visíveis.

Cada um apresenta:

```text id="12txit"
—
```

acompanhado da descrição:

```text id="ey53km"
Informação indisponível
```

---

# Regras Funcionais

## RF-001

Os cards representam informações consolidadas.

---

## RF-002

As métricas não executam ações.

---

## RF-003

Os cards não possuem comportamento de clique.

---

## RF-004

Os valores apresentados representam o último estado conhecido da aplicação.

---

## RF-005

Os cards nunca devem iniciar consultas ao MangaUpdates ou Notion.

---

## RF-006

A indisponibilidade de uma métrica não deve impedir a exibição das demais.

---

## RF-007

Os cards devem manter posição fixa independentemente dos valores apresentados.

---

## RF-008

Todos os cards devem utilizar o mesmo padrão visual.

---

# Atualização

As métricas são atualizadas:

* durante o carregamento inicial;
* após atualização manual do Dashboard;
* após retorno de uma operação concluída na página Fluxos.

O comportamento da atualização é documentado em **10-atualizacao.md**.

---

# Responsividade

## Desktop

Quatro cards exibidos na mesma linha.

---

## Tablet

Os cards podem ser distribuídos em duas linhas.

---

## Mobile

Cada card ocupa uma linha completa.

A ordem de exibição permanece:

1. Total de Obras
2. Novos Capítulos
3. Obras sem ID
4. Pendências do Notion

---

# Acessibilidade

Os cards devem:

* apresentar boa legibilidade;
* possuir contraste adequado;
* não depender exclusivamente de cores para transmitir significado;
* permitir leitura correta por tecnologias assistivas.

---

# Dependências

Este componente depende de:

* Dashboard API;
* PostgreSQL;
* Workflow;
* Processo de sincronização.

Não possui dependência visual dos demais componentes do Dashboard.

---

# Critérios de Aceite

O componente será considerado conforme esta especificação quando:

* apresentar exatamente quatro métricas;
* manter ordem fixa dos cards;
* utilizar dados fornecidos pela API agregadora;
* suportar os estados Loading, Ready, Empty, Partial e Error;
* não permitir interação direta com os indicadores;
* manter consistência visual em todas as resoluções;
* atualizar seus valores apenas durante o carregamento ou atualização do Dashboard.
